import unittest


class TestExample(unittest.TestCase):
    def test_dummy(self):
        self.assertEqual(1, 1)  # Simple test to check if unittest works

if __name__ == "__main__":
    unittest.main()