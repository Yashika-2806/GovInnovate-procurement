from sqlalchemy import create_engine, Column, String, JSON
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./procurement.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class WorkflowModel(Base):
    __tablename__ = "workflows"
    workflow_id = Column(String, primary_key=True)
    state = Column(String)
    context = Column(JSON) # Stores canonical models, evidence, etc

class AuditModel(Base):
    __tablename__ = "audits"
    audit_id = Column(String, primary_key=True)
    workflow_id = Column(String)
    event_type = Column(String)
    data = Column(JSON)

Base.metadata.create_all(bind=engine)
