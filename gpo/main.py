"""
GPO Microservice FastAPI Web App.
"""

import datetime
from io import StringIO
import logging
import math
import csv
from base64 import b64decode
from fastapi import FastAPI, Depends, Response
import paramiko
from starlette_prometheus import metrics, PrometheusMiddleware
from sqlalchemy.orm import Session

from . import settings, crud, models, schemas
from .database import SessionLocal, engine

# pylint: disable=invalid-name

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics/", metrics)

logging.getLogger().setLevel(settings.LOG_LEVEL)


def get_db():
    """
    get db connection
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def write(file, letters):
    """
    Write letter data to file
    """
    writer = csv.writer(file, delimiter="|")
    numLines = len(letters) + 1
    numIndexDigits = math.trunc(math.log(numLines, 10)) + 1
    width = max(2, numIndexDigits)
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
                port=settings.GPO_PORT,
                username=settings.GPO_USERNAME,
                password=settings.GPO_PASSWORD,
            )
            with ssh.open_sftp() as sftp:
                sftp.chdir("gsa_order")
                date = datetime.date.today().strftime("%Y%m%d")
                with sftp.open(f"idva-{date}-0.psv", mode="wx") as file:
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
