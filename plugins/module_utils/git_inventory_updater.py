from __future__ import absolute_import, division, print_function

__metaclass__ = type

"""

Module utility class that:

1) utilizes InventoryParser class instance to add/update/remove groups and/or hosts
   and respective vars for a specified YAML-based inventory.
2) if git repo is provided, will:
    - clone (to a temporary repo directory if not specified) and
    - commit and push the inventory changes to the specified inventory repo
    - and remove or keep the temporary directory as specified.

"""

import logging
import shutil
import tempfile
import inspect
from typing import Type, TypeVar

from ansible.module_utils.common.text.converters import to_text

# noinspection PyUnresolvedReferences
from ansible_collections.dettonville.git_inventory.plugins.module_utils.inventory_parser import (
    InventoryParser,
)

# noinspection PyUnresolvedReferences
from ansible_collections.dettonville.utils.plugins.module_utils.git_actions import Git

# noinspection PyUnresolvedReferences
from ansible_collections.dettonville.utils.plugins.module_utils.utils import (
    PrettyLog,
    get_collection_version,
    UtilsModuleException,
)

# _LOGLEVEL_DEFAULT = "INFO"
_LOGLEVEL_DEFAULT = "DEBUG"
T = TypeVar("T")


def class_init_wrapper(cls: Type[T], *args, **kwargs) -> T:
    """
    A wrapper function that dynamically filters args and kwargs for a class constructor.

    Args:
        cls: The class to be instantiated.
        *args: Positional arguments to pass to the constructor.
        **kwargs: A dictionary of keyword arguments.

    Returns:
        An instance of the class with filtered args and kwargs.

    Raises:
        TypeError: If required parameters are missing from args/kwargs.
    """
    init_signature = inspect.signature(cls.__init__)
    valid_params = {}
    missing_required = []
    param_names = list(init_signature.parameters.keys())

    # Skip 'self' parameter
    if param_names and param_names[0] == "self":
        param_names = param_names[1:]

    # Handle positional arguments
    for i, arg in enumerate(args):
        if i < len(param_names):
            param_name = param_names[i]
            param = init_signature.parameters[param_name]

            # Skip **kwargs parameters for positional assignment
            if param.kind != inspect.Parameter.VAR_KEYWORD:
                valid_params[param_name] = arg

    # Handle keyword arguments
    for name, param in init_signature.parameters.items():
        # Skip 'self' parameter
        if name == "self":
            continue

        # Skip if already handled by positional arguments
        if name in valid_params:
            continue

        # Skip positional-only parameters
        if param.kind == inspect.Parameter.POSITIONAL_ONLY:
            continue

        # Handle **kwargs in the constructor's signature
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            # Add all remaining kwargs that weren't explicitly handled
            remaining_kwargs = {
                k: v for k, v in kwargs.items() if k not in valid_params
            }
            valid_params.update(remaining_kwargs)
            continue

        # Check if parameter is provided in kwargs
        if name in kwargs:
            valid_params[name] = kwargs[name]
        elif param.default is inspect.Parameter.empty:
            # This is a required parameter without a default value
            missing_required.append(name)
        # If parameter has a default, we don't need to do anything

    # Check for missing required parameters
    if missing_required:
        raise TypeError(
            f"Missing required parameters for {cls.__name__}: {missing_required}"
        )

    return cls(**valid_params)


