from typing import List, Optional
from pydantic import BaseModel


# --------------------
# Users
# --------------------
class UserCreate(BaseModel):
    name: str


class UserOut(BaseModel):
    id: int
    name: str
    score: int

    class Config:
        orm_mode = True


# --------------------
# Categories
# --------------------
class CategoryCreate(BaseModel):
    name: str


class CategoryOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


# --------------------
# Questions
# --------------------
class QuestionCreate(BaseModel):
    text: str
    option_1: str
    option_2: str
    option_3: str
    option_4: str
    correct_option: int
    category_id: int


class QuestionOut(BaseModel):
    id: int
    text: str
    option_1: str
    option_2: str
    option_3: str
    option_4: str
    category_id: int

    class Config:
        orm_mode = True


# --------------------
# Queue
# --------------------
class QueueJoin(BaseModel):
    user_id: int
    stake: int


class QueueJoinResponse(BaseModel):
    message: str
    game_id: Optional[int] = None


# --------------------
# Game
# --------------------
class GamePlayerOut(BaseModel):
    user_id: int
    name: str
    current_game_score: int

    class Config:
        orm_mode = True


class GameOut(BaseModel):
    id: int
    status: str
    stake: int
    winner_user_id: Optional[int]
    current_turn_user_id: Optional[int]
    current_question_id: Optional[int]
    players: List[GamePlayerOut]

    class Config:
        orm_mode = True


class CurrentQuestionOut(BaseModel):
    game_id: int
    question_id: int
    text: str
    option_1: str
    option_2: str
    option_3: str
    option_4: str
    current_turn_user_id: int


class AnswerIn(BaseModel):
    user_id: int
    selected_option: int


class AnswerOut(BaseModel):
    message: str
    is_correct: bool
    awarded_score: int
    player_score: int
    game_status: str
    winner_user_id: Optional[int]
    next_turn_user_id: Optional[int]

class AnswerSubmit(BaseModel):
    user_id: int
    selected_option: int
