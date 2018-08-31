# Database metadata

[<- Back to the overview](../README.md)

**Note**: database metadata export and import should really only be used when you need to load metadata into an environment where that environment will not have access to the source database itself.  When possible, it will be more robust to directly load the metadata through IBM Metadata Asset Manager, which can be automated through the [IBM.infosvr-metadata-asset-manager](https://galaxy.ansible.com/IBM/infosvr-metadata-asset-manager) role.  IBM Metadata Asset Manager will ensure that accurate metadata is recorded, and can be periodically refreshed (re-imported) to be kept up-to-date, including staging potentially destructive changes for review.  The re-importing is handled automatically as part of the [IBM.infosvr-metadata-asset-manager](https://galaxy.ansible.com/IBM/infosvr-metadata-asset-manager) role, so can also be automated (and will warn if there is a potentially destructive change that has been stage and requires review before it can be published).

## Exports

The export will be generate an ISX file that could be separately processed through the `istool` command-line.

```yml
export:
  database:
    - to: <path>
      type: <string>
      changes_in_last_hours: <int>
      conditions:
        - { property: "<string>", operator: "<string>", value: "<value>" }
        - ...
    - ...
```

Only the `to` and `type` are required, and the `type` must be one of: `database` or `database_schema`.

[`conditions`](conditions.md) are purely optional and are currently always AND'd (all conditions must be met). The conditions should be relative to the top-level object `type` specified.

`changes_in_last_hours` is also optional; if used, specify the number of hours prior to the playbook running from which to identify (and extract) any changes. (Changes to sub-objects of the specified `type` -- its contained tables, views, stored procedures, and columns -- will automatically be checked for changes as well.)

## Imports

```yml
import:
  database:
    - from: <path>
      options: <string>
      map: <list>
      overwrite: <boolean>
    - ...
```

Mappings are purely optional, and the only required parameter for the import is the file `from` which to load them. If provided, mappings should use the [ISX style](mappings.md#isx-style).

Available `options` are:

- `-allowDuplicates`: Allows import when duplicates exists in the imported metadata or when imported metadata matches duplicate objects in the repository.

## Examples

```yml
export:
  database:
    - to: cache/db_schemas_changed_in_last_2_days.isx
      type: database_schema
      changes_in_last_hours: 48
      conditions:
        - { property: "database.host.name", operator: "=", value: "MYHOST.SOMEWHERE.COM" }

isx_mappings:
  - { type: "HostSystem", attr: "name", from: "MY_HOST", to: "YOUR_HOST" }

import:
  database:
    - from: db_schemas_changed_in_last_2_days.isx
      map: "{{ isx_mappings }}"
      overwrite: True
```

[<- Back to the overview](../README.md)
