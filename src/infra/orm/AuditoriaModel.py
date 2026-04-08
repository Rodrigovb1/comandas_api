from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from infra.database import Base
from infra.orm import FuncionarioModel

class AuditoriaDB(Base):
    """Modoelo para registrar audiotira de acessos e ações"""
    __tablename__ = "tb_auditoria"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    funcionario_id = Column(Integer, ForeignKey("tb_funcionario.id", ondelete="RESTRICT"), nullable=False) # ID do funcionário que realizou a ação
    acao = Column(String(50), nullable=False) # Ex: LOGIN, LOGOUT, CREATE, UPDATE, DELETE, CANCEL, etc
    recurso = Column(String(100), nullable=False) # Ex: comandas, recebimento, produto, etc
    recurso_id = Column(Integer, nullable=True) # ID do recurso afetado, se aplicável (ex: ID da comanda, ID do produto, etc)
    dados_antigos = Column(Text, nullable=True) # JSON com dados antes da alteração (ex: dados da comanda antes de ser atualizada)
    dados_novos = Column(Text, nullable=True) # JSON com dados depois da alteração (ex: dados da comanda depois de ser atualizada)
    ip_address = Column(String(45), nullable=True) # IP do cliente que realizou a ação
    user_agent = Column(Text, nullable=True) # User agent do navegador
    data_hora = Column(DateTime, nullable=False) # Data e hora da ação