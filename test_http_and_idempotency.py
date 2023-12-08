#!/usr/bin/env python3

import json
import os
import tempfile
import unittest
from unittest import mock

import requests
import run
import supplier_image_upload


class TestRunHTTPErrors(unittest.TestCase):
    def _make_desc_dir(self, tmpdir):
        desc_file = os.path.join(tmpdir, "apple.txt")
        with open(desc_file, "w") as f:
            f.write("Apple\n500\nA sweet fruit\n")
        return tmpdir

    def test_timeout_returns_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_desc_dir(tmpdir)
            with mock.patch("run.requests.post", side_effect=requests.exceptions.Timeout):
                results = run.process_descriptions(tmpdir, "http://localhost/fruits/")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0][0], "error")
            self.assertIn("timeout", results[0][2])

    def test_connection_error_returns_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_desc_dir(tmpdir)
            with mock.patch("run.requests.post", side_effect=requests.exceptions.ConnectionError):
                results = run.process_descriptions(tmpdir, "http://localhost/fruits/")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0][0], "error")
            self.assertIn("connection", results[0][2])

    def test_http_500_returns_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_desc_dir(tmpdir)
            mock_resp = mock.Mock()
            mock_resp.status_code = 500
            with mock.patch("run.requests.post", return_value=mock_resp):
                results = run.process_descriptions(tmpdir, "http://localhost/fruits/")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0][0], "error")
            self.assertIn("500", results[0][2])

    def test_http_200_returns_posted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_desc_dir(tmpdir)
            mock_resp = mock.Mock()
            mock_resp.status_code = 200
            with mock.patch("run.requests.post", return_value=mock_resp):
                results = run.process_descriptions(tmpdir, "http://localhost/fruits/")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0][0], "posted")
            self.assertEqual(results[0][2], 200)

    def test_invalid_url_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_desc_dir(tmpdir)
            with self.assertRaises(ValueError):
                run.process_descriptions(tmpdir, "ftp://bad")


class TestUploadHTTPErrors(unittest.TestCase):
    def test_timeout_returns_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = os.path.join(tmpdir, "apple.jpeg")
            with open(img_path, "wb") as f:
                f.write(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
            with mock.patch("supplier_image_upload.requests.post", side_effect=requests.exceptions.Timeout):
                results = supplier_image_upload.upload_images(tmpdir, "http://localhost/upload/")
            self.assertEqual(results[0][0], "error")
            self.assertIn("timeout", results[0][2])

    def test_connection_error_returns_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = os.path.join(tmpdir, "apple.jpeg")
            with open(img_path, "wb") as f:
                f.write(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
            with mock.patch("supplier_image_upload.requests.post", side_effect=requests.exceptions.ConnectionError):
                results = supplier_image_upload.upload_images(tmpdir, "http://localhost/upload/")
            self.assertEqual(results[0][0], "error")
            self.assertIn("connection", results[0][2])

    def test_http_403_returns_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = os.path.join(tmpdir, "apple.jpeg")
            with open(img_path, "wb") as f:
                f.write(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
            mock_resp = mock.Mock()
            mock_resp.status_code = 403
            with mock.patch("supplier_image_upload.requests.post", return_value=mock_resp):
                results = supplier_image_upload.upload_images(tmpdir, "http://localhost/upload/")
            self.assertEqual(results[0][0], "error")
            self.assertIn("403", results[0][2])


class TestIdempotency(unittest.TestCase):
    def test_already_posted_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            desc_file = os.path.join(tmpdir, "apple.txt")
            with open(desc_file, "w") as f:
                f.write("Apple\n500\nA sweet fruit\n")
            state = {"posted": ["apple.txt"]}
            mock_resp = mock.Mock()
            mock_resp.status_code = 200
            with mock.patch("run.requests.post", return_value=mock_resp) as mock_post:
                results = run.process_descriptions(tmpdir, "http://localhost/fruits/", state=state)
                mock_post.assert_not_called()
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0][0], "already-posted")

    def test_new_file_added_to_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            desc_file = os.path.join(tmpdir, "banana.txt")
            with open(desc_file, "w") as f:
                f.write("Banana\n200\nYellow fruit\n")
            state = {"posted": []}
            mock_resp = mock.Mock()
            mock_resp.status_code = 200
            with mock.patch("run.requests.post", return_value=mock_resp):
                run.process_descriptions(tmpdir, "http://localhost/fruits/", state=state)
            self.assertIn("banana.txt", state["posted"])

    def test_load_save_state_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "state.json")
            state = {"posted": ["a.txt", "b.txt"]}
            run.save_state(state_file, state)
            loaded = run.load_state(state_file)
            self.assertEqual(loaded["posted"], ["a.txt", "b.txt"])

    def test_load_state_missing_file(self):
        loaded = run.load_state("/nonexistent/path/state.json")
        self.assertEqual(loaded, {"posted": []})

    def test_dry_run_does_not_save_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            desc_file = os.path.join(tmpdir, "cherry.txt")
            with open(desc_file, "w") as f:
                f.write("Cherry\n10\nSmall red fruit\n")
            state = {"posted": []}
            results = run.process_descriptions(tmpdir, "http://localhost/fruits/", dry_run=True, state=state)
            self.assertEqual(results[0][0], "dry-run")
            self.assertEqual(state["posted"], [])


class TestExitCodes(unittest.TestCase):
    def test_run_main_exits_1_on_bad_dir(self):
        with mock.patch("run.config.get_user", return_value="testuser"):
            with mock.patch("run.config.get_descriptions_path", return_value="/nonexistent/dir/"):
                with self.assertRaises(SystemExit) as ctx:
                    run.main([])
                self.assertEqual(ctx.exception.code, 1)

    def test_upload_main_exits_1_on_bad_dir(self):
        with mock.patch("supplier_image_upload.config.get_user", return_value="testuser"):
            with mock.patch("supplier_image_upload.config.get_images_path", return_value="/nonexistent/dir/"):
                with self.assertRaises(SystemExit) as ctx:
                    supplier_image_upload.main([])
                self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
