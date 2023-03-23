#!/usr/bin/env python3

import os


DEFAULT_FRUIT_URL = "http://localhost/fruits/"
DEFAULT_UPLOAD_URL = "http://localhost/upload/"
DEFAULT_REPORT_PATH = "/tmp/processed.pdf"
DEFAULT_SENDER = "automation@example.com"
DEFAULT_IMAGE_WIDTH = 600
DEFAULT_IMAGE_HEIGHT = 400

CPU_THRESHOLD = 80.0
MEMORY_THRESHOLD_MB = 500
DISK_THRESHOLD_PERCENT = 20


def get_user():
    return os.getenv("USER")


def get_descriptions_path(user=None):
    user = user or get_user()
    return "/home/{}/supplier-data/descriptions/".format(user)


def get_images_path(user=None):
    user = user or get_user()
    return "/home/{}/supplier-data/images/".format(user)


def get_recipient(user=None):
    user = user or get_user()
    return "{}@example.com".format(user)
