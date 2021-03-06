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

"""Tests the |hksearch| module.

Usage:

    $ python src/test_hksearch.py
"""


from __future__ import with_statement

import time
import unittest

import hkutils
import hklib
import hksearch
import test_hklib


class Test_Search(unittest.TestCase, test_hklib.PostDBHandler):

    """Tests :func:`hksearch.search`."""

    def setUp(self):
        hklib.localtime_fun = time.gmtime
        self.setUpDirs()
        self.create_postdb()
        self.create_threadst()

    def tearDown(self):
        self.tearDownDirs()

    def test1(self):

        postdb = self._postdb
        all_posts = postdb.all()

        # Note: the body of post <i> is 'body<i>'

        ### Testing the target type 'whole'

        ## Testing searching in the body

        self.assertEqual(
            hksearch.search('body', all_posts),
            all_posts)

        self.assertEqual(
            hksearch.search('body1', all_posts),
            postdb.postset(self.p(1)))

        # Result: two posts (my_heap/0 and my_other_heap/0)
        self.assertEqual(
            hksearch.search('body0', all_posts),
            postdb.postset([self.p(0), self.po(0)]))

        ## Testing searching in the heap id

        # Result: only my_other_heap/0
        self.assertEqual(
            hksearch.search('my_other_heap', all_posts),
            postdb.postset([self.po(0)]))

        ## Testing case insensitivity

        self.assertEqual(
            hksearch.search('MY_OTHER_heap', all_posts),
            postdb.postset([self.po(0)]))

        ## Testing several patterns

        # Result: only my_heap/0, because that is the only post is my_heap that
        # contains 'body0'
        self.assertEqual(
            hksearch.search('my_heap body0', all_posts),
            postdb.postset([self.p(0)]))

        ### Testing other target types

        ## Testing target type 'heap'

        # Result: only my_other_heap/0
        self.assertEqual(
            hksearch.search('heap:^my_other_heap$', all_posts),
            postdb.postset([self.po(0)]))

        # Result: only my_other_heap/0
        self.assertEqual(
            hksearch.search('heap:o', all_posts),
            postdb.postset([self.po(0)]))

        ## Testing target type 'author'

        self.assertEqual(
            hksearch.search('author:author0', all_posts),
            postdb.postset([self.p(0), self.po(0)]))

        ## Testing target type 'subject'

        self.assertEqual(
            hksearch.search('subject:subject0', all_posts),
            postdb.postset([self.p(0), self.po(0)]))

        ## Testing target type 'tag'

        self.p(0).add_tag('tag0')
        self.p(0).add_tag('tag1')
        self.po(0).add_tag('tag0')

        self.assertEqual(
            hksearch.search('tag:tag0', all_posts),
            postdb.postset([self.p(0), self.po(0)]))

        ## Testing target type 'message-id'

        self.assertEqual(
            hksearch.search('message-id:0@', all_posts),
            postdb.postset([self.p(0), self.po(0)]))

        ## Testing target type 'body'

        self.assertEqual(
            hksearch.search('body:0', all_posts),
            postdb.postset([self.p(0), self.po(0)]))

        ## Testing target type 'before' and 'after'

        self.assertEqual(
            hksearch.search('before:2008-08-20_15:41:01', all_posts),
            postdb.postset([self.p(0), self.po(0)]))

        self.assertEqual(
            hksearch.search('after:2008-08-20_15:41:04', all_posts),
            postdb.postset([self.p(4)]))

        self.assertRaises(
            hkutils.HkException,
            lambda: hksearch.search('after:xx', all_posts))

        self.assertRaises(
            hkutils.HkException,
            lambda: hksearch.search('after:2009-00', all_posts))

        ### Testing unicode

        # The Hungarian "small u with double acute accent" (unicode \u0171,
        # utf-8 code '\xc5\xb1') character is used for the test.

        # Specifying the unicode character directly

        self.p(0).set_body('A\xc5\xb1B')
        self.assertEqual(
            hksearch.search('body:A\xc5\xb1B', all_posts),
            postdb.postset([self.p(0)]))

        # Specifying the unicode character as an UTF-8 character

        self.p(0).set_body('A\xc5\xb1B')
        self.assertEqual(
            hksearch.search('body:A\\xc5\\xb1B', all_posts),
            postdb.postset([self.p(0)]))

        # Specifying the unicode character as a unicode character
        #
        # After rewriting hklib to use unicode objects instead of UTF-8 encoded
        # strings, the expected result should be postdb.postset([self.p(0)])).

        self.p(0).set_body('A\xc5\xb1B')
        self.assertEqual(
            hksearch.search('body:A\u0171B', all_posts),
            postdb.postset([]))

        # Specifying the unicode character as a unicode character
        #
        # After rewriting hklib to use unicode objects instead of UTF-8 encoded
        # strings, the expected result should be postdb.postset([self.p(0)])).

        self.p(0).set_body('A\xc5\xb1B')
        self.assertEqual(
            hksearch.search('body:A\\u0171B', all_posts),
            postdb.postset([]))

        # Testing \b
        #
        # \b matches the word boundary. This test case tests that Heapkeeper
        # takes unicode characters into account, which is achieved by compiling
        # the regexp with the re.UNICODE option.

        self.p(0).set_body('A\xc5\xb1B')
        self.assertEqual(
            hksearch.search('body:\\b\xc5\xb1', all_posts),
            postdb.postset([]))

        ## Testing negation

        self.assertEqual(
            hksearch.search('-body1', all_posts),
            postdb.postset([self.p(0), self.p(2), self.p(3), self.p(4),
                            self.po(0)]))

        self.assertEqual(
            hksearch.search('heap:-my_heap', all_posts),
            postdb.postset([self.po(0)]))


if __name__ == '__main__':
    hkutils.set_log(False)
    unittest.main()
