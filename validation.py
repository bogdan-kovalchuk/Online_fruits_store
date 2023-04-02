#!/usr/bin/env python3

import os


REQUIRED_DESCRIPTION_KEYS = ["name", "weight", "description", "image_name"]

ALLOWED_IMAGE_EXTENSIONS = {".jpeg", ".jpg", ".tiff", ".tif", ".png"}
MAX_IMAGE_SIZE_BYTES = 50 * 1024 * 1024


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


def validate_image_file(path, max_size_bytes=MAX_IMAGE_SIZE_BYTES):
    errors = []
    if not path or not isinstance(path, str):
        errors.append("Image path is empty")
        return errors
    if not os.path.isfile(path):
        errors.append("Image file not found: {}".format(path))
        return errors
    _, ext = os.path.splitext(path)
    if ext.lower() not in ALLOWED_IMAGE_EXTENSIONS:
        errors.append(
            "Unsupported image format {}: {}".format(ext, path)
        )
    size = os.path.getsize(path)
    if size == 0:
        errors.append("Image file is empty: {}".format(path))
    elif size > max_size_bytes:
        errors.append(
            "Image exceeds max size ({}B > {}B): {}".format(
                size, max_size_bytes, path
            )
        )
    return errors


def validate_image_dimensions(width, height):
    errors = []
    if not isinstance(width, int) or width <= 0:
        errors.append("Width must be a positive integer, got {}".format(width))
    if not isinstance(height, int) or height <= 0:
        errors.append("Height must be a positive integer, got {}".format(height))
    return errors
