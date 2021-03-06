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

"""|hklib| implements the heap data structure.

Pseudo-types
''''''''''''

|hklib| has pseudo-types that are not real Python types, but we use them as
types in the documentation so we can talk about them easily.

.. _hklib_PostId:

- **PostId** -- The identifier of a |Post| in |PostDB|. Example:
  ``('my_heap', '42')``.

  Real type: (str, str)

.. _hklib_PostIdStr:

- **PostIdStr** -- The string representation of a |PostId|. It contains the
  heap id and the post index separated by a slash character. Example:
  ``'my_heap/42'``.

  Real type: str

.. _hklib_HeapId:

- **HeapId** -- The identifier (name) of a heap in |PostDB|. Example:
  ``'my_heap'``.

  Real type: str

.. _hklib_PostIndex:

- **PostIndex** -- The identifier of a |Post| in |PostDB| within a heap.
  Example: ``'42'``.

  Real type: str

.. _hklib_Messageid:

- **Messageid** -- The message identifier of the email from which the |Post|
  was created. Not all post have a message id. Example:
  ``'<4B32916C.5030604@gmail.com>'``

  Real type: str

.. _hklib_PrePostId:

- **PrePostId** -- An object that can be converted into a |PostId|. Examples:
  ``('my_heap', '42')``, ``('my_heap', 42)``, ``'my_heap/42'``.

  Real type: |PostId| | (str, int) | |PostIdStr|

.. _hklib_PrePost:

- **PrePost** -- An object that can be converted into a |Post|. Conversion
  means that an existing post will be looked up in the post database based on
  the prepost's content. If the prepost is a |PostIndex| or an int (which will
  be converted to a post index), then the prepost itself is not enough to find
  the post, a heap id is also needed. When a prepost is passed to a function to
  convert it to a post, often a default heap will be passed too, which is used
  when the prepost is a post index or an int to determine in which heap should
  the function look up the post.

  Real type: |PrePostId| | |Messageid| | |Post| | |PostIndex| | int

.. _hklib_PrePostSet:

- **PrePostSet** -- An object that can be converted into a |PostSet|. The
  object is converted by converting its elements one-by-one, and then putting
  them into a |PostSet|.

  Real type: set(|PrePost|)) | [|PrePost|] | |PrePost| | |PostSet|

.. _hklib_ThreadStruct:

- **ThreadStruct** -- A thread structure that describes parent-children
  relationships between posts. The structure is a tree, which is stored in a
  dictionary in which all children of a node are assigned to the node. The root
  of the tree is not a post but a ``None`` object. The posts that have no
  parent (the "roots") are stored as the children of ``None``. All other posts
  are child of some post (their parent). Usually, but not necessarily, thread
  structures describe the "real" parent-children relationships that the posts
  have.

  Real type: {(|PostId| | ``None``): [|PostId|]}

.. _hklib_PostDBEventListener:

- **PostDBEventListener** -- An object or function that can be called when a
  |PostDBEvent| happens.

  Real type: fun(|PostDBEvent|)

.. _hklib_HtmlStr:

- **HtmlStr** -- String that contains HTML.

  Real type: str

.. _hklib_HtmlText:

- **HtmlText** -- Text that contains HTML code.

  Subtype of |TextStruct|.
"""


from __future__ import with_statement

import datetime
import os
import os.path
import re
import StringIO
import sys
import time

import hkutils
import hkbodyparser


heapkeeper_version = '0.9+'

# Checking that the user has the appropriate Python version
major, minor, micro, releaselevel, _serial = sys.version_info
if (major != 2 or minor < 5):
    print ('ERROR: Heapkeeper ' + heapkeeper_version +
           ' runs only with Python 2.x, where x >= 5.')
    print ('The following Python version was detected: ' +
           '%s.%s.%s %s' % (major, minor, micro, releaselevel))
    sys.exit(0)


##### Post #####

# This variable should be put into hklib.Options, but we don't have that yet.
localtime_fun = time.localtime


class PostNotFoundError(hkutils.HkException):

    """An exception about not finding the specified post.

    **Data attribute:**

    - `value` (object) -- The reason of the error.
    """

    def __init__(self, value):
        """Constructor.

        **Argument:**

        - `value` (object) -- The reason of the error.
        """

        hkutils.HkException.__init__(self, value)

    def __str__(self):
        """Returns the string representation of the error reason.

        **Returns:** str
        """

        return 'Post not found: %s' % (self.value,)


