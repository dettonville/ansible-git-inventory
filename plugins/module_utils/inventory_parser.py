from __future__ import absolute_import, division, print_function

__metaclass__ = type

"""

Module utility class to:

1) load the layout / hierarchy of the YAML based inventory into memory as native python dictionary.
2) allows updates to the inventory to add, update, and/or remove group and/or host nodes and respective variables.

This class utilizes the YamlParser instance to add, update, overwrite, and/or remove nodes
to specified YAML file components in the inventory.

"""

import os
import sys
import logging
import tempfile
import traceback
import errno
import copy

# # ref: https://github.com/adrienverge/yamllint/blob/master/tests/test_linter.py
# ref: https://github.com/adrienverge/yamllint/issues/112

try:
    from yamllint.config import YamlLintConfig
    from yamllint import linter as yaml_linter
except ImportError as imp_exc:
    YAMLLINT_IMPORT_ERROR = imp_exc
else:
    YAMLLINT_IMPORT_ERROR = None


from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.six import string_types

# from ansible.module_utils.basic import missing_required_lib

# noinspection PyUnresolvedReferences
from ansible_collections.dettonville.utils.plugins.module_utils.utils import PrettyLog

# noinspection PyUnresolvedReferences
# from ansible_collections.dettonville.utils.plugins.module_utils.deep_merge \
#     import merge as deep_merge, merge_dicts, append_lists, overwrite

# noinspection PyUnresolvedReferences
from ansible_collections.dettonville.git_inventory.plugins.module_utils.yaml_parser import (
    get_yaml_parser,
)

_LOGLEVEL_DEFAULT = "INFO"

_SYMLINK_SUBDIRS_DEFAULT = ["DEV", "PROD", "QA", "SANDBOX"]

_CLASS_DEFAULT_VALUES = {
    "state": "merge",
    "yaml_lib_mode": "ruamel",
    "inventory_dir": None,
    "inventory_root_yaml_key": "all",
    "vars_state": "merge",
    "vars_overwrite_depth": 2,
    "backup": False,
    "use_vars_files": True,
    "create_empty_groupvars_files": True,
    "create_empty_hostvars_files": True,
    "create_parent_groupvar_files": True,
    "always_add_child_group_to_root": False,
    "always_add_host_to_root_hosts": False,
    "enable_groupvar_symlinks_for_child_inventories": True,
    "enforce_global_groups_must_already_exist": True,
    "symlink_subdirs": None,
    "global_groups_file": "inventory.yml",
    "validate_inventory": True,
    "test_mode": False,
    "remove_repo_dir": True,
    "logging_level": _LOGLEVEL_DEFAULT,
}

_YAML_LINT_CONFIG = """
extends: default
locale: en_US.UTF-8
rules:
  comments: disable
  document-start: disable
  empty-lines: disable
  key-duplicates: enable
  key-ordering: enable
  line-length: disable
  new-line-at-end-of-file: disable
  truthy: disable
"""


def append_lists(l1, l2):
    """
    Appends the values in one list on the end of another list
    """
    l1.extend(l2)
    return l1


def merge_dicts_by_depth(d1, d2, action="merge", depth=1, overwrite_depth=2):
    """Recursively merge d2 into d1.

    If an empty dictionary is provided as a d2 value, it will
    completely replace the existing dictionary.

    If action='overwrite' is used, overwrite_depth specifies the depth at which overwrites will begin.

    :param ``dict`` d1: version1 dict
    :param ``dict`` d2: version2 dict to merge/overlay onto dict d1
    :param ``str`` action: The action for the merge ('merge' or 'overwrite').
    :param ``int`` depth: the current depth of the merge
    :param ``int`` overwrite_depth: if action='overwrite' is used, the depth at which overwrites will begin
    :return dictionary:
    """
    log_prefix_asterisks = "*" * depth
    log_prefix = "%s merge_dicts_by_depth(%s, %s, %s):" % (
        log_prefix_asterisks,
        action,
        depth,
        overwrite_depth,
    )
    logging.debug("%s pre-merge d2=%s", log_prefix, PrettyLog(d2))

    # in the case that d2 is set to None
    if not d2:
        if action == "merge" or depth < overwrite_depth:
            logging.debug("%s Return unmodified source dict", log_prefix)
            return d1
        else:  # action == 'overwrite'
            logging.debug("%s Overwrite dict to None", log_prefix)
            d1 = d2
            return d1

    for key, value in d2.items():
        if key in d1:
            if isinstance(value, dict):
                if action == "merge" or depth < overwrite_depth:
                    logging.debug("%s merge dict key=%s", log_prefix, key)
                    d1_merge = merge_dicts_by_depth(
                        d1.get(key, {}), value, action, (depth + 1), overwrite_depth
                    )
                    d1[key] = d1_merge
                else:  # action == 'overwrite'
                    logging.debug("%s overwrite dict key=%s", log_prefix, key)
                    d1[key] = copy.deepcopy(value)
            elif isinstance(d1[key], list) and isinstance(d2[key], list):
                if action == "merge" or depth < overwrite_depth:
                    logging.debug("%s append list key=%s", log_prefix, key)
                    d1_append = append_lists(d1[key], d2[key])
                    d1[key] = d1_append
                else:  # action == 'overwrite'
                    logging.debug("%s overwrite list key=%s", log_prefix, key)
                    d1[key] = copy.deepcopy(value)
            else:
                logging.debug(
                    "%s overwrite key=%s with type=%s", log_prefix, key, type(d2[key])
                )
                d1[key] = copy.deepcopy(value)
        else:
            logging.debug("%s copy new key=%s", log_prefix, key)
            d1[key] = copy.deepcopy(value)

    logging.debug("%s post-merge d1=%s", log_prefix, PrettyLog(d1))
    return d1


