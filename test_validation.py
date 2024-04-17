#!/usr/bin/env python3

import os
import tempfile
import unittest
import validation


class TestValidateDescriptionFile(unittest.TestCase):
    def test_missing_file(self):
        errors = validation.validate_description_file("/nonexistent/file.txt")
        self.assertTrue(any("not found" in e for e in errors))

    def test_wrong_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            f.write("line1\nline2\nline3\n")
            path = f.name
        try:
            errors = validation.validate_description_file(path)
            self.assertTrue(any(".txt" in e for e in errors))
        finally:
            os.unlink(path)

    def test_too_few_lines(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write("only one line\n")
            path = f.name
        try:
            errors = validation.validate_description_file(path)
            self.assertTrue(any("fewer than 3" in e for e in errors))
        finally:
            os.unlink(path)

    def test_valid_file(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write("Apple\n500\nA sweet fruit\n")
            path = f.name
        try:
            errors = validation.validate_description_file(path)
            self.assertEqual(errors, [])
        finally:
            os.unlink(path)


class TestValidateDescriptionData(unittest.TestCase):
    def test_missing_keys(self):
        errors = validation.validate_description_data({"name": "Apple"})
        self.assertTrue(any("weight" in e for e in errors))
        self.assertTrue(any("description" in e for e in errors))
        self.assertTrue(any("image_name" in e for e in errors))

    def test_empty_name(self):
        data = {"name": "", "weight": 500, "description": "sweet", "image_name": "a.jpeg"}
        errors = validation.validate_description_data(data)
        self.assertTrue(any("Name" in e for e in errors))

    def test_negative_weight(self):
        data = {"name": "Apple", "weight": -1, "description": "sweet", "image_name": "a.jpeg"}
        errors = validation.validate_description_data(data)
        self.assertTrue(any("positive" in e for e in errors))

    def test_valid_data(self):
        data = {"name": "Apple", "weight": 500, "description": "sweet", "image_name": "a.jpeg"}
        errors = validation.validate_description_data(data)
        self.assertEqual(errors, [])


class TestValidateDirectory(unittest.TestCase):
    def test_empty_path(self):
        errors = validation.validate_directory("", "Test")
        self.assertTrue(any("empty" in e for e in errors))

    def test_nonexistent_directory(self):
        errors = validation.validate_directory("/nonexistent/dir", "Test")
        self.assertTrue(any("does not exist" in e for e in errors))

    def test_valid_directory(self):
        errors = validation.validate_directory(tempfile.gettempdir(), "Test")
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
