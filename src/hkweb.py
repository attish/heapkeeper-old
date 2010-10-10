# -*- coding: utf-8 -*-

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

"""Module for dynamic web output in Heapkeeper.

This module adds a facility to start a web application (complete with its own
web server) from |hkshell| via a simple command.

The output is fully customizable the same way as the static output.

hkweb can be started from the |hkshell| in the following way:

    >>> import hkweb
    >>> hkweb.start()

|hkweb| is executed in a separate daemon thread. When |hkshell| is closed, the
|hkweb| thread is automatically stopped.
"""


import base64
import exceptions
import itertools
import json
import sys
import datetime
import threading
import web as webpy

import hkutils
import hklib
import hkgen
import hksearch
import hkshell


##### Global variables #####

urls = [
    r'/', 'Index',
    r'/(external/[A-Za-z0-9_./-]+)', 'Fetch',
    r'/(static/[A-Za-z0-9_./-]+)', 'Fetch',
    r'/(plugins/[A-Za-z0-9_.-]+/static/[A-Za-z0-9_./-]+)', 'Fetch',
    r'/posts/(.*)', 'Post',
    r'/raw-post-bodies/(.*)', 'RawPostBody',
    r'/raw-post-text/(.*)', 'RawPostText',
    r'/set-post-body/(.*)', 'SetPostBody',
    r'/get-post-body/(.*)', 'GetPostBody',
    r'/set-raw-post/(.*)', 'SetRawPost',
    r'/show-json', 'ShowJSon',
    r'/search.*', 'Search',
    ]

log = []


##### HTTP basic authentication #####

def default_deny(realm, username, password, redirect_url):
    # Unused arguments 'password', 'realm', 'redirect_url'
    # pylint: disable-msg=W0613
    hkutils.log('Access denied for user %s.' % username)
    return 'Authentication needed!'

def make_auth(verifier, realm="Heapkeeper",
              deny=default_deny, redirect_url="/"):
    """Creates a decorator that allows the decorated function to run
    only after a successful HTTP basic authentication. The
    authentication is performed by a supplied verifier function.

    **Arguments:**

    - `verifier` (fun(str, str, str)) -- Verifies if the
      authentication is valid and returns the result as bool.
    - `realm` (str) -- The user will see this in the login box.
    - `deny` (fun(str, str, str, str)) -- Function called on failure.
    - `redirect_url` (str) -- Unsuccessful auth throws the user here.
    """

    def decorator(func, *args, **keywords):
        # Unused arguments 'args', 'keywords'
        # pylint: disable-msg=W0613
        def f(*args, **keywords):
            username = None
            password = None
            try:
                b64text = webpy.ctx.env['HTTP_AUTHORIZATION'][6:]
                plaintext = base64.b64decode(b64text)
                colonpos = plaintext.index(':')
                username = plaintext[:colonpos]
                password = plaintext[colonpos + 1:]
            except:
                # TODO: handle absent HTTP_AUTHORIZATION field
                # separately from failed base64 decoding or missing
                # colon in plaintext.
                pass
            if verifier(username, password, realm):
                last_access[username] = datetime.datetime.now()
                # Attach the user's name to the server. The way to
                # find the server depends on whether the function is a
                # bound method.
                if hasattr(func, 'im_self'):
                    func.im_self.user = username
                else:
                    args[0].user = username
                return func(*args, **keywords)
            else:
                webpy.ctx.status = '401 UNAUTHORIZED'
                webpy.header('WWW-Authenticate',
                             'Basic realm="%s"'  % webpy.websafe(realm))
                return deny(realm, username, password, redirect_url)
        return f
    return decorator

def make_minimal_verifier(correct_username, correct_password):
    # Unused argument 'realm' # pylint: disable-msg=W0613
    def minimal_verifier(username, password, realm):
        """A minimalistic verifier with a hardcoded user/password pair."""

        return (username == correct_username and
                password == correct_password)
    return minimal_verifier

def account_verifier(username, password, realm):
    # Unused argument 'realm' # pylint: disable-msg=W0613
    """A verifier that uses the account list in the config file."""

    accounts = hkshell.options.config['accounts']
    if username in accounts:
        correct_password = accounts[username]
        return correct_password == password
    return False

