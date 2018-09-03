# Data file metadata

[<- Back to the overview](../README.md)

**Note**: data file metadata export and import should really only be used when you need to load metadata into an environment where that environment will not have access to the source data file itself.  When possible, it will be more robust to directly load the metadata through IBM Metadata Asset Manager, which can be automated through the [IBM.infosvr-metadata-asset-manager](https://galaxy.ansible.com/IBM/infosvr-metadata-asset-manager) role.  IBM Metadata Asset Manager will ensure that accurate metadata is recorded, and can be periodically refreshed (re-imported) to be kept up-to-date, including staging potentially destructive changes for review.  The re-importing is handled automatically as part of the [IBM.infosvr-metadata-asset-manager](https://galaxy.ansible.com/IBM/infosvr-metadata-asset-manager) role, so can also be automated (and will warn if there is a potentially destructive change that has been stage and requires review before it can be published).

## Exports

The export will be generate an ISX file that could be separately processed through the `istool` command-line.

```yml
export:
  datafile:
    - into: <path>
      limited_to:
        changes_in_last_hours: <int>
        only_with_conditions:
          - { property: "<string>", operator: "<string>", value: "<value>" }
          - ...
    - ...
```

The options under `limited_to` are all optional:

- `only_with_conditions` defines [conditions](conditions.md) that are currently always AND'd (all conditions must be met). The conditions should be relative to the data_file asset type.
- `changes_in_last_hours` specifies the number of hours prior to the playbook running from which to identify (and extract) any changes. Changes to sub-objects of the data_file -- its contained data file records and data file fields -- will automatically be checked as well.

## Imports

```yml
import:
  datafile:
    - from: <path>
      with_options:
        overwrite: <boolean>
        transformed_by: <list>
        args: <string>
    - ...
```

The only required parameter for the import is the file `from` which to load them.

The options under `with_options` are all optional:

- `overwrite` specifies whether to overwrite any existing assets with the same identities.
- `transformed_by` specifies a list of mappings that can be used to transform the assets; if provided, mappings should use the [ISX style](mappings.md#isx-style).
- `args` provides additional arguments to the export command; currently the following are possible:
  - `-allowDuplicates`: Allows import when duplicates exists in the imported metadata or when imported metadata matches duplicate objects in the repository.

## Examples

```yml
export:
  datafile:
    - into: cache/files_changed_in_last_2_days.isx
      limited_to:
        changes_in_last_hours: 48
        only_with_conditions:
          - { property: "host.name", operator: "=", value: "MYHOST.SOMEWHERE.COM" }
          - { property: "name", operator: "=", value: "/" }

isx_mappings:
  - { type: "HostSystem", attr: "name", from: "MY_HOST", to: "YOUR_HOST" }

import:
  datafile:
    - from: cache/files_changed_in_last_2_days.isx
      with_options:
        transformed_by: "{{ isx_mappings }}"
        overwrite: True
```

[<- Back to the overview](../README.md)
