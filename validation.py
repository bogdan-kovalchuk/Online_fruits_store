#!/usr/bin/env python3

import os


REQUIRED_DESCRIPTION_KEYS = ["name", "weight", "description", "image_name"]


def validate_description_file(path):
    errors = []
    if not os.path.isfile(path):
        errors.append("File not found: {}".format(path))
        return errors
    if not path.endswith(".txt"):
        errors.append("Expected .txt extension: {}".format(path))
    with open(path, "r") as f:
        lines = f.read().split("\n")
    if len(lines) < 3:
        errors.append("File has fewer than 3 lines: {}".format(path))
    return errors


def validate_description_data(data):
    errors = []
    for key in REQUIRED_DESCRIPTION_KEYS:
        if key not in data:
            errors.append("Missing required key: {}".format(key))
    if "weight" in data:
        try:
            w = int(data["weight"]) if not isinstance(data["weight"], int) else data["weight"]
            if w <= 0:
                errors.append("Weight must be positive, got {}".format(w))
        except (ValueError, TypeError):
            errors.append("Weight is not a valid integer: {}".format(data["weight"]))
    if "name" in data and not str(data["name"]).strip():
        errors.append("Name must not be empty")
    return errors


def validate_directory(path, label="directory"):
    errors = []
    if not path:
        errors.append("{} path is empty".format(label))
    elif not os.path.isdir(path):
        errors.append("{} does not exist: {}".format(label, path))
    return errors
