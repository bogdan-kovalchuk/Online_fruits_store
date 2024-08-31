#!/usr/bin/env python3

import os
import emails
import psutil
import socket
import config


def validate_threshold(value, name, min_val=0, max_val=100):
    if not isinstance(value, (int, float)):
        raise TypeError("{} must be numeric, got {}".format(name, type(value).__name__))
    if value < min_val or value > max_val:
        raise ValueError("{} must be between {} and {}, got {}".format(name, min_val, max_val, value))


def check_health(cpu_threshold=None, memory_threshold_mb=None, disk_threshold_percent=None):
    cpu_threshold = cpu_threshold if cpu_threshold is not None else config.CPU_THRESHOLD
    memory_threshold_mb = memory_threshold_mb if memory_threshold_mb is not None else config.MEMORY_THRESHOLD_MB
    disk_threshold_percent = disk_threshold_percent if disk_threshold_percent is not None else config.DISK_THRESHOLD_PERCENT

    validate_threshold(cpu_threshold, "cpu_threshold", 0, 100)
    validate_threshold(disk_threshold_percent, "disk_threshold_percent", 0, 100)
    if memory_threshold_mb < 0:
        raise ValueError("memory_threshold_mb must be non-negative, got {}".format(memory_threshold_mb))

    sender = config.DEFAULT_SENDER
    recipient = config.get_recipient()
    body = "Please check your system and resolve the issue as soon as possible."
    alerts = []

    if psutil.cpu_percent(1) > cpu_threshold:
        alerts.append("Error - CPU usage is over {}%".format(cpu_threshold))

    if psutil.virtual_memory().available / 1024 / 1024 < memory_threshold_mb:
        alerts.append("Error - Available memory is less than {}MB".format(memory_threshold_mb))

    if psutil.disk_usage('/').percent < disk_threshold_percent:
        alerts.append("Error - Available disk space is less than {}%".format(disk_threshold_percent))

    try:
        if socket.gethostbyname('localhost') != "127.0.0.1":
            alerts.append("Error - localhost cannot be resolved to 127.0.0.1")
    except socket.error:
        alerts.append("Error - localhost cannot be resolved")

    return alerts


if __name__ == "__main__":
    sender = config.DEFAULT_SENDER
    recipient = config.get_recipient()
    body = "Please check your system and resolve the issue as soon as possible."

    alerts = check_health()
    for alert in alerts:
        message = emails.generate_error_report(sender, recipient, alert, body)
        emails.send(message)
