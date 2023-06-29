#!/usr/bin/env python3

import email.message
import mimetypes
import os.path
import smtplib

SMTP_TIMEOUT = 30


def generate(sender, recipient, subject, body, attachment_path=None):
    message = email.message.EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    if attachment_path is not None:
        attachment_filename = os.path.basename(attachment_path)
        mime_type, _ = mimetypes.guess_type(attachment_path)
        if mime_type is None:
            mime_type = "application/octet-stream"
        mime_type, mime_subtype = mime_type.split('/', 1)

        with open(attachment_path, 'rb') as ap:
            message.add_attachment(ap.read(),
                                  maintype=mime_type,
                                  subtype=mime_subtype,
                                  filename=attachment_filename)

    return message


def generate_error_report(sender, recipient, subject, body, attachment_path=None):
    return generate(sender, recipient, subject, body, attachment_path)


def send(message, smtp_host='localhost', timeout=SMTP_TIMEOUT):
    try:
        mail_server = smtplib.SMTP(smtp_host, timeout=timeout)
        mail_server.send_message(message)
        mail_server.quit()
        return True
    except (smtplib.SMTPException, OSError):
        return False
