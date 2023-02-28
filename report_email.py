#!/usr/bin/env python3

import os
import reports
import emails

from datetime import datetime


def process_data(descriptions_path):
    descriptions = []
    for description in os.listdir(descriptions_path):
        if description.endswith('txt'):
            description_path = os.path.join(descriptions_path, description)
            lines = open(description_path,'r').read().split('\n')
            lines = lines[:2]
            lines[0] = "name: " + lines[0]
            lines[1] = "weight: " + lines[1]
            lines.append("")
            descriptions.extend(lines)
    return "<br/>".join(descriptions)


if __name__ == "__main__":
    filename = "/tmp/processed.pdf"

    today = datetime.today().strftime("%B %d, %Y")
    title = "Processed Update on {}".format(today)

    user = os.getenv('USER')
    descriptions_path = '/home/{}/supplier-data/descriptions/'.format(user)

    paragraph = process_data(descriptions_path)
    reports.generate_report(filename, title, paragraph)

    sender = "automation@example.com"
    recipient = "{}@example.com".format(user)
    subject = " Upload Completed - Online Fruit Store"
    body = "All fruits are uploaded to our website successfully. A detailed list is attached to this email."
    attachment_path = filename
    message = emails.generate_error_report(sender, recipient, subject, body, attachment_path)
    emails.send(message)