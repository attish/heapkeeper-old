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

"""|hkshell| is Heapkeeper's interactive shell.

It defines commands that are actually Python functions. These functions perform
high-level manipulaton on the heap, and they tend to have very short names.

To get help after from within |hkshell|, type ``h()``. It will print the list
of features and commands with a short description.

Invocation
''''''''''

|hkshell| can be started using ``hk.py``. It gives a Heapkeeper shell (which is
a Python shell with some pre-defined functions) to the user.

**Command line arguments:**

``hk.py`` does not have any mandatory arguments, only options. They are the
following:

- ``-h``, ``--help`` --
  hkshell shows a help message and exits.
- ``-b <before_command>``, ``--before <before_command>`` --
  Python code to execute before importing hkrc. Any number of before commands
  may be specified.
- ``-c <after_command>``, ``--command <after_command>`` --
  Python code to execute after importing hkrc. Any number of after commands may
  be specified.
- ``-r <hkrc>``, ``--hkrc <hkrc>`` --
  Modules to import as hkrc modules. Any number of modules may be specified. If
  nothing is specified, the ``hkrc`` module is imported. If ``NONE`` is
  specified, nothing is imported. If a module is not found, the program gives
  only a warning.
- ``--configfile <configfile>`` --
  The name of the Heapkeeper config file to use.
- ``--version`` --
  Prints Heapkeeper version and exits.

The ``--hkrc`` option deals with the modules that should be imported when
hkshell is started. The convention (and the default behaviour) is that there is
a module called ``hkrc`` which is imported. The ``hkrc`` module customizes the
tool to the user's needs.

**Examples:**

.. highlight:: sh

Starting hkshell::

    $ python src/hk.py

This example downloads new emails, generates the index pages and exits after
saving the post database::

    $ python src/hk.py -c 'dl()' -c 'g()' -c 'x()'

Positional arguments
::::::::::::::::::::

Currently the ``-c`` markers may be omitted and the positional arguments (the
ones without ``-<character>`` and ``--<word>``) will be executed as commands::

    $ python src/hk.py 'dl()' 'g()' 'x()'

Always use ``-c`` in scripts that you want to keep, because this behaviour may
be changed in the future if we want to use positional arguments for something
else.

.. highlight:: python

Initialization
''''''''''''''

The following actions are performed when hkshell starts:

1. The commands after the ``--before`` options are executed.
2. The ``hk.cfg`` configuration file and the post database are read.
3. The default event handlers are set.
4. The ``hkrc`` file(s) are executed.
5. The commands after the ``--after`` options are executed.

Usage
'''''

After performing the initial tasks, the Python interpreter is provided to the
user. There are some functions of |hkshell| that has been added to the local
namespace of the interpreter, so they can be used without having to write
``hkshell.``. These functions are called commands. The user can define own
commands, as well. For reading about the commands of |hkshell|, type ``h()`` if
you are in |hkshell|, or go to the :ref:`hkshell_commands` section if you are
reading the documentation.

**Features**

|hkshell| has a concept of features. A feature can be turned on and off.
See the list of features and the detailed description in the :ref:`Features
<hkshell_features>` section.

Pseudo-types
''''''''''''

|hkshell| has pseudo-types that are not real Python types, but we use them as
types in the documentation so we can talk about them easily.

- :ref:`PrePost <hklib_PrePost>`

- :ref:`PrePostSet <hklib_PrePostSet>`

.. _hkshell_Tag:

- **Tag** -- A tag.

  Real type: str

.. _hkshell_PreTagSet:

- **PreTagSet** -- An object that can be converted
  into a set of tags.

  Real type: |Tag| | set(|Tag|) | [|Tag|]

.. _hkshell_Listener:

- **Listener(event)**  -- A listener (also called event handler) that can
  be called when an event is raised.

  Real type: fun(|Event|)

.. _hkshell_GenIndicesFun:

- **GenIndicesFun(postdb)** -- Function that generates index pages.

  Real type: fun(|PostDB|))

.. _hkshell_EditFileFun:

- **EditFileFun(filename)** -- Function that opens an editor with the given
  file. It should return ``True`` or ``False`` when the user finished editing
  the file. If the file was changed, it should return ``True``, otherwise
  ``False``.

  Real type: fun(str), returns bool

.. _hkshell_Writable:

- **Writable(filename)** -- Object that has a `write(str)` method.

  Real type: object

.. _hkshell_FeatureState:

- **FeatureState** -- ``'on'`` or ``'off'``.

  Real type: str
"""

console_help = """\
Types
-----

pp = PrePost = str | int | (str, int) | (str, str) | | Post
pps = PrePostSet = pp | [pp] | set(pp) | PostSet
pts = PreTagSet = tag | set(tag) | [tag]

Features
--------

gen_indices        - automatically regenerates the index pages
save               - automatically saves the post database after commands
timer              - times the commands
touched_post_printer - prints touched posts
event_printer      - prints all events

Commands
--------

h()                - prints a detailed help
s()                - save
x()                - save and exit
rl()               - reload the database (changes will be lost!)
g()                - generate HTML pages
gen_page(pps)      - generates a page that contains the posts
sh(str)            - set default heap
gh()               - get default heap
p(pp)              - get a post
ps(pps)            - create a postset
ls(ps)             - get a summary of a postset

pT(pps)            - propagate tags
aT(pps, pts)       - add tag/tags
aTr(pps, pts)      - add tag/tags recursively
rT(pps, pts)       - remove tag/tags
rTr(pps, pts)      - remove tag/tags recursively
sT(pps, pts)       - set tag/tags
sTr(pps, pts)      - set tag/tags recursively

pS(pps)            - propagate subject
sS(pps, subj)      - set subject
sSr(pps, subj)     - set subject recursively
cS(pps, subj)      - capitalize the subject
cSr(pps, subj)     - capitalize the subject recursively

d(pps)             - delete
dr(pps)            - delete recursively
j(pp, pp)          - join two threads
e(pps)             - edit posts as files
er(pps)            - edit posts as files recursively
enew()             - creates and edits a new post as a file
enew_str(str)      - creates a new post from a string
dl()               - download new mail
grep(pattern[, pps]) - searches in the post database

postdb()           - the post database object
c()                - shorthand for postdb().all().collect
on(feature)        - turning a feature on
off(feature)       - turning a feature off

For further help on a command type ``help(<command name>)`` or see the HTML
documentation.
"""


import code
import ConfigParser
import datetime
import functools
import optparse
import os
import re
import subprocess
import sys
import tempfile
import time

