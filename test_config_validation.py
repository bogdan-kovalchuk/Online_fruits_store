#!/usr/bin/env python3

import os
import tempfile
import unittest
import config


class TestResolveSafePath(unittest.TestCase):
    def test_normal_subpath(self):
        base = tempfile.gettempdir()
        result = config.resolve_safe_path(base, "subdir", "file.txt")
        expected = os.path.realpath(os.path.join(base, "subdir", "file.txt"))
        self.assertEqual(result, expected)

    def test_base_only(self):
        base = tempfile.gettempdir()
        result = config.resolve_safe_path(base)
        self.assertEqual(result, os.path.realpath(base))

    def test_traversal_raises(self):
        base = tempfile.gettempdir()
        with self.assertRaises(ValueError) as ctx:
            config.resolve_safe_path(base, "..", "..", "etc", "passwd")
        self.assertIn("escapes", str(ctx.exception))

    def test_absolute_traversal_raises(self):
        base = tempfile.gettempdir()
        with self.assertRaises(ValueError):
            config.resolve_safe_path(base, os.path.join("..", "etc"))


class TestValidateUrl(unittest.TestCase):
    def test_valid_http(self):
        self.assertEqual(config.validate_url("http://localhost/fruits/"), "http://localhost/fruits/")

    def test_valid_https(self):
        self.assertEqual(config.validate_url("https://example.com/api"), "https://example.com/api")

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            config.validate_url("")

    def test_none_raises(self):
        with self.assertRaises(ValueError):
            config.validate_url(None)

    def test_ftp_scheme_raises(self):
        with self.assertRaises(ValueError):
            config.validate_url("ftp://files.example.com/data")

    def test_no_host_raises(self):
        with self.assertRaises(ValueError):
            config.validate_url("http://")

    def test_custom_label(self):
        with self.assertRaises(ValueError) as ctx:
            config.validate_url("not-a-url", "Upload URL")
        self.assertIn("Upload URL", str(ctx.exception))


class TestValidateEmail(unittest.TestCase):
    def test_valid_email(self):
        self.assertEqual(config.validate_email("user@example.com"), "user@example.com")

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            config.validate_email("")

    def test_no_at_raises(self):
        with self.assertRaises(ValueError):
            config.validate_email("userexample.com")

    def test_no_domain_raises(self):
        with self.assertRaises(ValueError):
            config.validate_email("user@")

    def test_spaces_raises(self):
        with self.assertRaises(ValueError):
            config.validate_email("user @example.com")


class TestValidateUser(unittest.TestCase):
    def test_valid_user(self):
        self.assertEqual(config._validate_user("testuser"), "testuser")

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            config._validate_user("")

    def test_none_raises(self):
        with self.assertRaises(ValueError):
            config._validate_user(None)

    def test_slash_raises(self):
        with self.assertRaises(ValueError):
            config._validate_user("user/name")

    def test_dotdot_raises(self):
        with self.assertRaises(ValueError):
            config._validate_user("..hidden")

    def test_get_descriptions_path_rejects_bad_user(self):
        with self.assertRaises(ValueError):
            config.get_descriptions_path("../../../etc")

    def test_get_images_path_rejects_bad_user(self):
        with self.assertRaises(ValueError):
            config.get_images_path("")

    def test_get_recipient_rejects_bad_user(self):
        with self.assertRaises(ValueError):
            config.get_recipient("a/b")


if __name__ == "__main__":
    unittest.main()
