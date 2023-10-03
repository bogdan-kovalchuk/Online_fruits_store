#!/usr/bin/env python3

import argparse
import os
import sys

import reports
import emails
import config
import validation

from datetime import datetime


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Generate report and send email.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print actions without generating report or sending email")
    return parser.parse_args(argv)


def process_data(descriptions_path):
    descriptions = []
    for description in sorted(os.listdir(descriptions_path)):
        if description.endswith('txt'):
            description_path = os.path.join(descriptions_path, description)
            file_errors = validation.validate_description_file(description_path)
            if file_errors:
                continue
            with open(description_path, 'r') as f:
                lines = f.read().split('\n')
            lines = lines[:2]
            lines[0] = "name: " + lines[0]
            lines[1] = "weight: " + lines[1]
            lines.append("")
            descriptions.extend(lines)
    return "<br/>".join(descriptions)


def run(descriptions_path, report_path, sender, recipient, dry_run=False):
    dir_errors = validation.validate_directory(descriptions_path, "Descriptions path")
    if dir_errors:
        return dir_errors

    paragraph = process_data(descriptions_path)
    today = datetime.today().strftime("%B %d, %Y")
    title = "Processed Update on {}".format(today)
    subject = "Upload Completed - Online Fruit Store"
    body = "All fruits are uploaded to our website successfully. A detailed list is attached to this email."

    if dry_run:
        print("Would generate report: {}".format(report_path))
        print("Would send email from {} to {}".format(sender, recipient))
        return []

    report_errors = reports.validate_report_inputs(report_path, title, paragraph)
    if report_errors:
        return report_errors

    reports.generate_report(report_path, title, paragraph)
    config.validate_email(sender, "Sender")
    config.validate_email(recipient, "Recipient")
    message = emails.generate(sender, recipient, subject, body, report_path)
    sent = emails.send(message)
    if not sent:
        return ["Failed to send email via SMTP"]
    return []


def main(argv=None):
    args = parse_args(argv)
    user = config.get_user()
    descriptions_path = config.get_descriptions_path(user)
    report_path = config.DEFAULT_REPORT_PATH
    sender = config.DEFAULT_SENDER
    recipient = config.get_recipient(user)

    errors = run(descriptions_path, report_path, sender, recipient, dry_run=args.dry_run)
    if errors:
        for e in errors:
            print("Error: {}".format(e), file=sys.stderr)
        sys.exit(1)
    if args.dry_run:
        print("Dry-run complete.")
    else:
        print("Report generated and email sent.")


if __name__ == "__main__":
    main()
