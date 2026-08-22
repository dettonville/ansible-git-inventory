from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type

"""
Module utility class to configure the appropriate YAML parser and settings
to enabled loading and dumping YAML files.

The class supports two yaml libraries (PyYAML and RuamelYaml) that preserving
annotated inventory files.
"""

import logging
from abc import ABC, ABCMeta, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Union

# from ansible.errors import AnsibleError
# from ansible.module_utils.basic import missing_required_lib
# noinspection PyUnresolvedReferences
from ansible_collections.dettonville.git_inventory.plugins.module_utils.errors import (  # noqa: E501
    MissingLibError,
)

# noinspection PyUnresolvedReferences
# from ansible_collections.dettonville.utils.plugins.module_utils.utils
#   import PrettyLog

# ref: https://stackoverflow.com/questions/47382227/python-yaml-update-preserving-order-and-comments
# ref: https://github.com/ansible/ansible/issues/74383#issuecomment-824884558
# ref:
# https://docs.ansible.com/ansible-core/devel/dev_guide/testing/sanity/import.html#import
try:
    # noinspection PyUnresolvedReferences
    from ruamel.yaml import YAML

    # noinspection PyUnresolvedReferences
    from ruamel.yaml.comments import CommentedMap
except ImportError as imp_exc:
    YAML = CommentedMap = None
    YAML_RUAMEL_LIB_IMPORT_ERROR = imp_exc
else:
    YAML_RUAMEL_LIB_IMPORT_ERROR = None

try:
    # noinspection PyPackageRequirements
    import yaml
except ImportError as imp_exc:
    yaml = None
    YAML_IMPORT_ERROR = imp_exc
else:
    YAML_IMPORT_ERROR = None

CONFIG_YAML_DEFAULT = {
    "typ": "rt",
    "allow_duplicate_keys": None,
    "default_style": None,
    "default_flow_style": None,
    "encoding": None,
    "explicit_start": True,
    "explicit_end": False,
    "version": None,
    "tags": None,
    "canonical": None,
    "indent": None,
    "width": None,
    "allow_unicode": None,
    "line_break": None,
    "mapping": None,
    "sequence": None,
    "offset": None,
    "preserve_quotes": None,
}

log = logging.getLogger()

# # Python 3.10+ is required for UnionType support
# # ref: https://github.com/tiangolo/typer/issues/371
# MINIMUM_PYTHON_VERSION_UNION_TYPE_SUPPORT = (3, 10)
#
#
# # Verify if the current Python version is higher than
# # MINIMUM_PYTHON_VERSION_UNION_TYPE_SUPPORT
# def python_version_match_requirement_union_type():
#     return sys.version_info >= MINIMUM_PYTHON_VERSION_UNION_TYPE_SUPPORT


class GitInventoryParserMeta(ABCMeta):
    """Custom metaclass handling potential metaclass conflicts."""

    pass


