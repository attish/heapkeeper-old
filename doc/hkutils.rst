|hkutils|
=========

.. include:: defs.hrst

.. automodule:: hkutils

Directory structure
-------------------

.. autofunction:: plugin_dirs
.. autofunction:: plugin_src_dirs
.. autofunction:: update_path_with_plugin_src_dirs

Performance measurement
-----------------------

.. autofunction:: int_time
.. autofunction:: print_time

Exceptions
----------

.. autoclass:: HkException

    **Methods:**

    .. automethod:: __init__
    .. automethod:: __str__

Option handling (currently not used)
------------------------------------

.. autofunction:: arginfo
.. autofunction:: set_defaultoptions

Options handling
----------------

.. autofunction:: set_dict_items

Text structures
---------------

.. autofunction:: textstruct_to_str
.. autofunction:: is_textstruct
.. autofunction:: write_textstruct

Logging
-------

.. autofunction:: default_log_fun
.. autofunction:: set_log
.. autofunction:: log

Miscellaneous
-------------

.. autofunction:: file_to_string
.. autofunction:: string_to_file
.. autofunction:: utf8
.. autofunction:: uutf8
.. autofunction:: json_uutf8
.. autofunction:: calc_timestamp
.. autofunction:: humanize_timedelta
.. autofunction:: parse_date
.. autofunction:: copy_wo
.. autofunction:: plural
.. autofunction:: add_method
.. autofunction:: append_fun_to_method(class_, methodname, fun, resultfun=lambda res1, res2: res1)
.. autofunction:: insert_sep
.. autofunction:: configparser_to_configdict
.. autofunction:: quote_shell_arg
.. autofunction:: call
.. autoclass:: NOT_SET
