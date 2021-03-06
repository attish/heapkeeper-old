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

# Copyright (C) 2009-2010 Csaba Hoch
# Copyright (C) 2009 Attila Nagy

"""Tests the hkutils module.

Usage:

    $ python src/test_hkutils.py
"""


from __future__ import with_statement

import ConfigParser
import StringIO
import unittest

import hkutils


class Test__OptionHandling(unittest.TestCase):

    """Tests the option handling in |hkutils|."""

    @staticmethod
    def f(a, b, c=1, d=2):
        # Unused arguments # pylint: disable=W0613
        pass

    def test_arginfo(self):

        """Tests :func:`hkutils.arginfo`."""

        def f(a, b, c=1, d=2):
            # Unused arguments # pylint: disable=W0613
            pass
        self.assertEqual(hkutils.arginfo(f), (['a', 'b'], {'c':1, 'd':2}))
        f2 = Test__OptionHandling.f
        self.assertEqual(hkutils.arginfo(f2), (['a', 'b'], {'c':1, 'd':2}))

    def test_set_defaultoptions(self):

        """Tests :func:`hkutils.set_defaultoptions`."""

        def f(other1, a, b=1, c=2, other2=None):
            # Unused arguments # pylint: disable=W0613
            pass

        options = {'a':0, 'b': 1}
        hkutils.set_defaultoptions(options, f, ['other1', 'other2'])
        self.assertEqual(options, {'a':0, 'b':1, 'c':2})

        options = {'b': 1}
        def try_():
            # Function already defined # pylint: disable=E0102
            hkutils.set_defaultoptions(options, f, ['other1', 'other2'])
        self.assertRaises(hkutils.HkException, try_)

        options = {'a':0, 'b': 1, 'other': 2}
        def try_():
            # Function already defined # pylint: disable=E0102
            hkutils.set_defaultoptions(options, f, ['other1', 'other2'])
        self.assertRaises(hkutils.HkException, try_)

    def test_set_dict_items_1(self):

        """Tests :func:`hkutils.set_dict_items`."""

        class A:
            # Class has no __init__ method # pylint: disable=W0232
            pass
        a = A()
        d = {'self': 0, 'something': 1, 'notset': hkutils.NOT_SET}
        hkutils.set_dict_items(a, d)
        self.assertEqual(a.something, 1)

        def f():
            # Statement seems to have no effect # pylint: disable=W0104
            a.self
        self.assertRaises(AttributeError, f)

        def f():
            # Function already defined # pylint: disable=E0102
            # Statement seems to have no effect # pylint: disable=W0104
            a.notset
        self.assertRaises(AttributeError, f)

    def test_set_dict_items__2(self):

        """Tests :func:`hkutils.set_dict_items`."""

        NOT_SET = hkutils.NOT_SET
        class A(object):
            # Unused arguments # pylint: disable=W0613
            def __init__(self, x1=NOT_SET, x2=NOT_SET, x3=0, x4=0):
                super(A, self).__init__()
                hkutils.set_dict_items(self, locals())

        a = A(x1=1, x3=1)
        self.assertEqual(a.x1, 1)
        self.assertFalse(hasattr(a, 'x2'))
        self.assertEqual(a.x3, 1)
        self.assertEqual(a.x4, 0)

    def test_check(self):

        """Tests :func:`hkutils.check`."""

        class A(object):
            pass

        a = A()
        a.x = 1
        self.assertTrue(hkutils.check(a, ['x']))
        self.assertRaises(AttributeError, lambda: hkutils.check(a, ['y']))

