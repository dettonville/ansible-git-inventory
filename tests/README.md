
# Testing Modules

## Prepare test environment

```shell
export TEST_PYTHON_VERSION="3.13"
export ANSIBLE_KEEP_REMOTE_FILES=1
export ANSIBLE_DEBUG=1

```

### Sanity tests

```shell
ansible-test sanity --python 3.13  ## runs all sanity tests
ansible-test sanity --python 3.13 --test pep8
ansible-test sanity --python ${TEST_PYTHON_VERSION} --test pylint
ansible-test sanity --python ${TEST_PYTHON_VERSION} --test validate-modules
ansible-test sanity -v --docker --python ${TEST_PYTHON_VERSION} export_dicts
```

* Note: MacOS Issues

If running on MacOS may get the following error:
```output
 __NSCFConstantString initialize] may have been in progress in another thread when fork() was called

```

Resolved with the following setting:
```shell
## ref: https://github.com/ansible/ansible/issues/76322
## ref: https://github.com/ansible/ansible/issues/32499
$ export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
```

### Run All Tests

```shell
tests/run_tests.sh > run_test.results.txt
tests/run_tests.sh sanity
tests/run_tests.sh integration
tests/run_tests.sh -L DEBUG sanity

```

### Run Individually

## Sanity Testing

```shell
cd ${TEST_COLLECTION_DIR}
ansible-test sanity --test pep8
ansible-test sanity --python 3.13
```

To run automated resolve of issues using autopep8:

```shell
cd ${TEST_COLLECTION_DIR}
pip install autopep8
autopep8 --in-place plugins/modules/test_results_logger.py
autopep8 --in-place --aggressive --aggressive plugins/**/*.py
```

To run automated resolve of issues using black:

```shell
pip install black
black plugins/
ansible-test sanity --python 3.13 --test pep8
ansible-test sanity --python 3.13 --test pylint
```

To run automated resolve of unused imports/variables issues using autoflake (https://github.com/PyCQA/autoflake):

```shell
pip install autoflake
autoflake plugins/
autoflake -r --in-place --remove-unused-variables plugins/
autoflake -r --in-place --remove-unused-variables --remove-all-unused-imports plugins/
ansible-test sanity --python 3.13 --test pylint
```

To run automated resolve of issues using ruff (https://github.com/astral-sh/ruff):

```shell
pip install ruff
ruff format plugins/
ansible-test sanity --python 3.13 --test pep8
ansible-test sanity --python 3.13 --test pylint
```

```shell
ansible-test sanity -vv --python 3.13 --test pep8
ansible-test sanity --python 3.13 --python-interpreter ~/.pyenv/versions/3.13.3/bin/python3.13 --local --venv-system-site-packages
ansible-test sanity -v --docker --python ${TEST_PYTHON_VERSION} export_dicts
ansible-test sanity -v --color --coverage --junit --docker default --python ${TEST_PYTHON_VERSION}
ansible-test sanity -v --color --coverage --junit --docker default --python ${TEST_PYTHON_VERSION} export_dicts
```

## Integration Testing

```shell
export ANSIBLE_KEEP_REMOTE_FILES=1
ansible-test integration -v --color --python ${TEST_PYTHON_VERSION} update_hosts
```

### Running tests in docker image environment
```shell
ansible-test integration -v --docker --python ${TEST_PYTHON_VERSION} update_hosts
```

### Generating formatted test reports

```shell
$ ansible-test integration -v --color --python ${TEST_PYTHON_VERSION} update_hosts | aha > tests/integration/test-results.update_hosts.html
## OR
$ ansible-test integration -v --color --docker --python ${TEST_PYTHON_VERSION} update_hosts | ansi2html > tests/integration/test-results.update_hosts.html

Falling back to tests in "tests/integration/targets/" because "roles/test/" was not found.
Assuming Docker is available on localhost.
Run command: docker -v
Detected "docker" container runtime version: Docker version 20.10.16, build aa7e414
Starting new "ansible-test-controller-Nl1njsLi" container.
Run command: docker image inspect quay.io/ansible/default-test-container:4.2.0
Run command: docker run --volume /sys/fs/cgroup:/sys/fs/cgroup:ro --privileged=false --security-opt seccomp=unconfined --volume /var/run/docker.sock:/var/run/docker.sock --name ansible-test-controller-Nl1njsLi -d quay.io/ansible/default-test-container:4.2.0
...


PLAY RECAP *********************************************************************
testhost                   : ok=101  changed=19   unreachable=0    failed=0    skipped=9    rescued=0    ignored=4   

Run command: docker exec -i ansible-test-controller-Nl1njsLi sh -c 'tar cf - -C /root/ansible_collections/dettonville/git_inventory/tests --exclude .tmp output | gzip'
Run command: tar oxzf - -C /Users/ljohnson/repos/ansible/ansible_collections/dettonville/git_inventory/tests
Run command: docker rm -f ansible-test-controller-Nl1njsLi

```

* [Full detailed results here](./test-results.update_hosts.md)
* [Full detailed colorized results here](./test-results.update_hosts.pdf)


## Debugging test module

```shell
$ ls -Fla ../$(ls -Fla ../ | tail -16 | head -1 | cut -d':' -f2 | cut -d' ' -f2)
$ cd ${HOME}/.ansible/tmp/ansible-tmp-1657821639.432363-21127-34939542886107
./AnsiballZ_update_hosts.py explode
./AnsiballZ_update_hosts.py execute | jq
```

### Run All Tests

```shell
tests/run_tests.sh > run_test.results.txt

```