def enable_authentication(username=None, password=None):
    """Enables authentication with single or account-based
    username/password pair.

    If username is omitted, authentication will be based on account
    data specified in the config file. If both username and password
    are specified, these will be the only acceptable username/password
    pair. If password is omitted, it will be the same as the username
    (not recommended).

    **Argument:**

    - `username` (str)
    - `password` (str)
    """

    global auth
    if username is None:
        auth = make_auth(verifier=account_verifier)
    else:
        if password is None:
            password = username
        auth = make_auth(verifier=make_minimal_verifier(username, password))

# By default, auth is an identity decorator, that is, authentication
# is disabled. Enable it using `hkweb.enable_authentication()`.

auth = lambda f: f

# This dict keeps track of the time of the last access by users.
last_access = {}

def add_auth(server, auth_decorator):
    """Add authentication to a web.py server class."""

    server._postdb = hkshell.postdb()
    server.original_GET = getattr(server, 'GET', None)
    server.original_POST = getattr(server, 'POST', None)
    if server.original_GET:
        server.GET = auth_decorator(server.original_GET)
    if server.original_POST:
        server.POST = auth_decorator(server.original_POST)

def last():
    """Display the time of the last access in a conveniently
    interpretable ("human-readable") format."""

    access_datetimes = last_access.values()
    if len(access_datetimes) == 0:
        hkutils.log("Access list is empty.")
        return
    access_datetimes.sort()
    last_datetime = access_datetimes[-1]
    now_datetime = datetime.datetime.now()
    last_str = hkutils.humanize_timedelta(now_datetime - last_datetime)
    hkutils.log("Last access was %s ago." % (last_str,))


##### Utility functions #####

JSON_ESCAPE_CHAR = '\x00'

def get_web_args():
    """Gets the arguments transferred as a JSON object from the web.py module.

    **Returns:** json_object -- It will contain UTF-8 encoded strings instead
    of unicode objects.
    """

    result = {}
    for key, value in webpy.input().items():
        try:

            # If `value` starts with the JSON escape character, a JSON object
            # should be described after the escape character. (E.g. the value
            # '\x00[1,2]' (given as '%00[1,2]' in the query parameter) will
            # become [1, 2]). Otherwise `value` is a string.
            if len(value) > 1 and value[0] == JSON_ESCAPE_CHAR:
                json_value_unicode = json.loads(value[1:])
            else:
                json_value_unicode = value

            json_value = hkutils.json_uutf8(json_value_unicode)
            result[key] = json_value
        except exceptions.ValueError, e:
            raise hkutils.HkException(
                      'Error: the "%s" parameter is not a valid JSON object: '
                      '%s' % (key, value))
    return result


##### Generator classes #####

class WebGenerator(hkgen.Generator):
    """A Generator that is modified according to the needs of dynamic web page
    generation."""

    def __init__(self, postdb):
        hkgen.Generator.__init__(self, postdb)
        self.options.cssfiles.append("static/css/hkweb.css")
        self.options.favicon = '/static/images/heap.png'
        self.js_files = ['/external/jquery.js',
                         '/external/json2.js',
                         '/static/js/hkweb.js']

    def print_html_head_content(self):
        """Prints the content in the HTML header.

        **Returns:** |HtmlText|
        """

        stylesheets = \
            ['    <link rel="stylesheet" href="/%s" type="text/css" />\n' %
             (css,)
             for css in self.options.cssfiles]

        favicon = ('    <link rel="shortcut icon" href="%s">\n' %
                   (self.options.favicon))

        return (stylesheets, favicon)

    def print_postitem_link(self, postitem):
        """Prints the thread link of the post item in hkweb-compatible form."""

        return ('/posts/', postitem.post.post_id_str())

    def print_searchbar(self):
        return ('<center>\n'
                '<div class="searchbar-container">\n'
                '  <form id="searchbar-container-form" action="/search"'
                ' method="get">\n'
                '    <input id="searchbar-term" name="term" type="text"'
                ' size="40"/>\n'
                '    <input type="submit" value="Search the heaps" />\n'
                '  </form>\n'
                '</div>\n'
                '</center>\n')

    def print_js_links(self):
        return \
            [('<script type="text/javascript" src="%s"></script>\n' %
              (js_file,)) for js_file in self.js_files]


class IndexGenerator(WebGenerator):
    """Generator that generates the index page."""

    def __init__(self, postdb):
        WebGenerator.__init__(self, postdb)

    def print_main(self):
        return (self.print_searchbar(),
                self.print_main_index_page(),
                self.print_js_links())