class Post(object):

    """Represents a posted message on the heap.

    A post object is in the memory, but usually it represents a file that is in
    the filesystem.

    **Data attributes:**

    - `_header` ({str: (str | [str])}) -- The header of the post. See
      the contents below.
    - `_body` (str) -- The body of the post. The first character of the
      body is not a whitespace. The last character is a newline character, and
      the last but one character is not a whitespace. It does not contain any
      ``\\r`` characters, newlines are stored as ``\\n``. The form of the body
      expressed as a regular expression: ``(\\S|\\S[^\\r]*\\S)\\n``. The
      :func:`set_body` function converts any given string into this format.
    - `_post_id` (|PostId| | None) -- The identifier of the post.
    - `_postdb` (|PostDB| | None) -- The post database object that contains the
      post. If `_postdb` is not ``None``, `_heapid` must not be ``None``
      either.
    - `_modified` (bool) -- It is ``False`` if the post file that belongs to
      the post object is up-to-date. It is ``True`` if there is no such file or
      the post has been modified since the last synchronization.
    - `_meta_dict` ({str: (str | ``None``)}) -- Dictionary that contains meta
      text from the body.
    - `_body_object` (|Body|) -- The parsed body.

    The `_header` attribute is a dictonary that contains attributes of the post
    such as the subject. The `_header` always contains all the following items:

    - ``'Author'`` (str) -- The author of the post.
    - ``'Subject'`` (str) -- The subject of the post.
    - ``'Tag'`` ([str]) -- The tags of the post.
    - ``'Message-Id'`` (str) -- The message id of the post.
    - ``'Parent'`` (|PostIdStr| | |PostIndex| | |Messageid| | ``''``) -- A
      reference to the post that is the parent of the current post. It should
      be en empty string when the post has no parent. In case it is a post
      index, the parent is in the same heap as the current post.
    - ``'Date'`` (str) -- The date of the post. For example:
      ``'Date: Wed, 20 Aug 2008 17:41:01 +0200'``
    - ``'Flag'`` ([str]) -- The flags of the post. Currently there is only one
      flag, the ``delete`` flag.
    """

    @staticmethod
    def is_post_id(post_id):
        """Returns whether `post_id` is a correctly formatted |PrePostId|.

        **Argument:**

        - `post_id` (object)

        **Returns:** bool
        """

        return ((isinstance(post_id, tuple) and
                 len(post_id) == 2 and
                 isinstance(post_id[0], str) and
                 (isinstance(post_id[1], str) or
                  isinstance(post_id[1], int))) or
                (isinstance(post_id, str) and
                 len(post_id.split('/')) == 2))

    @staticmethod
    def assert_is_post_id(post_id):
        """Asserts that `post_id` is a correctly formatted |PrePostId|.

        **Argument:**

        - `post_id` (object)

        **Raises:** AssertionError
        """

        assert Post.is_post_id(post_id), \
               'The following object is not a post id: %s' % (post_id,)

    @staticmethod
    def unify_post_id(post_id):
        """Converts that |PrePostId| to |PostId|.

        **Argument:**

        - `post_id` (|PrePostId|)

        **Returns:** |PostId|
        """

        if post_id is None:
            return None
        elif isinstance(post_id, tuple):
            heap_id, post_index = post_id
            if isinstance(post_index, int):
                post_index = str(post_index)
        elif isinstance(post_id, str):
            heap_id, post_index = post_id.split('/')
        return (heap_id, post_index)

    # Parsing

    @staticmethod
    def parse_header(f):
        """Parses the header from f.

        **Argument:**

        - `f` (file) -- A file object.

        **Returns:** {str: [str]}
        """

        headers = {}
        line = f.readline()
        while line not in ['', '\n']:
            m = re.match('([^:]+): ?(.*)', line)
            if m is None:
                error_msg = ('Error parsing the following line: "%s"' %
                             (line.rstrip('\n'),))
                raise hkutils.HkException(error_msg)
            key = m.group(1)
            value = m.group(2)
            line = f.readline()
            while line not in ['', '\n'] and line[0] == ' ':
                line = line.rstrip('\n')
                value += '\n' + line[1:]
                line = f.readline()
            if key not in headers:
                headers[key] = [value]
            else:
                headers[key].append(value)
        return headers

    @staticmethod
    def create_header(d, post_id=None):
        """Transforms the ``{str: [str])}`` returned by :func:`parse_header` to
        a ``{str: (str | [str])}`` dictionary.

        Strings will be assigned to the ``'Author'``, ``'Subject'``, etc.
        attributes, while dictionaries to the ``'Tag'`` and ``'Flag'`` strings.
        If an attribute is not present in the input, an empty string or an
        empty list will be assigned to it. The list that is assigned to
        ``'Flag'`` is sorted.

        **Argument:**

        - `d` ({str: [str])})
        - `post_id` (|PostId| | ``None``) -- The id of the post to be read.
          Used in warning printouts.

        **Returns:** {str: (str | [str])}
        """

        if post_id is None:
            post_id_str = ''
        else:
            post_id_str = ' (post %s/%s)' % post_id

        def copy_one(key):
            try:
                [value] = d.pop(key, [''])
            except ValueError:
                raise hkutils.HkException, \
                      ('Multiple "%s" keys.' % key)
            h[key] = value

        def copy_list(key):
            h[key] = d.pop(key, [])

        d = d.copy()
        h = {}

        copy_one('Author')
        copy_one('Subject')
        copy_list('Tag')
        copy_one('Message-Id')
        copy_one('Parent')
        copy_one('Date')
        copy_list('Flag')
        h['Tag'].sort()
        h['Flag'].sort()

        # Adding additional keys to the _header and print warning about them
        # (We sort the keys so that the order of the warnings is
        # deterministic.)
        for attr in sorted(d.keys()):
            hkutils.log(
                'WARNING%s: Additional attribute in post: "%s"' %
                (post_id_str, attr))
            copy_list(attr)
        return h

    @staticmethod
    def parse(f, post_id=None):
        """Parses a file and returns a tuple of the header and the body.

        **Arguments:**

        - `f` (file) -- A file object.
        - `post_id` (|PostId| | ``None``) -- The id of the post to be read.
          Used in warning printouts.

        **Returns:** (str, str)
        """

        headers = Post.create_header(Post.parse_header(f), post_id)
        body = f.read().rstrip() + '\n'
        return headers, body

    # Constructors

    def __init__(self, f, post_id=None, postdb=None):
        """Constructor.

        **Arguments:**

        - `f` (file) -- A file object from which the header and the body of the
          post will be read. It will not be closed.
        - `post_id` (|PostId| | ``None``) -- The post id of the post.
        - `postdb` (|PostDB| | ``None``) -- The post database to which the post
          belongs.
        """

        assert(postdb is None or Post.is_post_id(post_id))
        super(Post, self).__init__()
        # Catch "Exception" # pylint: disable=W0703
        try:
            self._header, self._body = Post.parse(f, post_id)
            self._post_id = Post.unify_post_id(post_id)
            self._postdb = postdb
            self._datetime = hkutils.NOT_SET
            self._modified = not self.postfile_exists()
            self._meta_dict = None
            self._body_object = None
        except Exception, e:
            exc_info = sys.exc_info()
            if (isinstance(e, hkutils.HkException) and hasattr(f, 'name')):
                print exc_info[1]
                exc_info[1].value += '\nwhile parsing post file "%s"' % f.name
            raise exc_info[0], exc_info[1], exc_info[2]

    @staticmethod
    def from_str(s, post_id=None, postdb=None):
        """Creates a post object from the given string.

        **Arguments:**

        - `s` (str) -- String from which the post should be created. It is
          handled like the content of a post file.
        - `post_id` (|PostId| | ``None``) -- The post id of the post.
        - `postdb` (|PostDB| | ``None``) -- The post database to which the post
          belongs.

        **Returns:** |Post|
        """

        sio = StringIO.StringIO(s)
        p = Post(sio, Post.unify_post_id(post_id), postdb)
        sio.close()
        return p

    @staticmethod
    def from_file(filename, post_id=None, postdb=None):
        """Creates a post object from a file.

        **Arguments:**

        - `filename` (str) -- The post file from which the post should be
          created.
        - `post_id` (|PostId| | ``None``) -- The post id of the post.
        - `postdb` (|PostDB| | ``None``) -- The post database to which the post
          belongs.

        **Returns:** |Post|
        """

        with open(filename, 'r') as f:
            return Post(f, Post.unify_post_id(post_id), postdb)

    @staticmethod
    def create_empty(post_id=None, postdb=None):
        """Creates an empty post object.

        **Arguments:**

        - `post_id` (|PostId| | ``None``) -- The post id of the post.
        - `postdb` (|PostDB| | ``None``) -- The post database to which the post
          belongs.

        **Returns:** |Post|
        """

        return Post.from_str('', Post.unify_post_id(post_id), postdb)

    # Modifications

    def touch(self, touch_postdb=True):
        """Should be called each time after the post is modified.

        See also the :ref:`lazy_data_calculation_pattern` pattern.

        **Arguments:**

        - `touch_postdb` (bool) -- Touch the post database.
        """

        self._modified = True
        self._datetime = hkutils.NOT_SET
        self._meta_dict = None
        self._body_object = None
        if self._postdb is not None and touch_postdb:
            self._postdb.touch(self)

    def is_modified(self):
        """Returns whether the post is modified.

        See also the :ref:`lazy_data_calculation_pattern` pattern.

        **Returns:** bool
        """

        return self._modified

    # post id fields

    def post_id(self):
        """Returns the post id of the post.

        **Returns:** |PostId|
        """

        return self._post_id

    def heap_id(self):
        """Returns the heap id of the post's heap.

        **Returns:** |HeapId|
        """

        if self._post_id is None:
            raise hkutils.HkException('Post has no post id.')
        else:
            return self._post_id[0]

    def post_index(self):
        """Returns the post index of the post.

        **Returns:** |PostIndex|
        """

        if self._post_id is None:
            raise hkutils.HkException('Post has no post id.')
        else:
            return self._post_id[1]

    def post_id_str(self):
        """Returns the post id of the post in ``'<heap id>/<post index>'``
        format.

        **Returns:** |PostIdStr|
        """

        return '%s/%s' % (self.heap_id(), self.post_index())

    # author field

    def author(self):
        """Returns the author of the post.

        **Returns:** str
        """

        return self._header['Author']

    def set_author(self, author):
        """Sets the author of the post.

        **Argument:**

        - `author` (str)
        """

        self._header['Author'] = author
        self.touch()

    # subject field

    def real_subject(self):
        """Returns the real subject of the post as it is stored in the post
        file.

        **Returns:** str
        """

        return self._header['Subject']

    def subject(self):
        """The subject with the ``"Re:"`` prefix removed.

        **Returns:** str
        """

        subject = self._header['Subject']
        if re.match('[Rr][Ee]:', subject):
            subject = subject[3:]
        return subject.strip()

    def set_subject(self, subject):
        """Sets the ("real") subject of the post.

        **Argument:**

        - `subject` (str)
        """

        self._header['Subject'] = subject
        self.touch()

    # message id field

    def messid(self):
        """Returns the message id of the post.

        **Returns:** |Messageid| | ``None``
        """

        return self._header['Message-Id']

    def set_messid(self, messid):
        """Sets the message id of the post.

        **Argument:**

        - `messid` (|Messageid| | ``None``)
        """

        old_messid = self.messid()
        self._header['Message-Id'] = messid
        postdb = self._postdb
        if postdb is not None:
            postdb.notify_changed_messid(self, old_messid, messid)
        self.touch()

    # parent field

    def parent(self):
        """Returns the ``Parent`` attribute of the post.

        **Returns:** |PostIdStr| | |PostIndex| | |Messageid| | ``''``
        """

        return self._header['Parent']

    def set_parent(self, parent):
        """Sets the ``Parent`` attribute of the post.

        **Argument:**

        - `parent` (|PostIdStr| | |PostIndex| | |Messageid| | ``''``)
        """

        self._header['Parent'] = parent
        self.touch()

    # date field

    def date(self):
        """Returns the ``Date`` attribute of the post.

        **Returns:** str
        """

        return self._header['Date']

    def set_date(self, date):
        """Sets the ``Date`` attribute of the post.

        **Argument:**

        - `date` (str)
        """

        self._header['Date'] = date
        self.touch()

    # TODO test
    def timestamp(self):
        """Returns the timestamp of the date of the post.

        If the post does not have a date, 0 is returned.

        **Returns:** int
        """

        date = self.date()
        return int(hkutils.calc_timestamp(date)) if date != '' else 0

    # TODO test
    def datetime(self):
        """Returns the datetime object that describes the date of the post.

        If the post does not have a date, ``None`` is returned.

        **Returns:** datetime.datetime | ``None``
        """

        self._recalc_datetime()
        return self._datetime

    def _recalc_datetime(self):
        """Recalculates the `_datetime` data attribute if needed.

        See also the :ref:`lazy_data_calculation_pattern` pattern.
        """

        if self._datetime == hkutils.NOT_SET:
            timestamp = self.timestamp()
            if timestamp == 0:
                self._datetime = None
            else:
                struct_time = localtime_fun(timestamp)
                self._datetime = datetime.datetime(*list(struct_time)[0:6])

    # TODO test
    def date_str(self):
        """Returns the date converted to a string in local time.

        ``hklib.localtime_fun`` is used to calculate the local time.
        If the post does not have a date, an empty string is returned.

        **Returns:** str
        """

        timestamp = self.timestamp()
        if timestamp == 0:
            return ''
        else:
            return time.strftime('%Y.%m.%d. %H:%M', localtime_fun(timestamp))

    # TODO test
    def before(self, *dt):
        """Returns ``True`` if the post predates `dt`.

        Returns ``False`` if the post does not have date. Also returns
        ``False`` if the date of the Post is the given date.

        **Arguments:**

        - `*dt` ([object]) -- Argument list for datetime.datetime.

        **Returns:** bool

        **Example:** ::

            >>> p(1).before(2010, 1, 1)
            True
        """

        return (self.datetime() is not None and
                self.datetime() < datetime.datetime(*dt))

    # TODO test
    def after(self, *dt):
        """Returns ``True`` if `dt` predates the post.

        Returns ``True`` if the post does not have date. Also returns
        ``True`` if the date of the Post is the given date.

        This function is the exact opposite of :func:`before`: given `p` post
        and a `dt` datetime, exactly one of `p.before(dt)` and `p.after(dt)` is
        ``True``.

        **Arguments:**

        - `*dt` ([object]) -- Argument list for datetime.datetime.

        **Returns:** bool
        """

        return (self.datetime() is None or
                datetime.datetime(*dt) <= self.datetime())

    # TODO test
    def between(self, dts, dte):
        """Returns ``True`` if the post's date is between `dts` and `dte`.

        ``post.between(dts, dte)`` is equivalent to
        ``post.after(*dts) and post.before(*dte)``.

        **Arguments:**

        - `dts` ([object]) -- Argument list for datetime.datetime.
        - `dte` ([object]) -- Argument list for datetime.datetime.

        **Returns:** bool
        """

        return self.after(*dts) and self.before(*dte)

    # tag fields

    def tags(self):
        """Returns the tags of the post.

        The returned object should not be modified.

        **Returns:** [str]
        """

        return self._header['Tag']

    def set_tags(self, tags):
        """Sets the ``Tag`` attributes of the post.

        **Argument:**

        - `tags` (iterable(str))
        """

        self._header['Tag'] = sorted(tags)
        self.touch()

    # TODO test
    def add_tag(self, tag):
        """Adds a tag to the post.

        **Argument:**

        - `tag` (str)
        """

        assert(isinstance(tag, str))
        if not self.has_tag(tag):
            self._header['Tag'].append(tag)
            self._header['Tag'].sort()
        self.touch()

    # TODO test
    def remove_tag(self, tag):
        """Removes a tag from the post.

        **Argument:**

        - `tag` (str)
        """

        if self.has_tag(tag):
            self._header['Tag'].remove(tag)
        self.touch()

    # TODO test
    def has_tag(self, tag):
        """Returns whether the post has the given tag.

        **Argument:**

        - `tag` (str)

        **Returns:** bool
        """

        assert(isinstance(tag, str))
        return tag in self._header['Tag']

    # TODO test
    def has_tag_from(self, taglist):
        """Returns whether the post has one of the given tags.

        **Argument:**

        - `taglist` ([str])

        **Returns:** bool
        """

        for tag in taglist:
            if self.has_tag(tag):
                return True
        return False

    # flag fields

    def flags(self):
        """Returns the flags of the post.

        The returned object should not be modified.

        **Returns:** [str]
        """

        return self._header['Flag']

    def set_flags(self, flags):
        """Sets the flags of the post.

        **Argument:**

        - `flags` ([str])
        """

        assert(isinstance(flags, list))
        self._header['Flag'] = sorted(flags)
        self.touch()

    # deletion

    def is_deleted(self):
        """Returns whether the post is deleted.

        **Returns:** bool
        """

        return 'deleted' in self._header['Flag']

    def delete(self):
        """Deletes a post.

        All header attributes will be cleared except for the message id and the
        "deleted" flag. The body will be cleared, as well.
        """

        for key, value in self._header.items():
            if key == 'Message-Id':
                pass
            elif isinstance(value, str):
                self._header[key] = ''
            elif isinstance(value, list):
                self._header[key] = []
            else:
                raise hkutils.HkException, \
                      'Unknown type of field: %s' % (value,)
        self._header['Flag'] = ['deleted']
        self._body = ''
        self.touch()

    # meta field

    def meta_dict(self):
        """Returns the dictionary of meta texts in the post body.

        A meta text is a string or a key-value pair in the posts body. It
        should be enclosed within brackets, and nothing else should be in the
        line in which a meta text is. The key and value of the meta text are
        separated with a colon.

        **Returns:** {str: (str | ``None``)}

        **Examples of meta text:** ::

            [priority low]
            [important]
        """

        self._recalc_meta_dict()
        return self._meta_dict

    def _recalc_meta_dict(self):
        """Recalculates the dictionary of meta texts in the post body if
        needed.

        See also the :ref:`lazy_data_calculation_pattern` pattern.
        """

        if self._meta_dict is None:
            self._meta_dict = {}
            body_object = self.body_object()
            for segment in body_object.segments:
                if segment.is_meta and segment.key is not None:
                    self._meta_dict[segment.key] = segment.value

    # body object
    def body_object(self):
        """Returns the parsed body object.

        **Returns:** |Body|
        """

        self._recalc_body_object()
        return self._body_object

    def _recalc_body_object(self):
        """Recalculates the parsed body object."""

        if self._body_object is None:
            self._body_object = hkbodyparser.parse(self._body)

    # body

    def body(self):
        """Returns the body of the post.

        **Returns:** str
        """

        return self._body

    def set_body(self, body):
        """Sets the body of the post.

        **Argument:**

        - `body` (str)
        """

        self._body = body.rstrip() + '\n'
        self.touch()

    def body_contains(self, regexp):
        """Returns whether the body contains the given regexp.

        **Argument:**

        - `regexp` (regexp)

        **Returns:** bool
        """

        return re.search(regexp, self._body) != None

    # writing

    def write(self, f, force_print=set()):
        """Writes the post to a stream.

        **Arguments:**

        - `f` (|Writable|) -- The output stream.
        - `force_print` (set(str)) -- The attributes in this set will be
          printed even if they are empty strings.
        """

        def write_attr(key, value):
            """Writes an attribute to the output."""

            # Remove this attribute from the set of unprinted attributes, since
            # it is being printed now.
            unprinted_attrs.discard(key)

            t = (key, re.sub(r'\n', r'\n ', value))
            f.write('%s: %s\n' % t)

        def write_str(attr):
            """Writes a string attribute to the output."""
            if (self._header.get(attr, '') != '') or (attr in force_print):
                write_attr(attr, self._header[attr])

        def write_list(attr):
            """Writes a list attribute to the output."""
            for line in self._header.get(attr, []):
                write_attr(attr, line)

        unprinted_attrs = set(self._header.keys())

        write_str('Author')
        write_str('Subject')
        write_list('Tag')
        write_str('Message-Id')
        write_str('Parent')
        write_str('Date')
        write_list('Flag')

        # We print all other attributes that have not been printed yet
        for attr in sorted(unprinted_attrs):
            write_list(attr)

        f.write('\n')
        f.write(self._body)

    def write_str(self, force_print=set()):
        """Writes the post to a string.

        **Arguments:**

        - `force_print` (set(str)) -- The attributes in this set will be
          printed even if they are empty strings.

        **Returns:** str
        """

        sio = StringIO.StringIO()
        self.write(sio, force_print)
        result = sio.getvalue()
        sio.close()
        return result

    def read(self, f, silent=False):
        """Reads the post from a file object.

        **Arguments:**

        - `f` (file) -- File object to be read from.
        - `silent` (bool) --- Do not call :func:`PostDB.touch`.
        """

        # Parsing the post file and returning if it is the same as the post
        # object
        header, body = Post.parse(f, self._post_id)
        if header == self._header and body == self._body:
            return

        self._header, self._body = header, body
        self.touch(touch_postdb=(not silent))

    def read_str(self, post_text, silent=False):
        """Reads the post from a string.

        **Arguments:**

        - `post_text` (str) -- The text of the new contents of the post.
        - `silent` (bool) --- Do not call :func:`PostDB.touch`.
        """

        sio = StringIO.StringIO(post_text)
        self.read(sio, silent)
        sio.close()

    def postfile_str(self, force_print=set()):
        """Returns a string that contains the post in post file format.

        **Arguments:**

        - `force_print` (set(str)) -- The attributes in this set will be
          printed even if they are empty strings.

        **Returns:** str
        """

        sio = StringIO.StringIO()
        self.write(sio, force_print)
        s = sio.getvalue()
        sio.close()
        return s

    def save(self):
        """Saves the post."""

        assert(self._postdb != None)
        if self._modified:
            with open(self.postfilename(), 'w') as f:
                self.write(f)
                self._modified = False

    def load(self, silent=False):
        """(Re)loads the post from the disk.

        **Arguments:**

        - `silent` (bool) --- Do not call :func:`PostDB.touch`.
        """

        with open(self.postfilename(), 'r') as f:
            self.read(f, silent)

    # Filenames

    def postfilename(self):
        """Returns the name of the postfile in which the post is (or can be)
        stored, which is ``<heap dir>/<post index>.post``.

        **Returns:** str
        """

        return self._postdb.postfile_name(self)

    def htmlfilebasename(self):
        """Returns the base name of the HTML file that can be generated from
        the post, which is ``<heap id>/<post index>.html``

        **Returns:** str
        """

        return os.path.join(
                   self.heap_id(),
                   self.post_index() + '.html')

    def htmlfilename(self):
        """Returns the name of the HTML file that can be generated from the
        post, which is ``<html dir>/<heap id>/<post index>.html``.

        **Returns:** str
        """

        return os.path.join(
                   self._postdb.html_dir(),
                   self.htmlfilebasename())

    def htmlthreadbasename(self):
        """Returns the base name of the HTML file that can be generated from
        the thread, which is ``<heap id>/thread_<post index>.html``.

        This funcion shall be called only for root posts.

        **Returns:** str
        """

        assert(self._postdb.parent(self) == None)
        return os.path.join(
                   self.heap_id(),
                   'thread_' + self.post_index() + '.html')

    def htmlthreadfilename(self):
        """Returns the name of the HTML file that can be generated from the
        thread, which is ``<html dir>/<heap id>/thread_<post index>.html``.

        This funcion shall be called only for root posts.

        **Returns:** str
        """

        assert(self._postdb is not None)
        return os.path.join(
                   self._postdb.html_dir(),
                   self.htmlthreadbasename())

    def postfile_exists(self):
        """Returns whether the post file that belongs to the post exists.

        **Returns:** bool
        """

        if self._postdb == None:
            return False
        else:
            return os.path.exists(self.postfilename())

    # Post database

    # TODO test
    def add_to_postdb(self, post_id, postdb):
        """Adds the post to the `postdb`.

        **Arguments:**

        - `post_id` (|PostId| | None) -- The post will have this post id in the
          post database.
        - `postdb` (|PostDB| None) -- The post database to which the post
          should be added.
        """

        assert(self._postdb == None)
        self._post_id = Post.unify_post_id(post_id)
        self._postdb = postdb
        self.touch()

    # Python operators

    def __eq__(self, other):
        """Returns whether the post is equal to another post.

        Two posts are considered equal if they have the same post_id, header
        attributes and body.

        **Returns:** bool
        """

        if isinstance(other, Post):
            return self.post_id() == other.post_id() and \
                   self._header == other._header and \
                   self._body == other._body
        else:
            return False

    def __ne__(self, other):
        """Returns ``True`` if the posts are not equal."""
        if isinstance(other, Post):
            return not self == other
        else:
            return True

    def __lt__(self, other):
        """Returns whether the post is smaller than another post.

        The following method should be used to decide whether post1 or post2
        is greater:

        - If both of them have a timestamp and these are not equal, the post
          with the later timestamp is greater.
        - Otherwise the post with the greater heapid is the greater.

        **Arguments:**

        - `other` (|Post|) -- The post to compare this to.

        **Returns:** bool
        """

        assert(isinstance(other, Post))
        this_dt = self.datetime()
        other_dt = other.datetime()
        if this_dt and other_dt:
            if this_dt < other_dt:
                return True
            elif this_dt > other_dt:
                return False
        return self.post_id() < other.post_id()

    def __gt__(self, other):
        """Returns whether the post is greater than another post.

        **Arguments:**

        - `other` (|Post|) -- The post to compare this to.

        **Returns:** bool
        """

        assert(isinstance(other, Post))
        return other.__lt__(self)

    def __le__(self, other):
        """Returns whether the post is smaller or equal to another post.

        **Arguments:**

        - `other` (|Post|) -- The post to compare this to.

        **Returns:** bool
        """

        assert(isinstance(other, Post))
        if self == other:
            return True
        else:
            return self.__lt__(other)

    def __ge__(self, other):
        """Returns whether the post is greater or equal to another post.

        **Arguments:**

        - `other` (|Post|) -- The post to compare this to.

        **Returns:** bool
        """

        assert(isinstance(other, Post))
        return other.__le__(self)

    def __repr__(self):
        """Returns the string representation of the post.

        **Returns:** str

        **Example:** ::

            >>> str(p(0))
            <post my_heap/0>
        """

        if self._post_id is None:
            return '<post object without post id>'
        else:
            return '<post %s/%s>' % (self.heap_id(), self.post_index())

    # Misc

    # TODO test
    def remove_google_stuff(self):
        """Removes the Google banner from the post."""

        # old footer
        r = re.compile(r'--~--~---------~--~----~------------~-------~--~' + \
                       r'----~\n.*?\n' + \
                       r'-~----------~----~----~----~------~----~------~-' + \
                       r'-~---\n', re.DOTALL)
        self.set_body(r.sub('', self.body()))

        # new footer (since November 2009)
        footer_str = \
            (r'^--\s*'
              '^You received this message because you are subscribed to.*')
        footer_re = re.compile(footer_str, re.DOTALL | re.MULTILINE)
        self.set_body(footer_re.sub('', self.body()))
        self.set_body(self.body().strip() + '\n')

        # even newer footer (since 2010 April)
        footer_str = \
            (r'^--\s*'
              '^To unsubscribe, reply using "remove me" as the subject.')
        footer_re = re.compile(footer_str, re.MULTILINE)
        self.set_body(footer_re.sub('', self.body()))
        self.set_body(self.body().strip() + '\n')

        # even newer footer (since 2010 April)
        footer_str = \
            (r'^--\s*'
              '^Subscription settings: http://groups.google.com/.*')
        footer_re = re.compile(footer_str, re.MULTILINE)
        self.set_body(footer_re.sub('', self.body()))
        self.set_body(self.body().strip() + '\n')

    def remove_newlines_from_subject(self):
        """Removes newlines from the subject.

        The newline characters are removed together with the whitspace
        characters surrounding them, and they are replaced with one space.
        """

        r = re.compile(r'\n', re.MULTILINE)
        match = r.search(self.subject())
        if match is None:
            return # not a multiline subject
        else:
            r = re.compile(r'\s*\n\s*', re.MULTILINE)
            new_subject = r.sub(' ', self.subject())
            self.set_subject(new_subject)

    @staticmethod
    def parse_subject(subject):
        """Parses the subject of an email.

        Parses the tags and removes the "Re:" prefix and whitespaces.

        **Argument:**

        - `subject` (str)

        **Returns:** (str, [str]) -- The remaining subject and the tags.
        """

        # last_bracket==None  <=>  we are outside of a [tag]
        last_bracket = None
        brackets = []
        i = 0
        while i < len(subject):
            c = subject[i]
            if c == '[' and last_bracket == None:
                last_bracket = i
            elif c == ']' and last_bracket != None:
                brackets.append((last_bracket, i))
                last_bracket = None
            elif c != ' ' and last_bracket == None:
                break
            i += 1

        real_subject = subject[i:]
        if re.match('[Rr]e:', subject):
            subject = subject[3:]
        real_subject = real_subject.strip()

        tags = [ subject[first+1:last].strip() for first, last in brackets ]
        return real_subject, tags

    def normalize_subject(self):
        """Removes the tags from the subject and adds them to the post as real
        tags.

        Also removes the "Re:" prefix and whitespaces.
        """

        real_subject, tags = Post.parse_subject(self.subject())
        self.set_subject(real_subject)
        for tag in tags:
            self._header['Tag'].append(tag)


