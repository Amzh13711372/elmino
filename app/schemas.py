from pydantic import BaseModel
from typing import Optional, List


class UserCreate(BaseModel):
    name: str
    phone: str


class UserOut(BaseModel):
    id: int
    name: str
    phone: str
    score: int

    class Config:
        orm_mode = True


class CategoryCreate(BaseModel):
    name: str


class CategoryOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class QuestionCreate(BaseModel):
    category_id: int
    text: str
    correct_answer: str
    options: str


class QuestionOut(BaseModel):
    id: int
    category_id: int
    text: str
    correct_answer: str
    options: str

    class Config:
        orm_mode = True


class QueueJoinRequest(BaseModel):
    user_id: int
    stake: int


class QueueJoinResponse(BaseModel):
    message: str
    game_id: Optional[int] = None
    status: str


class GamePlayerOut(BaseModel):
    user_id: int
    current_game_score: int
    rank: Optional[int] = None

    class Config:
        orm_mode = True


class GameOut(BaseModel):
    id: int
    stake: int
    status: str
    winner_user_id: Optional[int] = None
    current_turn_user_id: Optional[int] = None
    turn_deadline: Optional[str] = None
    players: List[GamePlayerOut]

    class Config:
        orm_mode = True


class AnswerRequest(BaseModel):
    user_id: int
    answer: str