import hkutils
import hkcustomlib
import hkconfig
import hkemail
import hklib
import hkgen


##### Callbacks #####

# TODO Remove this function after releasing 0.9.
class Callbacks(object):

    """DEPRECATED. Stores callback functions or objects that are used by
    |hkshell|.

    Override hkshell functions instead of setting them as callbacks.

    The attributes are mentioned as functions, but they can be objects with
    `__call__` method, as well.

    **Data attributes:**

    - `gen_indices` (|GenIndicesFun|) -- Function to be used for generating
      index pages. Default value: :func:`hkcustomlib.gen_indices`.
    - `edit_files` (|EditFileFun|) -- Function to be used for editing posts.
      Default value: :func:`hkcustomlib.edit_files`.
    """

    # Unused arguments # pylint: disable=W0613
    def __init__(self,
                 gen_indices=hkcustomlib.gen_indices,
                 edit_files=hkcustomlib.edit_files):

        super(Callbacks, self).__init__()
        hkutils.set_dict_items(self, locals())


##### Options #####

# TODO Remove the `callbacks` item after releasing 0.9.
class Options(object):

    """Stores various options regarding how |hkshell| works.

    **Data attributes:**

    - `config` (|ConfigDict|) -- Configuration object.
    - `output` (|Writable|) -- When |hkshell| wants to print something, it
      calls `output`'s write method.
      Default value: ``sys.stdout``
    - `callbacks` (|Callbacks|) -- DEPRECATED. Callback functions to be called
       on various occasions. Override hkshell functions instead. Default value:
       the default |Callbacks| object.
    - `shell_banner` (str) -- A banner that is printed when the Python shell
      starts. If ``None``, the default text is printed with the interpreter
      information.
      Default value: ``''``
    - `save_on_ctrl_d` (bool | None) -- If boolean, it specifies whether to
      save when the user hits CTRL-D or to abandon the changes silently. If
      ``None``, the user will be asked what to do. Default value: ``None``.
    """

    # Unused arguments # pylint: disable=W0613
    def __init__(self,
                 postdb=hkutils.NOT_SET,
                 config=hkutils.NOT_SET,
                 output=sys.stdout,
                 callbacks=hkutils.NOT_SET,
                 shell_banner=("This is Heapkeeper's shell.\n"
                               "Type h() to get help.\n"
                               "Type q() to quit without saving."),
                 save_on_ctrl_d=None):

        super(Options, self).__init__()

        # TODO after releasing 0.9, add this line and remove the following code
        # hkutils.set_dict_items(self, locals())

        # We remove the 'callbacks' data member so that __getattr__ is called
        locals2 = locals().copy()
        locals2['callbacks_deprecated'] = locals2['callbacks']
        del locals2['callbacks']
        hkutils.set_dict_items(self, locals2)

    # TODO remove this function after releasing 0.9
    def __getattr__(self, name):
        if name == 'callbacks':
            print ('WARNING: hkshell.Callbacks is deprecated, and '
                    'it does not work any more. Please override '
                    'hkshell functions instead.')
            return self.callbacks_deprecated
        else:
            return object.__getattr__(self, name)


# The functions and methods of |hkshell| read the value of specific options
# from this object. The users of |hkshell| are allowed to change this object in
# order to achieve the behaviour they need.
options = Options(callbacks=Callbacks())


##### Commands #####

def hkshell_cmd(add_events=False, postset_operation=False,
                touching_command=False):
    """This function is a decorator that defines the decorated function as a
    hkshell command.

    **Arguments:**

    - `add_events` (bool) -- If ``True``, the decorator :func:`add_events`
      will also be applied to the function, with default arguments.
    - `postset_operation` (bool) -- If ``True``, the decorator
      :func:`postset_operation` will also be applied to the function.
    - `touching_command` (bool) -- If ``True``, the
      |TouchedPostPrinterListener| objects will print the touched posts after
      the command has been finished.

    Defining a hkshell command means that the decorated function can be used
    from |hkshell| without specifying in which module it is. It also can be
    used after the ``--before`` and ``--command`` arguments of |hkshell|.

    **Examples:**

    One of the important uses of this decorator is to decorate functions in the
    ``hkrc`` module that the user wants to use conveniently. As an example,
    let's suppose ``hkrc.py`` contains this code::

        @hkshell.hkshell_cmd()
        def mycmd():
            print 'Hi, this is my command.'

    The *mycmd* function can be used from the hkshell as a normal hkshell
    command::

        >>> mycmd()
        Hi, this is my command.
        >>>

    **Using it with other decorators:**

    If you use it with another decorator, :func:`hkshell_cmd` should be the
    last one to be applied, i.e. it should be first one in the source text.
    For example you may write the following::

        @hkshell_cmd()
        @mydecorator
        def f():
            ...

    But do *not* write this::

        @mydecorator
        @hkshell_cmd()
        def f():
            ...

    The reason is the in the second case, the original version of `f` will be
    registered as a command, which was not decorated with `mydecorator`.
    """

    def inner(f):
        if add_events:
            f = globals()['add_events']()(f)
        if postset_operation:
            f = globals()['postset_operation'](f)
        if touching_command:
            add_touching_command(f.__name__)
        register_cmd(f.__name__, f)
        return f
    return inner

# Stores the commands defined by the user.
# If you want to add a command to this, the preferred way is to use the
# hkshell_cmd decorator.
hkshell_commands = {}

def register_cmd(name, fun):
    """Registers a hkshell command.

    Registering a hkshell command means that :func:`register_cmd` adds the
    function to the `hkshell.hkshell_commands` dictionary.

    **Arguments:**

    - `name` (str) -- The name by which the command can be invoked, i.e. the
      name to which the function should be bound.
    - `fun` (fun(\*args, \*\*kw)) -- An arbitrary function. This will be called
      when the command is invoked.
    """

    # It defines the command in the hkshell_commands dictionary, which is used
    # by the exec_commands function to specify the global variables.
    hkshell_commands[name] = fun


##### Event handling #####

# See the description of the event handling system of hkshell in the user
# documentation of hkshell (hkshell.html or doc/hkshell.rst), in section "Event
# handling".

