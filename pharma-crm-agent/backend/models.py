# backend/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()


class Interaction(Base):
    """SQLAlchemy model for the interactions table."""
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    hcp_name = Column(String(255), nullable=False)
    interaction_type = Column(String(100))
    duration = Column(Integer)
    sentiment = Column(String(50))
    topics_discussed = Column(Text)
    outcomes = Column(Text)
    follow_up_actions = Column(Text)
    attendees = Column(Text)
    thread_id = Column(String(255), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatSession(Base):
    """SQLAlchemy model for chat sessions."""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    """SQLAlchemy model for chat messages."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer)
    role = Column(String(20))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
