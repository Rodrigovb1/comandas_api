from dotenv import load_dotenv, find_dotenv
import os

# localiza o arquivo de .env
dotenv_file = find_dotenv()

# Carrega o arquivo .env
load_dotenv(dotenv_file)

# Configurações da API
HOST = os.getenv("HOST", "0.0.0.0")
PORT = os.getenv("PORT", "8000")
RELOAD = os.getenv("RELOAD", True)

# Configuração banco de dados
DB_SGDB = os.getenv("DB_SGDB")
DB_NAME = os.getenv("DB_NAME")
# Caso seja diferente do sqlite
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

# Ajuste STR_DATABASE conforme gerenciador escolhido
if DB_SGDB == "sqlite":
    # Habilitar chaves estrangeiras - integridade referencial - pragma
    STR_DATABASE = f"sqlite:///{DB_NAME}.db?foreign_keys=1"
elif DB_SGDB == "mysql":
    import pymysql
    STR_DATABASE = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?charset=utf8mb4"
elif DB_SGDB == "mssql":
    import pymssql
    STR_DATABASE = f"mssql+pymssql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?charset=utf8"
else: # SQLite
    STR_DATABASE = f"sqlite:///apiDatabase.db?foreign_keys=1"

# CONFIGURAÇÕES JWT
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))