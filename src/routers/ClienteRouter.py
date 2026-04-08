# Aluno: Rodrigo Vaisam Bastos
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from slowapi.errors import RateLimitExceeded

# Domain Schemas
from domain.schemas.AuthSchema import FuncionarioAuth
from domain.schemas.ClienteSchema import ClienteCreate, ClienteUpdate, ClienteResponse

# Infra ORM, Database
from infra.orm.ClienteModel import ClienteDB
from infra.database import get_db
from infra.dependencies import get_current_active_user, require_group

# Limiter e AuditoriaService
from services.AuditoriaService import AuditoriaService
from infra.rate_limit import limiter, get_rate_limit

router = APIRouter()

# Novo get_cliente com ORM
@router.get("/cliente/", response_model=List[ClienteResponse], tags=["Cliente"], status_code=status.HTTP_200_OK)
@limiter.limit(get_rate_limit("moderate")) # o tempo em minutos do moderate é: 100min
async def get_clientes(
    request: Request,
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(get_current_active_user)
):
    """Retorna todos os clientes"""
    try:
        clientes = db.query(ClienteDB).all()
        return clientes
    except RateLimitExceeded:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar clientes: {str(e)}"
        )

# Novo get_cliente{id} com ORM, protegida
@router.get("/cliente/{id}", response_model=ClienteResponse, tags=["Cliente"], status_code=status.HTTP_200_OK)
async def get_cliente(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(get_current_active_user) # get_current_active_user -> protegida.
    ):
    """Retorna um cliente específico"""
    try:
        cliente = db.query(ClienteDB).filter(ClienteDB.id == id).first()
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente não encontrado"
            )
        return cliente
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar cliente: {str(e)}"
        )

# Novo post_cliente com ORM
@router.post("/cliente/", response_model=ClienteResponse, tags=["Cliente"], status_code=status.HTTP_201_CREATED)
@limiter.limit(get_rate_limit("restrictive")) # o tempo em minutos do restrictive é: 20min
async def post_cliente(
    request: Request,
    cliente_data: ClienteCreate,
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(require_group([1, 3])) # Somente gerentes e caixa podem criar clientes.
    ):
    """Cria um novo cliente"""
    try:
        # verifica se já existe um cliente com o mesmo CPF
        existing_cliente = db.query(ClienteDB).filter(ClienteDB.cpf == cliente_data.cpf).first()
        
        if existing_cliente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe um cliente com este CPF"
            )

        # Cria o novo cliente
        novo_cliente = ClienteDB(
            id=None, # O ID será gerado automaticamente pelo banco de dados
            nome=cliente_data.nome,
            cpf=cliente_data.cpf,
            telefone=cliente_data.telefone
        )
        db.add(novo_cliente)
        db.commit()
        db.refresh(novo_cliente) # Lembrando, o reload já faz o trabalho do refresh, mas deixa ai kk

        # Depois de tudo executado e antes do return, registra a ação na auditoria
        AuditoriaService.registrar_acao(
            db=db,
            funcionario_id=current_user.id,
            acao="CREATE",
            recurso="CLIENTE",
            recurso_id=novo_cliente.id,
            dados_antigos=None,
            dados_novos=novo_cliente,
            request=request
        )

        return novo_cliente
    
    except RateLimitExceeded:
    # Propagar a exceção original para o handler personalizado
        raise
    except Exception:
        raise
    except Exception as e:
        db.rollback() # Em caso de erro, desfaz as alterações no banco de dados
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar cliente: {str(e)}"
        )

# Novo put_cliente{id} com ORM
@router.put("/cliente/{id}", response_model=ClienteResponse, tags=["Cliente"], status_code=status.HTTP_200_OK)
@limiter.limit(get_rate_limit("restrictive")) # o tempo em minutos do restrictive é: 20min
async def put_cliente(
    request: Request,
    id: int,
    cliente_data: ClienteUpdate,
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(require_group([1, 3]))
    ):
    """Atualiza um cliente existente"""
    try:
        cliente = db.query(ClienteDB).filter(ClienteDB.id == id).first()

        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente não encontrado"
            )
        
        # Verifica se está tentando atualizar o CPF para um valor que já existe em outro cliente
        if cliente_data.cpf and cliente_data.cpf != cliente.cpf:
        # o cliente_data repete, pois o cliente_data.cpf é o novo CPF que está tentando atualizar, e o cliente.cpf
        # é o CPF atual do cliente no banco de dados, então só precisa verificar se o cliente_data.cpf é diferente do
        # cliente.cpf para evitar a situação onde o cliente está tentando atualizar o CPF para o mesmo valor que já tem.
            existing_cliente = db.query(ClienteDB).filter(ClienteDB.cpf == cliente_data.cpf).first()
            if existing_cliente:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Já existe um cliente com este CPF"
                )
            
            # Armazena uma cópia do objeto com os dados atuais, para salvar na auditoria
            # Não pode manter referência com funcionário, pare que o auditoria possa comparar
            # Por isso a cópia do __dict__
            dados_antigos_obj = cliente.__dict__.copy()
            
        # atualiza apenas os campos fornecidos, ou seja, que não são None
        update_data = cliente_data.model_dump(exclude_unset=True)
        # model_dump é um método do Pydantic que converte o modelo em um dicionário, e o exclude_unset=True faz com que ele exclua os campos que não foram fornecidos na requisição, ou seja, que são None.

        dados_antigos_obj = cliente.__dict__.copy()

        for field, value in update_data.items():
            setattr(cliente, field, value) # Atualiza os campos do cliente com os dados fornecidos
            # field é o nome do campo, que nesse caso está sendo percorrido pelo for

        db.commit()
        db.refresh(cliente) # Lembrando, o reload já faz o trabalho do refresh, mas deixa ai kk

        AuditoriaService.registrar_acao(
            db=db,
            funcionario_id=current_user.id,
            acao="UPDATE",
            recurso="CLIENTE",
            recurso_id=cliente.id,
            dados_antigos=dados_antigos_obj,
            dados_novos=cliente,
            request=request
        )

        return cliente
    
    except HTTPException:
        # Se for um erro HTTP conhecido (400, 404 que você mesmo criou), apenas repassa ele
        raise
    except Exception as e:
        db.rollback() # Em caso de erro, desfaz as alterações no banco de dados e devolve Erro 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar cliente: {str(e)}"
        )

@router.delete("/cliente/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Cliente"], summary="Remover cliente")
@limiter.limit(get_rate_limit("critical")) # o tempo em minutos do critical é: 5min
async def delete_cliente(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(require_group([1])) # Somente gerentes podem excluir clientes.
):
    """Exclui um cliente existente"""
    try:
        cliente = db.query(ClienteDB).filter(ClienteDB.id == id).first()

        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente não encontrado"
            )

        db.delete(cliente)
        db.commit()

        # Depois de tudo executado e antes do return, registra a ação na auditoria
        AuditoriaService.registrar_acao(
            db=db,
            funcionario_id=current_user.id,
            acao="DELETE",
            recurso="CLIENTE",
            recurso_id=cliente.id,
            dados_antigos=cliente,
            dados_novos=None,
            request=request
        )

        return None # Pesquisar no chat, do por quê retornar None, ja que antes ele tinha feito "return produto".
        # Resposta: O código HTTP 204 significa literalmente "No Content" (Sem Conteúdo).
        # A especificação do protocolo HTTP diz que, quando um servidor responde com 204,
        # ele é terminantemente proibido de enviar um corpo na resposta (body)

    except RateLimitExceeded:
        raise
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao excluir cliente: {str(e)}"
        )