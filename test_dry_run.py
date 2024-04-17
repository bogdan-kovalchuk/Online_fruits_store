#!/usr/bin/env python3

import os
import tempfile
import unittest
from unittest import mock

import run
import changeImage
import supplier_image_upload


class TestRunDryRun(unittest.TestCase):
    def test_dry_run_does_not_post(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            desc_file = os.path.join(tmpdir, "apple.txt")
            with open(desc_file, "w") as f:
                f.write("Apple\n500\nA sweet fruit\n")
            with mock.patch("run.requests.post") as mock_post:
                results = run.process_descriptions(tmpdir, "http://localhost/fruits/", dry_run=True)
                mock_post.assert_not_called()
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0][0], "dry-run")

    def test_normal_mode_posts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            desc_file = os.path.join(tmpdir, "apple.txt")
            with open(desc_file, "w") as f:
                f.write("Apple\n500\nA sweet fruit\n")
            mock_resp = mock.Mock()
            mock_resp.status_code = 200
            with mock.patch("run.requests.post", return_value=mock_resp) as mock_post:
                results = run.process_descriptions(tmpdir, "http://localhost/fruits/", dry_run=False)
                mock_post.assert_called_once()
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0][0], "posted")

    def test_parse_args_dry_run(self):
        args = run.parse_args(["--dry-run"])
        self.assertTrue(args.dry_run)

    def test_parse_args_default(self):
        args = run.parse_args([])
        self.assertFalse(args.dry_run)


class TestChangeImageDryRun(unittest.TestCase):
    def test_dry_run_does_not_convert(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tiff_path = os.path.join(tmpdir, "apple.tiff")
            with open(tiff_path, "w") as f:
                f.write("fake")
            results = changeImage.convert_images(tmpdir, dry_run=True)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0][0], "dry-run")
            self.assertFalse(os.path.exists(os.path.join(tmpdir, "apple.jpeg")))

    def test_parse_args_dry_run(self):
        args = changeImage.parse_args(["--dry-run"])
        self.assertTrue(args.dry_run)


class TestUploadDryRun(unittest.TestCase):
    def test_dry_run_does_not_upload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = os.path.join(tmpdir, "apple.jpeg")
            with open(img_path, "w") as f:
                f.write("fake")
            with mock.patch("supplier_image_upload.requests.post") as mock_post:
                results = supplier_image_upload.upload_images(tmpdir, "http://localhost/upload/", dry_run=True)
                mock_post.assert_not_called()
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0][0], "dry-run")

    def test_parse_args_dry_run(self):
        args = supplier_image_upload.parse_args(["--dry-run"])
        self.assertTrue(args.dry_run)


if __name__ == "__main__":
    unittest.main()
