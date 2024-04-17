#!/usr/bin/env python3

import os
import unittest
import config


class TestConfigDefaults(unittest.TestCase):
    def test_fruit_url(self):
        self.assertEqual(config.DEFAULT_FRUIT_URL, "http://localhost/fruits/")

    def test_upload_url(self):
        self.assertEqual(config.DEFAULT_UPLOAD_URL, "http://localhost/upload/")

    def test_report_path(self):
        self.assertEqual(config.DEFAULT_REPORT_PATH, "/tmp/processed.pdf")

    def test_sender(self):
        self.assertEqual(config.DEFAULT_SENDER, "automation@example.com")

    def test_image_dimensions(self):
        self.assertEqual(config.DEFAULT_IMAGE_WIDTH, 600)
        self.assertEqual(config.DEFAULT_IMAGE_HEIGHT, 400)

    def test_thresholds(self):
        self.assertEqual(config.CPU_THRESHOLD, 80.0)
        self.assertEqual(config.MEMORY_THRESHOLD_MB, 500)
        self.assertEqual(config.DISK_THRESHOLD_PERCENT, 20)


class TestConfigPaths(unittest.TestCase):
    def test_descriptions_path(self):
        result = config.get_descriptions_path("testuser")
        self.assertEqual(result, "/home/testuser/supplier-data/descriptions/")

    def test_images_path(self):
        result = config.get_images_path("testuser")
        self.assertEqual(result, "/home/testuser/supplier-data/images/")

    def test_recipient(self):
        result = config.get_recipient("testuser")
        self.assertEqual(result, "testuser@example.com")

    def test_get_user_returns_string(self):
        result = config.get_user()
        self.assertTrue(result is None or isinstance(result, str))


if __name__ == "__main__":
    unittest.main()
