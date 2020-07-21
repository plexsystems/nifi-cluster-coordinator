from py_example import foo as foo
from py_example.bar import utils as bar
import unittest


class ExampleUnitTests(unittest.TestCase):

    def test_main(self):
        pass

    def test_foo_true_is_true(self):
        self.assertTrue(foo.is_true())

    def test_bar_false_is_false(self):
        self.assertFalse(bar.is_false())


if __name__ == '__main__':
    unittest.main()
