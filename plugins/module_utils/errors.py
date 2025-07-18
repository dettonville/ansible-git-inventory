from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import missing_required_lib


class MissingLibError(Exception):
    def __init__(self, library, exception, url=None):
        self.exception = exception
        self.library = library
        self.url = url
        super().__init__(missing_required_lib(self.library, url=self.url))
