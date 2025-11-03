from __future__ import absolute_import, division, print_function, annotations

__metaclass__ = type

"""

Module utility class to configure the appropriate YAML parser and settings to enabled loading and dumping YAML files.

The class supports two yaml libraries (PyYAML and RuamelYaml) that preserving annotated inventory files.

"""

from collections import OrderedDict
from abc import ABC, ABCMeta, abstractmethod
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass

from pathlib import Path
import logging

# from ansible.errors import AnsibleError
# from ansible.module_utils.basic import missing_required_lib

from ansible_collections.dettonville.git_inventory.plugins.module_utils.errors import (
    MissingLibError,
)

# noinspection PyUnresolvedReferences
# from ansible_collections.dettonville.utils.plugins.module_utils.utils import PrettyLog

# ref: https://stackoverflow.com/questions/47382227/python-yaml-update-preserving-order-and-comments
# ref: https://github.com/ansible/ansible/issues/74383#issuecomment-824884558
# ref:
# https://docs.ansible.com/ansible-core/devel/dev_guide/testing/sanity/import.html#import
try:
    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedMap, CommentedSeq
    from ruamel.yaml.error import CommentMark
    from ruamel.yaml.tokens import CommentToken
    from ruamel.yaml.comments import merge_attrib
except ImportError as imp_exc:
    YAML_RUAMEL_LIB_IMPORT_ERROR = imp_exc
else:
    YAML_RUAMEL_LIB_IMPORT_ERROR = None

try:
    import yaml
except ImportError as imp_exc:
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
# # Verify if the current Python version is higher than MINIMUM_PYTHON_VERSION_UNION_TYPE_SUPPORT
# def python_version_match_requirement_union_type():
#     return sys.version_info >= MINIMUM_PYTHON_VERSION_UNION_TYPE_SUPPORT


@dataclass
class Comments:
    """Helper class for comments.

    It provides possibility to handle comments in the same way
    for map and sequence items. It doesn't depend whether it
    CommentToken or list of CommentToken.
    """

    # solved python 3.9 typeerror issue with addition of `from __future__ import annotations`
    # ref: https://github.com/tiangolo/typer/issues/371
    before: list[CommentToken] | None = None
    inline: list[CommentToken] | None = None
    after: list[CommentToken] | None = None

    # if not python_version_match_requirement_union_type():
    #     # '|' was added in python 3.10, so not available in python 3.9.
    #     # ref: https://github.com/tiangolo/typer/issues/371#issuecomment-1073649190
    #     before: list[CommentToken] | None = None
    #     inline: list[CommentToken] | None = None
    #     after: list[CommentToken] | None = None
    # else:
    #     before: list[CommentToken] | None = None
    #     inline: list[CommentToken] | None = None
    #     after: list[CommentToken] | None = None


class GitInventoryParserMeta(ABCMeta):
    """
    Custom metaclass that handles potential metaclass conflicts
    by inheriting from ABCMeta to ensure proper abstract method handling.
    """


