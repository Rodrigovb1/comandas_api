from infra import database
from sqlalchemy import Column, VARCHAR, CHAR, Integer

# Aqui estamos definindo chave primária, auto incremento, definição de índice, e as colunas, com seus tipos e restrições.
# O SQLAlchemy tem uma série de tipos de dados que podemos usar para definir as colunas do banco de dados,
# como Integer, String, Float, DateTime, etc. Além disso, podemos usar argumentos como nullable=False para indicar que a coluna não pode ser nula,
# unique=True para garantir que os valores sejam únicos, e primary_key=True para definir a chave primária da tabela.

# Também temos o atributo __tablename__, que é obrigatório para indicar o nome da tabela.
# O nome da classe pode ser diferente do nome da tabela, mas é comum usar um nome semelhante para facilitar a leitura do código.

# ORM
class ClienteDB(database.Base):
    __tablename__ = 'tb_cliente'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nome = Column(VARCHAR(100), nullable=False)
    cpf = Column(CHAR(11), unique=True, nullable=False, index=True)
    telefone = Column(CHAR(11), nullable=False)

    def __init__(self, id, nome, cpf, telefone):
        self.id = id
        self.nome = nome
        self.cpf = cpf
        self.telefone = telefone