class Test__TextStruct(unittest.TestCase):

    """Tests text structures in |hkutils|."""

    def test_textstruct_to_str(self):

        """Tests :func:`hkutils.textstruct_to_str`."""

        # Converting a string
        self.assertEqual(
            hkutils.textstruct_to_str('text'),
            'text')

        # Converting a structure that contains both lists and tuples
        self.assertEqual(
            hkutils.textstruct_to_str(['text1', ('2', ['3']), '4']),
            'text1234')

        # Trying to converting something that is not a TextStruct
        self.assertRaises(
            TypeError,
            lambda: hkutils.textstruct_to_str(0))

    def test_write_textstruct(self):

        """Tests :func:`hkutils.write_textstruct`."""

        # Writing a string
        sio = StringIO.StringIO()
        hkutils.write_textstruct(sio, 'text')
        self.assertEqual(sio.getvalue(), 'text')

        # Writing a structure that contains both lists and tuples
        sio = StringIO.StringIO()
        hkutils.write_textstruct(sio, ['text1', ('2', ['3']), '4'])
        self.assertEqual(sio.getvalue(), 'text1234')

        # Trying to writing something that is not a TextStruct
        sio = StringIO.StringIO()
        self.assertRaises(
            TypeError,
            lambda: hkutils.write_textstruct(sio, 0))

    def test_is_textstruct(self):

        """Tests :func:`hkutils.is_textstruct`."""

        self.assertTrue(hkutils.is_textstruct(''))
        self.assertTrue(hkutils.is_textstruct('text'))
        self.assertTrue(hkutils.is_textstruct([]))
        self.assertTrue(hkutils.is_textstruct(['text1', ('2', ['3']), '4']))

        # Testing something that is not a TextStruct
        self.assertFalse(hkutils.is_textstruct(0))


class Test__logging(unittest.TestCase):

    """Tests the logging functions of hklib."""

    def test__1(self):

        """Tests the following functions:

        - :func:`hkutils.set_log`
        - :func:`hkutils.log`
        """

        # We use a custom log function
        old_log_fun = hkutils.log_fun
        def log_fun(*args):
            log.append(list(args))
        hkutils.set_log(log_fun)

        # Test logging
        log = []
        hkutils.log('first line', 'second line')
        hkutils.log('third line')
        self.assertEqual(
            log,
            [['first line', 'second line'],
             ['third line']])

        # Setting the original logging function back
        hkutils.set_log(old_log_fun)