class Event(object):

    """Represents an event.

    Only the `type` attribute of Event is mandatory, the others are optional.

    **Data attributes:**

    - `type` (str) -- The type of the event. Examples: ``'before'``,
      ``'after'``, ``'touch'``.
    - `command` (str) -- The command that was executed when the event was
      raised.
    - `post` (|Post|) -- The post associated with the event.
    - `postset` (|PostSet|) -- The postset associated with the event.
    """

    # Unused arguments # pylint: disable=W0613
    def __init__(self,
                 type,
                 command=None,
                 post=None,
                 postset=None):

        """Initializes an object.

        **Arguments:**

        - `type` (str) -- See the data attributes of |Event|.
        - `command` (str) -- See the data attributes of |Event|.
        - `post` (|Post|) -- See the data attributes of |Event|.
        - `postset` (|PostSet|) -- See the data attributes of |Event|.
        """

        super(Event, self).__init__()
        hkutils.set_dict_items(self, locals())

    def __str__(self):
        s = '<Event with the following attributes:'
        for attr in ['type', 'command', 'postset']:
            s += '\n%s = %s' % (attr, getattr(self, attr))
        s += '>'
        return s

# This list contains the listeners (also called event handlers) that are
# called each time an event is raised.
listeners = []

def append_listener(listener):
    """Appends a new listener to the listeners' list.

    **Argument:**

    - `listener` (|Listener|)
    """

    if listener not in listeners:
        listeners.append(listener)
    else:
        raise hkutils.HkException, \
              'Listener already among listeners: %s' % (listener,)

def remove_listener(listener):
    """Removes a listener from the listeners' list.

    **Argument:**

    - `listener` (|Listener|)
    """

    if listener not in listeners:
        raise hkutils.HkException, \
              'Listener not among listeners: %s' % (listener,)
    else:
        listeners.remove(listener)

def event(*args, **kw):
    """Raises an event.

    First, an event (an |Event| object) is created. :func:`Event.__init__`
    is called with the same arguments as this function. Then all the listeners
    are invoked with the created event as their only argument.

    **Arguments:** the same as the arguments of :func:`Event.__init__`, see the
    details there.

    Example::

        def s():
            event(type='before', command='s')
            postdb().save()
            event(type='after', command='s')
    """

    e = Event(*args, **kw)
    for fun in listeners:
        fun(e)

def add_events(command=None):
    """This function is a decorator that raises events before and after the
    execution of the decorated function.

    **Arguments:**

    - `command` (str) -- The ``command`` attribute of the event that should be
      raised. If ``None``, the name of the function will be used as the command
      name. The default value is ``None``.

    Example::

        @add_events()
        def s():
            postdb().save()
    """

    def inner(f):
        command2 = f.__name__ if command == None else command
        @functools.wraps(f)
        def inner2(*args, **kw):
            event('before', command=command2)
            try:
                result = f(*args, **kw)
            finally:
                event('after', command=command2)
            return result
        return inner2
    return inner


##### Event handling utilities #####

def postset_operation(operation):
    '''This function is a decorator to be used for decorating commands that
    manipulate posts based on a given postset.

    The decorated function will perform the following steps when invoked:

    1. Raises ``event('before', command)``.
    2. Calculates the postset to operate on. This will be referred as the
       ``posts`` variable.
    3. Raises ``event('postset_calculated', command, postset=posts)``.
    4. If ``posts`` is not an empty set, invokes the original command with
       ``posts`` as a first formal parameter and the other actual parameters as
       other formal parameters.
    5. Raises ``event('after', command, postset=posts)``.

    Example on how to define a function that is decorated with
    `postset_operation`::

        @postset_operation
        def d(posts):
            """Deletes the posts in `pps`.

            **Argument:**

            - `pps` (|PrePostSet|)
            """

            posts.forall.delete()

    Note that the first (and only) parameter of the original function is
    `posts`, but the the first parameter of the decorated function is `pps`!
    That is why the documentation of :func:`d` states that the name of the
    parameter is `pps`.

    A more complex example::

        @postset_operation
        def add_tags_recursively(posts, tags):
            tags = tagset(tags)
            for p in posts.expf():
                p.set_tags(tags.union(p.tags()))
    '''

    @functools.wraps(operation)
    def inner(pps, *args, **kw):
        posts = []
        try:
            command = operation.__name__
            event('before', command)
            try:
                posts = ps(pps)
            except:
                hkutils.log('Posts not found: %s' % (pps,))
                return
            event('postset_calculated', command, postset=posts)
            if len(posts) != 0:
                result = operation(posts, *args, **kw)
        finally:
            event('after', command, postset=posts)
        return result
    return inner


##### Concrete listeners #####

class ModificationListener(object):

    """Listens to and stores the modifications made in the latest commands.

    A |ModificationListener| object subscribes to the modifications of both the
    given post database and |hkshell|. The posts modified since the latest
    command can be obtained by calling the :func:`touched_posts`.
    |ModificationListener| objects should be closed (using the :func:`close`
    method).

    **Implements:** |Listener|
    """

    def __init__(self, postdb_arg=None):
        """Initializes an object.

        **Argument:**

        - `postdb_arg` (|PostDB|) -- The post database whose modifications
          should be listened to.
        """

        super(ModificationListener, self).__init__()
        self._postdb = postdb_arg if postdb_arg != None else postdb()
        self._postdb.listeners.append(self)
        self._posts = self._postdb.postset([])

    def close(self):
        """Closes the |ModificationListener|.

        The object will unsubscribe from the notifications it subscribed to.
        """

        self._postdb.listeners.remove(self)

    def __call__(self, e):
        """The event handler method.

        **Argument:**

        - `e` (|Event|)
        """

        if e.type == 'before':
            self._posts = self._postdb.postset([])
        elif isinstance(e, hklib.PostDBEvent) and e.type == 'touch':
            self._posts.add(e.post)

    def touched_posts(self):
        """Returns the posts modified since the beginning of the latest
        command."""
        return self._posts


class PostPageListener(object):

    """Stores the post whose post page is not up-to-date.

    **Implements:** |Listener|
    """

    def __init__(self, postdb_arg=None):
        """Initializes an object.

        **Argument:**

        - `postdb_arg` (|PostDB|) -- The post database whose modifications
          should be listened to.
        """

        super(PostPageListener, self).__init__()
        self._postdb = postdb_arg if postdb_arg != None else postdb()
        self._postdb.listeners.append(self)
        self._posts = self.outdated_posts_from_disk()

    def outdated_posts_from_disk(self):
        """Returns the posts that are outdated, based on the timestamp of the
        post files and the post pages."""

        def outdated(post):
            try:
                time_html = os.stat(post.htmlfilename()).st_mtime
                time_post = os.stat(post.postfilename()).st_mtime
                return time_html < time_post
            except OSError:
                # a file is missing; hopefully the HTML
                return True

        if self._postdb.html_dir() is None:
            return self._postdb.postset([])
        else:
            return self._postdb.all().collect(outdated)

    def close(self):
        """Closes the |PostPageListener|.

        The object will unsubscribe from the notifications it subscribed to.
        """

        self._postdb.listeners.remove(self)

    def __call__(self, e):
        """The event handler method.

        **Argument:**

        - `e` (|Event|)
        """

        if e.type == 'post_page_created':
            self._posts.remove(e.post)
        elif isinstance(e, hklib.PostDBEvent) and e.type == 'touch':
            self._posts.add(e.post)

    def outdated_post_pages(self):
        """Returns the posts whose post pages are outdated.

        **Returns:** |PostSet|
        """

        return self._posts


