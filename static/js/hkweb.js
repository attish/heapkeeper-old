// This file is part of Heapkeeper.
//
// Heapkeeper is free software: you can redistribute it and/or modify it
// under the terms of the GNU General Public License as published by the Free
// Software Foundation, either version 3 of the License, or (at your option) any
// later version.
//
// Heapkeeper is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
// FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
// more details.
//
// You should have received a copy of the GNU General Public License along with
// Heapkeeper.  If not, see <http://www.gnu.org/licenses/>.

// Copyright (C) 2010 Csaba Hoch


/*global $, escape, location, scroll, window, document */


///// Types /////

// - postId: a string which contains a heap id and a post index, separated with
//   a '-' sign. Example: 'myheap-11'
// - postIdStr: a string which is very similar to postId, but uses '/' as a
//   separator. Internally Heapkeeper's JavaScript code uses PostId, because he
//   '/' character has a special meaning in JQuery, but externally Heapkeeper
//   uses postIdStr.

function postIdToPostIdStr(postId) {
    return postId.replace('-', '/');
}

function postIdStrToPostId(postId) {
    return postId.replace('/', '-');
}


///// Communication with the server: HTML queries and AJAX /////

var JSON_ESCAPE_CHAR = '\x00';

function stringify_object(obj) {
    // Converts the given object into a string.
    //
    // The result is either a string (e.g. "text") or the JSON escape character
    // followed by a stringified JSON object (e.g. "\x00[1,2]").
    //
    // Argument:
    // - obj (object)
    //
    // Returns: str

    return '\x00' + JSON.stringify(obj);
}


function url_and_dict_to_http_query(url, args) {
    // Converts an URL and a dictionary into a HTTP query string.
    //
    // - url(str) - args(object) -- `args` will be converted to a HTTP query
    //   string. The values in `args` will be converted to JSON.
    //
    // Returns: str -- it will look like this:
    //
    //     <url>?<key1>=<value1>&<key2>=<value2>&...
    //
    // where:
    // - all keys are escaped
    // - all values are converted to JSON and then escaped
    //
    // Example:

    var data = [url];
    var first = true;
    $.each(args, function(key, value) {
        if (first) {
            data.push('?');
            first = false;
        } else {
            data.push('&');
        }
        var value_param = stringify_object(value);
        data.push(escape(key) + '=' + escape(value_param));
    });

    return data.join('');
}

function gotoURL(url, args) {
    // Goes to the specified URL; the query parameters will be created from
    // `args`.
    //
    // - url(str) -- The URL to load. If empty string, the current URL (with
    //   'args' as query parameters) will be loaded.
    // - args(object) -- `args` will be converted to a JSON text and sent to
    //   the server as query parameters.
    var query_url = url_and_dict_to_http_query(url, args);
    $(location).attr('href', query_url);
}

function ajaxQuery(url, args, callback) {
    // Performs an AJAX query using JSON texts and calls the callback function
    // with the result.
    //
    // - url(str) -- The URL to be sent to the server.
    // - args(object) -- `args` will be converted to a JSON text and sent to the
    //   server.
    // - callback (fun(result)) -- Function to be called after we received the
    //   result. The server is expected to send a JSON text that will be
    //   converted to the `result` object.

    var data = {};
    $.each(args, function(key, value) {
        data[key] = stringify_object(value);
    });

    $.ajax({
        url: url,
        dataType: 'json',
        data: data,
        type: 'post',
        success: callback
    });
}


///// Basic DOM stuff /////

function setButtonVisibility(button, visibility) {
    // Sets the visibility of a button.
    //
    // When the button has to be hidden, it is not animated, but when it
    // appears, it is.
    //
    // Arguments:
    //
    // - button(JQuery)
    // - visibility(str) -- Either 'show' or 'hide'.

    if (visibility == 'show') {
        button.animate({opacity: visibility}, 'fast');
    } else {
        button.hide();
    }
}


///// Scrolling /////

// Code copied from Peter-Paul Koch:
// http://www.quirksmode.org/js/findpos.html
function ObjectPosition(obj) {
    var curleft = 0;
    var curtop = 0;
    if (obj.offsetParent) {
        do {
            curleft += obj.offsetLeft;
            curtop += obj.offsetTop;
        } while (obj == obj.offsetParent);
    }
    return [curleft, curtop];
}

