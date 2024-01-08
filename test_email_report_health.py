#!/usr/bin/env python3

import os
import smtplib
import sys
import tempfile
import unittest
from unittest import mock

_mock_psutil = mock.MagicMock()
sys.modules.setdefault('psutil', _mock_psutil)

import emails
import health_check


class TestEmailSend(unittest.TestCase):
    def test_send_returns_true_on_success(self):
        msg = emails.generate_error_report("a@b.com", "c@d.com", "subj", "body")
        with mock.patch("emails.smtplib.SMTP") as mock_smtp:
            instance = mock_smtp.return_value
            result = emails.send(msg)
            self.assertTrue(result)
            instance.send_message.assert_called_once_with(msg)
            instance.quit.assert_called_once()

    def test_send_returns_false_on_smtp_error(self):
        msg = emails.generate_error_report("a@b.com", "c@d.com", "subj", "body")
        with mock.patch("emails.smtplib.SMTP", side_effect=smtplib.SMTPException):
            result = emails.send(msg)
            self.assertFalse(result)

    def test_send_returns_false_on_os_error(self):
        msg = emails.generate_error_report("a@b.com", "c@d.com", "subj", "body")
        with mock.patch("emails.smtplib.SMTP", side_effect=OSError("Connection refused")):
            result = emails.send(msg)
            self.assertFalse(result)

    def test_generate_without_attachment(self):
        msg = emails.generate("a@b.com", "c@d.com", "subj", "body")
        self.assertEqual(msg["From"], "a@b.com")
        self.assertEqual(msg["To"], "c@d.com")
        self.assertEqual(msg["Subject"], "subj")

    def test_generate_with_unknown_mime(self):
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"data")
            path = f.name
        try:
            msg = emails.generate("a@b.com", "c@d.com", "subj", "body", path)
            self.assertIsNotNone(msg)
        finally:
            os.unlink(path)

    def test_generate_error_report_matches_generate(self):
        msg = emails.generate_error_report("x@y.com", "z@w.com", "Alert", "Body text")
        self.assertEqual(msg["From"], "x@y.com")
        self.assertEqual(msg["To"], "z@w.com")
        self.assertEqual(msg["Subject"], "Alert")


class TestHealthCheckInjection(unittest.TestCase):
    def test_cpu_over_threshold(self):
        alerts = health_check.check_health(
            cpu_threshold=50,
            get_cpu_percent=lambda: 80,
            get_available_memory_mb=lambda: 1000,
            get_disk_usage_percent=lambda: 50,
            resolve_localhost=lambda: "127.0.0.1",
        )
        self.assertEqual(len(alerts), 1)
        self.assertIn("CPU", alerts[0])

    def test_memory_below_threshold(self):
        alerts = health_check.check_health(
            memory_threshold_mb=500,
            get_cpu_percent=lambda: 10,
            get_available_memory_mb=lambda: 200,
            get_disk_usage_percent=lambda: 50,
            resolve_localhost=lambda: "127.0.0.1",
        )
        self.assertEqual(len(alerts), 1)
        self.assertIn("memory", alerts[0])

    def test_disk_below_threshold(self):
        alerts = health_check.check_health(
            disk_threshold_percent=30,
            get_cpu_percent=lambda: 10,
            get_available_memory_mb=lambda: 1000,
            get_disk_usage_percent=lambda: 15,
            resolve_localhost=lambda: "127.0.0.1",
        )
        self.assertEqual(len(alerts), 1)
        self.assertIn("disk", alerts[0])

    def test_localhost_resolution_failure(self):
        alerts = health_check.check_health(
            get_cpu_percent=lambda: 10,
            get_available_memory_mb=lambda: 1000,
            get_disk_usage_percent=lambda: 50,
            resolve_localhost=lambda: "0.0.0.0",
        )
        self.assertEqual(len(alerts), 1)
        self.assertIn("localhost", alerts[0])

    def test_all_checks_pass(self):
        alerts = health_check.check_health(
            cpu_threshold=90,
            memory_threshold_mb=100,
            disk_threshold_percent=10,
            get_cpu_percent=lambda: 50,
            get_available_memory_mb=lambda: 500,
            get_disk_usage_percent=lambda: 50,
            resolve_localhost=lambda: "127.0.0.1",
        )
        self.assertEqual(alerts, [])

    def test_invalid_threshold_raises(self):
        with self.assertRaises(ValueError):
            health_check.check_health(cpu_threshold=150)

    def test_non_numeric_threshold_raises(self):
        with self.assertRaises(TypeError):
            health_check.check_health(cpu_threshold="high")

    def test_send_alerts_with_injected_send(self):
        sent_messages = []
        mock_send = lambda msg: sent_messages.append(msg) or True
        results = health_check.send_alerts(
            ["Error - CPU over 90%"],
            sender_fn=lambda: "sender@example.com",
            recipient_fn=lambda: "recipient@example.com",
            send_fn=mock_send,
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], True)
        self.assertEqual(len(sent_messages), 1)

    def test_send_alerts_handles_failure(self):
        mock_send = lambda msg: False
        results = health_check.send_alerts(
            ["Error - disk low"],
            sender_fn=lambda: "sender@example.com",
            recipient_fn=lambda: "recipient@example.com",
            send_fn=mock_send,
        )
        self.assertEqual(results[0][1], False)


if __name__ == "__main__":
    unittest.main()
