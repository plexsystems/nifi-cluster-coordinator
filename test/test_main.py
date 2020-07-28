import unittest


class MainUnitTests(unittest.TestCase):

    def test_foo_true_is_true(self):
        self.assertTrue(True)

    def test_bar_false_is_false(self):
        self.assertFalse(False)


if __name__ == '__main__':
    unittest.main()