class PostPageGenerator(WebGenerator):
    """Generator that generates post pages.

    The generated post pages show the thread of the post. With the help of
    Javascript, the web browser is asked to jump to the relevant post.
    """

    def __init__(self, postdb):
        WebGenerator.__init__(self, postdb)

    def set_post_id(self, post_id):
        post = self._postdb.post(post_id)
        if post is None:
            return 'No such post: "%s"' % (post_id,)
        if post.is_deleted():
            return 'The post was deleted: "%s"' % (post_id,)
        root = self._postdb.root(post)
        if root is None:
            return 'The post is in a cycle: "%s"' % (post_id,)
        self._requested_post = post
        heap_id, post_index = post.post_id()
        id = 'post-summary-' + heap_id + '-' + post_index
        self.options.html_body_attributes += \
            'onload="ScrollToId(\'' + id + '\');"'
        self.options.html_title = post.subject()

        self._root = root
        self._post = post

    def print_post_page(self, post_id):
        result = self.set_post_id(post_id)
        if result is not None:
            return result

        # Post link example: /#post-summary-my_heap-12
        heap_id, post_index = self._post.post_id()
        post_link = ('/#post-summary-' + heap_id + '-' + post_index)

        buttons = \
            self.enclose(
                (self.enclose(
                     self.print_link(post_link, 'Back to the index'),
                     class_='button global-button'), '\n',
                 self.enclose(
                     'Hide all post bodies',
                     class_='button global-button',
                     id='hide-all-post-bodies'), '\n',
                 self.enclose(
                     'Show all post bodies',
                     class_='button global-button',
                     id='show-all-post-bodies'), '\n'),
                class_='global-buttons',
                tag='div',
                newlines=True)

        return (buttons,
                self.print_thread_page(self._root),
                self.print_js_links())

    def get_postsummary_fields_inner(self, postitem):
        """Returns the fields of the post summary when the pos position is
        ``"inner"``.

        The function gets the usual buttons from |Generator| and adds its own
        buttons.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** iterable(|PostItemPrinterFun|)
        """

        old_fields = \
            hkgen.Generator.get_postsummary_fields_inner(self, postitem)
        new_fields = [self.print_hkweb_summary_buttons]
        return tuple(list(old_fields) + new_fields)

    def print_hkweb_summary_buttons(self, postitem):
        """Prints the post id of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        heap_id, post_index = postitem.post.post_id()
        post_id = heap_id + '-' + post_index
        id = 'post-body-show-button-' + post_id

        return \
            (self.enclose(
                 'Show body',
                 class_='button post-summary-button',
                 id=id,
                 attributes=' style="display: none;"'))

    def print_postitem_body(self, postitem):
        """Prints the body the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        body = hkgen.Generator.print_postitem_body(self, postitem)

        heap_id, post_index = postitem.post.post_id()
        post_id = heap_id + '-' + post_index

        buttons = \
            self.enclose(
                (self.enclose(
                     'Hide',
                     class_='button post-body-button',
                     id='post-body-hide-button-' + post_id), '\n',
                 self.enclose(
                     'Edit',
                     class_='button post-body-button',
                     id='post-body-edit-button-' + post_id), '\n',
                 self.enclose(
                     'Edit raw post',
                     class_='button post-body-button',
                     id='post-raw-edit-button-' + post_id), '\n',
                 self.enclose(
                     'Add child',
                     class_='button post-body-button',
                     id='post-body-addchild-button-' + post_id), '\n',
                 self.enclose(
                     'Save',
                     class_='button post-body-button',
                     id='post-body-save-button-' + post_id,
                     attributes='style="display: none;"'), '\n',
                 self.enclose(
                     'Cancel',
                     class_='button post-body-button',
                     id='post-body-cancel-button-' + post_id,
                     attributes='style="display: none;"'), '\n'),
                class_='post-body-buttons',
                tag='div',
                newlines=True)

        return self.enclose(
                   (buttons, body),
                   tag='div',
                   class_='post-body-container',
                   newlines=True,
                   id='post-body-container-' + post_id)

    def print_main(self, postid):
        return (self.print_searchbar(),
                self.print_post_page(postid))


