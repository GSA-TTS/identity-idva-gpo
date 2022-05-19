"""
GPO Microservice FastAPI Web App.
"""

import datetime
from io import StringIO
import logging
import math
import csv
from base64 import b64decode
from zoneinfo import ZoneInfo
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

DEST_FILE_DIR = "gsa_order"


def get_db():
    """
    get db connection
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def write(file: StringIO | paramiko.SFTPFile, letters: list[models.Letter]):
    """
    Write letter data to file

    001|955
    002|FAKEY MCFAKERSON|123 FAKE ST||GREAT FALLS|MT|59010|Q82GZBP71C|January 11, 2022|January 21, 2022|Example Sinatra App|https://secure.login.gov
    003|JIMMY TESTERSON|456 FAKE RD|Apt 1|FAKE CITY|CA|40323|4WVGPG0Z5Z|January 11, 2022|January 21, 2022|Example Rails App|https://secure.login.gov
    004|MIKE MCMOCKDATA|789 TEST AVE||FALLS CHURCH|VA|20943|5HVFT58WJ0|January 11, 2022|January 21, 2022|Example Java App|https://secure.login.gov
    005|...
    ...
    956|...

    """

    writer = csv.writer(file, delimiter="|")
    numLines = len(letters) + 1

    # number of digits in the row index
    numIndexDigits = math.trunc(math.log(numLines, 10)) + 1
    # row index width is a least 2 and is enough to fit number of digits in the index
    width = max(2, numIndexDigits)

    header = [f"{1:0{width}}", len(letters)]
    writer.writerow(header)

    for i, val in enumerate(letters, start=2):

        # row with index
        row = val.as_list(f"{i:0{width}}")

        # remove any pipes that might be in the data
        sanitized_row = map(lambda x: x.replace("|", ""), row)
        writer.writerow(sanitized_row)


@app.post("/upload")
def upload_batch(db: Session = Depends(get_db)):
    """
    Upload letter data file to GPO server.
    """

    letters = crud.get_letters(db)
    count = len(letters)

    if count == 0:
        logging.info("No letters in db. Nothing to upload.")
        return Response(count)

    if settings.DEBUG:
        output = StringIO()
        write(output, letters)
        logging.debug(output.getvalue())
        crud.delete_letters(db, letters)
        return Response(count)

    with paramiko.SSHClient() as ssh_client:
        host_key = paramiko.RSAKey(data=b64decode(settings.GPO_HOSTKEY))
        ssh_client.get_host_keys().add(settings.GPO_HOST, "ssh-rsa", host_key)
        ssh_client.connect(
            settings.GPO_HOST,
            username=settings.GPO_USERNAME,
            password=settings.GPO_PASSWORD,
        )
        with ssh_client.open_sftp() as sftp:
            sftp.chdir(DEST_FILE_DIR)
            date = datetime.datetime.now(ZoneInfo("US/Eastern")).strftime("%Y%m%d")
            try:
                with sftp.open(f"idva-{date}-0.psv", mode="wx") as file:
                    write(file, letters)
            except PermissionError as err:
                logging.error(
                    "Error Creating file likely because it already exists: %s", err
                )
                return Response(status_code=500)

    crud.delete_letters(db, letters)

    return Response(count)


@app.post("/letters", response_model=schemas.Letter)
def queue_letter(letter: schemas.LetterCreate, db: Session = Depends(get_db)):
    """
    Add a letter to the queue
    """

    return crud.create_letter(db, letter)


@app.get("/letters")
def count_letter(db: Session = Depends(get_db)):
    """
    Get count of letter in the queue
    """

    return len(crud.get_letters(db))