class GitInventoryParser(ABC, metaclass=GitInventoryParserMeta):
    """Abstract base class for YAML parsers."""

    def __init__(
        self, yaml_lib: str, yaml_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the parser with optional configuration.

        Args:
            yaml_config: Configuration dictionary for YAML parsing options
        """
        self.yaml_lib = yaml_lib
        self.yaml_config = yaml_config or CONFIG_YAML_DEFAULT

    @abstractmethod
    def load(self, yaml_content: Union[str, bytes]) -> Any:
        pass

    @abstractmethod
    def dump(self, data: Any) -> str:
        pass

    @abstractmethod
    def load_from_file(self, file_path: Union[str, Path]) -> Union[dict, list]:
        pass

    @abstractmethod
    def dump_to_file(self, data: Any, file_path: str) -> None:
        pass


# ref:
# https://stackoverflow.com/questions/47382227/python-yaml-update-preserving-order-and-comments
class RuamelYamlParser(GitInventoryParser):
    def __init__(self, yaml_config=None):
        # ref:
        # https://docs.ansible.com/ansible-core/devel/dev_guide/testing/sanity/import.html#import
        if YAML_RUAMEL_LIB_IMPORT_ERROR:
            # Needs: from ansible.module_utils.basic import
            # missing_required_lib
            raise MissingLibError(
                "ruamel.yaml", "python ruamel.yaml library is missing"
            ) from YAML_RUAMEL_LIB_IMPORT_ERROR

        self.yaml = YAML()
        # self.yaml = YAML(typ='rt')
        # self.yaml = YAML(typ='full')
        self.yaml_parser_type = "RuamelYaml"
        super().__init__(
            yaml_lib=self.yaml_parser_type, yaml_config=yaml_config
        )

        # Configure Ruamel.YAML based on provided config
        if "preserve_quotes" in self.yaml_config:
            self.yaml.preserve_quotes = self.yaml_config["preserve_quotes"]
        if "width" in self.yaml_config:
            self.yaml.width = self.yaml_config["width"]
        if "allow_duplicate_keys" in self.yaml_config:
            self.yaml.allow_duplicate_keys = self.yaml_config[
                "allow_duplicate_keys"
            ]
        if "explicit_start" in self.yaml_config:
            self.yaml.explicit_start = self.yaml_config["explicit_start"]
        # if "indent" in self.yaml_config:
        #     self.yaml.indent(mapping=self.yaml_config['indent'],
        #       sequence=self.yaml_config['indent'])

        self.yaml.indent(
            mapping=self.yaml_config.get("mapping", 2),
            sequence=self.yaml_config.get("sequence", 4),
            offset=self.yaml_config.get("offset", 2),
        )

        # https://yaml.readthedocs.io/en/latest/
        # ref: https://stackoverflow.com/questions/51316491/ruamel-yaml-clarification-on-typ-and-pure-true#51318354
        # ref: https://stackoverflow.com/questions/76331049/ruamel-yaml-anchors-with-roundtriploader-roundtripdumper
        # typ can be one of ['rt','safe','unsafe','base']
        if "typ" in self.yaml_config:
            self.yaml.typ = self.yaml_config["typ"]

        # ref: https://stackoverflow.com/questions/44313992/how-to-keep-null-value-in-yaml-file-while-dumping-though-ruamel-yaml # noqa: E501 url size exceeds 120
        # noinspection PyShadowingNames
        def my_represent_none(self, data):
            return self.represent_scalar("tag:yaml.org,2002:null", "null")

        # ref: https://stackoverflow.com/questions/44313992/how-to-keep-null-value-in-yaml-file-while-dumping-though-ruamel-yaml # noqa: E501 url size exceeds 120
        self.yaml.representer.add_representer(type(None), my_represent_none)
        # self.yaml.representer.add_representer(self.my_represent_none)

        # # Default to safe loading
        # self.yaml.default_flow_style = config.get('default_flow_style',
        #   False)

    def __str__(self):
        return "RuamelYamlParser(yaml_config=%s)" % self.yaml_config

    def __getitem__(self, item):
        return self.yaml_config[item]

    def __setitem__(self, key, value):
        self.yaml_config[key] = value

    def load(self, yaml_content: Union[str, bytes]) -> Any:
        """Load YAML content using Ruamel.YAML."""
        try:
            from io import StringIO

            if isinstance(yaml_content, bytes):
                yaml_content = yaml_content.decode("utf-8")
            return self.yaml.load(StringIO(yaml_content))
        except Exception as e:
            raise yaml.YAMLError(f"Ruamel.YAML parsing error: {e}") from e

    def load_from_file(self, file_path: Union[str, Path]) -> Union[dict, list]:
        """Load YAML content from file using Ruamel.YAML."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return self.yaml.load(file)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"YAML file not found: {file_path}") from e
        except Exception as e:
            raise yaml.YAMLError(f"Ruamel.YAML file parsing error: {e}") from e

    # ref: https://pyyaml.org/wiki/PyYAMLDocumentation
    def dump(self, data: Any, stream: Optional[Any] = None) -> Optional[str]:
        """Serialize data to YAML string or write to stream using
        Ruamel.YAML."""
        try:
            if stream is not None:
                return self.yaml.dump(data, stream)
            from io import StringIO

            stream_io = StringIO()
            self.yaml.dump(data, stream_io)
            return stream_io.getvalue()
        except Exception as e:
            raise yaml.YAMLError(
                f"Ruamel.YAML serialization error: {e}"
            ) from e

    def dump_to_file(self, data: Any, file_path: str) -> None:
        """Write data to YAML file using Ruamel.YAML."""
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                self.yaml.dump(data, file)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"YAML file not found: {file_path}") from e
        except Exception as e:
            raise yaml.YAMLError(
                f"Ruamel.YAML file serialization error: {e}"
            ) from e

    ########################################
    # handle commented maps/dictionaries
    # ref: https://stackoverflow.com/questions/40226610/ruamel-yaml-equivalent-of-sort-keys#40227545
    # ref: https://stackoverflow.com/questions/49613901/sort-yaml-file-with-comments
    # ref: https://github.com/maxx27/pyyaml-sort/blob/main/comments_sort.py
    @staticmethod
    def recursive_sort(obj, level=0, reverse_sort=False):
        """Recursively sort dict keys (including CommentedMap) in-place while
        preserving comments and structure as much as possible.

        Uses pop + insert(0) on reverse-sorted keys so that the final order
        is ascending. This approach is more reliable for comment preservation
        than rebuilding comment attributes manually.
        """
        # log_prefix = "recursive_sort(%s):" % obj
        # log_prefix = "recursive_sort(level=%s):" % level

        if isinstance(obj, dict):
            # Process children first
            for key in list(obj.keys()):
                # noinspection PyUnresolvedReferences
                __class__.recursive_sort(
                    obj[key], level=level + 1, reverse_sort=reverse_sort
                )
            # Now sort keys. For CommentedMap use insert to keep comment
            # bindings.
            if isinstance(obj, CommentedMap):
                keys = sorted(
                    list(obj.keys()), key=str, reverse=not reverse_sort
                )
                for key in keys:
                    value = obj.pop(key)
                    obj.insert(0, key, value)
            else:
                # Plain dict: rebuild sorted
                sorted_items = sorted(
                    obj.items(), key=lambda x: str(x[0]), reverse=reverse_sort
                )
                obj.clear()
                obj.update(sorted_items)
            return obj
        if isinstance(obj, list):
            for idx, elem in enumerate(obj):
                # noinspection PyUnresolvedReferences
                obj[idx] = __class__.recursive_sort(
                    elem, level=level + 1, reverse_sort=reverse_sort
                )
        return obj


