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


def check_health(
    cpu_threshold=None,
    memory_threshold_mb=None,
    disk_threshold_percent=None,
    get_cpu_percent=None,
    get_available_memory_mb=None,
    get_disk_usage_percent=None,
    resolve_localhost=None,
):
    cpu_threshold = cpu_threshold if cpu_threshold is not None else config.CPU_THRESHOLD
    memory_threshold_mb = memory_threshold_mb if memory_threshold_mb is not None else config.MEMORY_THRESHOLD_MB
    disk_threshold_percent = disk_threshold_percent if disk_threshold_percent is not None else config.DISK_THRESHOLD_PERCENT

    validate_threshold(cpu_threshold, "cpu_threshold", 0, 100)
    validate_threshold(disk_threshold_percent, "disk_threshold_percent", 0, 100)
    if memory_threshold_mb < 0:
        raise ValueError("memory_threshold_mb must be non-negative, got {}".format(memory_threshold_mb))

    if get_cpu_percent is None:
        get_cpu_percent = lambda: psutil.cpu_percent(1)
    if get_available_memory_mb is None:
        get_available_memory_mb = lambda: psutil.virtual_memory().available / 1024 / 1024
    if get_disk_usage_percent is None:
        get_disk_usage_percent = lambda: 100 - psutil.disk_usage('/').percent
    if resolve_localhost is None:
        resolve_localhost = lambda: socket.gethostbyname('localhost')

    alerts = []

    if get_cpu_percent() > cpu_threshold:
        alerts.append("Error - CPU usage is over {}%".format(cpu_threshold))

    if get_available_memory_mb() < memory_threshold_mb:
        alerts.append("Error - Available memory is less than {}MB".format(memory_threshold_mb))

    if get_disk_usage_percent() < disk_threshold_percent:
        alerts.append("Error - Available disk space is less than {}%".format(disk_threshold_percent))

    try:
        if resolve_localhost() != "127.0.0.1":
            alerts.append("Error - localhost cannot be resolved to 127.0.0.1")
    except socket.error:
        alerts.append("Error - localhost cannot be resolved")

    return alerts


def send_alerts(alerts, sender_fn=None, recipient_fn=None, send_fn=None):
    if sender_fn is None:
        sender_fn = lambda: config.DEFAULT_SENDER
    if recipient_fn is None:
        recipient_fn = config.get_recipient
    if send_fn is None:
        send_fn = emails.send

    sender = sender_fn()
    recipient = recipient_fn()
    body = "Please check your system and resolve the issue as soon as possible."
    results = []
    for alert in alerts:
        message = emails.generate_error_report(sender, recipient, alert, body)
        ok = send_fn(message)
        results.append((alert, ok))
    return results


if __name__ == "__main__":
    alerts = check_health()
    if alerts:
        results = send_alerts(alerts)
        for alert, ok in results:
            status = "sent" if ok else "failed"
            print("Alert {}: {}".format(status, alert))
    else:
        print("All checks passed.")
