
# Unit Testing

## Running the tests directly

```shell
ansible-test units --python 3.13 update_inventory
ansible-test units --docker -v --python 3.13 update_inventory
ansible-test units --docker -v --python 3.13 update_hosts
```

```shell
## ref: https://github.com/ansible/ansible/issues/27446#issuecomment-318777441
export PYTHONPATH=$PYTHONPATH:/path/to/your/ansible_collections
pytest -r a --color yes path/to/the/test(s) -vvv
```

```shell
## upgrade the collection if necessary
ansible-galaxy collection install --upgrade dettonville.utils
cd ${HOME}/repos/ansible/ansible_collections/dettonville/utils
export PYTHONPATH=${HOME}/repos/ansible
## show logs for failed tests
pytest -s --color yes tests/unit/plugins/modules/test_update_inventory.py
## show logs for all tests (success and failed)
pytest -rP --color yes tests/unit/plugins/modules/test_update_inventory.py
## turn up verbosity
pytest -vvv -s --color yes tests/unit/plugins/modules/test_update_hosts.py
pytest -s --color yes tests/unit/plugins/modules/test_update_inventory.py::TestGitInventoryUpdater::test_update_repo_checkout_failure
pytest -r a --color yes tests/unit/plugins/modules/test_update_inventory.py::TestUpdateInventoryModule::test_successful_inventory_update
pytest -rP --color yes tests/unit/plugins/modules/test_update_inventory.py::TestUpdateInventoryModule::test_successful_inventory_update
pytest --color yes tests/unit/plugins/modules/test_update_inventory.py::TestUpdateInventoryModule::test_setup_module_object
pytest --color yes tests/unit/plugins/modules/test_update_inventory.py::TestGitInventoryUpdater::test_remove_host_update
pytest --color yes tests/unit/plugins/modules/test_update_inventory.py::TestGitInventoryUpdater::test_commit_changes
```

when using the python 'logging' module, need to specify to turn on logging output in addition to -s for generic stdout. Based on Logging within pytest tests:
ref: https://stackoverflow.com/questions/4673373/logging-within-pytest-tests

```shell
pytest --log-cli-level=DEBUG -s --color yes tests/unit/plugins/modules/test_update_inventory.py::TestUpdateInventoryModule::test_successful_inventory_update
pytest --log-cli-level=DEBUG -s --color yes tests/unit/plugins/modules/test_update_inventory.py::TestGitInventoryUpdater::test_validate_git_repo_failure
pytest --log-cli=true -s --color yes tests/unit/plugins/modules/test_update_inventory.py::TestGitInventoryUpdater::test_validate_git_repo_failure
```

To avoid having to add the log-cli option to the pytest command each time, add the following content to the pytest.ini:
```ini
[pytest]
log_cli = 1
log_cli_level = ERROR
log_cli_format = %(message)s

log_file = pytest.log
log_file_level = DEBUG
log_file_format = %(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)
log_file_date_format=%Y-%m-%d %H:%M:%S

```


```shell
ansible-test units --docker -v --python 3.13
```

```shell
pytest -r a -n auto --color yes -p no:cacheprovider \
  --rootdir /Users/ljohnson/repos/ansible/ansible_collections/dettonville/utils \
  --confcutdir /Users/ljohnson/repos/ansible/ansible_collections/dettonville/utils \
  tests/unit/plugins/modules/test_update_inventory.py

pytest -r a -n auto --color yes -p no:cacheprovider \
  -c /Users/ljohnson/.pyenv/versions/3.13.3/lib/python3.13/site-packages/ansible_test/_data/pytest/config/default.ini \
  --junit-xml /Users/ljohnson/repos/ansible/ansible_collections/dettonville/utils/tests/output/junit/python3.13-modules-units.xml \
  --strict-markers \
  --rootdir /Users/ljohnson/repos/ansible/ansible_collections/dettonville/utils \
  --confcutdir /Users/ljohnson/repos/ansible/ansible_collections/dettonville/utils \
  tests/unit/plugins/modules/test_update_inventory.py
```



```shell
cd ${PROJECT_DIR}/tests/unit/plugins/modules

# Run all tests
python -m unittest test_update_inventory.py -v

# Run specific test class
python -m unittest test_update_inventory.TestExportDicts -v

# Run individual test
python -m unittest test_update_inventory.TestExportDictUtils.test_get_headers_and_fields -v
python -m unittest test_update_inventory.TestExportDictUtils.test_get_headers_and_fields_no_headers -v
python -m unittest test_update_inventory.TestExportDictUtils.test_write_csv_file_success -v
```
