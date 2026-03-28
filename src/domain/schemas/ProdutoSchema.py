# Aluno: Rodrigo Vaisam Bastos

from pydantic import BaseModel, ConfigDict
from typing import Optional

class ProdutoCreate(BaseModel):
    nome: str
    descricao: str
    foto: bytes = None
    valor_unitario: float

class ProdutoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    foto: Optional[bytes] = None
    valor_unitario: Optional[float] = None


class ProdutoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: str
    foto: Optional[bytes] = None
    valor_unitario: float

# Criação de classe pública para resposta sem o id e valor, está sendo usada no endpoint público
class ProdutoPublicoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nome: str
    descricao: str
    foto: Optional[bytes] = None

# Comit: importou ConfigDict e Optional, fez o model de resposta, e fez o Response.
# Também tirei o id, pois o auto increment já cuida rs