class SearchPageGenerator(PostPageGenerator):

    def __init__(self, postdb, preposts):
        PostPageGenerator.__init__(self, postdb)
        self.posts = postdb.postset(preposts)
        self.options.html_title = 'Search page'

    def print_search_page_core(self):
        """Prints the core of a search page.

        **Returns:** |HtmlText|
        """

        # Getting the posts in the interesting threads
        xpostitems = self.walk_exp_posts(self.posts)

        xpostitems = \
            itertools.imap(
                self.set_postitem_attr('print_post_body'),
                xpostitems)
        xpostitems = \
            itertools.imap(
                self.set_postitem_attr('print_parent_post_id'),
                xpostitems)
        xpostitems = \
            itertools.imap(
                self.set_postitem_attr('print_children_post_id'),
                xpostitems)

        # Printing the page
        return self.print_postitems(xpostitems)

    def print_search_page(self):
        """Prints the search page.

        **Returns:** |HtmlText|
        """

        buttons = \
            self.enclose(
                (self.enclose(
                     'Hide all post bodies',
                     class_='button global-button',
                     id='hide-all-post-bodies'), '\n',
                 self.enclose(
                     'Show all post bodies',
                     class_='button global-button',
                     id='show-all-post-bodies'), '\n'),
                class_='global-buttons',
                tag='div',
                newlines=True)

        return (buttons,
                self.print_search_page_core())


class PostBodyGenerator(WebGenerator):

    def __init__(self, postdb):
        WebGenerator.__init__(self, postdb)

    def print_post_body(self, post_id):

        post = self._postdb.post(post_id)
        if post is None:
            return 'No such post: "%s"' % (post_id,)

        postitem = hklib.PostItem('inner', post)
        postitem.print_post_body = True
        body_str = self.print_postitem_body(postitem)
        return body_str


##### Server classes #####


class WebpyServer(object):
    """Base class for webservers."""

    def __init__(self):
        add_auth(self, auth)
        self._postdb = hkshell.postdb()

class HkPageServer(object):
    """Base class for webservers that serve a "usual" HTML page that is
    generated by a Heapkeeper generator."""

    def __init__(self):
        add_auth(self, auth)
        self._postdb = hkshell.postdb()

    def serve_html(self, content, generator):
        """Creates a HTML page that contains the given content.

        **Argument:**

        - `content` (|HtmlText|)

        **Returns:** str
        """

        webpy.header('Content-type', 'text/html')
        webpy.header('Transfer-Encoding', 'chunked')
        page = generator.print_html_page(content)
        return hkutils.textstruct_to_str(page)


class Index(HkPageServer):
    """Serves the index page that shows all posts."""

    def __init__(self):
        HkPageServer.__init__(self)

    def GET(self):
        generator = IndexGenerator(self._postdb)
        content = generator.print_main()
        return self.serve_html(content, generator)


class Post(HkPageServer):
    """Serves the post pages.

    Served URL: ``/post/<heap>/<post index>``"""

    def __init__(self):
        HkPageServer.__init__(self)

    def GET(self, name):
        post_id = hkutils.uutf8(name)
        generator = PostPageGenerator(self._postdb)
        content = generator.print_main(post_id)
        return self.serve_html(content, generator)


class Search(HkPageServer):
    """Serves the search pages.

    Served URL: ``/search``"""

    def __init__(self):
        HkPageServer.__init__(self)

    def main(self):

        try:
            args = get_web_args()
            preposts = self.get_posts(args)
        except hkutils.HkException, e:
            return str(e)

        if preposts is None:
            # `preposts` is None if there was no search performed. However, in
            # this function, we want to have `preposts` as a list of preposts,
            # and we use `show` to store the information that no search was
            # performed and thus no search result should be shown.
            preposts = []
            show = 'no_search'
        else:
            # 'normal' means here that a search was performed. Later we modify
            # thsi to 'no_post_found' if it turns out that the query does not
            # match any post.
            show = 'normal'

        generator = SearchPageGenerator(self._postdb, preposts)
        if (show == 'normal' and len(generator.posts) == 0):
            show = 'no_post_found'

        if show == 'no_search':
            main_content = ''
        elif show == 'no_post_found':
            main_content = 'No post found.'
        elif show == 'normal':
            active = len(generator.posts)
            all = len(generator.posts.exp())
            numbers = ('Posts found: %d<br/>'
                       'All posts shown: %d' % (active, all))
            numbers_box = generator.enclose(numbers, 'div', 'info-box')
            main_content = (numbers_box, generator.print_search_page())

        term = args.get('term')
        if term is not None:
            # We use json to make sure that `term` is represented in a format
            # readable by JavaScript
            fill_searchbar_js = \
                ('$("#searchbar-term").val(' +
                 json.dumps(term) +
                 ');\n')
        else:
            fill_searchbar_js = ''

        focus_searchbar_js = '$("#searchbar-term").focus();\n'

        js_code = \
            ('<script  type="text/javascript" language="JavaScript">\n',
            fill_searchbar_js,
            focus_searchbar_js,
             '</script>\n')

        content = (generator.print_searchbar(),
                   main_content,
                   generator.print_js_links(),
                   js_code)
        return self.serve_html(content, generator)

    def get_posts(self, args):

        posts = args.get('posts')
        if posts is not None:
            return posts

        term = args.get('term')
        if term is not None:
            return hksearch.search(term, self._postdb.all())

        return None # only the search bar will be shown

    def GET(self):
        return self.main()

    def POST(self):
        return self.main()


