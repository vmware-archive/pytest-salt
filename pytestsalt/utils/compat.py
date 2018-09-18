# -*- coding: utf-8 -*-
'''
    pytestsalt.utils.compat
    ~~~~~~~~~~~~~~~~~~~~~~~

    Imports compatability layer
'''

try:
    # Salt > 2017.1.1
    # pylint: disable=invalid-name
    import salt.utils.files
    fopen = salt.utils.files.fopen
except AttributeError:
    # Salt <= 2017.1.1
    # pylint: disable=invalid-name
    fopen = salt.utils.fopen
