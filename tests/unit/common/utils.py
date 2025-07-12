from __future__ import absolute_import, division, print_function

__metaclass__ = type

# import os
import json

from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes


TEST_MODULES_IMPORT_PATH = "dettonville.utils"


def set_module_args(args):
    """prepare arguments so that they will be picked up during module creation"""
    args = json.dumps({"ANSIBLE_MODULE_ARGS": args})
    basic._ANSIBLE_ARGS = to_bytes(args)


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""


def exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    if "changed" not in kwargs:
        kwargs["changed"] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs["failed"] = True
    raise AnsibleFailJson(kwargs)


# # --- Mock AnsibleModule for testing ---
# # This class simulates the AnsibleModule provided by Ansible's core.
# # It captures calls to exit_json and fail_json, and allows mocking run_command.
# class MockAnsibleModule:
#     def __init__(self, argument_spec, supports_check_mode=False, **kwargs):
#         self.argument_spec = argument_spec
#         self.supports_check_mode = supports_check_mode
#         self.params = kwargs.get("params", {})
#         self.check_mode = kwargs.get("check_mode", False)
#         self.exit_json_called = False
#         self.fail_json_called = False
#         self.exit_args = None
#         self.fail_args = None
#         self.bin_path_map = {}  # Used to mock get_bin_path
#
#     def exit_json(self, **kwargs):
#         """Simulates AnsibleModule.exit_json and raises SystemExit."""
#         self.exit_json_called = True
#         self.exit_args = kwargs
#         raise SystemExit  # To stop execution after exit_json
#
#     def fail_json(self, **kwargs):
#         """Simulates AnsibleModule.fail_json and raises SystemExit."""
#         self.fail_json_called = True
#         self.fail_args = kwargs
#         raise SystemExit  # To stop execution after fail_json
#
#     def run_command(
#         self,
#         cmd,
#         check_rc=True,
#         data=None,
#         binary_data=False,
#         path_prefix=None,
#         cwd=None,
#         use_unsafe_shell=False,
#         prompt_regex=None,
#         environ_update=None,
#         umask=None,
#         encoding=None,
#         errors="surrogate_or_strict",
#         expand_user_and_vars=True,
#         complex_args=None,
#         **kwargs,
#     ):
#         """
#         Simulates AnsibleModule.run_command.
#         This method should be mocked in specific tests to control its output.
#         """
#         raise NotImplementedError("run_command must be mocked in tests")
#
#     def get_bin_path(self, executable, required=False):
#         """Simulates AnsibleModule.get_bin_path."""
#         if executable in self.bin_path_map:
#             return self.bin_path_map[executable]
#         if required:
#             self.fail_json(msg=f"Executable '{executable}' not found")
#         return None
#
#     def atomic_move(self, src, dest):
#         """Simulates AnsibleModule.atomic_move."""
#         # For testing purposes, just simulate a successful move if source exists
#         if os.path.exists(src):
#             os.rename(src, dest)
#             return True
#         return False
#
#     def tmpdir(self):
#         """Simulates AnsibleModule.tmpdir for temporary file paths."""
#         return "/tmp/ansible_test_tmp"


# Mock ansible basic module
class MockAnsibleModule:
    def __init__(self, argument_spec=None,
                 supports_check_mode=False, **kwargs):

        self.supports_check_mode = supports_check_mode
        self.params = kwargs.get("params", {})
        self.check_mode = kwargs.get("check_mode", False)
        self.exit_json_called = False
        self.fail_json_called = False
        self.exit_args = None
        self.fail_args = None
        self.exit_json_kwargs = {}
        self.fail_json_kwargs = {}
        self.bin_path_map = {}  # Used to mock get_bin_path
        self.changed = False

        # self._name = TEST_MODULES_IMPORT_PATH + "." + self.__class__.__name__
        self._name = "dettonville.utils." + self.__class__.__name__
        # self._name = self.__class__.__name__
        self.debug_messages = []

    def debug(self, msg):
        self.debug_messages.append(msg)

    def exit_json(self, **kwargs):
        self.exit_json_called = True
        self.exit_json_kwargs = kwargs

    def fail_json(self, **kwargs):
        self.fail_json_called = True
        self.fail_json_kwargs = kwargs

    def run_command(self, cmd, **kwargs):
        # Mock successful git command
        return 0, "", ""
