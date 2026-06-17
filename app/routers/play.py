from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app import models, schemas

router = APIRouter(prefix="/games", tags=["Play"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def pick_next_player(game: models.Game):
    players = sorted(game.players, key=lambda p: p.user_id)

    if not players:
        return None

    if game.current_turn_user_id is None:
        return players[0].user_id

    current_index = None
    for i, player in enumerate(players):
        if player.user_id == game.current_turn_user_id:
            current_index = i
            break

    if current_index is None:
        return players[0].user_id

    next_index = (current_index + 1) % len(players)
    return players[next_index].user_id


def pick_question(db: Session):
    question = db.query(models.Question).first()
    if not question:
        raise HTTPException(status_code=404, detail="No question found")
    return question


@router.get("/{game_id}", response_model=schemas.GameOut)
def get_game(game_id: int, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    players_out = []
    for gp in game.players:
        players_out.append(
            schemas.GamePlayerOut(
                user_id=gp.user_id,
                name=gp.user.name,
                current_game_score=gp.current_game_score,
            )
        )

    return schemas.GameOut(
        id=game.id,
        status=game.status,
        stake=game.stake,
        winner_user_id=game.winner_user_id,
        current_turn_user_id=game.current_turn_user_id,
        current_question_id=game.current_question_id,
        players=players_out,
    )


@router.get("/{game_id}/question", response_model=schemas.CurrentQuestionOut)
def get_current_question(game_id: int, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if game.status != "active":
        raise HTTPException(status_code=400, detail="Game is not active")

    if game.current_question_id is None:
        question = pick_question(db)
        game.current_question_id = question.id

        if game.current_turn_user_id is None:
            next_turn = pick_next_player(game)
            game.current_turn_user_id = next_turn
            game.turn_deadline = datetime.now(timezone.utc) + timedelta(seconds=30)

        db.commit()
        db.refresh(game)

    question = db.query(models.Question).filter(models.Question.id == game.current_question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    return schemas.CurrentQuestionOut(
        game_id=game.id,
        question_id=question.id,
        text=question.text,
        option_1=question.option_1,
        option_2=question.option_2,
        option_3=question.option_3,
        option_4=question.option_4,
        current_turn_user_id=game.current_turn_user_id,
    )


@router.post("/{game_id}/answer", response_model=schemas.AnswerOut)
def answer_question(game_id: int, payload: schemas.AnswerIn, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if game.status != "active":
        raise HTTPException(status_code=400, detail="Game is not active")

    if game.current_question_id is None:
        raise HTTPException(status_code=400, detail="No active question for this game")

    if game.current_turn_user_id != payload.user_id:
        raise HTTPException(status_code=400, detail="It is not this user's turn")

    if payload.selected_option not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="selected_option must be between 1 and 4")

    question = db.query(models.Question).filter(models.Question.id == game.current_question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    game_player = (
        db.query(models.GamePlayer)
        .filter(
            models.GamePlayer.game_id == game.id,
            models.GamePlayer.user_id == payload.user_id,
        )
        .first()
    )
    if not game_player:
        raise HTTPException(status_code=404, detail="Player not found in game")

    is_correct = payload.selected_option == question.correct_option

    if is_correct:
        awarded_score = 100
    else:
        awarded_score = -50

    game_player.current_game_score += awarded_score

    winner_user_id = None
    next_turn_user_id = None

    if game_player.current_game_score >= 500:
        game.status = "finished"
        game.winner_user_id = game_player.user_id
        winner_user_id = game_player.user_id
        game.current_question_id = None
        game.current_turn_user_id = None
        game.turn_deadline = None
    else:
        next_turn_user_id = pick_next_player(game)
        game.current_turn_user_id = next_turn_user_id
        game.turn_deadline = datetime.now(timezone.utc) + timedelta(seconds=30)

        next_question = pick_question(db)
        game.current_question_id = next_question.id

    db.commit()
    db.refresh(game)
    db.refresh(game_player)

    return schemas.AnswerOut(
        message="Answer submitted successfully",
        is_correct=is_correct,
        awarded_score=awarded_score,
        player_score=game_player.current_game_score,
        game_status=game.status,
        winner_user_id=winner_user_id,
        next_turn_user_id=next_turn_user_id,
    )

