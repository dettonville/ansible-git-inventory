"""
Unit tests for update_inventory Ansible module and supporting utilities.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os
import sys
import tempfile
import shutil

import unittest
from unittest.mock import Mock, patch, call


from ansible_collections.dettonville.git_inventory.plugins.modules.update_inventory import (
    main as module_main,
    setup_module_object,
)
from ansible_collections.dettonville.git_inventory.plugins.module_utils.git_inventory_updater import (
    GitInventoryUpdater,
)
from ansible_collections.dettonville.git_inventory.plugins.module_utils.inventory_parser import (
    InventoryParser,
)
# from ansible_collections.dettonville.git_inventory.plugins.module_utils.yaml_parser import (
#     get_yaml_parser,
# )

MODULES_IMPORT_PATH = "ansible_collections.dettonville.git_inventory.plugins.modules"
MODULE_UTILS_IMPORT_PATH = "ansible_collections.dettonville.git_inventory.plugins.module_utils"


def make_absolute(base_path, name):
    return ".".join([base_path, name])


class TestUpdateInventoryModule(unittest.TestCase):
    """Test cases for the update_inventory Ansible module."""

    def setUp(self):
        """Set up test fixtures."""
        # self.mock_module = Mock(spec=AnsibleModule)
        # self.mock_module = MockAnsibleModule()
        self.temp_dir = tempfile.mkdtemp()
        self.inventory_repo_dir = os.path.join(self.temp_dir, 'test_inventory_repo')
        self.inventory_file = "inventory.yml"
        self.inventory_file_path = os.path.join(self.inventory_repo_dir, self.inventory_file)
        os.makedirs(self.inventory_repo_dir)

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
        with open(self.inventory_file_path, 'w') as f:
            f.write(self.sample_inventory)

        self.setup_module_object = setup_module_object
        self.main = module_main

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    @patch(make_absolute(MODULES_IMPORT_PATH, "update_inventory.AnsibleModule"))
    def test_setup_module_object(self, mock_ansible_module):
        """Test module object setup."""
        mock_module = Mock()
        mock_ansible_module.return_value = mock_module

        self.setup_module_object()

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

    @patch(make_absolute(MODULES_IMPORT_PATH, "update_inventory.AnsibleModule"))
    @patch(make_absolute(MODULES_IMPORT_PATH, "update_inventory.GitInventoryUpdater"))
    def test_successful_inventory_update(self, mock_git_class, mock_ansible_module):
        """Test successful inventory update."""
        mock_module = Mock()
        mock_module.params = {
            "inventory_repo_dir": self.inventory_repo_dir,
            "inventory_file": self.inventory_file,
            "host_list": [
                {
                    "host_name": "vmlnx123-q1-s1.example.int",
                    "host_vars": {
                        "provisioning_data": {
                            "jira_id": "INFRA-12345",
                            "infra_group": "automation-engineering"
                        }
                    },
                    "parent_groups": [
                        "vmware_flavor_medium",
                        "ntp_client",
                        "ldap_client",
                        "webserver"
                    ]
                }
            ]
        }
        mock_module.check_mode = False
        mock_ansible_module.return_value = mock_module

        # Test would call main function here
        self.main()

        # Verify that exit_json was called with success
        self.assertTrue(mock_module.exit_json.called)


class TestGitInventoryUpdater(unittest.TestCase):
    """Test cases for the GitInventoryUpdater class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.inventory_repo_dir = os.path.join(self.temp_dir, 'test_inventory_repo')
        self.inventory_file = 'inventory.yml'
        self.inventory_file_path = os.path.join(self.inventory_repo_dir, self.inventory_file)

        self.git_repo_config = {
            "repo_url": "https://github.com/test/repo.git",
            "repo_branch": "main",
            "user_name": "testuser",
            "user_email": "testuser@example.org",
        }

        # Create mock module
        self.mock_module = Mock()
        self.mock_module.params = {
            "inventory_file": self.inventory_file,
            "remove_repo_dir": False,
            "logging_level": "DEBUG"
        }
        self.mock_module.run_command.return_value = (0, "", "")
        self.mock_module.add_cleanup_file = Mock()
        self.mock_module.fail_json = Mock()

        self.mock_module.run_command = Mock(return_value=(0, "", ""))

        # Create sample inventory
        self.sample_inventory = {
            'all': {
                'hosts': {
                    'host1': {'ansible_host': '192.168.1.10'},
                    'host2': {'ansible_host': '192.168.1.11'}
                },
                'children': {
                    'webservers': {
                        'hosts': {
                            'host1': {},
                            'host2': {}
                        }
                    }
                }
            }
        }

        # Write sample inventory to file
        with open(self.inventory_file_path, 'w') as f:
            import yaml
            yaml.dump(self.sample_inventory, f)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test GitInventoryUpdater initialization."""
        updater = GitInventoryUpdater(self.mock_module)
        self.assertEqual(updater.module, self.mock_module)
        self.assertEqual(updater.repo_path, self.repo_path)
        self.assertEqual(updater.inventory_file, self.inventory_file)

    def test_validate_git_repo_success(self):
        """Test successful git repository validation."""
        updater = GitInventoryUpdater(self.mock_module)

        # Mock successful git command
        self.mock_module.run_command.return_value = (0, "", "")

        result = updater.validate_git_repo()
        self.assertTrue(result)
        self.mock_module.run_command.assert_called_with(['git', 'rev-parse', '--git-dir'],
                                                        cwd=self.repo_path)

    def test_validate_git_repo_failure(self):
        """Test git repository validation failure."""
        updater = GitInventoryUpdater(self.mock_module)

        # Mock failed git command
        self.mock_module.run_command.return_value = (1, "", "Not a git repository")

        result = updater.validate_git_repo()
        self.assertFalse(result)

    def test_backup_inventory(self):
        """Test inventory backup functionality."""
        updater = GitInventoryUpdater(self.mock_module)

        # Create a backup
        backup_file = updater.backup_inventory()

        # Verify backup was created
        self.assertTrue(os.path.exists(backup_file))
        self.assertTrue(backup_file.endswith('.bak'))

        # Verify backup content matches original
        with open(backup_file, 'r') as f:
            backup_content = f.read()
        with open(self.inventory_file, 'r') as f:
            original_content = f.read()

        self.assertEqual(backup_content, original_content)

    def test_commit_changes(self):
        """Test git commit functionality."""
        updater = GitInventoryUpdater(self.mock_module)

        # Mock successful git commands
        self.mock_module.run_command.return_value = (0, "", "")

        commit_message = "Test commit"
        updater.commit_changes(commit_message)

        # Verify git commands were called
        expected_calls = [
            call(['git', 'add', self.inventory_file], cwd=self.repo_path),
            call(['git', 'commit', '-m', commit_message], cwd=self.repo_path)
        ]

        self.mock_module.run_command.assert_has_calls(expected_calls)

    @patch(make_absolute(MODULES_IMPORT_PATH, "update_inventory.GitInventoryParser"))
    def test_add_host_update(self):
        """Test adding a host to inventory."""
        updater = GitInventoryUpdater(self.mock_module)

        updates = [
            {
                'action': 'add_host',
                'host': 'new_host',
                'group': 'webservers',
                'vars': {'ansible_host': '192.168.1.100'}
            }
        ]

        # Mock file operations
        result = updater.update_inventory(updates)

        self.assertTrue(result)

    @patch(make_absolute(MODULES_IMPORT_PATH, "update_inventory.GitInventoryParser"))
    def test_remove_host_update(self):
        """Test removing a host from inventory."""
        updater = GitInventoryUpdater(self.mock_module)

        updates = [
            {
                'action': 'remove_host',
                'host': 'host1',
                'group': 'webservers'
            }
        ]

        # Mock file operations
        result = updater.update_inventory(updates)

        self.assertTrue(result)

    @patch(make_absolute(MODULES_IMPORT_PATH, "update_inventory.GitInventoryParser"))
    def test_update_host_vars(self):
        """Test updating host variables."""
        updater = GitInventoryUpdater(self.mock_module)

        updates = [
            {
                'action': 'update_host_vars',
                'host': 'host1',
                'vars': {'ansible_host': '192.168.1.50', 'new_var': 'value'}
            }
        ]

        result = updater.update_inventory(updates)

        self.assertTrue(result)


class TestInventoryParser(unittest.TestCase):
    """Test cases for the InventoryParser class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.inventory_file = os.path.join(self.temp_dir, 'inventory.yml')
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

        # Create sample inventory
        self.sample_inventory = {
            'all': {
                'hosts': {
                    'host1': {'ansible_host': '192.168.1.10'},
                    'host2': {'ansible_host': '192.168.1.11'}
                },
                'children': {
                    'webservers': {
                        'hosts': {
                            'host1': {},
                            'host2': {}
                        }
                    },
                    'databases': {
                        'hosts': {
                            'db1': {'ansible_host': '192.168.1.20'}
                        }
                    }
                }
            }
        }

        # Write sample inventory to file
        with open(self.inventory_file, 'w') as f:
            import yaml
            yaml.dump(self.sample_inventory, f)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test InventoryParser initialization."""
        parser = InventoryParser(self.inventory_file)
        self.assertEqual(parser.inventory_file, self.inventory_file)

    def test_parse_inventory_success(self):
        """Test successful inventory parsing."""
        result = InventoryParser(self.inventory_file).get_inventory()

        self.assertIsInstance(result, dict)
        self.assertIn('all', result)
        self.assertIn('hosts', result['all'])
        self.assertIn('children', result['all'])

    def test_parse_inventory_file_not_found(self):
        """Test inventory parsing with missing file."""
        non_existent_file = os.path.join(self.temp_dir, 'missing.yml')
        parser = InventoryParser(non_existent_file)

        with self.assertRaises(FileNotFoundError):
            parser.parse_inventory()

    def test_parse_inventory_invalid_yaml(self):
        """Test inventory parsing with invalid YAML."""
        invalid_yaml_file = os.path.join(self.temp_dir, 'invalid.yml')
        with open(invalid_yaml_file, 'w') as f:
            f.write("invalid: yaml: content: [")

        parser = InventoryParser(invalid_yaml_file)

        with self.assertRaises(yaml.YAMLError):
            parser.parse_inventory()

    def test_validate_inventory_success(self):
        """Test successful inventory validation."""
        parser = InventoryParser(self.inventory_file)

        result = parser.validate_inventory()
        self.assertTrue(result)

    def test_validate_inventory_missing_all_group(self):
        """Test inventory validation with missing 'all' group."""
        invalid_inventory = {'webservers': {'hosts': {'host1': {}}}}
        invalid_file = os.path.join(self.temp_dir, 'invalid_inventory.yml')

        with open(invalid_file, 'w') as f:
            import yaml
            yaml.dump(invalid_inventory, f)

        parser = InventoryParser(invalid_file)

        result = parser.validate_inventory()
        self.assertFalse(result)

    def test_get_hosts(self):
        """Test getting all hosts from inventory."""
        parser = InventoryParser(self.inventory_file)

        hosts = parser.get_hosts()

        self.assertIsInstance(hosts, list)
        self.assertIn('host1', hosts)
        self.assertIn('host2', hosts)
        self.assertIn('db1', hosts)

    def test_get_groups(self):
        """Test getting all groups from inventory."""
        parser = InventoryParser(self.inventory_file)

        groups = parser.get_groups()

        self.assertIsInstance(groups, list)
        self.assertIn('all', groups)
        self.assertIn('webservers', groups)
        self.assertIn('databases', groups)

    def test_get_hosts_in_group(self):
        """Test getting hosts in a specific group."""
        parser = InventoryParser(self.inventory_file)

        webserver_hosts = parser.get_hosts_in_group('webservers')

        self.assertIsInstance(webserver_hosts, list)
        self.assertIn('host1', webserver_hosts)
        self.assertIn('host2', webserver_hosts)
        self.assertNotIn('db1', webserver_hosts)

    def test_get_host_vars(self):
        """Test getting variables for a specific host."""
        parser = InventoryParser(self.inventory_file)

        host_vars = parser.get_host_vars('host1')

        self.assertIsInstance(host_vars, dict)
        self.assertEqual(host_vars.get('ansible_host'), '192.168.1.10')

    def test_get_group_vars(self):
        """Test getting variables for a specific group."""
        parser = InventoryParser(self.inventory_file)

        # Add group vars to test data
        inventory_with_group_vars = self.sample_inventory.copy()
        inventory_with_group_vars['all']['children']['webservers']['vars'] = {
            'http_port': 80,
            'https_port': 443
        }

        with open(self.inventory_file, 'w') as f:
            import yaml
            yaml.dump(inventory_with_group_vars, f)

        group_vars = parser.get_group_vars('webservers')

        self.assertIsInstance(group_vars, dict)
        self.assertEqual(group_vars.get('http_port'), 80)
        self.assertEqual(group_vars.get('https_port'), 443)


if __name__ == '__main__':
    # Import required modules
    try:
        import yaml
    except ImportError:
        print("PyYAML is required for these tests. Please install it with: pip install PyYAML")
        sys.exit(1)

    # Run tests
    unittest.main(verbosity=2)