# ref: https://dave.dkjones.org/posts/2013/pretty-print-log-python/
# ref: https://realpython.com/python-pretty-print/
class PyYamlParser(GitInventoryParser):
    def __init__(self, yaml_config: Optional[Dict[str, Any]] = None):
        # ref:
        # https://docs.ansible.com/ansible-core/devel/dev_guide/testing/sanity/import.html#import
        if YAML_IMPORT_ERROR:
            # Needs: from ansible.module_utils.basic import
            # missing_required_lib
            raise MissingLibError(
                "pyyaml", "python pyyaml library is missing"
            ) from YAML_IMPORT_ERROR

        self.yaml_parser_type = "PyYaml"
        # self.yaml_config = yaml_config or CONFIG_YAML_DEFAULT
        super().__init__(
            yaml_lib=self.yaml_parser_type, yaml_config=yaml_config
        )
        self.yaml = yaml

        self.load_config = {
            "Loader": yaml.FullLoader,
            **self.yaml_config.get("load", {}),
        }
        self.dump_config = {
            "default_flow_style": False,
            "allow_unicode": True,
            **self.yaml_config.get("dump", {}),
        }

        if "preserve_quotes" in self.yaml_config:
            self.yaml.preserve_quotes = self.yaml_config["preserve_quotes"]

        # ref: https://stackoverflow.com/questions/44313992/how-to-keep-null-value-in-yaml-file-while-dumping-though-ruamel-yaml # noqa: E501 url size exceeds 120
        # noinspection PyShadowingNames
        def my_represent_none(self, data):
            return self.represent_scalar("tag:yaml.org,2002:null", "null")

        # ref: https://pyyaml.org/wiki/PyYAMLDocumentation#events
        self.yaml_dumper = yaml.Dumper

        # ref: https://stackoverflow.com/questions/44313992/how-to-keep-null-value-in-yaml-file-while-dumping-though-ruamel-yaml # noqa: E501 url size exceeds 120
        self.yaml_dumper.add_representer(type(None), my_represent_none)

    def __str__(self):
        return "PyYamlParser(yaml_config=%s)" % self.yaml_config

    def __getitem__(self, item):
        return self.yaml_config[item]

    def __setitem__(self, key, value):
        self.yaml_config[key] = value

    def load(self, yaml_content: Union[str, bytes]) -> Any:
        """Load YAML content using PyYAML."""
        try:
            return self.yaml.load(yaml_content, **self.load_config)
        except yaml.YAMLError as e:
            raise self.yaml.YAMLError(f"PyYAML parsing error: {e}") from e

    # def load(self, file_path: str):
    #     # with open(Path(file_path)) as file:
    #     with open(file_path) as file:
    #         try:
    #             # data = self.yaml.full_load(file)
    #             data = self.yaml.full_load(file, Loader=yaml.FullLoader)
    #         except AttributeError:
    #             # ref:
    #             # https://stackoverflow.com/questions/55551191/module-yaml-has-no-attribute-fullloader
    #             data = self.yaml.safe_load(file)
    #     return data

    def load_from_file(self, file_path: Union[str, Path]) -> Union[dict, list]:
        """Load YAML content from file using PyYAML."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return self.yaml.load(file, **self.load_config)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"YAML file not found: {file_path}") from e
        except self.yaml.YAMLError as e:
            raise self.yaml.YAMLError(f"PyYAML file parsing error: {e}") from e

    # ref: https://pyyaml.org/wiki/PyYAMLDocumentation
    def dump(self, data, stream: Optional[Any] = None):
        return self.yaml.dump(
            data,
            stream,
            Dumper=self.yaml_dumper,
            default_style=self.yaml_config.default_style,
            default_flow_style=self.yaml_config.default_flow_style,
            encoding=self.yaml_config.encoding,
            explicit_start=self.yaml_config.explicit_start,
            explicit_end=self.yaml_config.explicit_end,
            version=self.yaml_config.version,
            tags=self.yaml_config.tags,
            canonical=self.yaml_config.canonical,
            indent=self.yaml_config.indent,
            width=self.yaml_config.width,
            allow_unicode=self.yaml_config.allow_unicode,
            line_break=self.yaml_config.line_break,
        )

    def dump_to_file(self, data: Any, file_path: str) -> None:
        """Write data to YAML file using PyYAML."""
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                self.yaml.dump(data, file, **self.dump_config)
        except yaml.YAMLError as e:
            raise self.yaml.YAMLError(
                f"PyYAML file serialization error: {e}"
            ) from e
        except IOError as e:
            raise IOError(f"Error writing to file {file_path}: {e}") from e

    # ref:
    # https://stackoverflow.com/questions/40226610/ruamel-yaml-equivalent-of-sort-keys#40227545
    @staticmethod
    def recursive_sort(obj):
        if isinstance(obj, dict):
            res = dict()
            for k in sorted(obj.keys()):
                # noinspection PyUnresolvedReferences
                res[k] = __class__.recursive_sort(obj[k])
            return res
        if isinstance(obj, list):
            for idx, elem in enumerate(obj):
                # noinspection PyUnresolvedReferences
                obj[idx] = __class__.recursive_sort(elem)
        return obj


def get_yaml_parser(yaml_lib_mode, yaml_config) -> GitInventoryParser:
    yaml_parser = None
    if yaml_lib_mode == "pyyaml":
        yaml_parser = PyYamlParser(yaml_config)
    elif yaml_lib_mode == "ruamel":
        yaml_parser = RuamelYamlParser(yaml_config)
    else:
        raise ValueError(
            f"Unsupported YAML library mode: {yaml_lib_mode}. Use 'pyyaml' "
            f"or 'ruamel'."
        )

    return yaml_parser