// Code copied from Michael Khalili:
// http://www.michaelapproved.com/articles/scroll-to-object-without-leaving-page
function ScrollTo(obj) {
    var objpos = ObjectPosition(obj);
    scroll(0,objpos[1]);
    window.scrollTo(0, objpos[1]);
}

function ScrollToId(id) {
    ScrollTo(document.getElementById(id));
}


///// Post body visibility /////

function getPostIds() {
    // Returns an array that contains all post ids present on the page.
    //
    // Returns: [str]

    return $('.post-body-container').map(function(index) {
        return $(this).attr('id').replace(/post-body-container-/, '');
    });
}

function getRootPostId() {
    // Returns the root of the thread that is displayed.
    //
    // Returns: str

    return location.href.replace(/^.*\/([^\/]+)\/([^\/]+)$/, '$1-$2');
}


function showPostBody(postId, count) {
    // Shows a post body and hides the "Show body" button.
    //
    // Argument:
    //
    // - postId (PostId)
    // - count (int)

    if (count == undefined) {
        var postBody = $('#post-body-container-' + postId);
        var showButton = $('#post-body-show-button-' + postId);
    } else {
        var postBody = $('#new-' + count + '-post-body-container-' + postId);
        var showButton = $('#new-' + count + '-post-body-show-button-' +
            postId);
    }

    postBody.show('fast');
    setButtonVisibility(showButton, 'hide');
}

function hidePostBody(postId, count) {
    // Hides a post body and shows the "Show body" button.
    //
    // Argument:
    //
    // - postId (postId)
    // - count (int)

    if (count == undefined) {
        var postBody = $('#post-body-container-' + postId);
        var showButton = $('#post-body-show-button-' + postId);
    } else {
        var postBody = $('#new-' + count + '-post-body-container-' + postId);
        var showButton = $('#new-' + count + '-post-body-show-button-' +
            postId);
    }

    postBody.hide('fast');
    setButtonVisibility(showButton, 'show');
}

function hideNewPostBody(postId) {
    // Hides a new post body and shows the "Show body" button.
    //
    // Argument:
    //
    // - postId (postId)
    // - count (int)

    $('#new-' + count + '-post-body-container-' + postId).hide('fast');
    setButtonVisibility(
        $('#new-' + count + '-post-body-show-button-' + postId),
        'show');
}

// High level funtions

function hideAllPostBodies() {
    // Turns off the visibility for all visible post bodies.

    $('[id|=post-body-container]').hide();
    $('[id|=post-body-show-button]').show();
}

function showAllPostBodies() {
    // Turns on the visibility for all hidden post bodies.

    $('[id|=post-body-container]').show();
    $('[id|=post-body-show-button]').hide();
}


///// Post body editing /////

// Keys: post ids that are being edited.
// Values: mode of editing: either 'body' if the body is edited or 'raw' if the
// raw post text is edited.
var editState = {};

function getRawPostRequest(postId, mode, callback) {
    // Gets the raw body of the given post and executes a callback function with
    // it.
    //
    // Arguments:
    //
    // - postId (PostId)
    // - mode(str) -- Either 'body' or 'raw'.
    // - callback (fun(rawPostBody: str))

    var postIdStr = postIdToPostIdStr(postId);
    if (mode == 'body') {
        $.get("/raw-post-bodies/" + postIdStr, {}, callback);
    } else if (mode == 'raw') {
        $.get("/raw-post-text/" + postIdStr, {}, callback);
    }
}

