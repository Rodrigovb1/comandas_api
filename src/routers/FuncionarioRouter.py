# Aluno: Rodrigo Vaisam Bastos
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from typing import List, Optional

# Infra ORM, Database, Auth
from infra.orm.FuncionarioModel import FuncionarioDB
from infra.database import get_db
from infra.security import get_password_hash
from infra.dependencies import get_current_active_user, require_group
from domain.schemas.AuthSchema import FuncionarioAuth
from domain.schemas.FuncionarioSchema import FuncionarioCreate, FuncionarioUpdate, FuncionarioResponse

# Limiter e AuditoriaService
from services.AuditoriaService import AuditoriaService
from infra.rate_limit import limiter, get_rate_limit

# Ajustes nas rotas para inclusão dos comandas ORM
router = APIRouter()

@router.get("/funcionario/", response_model=List[FuncionarioResponse], tags=["Funcionário"], status_code=status.HTTP_200_OK, summary="Listar funcionários - protegida por autenticação e grupo")
@limiter.limit(get_rate_limit("moderate")) # o tempo em minutos do moderate é: 100min
async def get_funcionarios(
    request: Request,
    skip: int = Query(0, ge=0, description="Número de registros para pular"), # ge = maior ou igual
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"), # ge = maior ou igual, le = menor ou igual
    id: Optional[int] = Query(None, description="Filtrar por ID"),
    nome: Optional[str] = Query(None, description="Filtrar por nome"),
    matricula: Optional[str] = Query(None, description="Filtrar por matrícula"),
    cpf: Optional[str] = Query(None, description="Filtrar por CPF"),
    grupo: Optional[str] = Query(None, description="Filtrar por grupo: 1=Admin, 2=Balcão, 3=Caixa - Separar por vírgula"),
    telefone: Optional[str] = Query(None, description="Filtrar por telefone"),
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(require_group([1]))
):
    try:
        query = db.query(FuncionarioDB)

        # Aplicar filtros
        if id is not None:
            query = query.filter(FuncionarioDB.id == id)
        if nome is not None:
            query = query.filter(FuncionarioDB.nome.ilike(f"%{nome}%")) # ilike = case insensitive
        if matricula is not None:
            query = query.filter(FuncionarioDB.matricula == matricula)
        if cpf is not None:
            query = query.filter(FuncionarioDB.cpf == cpf)
        if grupo is not None:
            # Converter string separada por vírgula para lista de inteiros
            grupos_list = [int(g.strip()) for g in grupo.split(',') if g.strip().isdigit()]
            query = query.filter(FuncionarioDB.grupo.in_(grupos_list))
        if telefone is not None:
            query = query.filter(FuncionarioDB.telefone.ilike(f"%{telefone}%"))
        
        # Aplicar paginação
        funcionarios = query.offset(skip).limit(limit).all()
        
        return funcionarios
    except RateLimitExceeded:
        # Propagar exceção original para o handler personalizado
        raise
    except Exception as e:
        # Apenas erros reais da aplicação (não rate limit)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar funcionários: {str(e)}"
        )

@router.get("/funcionario/{id}", response_model=FuncionarioResponse, tags=["Funcionário"], status_code=status.HTTP_200_OK)
async def get_funcionario(
    id: int,
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(get_current_active_user)
    ):
    """Retorna um funcionário específico"""
    try:
        funcionario = db.query(FuncionarioDB).filter(FuncionarioDB.id == id).first()
        if not funcionario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Funcionário não encontrado"
            )
        return funcionario
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar funcionário: {str(e)}"
        )

# • O verbo post será utilizado para criar um novo funcionário.
# • Conforme já vimos anteriormente, a entrada dos dados será realizada através de um JSON enviado no corpo da requisição,
# sendo passada para dentro da nossa classe através da classe FuncionarioCreate, herdando de BaseModel.
@router.post("/funcionario/", response_model=FuncionarioResponse, tags=["Funcionário"], status_code=status.HTTP_201_CREATED)
@limiter.limit(get_rate_limit("restrictive")) # o tempo em minutos do restrictive é: 20min
async def post_funcionario(
    request: Request,
    funcionario_data: FuncionarioCreate,
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(require_group([1]))
    ):
    """Cria um novo funcionário"""
    try:
        # verifica se já existe um funcionário com este CPF
        existing_funcionario = db.query(FuncionarioDB).filter(FuncionarioDB.cpf == funcionario_data.cpf).first()

        if existing_funcionario:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe um funcionário com este CPF"
            )
        
        # O banco também tem uma restrição UNIQUE para a matrícula, precisamos verificar
        existing_matricula = db.query(FuncionarioDB).filter(FuncionarioDB.matricula == funcionario_data.matricula).first()
        if existing_matricula:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe um funcionário com esta matrícula"
            )
        
        # Hash de senha
        hashed_password = get_password_hash(funcionario_data.senha) # pegando a senha em texto puro (nos parênteses) e aplica a função de hash de senha, 

        # Cria o novo funcionário
        novo_funcionario = FuncionarioDB(
            id=None,  # O ID será gerado automaticamente pelo banco de dados
            nome=funcionario_data.nome,
            matricula=funcionario_data.matricula,
            cpf=funcionario_data.cpf,
            telefone=funcionario_data.telefone,
            grupo=funcionario_data.grupo,
            senha=hashed_password
        )
        # foi alterado o senha, que antes tava como funcionario_data.senha, ou seja, pegava a senha em texto puro.

        db.add(novo_funcionario)
        db.commit()
        db.refresh(novo_funcionario) # Não precisa, pois o reload já ta fazendo isso, mas deixa ai kk

        # Depois de tudo executado, e antes do return, registra a ação na auditoria
        AuditoriaService.registrar_acao(
            db=db,
            funcionario_id=current_user.id,
            acao="CREATE",
            recurso="funcionario",
            recurso_id=novo_funcionario.id,
            dados_antigos=None, # None, pois não existe um estado anterior do funcionário, já que ele está sendo criado agora
            dados_novos=novo_funcionario, # Objeto SQLAlchemy, com dados novos
            request=request # Request completo para capturar IP e user agent, mesmo que seja um endpoint protegido por autenticação, pois o request ainda é necessário para pegar esses dados de contexto do cliente
        )

        return novo_funcionario
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar funcionário: {str(e)}"
        )

