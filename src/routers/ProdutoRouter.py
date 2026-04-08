# Aluno: Rodrigo Vaisam Bastos
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

# Domain Schemas
from domain.schemas.AuthSchema import FuncionarioAuth
from domain.schemas.ProdutoSchema import ProdutoCreate, ProdutoPublicoResponse, ProdutoUpdate, ProdutoResponse

# Infra ORM
from infra.orm.ProdutoModel import ProdutoDB
from infra.database import get_db
from infra.dependencies import get_current_active_user, require_group

# Limiter e AuditoriaService
from services.AuditoriaService import AuditoriaService
from infra.rate_limit import limiter, get_rate_limit

router = APIRouter()

@router.get("/produto/publico", response_model=List[ProdutoPublicoResponse], tags=["Produto"], status_code=status.HTTP_200_OK)
@limiter.limit(get_rate_limit("moderate"))
async def get_produtos_publicos(
    request: Request, # Mesmo que seja um endpoint público, o request ainda é necessário para pegar esses dados de contexto (IP e user agent) do cliente
    db: Session = Depends(get_db)):
    """Retorna todos os produtos públicos, sem necessidade de autenticação"""
    try:
        produtos = db.query(ProdutoDB).all()
        return produtos
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar produtos: {str(e)}"
        )
    
@router.get("/produto/", response_model=List[ProdutoResponse], tags=["Produto"], status_code=status.HTTP_200_OK)
async def get_produtos(
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(get_current_active_user)
):
    """Retorna todos os produtos"""
    try:
        produtos = db.query(ProdutoDB).all()
        return produtos
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar produtos: {str(e)}"
        )

@router.get("/produto/{id}", response_model=ProdutoResponse, tags=["Produto"], status_code=status.HTTP_200_OK)
async def get_produto(
    id: int,
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(get_current_active_user)
):
    """Retorna um produto específico"""
    try:
        produto = db.query(ProdutoDB).filter(ProdutoDB.id == id).first()
        if not produto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto não encontrado"
            )
        return produto
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar produto: {str(e)}"
        )

@router.post("/produto/", response_model=ProdutoResponse, tags=["Produto"], status_code=status.HTTP_201_CREATED)
@limiter.limit(get_rate_limit("restrictive")) # o tempo em minutos do restrictive é: 20min
async def post_produto(
    request: Request,
    produto_data: ProdutoCreate,
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(require_group([1]))
):
    """Cria um novo produto"""
    try:
        # verifica se já existe um produto com o mesmo nome, para evitar duplicidade
        existing_produto = db.query(ProdutoDB).filter(ProdutoDB.nome == produto_data.nome).first()

        if existing_produto:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe um produto com este nome"
            )

    
        # Cria o novo produto
        novo_produto = ProdutoDB(
            id=None,  # O ID será gerado automaticamente pelo banco de dados
            nome=produto_data.nome,
            descricao=produto_data.descricao,
            foto=produto_data.foto,
            valor_unitario=produto_data.valor_unitario
        )

        db.add(novo_produto)
        db.commit()
        db.refresh(novo_produto)

        # Depois de tudo executado, e antes do return, registra a ação na auditoria
        AuditoriaService.registrar_acao(
            db=db,
            funcionario_id=current_user.id,
            acao="CREATE",
            recurso="PRODUTO",
            recurso_id=novo_produto.id,
            dados_antigos=None, # None, pois não existe um estado anterior do funcionário, já que ele está sendo criado agora
            dados_novos=novo_produto, # Objeto SQLAlchemy, com dados novos
            request=request # Request completo para capturar IP e user agent, mesmo que seja um endpoint protegido por autenticação, pois o request ainda é necessário para pegar esses dados de contexto do cliente
        )

        return novo_produto
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar produto: {str(e)}"
        )

@router.put("/produto/{id}", response_model=ProdutoResponse, tags=["Produto"], status_code=status.HTTP_200_OK)
@limiter.limit(get_rate_limit("restrictive")) # o tempo em minutos do restrictive é: 20min
async def put_produto(
    request: Request,
    id: int,
    produto_data: ProdutoUpdate,
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(require_group([1]))
):
    """Atualiza um produto existente"""
    try:
        produto = db.query(ProdutoDB).filter(ProdutoDB.id == id).first()

        if not produto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto não encontrado"
            )

        # Verifica se está tentando atualizar o nome para um valor que já existe em outro produto
        if produto_data.nome and produto_data.nome != produto.nome:
            existing_produto = db.query(ProdutoDB).filter(ProdutoDB.nome == produto_data.nome).first()

            if existing_produto:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Já existe um produto com este nome"
                )
            
        # Armazena uma cópia dos dados antigos do produto, antes de atualizar, para fins de auditoria
        # Não pode manter referência com produto, para que a auditoria possa comparar
        # Por isso a cópia do __dict__
        dados_antigos_obj = produto.__dict__.copy() # Cópia rasa do dicionário de atributos do produto, para manter os dados antigos antes da atualização
        
        # Atualiza apenas os campos fornecidos
        update_data = produto_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(produto, field, value)

        db.commit()
        db.refresh(produto)

        # Depois de tudo executado, e antes do return, registra a ação na auditoria
        AuditoriaService.registrar_acao(
            db=db,
            funcionario_id=current_user.id,
            acao="UPDATE",
            recurso="PRODUTO",
            recurso_id=produto.id,
            dados_antigos=dados_antigos_obj, # Dicionário com os dados antigos do produto, antes da atualização
            dados_novos=produto, # Objeto SQLAlchemy atualizado, com os dados novos do produto
            request=request # Request completo para capturar IP e user agent, mesmo que seja um endpoint protegido por autenticação, pois o request ainda é necessário para pegar esses dados de contexto do cliente
        )

        return produto
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar produto: {str(e)}"
        )

@router.delete("/produto/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Produto"], summary="Remover produto")
@limiter.limit(get_rate_limit("critical")) # o tempo em minutos do critical é: 5min
async def delete_produto(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(require_group([1]))
):
    """Exclui um produto existente"""
    try:
        produto = db.query(ProdutoDB).filter(ProdutoDB.id == id).first()

        if not produto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto não encontrado"
            )

        db.delete(produto)
        db.commit()

        # Depois de tudo executado, e antes do return, registra a ação na auditoria
        AuditoriaService.registrar_acao(
            db=db,
            funcionario_id=current_user.id,
            acao="DELETE",
            recurso="PRODUTO",
            recurso_id=produto.id,
            dados_antigos=produto,
            dados_novos=None,
            request=request
        )

        return None # Pesquisar no chat, do por quê retornar None, ja que antes ele tinha feito "return produto".
        # Resposta: O código HTTP 204 significa literalmente "No Content" (Sem Conteúdo).
        # A especificação do protocolo HTTP diz que, quando um servidor responde com 204,
        # ele é terminantemente proibido de enviar um corpo na resposta (body)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao excluir produto: {str(e)}"
        )