function setPostContentRequest(id, newPostText, mode, callback) {
    // Changes or creates a post.
    //
    // Depending on the value of the `mode` parameter, this function either:
    // - changes the body of an existing post,
    // - changes the whole text of an existing post,
    // - creates a new post as a child to an existing post,
    // - creates a new post as a new root of a heap.
    // Changes either the body or the whole text of an existing post
    // Sets the body of the given post in a raw format or create new root.
    //
    // Arguments:
    //
    // - id (PostId|HeapId) -- The PostID of the post to be changed or used as
    //   a parent, or the HeapId of the heap to add a new root to.
    // - newPostText(str)
    // - mode(str) -- 'body', 'raw', 'new' or 'newroot'.
    // - callback (fun(result)) -- Function to be called after we set the post
    //   body. `result` is the information returned by the server.

    if (mode == 'body') {
        ajaxQuery(
            "/set-post-body",
            {'post_id': postIdToPostIdStr(id),
             'new_body_text': newPostText},
            callback);
    } else if (mode == 'raw') {
        ajaxQuery(
            "/set-raw-post",
            {'post_id': postIdToPostIdStr(id),
             'new_post_text': newPostText},
            callback);
    } else if (mode == 'new') {
        ajaxQuery(
            "/new-post",
            {'post_id': postIdToPostIdStr(id),
             'new_body_text': newPostText},
            callback);
    } else if (mode == 'newroot') {
        ajaxQuery(
            "/add-new-root",
            {'heap_id': id,
             'new_body_text': newPostText},
            callback);
    }
}

function getPostBodyRequest(postId, callback) {
    // Gets the body of the given post.
    //
    // Arguments:
    //
    // - postId (PostId)
    // - callback (fun(result)) -- Function to be called with the post body.
    //   `result` is the information returned by the server.

    ajaxQuery(
        "/get-post-body",
        {'post_id': postIdToPostIdStr(postId)},
        callback);
}

function editPostStarted(postId, count) {
    // Should be called when editing the post body has been started.
    //
    // - postId (PostId)
    // - count (id)

    if (count == undefined)
        var prefix = '#post-';
    else
        var prefix = '#new-' + count + '-post-';

    var postBodyContainer = $(prefix + 'body-container-' + postId);

    setButtonVisibility($(prefix + 'body-edit-button-' + postId), 'hide');
    setButtonVisibility($(prefix + 'raw-edit-button-' + postId), 'hide');
    setButtonVisibility($(prefix + 'body-addchild-button-' + postId), 'hide');
    setButtonVisibility($(prefix + 'body-save-button-' + postId), 'show');
    setButtonVisibility($(prefix + 'body-cancel-button-' + postId), 'show');
    setButtonVisibility($(prefix + 'body-delete-button-' + postId), 'hide');

    var textArea = $('textarea', postBodyContainer);

    // Save the post body for shift-enter
    textArea.bind('keypress', function(e) {
        if (e.which == 13 && e.shiftKey) {
            e.preventDefault();
            savePost(postId);
        }
    });
}

function editPostFinished(postId) {
    // Should be called when editing the post body has been finished.
    //
    // - postId (PostId)

    setButtonVisibility($('#post-body-edit-button-' + postId), 'show');
    setButtonVisibility($('#post-raw-edit-button-' + postId), 'show');
    setButtonVisibility($('#post-body-addchild-button-' + postId), 'show');
    setButtonVisibility($('#post-body-save-button-' + postId), 'hide');
    setButtonVisibility($('#post-body-cancel-button-' + postId), 'hide');
    setButtonVisibility($('#post-body-delete-button-' + postId), 'show');

    delete editState[postId];
}

function editPost(postId, mode) {
    // Lets the user edit the body of a post.
    //
    // The post-body-content box is replaced with a textarea that contains
    // the post body.
    //
    // Argument:
    //
    // - postId (PostId)
    // - mode(str) -- Either 'body' or 'raw'.

    getRawPostRequest(postId, mode, function(postText) {
        var postBodyContainer = $('#post-body-container-' + postId);
        var postBodyContentNode = $('.post-body-content', postBodyContainer);

        editState[postId] = mode;

        // Replacing the post-body-content box with a textarea
        postBodyContentNode.after(
            '<textarea id="post-body-textarea-' + postId + '"' +
            ' rows="10" cols="80">' +
            '</textarea>').remove();

        // Adding the text to the textarea
        var textArea = $('textarea', postBodyContainer);
        textArea.attr('class', 'post-body-content');
        textArea.val(postText);
        textArea.focus();

        editPostStarted(postId);
     });
}