# Mesma coisa do post, a diferença aqui é que tem que especificar o id.
@router.put("/funcionario/{id}", response_model=FuncionarioResponse, tags=["Funcionário"], status_code=status.HTTP_200_OK)
@limiter.limit(get_rate_limit("restrictive")) # o tempo em minutos do restrictive é: 20min
async def put_funcionario(
    request: Request,
    id: int, funcionario_data: FuncionarioUpdate,
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(require_group([1]))
    ):
    """Atualiza um funcionário existente"""
    try:
        funcionario = db.query(FuncionarioDB).filter(FuncionarioDB.id == id).first()

        if not funcionario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Funcionário não encontrado"
            )

        # Verifica se está tentando atualizar o CPF para um valor que já existe em outro funcionário
        if funcionario_data.cpf and funcionario_data.cpf != funcionario.cpf:
            existing_funcionario = db.query(FuncionarioDB).filter(FuncionarioDB.cpf == funcionario_data.cpf).first()

            if existing_funcionario:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Já existe um funcionário com este CPF"
                )
            
        # Hash de senha, caso a senha for alterada
        if funcionario_data.senha:
            funcionario_data.senha = get_password_hash(funcionario_data.senha)
        # Os if de python usam um conceito chamado Truthy e Falsy
        # Falsy: None, False, 0, 0.0, '', [], {}, set()
        # Truthy: Qualquer coisa que contenha algum dado. Exemplos: "senha123", 1, [1, 2], True.
        
        # Se a senha não for fornecida (None, vazia), o if é ignorado, e a senha do funcionário permanecerá inalterada.

        # Isso permite que o endpoint de atualização funcione tanto para atualizações parciais (onde apenas alguns campos são fornecidos)
        # quanto para atualizações completas (onde todos os campos são fornecidos).

        # Se informado grupo, valida se é um grupo permitido (1, 2 ou 3)
        if funcionario_data.grupo:
            if funcionario_data.grupo not in [1, 2, 3]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Grupo deve ser 1 (Admin), 2 (Atendimento Balcão) ou 3 (Atendimento Caixa)"
                )

        # Armazena uma cópia dos dados antigos do funcionário, antes de atualizar, para fins de auditoria
        # Não pode manter referência com funcionário, para que a auditoria possa comparar
        # Por isso a cópia do __dict__
        dados_antigos_obj = funcionario.__dict__.copy() # Cópia rasa do dicionário de atributos do funcionário, para manter os dados antigos antes da atualização

        # Atualiza apenas os campos fornecidos
        update_data = funcionario_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(funcionario, field, value)

        db.commit()
        db.refresh(funcionario)

        # Depois de tudo executado, e antes do return, registra a ação na auditoria
        AuditoriaService.registrar_acao(
            db=db,
            funcionario_id=current_user.id,
            acao="UPDATE",
            recurso="funcionario",
            recurso_id=funcionario.id,
            dados_antigos=dados_antigos_obj, # Dicionário com os dados antigos do funcionário, antes da atualização
            dados_novos=funcionario, # Objeto SQLAlchemy atualizado, com os dados novos do funcionário
            request=request # Request completo para capturar IP e user agent, mesmo que seja um endpoint protegido por autenticação, pois o request ainda é necessário para pegar esses dados de contexto do cliente
        )

        return funcionario
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar funcionário: {str(e)}"
        )

@router.delete("/funcionario/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Funcionário"], summary="Remover funcionário - protegida por autenticação e grupo 1")
@limiter.limit(get_rate_limit("critical")) # o tempo em minutos do critical é: 5min
async def delete_funcionario(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(require_group([1]))
    ):
    """Exclui um funcionário existente"""
    try:
        funcionario = db.query(FuncionarioDB).filter(FuncionarioDB.id == id).first()

        if not funcionario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Funcionário não encontrado"
            )

        db.delete(funcionario)
        db.commit()

        # Depois de tudo executado, e antes do return, registra a ação na auditoria
        AuditoriaService.registrar_acao(
            db=db,
            funcionario_id=current_user.id,
            acao="DELETE",
            recurso="FUNCIONARIO",
            recurso_id=funcionario.id,
            dados_antigos=funcionario,
            dados_novos=None,
            request=request
        )

        return None # Pesquisar no chat, do por quê retornar None, ja que antes ele tinha feito "return funcionario".
        # Resposta: O código HTTP 204 significa literalmente "No Content" (Sem Conteúdo).
        # A especificação do protocolo HTTP diz que, quando um servidor responde com 204,
        # ele é terminantemente proibido de enviar um corpo na resposta (body)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao excluir funcionário: {str(e)}"
        )

# Comit: Coloca async antes dos def
# from domain.schemas.FuncionarioSchema import Funcionario -> removido, pois ele vai importar pelo create, update, response