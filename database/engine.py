"""Configuración de conexión a PostgreSQL."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
# No hardcodeamos credenciales por seguridad y flexibilidad (distintos entornos)
load_dotenv()

# DATABASE_URL se lee desde variable de entorno
# Formato: postgresql://usuario:password@localhost:5432/nombre_db
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL no está definida en variables de entorno")

# create_engine: crea el motor de conexión a PostgreSQL
# echo=False para no ver SQL en consola (cambiar a True para debug)
engine = create_engine(DATABASE_URL, echo=False)

# SessionLocal: fábrica de sesiones para interactuar con la DB
# autocommit=False: requerimos commit explícito (mejor control de transacciones)
# autoflush=False: SQLAlchemy no flush automático (control manual cuándo escribir a DB)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Obtener sesión de base de datos (para uso con FastAPI/dependencias)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Inicializar la base de datos creando todas las tablas.
    
    Base.metadata.create_all(engine) crea las tablas definidas en models.py
    si no existen. Es idempotente: si la tabla ya existe, no hace nada.
    """
    from .models import Base
    Base.metadata.create_all(bind=engine)
