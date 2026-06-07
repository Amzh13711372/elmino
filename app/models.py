from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    score = Column(Integer, default=0, nullable=False)

    wallet = relationship("Wallet", back_populates="user", uselist=False)
    queue_entries = relationship("GameQueueEntry", back_populates="user")
    game_players = relationship("GamePlayer", back_populates="user")


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    balance = Column(Integer, default=0, nullable=False)

    user = relationship("User", back_populates="wallet")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    questions = relationship("Question", back_populates="category")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    text = Column(String, nullable=False)
    correct_answer = Column(String, nullable=False)
    options = Column(String, nullable=False)

    category = relationship("Category", back_populates="questions")


class GameQueueEntry(Base):
    __tablename__ = "game_queue_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stake = Column(Integer, nullable=False)
    status = Column(String, default="waiting", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="queue_entries")


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    stake = Column(Integer, nullable=False)
    status = Column(String, default="waiting", nullable=False)
    winner_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    current_turn_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    turn_deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    players = relationship("GamePlayer", back_populates="game")


class GamePlayer(Base):
    __tablename__ = "game_players"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    current_game_score = Column(Integer, default=0, nullable=False)
    rank = Column(Integer, nullable=True)

    game = relationship("Game", back_populates="players")
    user = relationship("User", back_populates="game_players")