def merge_dicts(d1, d2):
    """Recursively merge d2 into d1.

    If an empty dictionary is provided as a d2 value, it will
    completely replace the existing dictionary.

    :param d1: ``dict``
    :param d2: ``dict``
    :return dictionary:
    """
    for key, value in d2.items():
        if isinstance(value, dict):
            d1_merge = merge_dicts(d1.get(key, {}), value)
            d1[key] = d1_merge
        else:
            # d1[key] = d2[key]
            d1[key] = copy.deepcopy(value)
    return d1


# ref:
# https://www.geeksforgeeks.org/python-extract-selective-keys-values-including-nested-keys/#
def search_key_values(input_dict: dict, key: str):
    # print("input_dict=%s" % PrettyLog(input_dict))
    for i, j in input_dict.items():
        if key in input_dict:
            yield j
        if isinstance(j, dict):
            yield from search_key_values(j, key)


class InventoryParserException(Exception):
    def __init__(self, msg: object, **kwargs: object) -> object:
        self.msg = msg
        self.kwargs = kwargs


class InventoryParser:

    def __init__(
        self,
        module,
        inventory_base_dir,
        inventory_file,
        inventory_dir=_CLASS_DEFAULT_VALUES["inventory_dir"],
        yaml_lib_mode=_CLASS_DEFAULT_VALUES["yaml_lib_mode"],
        inventory_root_yaml_key=_CLASS_DEFAULT_VALUES["inventory_root_yaml_key"],
        state=_CLASS_DEFAULT_VALUES["state"],
        global_groups_file=_CLASS_DEFAULT_VALUES["global_groups_file"],
        vars_state=_CLASS_DEFAULT_VALUES["vars_state"],
        vars_overwrite_depth=_CLASS_DEFAULT_VALUES["vars_overwrite_depth"],
        use_vars_files=_CLASS_DEFAULT_VALUES["use_vars_files"],
        create_empty_groupvars_files=_CLASS_DEFAULT_VALUES[
            "create_empty_groupvars_files"
        ],
        create_empty_hostvars_files=_CLASS_DEFAULT_VALUES[
            "create_empty_hostvars_files"
        ],
        create_parent_groupvar_files=_CLASS_DEFAULT_VALUES[
            "create_parent_groupvar_files"
        ],
        always_add_child_group_to_root=_CLASS_DEFAULT_VALUES[
            "always_add_child_group_to_root"
        ],
        always_add_host_to_root_hosts=_CLASS_DEFAULT_VALUES[
            "always_add_host_to_root_hosts"
        ],
        enable_groupvar_symlinks_for_child_inventories=_CLASS_DEFAULT_VALUES[
            "enable_groupvar_symlinks_for_child_inventories"
        ],
        enforce_global_groups_must_already_exist=_CLASS_DEFAULT_VALUES[
            "enforce_global_groups_must_already_exist"
        ],
        symlink_subdirs=_CLASS_DEFAULT_VALUES["symlink_subdirs"],
        backup=_CLASS_DEFAULT_VALUES["backup"],
        validate_inventory=_CLASS_DEFAULT_VALUES["validate_inventory"],
        remove_repo_dir=_CLASS_DEFAULT_VALUES["remove_repo_dir"],
        test_mode=_CLASS_DEFAULT_VALUES["test_mode"],
        logging_level=_CLASS_DEFAULT_VALUES["logging_level"],
    ):

        self.module = module

        log_prefix = "%s.init():" % self.__class__.__name__
        self.loglevel = logging_level
        logging.basicConfig(level=self.loglevel)
        # logging.basicConfig(level=self.loglevel, stream=sys.stdout)
        self.log = logging.getLogger()

        # self.log.info("%s loglevel=%s", log_prefix, self.loglevel)
        self.log.debug("%s loglevel=%s", log_prefix, self.loglevel)

        # ref:
        # https://stackoverflow.com/questions/44388701/how-get-the-sequences-properly-indented-with-ruamel-yaml
        self.yaml_config = {
            "allow_duplicate_keys": False,
            "explicit_start": True,
            "preserve_quotes": True,
            "mapping": 2,
            "sequence": 4,
            "offset": 2,
            "width": 4096,
            "indent": 2,
        }

        self.yaml_lib_mode = yaml_lib_mode
        self.yaml_parser = get_yaml_parser(self.yaml_lib_mode, self.yaml_config)

        self.inventory_file = inventory_file
        self.inventory_base_dir = inventory_base_dir

        self.log.info("%s inventory_file=%s", log_prefix, self.inventory_file)
        self.log.info("%s inventory_base_dir=%s", log_prefix, self.inventory_base_dir)

        # self.inventory_dir = os.path.dirname(self.inventory_file_path)
        if inventory_dir:
            self.inventory_dir = os.path.join(self.inventory_base_dir, inventory_dir)
            self.inventory_file_path = os.path.join(
                self.inventory_base_dir, self.inventory_dir, self.inventory_file
            )
        else:
            self.inventory_file_path = os.path.join(
                self.inventory_base_dir, self.inventory_file
            )
            self.inventory_dir = os.path.dirname(self.inventory_file_path)

        self.inventory_file_dir = os.path.dirname(self.inventory_file_path)
        self.inventory_root_yaml_key = inventory_root_yaml_key
        self.state = state
        self.vars_state = vars_state
        self.vars_overwrite_depth = vars_overwrite_depth
        self.remove_repo_dir = remove_repo_dir
        self.backup = backup
        self.backup_files = []

        self.log.debug(
            "%s inventory_file_path=%s", log_prefix, self.inventory_file_path
        )
        self.log.debug(
            "%s inventory_root_yaml_key=%s",
            log_prefix,
            self.inventory_root_yaml_key,
        )

        self.use_vars_files = use_vars_files
        self.create_empty_groupvars_files = create_empty_groupvars_files
        self.create_empty_hostvars_files = create_empty_hostvars_files
        self.create_parent_groupvar_files = create_parent_groupvar_files
        self.always_add_child_group_to_root = always_add_child_group_to_root
        self.always_add_host_to_root_hosts = always_add_host_to_root_hosts
        self.enable_groupvar_symlinks_for_child_inventories = (
            enable_groupvar_symlinks_for_child_inventories
        )
        self.symlink_subdirs = symlink_subdirs or _SYMLINK_SUBDIRS_DEFAULT

        self.groupvars_dir = os.path.join(self.inventory_dir, "group_vars")
        self.hostvars_dir = os.path.join(self.inventory_dir, "host_vars")

        self.global_groups_file = global_groups_file
        self.global_groups_path = os.path.join(self.inventory_dir, global_groups_file)

        self.enforce_global_groups_must_already_exist = (
            enforce_global_groups_must_already_exist
        )
        if self.global_groups_file == self.inventory_file:
            self.enforce_global_groups_must_already_exist = False

        self.validate_inventory = validate_inventory
        self.test_mode = test_mode

        self.log.debug("%s vars_state => %s", log_prefix, vars_state)
        self.log.debug(
            "%s vars_overwrite_depth => %s", log_prefix, vars_overwrite_depth
        )
        self.log.debug("%s use_vars_files => %s", log_prefix, use_vars_files)

        self.log.debug("%s global_groups_file => %s", log_prefix, global_groups_file)
        self.log.debug(
            "%s create_empty_groupvars_files => %s",
            log_prefix,
            create_empty_groupvars_files,
        )
        self.log.debug(
            "%s create_empty_hostvars_files => %s",
            log_prefix,
            create_empty_hostvars_files,
        )
        self.log.debug(
            "%s create_parent_groupvar_files => %s",
            log_prefix,
            create_parent_groupvar_files,
        )
        self.log.debug(
            "%s always_add_child_group_to_root => %s",
            log_prefix,
            always_add_child_group_to_root,
        )
        self.log.debug(
            "%s always_add_host_to_root_hosts => %s",
            log_prefix,
            always_add_host_to_root_hosts,
        )
        self.log.debug(
            "%s enable_groupvar_symlinks_for_child_inventories => %s",
            log_prefix,
            enable_groupvar_symlinks_for_child_inventories,
        )
        self.log.debug(
            "%s enforce_global_groups_must_already_exist => %s",
            log_prefix,
            enforce_global_groups_must_already_exist,
        )
        self.log.debug("%s symlink_subdirs => %s", log_prefix, symlink_subdirs)
        self.log.debug("%s backup => %s", log_prefix, backup)
        self.log.debug("%s validate_inventory => %s", log_prefix, validate_inventory)
        self.log.debug("%s remove_repo_dir => %s", log_prefix, remove_repo_dir)
        self.log.debug("%s test_mode => %s", log_prefix, test_mode)

        if not os.path.exists(self.inventory_file_path):
            self.log.error(
                "%s file does not exist at self.inventory_file_path=%s",
                log_prefix,
                self.inventory_file_path,
            )
            raise InventoryParserException(
                "%s inventory file %s does not exist"
                % (log_prefix, self.inventory_file_path)
            )

        self.log.debug(
            "%s loading repo inventory file from %s",
            log_prefix,
            self.inventory_file_path,
        )

        self.inventory_root = self.yaml_parser.load_from_file(self.inventory_file_path)
        self.log.debug(
            "%s self.inventory_root=%s",
            log_prefix,
            self.inventory_root,
        )

        if self.inventory_root_yaml_key not in self.inventory_root:
            raise InventoryParserException(
                "%s root key [%s] not found in inventory file %s"
                % (log_prefix, self.inventory_root_yaml_key, self.inventory_file_path)
            )

        self.inventory = self.inventory_root[self.inventory_root_yaml_key]

        if self.enforce_global_groups_must_already_exist:
            self.log.debug(
                "%s loading global groups from %s", log_prefix, self.global_groups_path
            )
            if not os.path.exists(self.global_groups_path):
                self.log.error(
                    "%s file does not exist at global_groups_path=%s",
                    log_prefix,
                    self.global_groups_path,
                )
                raise InventoryParserException(
                    "%s file does not exist at global_groups_path=%s"
                    % (log_prefix, self.global_groups_path)
                )

            # with open(self.global_groups_path) as file:
            #     self.global_groups = self.yaml_parser.load_from_file(file)
            self.global_groups = self.yaml_parser.load_from_file(
                self.global_groups_path
            )

        self.log.debug("%s finished", log_prefix)

    def get_inventory_root(self):
        return self.inventory_root

    def get_inventory(self):
        return self.inventory

    def update_yaml_file(self, filepath, yaml_content):
        filename = os.path.basename(filepath)
        log_prefix = "%s.update_yaml_file(%s):" % (self.__class__.__name__, filename)
        result = dict(changed=False)

        if self.backup:
            backup_file = self.module.backup_local(filepath)
            self.log.debug("%s backup_file=%s", log_prefix, backup_file)
            backup_file_rel_path = backup_file.replace(self.inventory_base_dir, "")
            self.log.debug(
                "%s backup_file_basename=%s", log_prefix, backup_file_rel_path
            )
            self.backup_files.extend([backup_file_rel_path])
            self.log.debug(
                "%s backup_files=%s", log_prefix, PrettyLog(self.backup_files)
            )

        dummy, tmpfile = tempfile.mkstemp()
        self.log.debug("%s tmpfile=%s", log_prefix, tmpfile)

        os.remove(tmpfile)

        try:
            with open(tmpfile, "w") as fd:
                if not yaml_content:
                    fd.write("---\n{}")
                else:
                    # ref:
                    # https://stackoverflow.com/questions/40226610/ruamel-yaml-equivalent-of-sort-keys#40227545
                    if sys.version_info < (3, 7):
                        self.log.warning(
                            "%s recursive_sort() requires python version 3.7+ - current version: %s",
                            log_prefix,
                            sys.version_info,
                        )
                        self.module.warn(
                            "%s recursive_sort() requires python version 3.7+ - current version: %s"
                            % (log_prefix, sys.version_info)
                        )
                        # display.warning('%s: recursive_sort() requires python version 3.7+ - current version: %s' %
                        #                 (log_prefix, sys.version_info))
                    self.yaml_parser.dump(
                        self.yaml_parser.recursive_sort(yaml_content), fd
                    )
                    result["message"] = "Inventory updated successfully"
                    result["changed"] = True
        except IOError as e:
            raise InventoryParserException(
                "%s write temporary file at %s results in IOError => %s"
                % (log_prefix, tmpfile, e)
            )
        except Exception as e:
            raise InventoryParserException(
                "%s write temporary file at %s results in error => %s"
                % (log_prefix, tmpfile, e),
                traceback=traceback.format_exc(),
            )

        try:
            self.module.atomic_move(tmpfile, filepath)
        except IOError as e:
            raise InventoryParserException(
                "%s move temporary file %s to %s results in IOError => %s"
                % (log_prefix, tmpfile, filepath, e)
            )
        except Exception as e:
            raise InventoryParserException(
                "%s move temporary file %s to %s results in error => %s"
                % (log_prefix, tmpfile, filepath, e),
                traceback=traceback.format_exc(),
            )
        finally:
            if os.path.exists(tmpfile):
                os.remove(tmpfile)

        if self.validate_inventory:
            self.validate_inventory_yamllint(filepath=filepath)

        return result

    def validate_inventory_yamllint(self, filepath=None, strict_mode=False) -> bool:
        result = True
        if filepath:
            filename = os.path.basename(filepath)
            log_prefix = "%s.validate_inventory_yamllint(%s):" % (
                self.__class__.__name__,
                filename,
            )
        else:
            log_prefix = "%s.validate_inventory_yamllint():" % self.__class__.__name__
            filepath = self.inventory_base_dir

        self.log.debug("%s started lint validation", log_prefix)

        if YAMLLINT_IMPORT_ERROR:
            if strict_mode:
                raise InventoryParserException("{}: missing required yamllint library".format(log_prefix))
            else:
                self.log.warning(
                    "%s missing yamllint - linting will be skipped", log_prefix
                )
                result = False
            return result

        # yamllint_error = False
        yamllint_conf = YamlLintConfig(_YAML_LINT_CONFIG)

        try:
            # ref: https://github.com/adrienverge/yamllint/blob/master/tests/test_cli.py
            # ref: https://github.com/adrienverge/yamllint/blob/master/tests/test_linter.py
            # ref:
            # https://github.com/ros-tooling/cross_compile/blob/master/test/test_colcon_mixins.py#L37-L54
            self.log.debug("%s yamllint => %s", log_prefix, filepath)
            yaml_lint_gen = yaml_linter.run(filepath, yamllint_conf)
            yaml_lint_errors = list(yaml_lint_gen)
            self.log.debug("%s yaml_lint_errors => %s", log_prefix, yaml_lint_errors)
            if yaml_lint_errors:
                result = True
                if strict_mode:
                    raise InventoryParserException(
                        "%s yamllint errors on path [%s] occurred: %s"
                        % (log_prefix, filepath, to_text(yaml_lint_errors))
                    )

        except SystemExit as yaml_lint_excp:
            # yaml_lint_errors |= bool(e.code)
            raise InventoryParserException(
                "%s yamllint exception on path [%s] occurred: %s "
                % (log_prefix, filepath, to_text(yaml_lint_excp))
            )

        return result

    # def validate_inventory_root(self):
    #     log_prefix = "%s.validate_inventory_root(%s):" % (self.__class__.__name__)
    #     result = dict(
    #         validate_failed=False
    #     )
    #
    #     # needs loader
    #     loader = DataLoader()
    #
    #     # create the inventory, and filter it based on the subset specified (if any)
    #     inventory = InventoryManager(loader=loader, sources=self.inventory_file_path)
    #
    #     # # create the variable manager, which will be shared throughout
    #     # # the code, ensuring a consistent view of global variables
    #     variable_manager = VariableManager(loader=loader, inventory=inventory)
    #
    #     return result

    ##################
    # group update methods
    ##################
    def update_group(self, group):
        group_name = group["group_name"]
        log_prefix = "%s.update_group(%s):" % (self.__class__.__name__, group_name)

        self.log.debug("%s group => %s", log_prefix, PrettyLog(group))

        if self.state == "overwrite":
            self.remove_group_from_node(group)

        if "children" not in self.inventory:
            self.inventory["children"] = {}

        inventory_groups = self.inventory["children"]

        if self.always_add_child_group_to_root or (
            "parent_groups" not in group and "groups" not in group
        ):
            if group_name not in inventory_groups:
                inventory_groups[group_name] = {}

        if self.use_vars_files:
            self.update_groupvars_file(group)
        else:
            self.update_group_vars(group)

        if "children" in group:
            group_children = group["children"]
            for child_name, child_group in group_children.items():
                if "children" not in inventory_groups[group_name]:
                    inventory_groups[group_name]["children"] = {}
                child_inventory_groups = inventory_groups[group_name]["children"]
                if child_name not in child_inventory_groups:
                    child_inventory_groups[child_name] = {}
                merge_dicts(child_inventory_groups[child_name], child_group)

        self.add_group_to_parent_groups(group)

    def update_groupvars_file(self, group):
        group_name = group["group_name"]
        log_prefix = "%s.update_groupvars_file(%s):" % (
            self.__class__.__name__,
            group_name,
        )

        self.log.debug("%s group => %s", log_prefix, PrettyLog(group))

        group_vars = None

        if "group_vars" not in group:
            if not self.create_empty_groupvars_files:
                return
        else:
            group_vars = group["group_vars"]

        groupvars_file = group_name + ".yml"
        self.log.debug("%s groupvars_file => %s", log_prefix, groupvars_file)

        if not os.path.exists(self.groupvars_dir):
            try:
                os.mkdir(self.groupvars_dir)
            except OSError as e:
                # Possibly something else created the dir since the os.path.exists
                # check above. As long as it's a dir, we don't need to error
                # out.
                if not (e.errno == errno.EEXIST and os.path.isdir(self.groupvars_dir)):
                    raise InventoryParserException(
                        "%s mkdir groupvars_dir at %s results in error => %s"
                        % (log_prefix, self.groupvars_dir, e)
                    )

        groupvars_filepath = os.path.join(self.groupvars_dir, groupvars_file)
        self.log.debug("%s groupvars_filepath => %s", log_prefix, groupvars_filepath)

        if not os.path.exists(groupvars_filepath):
            open(groupvars_filepath, "wb").close()

        inventory_groupvars = self.yaml_parser.load_from_file(groupvars_filepath)

        # if inventory_groupvars and self.state == 'merge':
        if bool(inventory_groupvars) and self.state == "merge":
            self.merge_dict_vars(inventory_groupvars, group_vars)
        else:
            inventory_groupvars = group_vars

        self.update_yaml_file(groupvars_filepath, inventory_groupvars)

        # add symbolic link if needed
        # ref: https://stackoverflow.com/questions/9793631/creating-a-relative-symlink-in-python-without-using-os-chdir#13353846
        # self.log.debug("%s self.inventory_file_dir => %s", log_prefix, self.inventory_file_dir)
        # if self.inventory_file_dir != self.inventory_dir:
        #     if self.enable_groupvar_symlinks_for_child_inventories:
        #         self.setup_child_inventory_groupvar_symlinks(groupvars_filepath)
        if self.enable_groupvar_symlinks_for_child_inventories:
            for child_inventory_dir in self.symlink_subdirs:
                child_inventory_path = os.path.join(
                    self.inventory_dir, child_inventory_dir
                )
                if os.path.exists(child_inventory_path):
                    self.log.debug(
                        "%s child_inventory_path => %s",
                        log_prefix,
                        child_inventory_path,
                    )
                    self.setup_child_inventory_groupvar_symlinks(
                        groupvars_filepath, child_inventory_path
                    )

    def setup_child_inventory_groupvar_symlinks(
        self, groupvars_filepath: str, child_inventory_path: str
    ):
        log_prefix = "%s.setup_child_inventory_groupvar_symlinks(%s):" % (
            self.__class__.__name__,
            groupvars_filepath,
        )

        cwd = os.getcwd()
        groupvars_file_dir = os.path.dirname(groupvars_filepath)
        self.log.debug("%s groupvars_file_dir => %s", log_prefix, groupvars_file_dir)

        groupvars_filename = os.path.basename(groupvars_filepath)
        self.log.debug("%s groupvars_filename => %s", log_prefix, groupvars_filename)

        # groupvars_link_dest_dir = os.path.join(self.inventory_file_dir, "group_vars")
        groupvars_link_dest_dir = os.path.join(child_inventory_path, "group_vars")
        self.log.debug(
            "%s groupvars_link_dest_dir => %s", log_prefix, groupvars_link_dest_dir
        )

        groupvars_link_path = os.path.join(groupvars_link_dest_dir, groupvars_filename)
        self.log.debug("%s groupvars_link_path => %s", log_prefix, groupvars_link_path)

        self.log.debug(
            "%s change current directory to groupvars_link_dest_dir => %s",
            log_prefix,
            groupvars_link_dest_dir,
        )
        os.makedirs(groupvars_link_dest_dir, exist_ok=True)
        os.chdir(groupvars_link_dest_dir)

        relative_symlink_path = os.path.relpath(
            groupvars_filepath, groupvars_link_dest_dir
        )
        self.log.debug(
            "%s relative_symlink_path = %s", log_prefix, relative_symlink_path
        )

        if os.path.islink(groupvars_filename):
            os.chdir(cwd)
            return

        if os.path.exists(groupvars_filename):
            self.log.debug("%s remove current file", log_prefix)
            os.remove(groupvars_filename)

        self.log.debug("%s create symbolic link", log_prefix)
        os.symlink(relative_symlink_path, groupvars_filename)
        os.chdir(cwd)

    def remove_groupvars_file(self, group):
        group_name = group["group_name"]
        log_prefix = "%s.remove_groupvars_file(%s):" % (
            self.__class__.__name__,
            group_name,
        )

        self.log.debug("%s group => %s", log_prefix, PrettyLog(group))

        groupvars_file = group_name + ".yml"

        if not os.path.exists(self.groupvars_dir):
            return

        groupvars_filepath = os.path.join(self.groupvars_dir, groupvars_file)

        if os.path.exists(groupvars_filepath):
            os.remove(groupvars_filepath)

    def update_group_vars(self, group):
        group_name = group["group_name"]
        log_prefix = "%s.update_group_vars(%s):" % (self.__class__.__name__, group_name)

        self.log.debug("%s group => %s", log_prefix, PrettyLog(group))

        if "group_vars" not in group:
            return

        inventory_groups = self.inventory["children"]
        if group_name not in inventory_groups:
            inventory_groups[group_name] = {}
        group_vars = group["group_vars"]
        if "vars" in inventory_groups[group_name] and self.state == "merge":
            self.merge_dict_vars(inventory_groups[group_name]["vars"], group_vars)
        else:
            inventory_groups[group_name]["vars"] = group_vars

    def add_group_to_parent_groups(self, group):
        # group_name = group['group_name']
        # log_prefix = "%s.add_group_to_parent_groups(%s):" % (self.__class__.__name__, group_name)
        # if 'groups' not in group:
        #     return

        parent_groups = []
        if "parent_groups" in group:
            parent_groups = group["parent_groups"]
        elif "groups" in group:
            parent_groups = group["groups"]

        if not parent_groups:
            return

        if isinstance(parent_groups, list):
            for parent_group in parent_groups:
                if isinstance(parent_group, string_types):
                    if parent_group:
                        self.add_group_to_parent_group(
                            self.inventory, group, parent_group
                        )
                elif isinstance(parent_groups, dict):
                    for group_name, group_children in parent_groups.items():
                        self.add_group_to_parent_group(
                            self.inventory, group, group_name, group_children
                        )
        elif isinstance(parent_groups, dict):
            for group_name, group_children in parent_groups.items():
                self.add_group_to_parent_group(
                    self.inventory, group, group_name, group_children
                )

    def validate_global_group_exists(self, group_name):
        log_prefix = "%s.validate_global_group_exists(%s):" % (
            self.__class__.__name__,
            group_name,
        )
        self.log.debug(
            "%s check if group [%s] exists in global groups file [%s]",
            log_prefix,
            group_name,
            self.global_groups_file,
        )

        key_value_list = list(search_key_values(self.global_groups, group_name))
        self.log.debug("key_value_list=%s", key_value_list)
        if not key_value_list:
            self.log.error(
                "%s group_name=[%s] not found in %s",
                log_prefix,
                group_name,
                self.global_groups_file,
            )
            raise InventoryParserException(
                "%s group_name=[%s] not found in %s"
                % (log_prefix, group_name, self.global_groups_file)
            )

    def add_group_to_parent_group(
        self, inventory_node, group, parent_group, group_children=None
    ):
        group_name = group["group_name"]
        log_prefix = "%s.add_group_to_parent_group(%s):" % (
            self.__class__.__name__,
            group_name,
        )

        self.log.debug("%s group => %s", log_prefix, PrettyLog(group))

        if self.enforce_global_groups_must_already_exist:
            self.validate_global_group_exists(parent_group)

        if "children" not in inventory_node:
            inventory_node["children"] = {}

        inventory_groups = inventory_node["children"]

        if parent_group not in inventory_groups:
            inventory_groups[parent_group] = {}

        self.log.debug("%s group_children => %s", log_prefix, PrettyLog(group_children))
        if bool(group_children):
            for child_group_name, child_groups in group_children.items():
                self.add_group_to_parent_group(
                    inventory_groups[parent_group],
                    group,
                    child_group_name,
                    child_groups,
                )
        else:
            if "children" not in inventory_groups[parent_group]:
                inventory_groups[parent_group]["children"] = {}
            inventory_groups[parent_group]["children"][group_name] = {}

        if self.use_vars_files and self.create_parent_groupvar_files:
            parent_group = {"group_name": parent_group}
            self.update_groupvars_file(parent_group)

    def remove_group_from_node(self, group, inventory_node=None):
        if inventory_node is None:
            inventory_node = self.inventory

        group_name = group["group_name"]
        log_prefix = "%s.remove_group_from_node(%s):" % (
            self.__class__.__name__,
            group_name,
        )
        self.log.debug("%s group => %s", log_prefix, PrettyLog(group))

        if "children" not in inventory_node:
            return None

        inventory_groups = inventory_node["children"]
        if group_name in inventory_groups:
            self.log.debug("%s removing group", log_prefix)
            inventory_groups.pop(group_name)

        for group_name in inventory_groups.keys():
            self.log.info("%s removing host from group_name=%s", log_prefix, group_name)
            child_inventory_groups = inventory_groups[group_name]
            self.remove_group_from_node(group, inventory_node=child_inventory_groups)

    def remove_group(self, group):
        self.remove_group_from_node(group)
        self.remove_groupvars_file(group)

    ##################
    # host update methods
    ##################
    def update_host(self, host):
        host_name = host["host_name"]
        log_prefix = "%s.update_host(%s):" % (self.__class__.__name__, host_name)

        if self.state == "overwrite":
            self.remove_host_from_node(host)

        if self.always_add_host_to_root_hosts or (
            "parent_groups" not in host and "groups" not in host
        ):
            if "hosts" not in self.inventory:
                self.inventory["hosts"] = {}

            inventory_hosts = self.inventory["hosts"]
            if host_name not in inventory_hosts:
                inventory_hosts[host_name] = {}

        if self.use_vars_files:
            self.update_hostvars_file(host)
        else:
            self.update_host_vars(host)

        self.add_host_to_groups(host)

    def update_hostvars_file(self, host):
        host_name = host["host_name"]
        log_prefix = "%s.update_hostvars_file(%s):" % (
            self.__class__.__name__,
            host_name,
        )

        self.log.debug("%s host => %s", log_prefix, PrettyLog(host))

        host_vars = None

        if "host_vars" not in host:
            if not self.create_empty_hostvars_files:
                return
        else:
            host_vars = host["host_vars"]

        hostvars_file = host_name + ".yml"

        if not os.path.exists(self.hostvars_dir):
            try:
                os.mkdir(self.hostvars_dir)
            except OSError as e:
                # Possibly something else created the dir since the os.path.exists
                # check above. As long as it's a dir, we don't need to error
                # out.
                if not (e.errno == errno.EEXIST and os.path.isdir(self.hostvars_dir)):
                    raise InventoryParserException(
                        "%s create groupvars_dir at %s results in error => %s"
                        % (log_prefix, self.groupvars_dir, e)
                    )

        hostvars_filepath = os.path.join(self.hostvars_dir, hostvars_file)

        if not os.path.exists(hostvars_filepath):
            open(hostvars_filepath, "wb").close()

        inventory_hostvars = self.yaml_parser.load_from_file(hostvars_filepath)

        # if inventory_hostvars and state == 'merge':
        if bool(inventory_hostvars) and self.state == "merge":
            self.merge_dict_vars(inventory_hostvars, host_vars)
        else:
            inventory_hostvars = host_vars

        self.update_yaml_file(hostvars_filepath, inventory_hostvars)

    def remove_hostvars_file(self, host):
        host_name = host["host_name"]
        log_prefix = "%s.remove_hostvars_file(%s):" % (
            self.__class__.__name__,
            host_name,
        )

        self.log.debug("%s host => %s", log_prefix, PrettyLog(host))

        hostvars_file = host_name + ".yml"

        if not os.path.exists(self.hostvars_dir):
            return

        hostvars_filepath = os.path.join(self.hostvars_dir, hostvars_file)

        if os.path.exists(hostvars_filepath):
            os.remove(hostvars_filepath)

    def update_host_vars(self, host):
        host_name = host["host_name"]
        log_prefix = "%s.update_host_vars(%s):" % (self.__class__.__name__, host_name)

        self.log.debug("%s host => %s", log_prefix, PrettyLog(host))

        if "host_vars" not in host:
            return

        inventory_hosts = self.inventory["hosts"]
        if host_name not in inventory_hosts:
            inventory_hosts[host_name] = {}
        host_vars = host["host_vars"]
        # ref:
        # https://www.geeksforgeeks.org/python-check-if-dictionary-is-empty/
        if bool(inventory_hosts[host_name]):
            self.merge_dict_vars(inventory_hosts[host_name], host_vars)
        else:
            inventory_hosts[host_name] = host_vars

    def add_host_to_groups(self, host):
        # host_name = host['host_name']
        # log_prefix = "%s.add_host_to_groups(%s):" % (self.__class__.__name__, host_name)
        # if 'groups' not in host:
        #     return

        parent_groups = []
        if "parent_groups" in host:
            parent_groups = host["parent_groups"]
        elif "groups" in host:
            parent_groups = host["groups"]

        if not parent_groups:
            return

        if isinstance(parent_groups, list):
            for parent_group in parent_groups:
                if isinstance(parent_group, string_types):
                    if parent_group:
                        self.add_host_to_group_children(
                            self.inventory, host, parent_group
                        )
                elif isinstance(parent_groups, dict):
                    for group_name, group_children in parent_groups.items():
                        self.add_host_to_group_children(
                            self.inventory, host, group_name, group_children
                        )
        elif isinstance(parent_groups, dict):
            for group_name, group_children in parent_groups.items():
                self.add_host_to_group_children(
                    self.inventory, host, group_name, group_children
                )

    def add_host_to_group_children(
        self, inventory_node, host, parent_group, group_children=None
    ):
        host_name = host["host_name"]
        # log_prefix = "%s.add_host_to_groups(%s):" % (self.__class__.__name__, host_name)

        if self.enforce_global_groups_must_already_exist:
            self.validate_global_group_exists(parent_group)

        if "children" not in inventory_node:
            inventory_node["children"] = {}

        inventory_groups = inventory_node["children"]

        if parent_group not in inventory_groups:
            inventory_groups[parent_group] = {}

        if bool(group_children):
            for child_group_name, child_groups in group_children.items():
                self.add_host_to_group_children(
                    inventory_groups[parent_group], host, child_group_name, child_groups
                )
        else:
            if "hosts" not in inventory_groups[parent_group]:
                inventory_groups[parent_group]["hosts"] = {}
            inventory_groups[parent_group]["hosts"][host_name] = {}

    def remove_host_from_node(self, host, inventory_node=None):
        if inventory_node is None:
            inventory_node = self.inventory

        host_name = host["host_name"]
        log_prefix = "%s.remove_host_from_node(%s):" % (
            self.__class__.__name__,
            host_name,
        )
        self.log.debug("%s host => %s", log_prefix, PrettyLog(host))

        if "hosts" in inventory_node:
            inventory_hosts = inventory_node["hosts"]

            if host_name in inventory_hosts:
                self.log.debug("%s removing host", log_prefix)
                inventory_hosts.pop(host_name)

        if "children" in inventory_node:
            inventory_groups = inventory_node["children"]

            for group_name in inventory_groups.keys():
                self.log.info(
                    "%s removing host from group_name=%s", log_prefix, group_name
                )
                child_inventory_groups = inventory_groups[group_name]
                self.remove_host_from_node(host, inventory_node=child_inventory_groups)

    def remove_host(self, host):
        self.remove_host_from_node(host)
        self.remove_hostvars_file(host)

    def merge_dict_vars(self, d1, d2):
        return merge_dicts_by_depth(
            d1, d2, action=self.vars_state, overwrite_depth=self.vars_overwrite_depth
        )

    def save_inventory(self):
        log_prefix = "%s.update_git_repo():" % self.__class__.__name__
        self.log.debug("%s saving inventory", log_prefix)
        result = dict(
            changed=False,
            failed=False,
            backup_files=None,
        )

        result.update(
            self.update_yaml_file(self.inventory_file_path, self.inventory_root)
        )
        if self.backup:
            result["backup_files"] = self.backup_files

        return result