function isNewNameAvailable(postId, count)
{
    return !$('#new-' + count + '-post-summary-' + postId).length;
}

function findAvailableNewName(postId)
{
    count = 1;
    while (!isNewNameAvailable(postId, count))
        count++;
    return count;
}

function renameToNew(clone, type, postId, count)
{
    if (type == 'summary')
        var elem = clone;
    else
        var elem = clone.find('#' + 'post-' + type + '-' + postId);
    var newID = 'new-' + count + '-post-' + type + '-' + postId;
    elem.attr('id', newID);
    elem.id = newID;

    return elem;
}

function bindNewPost(newPostSummary, postId, count)
{
    // Hide
    newPostSummary.find('#new-' + count + '-post-body-hide-button-' + postId).bind(
        'click',
        function() { hidePostBody(postId, count); }
    );

    // Show
    newPostSummary.find('#new-' + count + '-post-body-show-button-' + postId).bind(
        'click',
        function() { showPostBody(postId, count); }
    );

    // Save
    newPostSummary.find('#new-' + count + '-post-body-save-button-' +
                        postId).bind(
        'click',
        function() { savePostNew(postId, count); }
    );

    // Cancel
    newPostSummary.find('#new-' + count + '-post-body-cancel-button-' +
                        postId).bind(
        'click',
        function() { cancelPostNew(postId, count); }
    );
}

function addChildPost(postId) {
    // Add a child to an existing post.
    //
    // The post doesn't exist on the Heap until it is saved (this is
    // how hkshell's enew() works). This means that post summaries on
    // the page either represent real posts or newly created, yet
    // unsaved posts.
    //
    // New posts are created by copying existing posts, changing their
    // "id" attribute.

    // The summary of the post for which a new child is being created.
    var parentPostSummary = $('#post-summary-' + postId);

    // Find the element after which the new post box will be added.
    var beforePostBox = $('#post-summary-' + postId).add(
                    '#post-summary-' + postId + ' ~ .post-box').last()

    // Find new name for new post summary.
    // `postId` and `count` will identify the new post.
    var count = findAvailableNewName(postId);

    // Add new post box.
    var newPostBoxID = 'new-' + count + '-post-box-' + postId;
    var newPostBoxHTML = '<div class="post-box" id="' +
        newPostBoxID + '"></div>';
    beforePostBox.after(newPostBoxHTML);
    var newPostBox = $('#' + newPostBoxID);

    // Clone post summary and add to new post box.
    var newPostSummary = parentPostSummary.clone();
    newPostBox.append(newPostSummary);

    // Change IDs in the clone for summary, container and buttons.
    renameToNew(newPostSummary, 'summary', postId, count);
    renameToNew(newPostSummary, 'body-show-button', postId, count);
    renameToNew(newPostSummary, 'body-container', postId, count);
    renameToNew(newPostSummary, 'body-hide-button', postId, count);
    renameToNew(newPostSummary, 'body-edit-button', postId, count);
    renameToNew(newPostSummary, 'raw-edit-button', postId, count);
    renameToNew(newPostSummary, 'body-addchild-button', postId, count);
    renameToNew(newPostSummary, 'body-save-button', postId, count);
    renameToNew(newPostSummary, 'body-cancel-button', postId, count);
    renameToNew(newPostSummary, 'body-delete-button', postId, count);

    // Switch clone into edit mode.
    var newPostBodyContainer = newPostSummary.find('.post-body-container');
    var newPostBodyContentNode = newPostSummary.find('.post-body-content');
    newPostBodyContentNode.after(
        '<textarea id="new-' + count + '-post-body-textarea-' + postId +
        '"' + ' rows="10" cols="80">' +
        '</textarea>').remove();

    // Adding the text to the textarea
    var textArea = $('textarea', newPostBodyContainer);
    textArea.attr('class', 'post-body-content');
    textArea.val('');
    textArea.focus();

    editPostStarted(postId, count);

    // Alter clone.
    var newPSIndex = newPostSummary.find('.index');
    newPSIndex.html('&lt;new&gt;');
    bindNewPost(newPostSummary, postId, count);
}

