from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from settings import STR_DATABASE, ASYNC_STR_DATABASE
from sqlalchemy.orm import Session

# cria o engine do banco de dados
engine = create_engine(STR_DATABASE, echo=True)
# OBS: Se incluirmos o argumento echo=True, passaremos a ver no terminal os comandos SQL gerados pelo framework, algo que pode ser útil para depuração.

# cria o engine assíncrono do banco de dados
async_engine = create_async_engine(ASYNC_STR_DATABASE, echo=True)

# cria a sessão síncrona do banco de dados (mantida para compatibilidade com rotas síncronas)
Session = sessionmaker(bind=engine, autocommit=False, autoflush=True)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False)

# para trabalhar com tabelas
Base = declarative_base()

# cria, caso não existam, as tabelas de todos os modelos que encontrar na aplicação (importados)
async def cria_tabelas():
    Base.metadata.create_all(engine)
# Realiza somente a criação, caso a estrutura da tabela sofra alteração, terá que ser editada diretamente na base de dados,
# ou, se for possível, excluída e criada novamente ao reiniciar a API.

# dependência para injetar a sessão do banco de dados nas rotas
def get_db():
    db_session = Session()
    try:
        yield db_session
    finally:
        db_session.close()

# dependência para injetar a sessão assíncrona do banco de dados nas rotas
async def get_async_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        # except Exception as e:
        #     await session.rollback()
        #     raise e
        finally:
            await session.close()