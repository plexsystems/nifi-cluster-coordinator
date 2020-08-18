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


class ConstructApiUrlTests(unittest.TestCase):
    @parameterized.expand([
        ('http', 'www.foo.com', None, None, 'http://www.foo.com'),
        ('https', 'www.foo.com', 'api', None, 'https://www.foo.com/api'),
        ('https', 'www.foo.com', ['api', 'v1'], None, 'https://www.foo.com/api/v1'),
        ('http', 'www.foo.com', None, {'foo': 'bar'}, 'http://www.foo.com?foo=bar'),
        ('http', 'www.foo.com', ['api', 'v1'], {'foo': 'bar', 'bar': 'baz'}, 'http://www.foo.com/api/v1?foo=bar&bar=baz')
    ])
    def test_construct_api_url_returns_expected(self, scheme, host_name, path_parts, query_parts, expected):
        result = url_helper.construct_api_url(scheme, host_name, path_parts, query_parts)
        self.assertEqual(expected, result)


if __name__ == '__main__':
    unittest.main()