##### PostDBEvent #####

# TODO test
class PostDBEvent(object):

    """Represents an event that concerns the post database.

    **Data attributes:**

    - `type` (str) -- The type of the event. Currently always ``'touch'``.
    - `post` (|Post| | ``None``) -- The post that was touched.
    """

    # Unused arguments # pylint: disable=W0613
    def __init__(self,
                 type=hkutils.NOT_SET,
                 post=None):
        """Constructor.

        **Arguments:**

        - `type` (str) -- The type of the event.
        - `post` (|Post| | ``None``) -- The post that was touched.
        """

        super(PostDBEvent, self).__init__()
        hkutils.set_dict_items(self, locals())

    def __str__(self):
        """Returns the string representation of the postdb event.

        **Returns:** str

        **Example:** ::

            <PostDBEvent with the following attributes:
            type = touch
            post = <post my_heap/0>>
        """

        s = '<PostDBEvent with the following attributes:'
        for attr in ['type', 'post']:
            s += '\n%s = %s' % (attr, getattr(self, attr))
        s += '>'
        return s


##### PostDB #####

class PostDB(object):

    """The post database that stores and handles the posts.

    **Data attributes:**

    - `_heaps` ({|HeapId|: str}) -- Assigns directory names to the heaps in
      which they are stored in the file system.
    - `post_id_to_post` ({|PostId|: |Post|}) -- Stores the posts assigned to
      their post ids.
    - `messid_to_post_id` ({|Messageid|, |PostId|}) -- Stores which messids and
      post ids belong together.
    - `_next_post_index` ({(|HeapId|, str): int}) -- A dictionary that assigns
      the next free post indices to the heapid-prefix pairs. This is part of a
      caching mechanism. If a prefix is not found here, the whole lookup
      procedure is performed, then the results are added to this dictionary.
      The next free post index for a prefix is a number for which numbers in
      all other post indices with this prefix are smaller.
    - `_html_dir` (str) -- The directory that contains the generated HTML
      files.
    - `listeners` ([|PostDBEventListener|]) -- Listeners that are called when
      an event happens.

    **Lazy data attributes:**

    These data attributes are part of the :ref:`lazy_data_calculation_pattern`
    pattern.

    - `_posts` ([|Post|] | ``None``) -- All non-deleted posts as a list. It can
      be obtained using :func:`posts`.
    - `_all` (|PostSet| | ``None``) -- All non-deleted posts as a post set. It
      can be obtained using :func:`all`.
    - `_threadstruct` (|ThreadStruct| | ``None``) -- Assigns the childrens of a
      post to the post. Root posts are assigned to ``None``. It can be obtained
      using :func:`threadstruct`.
    - `_cycles` (|PostSet| | ``None``) -- Posts that are in a cycle in the
      thread structure. These posts will not be iterated by the
      :func:`iter_thread` function. It can be obtained using :func:`cycles`.
    - `_roots` (|PostSet| | ``None``) -- The root posts. It can be obtained
      using :func:`roots`.
    - `_threads` ({|Post|: |PostSet|} | ``None``) -- A dictionary that assigns
      posts in a thread to the root of the thread. It can be obtained using
      :func:`threads`.
    """

    # Constructors

    def __init__(self):
        """Constructor."""

        super(PostDB, self).__init__()
        self._heaps = {}
        self.post_id_to_post = {}
        self.messid_to_post_id = {}
        self._html_dir = None
        self._next_post_index = {}
        self.listeners = []
        self.touch()

    def add_post_to_dicts(self, post):
        """Adds the post to the `heapid_to_post` and `messid_to_post_id`
        dictionaries.

        **Arguments:**

        - `post` (|Post|)
        """

        post_id = post.post_id()
        self.post_id_to_post[post_id] = post
        messid = post.messid()
        if messid != '':
            # Don't store the messid if it is already used
            if messid in self.messid_to_post_id:
                messid_user_post = self.messid_to_post_id[messid]
                hkutils.log('Warning: post %s has message id %s, but that '
                            'message id is already used by post %s.' %
                            (post_id, messid, messid_user_post))
            else:
                self.messid_to_post_id[messid] = post_id
        self.touch()

    def remove_post_from_dicts(self, post):
        """Removed the post from the `heapid_to_post` and `messid_to_post_id`
        dictionaries.

        **Arguments:**

        - `post` (|Post|)
        """

        post_id = post.post_id()
        del self.post_id_to_post[post_id]
        messid = post.messid()
        if messid != '':
            # We should remove the messid from messid_to_post_id only if `post`
            # is stored as the owner of that messid
            if self.messid_to_post_id.get(messid) == post_id:
                del self.messid_to_post_id[post.messid()]
        self.touch()

    def load_heap(self, heap_id):
        """Loading a heap from the disk.

        **Arguments:**

        - `heap_id` (|HeapId|)
        """

        # We filter the posts in the given heap into `posts_in_heap` and remove
        # them from the post_id_to_post and messid_to_post_id
        posts_in_heap = {} # post index -> post
        for post_id, post in list(self.post_id_to_post.items()):
            if post_id[0] == heap_id:
                self.remove_post_from_dicts(post)
                posts_in_heap[post_id[1]] = post

        # We walk the heap directory and look for post files

        heap_dir = self._heaps[heap_id]
        if not os.path.isdir(heap_dir):
            raise hkutils.HkException('Directory %s not found.' % (heap_dir,))

        for file in os.listdir(heap_dir):

            if not file.endswith('.post'):
                continue # if `file` is not a post file, skip it

            post_index = file[:-5]
            post_id = (heap_id, post_index)
            post_file_absname = os.path.join(heap_dir, file)

            # We try to obtain the post which has the post id `post_id`. If
            # such a post exists (i.e. original_post_id_to_post contains
            # `post_id`), the post should be reloaded from the disk. This
            # way, if someone has a reference to post object, they will
            # refer to the reloaded posts. If there is no post with
            # `post_id`, a new Post object should be created.
            post = posts_in_heap.get(post_index)
            if post is None:
                post = Post.from_file(post_file_absname, post_id, self)
            else:
                post.load(silent=True)
            self.add_post_to_dicts(post)

        # We remove the entries about the given heap from the next_post_index
        # cache
        for curr_heap_id, prefix in list(self._next_post_index.keys()):
            if curr_heap_id == heap_id:
                del self._next_post_index[(curr_heap_id, prefix)]

        self.touch()

    def add_heap(self, heap_id, heap_dir):
        """Adds a heap to the post database and loads it.

        **Arguments:**

        - `heap_id` (|HeapId|)
        - `heap_dir` (str)
        """

        self._heaps[heap_id] = heap_dir
        if not os.path.exists(heap_dir):
            hkutils.log('Warning: post directory does not exists: "%s"' %
                        (heap_dir,))
            os.mkdir(heap_dir)
            hkutils.log('Post directory has been created.')
        self.load_heap(heap_id)

    def set_html_dir(self, html_dir):
        """Sets the HTML directory.

        **Argument:**

        - `html_dir` (str)
        """

        self._html_dir = html_dir
        if (html_dir is not None) and (not os.path.exists(html_dir)):
            hkutils.log('Warning: HTML directory does not exists: "%s"' %
                        (html_dir,))
            os.mkdir(html_dir)
            hkutils.log('HTML directory has been created.')

    @staticmethod
    def get_heaps_from_config(config):
        """Gets the details of the heaps from a configuration object.

        **Argument:**

        - `config` (|ConfigDict|)

        **Returns:** {|HeapId|: str} -- The directory that stores the heap is
        assigned to each heap.
        """

        heaps = {}
        for heap_config in config['heaps'].values():
            heaps[heap_config['id']] = heap_config['path']
        return heaps

    def read_config(self, config):
        """Configures the post database according to a configuration object.

        The `_html_dir` data attribute is set and heaps are added to the post
        database.

        **Argument:**

        - `config` (|ConfigDict|)
        """

        heaps = self.get_heaps_from_config(config)
        html_dir = config['paths']['html_dir']

        for heap_id, heap_dir in heaps.iteritems():
            self.add_heap(heap_id, heap_dir)
        self.set_html_dir(html_dir)

    # Modifications

    # TODO test
    def notify_listeners(self, event):
        """Notifies the listeners about an event.

        **Argument:**

        - `event` (|PostDBEvent|)
        """

        for listener in self.listeners:
            listener(event)

    # TODO test
    def touch(self, post=None):
        """If something in the database changes, this function should be
        called.

        If a post in the database is changed, this function will be invoked
        automatically, so there is no need to call it again.

        See also the :ref:`lazy_data_calculation_pattern` pattern.

        **Argument:**

        - `post` (|Post| | ``None``) -- The post concerned in the database
          modification. If not ``None``, the listeners will be notified.
        """

        self._posts = None
        self._all = None
        self._threadstruct = None
        self._cycles = None
        self._roots = None
        self._threads = None
        if post != None:
            self.notify_listeners(PostDBEvent(type='touch', post=post))

    def notify_changed_messid(self, post, old_messid, new_messid):
        """Should be called when the messid of a post changed.

        **Argument:**

        - `post` (|Post|) -- The post whose messid changed.
        - `old_messid` (|Messageid|) -- The old messid.
        - `new_messid` (|Messageid|) -- The new messid.
        """

        post_id = post.post_id()

        # We should remove the old messid from messid_to_post_id only if `post`
        # is stored as the owner of that messid
        if self.messid_to_post_id.get(old_messid) == post_id:
            del self.messid_to_post_id[old_messid]

        self.messid_to_post_id.setdefault(new_messid, post_id)

    # Get-set functions

    def has_post_id(self, post_id):
        """Returns whether there is a post with the given post id.

        **Argument:**

        - `post_id` (|PostId|)

        **Returns:** bool
        """

        return self.post_id_to_post.has_key(post_id)

    def heap_ids(self):
        """Returns the heap ids.

        **Returns:** [|HeapId|]
        """

        return self._heaps.keys()

    def has_heap_id(self, heap_id):
        """Returns whether there is a heap with the given heap id.

        **Argument:**

        - `heap_id` (|HeapId|)

        **Returns:** bool
        """

        return self._heaps.has_key(heap_id)

    def next_post_index(self, heap_id, prefix=''):
        """Returns the next free post index with the form ``prefix + int``.

        The "next" here means the post index with smallest number which is
        larger than all numbers present in all other post indices with the
        given prefix.

        This function uses a caching mechanism to avoid iterating over all
        posts on each calling. This cache is the `_next_heapid` data member,
        a dictionary where the keys are the prefixes. The empty prefix is
        always cached, while other prefixes are cached after the first lookup.

        **Arguments**:

        - `heap_id` (|HeapId|) -- The heap in which the next free post index
          should be found.
        - `prefix` (str) -- The prefix of the new heapid.

        **Returns**: |PostIndex|
        """

        cache = self._next_post_index
        key = (heap_id, prefix)

        # If the heap_id+prefix pair is not in the cache, we put it there
        if not cache.has_key(key):
            numbers = []
            for curr_post_id, _curr_post in self.post_id_to_post.iteritems():
                curr_heap_id, curr_post_index = curr_post_id
                if (curr_heap_id != heap_id or
                    not curr_post_index.startswith(prefix)):
                    continue
                number_str = curr_post_index[len(prefix):]
                try:
                    numbers.append(int(number_str))
                except ValueError:
                    pass
            if numbers == []:
                cache[(heap_id, prefix)] = 1
            else:
                cache[(heap_id, prefix)] = max(numbers) + 1

        # We find and return the first candidate index that is not used
        while True:
            next_candidate = prefix + str(cache[key])
            cache[key] += 1
            if not self.has_post_id((heap_id, next_candidate)):
                return next_candidate

    def invalidate_next_post_index_cache(self):
        """Invalidates the "next post index" cache."""

        self._next_post_index = {}

    def real_posts(self):
        """Returns the list of all posts, even the deleted ones.

        **Returns:** [|Post|]
        """

        return self.post_id_to_post.values()

    def posts(self):
        """Returns the list of all posts that are not deleted.

        The object returned by this function should not be modified.

        **Returns:** [|Post|]
        """

        self._recalc_posts()
        return self._posts

    def _recalc_posts(self):
        """Recalculates the `_posts` data attribute if needed.

        See also the :ref:`lazy_data_calculation_pattern` pattern.
        """

        if self._posts == None:
            self._posts = \
                [ p for p in self.real_posts() if not p.is_deleted() ]

    def postset(self, posts, default_heap=None):
        """Creates a PostSet that will contain the specified posts.

        **Arguments:**

        - `posts` (|PrePostSet|)
        - `default_heap` (|HeapId| | ``None``)

        **Returns:** |PostSet|
        """

        return PostSet(self, posts, default_heap)

    def post_by_post_id(self, post_id):
        """Finds a post by its post id.

        **Argument:**

        - `post_id` (|PostId|)

        **Returns:** |Post| | ``None``
        """

        Post.assert_is_post_id(post_id)
        return self.post_id_to_post.get(Post.unify_post_id(post_id))

    def post_by_messid(self, messid):
        """Finds a post by its message id.

        **Argument:**

        - `post_id` (|Messageid|)

        **Returns:** |Post| | ``None``
        """

        post_id = self.messid_to_post_id.get(messid)
        if post_id is None:
            return None
        else:
            return self.post_by_post_id(post_id)

    def post(self, prepost, default_heap=None, raise_exception=False):
        """Converts a |PrePost| into a |Post|.

        In other words, it returns the post specified by its post id or message
        id or post index or the post itself. See the definition of |PrePost| on
        how the conversion happens.

        **Arguments:**

        - `prepost` (|PrePost|)
        - `default_heap` (|HeapId| | ``None``)
        - `raise_exception` (bool) -- Specifies what should happen it the post
          is not found. If raise_exception is ``False``, ``None`` will be
          returned, otherwise a |PostNotFoundError| exception will be raised.

        **Returns:** |Post| | ``None``

        **Raises:**

        - |PostNotFoundError| -- The post was not found and `raise_exception`
          was ``True``.
        """

        # Is `prepost` the post itself?
        if isinstance(prepost, Post):
            return prepost

        # Try with `prepost` as post id
        if Post.is_post_id(prepost):
            post = self.post_by_post_id(prepost)
            if post is not None:
                return post

        # Try with `(default_heap, prepost)` as post id
        if (default_heap is not None
            and Post.is_post_id((default_heap, prepost))):

            post = self.post_by_post_id((default_heap, prepost))
            if post is not None:
                return post

        # Try with `prepost` as message id
        if isinstance(prepost, str):
            post = self.post_by_messid(prepost)
            if post is not None:
                return post

        if raise_exception:
            raise PostNotFoundError(prepost)
        else:
            return None

    # Save, reload

    def save(self):
        """Saves all the posts that needs to be saved."""
        for post in self.real_posts():
            post.save()

    def reload(self):
        """Reloads the database from the disk.

        The unsaved changes will be abandoned.
        """

        for heap_id in self._heaps:
            self.load_heap(heap_id)

    # New posts

    def add_new_post(self, post, heap_id, post_index=None, prefix=''):
        """Adds a new post to the postdb.

        **Arguments:**

        - `post` (|Post|) -- The post to be added to the database.
        - `heap_id` (|HeapId|) -- The heap to which the post is added.
        - `post_index` (str | ``None``) -- The post should have this post
          index. If ``None``, the post should get the next free post index
          that starts with `prefix` (see the definition of "next free post
          index" at :func:`next_post_index`).
        - `prefix` (str) -- If `post_index` is ``None``, the post should get
          the next free heapid that starts with `prefix`.

        **Returns:** |Post|
        """

        if post_index == None:
            post_index = self.next_post_index(heap_id, prefix=prefix)
        post.add_to_postdb((heap_id, post_index), self)
        self.add_post_to_dicts(post)
        return post

    # All posts

    def all(self):
        """Returns the post set of all posts that are not deleted.

        The object returned by this function should not be modified. On the
        other hand, the posts contained by it can be modified.

        **Returns:** |PostSet|
        """

        self._recalc_all()
        return self._all

    def _recalc_all(self):
        """Recalculates the `_all` data attribute if needed.

        See also the :ref:`lazy_data_calculation_pattern` pattern.
        """

        if self._all == None:
            self._all = PostSet(self, self.posts())

    # Thread structure

    def threadstruct(self):
        """Returns the thread structure of the post database.

        The object returned by this function should not be modified.

        **Returns:** |ThreadStruct|
        """

        self._recalc_threadstruct()
        return self._threadstruct

    def parent(self, post):
        """Returns the parent of the given post.

        If there is no such post in the database, it returns ``None``.

        **Argument:**

        - `post` (|Post|)

        **Returns:** |Post| | ``None``
        """

        assert(post in self.all())
        postparent = post.parent()

        if postparent == '':
            return None

        parentpost = self.post(postparent, default_heap=post.heap_id())

        # deleted posts do not count
        if parentpost is not None and parentpost.is_deleted():
            return None

        return parentpost

    def root(self, post):
        """Returns the :ref:`root <glossary_root>` of a post.

        **Argument:**

        - `post` (|Post|)

        **Returns:** |Post| | ``None`` -- ``None`` is returned when the post
        is in a cycle.
        """

        assert(post in self.all())
        posts = set([post])
        while True:
            parentpost = self.parent(post)
            if parentpost == None:
                return post
            elif parentpost in posts:
                return None # we found a cycle
            else:
                posts.add(parentpost)
                post = parentpost

    def children(self, post, threadstruct=None):
        """Returns the :ref:`children <glossary_parent_child>` of the given
        post.

        If `post` is ``None``, it returns the posts with no parents (i.e. whose
        parent is ``None``).

        **Arguments:**

        - `post` (|Post| | ``None``)
        - `threadstruct` (|ThreadStruct| | ``None``) -- The thread structure to
          be used. If ``None``, the thread structure of the post database is
          used. (Note: that is usually what we want.)

        **Returns:** [Post]
        """

        assert(post == None or post in self.all())

        if threadstruct is None:
            threadstruct = self.threadstruct()

        if post == None:
            children_post_ids = threadstruct.get(None, [])
        else:
            children_post_ids = threadstruct.get(post.post_id(), [])

        # This assertion can catch nasty bugs when the thread structure
        # contains a string as a value instead of a list.
        assert(isinstance(children_post_ids, list))

        return [ self.post(post_id) for post_id in children_post_ids ]

    def _recalc_threadstruct(self):
        """Recalculates the `_threadstruct` data attribute if needed.

        See also the :ref:`lazy_data_calculation_pattern` pattern.
        """

        if self._threadstruct == None:

            def add_timestamp(post):
                """Creates a (timestamp, post_id) pair from the post."""
                return (post.timestamp(), post.post_id())

            threads = {None: []} # dict(post_id,[answered:(timestamp,post_id)])
            for post in self.posts():
                parentpost = self.parent(post)
                parent_post_id = \
                    parentpost.post_id() if parentpost != None else None
                if parent_post_id in threads:
                    threads[parent_post_id].append(add_timestamp(post))
                else:
                    threads[parent_post_id] = [add_timestamp(post)]
            t = {}
            for post_id in threads:
                threads[post_id].sort()
                t[post_id] = \
                    [ post_id2 for timestamp, post_id2 in threads[post_id] ]
            self._threadstruct = t

    def iter_thread(self, post, threadstruct=None):
        """Iterates over a thread.

        The first element of the thread will be the post (except when the post
        is None, which will not be yielded). All the consequenses of post will
        be yielded in a preorder way. An example::

            1 <- 2 <- 3
              <- 4
            5

        The posts will be yielded in the following order: 1, 2, 3, 4, 5.

        The posts can be modified during the iteration.

        **Arguments:**

        - `post` (|Post| | ``None``) -- The post whose (sub)thread should be
          iterated.
        - `threadstruct` (|ThreadStruct| | ``None``) -- The thread structure to
          be used. If ``None``, the thread structure of the post database is
          used. (Note: that is usually what we want.)

        **Returns:** iterable(|Post|)
        """

        assert(post in self.all() or post == None)
        if post != None:
            yield post
        post_id = post.post_id() if post != None else None
        if threadstruct == None:
            threadstruct = self.threadstruct()
        for ch_post_id in threadstruct.get(post_id, []):
            for post2 in self.iter_thread(self.post(ch_post_id), threadstruct):
                yield post2

    def walk_thread(self, root, threadstruct=None, yield_inner=False):
        """Walks a thread and yields its posts.

        `walk_thread` walks the thread indicated by `root` with deep walk and
        yields |PostItem| objects. A post item contains a post and some
        additional information.

        The post item contains the post's position, which can be ``begin`` or
        ``end``. Each post is yielded twice during the walk. When the deep walk
        enters the subthread of a post, the post is yielded with ``begin``
        position. When the deep walk leaves its subthread, it is yielded with
        ``end`` position.

        The post item also contains the level of the post. The level of the
        root post is 0, the level of its children is 1, etc. When the `root`
        argument is ``None`` and the whole database is walked, the level of all
        root posts is 0.

        **Arguments:**

        - `root` (|Post| | ``None``) -- The root of the thread to be walked. If
          ``None``, the whole thread structure is walked.
        - `threadstruct` (|ThreadStruct| | ``None``) -- The thread structure to
          be used. If ``None``, the thread structure of the post database will
          be used. (Note: that is usually what we want.)

        **Returns:** iterable(|PostItem|)

        **Example:**

        The thread structure walked::

            0 <- 1 <- 2
              <- 3
            4

        The post items yielded (indentation is there only to help the human
        reader)::

            <PostItem: pos=begin, heapid='0', level=0>
              <PostItem: pos=begin, heapid='1', level=1>
                <PostItem: pos=begin, heapid='2', level=2>
                <PostItem: pos=end, heapid='2', level=2>
              <PostItem: pos=end, heapid='1', level=1>
              <PostItem: pos=begin, heapid='3', level=1>
              <PostItem: pos=end, heapid='3', level=1>
            <PostItem: pos=end, heapid='0', level=0>
            <PostItem: pos=begin, heapid='4', level=0>
            <PostItem: pos=end, heapid='4', level=0>
        """

        # `stack` is initialized with "beginning" `PostItem`s (i.e.
        # ``item.pos == 'begin'``).
        # During the execution of the loop:
        #  - the stack is popped,
        #  - whatever we got, we yield it,
        #  - if it is a beginning `PostItem`, we push the matching ending
        #    `PostItem`
        #  - then push a beginning `PostItem` for all the children of the
        #    popped item's post
        # This means that we will yield the ending `PostItem` once all the
        # children (and their children etc.) are processed.

        assert(root in self.all() or root == None)
        if threadstruct == None:
            threadstruct = self.threadstruct()

        if root is None:
            roots = [ PostItem(pos='begin', post=root, level=0)
                      for root in self.children(None, threadstruct) ]
            stack = list(reversed(roots))
        else:
            stack = [ PostItem(pos='begin', post=root, level=0) ]

        while len(stack) > 0:

            postitem = stack.pop()
            yield postitem

            if postitem.pos == 'begin':

                if yield_inner:
                    postitem_inner = postitem.copy()
                    postitem_inner.pos = 'inner'
                    yield postitem_inner

                # pushing the closing pair of postitem into the stack
                postitem_end = postitem.copy()
                postitem_end.pos = 'end'
                stack.append(postitem_end)

                # pushing the children of the post into the stack
                new_level = postitem.level + 1
                child_postitems = \
                    [ PostItem(pos='begin', post=child, level=new_level)
                      for child in self.children(postitem.post, threadstruct) ]
                stack += reversed(child_postitems)

    def cycles(self):
        """Returns the posts that are in a :ref:`cycle <glossary_cycle>` of the
        thread structure.

        **Returns:** |PostSet|
        """

        self._recalc_cycles()
        return self._cycles

    def has_cycle(self):
        """Returns whether there is a :ref:`cycle <glossary_cycle>` in the
        thread structure.

        **Returns:** bool
        """

        return len(self.cycles()) != 0

    def _recalc_cycles(self):
        """Recalculates the `_cycles` data attribute if needed.

        See also the :ref:`lazy_data_calculation_pattern` pattern.
        """

        if self._cycles == None:
            self._cycles = self.all().copy()
            # A post is in a cycle <=> it cannot be accessed by iter_thread
            for post in self.iter_thread(None):
                self._cycles.remove(post)

    def walk_cycles(self):
        """Walks and yields post items for the posts in :ref:`cycles
        <glossary_cycle>`.

        The ``pos`` attribute of the post items will be ``'flat'``. The
        ``level`` attribute will be 0.

        **Returns:** iterable(|PostItem|)
        """

        for post in self.cycles().sorted_list():
            yield PostItem(pos='flat', post=post, level=0)

    def roots(self):
        """Returns the :ref:`root <glossary_root>` posts (i.e. the ones with no
        parent).

        **Returns:** |PostSet|
        """

        self._recalc_roots()
        return self._roots

    def _recalc_roots(self):
        """Recalculates the `_roots` data attribute if needed.

        See also the :ref:`lazy_data_calculation_pattern` pattern.
        """

        if self._roots == None:
            self._roots = [ self.post(post_id)
                            for post_id in self.threadstruct()[None] ]

    def threads(self):
        """Returns a dictionary that assigns posts in a thread to the
        :ref:`root <glossary_root>` of the thread.

        **Returns:** {|Post|: |PostSet|}
        """

        self._recalc_threads()
        return self._threads

    def _recalc_threads(self):
        """Recalculates the `_threads` data attribute if needed.

        See also the :ref:`lazy_data_calculation_pattern` pattern.
        """

        if self._threads == None:
            self._threads = {}
            for root in self.roots():
                self._threads[root] = self.postset(root).expf()

    def move(self, post, new_post_id, placeholder=False):
        """Moves a post by changing its post id.

        This method should be used with care.

        **Arguments:**

        - `post` (|Post|)
        - `new_post_id` (|PrePostId|) -- The new post id of the post.
        - `placeholder` (bool) -- If ``True``, a placeholder post will be
          created with the original post id of `post`. The placeholder post
          will be marked as deleted.
        """

        Post.assert_is_post_id(new_post_id)
        new_post_id = Post.unify_post_id(new_post_id)
        new_heap_id, new_post_index = new_post_id

        if self.post(new_post_id) is not None:
            raise hkutils.HkException, \
                  ('The given post id is already occupied: %s' %
                   (new_post_id,))

        if not self.has_heap_id(new_heap_id):
            raise hkutils.HkException, \
                  ('No such heap: %s' % (new_heap_id,))

        old_post_id = post.post_id()

        def new_reference(source_post, old_post_ref, old_post_id, new_post_id):
            """Returns how a post reference should change when a post's id is
            renamed.

            **Arguments:**

            - `source_post` (|Post|) -- The post that contains the post
              reference.
            - `old_post_ref` (str) -- The post reference whose modification is
              in question.
            - `old_post_id` (|PostId|) -- The old post id of the post to be
              renamed.
            - `new_post_id` (|PostId|) -- The new post id of the post to be
              renamed.

            **Returns:** str | ``None`` -- If ``None`` is returned, the post
            reference should not be changed. If a string is returned, it is the
            new post reference that will be correct after the post was moved.
            It is a prepost id; it has one of the following forms: either
            ``"<post index>"`` or ``"<heap id>/<post index>"``.
            """

            old_heap_id, old_post_index = old_post_id
            old_post_id_str = '%s/%s' % old_post_id
            new_heap_id, new_post_index = new_post_id
            new_post_id_str = '%s/%s' % new_post_id

            # The reference is a full post id to the moving post
            if old_post_ref == old_post_id_str:
                return new_post_id_str

            # The reference if a post index to the moving post
            elif (old_post_ref == old_post_index and
                  source_post.heap_id() == old_heap_id):

                # The target post stays in the heap
                if new_heap_id == old_heap_id:
                    return new_post_index

                # The target post moves to another heap, so we need to set the
                # full post id
                else:
                    return new_post_id_str


        for curr_post in self.posts():

            # Modifying the Parent header item if necessary
            new_ref = new_reference(curr_post, curr_post.parent(),
                                    old_post_id, new_post_id)
            if new_ref is not None:
                curr_post.set_parent(new_ref)

            # Modifying the heap links if necessary
            body_object = curr_post.body_object()
            modified = False
            for segment in body_object.segments:
                if segment.type == 'heap_link':
                    new_ref = \
                        new_reference(curr_post, segment.get_prepost_id_str(),
                                      old_post_id, new_post_id)
                    if new_ref is not None:
                        segment.set_prepost_id_str(new_ref)
                        modified = True

            if modified:
                body_str = body_object.body_str()
                curr_post.set_body(body_str)

        self.remove_post_from_dicts(post)
        post._post_id = new_post_id
        post.touch()
        self.add_post_to_dicts(post)

        if placeholder:
            placeholder_post = Post.create_empty(old_post_id, self)
            placeholder_post.delete()
            self.add_post_to_dicts(placeholder_post)

        self.touch()

    # Filenames

    def postfile_name(self, post):
        """Returns the string ``<heap dir>/<post index>.post``, which is the
        name of the file in which the post should be stored.

        **Argument:**

        - `post` (|Post|)

        **Returns:** str
        """

        return os.path.join(
                   self._heaps[post.heap_id()],
                   post.post_index() + '.post')

    def html_dir(self):
        """Return the directory in which the generator HTML files are stored.

        **Returns:** str | ``None``
        """

        return self._html_dir


