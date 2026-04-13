from sqlalchemy import Column, VARCHAR, DECIMAL, Integer, DateTime, ForeignKey
from infra.database import Base

class ComandaDB(Base):
    __tablename__ = "tb_comanda"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    comanda = Column(VARCHAR(100), nullable=False)
    data_hora = Column(DateTime, nullable=False)
    status = Column(Integer, nullable=False, default=0) # 0=aberta, 1=fechada, 2=cancelada
    cliente_id = Column(Integer, ForeignKey("tb_cliente.id", ondelete="RESTRICT"), nullable=True, default=None)
    funcionario_id = Column(Integer, ForeignKey("tb_funcionario.id", ondelete="RESTRICT"), nullable=False)
    # ondelete="RESTRICT"), para evitar que um cliente ou funcionário seja excluído se estiver associado a uma comanda. Se for necessário excluir um cliente ou funcionário, primeiro será necessário atualizar ou excluir as comandas associadas a eles.

class ComandaProdutoDB(Base):
    __tablename__ = "tb_comanda_produto"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    comanda_id = Column(Integer, ForeignKey("tb_comanda.id", ondelete="RESTRICT"), nullable=False)
    produto_id = Column(Integer, ForeignKey("tb_produto.id", ondelete="RESTRICT"), nullable=False)
    funcionario_id = Column(Integer, ForeignKey("tb_funcionario.id", ondelete="RESTRICT"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    valor_unitario = Column(DECIMAL(10, 2), nullable=False)