function savePost(postId) {
    // Saves the contents of the post's textarea as the new post body.
    //
    // The textarea is replaced with the post-body-content box that contains
    // the new body.
    //
    // Argument:
    //
    // - postId (PostId)

    var postBodyContainer = $('#post-body-container-' + postId);
    var textArea = $('textarea', postBodyContainer);
    var newPostText = textArea.val();
    var mode = editState[postId];

    setPostContentRequest(postId, newPostText, mode, function(result) {

        if (result.error) {
            window.alert('Error occured:\n' + result.error);
            return;
        }

        if (mode == 'body') {
            // Replacing the textArea with the received post-body-container
            // box
            textArea.replaceWith(result.new_body_html);
        } else if (mode == 'raw') {
            var postSummary = $('#post-summary-' + postId);
            postSummary.replaceWith(result.new_post_summary);
            addEventHandlersToPostSummary(postId);
            if (result.major_change) {
                window.alert(
                    'A major change was made on the post that may have ' +
                    'affected the thread structure. To see the most current ' +
                    'thread structure, please reload the page.');
            }
        }

        editPostFinished(postId);
     });
}

function cancelEditPost(postId) {
    // Saves the contents of the post's textarea as the new post body.
    //
    // The textarea is replaced with the post-body-content box that contains
    // the new body.
    //
    // Argument:
    //
    // - postId (PostId)

    var postBodyContainer = $('#post-body-container-' + postId);
    var textArea = $('textarea', postBodyContainer);

    getPostBodyRequest(postId, function(result) {

        if (result.error) {
            window.alert('Error occured:\n' + result.error);
            return;
        }

        // Replacing the textArea with the received post-body-container
        // box
        textArea.replaceWith(result.body_html);

        editPostFinished(postId);
     });
}

function savePostNew(postId, count) {
    // Saves the contents of the new post's textarea as the new post's body.
    //
    // The textarea is replaced with the post-body-content box that contains
    // the body of the new post.
    //
    // Arguments:
    //
    // - postId (PostId)
    // - count (int)

    var postBodyContainer = $('#new-' + count +
        '-post-body-container-' + postId);
    var textArea = $('textarea', postBodyContainer);
    var newPostText = textArea.val();
    var mode = 'new';

    setPostContentRequest(postId, newPostText, mode, function(result) {

        if (result.error) {
            window.alert('Error occured:\n' + result.error);
            return;
        }

        var newPostId = postIdStrToPostId(result.new_post_id);
        var postSummary = $('#new-' + count + '-post-summary-' + postId);
        postSummary.replaceWith(result.new_post_summary);
        addEventHandlersToPostSummary(newPostId);

        // TODO is this needed?
        //editPostFinished(newPostId);
     });
}

function savePostNewRoot() {
    // Saves the contents of the new post's textarea as a new root.
    //
    // Upon completion, the browser is redirected to this new root.
    // The target heap is taken from the value of the selector input
    // field.
    //
    // This function takes no parameters as all necessary information (the
    // target heap and the post text) is taken from the form itself.

    var postBodyContainer = $('#new-root-post-body-container-new-root')
    var textArea = $('textarea', postBodyContainer);
    var newPostText = textArea.val();
    var mode = 'newroot'
    var heapId = $('#heapselector').val()

    setPostContentRequest(heapId, newPostText, mode, function(result) {

        if (result.error) {
            window.alert('Error occured:\n' + result.error);
            return;
        }

        var newPostId = result.new_post_id;
        window.location = '/posts/' + newPostId;
     });
}

function cancelPostNew(postId, count) {
    // Just throw the new post away

    var postBox = $('#new-' + count +
        '-post-box-' + postId);
    postBox.remove();
}

function saveHeaps() {
    // Equivalent to hkshell's `s()`.
    ajaxQuery(
        "/save",
        {},
        function(result) {
            if (result.error) {
                window.alert('Error occured:\n' + result.error);
                return;
            }
            window.alert('Save successful.');
        }
    );
}

