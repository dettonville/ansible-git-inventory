"""
Unit tests for update_inventory Ansible module and supporting utilities.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os
import sys
import tempfile
import shutil
import pprint
import yaml

import unittest
from unittest.mock import Mock, patch

from ansible_collections.dettonville.git_inventory.tests.unit.plugins.modules.utils import (
    set_module_args,
    AnsibleExitJson,
    AnsibleFailJson,
    ModuleTestCase,
)

from ansible_collections.dettonville.git_inventory.plugins.modules import (
    update_inventory,
)
from ansible_collections.dettonville.git_inventory.plugins.module_utils.git_inventory_updater import (
    GitInventoryUpdater,
)
from ansible_collections.dettonville.git_inventory.plugins.module_utils.inventory_parser import (
    InventoryParser,
    InventoryParserException
)

# from ansible_collections.dettonville.git_inventory.plugins.module_utils.yaml_parser import (
#     get_yaml_parser,
# )

MODULES_IMPORT_PATH = "ansible_collections.dettonville.git_inventory.plugins.modules"
MODULE_UTILS_IMPORT_PATH = (
    "ansible_collections.dettonville.git_inventory.plugins.module_utils"
)

UTILS_MODULES_IMPORT_PATH = "ansible_collections.dettonville.utils.plugins.modules"
UTILS_MODULE_UTILS_IMPORT_PATH = (
    "ansible_collections.dettonville.utils.plugins.module_utils"
)


def make_absolute(base_path, name):
    return ".".join([base_path, name])


class TestUpdateInventoryModule(ModuleTestCase):
    """Test cases for the update_inventory Ansible module."""

    def setUp(self):
        """Set up test fixtures."""
        super(TestUpdateInventoryModule, self).setUp()
        self.module = update_inventory
        self.test_dir = tempfile.mkdtemp(prefix="test_inventory_repo_")
        self.inventory_base_dir = self.test_dir
        self.inventory_file = "inventory.yml"
        self.inventory_file_path = os.path.join(
            self.inventory_base_dir, self.inventory_file
        )

        # Create a sample inventory file
        self.sample_inventory = """
all:
  hosts:
    host1:
      ansible_host: 192.168.1.10
    host2:
      ansible_host: 192.168.1.11
  children:
    webservers:
      hosts:
        host1:
        host2:
    databases:
      hosts:
        db1:
          ansible_host: 192.168.1.20
