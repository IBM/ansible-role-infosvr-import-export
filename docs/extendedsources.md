# Extended data sources

[<- Back to the overview](../README.md)

## Exports

The export will be generate a CSV file that could be separately processed through the `istool` command-line or uploaded via the IGC web user interface.

```yml
export:
  extendedsources:
    - to: <path>
      changes_in_last_hours: <int>
      type: <string>
      conditions:
        - { property: "<string>", operator: "<string>", value: "<value>" }
        - ...
    - ...
```

The `type` is required, and must be one of `application`, `file`, or `stored_procedure_definition`. 

[`conditions`](conditions.md) are purely optional and are currently always AND'd (all conditions must be met). Furthermore, they must currently be common amongst all sub-types of the extended data source objects (eg. `name`, `short_description`, `assigned_to_terms`, etc).

`changes_in_last_hours` is also optional; if used, specify the number of hours prior to the playbook running from which to identify (and extract) any changes. When using change-detection, the export automatically looks for any changes to sub-objects of these (eg. any changed `method`s for `application`), but will always extract the full outer containment object. For example, if only one `method` of an `application` has changed, it will still extract the entire `application` with all of its `method`s and other sub-objects.

## Imports

```yml
import:
  extendedsources:
    - from: <path>
      overwrite: <boolean>
    - ...
```

The only required parameter for the import is the file `from` which to load the assets.

## Examples

```yml
export:
  extendedsources:
    - to: cache/xa_apps_changed_in_last48hrs.csv
      changes_in_last_hours: 48
      type: application
    - to: cache/xa_files_changed_in_last48hrs.csv
      changes_in_last_hours: 48
      type: file
    - dest: cache/xa_sprocs_changed_in_last48hrs.csv
      changes_in_last_hours: 48
      type: stored_procedure_definition

import:
  extendedsources:
    - from: cache/xa_apps_changed_in_last48hrs.csv
      overwrite: True
    - from: cache/xa_files_changed_in_last48hrs.csv
      overwrite: True
    - from: cache/xa_sprocs_changed_in_last48hrs.csv
      overwrite: True
```

[<- Back to the overview](../README.md)