function deletePost(postId) {
    // Lets the user delete a post.
    //
    // Since deleting the post makes all its children root posts, the
    // post-body-content box is removed altogether.
    //
    // Argument:
    //
    // - postId (PostId)

    if (!confirm('Are you sure?')) return;

    ajaxQuery(
        "/delete-post",
        {'post_id': postIdToPostIdStr(postId)},
        function(result) {
            if (result.error) {
                window.alert('Error occured:\n' + result.error);
                return;
            }
        }
    );

    var postSummary = $('#post-summary-' + postId);
    postSummary.parent().remove();

    // If root is deleted, redirect browser to index.
    if (($('.post-box').length == 0)) {
        window.location.pathname = '';
    }
}

function confirmExit() {
    // Asks confirmation before leaving the page if there are any post being
    // edited.

    var needToConfirm = false;
    var postIdsStr = '';
    var separator = '';

    $.each(editState, function(postId, state) {

        postIdsStr = postIdsStr + separator + postIdToPostIdStr(postId);

        // This is the first postId
        if (!needToConfirm) {
            separator = ', ';
            needToConfirm = true;
        }
    });

    if (needToConfirm) {
        return 'You have attempted to leave this page, but there are posts ' +
               'being edited: ' + postIdsStr;
    }
}

///// Adding new buttons /////

function addGlobalButton(buttonText, buttonId, eventHandler) {
    // Adds the specified kind of button to global buttons.
    //
    // Arguments:
    //
    // - buttonText (str) -- The text of the button.
    // - buttonId (str) -- The button's HTML id.
    // - eventHandler(function(postId)) -- Functions that will be called when
    //   the button is clicked on.

    var globalButtons = $('.global-buttons');
    globalButtons.append(
        '<span class="button global-button" id="' + buttonId + '">' +
        buttonText +
        '</span>');
    $('#' + buttonId).bind('click', function() {
        eventHandler();
    });
}

function addBodyButtons(buttonText, buttonName, eventHandler) {
    // Adds the specified kind of button to each post body container.
    //
    // Arguments:
    //
    // - buttonText (str) -- The text of the button.
    // - buttonName (str) -- The button's HTML id will be
    //   buttonName + '-' + postId
    // - eventHandler(function(postId)) -- Functions that will be called when
    //   the button is clicked on.

    getPostIds().each(function(index) {
        var postId = this;
        var postBodyContainer = $('#post-body-container-' + postId);
        var postBodyButtons = $('.post-body-buttons', postBodyContainer);
        var buttonId = buttonName + '-' + postId;
        postBodyButtons.append(
            '<span class="button post-body-button" ' +
            'id="' + buttonId + '">' +
            buttonText +
            '</span>');
        $('#' + buttonId).bind('click', function() {
            eventHandler(postId);
        });
    });
}

///// Adding event handlers /////

function addEventHandlersToPostSummary(postId) {
    // Adds the necessary event handlers to the nodes inside a post summary.
    //
    // Argument:
    //
    // - postId(PostId)

    $('#post-body-hide-button-' + postId).bind('click', function() {
        hidePostBody(postId);
    });

    $('#post-body-show-button-' + postId).bind('click', function() {
        showPostBody(postId);
    });

    $('#post-body-edit-button-' + postId).bind('click', function() {
        editPost(postId, 'body');
    });

    $('#post-raw-edit-button-' + postId).bind('click', function() {
        editPost(postId, 'raw');
    });

    $('#post-body-addchild-button-' + postId).bind('click', function() {
        addChildPost(postId);
    });

    $('#post-body-save-button-' + postId).bind('click', function() {
        savePost(postId);
    });

    $('#post-body-cancel-button-' + postId).bind('click', function() {
        cancelEditPost(postId);
    });
    $('#post-body-delete-button-' + postId).bind('click', function() {
        deletePost(postId);
    });
}

$(document).ready(function() {

    $('[id|=post-body-show-button]').hide();

    $('#hide-all-post-bodies').bind('click', function() {
        hideAllPostBodies();
    });

    $('#show-all-post-bodies').bind('click', function() {
        showAllPostBodies();
    });

    // Adding the event handlers to the nodes inside post summaries
    getPostIds().each(function(index) {
        var postId = this;
        addEventHandlersToPostSummary(postId);
    });

    window.onbeforeunload = confirmExit;
});
