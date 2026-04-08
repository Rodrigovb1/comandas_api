# Aluno: Rodrigo Vaisam Bastos

from fastapi import FastAPI
from infra.orm.AuditoriaModel import AuditoriaDB
from settings import HOST, PORT, RELOAD
from infra.rate_limit import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import uvicorn

# import das classes com as rotas/endpoints
from routers import AuditoriaRouter
from routers import FuncionarioRouter, ProdutoRouter, ClienteRouter, AuthRouter
from routers import HealthRouter

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

# Configuração do rate limiter
app.state.limiter = limiter

# Registrar handler personalizado ANTES de incluir rotas
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# rota padrão para verificar se a API está rodando, e também para mostrar os links do Swagger UI e ReDoc
@app.get("/", tags=["Root"], status_code=200, summary="Informações da API - pública")
def root():
    return {"detail":"API Comandas", "Swagger UI": "http://127.0.0.1:8000/docs", "ReDoc": "http://127.0.0.1:8000/redoc" }

# Incluir as rotas/endpoints do FastAPI
app.include_router(FuncionarioRouter.router)
app.include_router(ClienteRouter.router)
app.include_router(ProdutoRouter.router)
app.include_router(AuthRouter.router)
app.include_router(AuditoriaRouter.router)
app.include_router(HealthRouter.router)

if __name__ == "__main__":
    uvicorn.run('main:app', host=HOST, port=int(PORT), reload=RELOAD)