# Information Analyzer assets

[<- Back to the overview](../README.md)

## Exports

The export will be generate an XML file that could be separately processed through the Information Analyzer REST API.

```yml
export:
  infoanalyzer:
    - to: <path>
      project: <string>
      objects:
        - type: data_rule_definition
          changes_in_last_hours: <int>
          conditions:
            - { property: "<string>", operator: "<string>", value: "<value>" }
            - ...
        - type: data_rule_set_definition
          changes_in_last_hours: <int>
          conditions:
            - { property: "<string>", operator: "<string>", value: "<value>" }
            - ...
        - type: data_rule
          changes_in_last_hours: <int>
          conditions:
            - { property: "<string>", operator: "<string>", value: "<value>" }
            - ...
        - type: data_rule_set
          changes_in_last_hours: <int>
          conditions:
            - { property: "<string>", operator: "<string>", value: "<value>" }
            - ...
        - type: metric
          changes_in_last_hours: <int>
          conditions:
            - { property: "<string>", operator: "<string>", value: "<value>" }
            - ...
```

Objects that can be conditionally exported include `data_rule_definition`, `data_rule_set_definition`, `data_rule`, `data_rule_set`, and `metric`. Other objects within the project (virtual tables, virtual columns, folders, etc) are all always included in the export.

[`conditions`](conditions.md) are purely optional and are currently always AND'd (all conditions must be met). The conditions should be relative to the object `type` specified.

`changes_in_last_hours` is also optional; if used, specify the number of hours prior to the playbook running from which to identify (and extract) any changes. For executable objects (`data_rule`, `data_rule_set` and `metric`), any execution of those rules within the the time defined will also be included.

## Imports

```yml
import:
  infoanalyzer:
    - from: <path>
      project: <string>
      map: <list>
    - ...
```

Mappings are purely optional, and the only required parameters for the import are the file `from` which to load the assets and the `project` name into which to load them. If provided, mappings should use the [Information Analyzer style](mappings.md#information-analyzer-style).

## Examples

```yml
export:
  infoanalyzer:
    - to: cache/ia_fullproject.xml
      project: UGDefaultWorkspace
      objects:
        - type: data_rule_definition
        - type: data_rule_set_definition
        - type: data_rule
        - type: data_rule_set
        - type: metric
    - to: cache/ia_project_delta.xml
      project: UGDefaultWorkspace
      objects:
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
      project: UGDefaultWorkspace
      map: "{{ ia_mappings }}"
```

[<- Back to the overview](../README.md)