class PostItem(object):

    """Represents a post when performing walk on posts.

    Used for example by :func:`PostDB.walk_thread`. For information about what
    exactly the values of the data attributes will be during a walk, please
    read the documenation of the function that performs the walk.

    **Data attributes:**

    - `pos` (str) -- The position of the post item. Possible values:
      ``'begin'``, ``'end'``, ``'flat'``.
    - `post` (Post) -- The post represented by the post item.
    - `level` (int) -- The level of the post.
    """

    def __init__(self, pos, post, level=0):
        """Constructor.

        **Arguments:**

        - `pos` (str) -- Initializes the `pos` data attribute.
        - `post` (Post) -- Initializes the `post` data attribute.
        - `level` (int) -- Initializes the `level` data attribute.
        """

        assert(pos in ['begin', 'end', 'inner', 'flat'])
        self.pos = pos
        self.post = post
        self.level = level

    def copy(self):
        """Creates a shallow copy of the post item.

        **Returns:** |PostItem|
        """

        p = PostItem(pos=self.pos,
                     post=self.post,
                     level=self.level)
        p.__dict__ = self.__dict__.copy()
        return p

    def __str__(self):
        """Returns the string representation of the PostItem.

        **Returns:** str

        **Example:** ``<PostItem: pos=begin, heapid='42', level=0>``
        """

        post_id = self.post.post_id()
        if post_id is None:
            post_id_str = 'None'
        else:
            post_id_str = "%s/%s" % post_id

        s = ('<PostItem: pos=%s, post_id=%s, level=%d' %
             (self.pos, post_id_str, self.level))
        attrs = self.__dict__.copy()
        del attrs['pos']
        del attrs['post']
        del attrs['level']

        for attr, value in attrs.items():
            s += ', %s=%s' % (attr, value)

        s += '>'
        return s

    def __eq__(self, other):
        """Returns whether the post item is equal to another post item.

        Two post items are considered equal if they have the same position,
        level, etc. and point to the same post.

        **Returns:** bool
        """

        return self.__dict__ == other.__dict__


