
[![ansible-test sanity](https://github.com/dettonville/ansible-git-inventory/actions/workflows/ansible-test-sanity.yml/badge.svg)](https://github.com/dettonville/ansible-git-inventory/actions/workflows/ansible-test-sanity.yml)
[![ansible-test units](https://github.com/dettonville/ansible-git-inventory/actions/workflows/ansible-test-units.yml/badge.svg)](https://github.com/dettonville/ansible-git-inventory/actions/workflows/ansible-test-units.yml)
[![ansible-lint](https://github.com/dettonville/ansible-git-inventory/actions/workflows/ansible-lint.yml/badge.svg)](https://github.com/dettonville/ansible-git-inventory/actions/workflows/ansible-lint.yml)
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg?style=flat)](LICENSE.md)

# Dettonville Ansible Git Inventory Collection

The Ansible ``dettonville.git_inventory`` collection includes 3 modules (update_inventory, update_groups, and update_hosts) support adding, updating, and/or removing host and group nodes and respective variable values for a specified YAML-based inventory.

The modules can be integrated to establish Git for a "configuration-as-code" approach to Ansible inventory management.

The features supported by the git_inventory modules are especially helpful when integrating an ansible YAML based inventory into a host and/or application provisioning workflow scheme as highlighted in the following graph. 

```mermaid
graph TD
    A[Provisioning Request Initiated] --> B{Provision Host / Application};

    B --> C[Host/Application Provisioned];
    C --> D[Gather Host/Application State Information<br>e.g., IP, Hostname, App Version, Roles];
    D --> E[Execute **git_inventory.update_inventory** Module];
    E --> F[Module Clones/Pulls Git Inventory Repo];
    F --> G[Module Applies Inventory Updates<br>Add/Update Host/Group/Vars];
    G --> H[Module Commits & Pushes Changes to Git];
    H --> I[Ansible Git Inventory Updated];
    I --> J[Apply ansible provisioning playbook for inventory updated Host/Application];
    J --> K[Provisioning Workflow Complete];

    style A fill:#f9f,stroke:#333,stroke-width:2px;
    style E fill:#ccf,stroke:#333,stroke-width:2px;
    style F fill:#ccf,stroke:#333,stroke-width:2px;
    style G fill:#ccf,stroke:#333,stroke-width:2px;
    style H fill:#ccf,stroke:#333,stroke-width:2px;
    style I fill:#ccf,stroke:#333,stroke-width:2px;
    style K fill:#f9f,stroke:#333,stroke-width:2px;

```

The following process flow graph visually represents the logic of the **dettonville.git_inventory.update_inventory** module, particularly when a remote Git repository is involved.

```mermaid
graph TD
    A[Start] --> B{Is 'inventory_repo_url' specified?};

    B -- Yes --> C[Clone and pull remote repository];
    C --> D[Apply inventory node updates - groups, hosts, and vars];
    D --> E[Commit and push inventory changes];
    E --> F{Remove or keep temporary directory?};
    F -- Remove --> G[End];
    F -- Keep --> G[End];

    B -- No --> H[Apply inventory node updates locally - no git operations];
    H --> G[End];

%% Style definitions below, ensure there's a blank line before them
style A fill:#f9f,stroke:#333,stroke-width:2px;
style G fill:#f9f,stroke:#333,stroke-width:2px;
```

To summarize:

- **Start/End**: The beginning and end of the module's execution.

- **Is 'inventory_repo_url' specified?**: This is the key decision point.

    Yes: If a remote repository is provided, the module proceeds with Git operations.
    
    No: If no remote repository is specified, the module only performs local inventory updates.

- **Clone and pull remote repository**: The first step when a remote repo is used.

- **Apply inventory node updates (groups/hosts/vars)**: This is where the actual inventory modifications happen, whether locally or after cloning.

- **Commit and push inventory changes**: If a remote repo is used, these changes are pushed back.

- **Remove or keep temporary directory?**: The final step for remote repo operations, based on user preference.

- **Apply inventory node updates locally (no git operations)**: This path is taken when no remote repository is specified, meaning updates are only applied to the local inventory files.

### Other useful information

All three modules simply wrap and expose the features of the module_utils **GitInventoryUpdater** class instance.

The features supported by the **dettonville.git_inventory.update_inventory** module are a superset of the features supported by the host and group modules.

Put simply, one can implement the **dettonville.git_inventory.update_inventory** module to support both host and group use cases.

## Detailed test / use case examples

The integration tests performed regularly on the main branch demonstrate the use case examples supported by the **module**.

A short/brief description overview of the [tested use cases can be found here](https://github.com/dettonville/ansible-test-automation/blob/main/tests/dettonville/git_inventory/main/README.md#testuse-case-example-index).

A summary table summary of test results for [each module/filter can be found here](https://github.com/dettonville/ansible-test-automation/blob/main/tests/dettonville/git_inventory/main/test-results.md).

## Requirements

The host running the tasks must have the python requirements described in [requirements.txt](https://github.com/dettonville/ansible-git-inventory/blob/main/requirements.txt)
Once the collection is installed, you can install them into a python environment using pip: `pip install -r ~/.ansible/collections/ansible_collections/dettonville/git_inventory/requirements.txt`

<!--start requires_ansible-->
## Ansible version compatibility

This collection has been tested against following Ansible versions: **>=2.16.0**.

Plugins and modules within a collection may be tested with only specific Ansible versions.
A collection may contain metadata that identifies these versions.
PEP440 is the schema used to describe the versions of Ansible.
<!--end requires_ansible-->

## Included content

<!--start collection content-->

### Modules

Name | Description
--- | ---
[update_inventory](https://github.com/dettonville/ansible-git-inventory/blob/main/plugins/modules/update_inventory.py) | Add groups and/or hosts to git inventory repository.
[update_groups](https://github.com/dettonville/ansible-git-inventory/blob/main/plugins/modules/update_groups.py) | Add groups to git inventory repository.
[update_hosts](https://github.com/dettonville/ansible-git-inventory/blob/main/plugins/modules/update_hosts.py) | Add hosts to git inventory repository.

<!--end collection content-->

## Installing this collection

You can install the ``dettonville.git_inventory`` collection with the Ansible Galaxy CLI:

    ansible-galaxy collection install dettonville.git_inventory

You can also include it in a `requirements.yml` file and install it with `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: dettonville.git_inventory
```
## Using this collection

A comprehensive set of [tested use cases/examples can be found here.](https://github.com/dettonville/ansible-test-automation/blob/main/tests/dettonville/git_inventory/main/README.md#testuse-case-example-index).


### See Also:

* [Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) in the Ansible documentation for more details.

## Contributing to this collection

This collection is intended for plugins that are not platform or discipline specific. Simple plugin examples should be generic in nature. More complex examples can include real world platform modules to demonstrate the utility of the plugin in a playbook.

We welcome community contributions to this collection. If you find problems, please open an issue or create a PR against the [dettonville.git_inventory collection repository](https://github.com/dettonville/ansible-git-inventory). See [Contributing to Ansible-maintained collections](https://docs.ansible.com/ansible/devel/community/contributing_maintained_collections.html#contributing-maintained-collections) for complete details.

See the [Ansible Community Guide](https://docs.ansible.com/ansible/latest/community/index.html) for details on contributing to Ansible.


## Testing

All releases will meet the following test criteria.

* 100% success for [Integration](https://github.com/dettonville/ansible-git-inventory/blob/main/tests/integration) tests.
* 100% success for [Unit](https://github.com/dettonville/ansible-git-inventory/blob/main/tests/unit) tests.
* 100% success for [Sanity](https://docs.ansible.com/ansible/latest/dev_guide/testing/sanity/index.html#all-sanity-tests) tests as part of [ansible-test](https://docs.ansible.com/ansible/latest/dev_guide/testing.html#run-sanity-tests).
* 100% success for [ansible-lint](https://ansible.readthedocs.io/projects/lint/) allowing only false positives.

### Developer notes

- 100% code coverage is the goal, although it's not always possible. Please include unit and integration tests with all PRs. PRs should not cause a decrease in code coverage.
- Filter plugins should be 1 per file, with an included DOCUMENTATION string, or reference a lookup plugin with the same name.
- This collection should not depend on other collections for imported code
- Use of the latest version of black is required for formatting (black -l79)
- The README contains a table of plugins. Use the [collection_prep](https://github.com/ansible-network/collection_prep) utilities to maintain this.


### Code of Conduct
This collection follows the Ansible project's
[Code of Conduct](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html).
Please read and familiarize yourself with this document.


## Release notes
<!--Add a link to a changelog.md file or an external docsite to cover this information. -->
Release notes are available [here](https://github.com/dettonville/ansible-git-inventory/blob/main/changelogs/CHANGELOG.rst)
For automated release announcements refer [here](https://twitter.com/AnsibleContent).


## Roadmap
For information on releasing, versioning and deprecation see the [stratergy document](https://access.redhat.com/articles/4993781).

In general, major versions can contain breaking changes, while minor versions only contain new features (like new plugin addition) and bugfixes.
The releases will be done on an as-needed basis when new features and/or bugfixes are done.

<!-- Optional. Include the roadmap for this collection, and the proposed release/versioning strategy so users can anticipate the upgrade/update cycle. -->

## More information

- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)
