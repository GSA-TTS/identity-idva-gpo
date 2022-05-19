"""
CRUD operations for gpo µservice
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models, schemas


def get_letters(
    session: Session, skip: int = 0, limit: int = 1000
) -> list[models.Letter]:
    """
    get letters
    """
    return (
        session.execute(select(models.Letter).offset(skip).limit(limit)).scalars().all()
    )


def delete_letters(session: Session, letters: list[models.Letter]):
    """
    delete letters by id
    """

    for letter in letters:
        session.delete(letter)

    session.commit()
    return


def create_letter(session: Session, letter: schemas.LetterCreate) -> models.Letter:
    """
    create letter
    """
    db_item = models.Letter(**letter.dict())
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item
