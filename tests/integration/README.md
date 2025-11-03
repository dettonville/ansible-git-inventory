
# Testing Modules

## Test environment

```shell
## ref: https://github.com/ansible/ansible/issues/76322
## ref: https://github.com/ansible/ansible/issues/32499
$ export TEST_PYTHON_VERSION="3.13"
$ export ANSIBLE_KEEP_REMOTE_FILES=1
$ export ANSIBLE_DEBUG=1
## is MacOS
$ export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
```

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

## Script to setup env vars and running ansible-test integration

Use the script ['ansible-test-integration.sh'](./../../../../../ansible-test-integration.sh) that will automatically:

1) set the necessary aforementioned environment variables
2) temporarily decrypt the integration_config.vault.yml to be used by the integration test
3) run the `ansible-test integration` command using any params passed to the script.

E.g., 

```shell
$ PROJECT_DIR="$( git rev-parse --show-toplevel )"
$ COLLECTION_DIR=${PROJECT_DIR}/collections/ansible_collections/dettonville/git_inventory
$ cd ${COLLECTION_DIR}
$ ${PROJECT_DIR}/ansible-test-integration.sh -v link_accounts
```

### Testing

## Sanity Testing

```shell
ansible-test sanity -v --docker --python ${TEST_PYTHON_VERSION} update_hosts

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


## Debugging modules

```shell
$ cd ${HOME}/.ansible/tmp/
$ ls -Fla ../$(ls -Fla ../ | tail -16 | head -1 | cut -d':' -f2 | cut -d' ' -f2)
$ cd ${HOME}/.ansible/tmp/ansible-tmp-1657821639.432363-21127-34939542886107
./AnsiballZ_update_hosts.py explode
./AnsiballZ_update_hosts.py execute | jq
## OR if jq unavailable
./AnsiballZ_update_hosts.py execute | python -m json.tool
```

### Run All Tests

```shell
tests/run_tests.sh > run_test.results.txt

```

### Debugging module references

* https://docs.ansible.com/ansible/latest/dev_guide/debugging.html
* https://yaobinwen.github.io/2021/01/29/Ansible-how-to-debug-a-problematic-module.html
