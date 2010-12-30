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


function setPostReviewed(postId) {
    // Sets the post's thread to reviewed.
    //
    // Argument:
    //
    // - postId (postId)

    ajaxQuery(
        "/set-post-reviewed",
        {'post_id': postIdToPostIdStr(getRootPostId())},
        function() {
            location.reload();
        });
}

$(document).ready(function() {

    // Adding the 'Set to reviewed' button
    addGlobalButton(
        'Set to reviewed',
        'set-to-reviewed-button',
        function(postId) {
            setPostReviewed(postId);
        });
});
