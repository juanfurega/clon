"""Modelos SQLAlchemy para la base de datos PostgreSQL."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Source(Base):
    """Fuentes de datos (redes sociales, escritos personales, etc.)."""
    __tablename__ = 'sources'
    
    id = Column(Integer, primary_key=True)
    platform = Column(String(50), nullable=False)  # ej. "twitter", "instagram", "reflexion_personal"
    raw_file_path = Column(Text)  # ruta al archivo JSON/NDJSON crudo
    
    # Relación uno-a-muchos con TextEntry
    # relationship: permite navegar entre objetos relacionados sin escribir SQL manual
    # back_populates: crea la relación bidireccional para poder acceder desde ambos lados
    texts = relationship("TextEntry", back_populates="source")


class TextEntry(Base):
    """Textos individuales recolectados de las fuentes."""
    __tablename__ = 'texts'
    
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('sources.id'), nullable=False)
    content = Column(Text, nullable=False)  # sin límite de caracteres
    created_at = Column(DateTime, default=datetime.utcnow)  # sin paréntesis porque SQLAlchemy llama a la función
    processed = Column(Boolean, default=False)  # para saber si ya pasó por processing/
    embedding_id = Column(String(50), nullable=True)  # referencia al vector en Chroma
    
    # Relación con Source
    source = relationship("Source", back_populates="texts")
    # Relación con MentionedEntity
    mentioned_entities = relationship("MentionedEntity", back_populates="text")


class MentionedEntity(Base):
    """Entidades (personas) mencionadas en los textos para control de consentimiento."""
    __tablename__ = 'mentioned_entities'
    
    id = Column(Integer, primary_key=True)
    text_id = Column(Integer, ForeignKey('texts.id'), nullable=False)  # FK a tabla 'texts' (clase TextEntry)
    entity_name = Column(Text)  # nombre de la persona mencionada
    anonymized = Column(Boolean, default=False)  # si fue anonimizado en el procesamiento
    
    # Índice en text_id porque se consulta frecuentemente al procesar
    __table_args__ = (
        Index('idx_mentioned_entities_text_id', 'text_id'),
    )
    
    # Relación con TextEntry
    text = relationship("TextEntry", back_populates="mentioned_entities")
