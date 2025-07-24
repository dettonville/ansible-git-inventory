
# Integration Tests

## Setup development env

## Run Tests Locally

## Check test inventory

### Check correct hosts appear in the test groups 

```shell
ansible-inventory -i _test_inventory/ --graph --yaml testgroup_app123_platforms
ansible-inventory -i _test_inventory/ --graph --yaml test_app123_platform_lnx_managed_local_dmz
ansible-inventory -i _test_inventory/ --graph --yaml dcc_app123_platform_lnx_managed_local_dmz
ansible-inventory -i _test_inventory/ --graph --yaml dmz
```

### Check the host variable values are correctly set  

Variable value/state query based on group:

```shell
$ ansible -i _test_inventory/ -m debug -a var=group_names dmz
$ ansible -i _test_inventory/ -m debug -a var=app123_platform_accounts__platform_type dcc_app123_platform_lnx_nondomain_dmz
test1s1.qa.example.org | SUCCESS => {
    "app123_platform_accounts__platform_type": "nondomain_dmz"
}
test2s1.qa.example.org | SUCCESS => {
    "app123_platform_accounts__platform_type": "nondomain_dmz"
}

```

Query intersecting groups:
```shell
$ ansible -i _test_inventory/ -m debug -a var=group_names dmz:\&lnx_all
$ ansible -i _test_inventory/ -m debug -a var=group_names dmz:\&testgroup_lnx
$ ansible -i _test_inventory/ -m debug -a var=group_names dmz:\&testgroup_lnx:\&ntp_network
```

Query vaulted variable

```shell
$ PROJECT_DIR="$( git rev-parse --show-toplevel )"
$ cd tests
$ ansible -e @vars/vault.yml --vault-password-file ${PROJECT_DIR}/.vault_pass -i _test_inventory/ -m debug -a var=vault__ldap_readonly_password testgroup_lnx
```

```shell
$ PROJECT_DIR="$( git rev-parse --show-toplevel )"
$ cd collections/ansible_collections/dettonville/utils/tests/integration/targets
$ ansible -e @../integration_config.vault.yml --vault-password-file ${PROJECT_DIR}/.vault_pass -i _test_inventory/ -m debug -a var=ansible_user app_cdata_sync_sandbox
$ ansible -e @../integration_config.vault.yml --vault-password-file ${PROJECT_DIR}/.vault_pass -i _test_inventory/ -m debug -a var=ansible_user app_tableau
```


Query with vault and vars files variables (e.g., `./test-vars.yml`) 

```shell
$ PROJECT_DIR="$( git rev-parse --show-toplevel )"
$ cd collections/ansible_collections/dettonville/utils/tests/integration/targets
$ ansible -e @../integration_config.vault.yml -e @test-vars.yml \
    --vault-password-file \
    ${PROJECT_DIR}/.vault_pass \
    -i _test_inventory/ \
    -m debug \
    -a var=test_component_app123_base_url \
    localhost
$ ansible -e @test-vars.yml -e @../integration_config.vault.yml --vault-password-file ${PROJECT_DIR}/.vault_pass -i _test_inventory/ -m debug -a var=vault_platform test1s4.qa.example.org
$ ansible -e @test-vars.yml -e @../integration_config.vault.yml --vault-password-file ${PROJECT_DIR}/.vault_pass -i _test_inventory/ -m debug -a var=ansible_user app_cdata_sync_sandbox
$ ansible -e @test-vars.yml -e @../integration_config.vault.yml --vault-password-file ${PROJECT_DIR}/.vault_pass -i _test_inventory/ -m debug -a var=ansible_user app_tableau
```

```shell
$ PROJECT_DIR="$( git rev-parse --show-toplevel )"
$ cd tests
$ ansible -e @test-vars.yml -e @vars/vault.yml --vault-password-file ${PROJECT_DIR}/.vault_pass -i _test_inventory/ -m debug -a var=vault__ldap_readonly_password testgroup_lnx
```


