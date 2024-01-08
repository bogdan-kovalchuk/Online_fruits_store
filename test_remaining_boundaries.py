#!/usr/bin/env python3

import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest import mock

from PIL import Image

import report_email
import run
import supplier_image_upload
import validation


class TestImageContentValidation(unittest.TestCase):
    def test_real_jpeg_is_valid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, "apple.jpeg")
            Image.new("RGB", (3, 2), "green").save(image_path, format="JPEG")
            self.assertEqual(validation.validate_image_file(image_path), [])

    def test_non_image_bytes_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, "fake.jpeg")
            with open(image_path, "wb") as image_file:
                image_file.write(b"not an image")
            errors = validation.validate_image_file(image_path)
            self.assertTrue(any("invalid or corrupt" in error for error in errors))

    def test_truncated_jpeg_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, "truncated.jpeg")
            Image.new("RGB", (4, 4), "blue").save(image_path, format="JPEG")
            with open(image_path, "rb") as image_file:
                prefix = image_file.read(12)
            with open(image_path, "wb") as image_file:
                image_file.write(prefix)
            errors = validation.validate_image_file(image_path)
            self.assertTrue(any("invalid or corrupt" in error for error in errors))

    def test_invalid_image_is_never_uploaded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, "fake.jpeg")
            with open(image_path, "wb") as image_file:
                image_file.write(b"not an image")
            with mock.patch("supplier_image_upload.requests.post") as post:
                results = supplier_image_upload.upload_images(
                    tmpdir, "http://localhost/upload/"
                )
            post.assert_not_called()
            self.assertEqual(results[0][0], "skip")

    def test_uppercase_jpg_is_uploaded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = os.path.join(tmpdir, "apple.JPG")
            Image.new("RGB", (2, 2), "red").save(image_path, format="JPEG")
            response = mock.Mock(status_code=200)
            with mock.patch(
                "supplier_image_upload.requests.post", return_value=response
            ) as post:
                results = supplier_image_upload.upload_images(
                    tmpdir, "http://localhost/upload/"
                )
            post.assert_called_once()
            self.assertEqual(results, [("uploaded", "apple.JPG", 200)])


class TestWeightBoundaries(unittest.TestCase):
    def _process_weight(self, value):
        with tempfile.TemporaryDirectory() as tmpdir:
            description_path = os.path.join(tmpdir, "apple.txt")
            with open(description_path, "w") as description_file:
                description_file.write("Apple\n{}\nSweet fruit\n".format(value))
            with mock.patch("run.requests.post") as post:
                results = run.process_descriptions(
                    tmpdir, "http://localhost/fruits/", dry_run=True
                )
            post.assert_not_called()
            return results

    def test_unit_bearing_weight_is_parsed(self):
        results = self._process_weight("500 g")
        self.assertEqual(results[0][0], "dry-run")
        self.assertEqual(results[0][2]["weight"], 500)

    def test_empty_weight_is_skipped(self):
        results = self._process_weight("")
        self.assertEqual(results[0][0], "skip")
        self.assertIn("valid integer", results[0][2])

    def test_non_numeric_weight_is_skipped(self):
        results = self._process_weight("heavy")
        self.assertEqual(results[0][0], "skip")
        self.assertIn("valid integer", results[0][2])

    def test_non_positive_weight_is_skipped(self):
        for value in ("0 g", "-2 g"):
            with self.subTest(value=value):
                results = self._process_weight(value)
                self.assertEqual(results[0][0], "skip")
                self.assertIn("positive", results[0][2])


