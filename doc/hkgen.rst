|hkgen|
=======

.. include:: defs.hrst

.. automodule:: hkgen

GeneratorOptions
----------------

.. autoclass:: GeneratorOptions

    .. automethod:: __init__

Base generator
--------------

.. autoclass:: BaseGenerator

    **Methods:**

    .. automethod:: __init__
    .. automethod:: escape
    .. automethod:: escape_url
    .. automethod:: print_link
    .. automethod:: print_comment
    .. automethod:: enclose
    .. automethod:: section_begin
    .. automethod:: section_end
    .. automethod:: section
    .. automethod:: postitem_is_star_needed
    .. automethod:: print_postitem_author_core
    .. automethod:: print_postitem_author
    .. automethod:: print_postitem_subject_core
    .. automethod:: print_postitem_subject
    .. automethod:: print_postitem_tags_core
    .. automethod:: print_postitem_tags
    .. automethod:: print_postitem_threadlink_core
    .. automethod:: print_postitem_threadlink
    .. automethod:: print_postitem_post_id_core
    .. automethod:: print_postitem_post_id
    .. automethod:: print_postitem_parent_post_id_core
    .. automethod:: print_postitem_parent_post_id
    .. automethod:: format_timestamp
    .. automethod:: print_postitem_date_core
    .. automethod:: print_postitem_date
    .. automethod:: print_postitem_body_core
    .. automethod:: print_postitem_body
    .. automethod:: print_postitem_link
    .. automethod:: print_postitem_begin
    .. automethod:: print_postitem_end
    .. automethod:: print_postitem_inner
    .. automethod:: print_postitem_flat
    .. automethod:: print_postitem
    .. automethod:: walk_thread
    .. automethod:: walk_exp_posts
    .. automethod:: get_print_fun
    .. automethod:: print_postitems
    .. automethod:: set_postitem_attr
    .. automethod:: reverse_threads
    .. automethod:: enclose_posts
    .. automethod:: enclose_threads
    .. automethod:: print_main_index_page
    .. automethod:: print_thread_page
    .. automethod:: print_html_header
    .. automethod:: print_html_footer
    .. automethod:: print_html_page

Static generator
----------------

.. autoclass:: StaticGenerator

    **Methods:**

    .. automethod:: __init__
    .. automethod:: print_html_head_content
    .. automethod:: print_postitem_link
    .. automethod:: settle_files_to_copy
    .. automethod:: write_page
    .. automethod:: is_file_newer
    .. automethod:: outdated_thread_pages
    .. automethod:: outdated_post_pages
    .. automethod:: write_main_index_page
    .. automethod:: write_thread_pages
    .. automethod:: write_all

.. autoclass:: Generator

    **Methods:**

    .. automethod:: __init__

GivenPostsGenerator
-------------------

.. autoclass:: GivenPostsGenerator

    **Methods:**

    .. automethod:: __init__
    .. automethod:: print_given_posts_page
    .. automethod:: write_given_posts_page
    .. automethod:: write_all