def gen_indices_listener(e):
    """Regenerates the index pages after commands that changed the posts.

    **Type:** |Listener|
    """

    if (e.type == 'after' and len(modification_listener.touched_posts()) > 0):
        gen_indices()

def save_listener(e):
    """Saves the database after commands that changed it.

    **Type:** |Listener|
    """

    if (e.type == 'after' and len(modification_listener.touched_posts()) > 0):
        postdb().save()
        write('Mail database saved.\n')

def timer_listener(e, start=[None]):
    """Prints the execution time of commands.

    **Type:** |Listener|
    """

    if e.type == 'before':
        start[0] = time.time()
    elif e.type == 'after':
        write('%s: %f seconds.\n' % (e.command, time.time() - start[0]))

def event_printer_listener(e):
    """Prints the event.

    **Type:** |Listener|
    """

    write('%s\n' % (e,))


class TouchedPostPrinterListener(object):

    """Prints the post that have been touched after executing commands.

    More precisely, it happend only after commands that are "touching
    commands", i.e. they are added to the ``hkshell.touching_commands``
    list.

    **Implements:** |Listener|
    """

    def __init__(self, commands):
        """Initializes an object.

        **Argument:**

        - `commands` ([str]) -- The names of the commands

        """

        super(TouchedPostPrinterListener, self).__init__()
        self.commands = commands
        self.command = None

    def __call__(self, e):
        """The event handler method.

        **Argument:**

        - `e` (|Event|)
        """

        if e.type == 'before':
            self.command = e.command
        elif e.type == 'after' and self.command in self.commands:
            touched_posts = modification_listener.touched_posts()
            if len(touched_posts) == 0:
                write('No post has been touched.\n')
            else:
                if len(touched_posts) == 1:
                    write('1 post has been touched:\n')
                else:
                    write('%s posts have been touched:\n' %
                          (len(touched_posts),))
                post_ids = sorted([post.post_id() for post in touched_posts])
                write('%s\n' % ([ '%s/%s' % post_id for post_id in post_ids]))

# Commands after which the touched_post_printer should print the touched posts.
# The preferred way to add a command to the list is use the
# add_touching_command function.
touching_commands = []

def add_touching_command(command):
    """Add a command to the list of "touching" commands."""
    touching_commands.append(command)

# The global TouchedPostPrinterListener object of hkshell.
touched_post_printer_listener = TouchedPostPrinterListener(touching_commands)


##### Features #####

def set_listener_feature(listener, state):
    """Sets the given listener feature to the given state.

    **Arguments:**

    - `listener` (|Listener|)
    - `state` (|FeatureState|)
    """

    if state == 'on':
        try:
            append_listener(listener)
        except hkutils.HkException:
            write('Feature already set.\n')
    else:
        assert(state == 'off')
        try:
            remove_listener(listener)
        except hkutils.HkException:
            write('Feature not set.\n')

def get_listener_feature(listener):
    """Returns whether the given listener feature is turned on.

    **Argument:**

    - `listener` (|Listener|)

    **Returns:** |FeatureState|
    """

    if listener in listeners:
        return 'on'
    else:
        return 'off'

def set_feature(state, feature):
    """Sets the given feature to the given state.

    **Arguments:**

    - `state` (|FeatureState|)
    - `feature` (str)
    """

    if feature in ['gi', 'gen_indices']:
        set_listener_feature(gen_indices_listener, state)
    elif feature in ['s', 'save']:
        set_listener_feature(save_listener, state)
    elif feature in ['t', 'timer']:
        set_listener_feature(timer_listener, state)
    elif feature in ['tpp', 'touched_post_printer']:
        set_listener_feature(touched_post_printer_listener, state)
    elif feature in ['ep', 'event_printer']:
        set_listener_feature(event_printer_listener, state)
    else:
        write('Unknown feature.\n')

def features():
    """Returns the states of all features.

    **Arguments:**

    - `state` (|FeatureState|)
    - `feature` (str)

    **Returns:** {str: |FeatureState|}
    """

    g = get_listener_feature
    return {'gen_indices': g(gen_indices_listener),
            'save': g(save_listener),
            'timer': g(timer_listener),
            'touched_post_printer': g(touched_post_printer_listener)}

@hkshell_cmd()
def on(feature):
    """Sets a feature to on.

    **Argument:**

    - `feature` (str)
    """

    set_feature('on', feature)

@hkshell_cmd()
def off(feature):
    """Sets a feature to off.

    **Argument:**

    - `feature` (str)
    """

    set_feature('off', feature)


##### Generic functionality #####

def write(s):
    """Writes the string to |hkshell|'s output.

    **Argument:**

    - `s` (str)
    """

    options.output.write(s)

def gen_indices():
    """Generates index and thread pages."""

    g = hkgen.StaticGenerator(postdb())
    g.write_all()

def tagset(tags):
    """Converts the argument to a set that contains the given tags.

    **Argument:**

    - `tags` (|PreTagSet|)

    **Returns:** set(|Tag|)
    """

    if isinstance(tags, set):
        return tags
    elif isinstance(tags, str):
        return set([tags])
    elif isinstance(tags, list):
        return set(tags)
    else:
        raise hkutils.HkException, \
              'Cannot convert object to tagset: %s' % (tags,)


##### Editing files with a text editor #####

def default_editor():
    """Returns the default editor of the operating system.

    On Unix systems, the default is ``vi``. On Windows, it is ``notepad``.
    On other operating systems, the function returns ``None.``

    **Returns:** str
    """

    if os.name == 'posix':
        return 'vi'
    elif os.name == 'nt':
        return 'notepad'
    else:
        return None

class IncorrectEditorException(hkutils.HkException):

    """Raised when the editor variable is incorrect."""

    def __init__(self, editor, message):
        """Constructor."""
        value = ('Incorrect editor variable:\n'
                 '    %s\n'
                 '%s' % (editor, message))
        super(IncorrectEditorException, self).__init__('Incorrect editor.')

