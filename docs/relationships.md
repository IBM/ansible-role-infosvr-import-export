# IGC metadata relationships

[<- Back to the overview](../README.md)

## Exports

The export will be generate a JSON file that can currently only be loaded through the `import` action of this Ansible role.

```yml
export:
  relationships:
    - to: <path>
      changes_in_last_hours: <int>
      type: <string>
      relationship: <string>
      limit:
        - <string>
        - ...
      conditions:
        - { property: "<string>", operator: "<string>", value: "<value>" }
        - ...
    - ...
```

The `to`, `type` and `relationship` are required:

- `to` defines the file to which to extract the relationships
- `type` defines the type of asset for which to extract relationships
- `relationship` defines the relationship property to extract

For the names of the `type`s and their `relationship` properties, check the REST API type documentation for your release at: https://github.com/IBM/node-igc-rest/tree/master/doc

[`conditions`](conditions.md) are purely optional and are currently always AND'd (all conditions must be met). The conditions should be relative to the `type` specified.

`changes_in_last_hours` is also optional; if used, specify the number of hours prior to the playbook running from which to identify (and extract) any changes.

Finally, `limit` is also optional: when used it should provide a list of the related asset types to retain as relationships.

Be aware that all relationships in IGC are bi-directional, so it is usually possible to achieve the extraction of the same relationship in two different ways (depending on the `type` and `relationship` used). For example, the `assigned_assets` on a `term` is also represented by the `assigned_to_terms` on a `database_column`, `database_table`, `data_file_field`, etc. Depending on the intended import mode (see below), one of the directions may be significantly more efficient to load than the other.

## Imports

```yml
import:
  relationships:
    - from: <path>
      type: <string>
      relationship: <string>
      map: <list>
      mode: <string>
      replace_type: <string>
      conditions:
        - { property: "<string>", operator: "<string>", value: "<value>" }
        - ...
    - ...
```

The required parameters for the import are the file `from` which to load them, the `type` of the asset for which to load relationships, the `relationship` property to load and the `mode` to use when loading them.

Mappings are purely optional; if provided, they should use the [REST style](mappings.md#rest-style).

The `mode` must be one of the following:

- `APPEND` - only add these relationships to the asset, don't change any existing relationships. (If the relationship already exists it will simply be retained, not duplicated.)
- `REPLACE_ALL` - replace all relationships on the specified asset (`type`) and property (`relationship`) with the ones being loaded.
- `REPLACE_SOME` - replace only a portion of the relationships. For this option, you must additionally specify at least the `replace_type`, giving a REST API asset type specifying the related asset types you want to replace. You can also optionally provide a further list of `conditions` that apply to the `replace_type` asset. For example, if you specify `database_column` as the `replace_type`, and a condition of `name = XYZ` the import will only replace related database columns where the name of the database column is XYZ and leave all other relationships alone.

As noted above in the export, be aware of your intended import mode. It will be more efficient to export relationships in one direction (eg. `assigned_to_terms` from `database_column`) and use `REPLACE_ALL` then it is to use `REPLACE_SOME` (eg. with `assigned_assets` from `term`).

## Examples

```yml
export:
  relationships:
    - to: cache/terms2assets_underSomeCategory_changed_in_last48hrs_only_dbcols.json
      type: term
      relationship: assigned_assets
      changes_in_last_hours: 48
      limit:
        - database_column
      conditions:
        - { property: "category_path._id", operator: "=", value: "6662c0f2.ee6a64fe.ko15n9ej3.cq2arq8.ld2q5u.2qonhvupr4m3b68ouj93c" }
    - to: cache/same_as_above_but_more_efficient_to_import.json
      type: database_column
      relationship: assigned_to_terms
      changes_in_last_hours: 48
      conditions:
        - { property: "assigned_to_terms.category_path._id", operator: "=", value: "6662c0f2.ee6a64fe.ko15n9ej3.cq2arq8.ld2q5u.2qonhvupr4m3b68ouj93c" }

rest_mappings:
  - { type: "host", property: "name", from: "MY", to: "YOUR" }

import:
  relationships:
    - from: cache/terms2assets_underSomeCategory_changed_in_last48hrs_only_dbcols.json
      type: term
      relationship: assigned_assets
      map: "{{ rest_mappings }}"
      mode: REPLACE_SOME
      replace_type: database_column
      conditions:
        - { property: "database_table_or_view.name", operator: "=", value: "MYTABLE" }
    - from: cache/same_as_above_but_more_efficient_to_import.json
      type: database_column
      relationship: assigned_to_terms
      map: "{{ rest_mappings }}"
      mode: REPLACE_ALL
```

[<- Back to the overview](../README.md)
