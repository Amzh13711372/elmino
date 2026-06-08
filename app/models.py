from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    score = Column(Integer, default=0)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)

    option_1 = Column(String, nullable=False)
    option_2 = Column(String, nullable=False)
    option_3 = Column(String, nullable=False)
    option_4 = Column(String, nullable=False)

    correct_option = Column(Integer, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    category = relationship("Category")


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    stake = Column(Integer, nullable=False)
    status = Column(String, default="waiting")
    winner_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    current_turn_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    turn_deadline = Column(DateTime(timezone=True), nullable=True)

    current_question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    players = relationship("GamePlayer", back_populates="game")
    current_question = relationship("Question")
    winner = relationship("User", foreign_keys=[winner_user_id])


class GamePlayer(Base):
    __tablename__ = "game_players"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    current_game_score = Column(Integer, default=0)
    rank = Column(Integer, nullable=True)

    game = relationship("Game", back_populates="players")
    user = relationship("User")


class QueueEntry(Base):
    __tablename__ = "queue_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stake = Column(Integer, nullable=False)
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User")