def editor_to_editor_list(editor):
    r"""Converts an editor variable to a list of program name and arguments.

    **Argument:**

    - `editor` (str)

    **Returns:** [str]

    **Examples:** ::

        >>> editor_to_editor_list('gvim')
        ['gvim']
        >>> editor_to_editor_list('vim arg1 arg2')
        ['vim', 'arg1', 'arg2']
        >>> editor_to_editor_list('vim long\\ argument')
        ['vim', 'long argument']
        >>> editor_to_editor_list('vim argument\\\\with\\\\backslash')
        ['vim', 'argument\\with\\backslash']
    """

    editor_list = []
    current_arg = []
    i = 0
    while i < len(editor):
        # If a backslash is found, the next character has to be a space or a
        # backslash, and it should be added to the current argument.
        if editor[i] == '\\':
            if len(editor) <=  i + 1:
                msg = 'Unescaped backslash should not be the final character.'
                raise IncorrectEditorException(editor, msg)
            i += 1
            if editor[i] in [' ', '\\']:
                current_arg.append(editor[i])
            else:
                msg = 'Unexpected character after backslash.'
                raise IncorrectEditorException(editor, msg)
        # If a space is found, a new argument should be started.
        elif editor[i] == ' ':
            if current_arg != []:
                editor_list.append(''.join(current_arg))
                current_arg = []
        # Otherwise the current character has to be added to the current
        # argument.
        else:
            current_arg.append(editor[i])
        i += 1
    if current_arg != []:
        editor_list.append(''.join(current_arg))
        current_arg = []
    return editor_list

def edit_files(files):
    """Opens an editor in which the user edits the given files.

    It invokes the editor program stored in the ``EDITOR`` environment
    variable. If ``EDITOR`` is undefined or empty, it invokes the default
    editor on the system using the :func:`default_editor` function.

    **Type:** |EditFileFun|
    """

    old_content = {}
    for file in files:
        old_content[file] = hkutils.file_to_string(file, return_none=True)

    editor = os.getenv('HEAPKEEPER_EDITOR')

    # if HEAPKEEPER_EDITOR is not set, get EDITOR
    if editor is None or editor == '':
        editor = os.getenv('EDITOR')

    # if EDITOR is not set, get the default editor
    if editor is None or editor == '':
        editor = default_editor()

    # if not even the default is set, print an error message
    if editor is None:
        hkutils.log(
           'Cannot determine the default editor based on the operating\n'
           'system. Please set the EDITOR environment variable to the editor\n'
           'you want to use or set hkshell.options.callback.edit_files to\n'
           'call your editor of choice.')
        return False

    try:
        editor = editor_to_editor_list(editor)
    except IncorrectEditorException:
        hkutils.log(
            'The editor variable is incorrect:\n' +
            editor +
            'Please set the EDITOR environment variable to the editor\n'
            'you want to use or set hkshell.options.callback.edit_files to\n'
            'call your editor of choice.')
        return False

    subprocess.call(editor + files)

    def did_file_change(file):
        new_content = hkutils.file_to_string(file, return_none=True)
        return old_content[file] != new_content

    changed_files = filter(did_file_change, files)
    return changed_files


##### Commands #####

@hkshell_cmd()
def h():
    """Prints the console help."""
    write(console_help)

default_heap_var = None

@hkshell_cmd()
def gh():
    """Gets the heap id of the default heap."""
    return default_heap_var

@hkshell_cmd()
def sh(default_heap):
    """Sets the default heap.

    **Argument:**

    - `default_heap` (|HeapId|) -- The heap id of the heap that should be the
      new default heap.
    """

    global default_heap_var
    default_heap_var = default_heap

@hkshell_cmd()
def p(pp):
    """Returns the post specified by its post id or message id or post
    index.

    See :func:`hklib.PostDB.post` for more information.

    **Argument:**

    - `pp` (|PrePost|)

    **Returns:** |Post|
    """

    # PostSet is better in making post from a prepost...
    postset = postdb().postset(pp, default_heap_var)
    return postset.pop()

@hkshell_cmd()
def ps(pps):
    """Creates a PostSet that will contain the specified posts.

    **Argument:**

    - `pp` (|PrePostSet|)

    **Returns:** |PrePost|
    """

    return postdb().postset(pps, default_heap_var)

@hkshell_cmd()
def postdb():
    """Returns the post database.

    **Returns:** |PostDB|
    """

    return options.postdb

@hkshell_cmd()
def c():
    """Shorthand for ``postdb().all().collect``."""
    return postdb().all().collect

@hkshell_cmd(add_events=True)
def s():
    """Saves the post database."""
    postdb().save()

@hkshell_cmd()
def x():
    """Saves the post database and exits."""
    event('before', 'x')
    postdb().save()
    event('after', 'x')
    sys.exit()

@hkshell_cmd()
def q():
    """Exits without saving the post database."""
    event('before', 'q')
    event('after', 'q')
    sys.exit()

@hkshell_cmd(add_events=True)
def rl():
    """Reloads the post from the disk.

    Changes that have not been saved (e.g. with the :func:`s` command) will
    be lost.
    """

    postdb().reload()

@hkshell_cmd(add_events=True)
def g():
    """Generates the index pages."""
    gen_indices()

@hkshell_cmd()
def gen_page(pps=None):
    """Generetes a post page from the posts in `pps`.

    See more information in the documentation of
    :class:`hkgen.GivenPostsGenerator`.

    **Argument:**

    - `pps` (|PrePostSet|)
    """

    ps = postdb().postset(pps)
    g = hkgen.GivenPostsGenerator(postdb())
    g.posts = ps
    g.html_filename = 'index/gen_page.html'
    g.write_all()

@hkshell_cmd(add_events=True)
def opp():
    """Returns the posts whose post pages are outdated.

    Note: `opp` stands for "outdated post pages".
    """

    return postpage_listener.outdated_post_pages()

