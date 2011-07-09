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

# Copyright (C) 2011 Attila Nagy

""":mod:`hkp_reply_link` implements the "Reply link" plugin for Heapkeeper.

This plugin helps reply posts via your preferred email client.

It adds a "mailto:" link to all posts that include the subject and the
"In-Reply-To" as pre-defined header fields.

The plugin can be activated in the following way::

    >>> import hkp_reply_link
    >>> hkp_reply_link.start()

"""


import hkgen
import hkshell
import hkutils
import hkweb


def start(reply_email='set_this@your.heap.net'):
    """Starts the plugin.

    **Argument:**

    - `reply_email` (str) -- The email address to reply to.
    """

    def print_postitem_body_with_reply(self, postitem):
        """Prints the body of the post item.

        **Argument:**

        - `postitem` (|PostItem|)

        **Returns:** |HtmlText|
        """

        mailto_link = (
                'mailto:' +
                reply_email +
                '?subject=' + postitem.post.subject() +
                '&In-Reply-To=' + postitem.post.messid()
            )

        body = hkgen.BaseGenerator.print_postitem_body(self, postitem)

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
                     attributes='style="display: none;"'), '\n',
                 self.enclose(
                     self.print_link(
                         mailto_link,
                         'Reply via email'),
                     class_='button reply-link-button',
                     id='reply-link-button-' + post_id)),
                class_='post-body-buttons',
                tag='div',
                newlines=True)

        return self.enclose(
                   (buttons, body),
                   tag='div',
                   class_='post-body-container',
                   newlines=True,
                   id='post-body-container-' + post_id)

    hkweb.PostPageGenerator.print_postitem_body = \
        print_postitem_body_with_reply
