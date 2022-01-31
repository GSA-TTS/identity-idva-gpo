"""
GPO Microservice FastAPI Web App.
"""

import datetime
from io import StringIO
import logging
import math
from fastapi import FastAPI, Depends, Response
import paramiko
import csv
from starlette_prometheus import metrics, PrometheusMiddleware
from gpo import settings
from sqlalchemy.orm import Session
from base64 import b64decode

from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics/", metrics)

logging.getLogger().setLevel(settings.LOG_LEVEL)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def write(file, letters):
    writer = csv.writer(file, delimiter="|")
    width = max(2, math.trunc(math.log(len(letters) + 1, 10) + 1))
    writer.writerow([f"{1:0{width}}", len(letters)])
    for i, val in enumerate(letters, start=2):
        writer.writerow(map(lambda x: x.replace("|", ""), val.as_list(f"{i:0{width}}")))


@app.post("/upload")
def upload_batch(db: Session = Depends(get_db)):
    """
    Upload letter data file to GPO server.
    """

    letters = crud.get_letters(db)

    if not settings.DEBUG:
        with paramiko.SSHClient() as ssh:
            key = paramiko.RSAKey(data=b64decode(settings.GPO_HOSTKEY))
            ssh.get_host_keys().add(settings.GPO_HOST, "ssh-rsa", key)
            ssh.connect(
                settings.GPO_HOST,
                username=settings.GPO_USERNAME,
                password=settings.GPO_PASSWORD,
            )
            with ssh.open_sftp() as sftp:
                date = datetime.date.today().strftime("%Y%m%d")
                with sftp.open(f"IDVA-{date}.psv", mode="wx") as file:
                    write(file, letters)
    else:
        output = StringIO()
        write(output, letters)
        logging.debug(output.getvalue())

    crud.delete_letters(db, letters)

    return Response()


@app.post("/letters", response_model=schemas.Letter)
def queue_letter(letter: schemas.LetterCreate, db: Session = Depends(get_db)):
    """
    Add a letter to the queue
    """

    return crud.create_letter(db, letter)