```shell
$ ansible -i _test_inventory/ -m debug -a \
    var=ansible_connection,ansible_port,ansible_winrm_scheme,ansible_winrm_transport \
    dc9.example.int
$ ansible -i _test_inventory/ -m debug -a var=app123_platform_accounts__platform_type testgroup_app123_123
winansd3s1.example.int | SUCCESS => {
    "app123_platform_accounts__platform_type": "managed_domain_vdi"
}
winansd3s4.example.int | SUCCESS => {
    "app123_platform_accounts__platform_type": "managed_domain_vdi"
}

```


### Run module tests

```shell
$ PROJECT_DIR="$( git rev-parse --show-toplevel )"
$ cd collections/ansible_collections/dettonville/git_inventory/tests/integration/targets
## view the existing test cases
$ find -L test_component/vars/update_inventory -name "test_*.yml" | sort
$ runme.sh -v -t update_inventory
## OR
$ run-module-tests.sh -v -t update_inventory"
```

### Run specific test case

```shell
$ runme.sh -v -t update_inventory --extra-vars \'{\"test_case_id_list\": [\"group01\"]}\'
## OR
$ run-module-tests.sh -t update_inventory --extra-vars \'{\"test_case_id_list\": [\"group01\"]}\'
```

#### Run specific set of test cases

```shell
$ run-module-tests.sh -v -t update_inventory --extra-vars \'{\"test_case_id_list\": [\"group01\",\"host01\"]}\'
```

#### Run test cases with regex pattern

The following will run all test cases with pattern test_*01*.yml.
This will effectively result in running just the first case for each test case group/category.

```shell
$ run-module-tests.sh -t update_inventory --extra-vars \'{\"test_case_id_list\": [\"host01\"]}\'
## runs all test cases beginning with 'group'
$ run-module-tests.sh -v -t update_inventory --extra-vars \'{\"test_case_id_list\": [\"group\"]}\'
## runs all test cases beginning with 'combined'
$ run-module-tests.sh -v -t update_inventory --extra-vars \'{\"test_case_id_list\": [\"combined\"]}\'
## runs test cases 'group14' and 'group15'
$ run-module-tests.sh -v -t update_inventory --extra-vars \'{\"test_case_id_list\": [\"group1[45]\"]}\'
## runs test cases from 'host10' to 'host15'
$ run-module-tests.sh -v -t update_inventory --extra-vars \'{\"test_case_id_list\": [\"host1[0-5]\"]}\'
## runs test cases from 'host10' to 'host29'
$ run-module-tests.sh -v -t update_inventory --extra-vars \'{\"test_case_id_list\": [\"host[12][0-9]\"]}\'
```

#### Run test cases for specified test case category/group

The following will run all test cases with pattern test_*combined*.yml.
This will effectively result in running just the first case for each test case group/category.

```shell
$ run-module-tests.sh -v -t update_inventory --extra-vars \'{\"test_case_id_list\": [\"combined*\"]}\'
```

### Run pytest wrapper

