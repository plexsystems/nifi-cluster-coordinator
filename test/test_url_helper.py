import unittest
from parameterized import parameterized
import nifi_cluster_coordinator.utils.url_helper as url_helper


class ConstructPathPartsTests(unittest.TestCase):
    @parameterized.expand([
        (None, ''),
        ('foo', 'foo'),
        (['foo'], 'foo'),
        (['foo', 'bar'], 'foo/bar'),
        (['foo', 'bar', 'baz'], 'foo/bar/baz')
    ])
    def test_construct_path_parts_returns_expected(self, given, expected):
        result = url_helper.construct_path_parts(given)
        self.assertEqual(expected, result)


class ConstrucQueryPartsTests(unittest.TestCase):
    @parameterized.expand([
        (None, None),
        ('foo=bar', 'foo=bar'),
        ('foo=bar&baz=foo', 'foo=bar&baz=foo'),
        ({'foo': 'bar'}, 'foo=bar'),
        ({'foo': 'bar', 'baz': 'foo'}, 'foo=bar&baz=foo'),
        ({'foo': 'bar', 'baz': 'foo', 'bar': 'foo'}, 'foo=bar&baz=foo&bar=foo')
    ])
    def test_construct_query_parts_returns_expected(self, given, expected):
        result = url_helper.construct_query_parts(given)
        self.assertEqual(expected, result)


if __name__ == '__main__':
    unittest.main()