@hkshell_cmd(add_events=True)
def ls(pps=None, show_author=True, show_tags=False, show_date=True, indent=2):
    """Lists the summary of the posts in `pps`.

    **Arguments:**

    - `pps` (|PrePostSet| | None) -- The set of posts to print. If ``None``,
      the summary of all posts in the post database will be printed.
    - `show_author` (bool) -- Show the author of the posts.
    - `show_tags` (bool) -- Show the tags of the posts.
    - `show_date` (bool) -- Show the dates of the posts.
    - `indent` (int) -- The number of spaces to be used to indicate one
      indentation level.

    **Example:** ::

        >>> ls()
        <0> Mind-reader robot  ashe@usrobots.com
          <1> Mind-reader robot  alfred.lanning@usrobots.com
            <2> Mind-reader robot  peter.bogert@usrobots.com
              <4> Mind-reader robot  alfred.lanning@usrobots.com
            <3> Mind-reader robot  susan@usrobots.com
              <5> Mind-reader robot  alfred.lanning@usrobots.com
                <6> Mind-reader robot  susan@usrobots.com
        <7> Cinema  susan@usrobots.com
          <8> Cinema  ashe@usrobots.com
    """

    if pps == None:
        pps = postdb().all()
    postset = ps(pps)

    for postitem in postdb().walk_thread(root=None):

        post = postitem.post

        if postitem.pos == 'begin' and post in postset:

            # indentation
            line = ' ' * (postitem.level * indent)

            # post id
            line += '<%s>' % (post.post_id_str(),)

            # subject
            if len(post.subject()) < 40:
                line += ' ' + post.subject()
            else:
                line += ' ' + post.subject()[:37] + '...'

            # tags
            if show_tags:
                line += '  [%s]' % (','.join(post.tags()),)

            # author
            if show_author:
                line += '  ' + post.author()

            # date
            if show_date and post.date_str() != '':
                line += ' (%s)' % (post.date_str(),)

            write(line + '\n')

@hkshell_cmd(add_events=True)
def cat(pps):
    """Prints the content of the given posts.

    The printout contains the contatenation of the posts exactly as they are
    in the post files, with two differences:

    - There is an additional attribute called ``Post-id``, which shows the
      post id of the post.
    - There are separators between posts. Separators are lines that consist of
      hyphens.

    **Arguments:**

    - `pps` (|PrePostSet|)
    """

    # We want to iterate on the posts in the order of their post ids, so we
    # collect the post ids and iterate over their sorted list.
    post_ids = sorted([post.post_id() for post in ps(pps)])

    first = True
    for post_id in post_ids:
        if first:
            first = False
        else:
            write('\n' + ('-' * 60) + '\n\n')
        post = postdb().post(post_id)
        write('Post-id: %s\n' % (post.post_id_str(),))
        post.write(options.output)

@hkshell_cmd(postset_operation=True, touching_command=True)
def d(posts):
    """Deletes the posts in `pps`.

    **Argument:**

    - `pps` (|PrePostSet|)
    """

    posts.forall.delete()

@hkshell_cmd(postset_operation=True, touching_command=True)
def dr(posts):
    """Deletes the posts in `pps` and all their children.

    **Argument:**

    - `pps` (|PrePostSet|)
    """

    posts.expf().forall.delete()

@hkshell_cmd(add_events=True, touching_command=True)
def j(pp1, pp2):
    """Joins two posts.

    Arguments:

    - `pp1` (|PrePost|) -- The post that will be the parent.
    - `pp2` (|PrePost|) -- The post that will be the child.
    """

    p1 = postdb().post(pp1, default_heap=gh())
    p2 = postdb().post(pp2, default_heap=gh())
    event('postset_calculated', 'j')
    if p1 != None and p2 != None:
        p2.set_parent(p1.post_id_str())


def edit_posts(pps):
    """Edits the posts in `pps`.

    **Argument:**

    - `pps` (|PrePostSet|)
    """

    posts = pps.sorted_list()
    if posts == []:
        hkutils.log('No post to edit.')
    else:

        # Editing the post files of given posts
        postdb().save()
        postfilenames = [ post.postfilename() for post in posts ]
        changed_files = edit_files(postfilenames)

        # Calculating postfilename_to_post
        postfilename_to_post = {}
        for post in posts:
            postfilename_to_post[post.postfilename()] = post

        # Reloading the modified posts
        for filename in postfilenames:
            post = postfilename_to_post[filename]
            if filename in changed_files:
                post.load()
                hkutils.log('Post "%s" reloaded.' % (post.post_id_str(),))
            else:
                hkutils.log('Post "%s" left unchanged.' %
                            (post.post_id_str(),))

@hkshell_cmd(postset_operation=True)
def e(pps):
    """Edits the posts in `pps`.

    **Argument:**

    - `pps` (|PrePostSet|)
    """

    edit_posts(pps)

@hkshell_cmd(postset_operation=True)
def er(pps):
    """Edits the posts in `pps` and all their children.

    **Argument:**

    - `pps` (|PrePostSet|)
    """

    edit_posts(pps.expf())

def add_post_to_heap(post, prefix, heap_id):
    """Adds the given post to a heap if it can find out which heap to use.

    **Argument:**

    - `post` (|Post|)
    - `prefix` (str) -- The prefix of the file.
    - `heap_id` (|HeapId| | ``None``) -- The id of the heap in which the post
      will be created. If ``None``, the value of |gh| is used.

    **Returns:** |Post| | ``None`` -- Returns ``None`` if the post was not
    added to any heap.
    """

    if heap_id is None:
        default_heap = gh()
        if default_heap is None:
            hkutils.log('Post cannot be created: no heap specified.')
            return None
        else:
            heap_id = default_heap
    postdb().add_new_post(post, heap_id, prefix=prefix)
    hkutils.log('Post created.')
    return post

@hkshell_cmd(add_events=True, touching_command=True)
def enew(prefix='', author='', parent=None, heap_id=None, dt=None):
    """Creates and edits a post.

    A temporary file with a post stub will be created and an editor will be
    opened so that the user can edit it. After saving the file, it will be read
    as a post file and the post created from it will be added to the post
    database. If the post stub was not edited, nothing will happen.

    **Arguments:**

    - `prefix` (str) -- The prefix of the file.
    - `author` (str) -- The author of the post.
    - `parent` (|Post| | ``None``) -- The parent of the post. If not ``None``,
      the subject of the parent is also copied.
    - `heap_id` (|HeapId| | ``None``) -- The id of the heap in which the post
      will be created. If ``None``, the value of |gh| is used.
    - `dt` (datetime | ``None`` | ``0``) -- The UTC datetime of the post. If
      ``None``, the current datetime will be used. If 0, no date will be added
      to the post.

    **Returns:** |Post| | ``None`` -- The newly created post.
    """

    tmp_file_fd, tmp_file_name = tempfile.mkstemp()
    try:
        post = hklib.Post.from_str('')
        post.set_author(author)

        if dt is None:
            dt = datetime.datetime.utcnow()
        if dt != 0:
            date_str = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
            post.set_date(date_str)

        if parent != None:
            parent = p(parent)
            post.set_parent(parent.post_id_str())
            post.set_subject(parent.subject())
            post.set_tags(parent.tags())
        post_str = post.postfile_str(force_print=set(['Author', 'Subject']))
        os.write(tmp_file_fd, post_str)
        os.close(tmp_file_fd)
        changed_files = edit_files([tmp_file_name])
        if len(changed_files) > 0:
            post = hklib.Post.from_file(tmp_file_name)
            return add_post_to_heap(post, prefix, heap_id)
        else:
            hkutils.log('No change in the data base.')
    finally:
        os.remove(tmp_file_name)