The pytest wrapper method uses the ['pytest-shell'](https://pytest-shell-utilities.readthedocs.io/en/latest/index.html#usage) plugin to launch the `run-module-tests.sh` script.

Using the pytest wrapper has the benefit of generating the test results in a junit format for pipeline utilization. 

```shell
## To list all the module test cases: 
$ run-pytest.sh -l

## To run all the module test cases for the `update_inventory` plugin: 
$ run-pytest.sh update_inventory

## To run the module test for the `update_inventory` plugin and for only test case 'host01' 
$ run-pytest.sh update_inventory-host01

```

#### Reset test data

```shell
$ reset-test-data.sh
```


## Debugging test module

```shell
$ cd ${HOME}/.ansible/tmp/

## find last 10 update_hosts module execs sorted order
## use gfind if using MacOS brew installed gnu utils 
$ find . -maxdepth 2 -name "*.py" -type f -printf "\n%TY-%Tm-%Td %AT %p" |sort -nk1 -nk2 | grep update_hosts | tail -10
```

### debug update_hosts
```shell
## find last update_hosts module exec
$ find .  -maxdepth 2 -name "*.py" -type f -printf "\n%TY-%Tm-%Td %AT %p" |sort -nk1 | grep update_hosts | tail -1
## cd into last module exec debug dir
$ cd $(dirname $(find . -maxdepth 2 -name "*.py" -type f -printf "\n%TY-%Tm-%Td %AT %p" | sort -nk1 | grep update_groups | tail -1 | cut -d' ' -f3))
$ ./AnsiballZ_update_hosts.py explode
$ ./AnsiballZ_update_hosts.py execute | jq
```

### debug update_groups.py
```shell
## cd into last module exec debug dir
$ cd $(dirname $(find . -maxdepth 2 -name "*.py" -type f -printf "\n%TY-%Tm-%Td %AT %p" | sort -nk1 | grep update_inventory.py | tail -1 | cut -d' ' -f3))
$ ./AnsiballZ_update_groups.py explode
$ export ANSIBLE_DEBUG=1
$ ANSIBLE_KEEP_REMOTE_FILES=1
# Clear Python cache and force fresh module loading
$ export ANSIBLE_PIPELINING=false
$ export PYTHONDONTWRITEBYTECODE=1
$ ./AnsiballZ_update_groups.py execute | jq
## if wanting to capture the log for reference
$ ./AnsiballZ_update_hosts.py execute 2>&1 | tee test-case.log 
```

Define function to perform regular/repetitive debug tasks
E.g., in ~/.bash_functions or ~/.bashrc:
```shell
function explode_ansible_test() {
  export ANSIBLE_DEBUG=1 && \
  recent=$(find . -name AnsiballZ_\*.py | head -n1) && \
  ${recent} explode && \
  cat debug_dir/args | jq '.ANSIBLE_MODULE_ARGS.logging_level = "DEBUG"' > debug_dir/args.json && \
  cp debug_dir/args.json debug_dir/args && \
  cp debug_dir/args.json debug_dir/args.orig.json
}
```

Then use as follows:
```shell
## Find module used in 2nd to last step
$ ls -Fla ../$(ls -Fla ../ | tail -2 | head -1 | cut -d':' -f2 | cut -d' ' -f2)
$ cd $(ls -Fla ../ | tail -2 | head -1 | cut -d':' -f2 | cut -d' ' -f2)
$ export ANSIBLE_DEBUG=1
## perform debug_dir steps 
$ cat debug_dir/args.json | jq '.ANSIBLE_MODULE_ARGS += { "remove_repo_dir": false, "test_mode": true }' > debug_dir/args
$ explode_ansible_test
```

The function will perform the explode and json formatting:

```shell
$ cd $(dirname $(find . -maxdepth 2 -name "*.py" -type f -printf "\n%TY-%Tm-%Td %AT %p" | sort -nk1 | grep update_inventory.py | tail -1 | cut -d' ' -f3))
$ explode_ansible_test
$ cat debug_dir/args.json | jq '.ANSIBLE_MODULE_ARGS += { "remove_repo_dir": false, "test_mode": true }' > debug_dir/args
$ ./AnsiballZ_update_inventory.py execute
## OR if only want module return json to be parsed
$ ./AnsiballZ_update_inventory.py execute | jq
```

If already in a module debug dir, to move to latest and re-run:

```shell
$ cd $(dirname $(find .. -maxdepth 2 -name "*.py" -type f -printf "\n%TY-%Tm-%Td %AT %p" | sort -nk1 | grep update_inventory.py | tail -1 | cut -d' ' -f3))
$ explode_ansible_test
$ cat debug_dir/args.json | jq '.ANSIBLE_MODULE_ARGS += { "remove_repo_dir": false, "test_mode": true }' > debug_dir/args
$ ./AnsiballZ_update_inventory.py execute
## OR if only want module return json to be parsed
$ ./AnsiballZ_update_inventory.py execute | jq
```

### Reset inventory test data between repeated module/plugin debug runs

Run the following script to reset test data (e.g., tests/example/inventory/[plugin]/testrun/testdata.yml) to the starting state before repeated test runs:

```shell
$ reset-test-data.sh
```

### Debugging integration test results

```shell
$ cd ${HOME}/.ansible/tmp
$ cd ansible-tmp-1657821639.432363-21127-34939542886107
$ ./AnsiballZ_update_hosts.py explode
Module expanded into:
...
$ ./AnsiballZ_update_hosts.py execute | jq
INFO:root:Starting Module
...

```
