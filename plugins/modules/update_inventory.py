#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: update_inventory
author:
    - "Lee Johnson (@lj020326)"
short_description: Add/update group and/or host nodes and respective variable settings to a specified YAML-file based inventory. 
description:
  Ansible module to add, update, and/or remove group and/or host nodes to a specified YAML-file
  based inventory repository.

  If a 'inventory_repo_url' is specified, modules will clone (optionally to a temporary repo directory) and commit and push inventory changes to the specified inventory repository.

  After git operations are completed, the repository directory may be removed or preserved based on the 'remove_repo_dir' setting. 
options:
    inventory_file:
        required: true
        type: path
        description:
            - File path to inventory hosts YAML file relative to repo directory root or parameter `inventory_dir` if defined/set.
            - The inventory file must be YAML formatted.
            - E.g., `test_inventory/child_inventory/hosts.yml`, `inventory/SANDBOX/hosts.yml`, etc. 
    inventory_dir:
        required: false
        type: path
        description:
            - Relative path to inventory directory where inventory YAML files are located relative to repo directory root. 
            - If not specified, the `inventory_dir` is derived from the implied relative path of `inventory_file`.
            - E.g., `test_inventory/child_inventory`, `inventory/SANDBOX`, `inventory/DEV`, or `inventory` for parent inventory use cases. 
    inventory_repo_url:
        description:
            - Git inventory repository URL.
        type: str
    inventory_base_dir:
        required: false
        type: path
        description:
            - Path to base directory where the inventory git repository will be cloned.
            - If not specified, a temporary directory is created in order to clone the inventory git repo.
            - The temporary directory is automatically removed after performing the inventory update and git pacp action.
            - If desired, the temporary directory may be saved by setting the 'remove_repo_dir' option to true.
    inventory_repo_branch:
        description:
            - Git branch where perform git push.
        type: str
        default: main
    yaml_lib_mode:
        description: 
            - specifies the YAML library - 'ruamel' or 'pyyaml'.
        choices: [ ruamel, pyyaml ]
        default: ruamel
        type: str
    global_groups_file:
        type: path
        required: false
        default: "xenv_groups.yml"
        description:
            - File path to global groups YAML file relative to repo directory root or parameter `inventory_dir` if defined/set.
            - The inventory file must be YAML formatted.
            - E.g., `global_groups.yml`, `test_inventory/xenv_groups.yml`, `inventory/xenv_groups.yml`, etc.
            - Used to validate addition of groups to inventory file when the parameter `enforce_global_groups_must_already_exist` is set to true
    inventory_root_yaml_key:
        description:
            - Inventory root node key in yaml. E.g., 'all'
        type: str
        default: all
    logging_level:
        description:
            - Parameter used to define the level of troubleshooting output.
        required: false
        choices: [NOTSET, DEBUG, INFO, ERROR]
        default: INFO
        type: str
    state:
        description:
            - State for the update - 'merge', 'overwrite', or 'absent'.
        choices: ['merge', 'overwrite', 'absent']
        default: merge
        type: str
    vars_state:
        description:
            - State for the vars update - 'merge' or 'overwrite'.
        choices: ['merge', 'overwrite']
        default: merge
        type: str
    vars_overwrite_depth:
        description:
            - if vars_state='overwrite' is used, the depth at which variable overwrites will begin.
        default: 2
        type: int
    backup:
        description:
          - Create a backup inventory file including the timestamp information so you can get
            the original inventory file back if you somehow clobbered it incorrectly.  
            This option is should not be necessary since the file can be rolled back to a prior commit using git.  
        type: bool
        default: false
    remove_repo_dir:
        description:
            - Remove temporary repo inventory directory after completing.
        type: bool
        default: true
    group_list:
        description:
            - Specifies a list of group dicts.  
              The required key within the group item is 'group_name'.
              The supported keys within the group item dict are 'group_vars', 'parent_groups' and 'groups'.
              The 'parent_groups'/'groups' value is used to specify parent groups and may either be a list of group name strings or 
              nested dicts where each key represents a group name. 
        aliases: ['groups']
        default: []
        type: list
        elements: dict
    host_list:
        description:
            - Specifies a list of host dicts.  
              The required key within the group item is 'host_name'.
              The supported keys within the host item dict are 'host_name', 'host_vars', 'parent_groups' and 'groups'.
              The 'parent_groups'/'groups' value may either be a list of hostname strings or 
              nested dicts where each key represents a parent group name. 
        aliases: ['hosts']
        default: []
        type: list
        elements: dict
    use_vars_files:
        description:
            - Use vars files ('group_vars/' or 'host_vars/') for group/host vars instead of inline host_vars/group_vars.
        type: bool
        default: true
    create_empty_groupvars_files:
        description:
            - Creates empty 'group_vars/' vars files for group vars even when no vars specified.
            - Only used if the `use_vars_files` is enabled. 
        type: bool
        default: true
    create_empty_hostvars_files:
        description:
            - Creates empty 'host_vars/' vars files for host vars even when no vars specified.
            - Only used if the `use_vars_files` is enabled. 
        type: bool
        default: false
    create_parent_groupvar_files:
        description:
            - Creates empty groupvar files ('group_vars/') for parent groups even when no vars specified.
            - Only used if the `use_vars_files` or `create_empty_groupvars_files` is enabled (default). 
        type: bool
        default: true
    always_add_child_group_to_root:
        description:
            - Always add child groups to root all.
        type: bool
        default: false
    always_add_host_to_root_hosts:
        description:
            - Always add host to root hosts.
        type: bool
        default: false
    enforce_global_groups_must_already_exist:
        description:
            - Validate host groups exist already in the specified global_groups_file before allowing hosts to be added.
            - This will automatically be set to 'false' (ignored) when `global_groups_file` is equal to the `inventory_file` parameter 
        type: bool
        default: true
    enable_groupvar_symlinks_for_child_inventories:
        description:
            - Enables `group_vars` symlinks for child inventories.
            - Only used if the `use_vars_files` is enabled. 
            - Used to link group_vars/*.yml files upon creation of corresponding root inventory `group_vars`.
        type: bool
        default: true
    symlink_subdirs:
        description:
            - Specifies a list of inventory sub-directories.
            - Used when 'enable_groupvar_symlinks_for_child_inventories' is set to create group_vars symlinks.
            - The sub-directories must reside directly in 'inventory_dir'.  
        default: ['DEV','QA','PROD','SANDBOX']
        type: list
        elements: str
    git_comment_prefix:
        description:
            - Git comment prefix string.
        type: str
        aliases: ['jira_id']
        required: false
    git_comment_body:
        description:
            - Git comment body string.
        type: str
        required: false
        version_added: 2025.7.0
    ssh_params:
        description:
            - Dictionary containing SSH parameters.
        type: dict
        suboptions:
            key_file:
                description:
                    - Specify an optional private key file path, on the target host, to use for the checkout.
                type: path
            accept_hostkey:
                description:
                    - If C(yes), ensure that "-o StrictHostKeyChecking=no" is
                      present as an ssh option.
                type: bool
                default: false
            ssh_opts:
                description:
                    - Creates a wrapper script and exports the path as GIT_SSH
                      which git then automatically uses to override ssh arguments.
                      An example value could be "-o StrictHostKeyChecking=no"
                      (although this particular option is better set via
                      C(accept_hostkey)).
                type: str
    test_mode:
        description:
            - Enable test mode
        type: bool
        default: false
    git_user_name:
        description:
            - Explicit git local user name. Nice to have for remote operations.
        type: str
        default: ansible
    git_user_email:
        description:
            - Explicit git local email address. Nice to have for remote operations.
        type: str
        default: ansible@example.org

requirements:
    - git>=2.10.0 (the command line tool)
"""  # NOQA

EXAMPLES = r"""
- name: "Add groups with system_name and system_env using groups list method"
  dettonville.git_inventory.update_inventory:
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
  dettonville.git_inventory.update_inventory:
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
  dettonville.git_inventory.update_inventory:
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
  dettonville.git_inventory.update_inventory:
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
  dettonville.git_inventory.update_inventory:
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
  dettonville.git_inventory.update_inventory:
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
  dettonville.git_inventory.update_inventory:
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
  dettonville.git_inventory.update_inventory:
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
  dettonville.git_inventory.update_inventory:
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
  dettonville.git_inventory.update_inventory:
    inventory_repo_url: ssh://git@repo.example.org:2222/ansible/demo-inventory.git
    inventory_file: inventory/SANDBOX/hosts.yml
    git_comment_prefix: "INFRA-24007"
    ssh_params:
      key_file: '~/.ssh/id_rsa'
    state: absent
    group_list:
      - group_name: location_site1

- name: Add hosts to inventory at hosts.yml
  dettonville.git_inventory.update_inventory:
    inventory_repo_url: ssh://git@repo.example.org:2222/ansible/demo-inventory.git
    inventory_file: inventory/SANDBOX/hosts.yml
    git_comment_prefix: "INFRA-24007"
    ssh_params: "{{ test_git_ssh_params }}"
    backup: false
    host_list:
      - host_name: vmlnx123-q1-s1.example.int
        host_vars:
          provisioning_data:
            jira_id: INFRA-12345
            infra_group: automation-engineering
        parent_groups:
          - vmware_flavor_medium
          - ntp_client
          - ldap_client
      ## the original/ambiguous subkey 'groups' is still supported
      - host_name: vmlnx124-q1-s1.example.int
        host_vars:
          provisioning_data:
            jira_id: DCC-12346
            infra_group: automation-engineering
        groups:
          - vmware_flavor_medium
          - ntp_client
          - nfs_client
          - ldap_client

- name: Add hosts with vars in host_vars files
  dettonville.git_inventory.update_inventory:
    inventory_repo_url: ssh://git@repo.example.org:2222/ansible/demo-inventory.git
    inventory_file: inventory/SANDBOX/hosts.yml
    inventory_repo_branch: develop
    git_comment_prefix: "INFRA-24007 - add hosts: admin01.qa.site1.example.int"
    ssh_params: "{{ test_git_ssh_params }}"
    use_vars_files: true
    host_list:
      - host_name: admin01.qa.site1.example.int
        host_vars:
          infra_group: DCC
          service_domains:
            - admin.qa.example.int

- name: "Adds host vars into inventory root `host_vars` and update child inventory hosts.yml"
  dettonville.git_inventory.update_inventory:
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
    host_list:
      - host_name: vmlnx123.qa.site1.example.int
        parent_groups:
          location_site1:
            nfs_server: {}
            ntp_client: {}
            ldap_client: {}
      - host_name: vmlnx124.qa.site1.example.int
        parent_groups:
          location_site1:
            nfs_client: {}
            ntp_client: {}
            ldap_client: {}

- name: Add hosts to hierarchical groups
  dettonville.git_inventory.update_inventory:
    inventory_repo_url: ssh://git@repo.example.org:2222/ansible/demo-inventory.git
    inventory_file: inventory/SANDBOX/hosts.yml
    inventory_repo_branch: develop
    git_comment_prefix: "INFRA-24007"
    ssh_params: "{{ test_git_ssh_params }}"
    use_vars_files: true
    create_empty_hostvars_files: false
    host_list:
      - host_name: vmlnx123.qa.site1.example.int
        parent_groups:
          location_site1:
            nfs_server: {}
            ntp_client: {}
            ldap_client: {}
      - host_name: vmlnx124.qa.site1.example.int
        parent_groups:
          location_site1:
            nfs_client: {}
            ntp_client: {}
            ldap_client: {}

- name: Update hosts at hosts.yml
  dettonville.git_inventory.update_inventory:
    inventory_repo_url: ssh://git@repo.example.org:2222/ansible/demo-inventory.git
    inventory_file: inventory/SANDBOX/hosts.yml
    inventory_repo_branch: main
    git_comment_prefix: "INFRA-24007"
    ssh_params:
      accept_hostkey: true
      key_file: '~/.ssh/id_rsa'
    host_list:
      - host_name: admin-q1-internal-s1.example.int
        host_vars:
          provisioning_data:
            jira_id: INFRA-12345
            infra_group: DCC
        parent_groups:
          - vmware_flavor_large
          - ntp_server
          - nfs_server
          - ldap_server
      - host_name: web-q1-internal-s1.example.int
        host_vars:
          provisioning_data:
            jira_id: DCC-12346
            infra_group: automation-engineering
        parent_groups:
          - vmware_flavor_small
          - ntp_client
          - nfs_client
          - ldap_client
          - web_server
      - host_name: web-q2-internal-s1.example.int
        host_vars:
          provisioning_data:
            jira_id: DCC-12346
            infra_group: automation-engineering
        parent_groups:
          - vmware_flavor_small
          - ntp_client
          - nfs_client
          - ldap_client
          - web_server

- name: Overwrite hosts at hosts.yml
  dettonville.git_inventory.update_inventory:
    inventory_repo_url: ssh://git@repo.example.org:2222/ansible/demo-inventory.git
    inventory_file: inventory/SANDBOX/hosts.yml
    inventory_repo_branch: main
    git_comment_prefix: "INFRA-24007"
    ssh_params:
      accept_hostkey: true
      key_file: '~/.ssh/id_rsa'
      ssh_opts: '-o UserKnownHostsFile={{ remote_tmp_dir }}/known_hosts'
    state: overwrite
    host_list:
      - host_name: admin-q1-internal-s1.example.int
        host_vars:
          provisioning_data: {}
        parent_groups: {}
      - host_name: web-q1-internal-s1.example.int
        host_vars:
          provisioning_data:
            jira_id: DCC-88888
            infra_group: automation-engineering
        parent_groups:
          - vmware_flavor_medium
          - rhel7
          - network_internal
          - location_site1
          - ntp_client
          - web_server
      - host_name: web-q2-internal-s1.example.int
        host_vars:
          provisioning_data:
            jira_id: DCC-888888
            infra_group: automation-engineering
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

- name: Remove hosts from inventory at hosts.yml
  dettonville.git_inventory.update_inventory:
    inventory_repo_url: ssh://git@repo.example.org:2222/ansible/demo-inventory.git
    inventory_file: inventory/SANDBOX/hosts.yml
    git_comment_prefix: "INFRA-24007"
    ssh_params:
      key_file: '~/.ssh/id_rsa'
    state: absent
    host_list:
      - host_name: admin-q1-internal-s1.example.int
      - host_name: web-q1-internal-s1.example.int
      - host_name: web-q2-internal-s1.example.int

- name: Add groups and hosts to inventory at hosts.yml
  dettonville.git_inventory.update_inventory:
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
    host_list:
      - host_name: vmlnx123-q1-s1.example.int
        host_vars:
          provisioning_data:
            jira_id: INFRA-12345
            infra_group: automation-engineering
        parent_groups:
          - vmware_flavor_medium
          - ntp_client
          - ldap_client

- name: Update groups and hosts at hosts.yml
  dettonville.git_inventory.update_inventory:
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
    host_list:
      - host_name: admin-q1-internal-s1.example.int
        host_vars:
          provisioning_data:
            jira_id: INFRA-12345
            infra_group: DCC
        parent_groups:
          - vmware_flavor_large
          - ntp_server
          - nfs_server
          - ldap_server

- name: Overwrite groups and hosts at hosts.yml
  dettonville.git_inventory.update_inventory:
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
    host_list:
      - host_name: admin-q1-internal-s1.example.int
        host_vars:
          provisioning_data: {}
        parent_groups: {}
      - host_name: web-q1-internal-s1.example.int
        host_vars:
          provisioning_data:
            jira_id: DCC-88888
            infra_group: automation-engineering
        parent_groups:
          - vmware_flavor_medium
          - rhel7
          - network_internal
          - location_site1
          - ntp_client
          - web_server
      - host_name: web-q2-internal-s1.example.int
        host_vars:
          provisioning_data:
            jira_id: DCC-888888
            infra_group: automation-engineering
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

- name: Remove groups and hosts from inventory at hosts.yml
  dettonville.git_inventory.update_inventory:
    inventory_repo_url: ssh://git@repo.example.org:2222/ansible/demo-inventory.git
    inventory_file: inventory/SANDBOX/hosts.yml
    git_comment_prefix: "INFRA-24007"
    ssh_params:
      key_file: '~/.ssh/id_rsa'
    state: absent
    group_list:
      - group_name: location_site1
    host_list:
      - host_name: admin-q1-internal-s1.example.int
      - host_name: web-q1-internal-s1.example.int
      - host_name: web-q2-internal-s1.example.int
"""  # NOQA

RETURN = r"""
message: 
    description: Status message for lookup
    type: str
    returned: always
    sample: "Inventory updated successfully"
failed: 
    description: True if failed to update the inventory.
    type: bool
    returned: always
changed: 
    description: True if successful
    type: bool
    returned: always
inventory_base_dir:
    description: The path of the inventory repo directory that was updated
    type: str
    returned: when remove_repo_dir=false
    sample: /tmp/path/to/git_inventory_repo
backup_files:
    description: List of inventory backup file(s) created
    type: list
    returned: when backup=yes
    sample: ['/path/to/hosts.yml.1942.2017-08-24@14:16:01~']

"""  # NOQA

from ansible.module_utils.basic import AnsibleModule

# ref: https://terryhowe.github.io/ansible-modules-hashivault/dev_guide/developing_collections.html
# noinspection PyUnresolvedReferences
from ansible_collections.dettonville.git_inventory.plugins.module_utils.git_inventory_updater import (
    GitInventoryUpdater,
)

import sys
import logging
import pprint

# define available arguments/parameters a user can pass to the module
module_args = dict(
    inventory_file=dict(required=True, type="path"),
    inventory_dir=dict(required=False, type="path"),
    inventory_repo_url=dict(default=None),
    inventory_repo_branch=dict(default="main"),
    inventory_base_dir=dict(required=False, type="path"),
    inventory_root_yaml_key=dict(type="str", default="all"),
    global_groups_file=dict(type="path", default="xenv_groups.yml"),
    logging_level=dict(
        type="str", choices=["NOTSET", "DEBUG", "INFO", "ERROR"], default="INFO"
    ),
    git_comment_prefix=dict(
        aliases=["jira_id"], required=False, type="str", default=None
    ),
    git_comment_body=dict(required=False, type="str", default=None),
    group_list=dict(aliases=["groups"], type="list", elements="dict", default=[]),
    host_list=dict(aliases=["hosts"], type="list", elements="dict", default=[]),
    state=dict(choices=["merge", "overwrite", "absent"], default="merge"),
    vars_state=dict(choices=["merge", "overwrite"], default="merge"),
    vars_overwrite_depth=dict(type="int", default=2),
    use_vars_files=dict(type="bool", default=True),
    create_empty_groupvars_files=dict(type="bool", default=True),
    create_empty_hostvars_files=dict(type="bool", default=False),
    create_parent_groupvar_files=dict(type="bool", default=True),
    always_add_child_group_to_root=dict(type="bool", default=False),
    always_add_host_to_root_hosts=dict(type="bool", default=False),
    enforce_global_groups_must_already_exist=dict(type="bool", default=True),
    enable_groupvar_symlinks_for_child_inventories=dict(type="bool", default=True),
    symlink_subdirs=dict(
        type="list", elements="str", default=["DEV", "QA", "PROD", "SANDBOX"]
    ),
    remove_repo_dir=dict(type="bool", default=True),
    backup=dict(type="bool", default=False),
    ssh_params=dict(
        type="dict",
        required=False,
        options=dict(
            key_file=dict(type="path"),
            accept_hostkey=dict(type="bool", default=False),
            ssh_opts=dict(type="str", default=None),
        ),
    ),
    test_mode=dict(type="bool", default=False),
    yaml_lib_mode=dict(choices=["ruamel", "pyyaml"], default="ruamel"),
    git_user_name=dict(type="str", default="ansible"),
    git_user_email=dict(type="str", default="ansible@example.org"),
)


# ref: https://docs.ansible.com/ansible/latest/dev_guide/testing_units_modules.html#restructuring-modules-to-enable-testing-module-set-up-and-other-processes
def setup_module_object():

    required_one_of = [
        ["group_list", "host_list"],
    ]
    required_together = [
        ["git_user_name", "git_user_email"],
    ]
    module = AnsibleModule(
        argument_spec=module_args,
        required_one_of=required_one_of,
        required_together=required_together,
        supports_check_mode=True,
    )
    return module


def run_module():
    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    module = setup_module_object()
    module._ansible_debug = True

    result = dict(changed=False, failed=False, check_mode=module.check_mode)

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # logging.basicConfig(level=module.params["logging_level"], stream=sys.stdout)
    loglevel = module.params.get("logging_level")
    logging.basicConfig(level=loglevel, stream=sys.stdout)

    inventory_file = module.params["inventory_file"]
    if not inventory_file:
        module.fail_json(msg="Missing required parameter 'inventory_file'")

    logging.debug("inventory_file => %s", inventory_file)

    git_user_name = module.params.get("git_user_name")
    git_user_email = module.params.get("git_user_email")

    inventory_repo_url = module.params.get("inventory_repo_url")
    if inventory_repo_url:
        git_repo_config = {
            "repo_url": inventory_repo_url,
            "repo_branch": module.params.get("inventory_repo_branch"),
            "ssh_params": module.params.get("ssh_params") or None,
            "user_name": git_user_name,
            "user_email": git_user_email,
        }
    else:
        git_repo_config = None

    # Pass all relevant module parameters to GitInventoryUpdater
    updater_kwargs = {
        k: module.params[k]
        for k in module.params
        if k
        not in [
            "group_list",
            "host_list",
            "inventory_file",
            "inventory_repo_url",
            "inventory_repo_branch",
            "ssh_params",  # These are handled in git_repo_config
        ]
    }

    group_list = module.params.get("group_list", None)
    host_list = module.params.get("host_list", None)

    logging.debug("module.params => %s", pprint.pformat(module.params))

    inventory_updater = GitInventoryUpdater(
        module=module,
        inventory_file=inventory_file,
        git_repo_config=git_repo_config,
        **updater_kwargs
    )

    update_result = inventory_updater.update_inventory(
        group_list=group_list, host_list=host_list
    )

    result.update(update_result)

    logging.debug("result => %s", pprint.pformat(result))
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
