

```shell
$ ansible --version
ansible [core 2.19.2]
  config file = None
  configured module search path = [/Users/ljohnson/.ansible/plugins/modules, /usr/share/ansible/plugins/modules]
  ansible python module location = /Users/ljohnson/.pyenv/versions/3.13.5/lib/python3.13/site-packages/ansible
  ansible collection location = /Users/ljohnson/.ansible/collections:/usr/share/ansible/collections
  executable location = /Users/ljohnson/.pyenv/versions/3.13.5/bin/ansible
  python version = 3.13.5 (main, Sep 18 2025, 19:11:35) [Clang 16.0.0 (clang-1600.0.26.6)] (/Users/ljohnson/.pyenv/versions/3.13.5/bin/python3.13)
  jinja version = 3.1.6
  pyyaml version = 6.0.2 (with libyaml v0.2.5)
$
$ REPO_DIR="$( git rev-parse --show-toplevel )"
$ cd ${REPO_DIR}
$
$ env ANSIBLE_NOCOLOR=True ansible-doc -t module dettonville.git_inventory.update_groups | tee /Users/ljohnson/repos/ansible/ansible_collections/dettonville/git_inventory/docs/update_groups.md
> MODULE dettonville.git_inventory.update_groups (/Users/ljohnson/tmp/_zRcNud/ansible_collections/dettonville/git_inventory/plugins/modules/update_groups.py)

  Ansible module to add, update, and/or remove group nodes to a
  specified YAML-file based inventory repository. If a
  'inventory_repo_url' is specified, modules will clone (optionally to
  a temporary repo directory) and commit and push inventory changes to
  the specified inventory repository. After git operations are
  completed, the repository directory may be removed or preserved
  based on the 'remove_repo_dir' setting.

OPTIONS (= indicates it is required):

- always_add_child_group_to_root  Always add group to root all.
        default: false
        type: bool

- backup  Create a backup inventory file including the timestamp
           information so you can get the original inventory file back
           if you somehow clobbered it incorrectly. This option is
           should not be necessary since the file can be rolled back
           to a prior commit using git.
        default: false
        type: bool

- create_empty_groupvars_files  Creates empty vars files
                                 ('group_vars/' or 'host_vars/') for
                                 group/host vars even when no vars
                                 specified.
                                 Only used if the `use_vars_files` is
                                 enabled.
        default: true
        type: bool

- create_parent_groupvar_files  Creates empty groupvar files
                                 ('group_vars/') for parent groups
                                 even when no vars specified.
                                 Only used if the `use_vars_files` or
                                 `create_empty_groupvars_files` is
                                 enabled (default).
        default: true
        type: bool

- enable_groupvar_symlinks_for_child_inventories  Enables
                                                   `group_vars`
                                                   symlinks for child
                                                   inventories.
                                                   Only used if the
                                                   `use_vars_files` is
                                                   enabled.
                                                   Used to link
                                                   group_vars/*.yml
                                                   files upon creation
                                                   of corresponding
                                                   root inventory
                                                   `group_vars`.
        default: true
        type: bool

- enforce_global_groups_must_already_exist  Validate host groups
                                             exist already in the
                                             specified
                                             global_groups_file before
                                             allowing hosts to be
                                             added.
                                             This will automatically
                                             be set to 'false'
                                             (ignored) when
                                             `global_groups_file` is
                                             equal to the
                                             `inventory_file`
                                             parameter
        default: true
        type: bool

- git_comment_body  Git comment body string.
        default: null
        type: str

- git_comment_prefix  Git comment prefix string.
        aliases: [jira_id]
        default: null
        type: str

- git_user_email  Explicit git local email address. Nice to have for
                   remote operations.
        default: ansible@example.org
        type: str

- git_user_name  Explicit git local user name. Nice to have for
                  remote operations.
        default: ansible
        type: str

- global_groups_file  File path to global groups YAML file relative
                       to repo directory root or parameter
                       `inventory_dir` if defined/set.
                       The inventory file must be YAML formatted.
                       E.g., `global_groups.yml`,
                       `test_inventory/xenv_groups.yml`,
                       `inventory/xenv_groups.yml`, etc.
                       Used to validate addition of groups to
                       inventory file when the parameter
                       `enforce_global_groups_must_already_exist` is
                       set to true
        default: xenv_groups.yml
        type: path

= group_list  Specifies a list of group dicts. The required key
               within the group item is 'group_name'. The supported
               keys within the group item dict are 'group_vars',
               'parent_groups' and 'groups'. The
               'parent_groups'/'groups' value is used to specify
               parent groups and may either be a list of group name
               strings or nested dicts where each key represents a
               group name.
        aliases: [groups]
        elements: dict
        type: list

- inventory_base_dir  Path to base directory where the inventory git
                       repository will be cloned.
                       If not specified, a temporary directory is
                       created in order to clone the inventory git
                       repo.
                       The temporary directory is automatically
                       removed after performing the inventory update
                       and git pacp action.
                       If desired, the temporary directory may be
                       saved by setting the 'remove_repo_dir' option
                       to true.
        default: null
        type: path

- inventory_dir  Relative path to inventory directory where inventory
                  YAML files are located relative to repo directory
                  root.
                  If not specified, the `inventory_dir` is derived
                  from the implied relative path of `inventory_file`.
                  E.g., `test_inventory/child_inventory`,
                  `inventory/SANDBOX`, `inventory/DEV`, or `inventory`
                  for parent inventory use cases.
        default: null
        type: path

= inventory_file  File path to inventory hosts YAML file relative to
                   repo directory root or parameter `inventory_dir` if
                   defined/set.
                   The inventory file must be YAML formatted.
                   E.g., `test_inventory/child_inventory/hosts.yml`,
                   `inventory/SANDBOX/hosts.yml`, etc.
        type: path

- inventory_repo_branch  Git branch where perform git push.
        default: main
        type: str

- inventory_repo_url  Git inventory repository URL.
        default: null
        type: str

- inventory_root_yaml_key  Inventory root node key in yaml. E.g.,
                            'all'
        default: all
        type: str

- logging_level  Parameter used to define the level of
                  troubleshooting output.
        choices: [NOTSET, DEBUG, INFO, ERROR]
        default: INFO
        type: str

- remove_repo_dir  Remove temporary repo inventory directory after
                    completing.
        default: true
        type: bool

- ssh_params  Dictionary containing SSH parameters.
        default: null
        type: dict
        suboptions:

        - accept_hostkey  If `yes', ensure that "-o
                           StrictHostKeyChecking=no" is present as an
                           ssh option.
          default: false
          type: bool

        - key_file  Specify an optional private key file path, on the
                     target host, to use for the checkout.
          default: null
          type: path

        - ssh_opts  Creates a wrapper script and exports the path as
                     GIT_SSH which git then automatically uses to
                     override ssh arguments. An example value could be
                     "-o StrictHostKeyChecking=no" (although this
                     particular option is better set via
                     `accept_hostkey').
          default: null
          type: str

- state   State for the update - 'merge', 'overwrite', or 'absent'.
        choices: [merge, overwrite, absent]
        default: merge
        type: str

- symlink_subdirs  Specifies a list of inventory sub-directories.
                    Used when
                    'enable_groupvar_symlinks_for_child_inventories'
                    is set to create group_vars symlinks.
                    The sub-directories must reside directly in
                    'inventory_dir'.
        default: [DEV, QA, PROD, SANDBOX]
        elements: str
        type: list

- test_mode  Enable test mode
        default: false
        type: bool

- use_vars_files  Use vars files ('group_vars/') for group vars
                   instead of inline group_vars.
        default: true
        type: bool

- vars_overwrite_depth  if vars_state='overwrite' is used, the depth
                         at which variable overwrites will begin.
        default: 2
        type: int

- vars_state  State for the vars update - 'merge' or 'overwrite'.
        choices: [merge, overwrite]
        default: merge
        type: str

- yaml_lib_mode  specifies the YAML library - 'ruamel' or 'pyyaml'.
        choices: [ruamel, pyyaml]
        default: ruamel
        type: str

REQUIREMENTS:  git>=2.10.0 (the command line tool)


AUTHOR: Lee Johnson (@lj020326)

EXAMPLES:
- name: "Add groups with system_name and system_env using groups list method"
  dettonville.git_inventory.update_groups:
    inventory_repo_url: ssh://git@repo.example.org:2222/ansible/demo-inventory.git
    inventory_repo_branch: develop
    inventory_dir: inventory/SANDBOX
    inventory_file: hosts.yml
    use_vars_files: true
    git_comment_prefix: "INFRA-25088"
    ssh_params:
      accept_hostkey: true
      key_file: /tmp/.ansible_test_jobs_qhg_dmhp/ansible_repo.key
    logging_level: "DEBUG"
    group_list:
      - group_name: app_systest1_sandbox
        group_vars:
          app_var: something here
        parent_groups:
          - app_systest1
      ## the original/ambiguous subkey 'groups' is still supported
      - group_name: app_systest2_sandbox
        group_vars:
          app_var: something here
        groups:
          - app_systest2

- name: "Add groups with system_name and system_env using children groups method"
  dettonville.git_inventory.update_groups:
    inventory_repo_url: ssh://git@repo.example.org:2222/ansible/demo-inventory.git
    inventory_repo_branch: develop
    inventory_dir: inventory/SANDBOX
    inventory_file: hosts.yml
    use_vars_files: true
    git_comment_prefix: "INFRA-25088"
    ssh_params: "{{ __test_git_ssh_params }}"
    logging_level: "DEBUG"
    group_list:
      - group_name: app_systest1
        group_vars:
          app_var: something here
        children:
          app_systest1_sandbox: {}
      - group_name: app_systest2
        group_vars:
          app_var: something for app systest2 here
        children:
          app_systest2_sandbox: {}

- name: "Add `groups_vars` to inventory"
  dettonville.git_inventory.update_groups:
    inventory_repo_url: ssh://git@repo.example.org:2222/ansible/demo-inventory.git
    inventory_repo_branch: develop
    inventory_dir: inventory/SANDBOX
    inventory_file: hosts.yml
    use_vars_files: true
    git_comment_prefix: "INFRA-25088"
    ssh_params: "{{ __test_git_ssh_params }}"
    logging_level: "DEBUG"
    group_list:
      - group_name: fake_group_kcp
      - group_name: fake_group_kcp_sandbox
        group_vars:
          fake_env: sandbox
        parent_groups:
          - fake_group_kcp
  register: __update_group_result

- name: "Adds vars into inventory root `group_vars` and symlinks to child inventory `groups_vars`"
  dettonville.git_inventory.update_groups:
    inventory_repo_url: "{{ __test_inventory_git_repo_url }}"
    inventory_repo_branch: "{{ __test_inventory_git_repo_branch }}"
    ## Note when the inventory file is in a child directory from the inventory_dir,
    ## a symlink will automatically get created into the child inventory directory `group_vars`
    inventory_dir: inventory
    inventory_file: SANDBOX/hosts.yml
    use_vars_files: true
    git_comment_prefix: "{{ __test_inventory_jira_id }}"
    ssh_params: "{{ __test_git_ssh_params }}"
    logging_level: "DEBUG"
    group_list:
      - group_name: fake_group_kcp_sandbox
        group_vars:
          fake_env: sandbox
        ## Note parent groups will automatically get created if they do not already exist
        ## so there is no need to include separate items/entries for any of the parent groups
        parent_groups:
          - fake_group_kcp
  register: __update_groups_result

- name: Add groups to inventory at hosts.yml
  dettonville.git_inventory.update_groups:
    inventory_repo_url: ssh://git@repo.example.org:2222/ansible/demo-inventory.git
    inventory_file: inventory/SANDBOX/hosts.yml
    git_comment_prefix: "INFRA-24007"
    ssh_params: "{{ test_git_ssh_params }}"
    backup: false
    group_list:
      - group_name: ocp_common
        group_vars:
          ocp_namespace_configuration:
            - name: name1
              value: something else
            - name: name2
              value: raboof
      - group_name: ocp_dev_s1
        group_vars:
          ocp_environment: dev
          ocp_site: s1
        parent_groups:
          - ocp_common
      - group_name: ocp_qa_s1
        group_vars:
          ocp_environment: qa
          ocp_site: s1
        parent_groups:
          - ocp_common
      - group_name: ocp_prod_s1
        group_vars:
          ocp_environment: prod
          ocp_site: s1
        parent_groups:
          - ocp_common

- name: Add and update groups with vars in group_vars files
  dettonville.git_inventory.update_groups:
    inventory_repo_url: ssh://git@repo.example.org:2222/ansible/demo-inventory.git
    inventory_file: inventory/SANDBOX/hosts.yml
    inventory_repo_branch: develop
    git_comment_prefix: "INFRA-24007"
    use_vars_files: true
    ssh_params: "{{ test_git_ssh_params }}"
    group_list:
      - group_name: location_site1
        group_vars:
          site: site1

- name: Add groups to hierarchical groups
  dettonville.git_inventory.update_groups:
    inventory_repo_url: ssh://git@repo.example.org:2222/ansible/demo-inventory.git
    inventory_file: inventory/SANDBOX/hosts.yml
    inventory_repo_branch: main
    git_comment_prefix: "INFRA-24007"
    use_vars_files: true
    create_empty_groupvars_files: false
    ssh_params: "{{ test_git_ssh_params }}"
    group_list:
      - group_name: admin_qa_site1
        group_vars:
          infra_group: DCC
        parent_groups:
          location_site1:
            nfs_server: {}
            ntp_server: {}
            ldap_server: {}
          vmware_flavor_large: {}
      - group_name: webapp01_qa_site1
        group_vars:
          app_version: 2023086
        parent_groups:
          location_site1:
            ntp_client: {}
            nfs_client: {}
            ldap_client: {}
            web_server: {}
          vmware_flavor_small: {}
      - group_name: webapp02_qa_site1
        group_vars:
          app_version: 2023086
        parent_groups:
          location_site1:
            ntp_client: {}
            nfs_client: {}
            ldap_client: {}
            web_server: {}
          vmware_flavor_small: {}

- name: Update groups at hosts.yml
  dettonville.git_inventory.update_groups:
    inventory_repo_url: ssh://git@repo.example.org:2222/ansible/demo-inventory.git
    inventory_file: inventory/SANDBOX/hosts.yml
    inventory_repo_branch: main
    git_comment_prefix: "INFRA-24007"
    ssh_params:
      accept_hostkey: true
      key_file: '~/.ssh/id_rsa'
    group_list:
      - group_name: admin_qa_site1
        group_vars:
          infra_group: DCC
        parent_groups:
          - vmware_flavor_large
          - ntp_server
          - nfs_server
          - ldap_server
      - group_name: webapp01_qa_site1
        group_vars:
          app_version: 2023086
        parent_groups:
          - vmware_flavor_small
          - ntp_client
          - nfs_client
          - ldap_client
          - web_server
      - group_name: webapp02_qa_site1
        group_vars:
          app_version: 2023086
        parent_groups:
          - vmware_flavor_small
          - ntp_client
          - nfs_client
          - ldap_client
          - web_server

- name: Overwrite groups at hosts.yml
  dettonville.git_inventory.update_groups:
    inventory_repo_url: ssh://git@repo.example.org:2222/ansible/demo-inventory.git
    inventory_file: inventory/SANDBOX/hosts.yml
    inventory_repo_branch: main
    git_comment_prefix: "INFRA-24007"
    ssh_params:
      accept_hostkey: true
      key_file: '~/.ssh/id_rsa'
      ssh_opts: '-o UserKnownHostsFile={{ remote_tmp_dir }}/known_hosts'
    state: overwrite
    group_list:
      - group_name: location_site1
        group_vars:
          site: site1
      - group_name: admin_qa_site1
        group_vars:
          provisioning_data: {}
      - group_name: webapp01_qa_site1
        group_vars:
          app_version: 2023086
        parent_groups:
          - vmware_flavor_medium
          - rhel7
          - network_internal
          - location_site1
          - ntp_client
          - web_server
      - group_name: webapp02_qa_site1
        group_vars:
          app_version: 2023086
        parent_groups:
          - vmware_flavor_small
          - rhel7
          - network_dmz
          - location_site1
          - ntp_client
          - nfs_client
          - ldap_client
          - web_server
          - unica_proxy

- name: Remove groups from inventory at hosts.yml
  dettonville.git_inventory.update_groups:
    inventory_repo_url: ssh://git@repo.example.org:2222/ansible/demo-inventory.git
    inventory_file: inventory/SANDBOX/hosts.yml
    git_comment_prefix: "INFRA-24007"
    ssh_params:
      key_file: '~/.ssh/id_rsa'
    state: absent
    group_list:
      - group_name: location_site1

RETURN VALUES:

- backup_files  List of inventory backup file(s) created
        returned: when backup=yes
        sample: ['/path/to/hosts.yml.1942.2017-08-24@14:16:01~']
        type: list

- changed  True if successful
        returned: always
        type: bool

- failed  True if failed to update the inventory.
        returned: always
        type: bool

- inventory_base_dir  The path of the inventory repo directory that
                       was updated
        returned: when remove_repo_dir=false
        sample: /tmp/path/to/git_inventory_repo
        type: str

- message  Status message for lookup
        returned: always
        sample: Inventory updated successfully
        type: str

```