class Test__Misc(unittest.TestCase):

    """Tests the miscellaneous functions in |hkutils|."""

    def test_utf8(self):
        """Tests the following functions:

        - :func:`hkutils.utf8`
        - :func:`hkutils.uutf8`
        """

        # The Hungarian "small u with double acute accent" (u") character is
        # used for the tests.
        #
        # - latin2 code: \xfb
        # - utf-8 code: \xc5\xb1

        # Converting from latin2 to utf-8
        self.assertEqual(hkutils.utf8('\xfb', 'latin2'), '\xc5\xb1')

        # Converting from utf-8 to utf-8
        self.assertEqual(hkutils.utf8('\xc5\xb1', 'utf-8'), '\xc5\xb1')

        # When the encoding is not specified, it is assumed to be already in
        # UTF-8
        self.assertEqual(hkutils.utf8('\xc5\xb1', None), '\xc5\xb1')

        # Converting a unicode object to utf-8
        self.assertEqual(hkutils.uutf8(u'\u0171'), '\xc5\xb1')

    def test_json_uutf8(self):
        """Tests :func:`hkutils.utf8`."""

        # String
        self.assertEqual(
            hkutils.json_uutf8(u'\u0171aa'),
            '\xc5\xb1aa')

        # Dictionary
        self.assertEqual(
            hkutils.json_uutf8({u'\u0171': u'\u0171'}),
            {'\xc5\xb1': '\xc5\xb1'})

        # List
        self.assertEqual(
            hkutils.json_uutf8([u'\u0171', u'\u0171']),
            ['\xc5\xb1', '\xc5\xb1'])

        # Numbers, bools, null
        self.assertEqual(
            hkutils.json_uutf8([u'\u0171', 1, 1.1, True, None]),
            ['\xc5\xb1', 1, 1.1, True, None])

        # Embedded data structures
        self.assertEqual(
            hkutils.json_uutf8([{'key': [u'\u0171']}]),
            [{'key': ['\xc5\xb1']}])

    def test_calc_timestamp(self):

        """Tests :func:`hkutils.calc_timestamp`."""

        ts = hkutils.calc_timestamp('Wed, 20 Aug 2008 17:41:30 +0200')
        self.assertEqual(ts, 1219246890.0)

    def test_parse_date(self):

        """Tests :func:`hkutils.parse_date`."""

        # Fields

        self.assertEqual(
            hkutils.parse_date('2009'),
            (2009, 1, 1, 0, 0, 0))

        self.assertEqual(
            hkutils.parse_date('2009-02'),
            (2009, 2, 1, 0, 0, 0))

        self.assertEqual(
            hkutils.parse_date('2009-02-03'),
            (2009, 2, 3, 0, 0, 0))

        self.assertEqual(
            hkutils.parse_date('2009-02-03_04'),
            (2009, 2, 3, 4, 0, 0))

        self.assertEqual(
            hkutils.parse_date('2009-02-03_04:05'),
            (2009, 2, 3, 4, 5, 0))

        self.assertEqual(
            hkutils.parse_date('2009-02-03_04:05:06'),
            (2009, 2, 3, 4, 5, 6))

        # Space instead of underscore

        self.assertEqual(
            hkutils.parse_date('2009-02-03 04:05:06'),
            (2009, 2, 3, 4, 5, 6))

        # Wrong format

        self.assertRaises(
            hkutils.HkException,
            lambda: hkutils.parse_date('200'))


    def test_HkException(self):

        """Tests :class:`hkutils.HkException`."""

        def f():
            raise hkutils.HkException, 'description'
        self.assertRaises(hkutils.HkException, f)

        try:
            raise hkutils.HkException, 'description'
        except hkutils.HkException, h:
            self.assertEqual(h.value, 'description')
            self.assertEqual(str(h), 'description')

    def test_plural(self):

        """Tests :func:`hkutils.plural`."""

        for i in (-1, 1):
            self.assertEqual(hkutils.plural(i), '')
            self.assertEqual(hkutils.plural(i, 'ox', 'oxen'), 'ox')

        for i in (-2, 0, 2):
            self.assertEqual(hkutils.plural(i), 's')
            self.assertEqual(hkutils.plural(i, 'ox', 'oxen'), 'oxen')

    def test_add_method(self):

        """Tests :func:`hkutils.add_method`."""

        class A(object):
            pass

        def add_method(self, num2):
            return self.num + num2

        a = A()
        a.num = 1
        hkutils.add_method(a, 'add', add_method)
        self.assertEqual(a.add(2), 3)

    def test_append_fun_to_method(self):

        """Tests :func:`hkutils.append_fun_to_method`."""

        # Basic test

        class MyClass(object):
            def my_method(self, a):
                l.append(['my_method', a])
                return a * 2

        def my_fun(self, a):
            # unused argument # pylint: disable= W0613
            l.append(['my_fun', a])

        hkutils.append_fun_to_method(MyClass, 'my_method', my_fun)
        a = MyClass()
        l = []
        l.append(['result', a.my_method(2)])
        self.assertEqual(
            l,
            [['my_method', 2], ['my_fun', 2], ['result', 4]])

        # Testing the `resultfun` parameter

        class MyClass2(object):
            def my_method(self, a):
                l.append(['my_method', a])
                return a * 2

        def my_fun2(self, a):
            # unused argument # pylint: disable= W0613
            l.append(['my_fun', a])
            return a * 4

        hkutils.append_fun_to_method(MyClass2, 'my_method', my_fun2,
                                     resultfun=lambda r1, r2: (r1, r2))
        a = MyClass2()
        l = []
        l.append(['result', a.my_method(2)])
        self.assertEqual(
            l,
            [['my_method', 2], ['my_fun', 2], ['result', (4, 8)]])

    def test_insert_sep(self):
        """Tests :func:`hkutils.insert_sep`."""

        # Normal case
        self.assertEqual(
            hkutils.insert_sep([1, 2, 3], 0),
            [1, 0, 2, 0, 3])

        # List with one element
        self.assertEqual(
            hkutils.insert_sep([1], 0),
            [1])

        # Empty list
        self.assertEqual(
            hkutils.insert_sep([], 0),
            [])

        # Tuple as `seq`
        self.assertEqual(
            hkutils.insert_sep((1, 2, 3), 0),
            [1, 0, 2, 0, 3])

    def test_configparser_to_configdict(self):
        """Tests :func:`hkutils.configparser_to_configdict`."""

        ## Basic tests

        # Basic test
        configparser = ConfigParser.ConfigParser()
        configparser.add_section('section')
        configparser.set('section', 'key', 'value')
        self.assertEqual(
            hkutils.configparser_to_configdict(configparser),
            {'section': {'key': 'value'}})

        # Testing empty configparser
        configparser = ConfigParser.ConfigParser()
        self.assertEqual(
            hkutils.configparser_to_configdict(configparser),
            {})

        ## Testing subsections

        # Testing subsection
        configparser = ConfigParser.ConfigParser()
        configparser.add_section('section/subsection')
        configparser.set('section/subsection', 'key', 'value')
        self.assertEqual(
            hkutils.configparser_to_configdict(configparser),
            {'section': {'subsection': {'key': 'value'}}})

        # Testing subsubsection
        configparser = ConfigParser.ConfigParser()
        configparser.add_section('section/subsection/subsubsection')
        self.assertEqual(
            hkutils.configparser_to_configdict(configparser),
            {'section': {'subsection': {'subsubsection': {}}}})

        # Testing when we have both section and subsection
        configparser = ConfigParser.ConfigParser()
        configparser.add_section('section')
        configparser.add_section('section/subsection')
        configparser.set('section', 'key', 'value')
        configparser.set('section/subsection', 'key sub', 'value sub')
        self.assertEqual(
            hkutils.configparser_to_configdict(configparser),
            {'section': {'key': 'value',
                         'subsection': {'key sub': 'value sub'}}})

        ## Testing key-value pairs

        # Testing empty section (=no key-value pair)
        configparser = ConfigParser.ConfigParser()
        configparser.add_section('section')
        self.assertEqual(
            hkutils.configparser_to_configdict(configparser),
            {'section': {}})

        # Testing several key-value pairs
        configparser = ConfigParser.ConfigParser()
        configparser.add_section('section')
        configparser.set('section', 'key', 'value')
        configparser.set('section', 'key2', 'value2')
        self.assertEqual(
            hkutils.configparser_to_configdict(configparser),
            {'section': {'key': 'value' ,
                         'key2': 'value2'}})

        # Testing conflicting key-value pairs
        configparser = ConfigParser.ConfigParser()
        configparser.add_section('section')
        configparser.set('section', 'key', 'value1')
        configparser.set('section', 'key', 'value2')
        self.assertEqual(
            hkutils.configparser_to_configdict(configparser),
            {'section': {'key': 'value2'}})

        # Testing the same key in different sections
        configparser = ConfigParser.ConfigParser()
        configparser.add_section('section1')
        configparser.add_section('section2')
        configparser.add_section('section1/subsection')
        configparser.set('section1', 'key', 'value1')
        configparser.set('section2', 'key', 'value2')
        configparser.set('section1/subsection', 'key', 'value sub')
        self.assertEqual(
            hkutils.configparser_to_configdict(configparser),
            {'section1': {'key': 'value1',
                          'subsection': {'key': 'value sub'}},
             'section2': {'key': 'value2'}})

        ## Testing funny section names

        # Testing empty section name
        configparser = ConfigParser.ConfigParser()
        configparser.add_section('')
        configparser.set('', 'key', 'value')
        self.assertEqual(
            hkutils.configparser_to_configdict(configparser),
            {'': {'key': 'value'}})

        # Testing empty subsection name
        configparser = ConfigParser.ConfigParser()
        configparser.add_section('/')
        configparser.set('/', 'key', 'value')
        self.assertEqual(
            hkutils.configparser_to_configdict(configparser),
            {'': {'': {'key': 'value'}}})

    def test_quote_shell_arg(self):
        """Tests :func:`hkutils.quote_shell_arg`."""

        self.assertEqual(
            hkutils.quote_shell_arg('text'),
            'text')

        self.assertEqual(
            hkutils.quote_shell_arg('te xt'),
            "'te xt'")

        self.assertEqual(
            hkutils.quote_shell_arg('te "x" t'),
            "'te \"x\" t'")

        self.assertEqual(
            hkutils.quote_shell_arg("te 'x' t"),
            "'te '\"'\"'x'\"'\"' t'")


if __name__ == '__main__':
    unittest.main()
