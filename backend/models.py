from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    id         = Column(Integer, primary_key=True, index=True)
    email      = Column(String, unique=True, index=True, nullable=False)
    username   = Column(String, nullable=False)
    hashed_pw  = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    entries    = relationship("WellbeingEntry", back_populates="user")
    journals   = relationship("JournalEntry", back_populates="user")
    todos      = relationship("Todo", back_populates="user")
    tracking   = relationship("TrackingEntry", back_populates="user")

class WellbeingEntry(Base):
    __tablename__ = "wellbeing_entries"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    mood        = Column(Integer)
    energy      = Column(Integer)
    stress      = Column(Integer)
    sleep_hours = Column(Float)
    notes       = Column(Text, default="")
    embedding   = Column(Vector(384), nullable=True)  # for semantic search
    created_at  = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="entries")

class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    title      = Column(String, nullable=False)
    body       = Column(Text, default="")
    mood       = Column(String, default="neutral")
    embedding  = Column(Vector(384), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="journals")

class Todo(Base):
    __tablename__ = "todos"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    title      = Column(String, nullable=False)
    category   = Column(String, default="Wellness")
    priority   = Column(String, default="medium")
    done       = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="todos")

class TrackingEntry(Base):
    __tablename__ = "tracking_entries"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    date        = Column(String, nullable=False)  # YYYY-MM-DD
    sleep       = Column(Float, default=0)
    exercise    = Column(Float, default=0)
    water       = Column(Integer, default=0)
    heart_rate  = Column(Integer, default=0)
    meditation  = Column(Float, default=0)
    created_at  = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="tracking")