##### PostSet #####

class PostSet(set):

    """A set of posts.

    **Data attributes:**

    - `_postdb` (|PostDB|) -- The post database.
    """

    def __init__(self, postdb, posts, default_heap=None):
        """Constructor.

        **Arguments:**

        - `postdb` (| PostDB|) -- The post database.
        - `posts` ( |PrePostSet|) -- The set of posts to be initially
          contained.
        - `default_heap` (|HeapId| | ``None``) -- Default heap for `posts`.
        """

        initpostset = PostSet._to_set(postdb, posts, default_heap)
        super(PostSet, self).__init__(initpostset)
        self._postdb = postdb

    def empty_clone(self):
        """Returns an empty post set that has the same post database as this
        one.

        **Returns:** |PostSet|
        """

        return PostSet(self._postdb, [])

    def copy(self):
        """Returns a copy of the post set.

        The returned |PostSet| object will be different, but the posts
        contained by it will be the same objects.

        **Returns:** |PostSet|
        """

        return PostSet(self._postdb, self)

    @staticmethod
    def _to_set(postdb, prepostset, default_heap=None):
        """Converts a |PrePostSet| object to a set of posts.

        **Arguments:**

        - `prepostset` (|PrePostSet|) -- The PrePostSet to be converted.

        **Returns:** set(|Post|) | PostSet
        """

        def is_prepost(prepost):
            return (isinstance(prepost, str) or
                    isinstance(prepost, int) or
                    isinstance(prepost, tuple) or
                    isinstance(prepost, Post))

        if isinstance(prepostset, PostSet):
            return prepostset
        elif is_prepost(prepostset): # we have a prepost
            return set([postdb.post(prepostset,
                                    default_heap,
                                    raise_exception=True)])
        else: # we have a list of preposts
            result = set()
            for prepost in prepostset:
                if prepost is None:
                    continue
                if is_prepost(prepost):
                    result.add(postdb.post(prepost,
                                           default_heap,
                                           raise_exception=True))
                else:
                    raise hkutils.HkException, \
                          ("Object type not compatible with Post: %s" % \
                           (prepost,))
            return result

    def is_set(self, s):
        """The given set equals to the set of contained posts.

        **Arguments:**

        - `s` (|PrePostSet|)

        **Returns:** bool
        """

        return set.__eq__(self, PostSet._to_set(self._postdb, s))

    def __getattr__(self, funname):
        """Returns delegates when `funname` is ``'forall'`` or ``'collect'``.

        **Argument:**

        - `funname` (str)

        **Returns:** :class:`PostSetForallDelegate` |
                     :class:`PostSetCollectDelegate`

        **Raises:** AttributeError
        """

        if funname == 'forall':
            return PostSetForallDelegate(self)
        if funname == 'collect':
            return PostSetCollectDelegate(self)
        else:
            raise AttributeError, \
                  ("'PostSet' object has no attribute '%s'" % funname)

    def expb(self):
        """Expand backwards: returns all :ref:`ancestors <glossary_ancestor>`
        of the posts in the post set.

        **Returns:** |PostSet|
        """

        result = PostSet(self._postdb, [])
        for post in self:
            # if post is in result, then it has already been processed
            # (and all its consequences has been added to result)
            if post not in result:
                while True:
                    result.add(post)
                    post = self._postdb.parent(post)
                    if post == None:
                        break
        return result

    def expf(self):
        """Expand forward: returns all :ref:`descendants <glossary_descendant>`
        of the posts in the post set.

        **Returns:** |PostSet|
        """

        result = PostSet(self._postdb, [])
        for post in self:
            # if post is in result, then it has already been processed
            # (and all its consequences has been added to result)
            if post not in result:
                for post2 in self._postdb.iter_thread(post):
                    result.add(post2)
        return result

    def exp(self):
        """Expand: returns all :ref:`thread mates <glossary_thread_mate>` of
        the posts in the post set.

        **Returns:** |PostSet|
        """

        return self.expb().expf()

    def sorted_list(self):
        """Returns the sorted list of posts in the post set.

        **Returns:** [|Post|]
        """

        posts = list(self)
        posts.sort()
        return posts

    # Overriding set's methods

    def construct(self, methodname, other):
        """Constructs a new post set by calling the specified method of the set
        class with `self` and `other`.

        **Arguments:**

        - `methodname` (str) -- A name of a method of the `set` class
        - `other` (|PrePostSet|)

        **Returns:** |PostSet|
        """

        try:
            other = self._postdb.postset(other)
        except TypeError:
            return NotImplemented
        result = getattr(set, methodname)(self, other)
        result._postdb = self._postdb
        return result

    # TODO doc
    def __and__(self, other):
        return self.construct('__and__', other)

    # TODO doc
    def __eq__(self, other):
        if isinstance(other, PostSet):
            return set.__eq__(self, other)
        else:
            return False

    # TODO doc
    def __ne__(self, other):
        return not self == other

    # TODO doc
    def __or__(self, other):
        return self.construct('__or__', other)

    # TODO doc
    def __sub__(self, other):
        return self.construct('__sub__', other)

    # TODO doc
    def __xor__(self, other):
        return self.construct('__xor__', other)

    # TODO doc
    def difference(self, other):
        return self.construct('difference', other)

    # TODO doc
    def intersection(self, other):
        return self.construct('intersection', other)

    # TODO doc
    def symmetric_difference(self, other):
        return self.construct('symmetric_difference', other)

    # TODO doc
    def union(self, other):
        return self.construct('union', other)

    # TODO doc
    def __rand__(self, other):
        return self.construct('__rand__', other)

    # TODO doc
    def __ror__(self, other):
        return self.construct('__ror__', other)

    # TODO doc
    def __rsub__(self, other):
        return self.construct('__rsub__', other)

    # TODO doc
    def __rxor__(self, other):
        return self.construct('__rxor__', other)

    # Methods inherited from set.
    #
    # These functions does not have to be overriden, because they do not
    # construct a new PostSet object (as opposed to most of the overriden
    # functions).
    #
    # __contains__(...)
    # __iand__(...)
    # __ior__(...)
    # __isub__(...)
    # __ixor__(...)
    # __iter__(...)
    # __len__(...)
    # add(...)
    # clear(...)
    # difference_update(...)
    # discard(...)
    # intersection_update(...)
    # issubset(...)
    # issuperset(...)
    # pop(...)
    # remove(...)
    # symmetric_difference_update(...)
    # update(...)

    #  Methods inherited from set which should not be used (yet?)
    #
    # TODO: These method should be reviewed whether they should be inherited,
    # overriden or removed.
    #
    # __cmp__(...)
    # __ge__(...)
    # __getattribute__(...)
    # __gt__(...)
    # __hash__(...)
    # __le__(...)
    # __lt__(...)
    # __reduce__(...)
    # __repr__(...)