"""
        with open(self.inventory_file_path, "w") as f:
            f.write(self.sample_inventory)

    def tearDown(self):
        """Clean up test fixtures."""
        super(TestUpdateInventoryModule, self).tearDown()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch(make_absolute(MODULES_IMPORT_PATH, "update_inventory.AnsibleModule"))
    def test_setup_module_object(self, mock_ansible_module):
        """Test module object setup."""
        self.module.setup_module_object()

        # Verify AnsibleModule was called with correct parameters
        mock_ansible_module.assert_called_once()
        args, kwargs = mock_ansible_module.call_args

        # Check that argument_spec is properly defined
        self.assertIn("argument_spec", kwargs)
        arg_spec = kwargs["argument_spec"]

        # Verify required parameters
        self.assertIn("inventory_file", arg_spec)
        self.assertEqual(arg_spec["inventory_file"]["required"], True)

        # Verify optional parameters
        self.assertIn("yaml_lib_mode", arg_spec)
        self.assertIn("state", arg_spec)
        self.assertIn("vars_state", arg_spec)
        self.assertIn("inventory_repo_url", arg_spec)
        self.assertIn("inventory_repo_branch", arg_spec)
        self.assertIn("inventory_dir", arg_spec)
        self.assertIn("inventory_root_yaml_key", arg_spec)
        self.assertIn("global_groups_file", arg_spec)
        self.assertIn("logging_level", arg_spec)

        # Verify choices
        self.assertEqual(arg_spec["yaml_lib_mode"]["choices"], ["ruamel", "pyyaml"])
        self.assertEqual(arg_spec["state"]["choices"], ["merge", "overwrite", "absent"])
        self.assertEqual(arg_spec["vars_state"]["choices"], ["merge", "overwrite"])
        self.assertEqual(
            arg_spec["logging_level"]["choices"], ["NOTSET", "DEBUG", "INFO", "ERROR"]
        )

        # Verify defaults
        self.assertEqual(arg_spec["yaml_lib_mode"]["default"], "ruamel")
        self.assertEqual(arg_spec["state"]["default"], "merge")
        self.assertEqual(arg_spec["vars_state"]["default"], "merge")
        self.assertEqual(arg_spec["inventory_repo_url"]["default"], None)
        self.assertEqual(arg_spec["inventory_repo_branch"]["default"], "main")
        self.assertEqual(arg_spec["logging_level"]["default"], "INFO")

    @patch(make_absolute(MODULES_IMPORT_PATH, "update_inventory.GitInventoryUpdater"))
    def test_without_required_parameters(self, mock_updater_class):
        """Failure must occur when all parameters are missing"""
        with self.assertRaises(AnsibleFailJson):
            with set_module_args({}):
                self.module.main()

    @patch(make_absolute(MODULES_IMPORT_PATH, "update_inventory.GitInventoryUpdater"))
    def test_successful_inventory_update(self, mock_updater_class):
        """Test successful inventory update."""

        # mock_module.params = {
        module_args = {
            "inventory_base_dir": self.inventory_base_dir,
            "inventory_file": self.inventory_file,
            "state": "merge",
            "host_list": [
                {
                    "host_name": "vmlnx123-q1-s1.example.int",
                    "host_vars": {
                        "provisioning_data": {
                            "jira_id": "INFRA-12345",
                            "infra_group": "automation-engineering",
                        }
                    },
                    "parent_groups": [
                        "vmware_flavor_medium",
                        "ntp_client",
                        "ldap_client",
                        "webserver",
                    ],
                }
            ],
        }

        with set_module_args(module_args):
            # Verify that exit_json was called with success
            # self.assertTrue(mock_module.exit_json.called)
            with self.assertRaises(AnsibleExitJson) as result:
                # Test would call main function here
                self.module.main()

    # @patch('ansible.module_utils.basic.AnsibleModule', side_effect=MockAnsibleModule)
    # @patch(make_absolute(MODULES_IMPORT_PATH, "update_inventory.AnsibleModule"))
    @patch(
        make_absolute(
            MODULE_UTILS_IMPORT_PATH, "git_inventory_updater.GitInventoryUpdater"
        )
    )
    def test_module_basic_add_group(self, mock_updater_class):
        """
        Test adding a new group without Git operations.
        """
        # Define module parameters
        # No Git operations
        # Keep temp dir for inspection if needed during debug
        # Test mode
        module_args = {
            "inventory_file": self.inventory_file,
            "inventory_base_dir": self.inventory_base_dir,
            "global_groups_file": self.inventory_file,
            "group_list": [{"group_name": "new_group", "group_vars": {"key": "value"}}],
            "inventory_repo_url": None,
            "remove_repo_dir": False,
        }
        with self.assertRaises(AnsibleExitJson) as exc:
            with set_module_args(module_args):
                self.module.main()

        result = exc.exception.args[0]
        print("result =>", pprint.pformat(result))
        # Assertions
        self.assertTrue(result["changed"])
        self.assertEqual(result["message"], "Inventory updated successfully")


class TestGitInventoryUpdater(ModuleTestCase):
    """Test cases for the GitInventoryUpdater class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp(prefix="test_inventory_repo_")
        self.inventory_base_dir = self.test_dir
        self.inventory_file = "inventory.yml"
        self.inventory_file_path = os.path.join(
            self.inventory_base_dir, self.inventory_file
        )

        self.git_repo_config = {
            "repo_url": "https://github.com/test/repo.git",
            "repo_branch": "main",
            "user_name": "testuser",
            "user_email": "testuser@example.org",
        }

        # Create mock module
        self.mock_module = Mock()

        # Set the '_name' attribute
        self.mock_module._name = "dettonville.git_inventory.update_inventory"
        self.mock_module.check_mode = False

        self.mock_module.params = {
            "inventory_file": self.inventory_file,
            "remove_repo_dir": False,
            "logging_level": "DEBUG",
        }
        self.mock_module.run_command.return_value = (0, "", "")
        self.mock_module.add_cleanup_file = Mock()
        self.mock_module.fail_json = Mock()

        self.mock_module.run_command = Mock(return_value=(0, "", ""))

        # Create sample inventory
        self.sample_inventory = {
            "all": {
                "hosts": {
                    "host1": {"ansible_host": "192.168.1.10"},
                    "host2": {"ansible_host": "192.168.1.11"},
                },
                "children": {"webservers": {"hosts": {"host1": {}, "host2": {}}}},
            }
        }

        # Write sample inventory to file
        with open(self.inventory_file_path, "w") as f:
            import yaml

            yaml.dump(self.sample_inventory, f)

        self.inventory_updater = GitInventoryUpdater(
            self.mock_module,
            self.inventory_file,
            inventory_base_dir=self.inventory_base_dir,
            remove_repo_dir=False,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_initialization(self):
        """Test GitInventoryUpdater initialization."""
        self.assertEqual(self.inventory_updater.module, self.mock_module)
        self.assertEqual(
            self.inventory_updater.inventory_base_dir, self.inventory_base_dir
        )
        self.assertEqual(self.inventory_updater.inventory_file, self.inventory_file)

    def test_validate_git_repo_success(self):
        """Test successful git repository validation."""
        # Mock successful git command
        self.mock_module.run_command.return_value = (0, "", "")

        result = self.inventory_updater.update_inventory()
        self.assertTrue(result)

    def test_backup_inventory(self):
        """Test inventory backup functionality."""
        inventory_updater = GitInventoryUpdater(
            self.mock_module,
            inventory_file=self.inventory_file,
            inventory_base_dir=self.inventory_base_dir,
            backup=True,
        )

        # Create a backup
        host_list = [{"host_name": "vmlnx123-q1-s1.example.int"}]

        result = inventory_updater.update_inventory(host_list=host_list)
        print("result=%s" % result)
        backup_files = result["backup_files"]
        backup_file = backup_files[0]

        # Verify backup was created
        self.assertTrue(backup_file.endswith("~"))

    @patch(make_absolute(MODULE_UTILS_IMPORT_PATH, "git_inventory_updater.Git"))
    def test_commit_changes(self, mock_git_class):
        """Test git commit functionality."""
        # Mock successful git commands
        # mock_git_module.run_command.return_value = (0, "", "")

        host_list = [{"host_name": "vmlnx123-q1-s1.example.int"}]

        result = self.inventory_updater.update_inventory(host_list=host_list)
        print("result=%s" % result)

        # mock_git_class.return_value.do_something.side_effect = [
        #     (128, "", "fatal: No such remote"),  # remote get-url fails
        # ]

        # # Verify git commands were called
        # expected_calls = [
        #     call(['git', 'clone'], cwd=self.inventory_base_dir),
        #     call(['git', 'status'], cwd=self.inventory_base_dir),
        #     call(['git', 'add', self.inventory_file], cwd=self.inventory_base_dir),
        #     call(['git', 'commit', '-m', 'test'], cwd=self.inventory_base_dir),
        #     call(['git', 'push'], cwd=self.inventory_base_dir),
        # ]
        #
        # self.mock_module.run_command.assert_has_calls(expected_calls)

        # # Verify git operations were called in correct order (no pull for acp)
        # mock_git_instance.status.assert_called_once()
        # # mock_git_instance.set_user_config.assert_called_once()
        # mock_git_instance.pull.assert_not_called()  # Should not be called for acp
        # mock_git_instance.add.assert_called_once()
        # mock_git_instance.commit.assert_called_once_with("test commit")
        # mock_git_instance.push.assert_called_once()

    @patch(make_absolute(MODULE_UTILS_IMPORT_PATH, "git_inventory_updater.Git"))
    def test_validate_git_repo_failure(self, mock_git_class):
        def git_clone_exception():
            raise ValueError("fatal: No such remote")

        mock_git_class.return_value.clone.side_effect = git_clone_exception

        with self.assertRaises(Exception):
            """Test git repository validation failure."""
            inventory_updater = GitInventoryUpdater(
                self.mock_module,
                inventory_file=self.inventory_file,
                inventory_base_dir=self.inventory_base_dir,
                git_repo_config=self.git_repo_config,
                backup=True,
            )

    @patch(make_absolute(MODULE_UTILS_IMPORT_PATH, "git_inventory_updater.Git"))
    def test_add_host_update(self, mock_git_class):
        """Test adding a host to inventory."""

        # Mock successful git commands
        # mock_git_module.run_command.return_value = (0, "", "")

        host_list = [{"host_name": "vmlnx123-q1-s1.example.int"}]

        result = self.inventory_updater.update_inventory(host_list=host_list)
        print("result=%s" % result)

        self.assertTrue(result["changed"])
        self.assertEqual(result["message"], "Inventory updated successfully")
        self.assertTrue(result)

    @patch(make_absolute(MODULE_UTILS_IMPORT_PATH, "git_inventory_updater.Git"))
    def test_remove_host_update(self, mock_git_class):
        """Test removing a host from inventory."""
        host_list = [{"host_name": "host1"}]

        result = self.inventory_updater.update_inventory(
            host_list=host_list, state="absent"
        )
        print("result=%s" % result)

        self.assertTrue(result)

    @patch(make_absolute(MODULE_UTILS_IMPORT_PATH, "git_inventory_updater.Git"))
    def test_update_host_vars(self, mock_git_class):
        """Test updating host variables."""

        host_list = [
            {
                "host_name": "vmlnx123-q1-s1.example.int",
                "host_vars": {
                    "provisioning_data": {
                        "jira_id": "INFRA-12345",
                        "infra_group": "automation-engineering",
                    }
                },
                "parent_groups": ["vmware_flavor_medium", "ntp_client", "ldap_client"],
            }
        ]

        result = self.inventory_updater.update_inventory(host_list=host_list)

        self.assertTrue(result)


class TestInventoryParser(ModuleTestCase):
    """Test cases for the InventoryParser class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.inventory_base_dir = self.test_dir
        self.inventory_file = "inventory.yml"
        self.inventory_file_path = os.path.join(
            self.inventory_base_dir, self.inventory_file
        )
        self.yaml_lib_mode = "ruamel"
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

        # Create mock module
        self.mock_module = Mock()

        # Create sample inventory
        self.sample_inventory = {
            "all": {
                "hosts": {
                    "host1": {"ansible_host": "192.168.1.10"},
                    "host2": {"ansible_host": "192.168.1.11"},
                },
                "children": {
                    "webservers": {"hosts": {"host1": {}, "host2": {}}},
                    "databases": {"hosts": {"db1": {"ansible_host": "192.168.1.20"}}},
                },
            }
        }

        # Write sample inventory to file
        with open(self.inventory_file_path, "w") as f:
            import yaml
            yaml.dump(self.sample_inventory, f)

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_initialization(self):
        """Test InventoryParser initialization."""
        parser = InventoryParser(self.mock_module, self.inventory_base_dir, self.inventory_file)
        self.assertEqual(parser.inventory_file, self.inventory_file)

    def test_parse_inventory_success(self):
        """Test successful inventory parsing."""
        result = InventoryParser(self.mock_module, self.inventory_base_dir, self.inventory_file).get_inventory_root()
        print("result =>", pprint.pformat(result))

        self.assertIsInstance(result, dict)
        self.assertIn("all", result)
        self.assertIn("hosts", result["all"])
        self.assertIn("children", result["all"])

    def test_parse_inventory_file_not_found(self):
        """Test inventory parsing with missing file."""
        non_existent_file = os.path.join(self.test_dir, "missing.yml")
        with self.assertRaises(InventoryParserException):
            parser = InventoryParser(self.mock_module, self.inventory_base_dir, non_existent_file)

    def test_parse_inventory_invalid_yaml(self):
        """Test inventory parsing with invalid YAML."""
        invalid_yaml_file = os.path.join(self.test_dir, "invalid.yml")
        with open(invalid_yaml_file, "w") as f:
            f.write("invalid: yaml: content: [")

        with self.assertRaises(yaml.YAMLError):
            parser = InventoryParser(self.mock_module, self.inventory_base_dir, invalid_yaml_file)

    def test_validate_inventory_success(self):
        """Test successful inventory validation."""
        parser = InventoryParser(self.mock_module, self.inventory_base_dir, self.inventory_file)

        result = parser.validate_inventory_yamllint(strict_mode=True)
        self.assertTrue(result)

    def test_validate_inventory_missing_all_group(self):
        """Test inventory validation with missing 'all' group."""
        invalid_inventory = {"webservers": {"hosts": {"host1": {}}}}
        invalid_file = os.path.join(self.test_dir, "invalid_inventory.yml")

        with open(invalid_file, "w") as f:
            import yaml
            yaml.dump(invalid_inventory, f)

        with self.assertRaises(InventoryParserException):
            parser = InventoryParser(self.mock_module, self.inventory_base_dir, invalid_file)

    def test_get_hosts(self):
        """Test getting all hosts from inventory."""
        parser = InventoryParser(self.mock_module, self.inventory_base_dir, self.inventory_file)

        inventory = parser.get_inventory()
        print("inventory =>", pprint.pformat(inventory))
        hosts = inventory["hosts"]

        self.assertIsInstance(hosts, dict)
        self.assertIn("host1", inventory["hosts"])
        self.assertIn("host2", inventory["hosts"])
        self.assertIn("db1", inventory["children"]["databases"]["hosts"])

    def test_get_groups(self):
        """Test getting all groups from inventory."""
        parser = InventoryParser(self.mock_module, self.inventory_base_dir, self.inventory_file)

        inventory = parser.get_inventory()
        print("inventory =>", pprint.pformat(inventory))
        groups = inventory["children"]

        self.assertIsInstance(groups, dict)
        self.assertIn("webservers", groups)
        self.assertIn("databases", groups)

    def test_get_hosts_in_group(self):
        """Test getting hosts in a specific group."""
        parser = InventoryParser(self.mock_module, self.inventory_base_dir, self.inventory_file)

        inventory = parser.get_inventory()
        print("inventory =>", pprint.pformat(inventory))

        webserver_hosts = inventory["children"]["webservers"]["hosts"]

        self.assertIsInstance(webserver_hosts, dict)
        self.assertIn("host1", webserver_hosts)
        self.assertIn("host2", webserver_hosts)
        self.assertNotIn("db1", webserver_hosts)

    def test_get_host_vars(self):
        """Test getting variables for a specific host."""
        parser = InventoryParser(self.mock_module, self.inventory_base_dir, self.inventory_file)

        inventory = parser.get_inventory()
        print("inventory =>", pprint.pformat(inventory))

        host_vars = inventory["hosts"]["host1"]

        self.assertIsInstance(host_vars, dict)
        self.assertEqual(host_vars.get("ansible_host"), "192.168.1.10")

    def test_get_group_vars(self):
        """Test getting variables for a specific group."""
        # Add group vars to test data
        inventory_with_group_vars = self.sample_inventory.copy()
        inventory_with_group_vars["all"]["children"]["webservers"]["vars"] = {
            "http_port": 80,
            "https_port": 443,
        }

        with open(self.inventory_file_path, "w") as f:
            import yaml
            yaml.dump(inventory_with_group_vars, f)

        parser = InventoryParser(self.mock_module, self.inventory_base_dir, self.inventory_file)

        inventory = parser.get_inventory()
        print("inventory =>", pprint.pformat(inventory))
        group_vars = inventory["children"]["webservers"]["vars"]

        self.assertIsInstance(group_vars, dict)
        self.assertEqual(group_vars.get("http_port"), 80)
        self.assertEqual(group_vars.get("https_port"), 443)


if __name__ == "__main__":
    # Import required modules
    try:
        import yaml
    except ImportError:
        print(
            "PyYAML is required for these tests. Please install it with: pip install PyYAML"
        )
        sys.exit(1)

    # Run tests
    unittest.main(verbosity=2)
