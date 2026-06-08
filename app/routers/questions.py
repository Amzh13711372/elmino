from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models, schemas

router = APIRouter(prefix="/questions", tags=["Questions"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=schemas.QuestionOut)
def create_question(question: schemas.QuestionCreate, db: Session = Depends(get_db)):
    category = db.query(models.Category).filter(
        models.Category.id == question.category_id
    ).first()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    new_question = models.Question(
        text=question.text,
        option_1=question.option_1,
        option_2=question.option_2,
        option_3=question.option_3,
        option_4=question.option_4,
        correct_option=question.correct_option,
        category_id=question.category_id,
    )

    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return new_question


@router.get("/", response_model=list[schemas.QuestionOut])
def list_questions(db: Session = Depends(get_db)):
    return db.query(models.Question).all()
