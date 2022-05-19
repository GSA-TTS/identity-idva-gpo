"""
Configuration for the GPO microservice settings.
Context is switched based on if the app is in debug mode.
"""
import logging
import os
import json
import sys

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG set is set to True if env var is "True"
DEBUG = os.getenv("DEBUG", "False") == "True"

LOG_LEVEL = os.getenv("LOG_LEVEL", logging.getLevelName(logging.INFO))

GPO_USERNAME = os.getenv("GPO_USERNAME")
GPO_PASSWORD = os.getenv("GPO_PASSWORD")
GPO_HOST = os.getenv("GPO_HOST")
GPO_HOSTKEY = os.getenv("GPO_HOSTKEY")

try:
    db_uri = json.loads(os.getenv("VCAP_SERVICES"))["aws-rds"][0]["credentials"]["uri"]
except (json.JSONDecodeError, KeyError, TypeError):
    sys.exit("Failed to load the aws-rds uri from VCAP_SERVICES")

DB_URI = os.getenv("DB_URI", db_uri)
