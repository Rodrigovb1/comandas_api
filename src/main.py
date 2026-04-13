# Aluno: Rodrigo Vaisam Bastos
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from settings import HOST, PORT, RELOAD, CORS_ORIGINS
from infra.rate_limit import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import uvicorn

# import das classes com as rotas/endpoints
from routers import AuditoriaRouter
from routers import FuncionarioRouter, ProdutoRouter, ClienteRouter, AuthRouter
from routers import ComandaRouter
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

# Importar middleware personalizado para controle de acesso por IP
from infra.middleware.IPAccessMiddleware import IPAccessMiddleware
# Aplicar middleware de controle de acesso por IP, usando as origens permitidas do CORS_ORIGINS
app.add_middleware(IPAccessMiddleware, allowed_origins=CORS_ORIGINS)

# Configuração de CORS - Impede erros quando um Frontend moderno, tipo React/Vue, tentar acessar a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS, # Permitir os domínios especificados no .env ou todos (*)
    allow_credentials=False if "*" in CORS_ORIGINS else True, # Não permite credenciais (cookies, auth headers) se origem for *
    allow_methods=["GET", "POST", "PUT", "DELETE"], # Métodos específicos - * para permitir todos
    allow_headers=["Content-Type", "Authorization"], # Headers específicos - * para permitir todos
    expose_headers=["*"], # Expõe headers para debug
    max_age=600, # Cache de preflight por 10 minutos
)

# Configuração do rate limiter
app.state.limiter = limiter

# Registrar handler personalizado ANTES de incluir rotas
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
print ("Rate limit handler registrado")

# rota padrão para verificar se a API está rodando, e também para mostrar os links do Swagger UI e ReDoc
@app.get("/", tags=["Root"], status_code=200, summary="Informações da API - pública")
def root():
    return {"detail":"API Comandas", "Swagger UI": "http://127.0.0.1:8000/docs", "ReDoc": "http://127.0.0.1:8000/redoc" }

# Incluir as rotas/endpoints do FastAPI
app.include_router(FuncionarioRouter.router)
app.include_router(ClienteRouter.router)
app.include_router(ProdutoRouter.router)
app.include_router(AuthRouter.router)
app.include_router(ComandaRouter.router)
app.include_router(AuditoriaRouter.router)
app.include_router(HealthRouter.router)

if __name__ == "__main__":
    uvicorn.run('main:app', host=HOST, port=int(PORT), reload=RELOAD)