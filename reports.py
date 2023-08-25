#!/usr/bin/env python3

import os

from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def validate_report_inputs(filename, title, paragraph):
    errors = []
    if not filename or not isinstance(filename, str):
        errors.append("Filename must be a non-empty string")
    elif not filename.lower().endswith('.pdf'):
        errors.append("Filename must have .pdf extension: {}".format(filename))
    if not title or not isinstance(title, str):
        errors.append("Title must be a non-empty string")
    if not paragraph or not isinstance(paragraph, str):
        errors.append("Paragraph must be a non-empty string")
    return errors


def generate_report(filename, title, paragraph):
    errors = validate_report_inputs(filename, title, paragraph)
    if errors:
        raise ValueError("; ".join(errors))

    parent = os.path.dirname(filename)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)

    styles = getSampleStyleSheet()
    report = SimpleDocTemplate(filename)
    report_title = Paragraph(title, styles["h1"])
    report_paragraph = Paragraph(paragraph, styles["BodyText"])
    empty_line = Spacer(1, 20)
    report.build([report_title, empty_line, report_paragraph])
    return True