class ShowJSon(HkPageServer):
    """Serves the search pages.

    Served URL: ``/showjson``"""

    def __init__(self):
        HkPageServer.__init__(self)

    def GET(self):
        input = webpy.input()
        try:
            args = get_web_args()
        except hkutils.HkException, e:
            return str(e)
        generator = IndexGenerator(self._postdb)
        content = ("JSon dictionary of the query parameters: ",
                    generator.escape(repr(args)))
        return self.serve_html(content, generator)

    def POST(self):
        return self.GET()


class RawPostBody(WebpyServer):
    """Serves raw post bodies.

    Served URL: ``/raw-post-bodies/<heap>/<post index>``"""

    def __init__(self):
        WebpyServer.__init__(self)

    def GET(self, name):
        webpy.header('Content-type', 'text/plain')
        webpy.header('Transfer-Encoding', 'chunked')
        post_id = hkutils.uutf8(name)
        post = self._postdb.post(post_id)
        if post is None:
            return 'No such post: "%s"' % (post_id,)
        content = post.body()
        return content


class RawPostText(WebpyServer):
    """Serves raw post text.

    Served URL: ``/raw-post-text/<heap>/<post index>``"""

    def __init__(self):
        WebpyServer.__init__(self)

    def GET(self, name):
        webpy.header('Content-type', 'text/plain')
        webpy.header('Transfer-Encoding', 'chunked')
        post_id = hkutils.uutf8(name)
        post = self._postdb.post(post_id)
        if post is None:
            return 'No such post: "%s"' % (post_id,)
        content = post.write_str()
        return content


class AjaxServer(WebpyServer):
    """Base class for classes that serve AJAX requests.

    The concrete classes should implement the `execute` method."""

    def __init__(self):
        WebpyServer.__init__(self)

    def GET(self, name_uni):
        return self.POST(name_uni)

    def POST(self, name_uni):
        # RFC4627: "The MIME media type for JSON text is application/json."
        webpy.header('Content-type','application/json')
        webpy.header('Transfer-Encoding','chunked')
        name = hkutils.uutf8(name_uni)
        try:
            args = get_web_args()
        except hkutils.HkException, e:
            return str(e)
        result = self.execute(name, args)
        return json.dumps(result)


class SetPostBody(AjaxServer):
    """Sets the body of the given post.

    Served URL: ``/set-post-body/<heap>/<post index>``"""

    def __init__(self):
        AjaxServer.__init__(self)

    def execute(self, post_id, args):
        """Sets the post body.

        **Argument:**

        - `args` ({'new_body_text': str, 'new_count': int})

        **Returns:** {'error': str} | {'new': str}
        """

        postdb = self._postdb

        new = args.get('new')
        if new is None:
            post = postdb.post(post_id)
        else:
            parent = postdb.post(post_id)

            # Create new post, make it a child of the existing one.
            post = hklib.Post.from_str('')
            post.set_author(parent.author())
            post.set_subject(parent.subject())
            post.set_date(parent.date())
            post.set_tags(parent.tags())
            post.set_parent(parent.post_id_str())
            heap = parent.heap_id()
            prefix = 'hkweb_'
            hkshell.add_post_to_heap(post, prefix, heap)
            post_id = post.post_id()

        if post is None:
            return {'error': 'No such post: "%s"' % (post_id,)}

        newPostBodyText = args.get('new_body_text')
        if newPostBodyText is None:
            return {'error': 'No post body specified'}

        post.set_body(newPostBodyText)

        # Generating the HTML for the new body or new post summary.
        if new is None:
            generator = PostBodyGenerator(self._postdb)
            new_body_html = generator.print_post_body(post_id)
            new_body_html = hkutils.textstruct_to_str(new_body_html)
            return {'new_body_html': new_body_html}
        else:
            generator = PostPageGenerator(self._postdb)
            generator.set_post_id(post.post_id())
            postitem = hklib.PostItem('inner', post)
            postitem.print_post_body = True
            postitem.print_parent_post_id = True
            postitem.print_children_post_id = True
            new_post_summary = generator.print_postitems([postitem])
            new_post_summary = hkutils.textstruct_to_str(new_post_summary)
            return \
                {
                    'new_post_summary': new_post_summary,
                    'new_post_id': '-'.join(post.post_id())
                }