class PostSetForallDelegate(object):

    """A delegate of posts.

    If a method is called on a PostSetForallDelegate object, it will forward
    the call to the posts it represents. A PostSetForallDelegate object can
    be obtained from a |PostSet| object via its "forall" attribute.

    **Data attribute:**

    - `_postset` (|PostSet|) -- The post set to work on.
    """

    def __init__(self, postset):
        """Constructor.

        **Argument:**

        - `postset` (|PostSet|) -- The post set to work on.
        """

        super(PostSetForallDelegate, self).__init__()
        self._postset = postset

    def __call__(self, forallfun):
        """Performs `forallfun` on each post.

        **Argument:**

        - `forallfun` (fun(|Post|))
        """
        for post in self._postset:
            forallfun(post)

    def __getattr__(self, funname):
        """Returns a function that calls the `funname` method of all the posts
        in the post set when called with the given arguments.

        **Argument:**

        - `funname` (str)

        **Returns:** fun(\\*args, \\*\\*kw)
        """

        def forall_fun(*args, **kw):
            for post in self._postset:
                getattr(post, funname)(*args, **kw)
        return forall_fun


class PostSetCollectDelegate(object):

    """A delegate of posts.

    It can be used to collect posts with a specified property from a post set.
    A PostSetCollectDelegate object can be obtained from a |PostSet| object
    via its "collect" attribute.

    Collecting posts can be done in three ways:

    1. The PostSetCollectDelegate class has some functions that collect
       specific posts.

       The following example collects the posts that are roots of a thread
       ("collect" is a PostSetCollectDelegate object)::

           ps = collect.is_root()

    2. If a method is called on a PostSetCollectDelegate object which is not
       a method of the PostSetCollectDelegate class, the object will invoke the
       given method with the given arguments on all the posts of the postset,
       and returns those in a new postset whose method returned true.

       An example that collects the posts that has 'mytag' tag::

            ps = collect.has_tag('mytag')

    3. The user can call the PostSetCollectDelegate object with any function as
       an argument that gets a Post and returns a boolean.

       An example that collects the posts that has 'mytag' tag but does not
       have 'other_tag' tag::

            ps = collect(lambda p: p.has_tag('mytag') and \\
                                   not p.has_tag('other_tag'))

    **Data attributes:**

    - `_postset` (|PostSet|) -- The post set to work on.
    """

    def __init__(self, postset):
        """Constructor.

        **Argument:**

        - `postset` (|PostSet|) -- Initialises _postset.
        """

        super(PostSetCollectDelegate, self).__init__()
        self._postset = postset

    def __call__(self, filterfun):
        """Returns posts with which `filterfun` returns true.

        **Argument:**

        - `filterfun` (fun(|Post|) -> bool)

        **Returns:** |PostSet|
        """

        result = self._postset.empty_clone()
        for post in self._postset:
            post_true = filterfun(post)
            assert(isinstance(post_true, bool))
            if post_true:
                result.add(post)
        return result

    def is_root(self):
        """Returns the posts that are roots of a thread."""
        return self.__call__(lambda p: self._postset._postdb.parent(p) == None)

    def __getattr__(self, funname):
        """Returns a function that collects posts whose return value is true
        when their "funname" method is called with the given arguments.

        **Argument:**

        - `funname` (str)

        **Returns:** fun(\\*args, \\*\\*kw) -> |PostSet|
        """

        def collect_fun(*args, **kw):
            return self.__call__(lambda p: getattr(p, funname)(*args, **kw))
        return collect_fun
