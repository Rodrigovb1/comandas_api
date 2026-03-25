# Aluno: Rodrigo Vaisam Bastos

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
# Import das classes relacionadas com aos schemas e persistência dos dados

# Domain Schemas
from domain.schemas.FuncionarioSchema import (
    FuncionarioCreate,
    FuncionarioUpdate,
    FuncionarioResponse
)

# Infra ORM, Database
from infra.orm.FuncionarioModel import FuncionarioDB
from infra.database import get_db
from infra.security import get_password_hash

# Ajustes nas rotas para inclusão dos comandas ORM
router = APIRouter()

# Criar as rotas/endpoints: GET, POST, PUT, DELETE

# @router.get("/funcionario/", tags=["Funcionário"], status_code=200)
# async def get_funcionario():
#     return {"msg": "funcionario get todos executado"}

@router.get("/funcionario/", response_model=List[FuncionarioResponse], tags=["Funcionário"], status_code=status.HTTP_200_OK)
async def get_funcionarios(db: Session = Depends(get_db)):
    """Retorna todos os funcionários"""
    try:
        funcionarios = db.query(FuncionarioDB).all()
        return funcionarios
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar funcionários: {str(e)}"
        )

# @router.get("/funcionario/{id}", tags=["Funcionário"], status_code=200)
# async def get_funcionario(id: int):
#     return {"msg": "funcionario get um executado"}

@router.get("/funcionario/{id}", response_model=FuncionarioResponse, tags=["Funcionário"], status_code=status.HTTP_200_OK)
async def get_funcionario(id: int, db: Session = Depends(get_db)):
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

# @router.post("/funcionario/", tags=["Funcionário"], status_code=200)
# async def post_funcionario(corpo: FuncionarioCreate): # Recebe um objeto do tipo FuncionarioCreate no corpo da requisição
#     return {"msg": "funcionario post executado", "nome": corpo.nome, "cpf": corpo.cpf, "telefone": corpo.telefone}

# • O verbo post será utilizado para criar um novo funcionário.
# • Conforme já vimos anteriormente, a entrada dos dados será realizada através de um JSON enviado no corpo da requisição,
# sendo passada para dentro da nossa classe através da classe FuncionarioCreate, herdando de BaseModel.
@router.post("/funcionario/", response_model=FuncionarioResponse, tags=["Funcionário"], status_code=status.HTTP_201_CREATED)
async def post_funcionario(funcionario_data: FuncionarioCreate, db: Session = Depends(get_db)):
    """Cria um novo funcionário"""
    try:
        # verifica se já existe um funcionário com este CPF
        existing_funcionario = db.query(FuncionarioDB).filter(FuncionarioDB.cpf == funcionario_data.cpf).first()

        if existing_funcionario:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe um funcionário com este CPF"
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

        return novo_funcionario
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar funcionário: {str(e)}"
        )

# @router.put("/funcionario/{id}", tags=["Funcionário"], status_code=200)
# async def put_funcionario(id: int, corpo: FuncionarioCreate):
#     return {"msg": "funcionario put executado", "nome": corpo.nome, "cpf": corpo.cpf, "telefone": corpo.telefone} # Só 3 parâmetros pois é só pra testar leitura

# Mesma coisa do post, a diferença aqui é que tem que especificar o id.
@router.put("/funcionario/{id}", response_model=FuncionarioResponse, tags=["Funcionário"], status_code=status.HTTP_200_OK)
async def put_funcionario(id: int, funcionario_data: FuncionarioUpdate, db: Session = Depends(get_db)):
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
        # Os if de python usam um conceito chamado Truthy e Falsy, ou seja, eles avaliam o valor da variável como verdadeiro ou falso.
        # Falsy: None, False, 0, 0.0, '', [], {}, set()
        # Truthy: Qualquer coisa que contenha algum dado. Exemplos: "senha123", 1, [1, 2], True.
        
        # Nesse caso, se a senha for fornecida (Não None, não vazia) o if será executado.
        # Se a senha não for fornecida, o if é ignorado, e a senha do funcionário permanecerá inalterada.

        # Isso permite que o endpoint de atualização funcione tanto para atualizações parciais (onde apenas alguns campos são fornecidos)
        # quanto para atualizações completas (onde todos os campos são fornecidos).

        # Atualiza apenas os campos fornecidos
        update_data = funcionario_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(funcionario, field, value)

        db.commit()
        db.refresh(funcionario)

        return funcionario
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar funcionário: {str(e)}"
        )

# @router.delete("/funcionario/{id}", tags=["Funcionário"], status_code=200)
# async def delete_funcionario(id: int):
#     return {"msg": "funcionario delete executado", "id":id}

@router.delete("/funcionario/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Funcionário"], summary="Remover funcionário")
async def delete_funcionario(id: int, db: Session = Depends(get_db)):
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