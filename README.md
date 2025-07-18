
[![ansible-test sanity](https://github.com/dettonville/ansible-git-inventory/actions/workflows/ansible-test-sanity.yml/badge.svg)](https://github.com/dettonville/ansible-git-inventory/actions/workflows/ansible-test-sanity.yml)
[![ansible-lint](https://github.com/dettonville/ansible-git-inventory/actions/workflows/ansible-lint.yml/badge.svg)](https://github.com/dettonville/ansible-git-inventory/actions/workflows/ansible-lint.yml)
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg?style=flat)](LICENSE.md)

# Dettonville Ansible Git Inventory Collection

The Ansible ``dettonville.git_inventory`` collection includes modules to add, update, and/or remove group and/or host nodes to a specified inventory repository.

The modules (update_inventory, update_groups, and update_hosts):
1) utilize the module 'GitInventoryUpdater' module utility class instance to add, update, and/or remove group and/or host nodes and respective variables for a specified YAML-based inventory.
2) if a git repository is provided, the updater class will:
    - clone (to a temporary repo directory if not specified) and
    - commit and push the inventory changes to the specified inventory repo
    - and remove or keep the temporary directory as specified.


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

The most common use case for this collection is when you want to work with the complex data structures present in an Ansible playbook, inventory, or returned from modules. See each plugin documentation page for detailed examples for how these utilities can be used in tasks.


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
