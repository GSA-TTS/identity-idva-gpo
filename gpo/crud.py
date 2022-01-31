from sqlalchemy.orm import Session

from . import models, schemas


def get_letters(db: Session, skip: int = 0, limit: int = 1000):
    return db.query(models.Letter).offset(skip).limit(limit).all()


def delete_letters(db: Session, letters: models.Letter):
    result = (
        db.query(models.Letter)
        .filter(models.Letter.id.in_(map(lambda x: x.id, letters)))
        .delete()
    )
    db.commit()
    return result


def create_letter(db: Session, letter: schemas.LetterCreate):
    db_item = models.Letter(**letter.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
