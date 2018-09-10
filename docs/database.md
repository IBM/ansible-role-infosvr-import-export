# Database metadata

[<- Back to the overview](../README.md)

**Note**: database metadata export and ingest should really only be used when you need to load metadata into an environment where that environment will not have access to the source database itself.  When possible, it will be more robust to directly load the metadata through IBM Metadata Asset Manager, which can be automated through the [IBM.infosvr-metadata-asset-manager](https://galaxy.ansible.com/IBM/infosvr-metadata-asset-manager) role.  IBM Metadata Asset Manager will ensure that accurate metadata is recorded, and can be periodically refreshed (re-ingested) to be kept up-to-date, including staging potentially destructive changes for review.  The re-ingesting is handled automatically as part of the [IBM.infosvr-metadata-asset-manager](https://galaxy.ansible.com/IBM/infosvr-metadata-asset-manager) role, so can also be automated (and will warn if there is a potentially destructive change that has been stage and requires review before it can be published).

## Exports

The export will be generate an ISX file that could be separately processed through the `istool` command-line.

```yml
export:
  database:
    - into: <path>
      including_objects:
        - type: <string>
          changes_in_last_hours: <int>
          only_with_conditions:
            - { property: "<string>", operator: "<string>", value: "<value>" }
            - ...
        - ...
    - ...
```

In addition to the file `into` which to extract the assets, at least one `type` should be specified under `including_objects`. Each `type` must be one of `database` or `database_schema`.

- `only_with_conditions` are purely optional and are currently always AND'd (all conditions must be met). Any [conditions](conditions.md) specified should be within the context of the specified asset `type`.
- `changes_in_last_hours` is also optional; if used, specify the number of hours prior to the playbook running from which to identify (and extract) any changes of the specified `type`.

## Ingests

```yml
ingest:
  database:
    - from: <path>
      with_options:
        overwrite: <boolean>
        transformed_by: <list>
        args: <string>
    - ...
```

The only required parameter for the ingest is the file `from` which to load them.

The options under `with_options` are all optional:

- `overwrite` specifies whether to overwrite any existing assets with the same identities.
- `transformed_by` specifies a list of mappings that can be used to transform the assets; if provided, mappings should use the [ISX style](mappings.md#isx-style).
- `args` provides additional arguments to the export command; currently the following are possible:
  - `-allowDuplicates`: Allows import when duplicates exists in the imported metadata or when imported metadata matches duplicate objects in the repository.

## Examples

```yml
export:
  database:
    - into: cache/db_schemas_changed_in_last_2_days.isx
      including_objects:
        type: database_schema
        changes_in_last_hours: 48
        only_with_conditions:
          - { property: "database.host.name", operator: "=", value: "MYHOST.SOMEWHERE.COM" }

isx_mappings:
  - { type: "HostSystem", attr: "name", from: "MY_HOST", to: "YOUR_HOST" }

ingest:
  database:
    - from: db_schemas_changed_in_last_2_days.isx
      with_options:
        transformed_by: "{{ isx_mappings }}"
        overwrite: True
```

[<- Back to the overview](../README.md)
