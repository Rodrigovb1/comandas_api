# Aluno: Rodrigo Vaisam Bastos

from pydantic import BaseModel, ConfigDict
from typing import Optional

class FuncionarioCreate(BaseModel):
    nome: str
    matricula: str
    cpf: str
    telefone: str = None
    grupo: int
    senha: str = None

class FuncionarioUpdate(BaseModel):
    nome: Optional[str] = None
    matricula: Optional[str] = None
    cpf: Optional[str] = None
    telefone: Optional[str] = None
    grupo: Optional[int] = None
    senha: Optional[str] = None


class FuncionarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    matricula: str
    cpf: str
    telefone: Optional[str] = None
    grupo: int
    # não retorna senha por segurança, mesmo que seja um hash da senha,
    # não é recomendado retornar a senha em nenhuma situação, nem mesmo para fins de teste,
    # pois pode ser um risco de segurança.

# Comit: importou ConfigDict e Optional, fez o model de resposta, e fez o Response.

# Nota sobre o id ser opcional, se fosse num model para retornar, o id seria obrigatório,
# mas como é um model para receber os dados, o id é opcional, pois ele será gerado automaticamente
# pelo auto increment do banco de dados.