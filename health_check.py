#!/usr/bin/env python3

import os
import emails
import psutil
import socket

if __name__ == "__main__":
    sender = "automation@example.com"
    recipient = "{}@example.com".format(os.getenv('USER'))
    body = "Please check your system and resolve the issue as soon as possible."

    if psutil.cpu_percent(1) > 80.0:
        subject = "Error - CPU usage is over 80%"
        message = emails.generate_error_report(sender, recipient, subject, body)
        emails.send(message)

    if psutil.virtual_memory().available/1024/1024 < 500:
        subject = "Error - Available memory is less than 500MB"
        message = emails.generate_error_report(sender, recipient, subject, body)
        emails.send(message)

    if psutil.disk_usage('/').percent < 20:
        subject = "Error - Available disk space is less than 20%"
        message = emails.generate_error_report(sender, recipient, subject, body)
        emails.send(message)
    
    if socket.gethostbyname('localhost') != "127.0.0.1":
        subject = "Error - localhost cannot be resolved to 127.0.0.1"
        message = emails.generate_error_report(sender, recipient, subject, body)
        emails.send(message)