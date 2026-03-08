from pydantic import BaseModel

class Funcionario(BaseModel):
    id_funcionario: int = None # Atributo opcional para o ID do funcionário, pois será gerado automaticamente pelo auto increment
    nome: str
    matricula: str
    cpf: str
    telefone: str = None
    grupo: int
    senha: str = None

# Nota sobre o id ser opcional, se fosse num model para retornar, o id seria obrigatório,
# mas como é um model para receber os dados, o id é opcional, pois ele será gerado automaticamente
# pelo auto increment do banco de dados.