@hkshell_cmd(add_events=True)
def enew_str(post_string, prefix='', heap_id=None):
    """Creates a post from `post_string` and adds it to the post database.

    **Argument:**

    - `post_string` (str)
    - `prefix` (str) -- The prefix of the file.
    - `heap_id` (|HeapId| | ``None``) -- The id of the heap in which the post
      will be created. If ``None``, the value of |gh| is used.
    """

    post = hklib.Post.from_str(post_string)
    return add_post_to_heap(post, prefix, heap_id)

@hkshell_cmd(add_events=True)
def dl(from_=0, detailed_log=False, ps=False):
    """Downloads new posts from an IMAP server.

    **Arguments:**

    - `from_` (int) -- The messages whose index in the INBOX is lower than
      this parameter will not be downloaded.
    - `detailed_log` (bool) -- If ``True``, every mail found or download is
      reported.
    - `ps` (bool) -- If ``True``, the function returns the set of newly
      downloaded posts.

    **Returns:** |PostSet| | ``None`` -- The set of the newly downloaded posts
    if `ps` is ``True``; ``None`` otherwise.
    """

    if default_heap_var is None:
        hkutils.log("No default heap specified. Select a heap using 'sh()'.")
        return
    else:
        heap_id = default_heap_var

    email_downloader = \
        hkemail.EmailDownloader(postdb(), options.config, heap_id)
    email_downloader.connect()
    new_posts = email_downloader.download_new(int(from_), bool(detailed_log))
    email_downloader.close()
    if ps:
        return new_posts

##### Commands / tags #####

@hkshell_cmd(postset_operation=True, touching_command=True)
def pT(posts):
    """Propagates the tags of the posts in `pps` to all their children.

    **Argument:**

    - `pps` (|PrePostSet|)
    """

    for post in posts:
        def add_tags(p):
            for tag in post.tags():
                p.add_tag(tag)
        postdb().postset(post).expf().forall(add_tags)

@hkshell_cmd(postset_operation=True, touching_command=True)
def aT(posts, tags):
    """Adds the given tags to the posts in `pps`.

    **Arguments:**

    - `pps` (|PrePostSet|)
    - `tags` (|PreTagSet|) -- Tags to be added.
    """

    tags = tagset(tags)
    for p in posts:
        p.set_tags(tags.union(p.tags()))

@hkshell_cmd(postset_operation=True, touching_command=True)
def aTr(posts, tags):
    """Adds the given tags to the posts of the given postset and all their
    children.

    **Arguments:**

    - `pps` (|PrePostSet|)
    - `tags` (|PreTagSet|) -- Tags to be added.
    """

    tags = tagset(tags)
    for p in posts.expf():
        p.set_tags(tags.union(p.tags()))

@hkshell_cmd(postset_operation=True, touching_command=True)
def rT(posts, tags):
    """Removes the given tags from the posts in `pps`.

    **Arguments:**

    - `pps` (|PrePostSet|)
    - `tags` (|PreTagSet|) -- Tags to be removed.
    """

    tags = tagset(tags)
    for p in posts:
        p.set_tags(set(p.tags()) - tags)

@hkshell_cmd(postset_operation=True, touching_command=True)
def rTr(posts, tags):
    """Removes the given tags from the posts in `pps` and from all their
    children.

    **Arguments:**

    - `pps` (|PrePostSet|)
    - `tags` (|PreTagSet|) -- Tags to be removed.
    """

    tags = tagset(tags)
    for p in posts.expf():
        p.set_tags(set(p.tags()) - tags)

@hkshell_cmd(postset_operation=True, touching_command=True)
def sT(posts, tags):
    """Sets the given tags on the posts in `pps`.

    **Arguments:**

    - `pps` (|PrePostSet|)
    - `tags` (|PreTagSet|) -- Tags to be set.
    """

    tags = tagset(tags)
    for p in posts:
        p.set_tags(tags)

@hkshell_cmd(postset_operation=True, touching_command=True)
def sTr(posts, tags):
    """Sets the given tags on the posts in `pps` and on all their children.

    **Arguments:**

    - `pps` (|PrePostSet|)
    - `tags` (|PreTagSet|) -- Tags to be set.
    """

    tags = tagset(tags)
    for p in posts.expf():
        p.set_tags(tags)


##### Commands / subject #####

@hkshell_cmd(postset_operation=True, touching_command=True)
def pS(posts):
    """Propagates the subject of the posts in `pps` and all their children.

    **Argument:**

    - `pps` (|PrePostSet|)
    """

    for post in posts:
        postdb().postset(post).expf().forall.set_subject(post.subject())

@hkshell_cmd(postset_operation=True, touching_command=True)
def sS(posts, subject):
    """Sets the given subject for the posts in `pps`.

    **Arguments:**

    - `pps` (|PrePostSet|)
    - `subject` (str) - Subject to be set.
    """

    posts.forall.set_subject(subject)

@hkshell_cmd(postset_operation=True, touching_command=True)
def sSr(posts, subject):
    """Sets the given subject for the posts in `pps` and for all their
    children.

    **Arguments:**

    - `pps` (|PrePostSet|)
    - `subject` (str) - Subject to be set.
    """

    posts.expf().forall.set_subject(subject)

def capitalize_subject(post):
    """Capitalizes the subject of `post`

    **Arguments:**

    - post (|Post|)
    """

    post.set_subject(post.subject().capitalize())

@hkshell_cmd(postset_operation=True, touching_command=True)
def cS(posts):
    """Capitalizes the subject of the posts in `pps`.

    **Arguments:**

    - `pps` (|PrePostSet|)
    """

    posts.forall(capitalize_subject)

@hkshell_cmd(postset_operation=True, touching_command=True)
def cSr(posts):
    """Capitalizes the subject of the posts in `pps` and all their children.

    **Argument:**

    - `pps` (|PrePostSet|)
    """

    posts.expf().forall(capitalize_subject)

##### Commands / search #####

