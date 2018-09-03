# Information Analyzer assets

[<- Back to the overview](../README.md)

## Exports

The export will be generate an XML file that could be separately processed through the Information Analyzer REST API.

```yml
export:
  infoanalyzer:
    - into: <path>
      from_project: <string>
      including_objects:
        - type: data_rule_definition
          changes_in_last_hours: <int>
          only_with_conditions:
            - { property: "<string>", operator: "<string>", value: "<value>" }
            - ...
        - type: data_rule_set_definition
          changes_in_last_hours: <int>
          only_with_conditions:
            - { property: "<string>", operator: "<string>", value: "<value>" }
            - ...
        - type: data_rule
          changes_in_last_hours: <int>
          only_with_conditions:
            - { property: "<string>", operator: "<string>", value: "<value>" }
            - ...
        - type: data_rule_set
          changes_in_last_hours: <int>
          only_with_conditions:
            - { property: "<string>", operator: "<string>", value: "<value>" }
            - ...
        - type: metric
          changes_in_last_hours: <int>
          only_with_conditions:
            - { property: "<string>", operator: "<string>", value: "<value>" }
            - ...
```

Objects that can be conditionally exported include `data_rule_definition`, `data_rule_set_definition`, `data_rule`, `data_rule_set`, and `metric`. Other objects within the project (virtual tables, virtual columns, folders, etc) are all always included in the export.

- `only_with_conditions` are purely optional and are currently always AND'd (all conditions must be met). The [conditions](conditions.md) should be relative to the object `type` specified.
- `changes_in_last_hours` is also optional; if used, specify the number of hours prior to the playbook running from which to identify (and extract) any changes. For executable objects (`data_rule`, `data_rule_set` and `metric`), any execution of those rules within the the time defined will also be included.

## Imports

```yml
import:
  infoanalyzer:
    - from: <path>
      into_project: <string>
      with_options:
        transformed_by: <list>
    - ...
```

The required parameters for the import are the file `from` which to load the assets and the `into_project` project name into which to load them.

The options under `with_options` are all optional:

- `transformed_by` specifies a list of mappings that can be used to transform the assets; if provided, mappings should use the [Information Analyzer style](mappings.md#information-analyzer-style).

## Examples

```yml
export:
  infoanalyzer:
    - into: cache/ia_fullproject.xml
      from_project: UGDefaultWorkspace
      including_objects:
        - type: data_rule_definition
        - type: data_rule_set_definition
        - type: data_rule
        - type: data_rule_set
        - type: metric
    - into: cache/ia_project_delta.xml
      from_project: UGDefaultWorkspace
      including_objects:
        - type: data_rule_definition
          changes_in_last_hours: 48
        - type: data_rule_set_definition
          changes_in_last_hours: 48
        - type: data_rule
          changes_in_last_hours: 48
        - type: data_rule_set
          changes_in_last_hours: 48
        - type: metric
          changes_in_last_hours: 48

ia_mappings:
  - { type: "DataSource", attr: "host", from: "MY_HOST", to: "YOUR_HOST" }
  - { type: "DataSource", attr: "name", from: "MYDB", to: "YOURDB" }
  - { type: "Schema", attr: "name", from: "MY_SCH", to: "YOUR_SCH" }

import:
  infoanalyzer:
    - from: cache/ia_project_delta.xml
      into_project: UGDefaultWorkspace
      with_options:
        transformed_by: "{{ ia_mappings }}"
```

[<- Back to the overview](../README.md)
