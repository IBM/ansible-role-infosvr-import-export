# Extended data sources

[<- Back to the overview](../README.md)

## Exports

The export will be generate a CSV file that could be separately processed through the `istool` command-line or uploaded via the IGC web user interface.

```yml
export:
  extendedsource:
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

In addition to the file `into` which to extract the assets, at least one `type` should be specified under `including_objects`. Each `type` must be one of `application`, `file`, or `stored_procedure_definition`.

- `only_with_conditions` are purely optional and are currently always AND'd (all conditions must be met). Any [conditions](conditions.md) specified should be within the context of the specified asset `type`, and must currently be common amongst all sub-types of that type (eg. `name`, `short_description`, `assigned_to_terms`, etc).
- `changes_in_last_hours` is also optional; if used, specify the number of hours prior to the playbook running from which to identify (and extract) any changes of the specified `type`. When using change-detection, the export automatically looks for any changes to sub-objects of these (eg. any changed `method`s for `application`), but will always extract the full outer containment object. For example, if only one `method` of an `application` has changed, it will still extract the entire `application` with all of its `method`s and other sub-objects.

## Ingests

```yml
ingest:
  extendedsource:
    - from: <path>
      with_options:
        overwrite: <boolean>
    - ...
```

The only required parameter for the ingest is the file `from` which to load them.

The options under `with_options` are all optional:

- `overwrite` specifies whether to overwrite any existing assets with the same identities.

## Examples

```yml
export:
  extendedsource:
    - into: cache/xa_apps_changed_in_last48hrs.csv
      including_objects:
        type: application
        changes_in_last_hours: 48
    - into: cache/xa_files_changed_in_last48hrs.csv
      including_objects:
        type: file
        changes_in_last_hours: 48
    - into: cache/xa_sprocs_changed_in_last48hrs.csv
      including_objects:
        type: stored_procedure_definition
        changes_in_last_hours: 48

ingest:
  extendedsource:
    - from: cache/xa_apps_changed_in_last48hrs.csv
      with_options:
        overwrite: True
    - from: cache/xa_files_changed_in_last48hrs.csv
      with_options:
        overwrite: True
    - from: cache/xa_sprocs_changed_in_last48hrs.csv
      with_options:
        overwrite: True
```

[<- Back to the overview](../README.md)
