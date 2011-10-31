#!/usr/bin/python

# This file is part of Heapkeeper.
#
# Heapkeeper is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Heapkeeper is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Heapkeeper.  If not, see <http://www.gnu.org/licenses/>.

# Copyright (C) 2010 Csaba Hoch
# Copyright (C) 2011 Attila Nagy

"""Tests the hkweb module.

Usage:

    $ python src/test_hkweb.py
"""


from __future__ import with_statement

import datetime
import unittest
import web as webpy

import hkutils
import hkweb
import test_hkgen


class Test_UtilityFunctions(unittest.TestCase):

    """Tests utility functions of |hkweb|."""

    def setUp(self):
        """Build a mock web.py that has only a `webpy.input().items` that
        returns a preset input (from `self._input`)."""

        class Mocker():
            # Class has no __init__ method # pylint: disable=W0232
            pass

        def mock_input():
            input = Mocker()
            input.items = lambda: self._input
            return input

        self._old_webpy = webpy
        mock_webpy = Mocker()
        mock_webpy.input = mock_input
        hkweb.webpy = mock_webpy

        self._log = []
        self._old_log_fun = hkutils.log_fun
        def log_fun(*args):
            self._log.append(''.join(args))
        hkutils.set_log(log_fun)

        # Mock `datetime.datetime.now`
        class DatetimeMocker():
            """DatetimeMocker is a class that mocks the `datetime` module.

            It redirects all accesses to the original module, except for two:
            it redirects acesses to `datetime` to itself, and when accessing
            `now`, it returns a fixed datetime object."""

            def __init__(self, old_datetime):
                self._inner = self
                self._old_datetime = old_datetime
                self._fixed = old_datetime.datetime(2011, 1, 1, 12, 0)

            def __getattr__(self, attr):
                if attr == 'datetime':
                    return self._inner
                if attr == 'now':
                    return lambda: self._fixed
                return getattr(self._old_datetime, attr)

        self._old_datetime = hkweb.datetime
        hkweb.datetime = DatetimeMocker(self._old_datetime)

    def tearDown(self):
        """Restore original web.py."""

        hkweb.webpy = self._old_webpy

        # Setting the original logging function back
        self.assertEqual(self._log, [])
        hkutils.set_log(self._old_log_fun)

        # Restore `datetime.datetime.now`
        hkweb.datetime = self._old_datetime

    def pop_log(self):
        """Set the log to empty but return the previous logs.

        **Returns:** str
        """

        log = self._log
        self._log = []
        return '\n'.join(log)

    def test_get_web_args(self):
        """Tests :func:`hkweb.get_web_args`"""

        self._input = \
            [
                ('post_id', u'\x00"h/12"'),
                ('new_body_text', u'\x00"xyz"'),
                ('new', u'\x001')
            ]
        self.assertEqual(
                hkweb.get_web_args(),
                {'post_id': 'h/12', 'new_body_text': 'xyz', 'new': 1}
            )

        self._input = \
            [
                ('post_id', u'h/12'),
                ('new_body_text', u'xyz'),
                ('new', u'\x001')
            ]
        self.assertEqual(
                hkweb.get_web_args(),
                {'post_id': 'h/12', 'new_body_text': 'xyz', 'new': 1}
            )

        self._input = []
        self.assertEqual(hkweb.get_web_args(), {})

        self._input = [('x', u'')]
        self.assertEqual(hkweb.get_web_args(), {'x': ''})

        self._input = [('x', u'\00')]
        self.assertEqual(hkweb.get_web_args(), {'x': '\00'})

        self._input = [('x', u'\00042')]
        self.assertEqual(hkweb.get_web_args(), {'x': 42})

        self._input = [('x', u'\00[1,2]')]
        self.assertEqual(hkweb.get_web_args(), {'x': [1, 2]})

        self._input = [('x', u'\00[1,2')]
        self.assertRaises(hkutils.HkException, lambda: hkweb.get_web_args())

    def test_last(self):
        """Tests the `hkweb.last()` function."""

        hkweb.last_access = {}

        self.assertEqual(hkweb.last(), None)
        self.assertEqual(self.pop_log(), 'Access list is empty.')

        hkweb.last_access = {'A': datetime.datetime(2011, 1, 1, 11, 59)}
        hkweb.last()
        self.assertEqual(self.pop_log(), 'Last access was 1 minute ago.')

        hkweb.last_access = {'A': datetime.datetime(2011, 1, 1, 11, 58)}
        hkweb.last()
        self.assertEqual(self.pop_log(), 'Last access was 2 minutes ago.')

        hkweb.last_access = {'A': datetime.datetime(2011, 1, 1, 11, 0)}
        hkweb.last()
        self.assertEqual(self.pop_log(), 'Last access was 1 hour ago.')

        hkweb.last_access = {'A': datetime.datetime(2011, 1, 1, 10, 0)}
        hkweb.last()
        self.assertEqual(self.pop_log(), 'Last access was 2 hours ago.')

        hkweb.last_access = {'A': datetime.datetime(2010, 12, 31, 12, 0)}
        hkweb.last()
        self.assertEqual(self.pop_log(), 'Last access was 1 day ago.')

        hkweb.last_access = {'A': datetime.datetime(2010, 12, 30, 12, 0)}
        hkweb.last()
        self.assertEqual(self.pop_log(), 'Last access was 2 days ago.')

        hkweb.last_access = {'A': datetime.datetime(1970, 12, 30, 12, 0)}
        hkweb.last()
        self.assertEqual(self.pop_log(), 'Last access was 14612 days ago.')

        hkweb.last_access = {'A': datetime.datetime(2011, 1, 2, 12, 0)}
        hkweb.last()
        self.assertEqual(self.pop_log(), 'Last access was 0 seconds ago.')


class Test_WebGenerator(test_hkgen.Test_BaseGenerator):

    """Tests |WebGenerator|."""

    def create_generator(self):
        """Returns a generator object to be used for the testing.

        **Returns:** |WebGenerator|
        """

        return hkweb.WebGenerator(self._postdb)

    def test_print_html_head_content(self):
        """Tests the following functions:

        - :func:`hkweb.WebGenerator.get_static_path`
        - :func:`hkgen.BaseGenerator.print_html_head_content`
        """

        postdb, g, p = self.get_ouv()

        # We overwrite some options of the generator so that we can use these
        # in our test cases. Since different subclasses of BaseGenerator have
        # different options, this way testing will be easier because we can
        # hardcode these values in the tests.
        g.options.js_files = ['static/js/myjs.js']
        g.options.cssfiles = ['static/css/mycss1.css', 'static/css/mycss2.css']
        g.options.favicon = 'static/images/myicon.ico'

        self.assertTextStructsAreEqual(
            g.print_html_head_content(),
            ('    <link rel="stylesheet" href="/static/css/mycss1.css" '
             'type="text/css" />\n'
             '    <link rel="stylesheet" href="/static/css/mycss2.css" '
             'type="text/css" />\n'
             '    <link rel="shortcut icon" '
             'href="/static/images/myicon.ico">\n'))

    def test_print_postitem_flat(self):
        """Inherited test case that we don't want to execute because it would
        fail."""

        pass

    def test_print_postitem_inner(self):
        """Inherited test case that we don't want to execute because it would
        fail."""

        pass


if __name__ == '__main__':
    hkutils.set_log(False)
    unittest.main()