class TestReportEmailOrchestration(unittest.TestCase):
    def _description_directory(self, root, name="Apple", weight="500 g"):
        description_path = os.path.join(root, "apple.txt")
        with open(description_path, "w") as description_file:
            description_file.write("{}\n{}\nSweet fruit\n".format(name, weight))
        return root

    def test_process_data_escapes_reportlab_markup(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._description_directory(tmpdir, "A & B <fruit>")
            paragraph = report_email.process_data(tmpdir)
        self.assertIn("A &amp; B &lt;fruit&gt;", paragraph)
        self.assertNotIn("A & B <fruit>", paragraph)

    def test_dry_run_validates_configuration_without_side_effects(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._description_directory(tmpdir)
            report_path = os.path.join(tmpdir, "report.pdf")
            with mock.patch("report_email.reports.generate_report") as generate:
                with mock.patch("report_email.emails.generate") as make_email:
                    with mock.patch("report_email.emails.send") as send:
                        output = io.StringIO()
                        with contextlib.redirect_stdout(output):
                            errors = report_email.run(
                                tmpdir, report_path,
                                "sender@example.com", "recipient@example.com",
                                dry_run=True,
                            )
            self.assertEqual(errors, [])
            self.assertIn("Would generate report", output.getvalue())
            generate.assert_not_called()
            make_email.assert_not_called()
            send.assert_not_called()
            self.assertFalse(os.path.exists(report_path))

    def test_invalid_dry_run_configuration_has_no_side_effects(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._description_directory(tmpdir)
            with mock.patch("report_email.reports.generate_report") as generate:
                with mock.patch("report_email.emails.generate") as make_email:
                    with mock.patch("report_email.emails.send") as send:
                        errors = report_email.run(
                            tmpdir, os.path.join(tmpdir, "report.txt"),
                            "bad sender", "bad recipient", dry_run=True,
                        )
            self.assertTrue(any(".pdf" in error for error in errors))
            self.assertTrue(any("Sender" in error for error in errors))
            self.assertTrue(any("Recipient" in error for error in errors))
            generate.assert_not_called()
            make_email.assert_not_called()
            send.assert_not_called()

    def test_successful_run_orders_validations_before_side_effects(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._description_directory(tmpdir)
            events = []
            message = object()

            def validate_report(*args):
                events.append("validate report")
                return []

            def validate_email(address, label):
                events.append("validate {}".format(label.lower()))
                return address

            with mock.patch(
                "report_email.reports.validate_report_inputs",
                side_effect=validate_report,
            ):
                with mock.patch(
                    "report_email.config.validate_email", side_effect=validate_email
                ):
                    with mock.patch(
                        "report_email.reports.generate_report",
                        side_effect=lambda *args: events.append("generate report"),
                    ):
                        with mock.patch(
                            "report_email.emails.generate",
                            side_effect=lambda *args: events.append("generate email") or message,
                        ):
                            with mock.patch(
                                "report_email.emails.send",
                                side_effect=lambda value: events.append("send email") or True,
                            ):
                                errors = report_email.run(
                                    tmpdir, os.path.join(tmpdir, "report.pdf"),
                                    "sender@example.com", "recipient@example.com",
                                )
        self.assertEqual(errors, [])
        self.assertEqual(
            events,
            [
                "validate report", "validate sender", "validate recipient",
                "generate report", "generate email", "send email",
            ],
        )

    def test_report_failure_prevents_email_work(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._description_directory(tmpdir)
            with mock.patch(
                "report_email.reports.generate_report",
                side_effect=OSError("disk full"),
            ):
                with mock.patch("report_email.emails.generate") as make_email:
                    with mock.patch("report_email.emails.send") as send:
                        errors = report_email.run(
                            tmpdir, os.path.join(tmpdir, "report.pdf"),
                            "sender@example.com", "recipient@example.com",
                        )
            self.assertEqual(errors, ["Failed to generate report: disk full"])
            make_email.assert_not_called()
            send.assert_not_called()

    def test_send_failure_is_returned(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._description_directory(tmpdir)
            with mock.patch("report_email.reports.generate_report"):
                with mock.patch("report_email.emails.generate", return_value=object()):
                    with mock.patch("report_email.emails.send", return_value=False):
                        errors = report_email.run(
                            tmpdir, os.path.join(tmpdir, "report.pdf"),
                            "sender@example.com", "recipient@example.com",
                        )
        self.assertEqual(errors, ["Failed to send email via SMTP"])


class TestStateStorageBoundaries(unittest.TestCase):
    def test_default_state_file_uses_platform_temp_directory(self):
        self.assertEqual(os.path.dirname(run.DEFAULT_STATE_FILE), tempfile.gettempdir())

    def test_corrupt_state_returns_empty_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, "state.json")
            with open(state_path, "w") as state_file:
                state_file.write("{broken")
            self.assertEqual(run.load_state(state_path), {"posted": []})

    def test_wrong_state_shape_returns_empty_state(self):
        invalid_states = [[], {"posted": "apple.txt"}, {"posted": [1]}]
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, "state.json")
            for invalid_state in invalid_states:
                with self.subTest(state=invalid_state):
                    with open(state_path, "w") as state_file:
                        json.dump(invalid_state, state_file)
                    self.assertEqual(run.load_state(state_path), {"posted": []})

    def test_save_state_replaces_file_atomically(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, "state.json")
            with mock.patch("run.os.replace", wraps=os.replace) as replace:
                run.save_state(state_path, {"posted": ["apple.txt"]})
            replace.assert_called_once()
            temporary_path, destination = replace.call_args.args
            self.assertEqual(os.path.dirname(temporary_path), tmpdir)
            self.assertEqual(destination, state_path)
            self.assertEqual(run.load_state(state_path), {"posted": ["apple.txt"]})
            self.assertEqual(os.listdir(tmpdir), ["state.json"])

    def test_save_state_rejects_empty_path(self):
        with self.assertRaises(ValueError):
            run.save_state("", {"posted": []})


if __name__ == "__main__":
    unittest.main()
