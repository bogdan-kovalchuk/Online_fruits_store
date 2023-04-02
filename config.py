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


def resolve_safe_path(base_dir, *segments):
    base = os.path.realpath(base_dir)
    joined = os.path.join(base, *segments) if segments else base
    resolved = os.path.realpath(joined)
    if not resolved.startswith(base + os.sep) and resolved != base:
        raise ValueError(
            "Path escapes base directory: {} escapes {}".format(joined, base)
        )
    return resolved


def _validate_user(user):
    if not user or not isinstance(user, str):
        raise ValueError("User must be a non-empty string")
    if os.sep in user or "/" in user or ".." in user:
        raise ValueError("User contains path separators: {}".format(user))
    return user


def get_descriptions_path(user=None):
    user = _validate_user(user or get_user())
    return "/home/{}/supplier-data/descriptions/".format(user)


def get_images_path(user=None):
    user = _validate_user(user or get_user())
    return "/home/{}/supplier-data/images/".format(user)


def get_recipient(user=None):
    user = _validate_user(user or get_user())
    return "{}@example.com".format(user)