class GitInventoryParser(ABC, metaclass=GitInventoryParserMeta):
    """
    Abstract base class for YAML parsers used in Git inventory management.

    This class defines the interface that all YAML parser implementations
    must follow, ensuring consistent behavior across different YAML libraries.
    """

    def __init__(self, yaml_lib: str, yaml_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the parser with optional configuration.

        Args:
            yaml_config: Configuration dictionary for YAML parsing options
        """
        self.yaml_lib = yaml_lib
        self.yaml_config = yaml_config or CONFIG_YAML_DEFAULT

    @abstractmethod
    def load(self, yaml_content: Union[str, bytes]) -> Any:
        """
        Load and parse YAML content.

        Args:
            yaml_content: YAML string or bytes to parse

        Returns:
            Parsed YAML data structure

        Raises:
            YAMLError: If parsing fails
        """

    @abstractmethod
    def dump(self, data: Any) -> str:
        """
        Serialize data to YAML string.

        Args:
            data: Python data structure to serialize

        Returns:
            YAML string representation

        Raises:
            YAMLError: If serialization fails
        """

    @abstractmethod
    def load_from_file(self, file_path: Union[str, Path]) -> Union[dict, list]:
        """
        Load YAML content from a file.

        Args:
            file_path: Path to the YAML file

        Returns:
            Parsed YAML data structure

        Raises:
            FileNotFoundError: If file doesn't exist
            YAMLError: If parsing fails
        """

    @abstractmethod
    def dump_to_file(self, data: Any, file_path: str) -> None:
        """
        Write data to a YAML file.

        Args:
            data: Python data structure to serialize
            file_path: Path where to write the YAML file

        Raises:
            YAMLError: If serialization fails
            IOError: If file writing fails
        """


# ref:
# https://stackoverflow.com/questions/47382227/python-yaml-update-preserving-order-and-comments
class RuamelYamlParser(GitInventoryParser):

    def __init__(self, yaml_config=None):
        # ref:
        # https://docs.ansible.com/ansible-core/devel/dev_guide/testing/sanity/import.html#import
        if YAML_RUAMEL_LIB_IMPORT_ERROR:
            # Needs: from ansible.module_utils.basic import
            # missing_required_lib
            raise MissingLibError("ruamel.yaml", "python ruamel.yaml library is missing") from YAML_RUAMEL_LIB_IMPORT_ERROR

        self.yaml = YAML()
        # self.yaml = YAML(typ='rt')
        # self.yaml = YAML(typ='full')
        self.yaml_parser_type = "RuamelYaml"
        super().__init__(yaml_lib=self.yaml_parser_type, yaml_config=yaml_config)

        # Configure Ruamel.YAML based on provided config
        if "preserve_quotes" in self.yaml_config:
            self.yaml.preserve_quotes = self.yaml_config["preserve_quotes"]
        if "width" in self.yaml_config:
            self.yaml.width = self.yaml_config["width"]
        if "allow_duplicate_keys" in self.yaml_config:
            self.yaml.allow_duplicate_keys = self.yaml_config["allow_duplicate_keys"]
        if "explicit_start" in self.yaml_config:
            self.yaml.explicit_start = self.yaml_config["explicit_start"]
        # if "indent" in self.yaml_config:
        #     self.yaml.indent(mapping=self.yaml_config['indent'], sequence=self.yaml_config['indent'])

        self.yaml.indent(
            mapping=self.yaml_config["mapping"],
            sequence=self.yaml_config["sequence"],
            offset=self.yaml_config["offset"],
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
        # self.yaml.default_flow_style = config.get('default_flow_style', False)

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
            raise yaml.YAMLError(f"Ruamel.YAML parsing error: {e}")

    def load_from_file(self, file_path: Union[str, Path]) -> Union[dict, list]:
        """Load YAML content from file using Ruamel.YAML."""
        try:
            # with open(file_path, "r", encoding="utf-8") as file:
            with open(file_path) as file:
                return self.yaml.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"YAML file not found: {file_path}")
        except Exception as e:
            raise yaml.YAMLError(f"Ruamel.YAML file parsing error: {e}")

    # def load_from_file(self, file_path: Union[str, Path]) -> Union[dict, list]:
    #     # ref: https://www.programcreek.com/python/example/103799/ruamel.yaml.load
    #     # ref:
    #     # https://stackoverflow.com/questions/36969808/can-i-insert-a-line-into-ruamel-yamls-commentedmap#36970608
    #     with open(file_path) as file:
    #         data = self.yaml.load(file)
    #     return data

    def dump(self, data: Any) -> str:
        """Serialize data to YAML string using Ruamel.YAML."""
        try:
            from io import StringIO

            stream = StringIO()
            self.yaml.dump(data, stream)
            return stream.getvalue()
        except Exception as e:
            raise yaml.YAMLError(f"Ruamel.YAML serialization error: {e}")

    # ref: https://pyyaml.org/wiki/PyYAMLDocumentation
    def dump(self, data, stream):
        return self.yaml.dump(data, stream)

    def dump_to_file(self, data: Any, file_path: str) -> None:
        """Write data to YAML file using Ruamel.YAML."""
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                self.yaml.dump(data, file)
        except Exception as e:
            if "No such file or directory" in str(e):
                raise IOError(f"Error writing to file {file_path}: {e}")
            else:
                raise yaml.YAMLError(f"Ruamel.YAML file serialization error: {e}")

    ########################################
    # handle commented maps/dictionaries
    # ref:
    # https://stackoverflow.com/questions/62953548/how-to-recursively-sort-yaml-with-anchors-using-commentedmap
    @staticmethod
    def recursive_sort_v2(obj: OrderedDict, level=0, reverse_sort=False):
        log_prefix = "recursive_sort(level=%s):" % level
        if isinstance(obj, list):
            for elem in obj:
                __class__.recursive_sort_v2(
                    elem, level=level + 1, reverse_sort=reverse_sort
                )
            return
        if not isinstance(obj, dict):
            return
        merge = getattr(obj, merge_attrib, [None])[0]
        # << not in first position, move it
        if merge is not None and merge[0] != 0:
            setattr(obj, merge_attrib, [(0, merge[1])])

        if isinstance(obj, CommentedMap):
            # _ok -> set of Own Keys, i.e. not merged in keys
            sorted_keys = sorted(obj._ok)
        else:
            sorted_keys = sorted(obj.keys())

        if reverse_sort:
            sorted_keys = reversed(sorted_keys)

        for key in sorted_keys:
            value = obj[key]
            # print('v1', level, key, super(ruamel.yaml.comments.CommentedMap, obj).keys())
            __class__.recursive_sort_v2(
                value, level=level + 1, reverse_sort=reverse_sort
            )
            # print('v2', level, key, super(ruamel.yaml.comments.CommentedMap, obj).keys())
            obj.move_to_end(key)

    ########################################
    # handle commented maps/dictionaries
    # ref: https://stackoverflow.com/questions/40226610/ruamel-yaml-equivalent-of-sort-keys#40227545
    # ref: https://stackoverflow.com/questions/49613901/sort-yaml-file-with-comments
    # ref: https://github.com/maxx27/pyyaml-sort/blob/main/comments_sort.py
    @staticmethod
    def recursive_sort(obj, level=0, reverse_sort=False):
        # log_prefix = "recursive_sort(%s):" % obj
        log_prefix = "recursive_sort(level=%s):" % level

        if isinstance(obj, dict):
            # res = dict()
            if isinstance(obj, CommentedMap):
                res = __class__.map_sort_before(obj, reverse_sort=reverse_sort)

                # for k in obj.keys():
                # _ok -> set of Own Keys, i.e. not merged in keys
                for k in list(obj._ok):
                    res[k] = __class__.recursive_sort(
                        obj[k], level=level + 1, reverse_sort=reverse_sort
                    )
            else:
                res = dict()
                sorted_keys = sorted(list(obj.keys()))
                # sorted_keys = sorted(
                #     list(obj.keys()),
                #     key=lambda x: x,
                # )
                if reverse_sort:
                    sorted_keys = reversed(sorted_keys)

                for k in sorted_keys:
                    res[k] = __class__.recursive_sort(
                        obj[k], level=level + 1, reverse_sort=reverse_sort
                    )

            # if res:
            #     log.debug("%s map_sort_before : res => %s", log_prefix, PrettyLog(res))
            # for k in sorted(obj.keys()):
            #     res[k] = __class__.recursive_sort(obj[k], level=level+1, reverse_sort=reverse_sort)
            return res
        if isinstance(obj, list):
            # if isinstance(obj, CommentedMap):
            #     res = __class__.seq_sort_before(obj)
            # else:
            #     res = obj
            # log.debug("%s seq_sort_before : res => %s", log_prefix, PrettyLog(res))
            # for idx, elem in enumerate(res):
            for idx, elem in enumerate(obj):
                obj[idx] = __class__.recursive_sort(
                    elem, level=level + 1, reverse_sort=reverse_sort
                )
        return obj

    @staticmethod
    def _comment_tokens_to_str(
        comment_tokens: None | CommentToken | list[CommentToken],
    ) -> str | None:
        """Convert CommentToken or list of CommentToken into string.

        Args:
            comments (Any): source for comments.

        Returns:
            str | None: string with joined comments.
        """
        if comment_tokens is None:
            return None

        if isinstance(comment_tokens, CommentToken):
            comment_tokens = [comment_tokens]

        tokens = []
        for token in comment_tokens:
            if token is None:
                continue
            elif isinstance(token, list):
                tokens.extend(token)
            else:
                tokens.append(token)

        comments: list[str] = []
        for token in tokens:
            if not token:
                continue
            # assert token.value
            if "value" not in token.keys():
                raise AssertionError("assert token.value")

            comments.append(token.value)

        return "".join(comments)

    @staticmethod
    def _copy_comment_token(
        token: CommentToken,
        **kwargs,
    ) -> CommentToken:
        return CommentToken(
            value=kwargs["value"] if "value" in kwargs else token.value,
            start_mark=(
                kwargs["start_mark"] if "start_mark" in kwargs else token.start_mark
            ),
            end_mark=kwargs["end_mark"] if "end_mark" in kwargs else token.end_mark,
            column=kwargs["column"] if "column" in kwargs else token.column,
        )

    @staticmethod
    def _merge_comment_tokens(tokens: list[CommentToken]) -> CommentToken:
        # assert len(tokens) > 0
        if len(tokens) == 0:
            raise AssertionError("assert len(tokens) > 0")

        if len(tokens) == 1:
            return tokens[0]

        return __class__._copy_comment_token(
            token=tokens[0],
            value=__class__._comment_tokens_to_str(tokens),
        )

    @staticmethod
    def _get_comment_list(
        comment_tokens: None | CommentToken | list[CommentToken],
    ) -> None | list[CommentToken]:
        """Helper function to get list of CommentToken or None."""
        if comment_tokens is None:
            return None

        if isinstance(comment_tokens, CommentToken):
            comment_tokens = [comment_tokens]

        return comment_tokens

    @staticmethod
    def _get_start_comments(
        comment_tokens: list[CommentToken] | None,
    ) -> Comments:
        """Get beginning comment (`.ca.comment`)."""

        res = Comments()
        if comment_tokens is None:
            return res

        # assert len(comment_tokens) == 2
        # assert comment_tokens[0] is None or isinstance(comment_tokens[0], CommentToken)
        # assert comment_tokens[1] is None or isinstance(comment_tokens[1], list)

        if len(comment_tokens) != 2:
            raise AssertionError("assert len(comment_tokens) == 2")
        if comment_tokens[0] is not None and not isinstance(
            comment_tokens[0], CommentToken
        ):
            raise AssertionError(
                "assert comment_tokens[0] is None or isinstance(comment_tokens[0], CommentToken)"
            )
        if comment_tokens[1] is not None and not isinstance(comment_tokens[1], list):
            raise AssertionError(
                "assert comment_tokens[1] is None or isinstance(comment_tokens[1], list)"
            )

        res.before = __class__._get_comment_list(comment_tokens[0])
        res.inline = __class__._get_comment_list(comment_tokens[1])
        return res

    @staticmethod
    def _get_map_comments(
        comment_tokens: list[CommentToken] | None,
    ) -> Comments:
        """Get comments for map items.

        Comment for current element is splitted into two: current element and after it.
        """

        res = Comments()
        if comment_tokens is None:
            return res

        # assert len(comment_tokens) == 4
        # assert comment_tokens[0] is None
        # assert comment_tokens[2] is None or isinstance(comment_tokens[2], CommentToken)
        # assert comment_tokens[3] is None or isinstance(comment_tokens[3], list)

        if len(comment_tokens) != 4:
            raise AssertionError("assert len(comment_tokens) == 4")
        if comment_tokens[0] is not None:
            raise AssertionError("assert comment_tokens[0] is None")
        if comment_tokens[2] is not None and not isinstance(
            comment_tokens[2], CommentToken
        ):
            raise AssertionError(
                "assert comment_tokens[2] is None or isinstance(comment_tokens[2], CommentToken)"
            )
        if comment_tokens[3] is not None and not isinstance(comment_tokens[3], list):
            raise AssertionError(
                "assert comment_tokens[3] is None or isinstance(comment_tokens[3], list)"
            )

        # "before" for map is in the [1]
        res.before = __class__._get_comment_list(comment_tokens[1])

        # "inline" for map is in the [2]
        s = __class__._comment_tokens_to_str(comment_tokens[2])
        if s is not None:
            if "\n" not in s:
                # no need to split "inline" comment
                res.inline = __class__._get_comment_list(comment_tokens[2])
                return res

            # first line - inline comment
            # second line and others - for next elements
            current_after: list[str | None] = s.split("\n", 1)
            # replace with None if second line is empty
            if len(current_after) > 1 and current_after[1] == "":
                current_after[1] = None

            if current_after[0]:
                res.inline = [
                    __class__._copy_comment_token(
                        token=comment_tokens[2],
                        value=current_after[0],
                    )
                ]
            if current_after[1]:
                # start_mark and columns have new indent
                res.after = [
                    CommentToken(
                        value=current_after[1],
                        start_mark=CommentMark(0),
                        end_mark=comment_tokens[2].end_mark,
                        column=0,
                    )
                ]

        if comment_tokens[3]:
            if res.after is None:
                res.after = []
            res.after.extend(__class__._get_comment_list(comment_tokens[3]))

        return res

    # ref: https://stackoverflow.com/questions/49613901/sort-yaml-file-with-comments
    # ref: https://github.com/maxx27/pyyaml-sort/blob/main/comments_sort.py
    # ref:
    # https://towardsdatascience.com/writing-yaml-files-with-python-a6a7fc6ed6c3
    @staticmethod
    def map_sort_before(obj: CommentedMap, reverse_sort=False) -> CommentedMap:
        """Sort map with comments before a block.

        Args:
            obj (CommentedMap): source object
            reverse_sort (bool): set to True if reverse sort key order preferred (default=True)

        Returns:
            CommentedMap: target object
        """

        # assert isinstance(obj, CommentedMap)
        if not isinstance(obj, CommentedMap):
            raise AssertionError("assert isinstance(obj, CommentedMap)")

        all_comments: dict[Any, Comments] = {}

        sorted_keys = sorted(
            list(obj.keys()),
            key=lambda x: x,
        )
        if reverse_sort:
            sorted_keys = reversed(sorted_keys)

        # Gather comments

        # First comment is handled specially
        comments = __class__._get_start_comments(obj.ca.comment)

        # assert comments.after is None
        if comments.after is not None:
            raise AssertionError("assert comments.after is None")

        prev_after = comments.inline
        # Next lines' comments
        for key in obj.keys():
            comments = __class__._get_map_comments(obj.ca.items.get(key))

            # add "after" comment from previous element, if any
            if prev_after:
                if not comments.before:
                    comments.before = []
                comments.before = prev_after + comments.before
                prev_after = None

            if not any(
                isinstance(obj.get(key), cls) for cls in [CommentedMap, CommentedSeq]
            ):
                # consider "after" comment as "before" only
                # for simple elements
                prev_after = comments.after
                comments.after = None
            all_comments[key] = comments

        if sorted_keys and (prev_after or obj.ca.end):
            last_key = sorted_keys[-1]
            inline = all_comments[last_key].inline
            # Combine inline and after comments
            if inline:
                inline[-1].value += "\n"
                inline += prev_after or []
                inline += __class__._get_comment_list(obj.ca.end) or []
            else:
                inline = prev_after or []
                inline += __class__._get_comment_list(obj.ca.end) or []
                inline[0].value = "\n" + inline[0].value
            all_comments[last_key].inline = inline

        # Create another map and put comments
        obj_sorted = CommentedMap()
        if obj.ca.comment and obj.ca.comment[0] is not None:
            obj_sorted.ca.comment = [obj.ca.comment[0], None]
            # obj_sorted.ca.comment = [
            #     CommentToken(
            #         value=obj.ca.comment[0],
            #         start_mark=CommentMark(0),  # reset line
            #     ),
            #     None,
            # ]
        for key in sorted_keys:
            obj_sorted[key] = obj[key]
            comments = all_comments[key]
            if comments.before:
                c = obj_sorted.ca.items.setdefault(key, [None, [], None, None])
                if c[1] is None:
                    c[1] = []
                c[1].extend(comments.before)
            if comments.inline:
                # assert isinstance(comments.inline, list)
                if not isinstance(comments.inline, list):
                    raise AssertionError("assert isinstance(comments.inline, list)")

                c = obj_sorted.ca.items.setdefault(key, [None, None, None, None])
                # assert c[2] is None
                if c[2] is not None:
                    raise AssertionError("assert c[2] is None")
                c[2] = __class__._merge_comment_tokens(comments.inline)
            if comments.after:
                c = obj_sorted.ca.items.setdefault(key, [None, None, None, []])
                if c[3] is None:
                    c[3] = []
                c[3].extend(comments.after)

        return obj_sorted

    @staticmethod
    def _get_seq_comments(
        comment_tokens: list[CommentToken] | None,
    ) -> Comments:
        """Get comments for seq items.

        Comment for current element is splitted into two: current element and after it.
        """

        res = Comments()
        if comment_tokens is None:
            return res

        # assert len(comment_tokens) == 4
        # assert comment_tokens[0] is not None
        # assert comment_tokens[1] is None
        # assert comment_tokens[2] is None
        # assert comment_tokens[3] is None

        if len(comment_tokens) != 4:
            raise AssertionError("assert len(comment_tokens) == 4")
        if comment_tokens[0] is None:
            raise AssertionError("assert comment_tokens[0] is not None")
        if comment_tokens[1] is not None:
            raise AssertionError("assert comment_tokens[1] is None")
        if comment_tokens[2] is not None:
            raise AssertionError("assert comment_tokens[2] is None")
        if comment_tokens[3] is not None:
            raise AssertionError("assert comment_tokens[3] is None")

        s = __class__._comment_tokens_to_str(comment_tokens[0])
        # If no inline comment for current element
        if s is None:
            return res
        if "\n" not in s:
            # no need to split "inline" comment
            res.inline = __class__._get_comment_list(comment_tokens[2])
            return res

        # first line - inline comment
        # second line and others - for next elements
        current_after: list[str | None] = s.split("\n", 1)
        # replace with None if second line is empty
        if len(current_after) > 1 and current_after[1] == "":
            current_after[1] = None

        # assert isinstance(comment_tokens[0], CommentToken)
        if not isinstance(comment_tokens[0], CommentToken):
            raise AssertionError("assert isinstance(comment_tokens[0], CommentToken)")
        if current_after[0]:
            res.inline = [
                __class__._copy_comment_token(
                    token=comment_tokens[0],
                    value=current_after[0],
                )
            ]
        if current_after[1]:
            # start_mark and columns have new indent
            res.after = [
                CommentToken(
                    value=current_after[1],
                    start_mark=CommentMark(0),
                    end_mark=comment_tokens[0].end_mark,
                    column=0,
                )
            ]

        return res

    @staticmethod
    def sorted_index(iterable, /, *, key=None, reverse=False) -> list[int]:
        """Wrapper for `sorted` function to return indices.

        Mainly uses for `seq_sort_before()` to generate `sorted_indices`.
        """

        # source values  [1, 5, 3, 2]
        # source index   [0, 1, 2, 3]
        # result values  [1, 2, 3, 5]
        # result indices [0, 3, 2, 1] <-- this is result
        return [
            i[0]
            for i in sorted(
                enumerate(iterable),
                key=lambda x: key(x[1]) if key is not None else x[1],
                reverse=reverse,
            )
        ]

    @staticmethod
    def seq_sort_before(obj: CommentedSeq, sorted_indices: list[Any]) -> CommentedSeq:
        """Sort sequence with comments before a block.

        Args:
            obj (CommentedSeq): source object

        Returns:
            CommentedSeq: target object
        """
        # assert isinstance(obj, CommentedSeq)
        if not isinstance(obj, CommentedSeq):
            raise AssertionError("assert isinstance(obj, CommentedSeq)")

        all_comments: dict[int, Comments] = {}

        # Gather comments

        # First comment is handled specially
        comments = __class__._get_start_comments(obj.ca.comment)
        # assert comments.after is None
        if comments.after is not None:
            raise AssertionError("assert comments.after is None")
        prev_after = comments.inline
        # Next lines' comments
        for obj_index in range(len(obj)):
            comments = __class__._get_seq_comments(obj.ca.items.get(obj_index))

            # add "after" comment from previous element, if any
            if prev_after:
                if not comments.before:
                    comments.before = []
                comments.before = prev_after + comments.before

            prev_after = comments.after
            comments.after = None
            all_comments[obj_index] = comments

        if sorted_indices and (prev_after or obj.ca.end):
            last_key = sorted_indices[-1]
            inline = all_comments[last_key].inline
            # Combine inline and after comments
            if inline:
                inline[-1].value += "\n"
                inline += prev_after or []
                inline += __class__._get_comment_list(obj.ca.end) or []
            else:
                inline = prev_after or []
                inline += __class__._get_comment_list(obj.ca.end) or []
                inline[0].value = "\n" + inline[0].value
            all_comments[last_key].inline = inline

        # Create another list and put comments
        obj_sorted = CommentedSeq()
        for sorted_index, obj_index in enumerate(sorted_indices):
            obj_sorted.append(obj[obj_index])
            comments = all_comments[obj_index]
            if comments.before:
                c = obj_sorted.ca.items.setdefault(sorted_index, [None, [], None, None])
                if c[1] is None:
                    c[1] = []
                c[1].extend(comments.before)
            if comments.inline:
                # assert isinstance(comments.inline, list)
                if not isinstance(comments.inline, list):
                    raise AssertionError("assert isinstance(comments.inline, list)")
                c = obj_sorted.ca.items.setdefault(
                    sorted_index, [None, None, None, None]
                )
                # assert c[0] is None
                if c[0] is not None:
                    raise AssertionError("assert c[0] is None")
                c[0] = __class__._merge_comment_tokens(comments.inline)
            # assert comments.after is None
            if comments.after is not None:
                raise AssertionError("assert comments.after is None")

        return obj_sorted

    # # ref:
    # # https://stackoverflow.com/questions/40226610/ruamel-yaml-equivalent-of-sort-keys#40227545
    # @staticmethod
    # def recursive_sort_v1(obj):
    #     CM = ruamel.yaml.comments.CommentedMap
    #     # handle commented maps/dictionaries
    #     # the commented map is the structure ruamel.yaml uses when doing a round-trip (load+dump) and
    #     # round-tripping is designed to keep the keys in the order that they
    #     # were during loading
    #     try:
    #         if isinstance(obj, __class__.CM):
    #             return obj.sort()
    #     except AttributeError:
    #         pass
    #
    #     if isinstance(obj, dict):
    #         res = dict()
    #         for k in sorted(obj.keys()):
    #             res[k] = __class__.recursive_sort(obj[k])
    #         return res
    #     if isinstance(obj, list):
    #         for idx, elem in enumerate(obj):
    #             obj[idx] = __class__.recursive_sort(elem)
    #     return obj


# ref: https://dave.dkjones.org/posts/2013/pretty-print-log-python/
# ref: https://realpython.com/python-pretty-print/
class PyYamlParser(GitInventoryParser):
    def __init__(self, yaml_config: Optional[Dict[str, Any]] = None):
        # ref:
        # https://docs.ansible.com/ansible-core/devel/dev_guide/testing/sanity/import.html#import
        if YAML_IMPORT_ERROR:
            # Needs: from ansible.module_utils.basic import
            # missing_required_lib
            raise MissingLibError("pyyaml", "python pyyaml library is missing") from YAML_IMPORT_ERROR

        self.yaml_parser_type = "PyYaml"
        # self.yaml_config = yaml_config or CONFIG_YAML_DEFAULT
        super().__init__(yaml_lib=self.yaml_parser_type, yaml_config=yaml_config)
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
            raise self.yaml.YAMLError(f"PyYAML parsing error: {e}")

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
        except FileNotFoundError:
            raise FileNotFoundError(f"YAML file not found: {file_path}")
        except self.yaml.YAMLError as e:
            raise self.yaml.YAMLError(f"PyYAML file parsing error: {e}")

    # ref: https://pyyaml.org/wiki/PyYAMLDocumentation
    def dump(self, data, stream):
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
            raise self.yaml.YAMLError(f"PyYAML file serialization error: {e}")
        except IOError as e:
            raise IOError(f"Error writing to file {file_path}: {e}")

    # ref:
    # https://stackoverflow.com/questions/40226610/ruamel-yaml-equivalent-of-sort-keys#40227545
    @staticmethod
    def recursive_sort(obj):
        if isinstance(obj, dict):
            res = dict()
            for k in sorted(obj.keys()):
                res[k] = __class__.recursive_sort(obj[k])
            return res
        if isinstance(obj, list):
            for idx, elem in enumerate(obj):
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
            f"Unsupported YAML library mode: {yaml_lib_mode}. Use 'pyyaml' or 'ruamel'."
        )

    return yaml_parser