class GitInventoryUpdater:

    def __init__(
        self,
        module,
        inventory_file,
        git_repo_config=None,
        test_mode=False,
        remove_repo_dir=True,
        **kwargs,
    ):

        self.module = module
        if hasattr(module, "_name"):
            # if '_name' in module:
            self.module_name = module._name
        else:
            self.module_name = self.__class__.__name__
        # self.module_name = kwargs.get("module_name", self.__class__.__name__)

        log_prefix = "%s.init():" % self.__class__.__name__
        self.loglevel = kwargs.get("logging_level", _LOGLEVEL_DEFAULT)

        logging.basicConfig(level=self.loglevel)
        # logging.basicConfig(level=self.loglevel, stream=sys.stdout)
        self.log = logging.getLogger()

        # self.log.info("%s loglevel=%s", log_prefix, self.loglevel)
        self.log.debug("%s loglevel=%s", log_prefix, self.loglevel)

        self.log.debug("%s kwargs=%s", log_prefix, PrettyLog(kwargs))

        self.collection_version = self.get_internal_collection_version()

        self.remove_repo_dir = remove_repo_dir
        self.test_mode = test_mode

        self.inventory_file = inventory_file
        self.log.debug("%s inventory_file => %s", log_prefix, self.inventory_file)

        self.inventory_base_dir = kwargs.get("inventory_base_dir") or None
        if self.inventory_base_dir is None:
            self.inventory_base_dir = tempfile.mkdtemp(prefix="update_inventory")
            kwargs["inventory_base_dir"] = self.inventory_base_dir

        self.log.info(
            "%s inventory_base_dir => %s", log_prefix, self.inventory_base_dir
        )

        self.git_comment_prefix = kwargs.get("git_comment_prefix", "")
        self.git_comment_body = kwargs.get("git_comment_body", "")
        self.git_user_name = kwargs.get("git_user_name", "ansible")
        self.git_user_email = kwargs.get("git_user_email", "ansible@example.org")
        self.git_user_config = {
            "name": self.git_user_name,
            "email": self.git_user_email,
        }

        self.git = None
        self.git_comment_prefix = None
        self.git_comment_body = None
        self.git_comment_module_stamp = None
        self.git_commit_message = None
        self.git_user_config = None
        self.git_repo_config = git_repo_config

        if self.git_repo_config:
            self.log.debug(
                "%s git_repo_config => %s", log_prefix, PrettyLog(self.git_repo_config)
            )
            self.load_git_repo(**kwargs)

        ###################
        # inventory_parser
        # ref: https://stackoverflow.com/a/72085255/2791368
        # ref: https://stackoverflow.com/questions/71265557/can-i-use-inspect-signature-to-interpret-a-decorators-args-kwargs-as-the
        self.inventory_parser = class_init_wrapper(
            InventoryParser, self.module, inventory_file=self.inventory_file, **kwargs
        )

        self.log.debug("%s finished", log_prefix)

    def get_internal_collection_version(self):
        log_prefix = "%s.get_internal_collection_version():" % self.__class__.__name__
        self.log.debug("%s module_name => %s", log_prefix, self.module_name)

        if "." in self.module_name:
            module_parts = self.module_name.rsplit(".", 1)
            self.log.info("%s module_parts=%s", log_prefix, module_parts)
            module_fqcn = module_parts[0]
        else:
            module_fqcn = self.module_name

        self.log.debug("%s module_fqcn => %s", log_prefix, module_fqcn)

        collection_version = None
        try:
            collection_version = get_collection_version(
                module_fqcn, no_version=None
            )
            self.log.debug("%s collection_version=%s", log_prefix, collection_version)
        except UtilsModuleException as e:
            pass

        return collection_version

    def load_git_repo(self, **kwargs):
        log_prefix = "%s.load_git_repo():" % self.__class__.__name__

        self.log.debug(
            "%s git_repo_config => %s", log_prefix, PrettyLog(self.git_repo_config)
        )

        if "repo_dir" not in self.git_repo_config:
            self.git_repo_config["repo_dir"] = self.inventory_base_dir

        self.git_comment_prefix = kwargs.get("git_comment_prefix", None)
        self.git_comment_body = kwargs.get("git_comment_body", None)

        # self.git_comment_module_stamp = "[%s]: updated inventory file %s" % (self.__class__.__name__)
        self.git_comment_module_stamp = "%s" % self.module_name
        if self.collection_version:
            self.git_comment_module_stamp += "[%s]" % self.collection_version

        self.log.debug(
            "%s git_comment_module_stamp => %s",
            log_prefix,
            self.git_comment_module_stamp,
        )
        self.log.debug(
            "%s git_comment_prefix => %s", log_prefix, self.git_comment_prefix
        )
        self.log.debug("%s git_comment_body => %s", log_prefix, self.git_comment_body)

        self.git_commit_message = self.get_commit_message()
        self.log.debug(
            "%s git_commit_message => %s", log_prefix, self.git_commit_message
        )

        if self.git_repo_config["user_name"] and self.git_repo_config["user_email"]:
            self.git_user_config = {
                "name": self.git_repo_config["user_name"],
                "email": self.git_repo_config["user_email"],
            }

        self.git = Git(self.module, self.git_repo_config)

        if self.git_repo_config.get("repo_url"):
            self.log.debug("%s cloning git repository", log_prefix)
            self.git.clone()
            self.git.pull()

        return

    def get_commit_message(self):

        git_commit_message_default = "%s: updated inventory" % (
            self.git_comment_module_stamp
        )
        git_commit_message = git_commit_message_default

        if self.git_comment_body:
            git_commit_message = "%s: %s" % (
                self.git_comment_module_stamp,
                self.git_comment_body,
            )

        if self.git_comment_prefix:
            git_commit_message = "%s - %s" % (
                self.git_comment_prefix,
                git_commit_message,
            )

        return git_commit_message

    def update_inventory(self, group_list=None, host_list=None, state="merge"):
        log_prefix = "%s.update_inventory():" % self.__class__.__name__
        # self.log.info("%s group => %s", log_prefix, PrettyLog(group))

        result = dict(
            changed=False,
            failed=False,
            backup_files=None,
            inventory_base_dir=self.inventory_base_dir,
        )

        # if group_list is None:
        #     group_list = []
        # if host_list is None:
        #     host_list = []

        self.log.debug("%s module.check_mode => %s", log_prefix, self.module.check_mode)

        if self.module.check_mode:
            result["message"] = "The inventory has been updated successfully"
            return result

        if group_list:
            self.log.debug("%s group_list => %s", log_prefix, PrettyLog(group_list))
            for group in group_list:
                if state in ["merge", "overwrite"]:
                    self.inventory_parser.update_group(group)
                if state == "absent":
                    self.inventory_parser.remove_group(group)

        if host_list:
            self.log.debug("%s host_list => %s", log_prefix, PrettyLog(host_list))
            for host in host_list:
                if state in ["merge", "overwrite"]:
                    self.inventory_parser.update_host(host)
                if state == "absent":
                    self.inventory_parser.remove_host(host)

        self.log.debug("%s saving inventory", log_prefix)

        result.update(self.inventory_parser.save_inventory())

        if self.test_mode:
            result["message"] = "Inventory updated successfully"
            return result

        if self.git_repo_config:
            self.log.info("%s updating git repository", log_prefix)
            result.update(self.update_git_repo())

        self.log.info("%s result => %s", log_prefix, PrettyLog(result))

        return result

    def update_git_repo(self):

        log_prefix = "%s.update_git_repo():" % self.__class__.__name__
        # self.log.info("%s group => %s", log_prefix, PrettyLog(group))
        result = dict(changed=False)

        self.log.info("%s updating git repository", log_prefix)

        changed_files = self.git.status()
        self.log.debug("%s changed_files=%s", log_prefix, changed_files)

        if changed_files:
            # if self.validate_inventory:
            #     validate_result = self.validate_inventory_repo()
            #     result.update(validate_result)

            if self.git_user_config:
                result.update(self.git.set_user_config(self.git_user_config))

            result.update(self.git.pull())
            result.update(self.git.add())
            result.update(self.git.commit(self.git_commit_message))
            result.update(self.git.push())
            result["message"] = "Inventory updated successfully"
            result["changed"] = True
        else:
            result["message"] = "No changes required for inventory"
            result["changed"] = False

        if self.remove_repo_dir:
            try:
                shutil.rmtree(self.inventory_base_dir)
            except OSError as e:
                self.module.fail_json(
                    msg="Failed to remove temp inventory repo dir at %s"
                    % self.inventory_base_dir,
                    details="Error occurred while removing : %s" % to_text(e),
                )
            except Exception as e:
                self.module.fail_json(
                    msg="Exception occurred when attempting to remove temp inventory repo dir at %s"
                    % self.inventory_base_dir,
                    details="Error occurred while removing : %s" % to_text(e),
                )
        else:
            result["inventory_base_dir"] = self.inventory_base_dir

        self.log.info("%s result => %s", log_prefix, PrettyLog(result))

        return result
