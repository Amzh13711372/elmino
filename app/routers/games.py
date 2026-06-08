from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter()

@router.post("/games/{game_id}/answer")
def submit_answer(
    game_id: int,
    payload: schemas.AnswerSubmit,
    db: Session = Depends(get_db)
):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if game.status != "active":
        raise HTTPException(status_code=400, detail="Game is not active")

    if game.current_turn_user_id != payload.user_id:
        raise HTTPException(status_code=400, detail="It is not your turn")

    game_player = db.query(models.GamePlayer).filter(
        models.GamePlayer.game_id == game_id,
        models.GamePlayer.user_id == payload.user_id
    ).first()

    if not game_player:
        raise HTTPException(status_code=404, detail="Player not found in this game")

    question = db.query(models.Question).filter(
        models.Question.id == game.current_question_id
    ).first()

    if not question:
        raise HTTPException(status_code=404, detail="Current question not found")

    is_correct = payload.selected_option == question.correct_option

    if is_correct:
        game_player.current_game_score += 1

    players = db.query(models.GamePlayer).filter(
        models.GamePlayer.game_id == game.id
    ).all()

    player_ids = [p.user_id for p in players]

    current_index = player_ids.index(game_player.user_id)
    next_index = (current_index + 1) % len(player_ids)
    next_turn_user_id = player_ids[next_index]

    next_question = db.query(models.Question).filter(
        models.Question.id == game.current_question_id + 1
    ).first()

    if next_question:
        game.current_question_id = next_question.id
        game.current_turn_user_id = next_turn_user_id
    else:
        game.status = "finished"
        winner = max(players, key=lambda p: p.current_game_score)
        game.winner_user_id = winner.user_id

    db.commit()
    db.refresh(game)

    return {
        "message": "Answer submitted successfully",
        "is_correct": is_correct,
        "your_score": game_player.current_game_score,
        "game_status": game.status,
        "winner_user_id": game.winner_user_id,
        "next_turn_user_id": game.current_turn_user_id,
        "current_question_id": game.current_question_id,
    }

@router.get("/games/{game_id}")
def get_game(game_id: int, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    players = db.query(models.GamePlayer).filter(
        models.GamePlayer.game_id == game.id
    ).all()

    return {
        "id": game.id,
        "status": game.status,
        "stake": game.stake,
        "current_turn_user_id": game.current_turn_user_id,
        "current_question_id": game.current_question_id,
        "winner_user_id": game.winner_user_id,
        "players": [
            {
                "user_id": p.user_id,
                "score": p.current_game_score
            }
            for p in players
        ]
    }