@hkshell_cmd()
def grep(pattern, pps=None):
    """Searches for `pattern` in `pps`.

    **Arguments:**

    - `pattern` (str) -- Regular expression.
    - `pps` (|PrePostSet|)

    **Returns:** |PostSet|

    **Examples:**

    Posts that contain ``"hh"``:

        >>> grep("master branch")
        PostSet([<post '3059'>, <post '2622'>])

    Posts that contain ``"hh"`` and ``"master branch"``:

        >>> grep("master branch", grep("hh"))
        PostSet([<post '3059'>])

    :func:`grep` can be used together with :func:`gen_page`:

        >>> gen_page(grep("master branch", grep("hh")))
    """

    if pps == None:
        ps = postdb().all()
    else:
        ps = postdb().postset(pps)

    r = re.compile(pattern)
    def has_pattern(post):
        if (r.search(post.author()) or
            r.search(post.subject()) or
            r.search(post.messid()) or
            r.search(post.date_str()) or
            r.search(post.parent()) or
            r.search(post.post_id_str()) or
            r.search(post.body())):
            return True
        for tag in post.tags():
            if r.search(tag):
                return True
        return False

    return ps.collect(has_pattern)


##### Starting hkshell #####

def exec_commands(commands):
    """Executes the given commands.

    **Argument:**

    - `commands` ([str])
    """

    for command in commands:
        # # comment out to access hkshell.* more easily
        # exec command in globals(), hkshell_commands
        exec command in hkshell_commands

def read_postdb(configfile):
    """Reads the config file and the post database from the disk.

    **Argument:**

    - `configfile` (str) -- The name of the config file to use as ``hk.cfg``.

    **Returns:** (ConfigParser, |PostDB|)
    """

    config = ConfigParser.ConfigParser()
    try:
        config.readfp(open(configfile))
    except IOError:
        hkutils.log('Config file not found: "%s"' % (configfile,))
        sys.exit(1)
    configdict = hkutils.configparser_to_configdict(config)
    hkconfig.unify_config(configdict)
    postdb = hklib.PostDB()
    postdb.read_config(configdict)

    # If there is only one heap, select it
    if len(postdb.heap_ids()) == 1:
        sh(postdb.heap_ids()[0])

    return configdict, postdb

def init():
    """Sets the default event handlers."""

    global modification_listener
    modification_listener = ModificationListener(postdb())
    listeners.append(modification_listener)

    global postpage_listener
    postpage_listener = PostPageListener(postdb())
    listeners.append(postpage_listener)

def import_module(modname, warning):
    """Imports the `modname` module.

    It prints whether it succeeded or not using :func:`hkutils.log`.

    **Argument:**

    - `modname` (str)
    - `warning` (bool): print warning if import fails
    """

    try:
        if warning:
            hkutils.log('Importing %s...' % (modname,))
        __import__(modname)
        hkutils.log('Importing %s OK' % (modname,))
    except ImportError, e:
        if str(e) == ('No module named ' + modname):
            if warning:
                hkutils.log('Module not found: "%s"' % (modname,))
        else:
            exc_info = sys.exc_info()
            raise exc_info[0], exc_info[1], exc_info[2]

def parse_args(args=None):
    """Parses the given command line options.

    **Argument:**

    - `args` ([str] | ``None``) -- Arguments to be processed. If ``None``,
      ``sys.argv[1:]`` is used.

    **Returns:** (optparse.Values, [str])
    """

    # Parsing the command line options

    parser = optparse.OptionParser()

    # Note: dest='before_commands' would be more logical than
    # dest='before_command' since it is a list; but the help text is more
    # sensible this way.
    parser.add_option('-b', '--before', dest='before_command',
                      help='Python code to execute before importing hkrc',
                      action='append', default=[])
    parser.add_option('-c', '--command', dest='after_command',
                      help='Python code to execute after importing hkrc',
                      action='append', default=[])
    parser.add_option('-r', '--hkrc', dest='hkrc',
                      help='Modules to import',
                      action='append', default=[])
    parser.add_option('--configfile', dest='configfile',
                      help='Configfile to use',
                      action='store', default='hk.cfg')
    parser.add_option('--noshell', dest='no_shell',
                      help='No shell',
                      action='store_true', default=False)
    parser.add_option('--version', dest='version',
                      help='Prints heapkeeper version and exits',
                      action='store_true', default=False)
    (cmdl_options, args) = parser.parse_args(args)
    return cmdl_options, args

def main(cmdl_options, args):
    """Initializes |hkshell|.

    It performs the following steps:

    1. Executes the "before" commands.
    2. Reads the configuration file and the post database.
    3. Sets the default event handlers.
    4. Executes the ``hkrc`` file(s).
    5. Executes the "after" commands.

    **Arguments:**

    - `cmdl_options` (object) -- Command line options as returned by
      optparse.OptionParser.parse_args. The attributes of the object are the
      command line arguments. The values of these arguments are strings or list
      of strings that contain the values of the command line arguments.
    - `args` ([str]) -- Command line arguments.
    """

    # Processing the command line options
    cmdl_options.after_command += args

    if cmdl_options.hkrc == []:
        # No warning if no hkrc module is present
        to_import = [('hkrc', False)]
    elif cmdl_options.hkrc == ['NONE']:
        to_import = []
    else:
        # Warn for all other missing modules
        to_import = [(module, True) for module in cmdl_options.hkrc]

    # Executing "before" commands
    exec_commands(cmdl_options.before_command)

    # Reading the configuration file and the post database.
    options.config, options.postdb = read_postdb(cmdl_options.configfile)

    # Init
    init()

    # Importing modules
    for modtuple in to_import:
        import_module(*modtuple)

    # Executing "after" commands
    exec_commands(cmdl_options.after_command)

    if cmdl_options.no_shell:
        return

    while True:

        # Creating a shell to the user

        # # use this to access hkshell.* more easily
        # locals = globals().copy()
        # locals.update(hkshell_commands)
        # code.interact(banner=options.shell_banner, local=locals)

        code.interact(banner=options.shell_banner, local=hkshell_commands)

        # User typed CTRL-D
        if options.save_on_ctrl_d is None:
            write('Do you want to save the post database? [yes/no/cancel] ')
            line = sys.stdin.readline().strip()

            # If the user typed "yes", save & quit
            if len(line) > 0 and line[0] in ['y', 'Y']:
                postdb().save()
                break
            # If the user typed "no", just quit
            elif len(line) > 0 and line[0] in ['n', 'N']:
                break
            # Otherwise go back to the interpreter
            else:
                pass
        elif options.save_on_ctrl_d:
            postdb().save()
            break
        else:
            break