class GetPostBody(AjaxServer):
    """Gets the body of the given post.

    Served URL: ``/get-post-body/<heap>/<post index>``"""

    def __init__(self):
        AjaxServer.__init__(self)

    def execute(self, post_id, args):
        # Unused argument 'postitem' # pylint: disable-msg=W0613
        """Gets the post body.

        **Argument:**

        - `args` ({})

        **Returns:** {'error': str} | {'body_html': str}
        """

        post = self._postdb.post(post_id)
        if post is None:
            return {'error': 'No such post: "%s"' % (post_id,)}

        # Generating the HTML for the new body
        generator = PostBodyGenerator(self._postdb)
        new_body_html = generator.print_post_body(post_id)
        new_body_html = hkutils.textstruct_to_str(new_body_html)

        return {'body_html': new_body_html}


class SetRawPost(AjaxServer):
    """Sets the raw content of the given post.

    Served URL: ``/set-raw-post/<heap>/<post index>``"""

    def __init__(self):
        AjaxServer.__init__(self)

    def execute(self, post_id, args):
        """Sets the raw content of the given post.

        **Argument:**

        - `args` ({'new_post_text': str})

        **Returns:** {'error': str} | {'new_post_summary': str}
        """

        post = self._postdb.post(post_id)
        if post is None:
            return {'error': 'No such post: "%s"' % (post_id,)}

        new_post_text = args.get('new_post_text')
        if new_post_text is None:
            return {'error': 'No post text specified'}

        old_parent = post.parent()

        # Catch "Exception" # pylint: disable-msg=W0703
        try:
            post.read_str(new_post_text)
        except Exception, e:
            return {'error':
                    'Exception was raised while parsing the post:\n' + str(e)}

        if post.parent() != old_parent:
            major_change = True
        else:
            major_change = False

        # Generating the HTML for the new post text
        generator = PostPageGenerator(self._postdb)
        generator.set_post_id(post.post_id())
        postitem = hklib.PostItem('inner', post)
        postitem.print_post_body = True
        postitem.print_parent_post_id = True
        postitem.print_children_post_id = True
        new_post_summary = generator.print_postitems([postitem])
        new_post_summary = hkutils.textstruct_to_str(new_post_summary)

        return {'new_post_summary': new_post_summary,
                'major_change': major_change}


class Fetch(object):
    """Serves the files that should be served unchanged."""

    def GET(self, name):
        filename = hkutils.uutf8(name)
        return hkutils.file_to_string(filename)


##### Main server class #####

class Server(threading.Thread):
    """Implements the hkweb server thread."""

    def __init__(self, port):
        super(Server, self).__init__()
        self.daemon = True
        self._port = port

    def run(self):

        # Passing the port parameter to web.py is ugly, but the mailing list
        # entries I have found so far suggest this, and it does the job. A
        # wrapper around sys would be the answer, which should be done anyway
        # to control logging (there sys.stderr should be diverted).
        sys.argv = (None, str(self._port),)
        webapp = webpy.application(urls, globals())
        self.webapp = webapp
        webapp.run()


##### Interface functions #####

def start(port=8080):
    """Starts the hkweb web server.

    **Argument:**

    - `port` (int) -- The port to listen on.
    """

    options = hkshell.options
    options.web_server = Server(port)
    options.web_server.start()
    hkutils.log('Web service started.')

def insert_urls(new_urls):
    """Inserts the given urls before the already handles URLs.

    **Argument:**

    - `new_urls` ([str])

    **Returns:**

    **Example:** ::

        >>> hkweb.insert_urls(['/myurl', 'mymodule.MyServer'])
    """

    urls[0:0] = new_urls
