# Aluno: Rodrigo Vaisam Bastos

from fastapi import FastAPI
from settings import HOST, PORT, RELOAD
import uvicorn

# import das classes com as rotas/endpoints
from routers import FuncionarioRouter, ProdutoRouter, ClienteRouter
from routers import AuthRouter

# lifespan - ciclo de vida da aplicação
from infra import database
from contextlib import asynccontextmanager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # executa no startup
    print("API has started")
    # cria, caso não existam, as tabelas de todos os modelos que encontrar na aplicação (importados)
    await database.cria_tabelas()
    yield # ponto de execução da aplicação
    # executa no shutdown
    print("API is shutting down")

# cria a aplicação FastAPI com o contexto de vida
app = FastAPI(lifespan=lifespan)

# mapeamento das rotas/endpoints
app.include_router(FuncionarioRouter.router)
app.include_router(ClienteRouter.router)
app.include_router(ProdutoRouter.router)
app.include_router(AuthRouter.router)

# rota padrão para verificar se a API está rodando, e também para mostrar os links do Swagger UI e ReDoc
@app.get("/", tags=["Root"], status_code=200)
def root():
    return {"detail":"API Pastelaria", "Swagger UI": "http://127.0.0.1:8000/docs", "ReDoc": "http://127.0.0.1:8000/redoc" }

if __name__ == "__main__":
    uvicorn.run('main:app', host=HOST, port=int(PORT), reload=RELOAD)

# Comit: Colocado lifespan para criar as tabelas automaticamente ao iniciar a API,
# e também para mostrar mensagens no startup e shutdown da aplicação