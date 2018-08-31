# Glossary assets

[<- Back to the overview](../README.md)

## Exports

The export will be generate an XML file that could be separately loaded through the `istool` command-line or the IGC web user interface.

```yml
export:
  glossary:
    - to: <path>
      categories: <string>
      options: <string>
      objects:
        - type: <string>
          changes_in_last_hours: <int>
          conditions:
            - { property: "<string>", operator: "<string>", value: "<value>" }
            - ...
        - ...
    - ...
```

The required parameters for an export are the file `to` which to extract and one or more `type` of assets to export (under `object`). `type` must be one of `category`, `term`, `information_governance_policy`, `information_governance_rule`, or `label`.

[`conditions`](conditions.md) are purely optional and are currently always AND'd (all conditions must be met). The conditions should be relative to the object `type` specified.

`changes_in_last_hours` is also optional; if used, specify the number of hours prior to the playbook running from which to identify (and extract) any changes for that object `type`.

Because of the way the export for these assets works, you may be able to improve the efficiency by using the optional `categories` limiter. This will not be considered in coordination with the `conditions`, so should be used only for optimisation purposes: to limit the amount of content exported. You can specify multiple categories as comma-separated in the `categories` string. The path separator for categories is `::`. (Leaving this option out will export all categories initially, and later restrict these based on the `type`s and `conditions` specified by the other options.)

Available `options` are:

- `-includeassignedassets`: Include links to assigned assets.
- `-includestewardship`: Include stewardship links.
- `-includeassetcollections`: Include Asset Collection links.
- `-includelabeledassets`: Include Labeled Asset links.
- `-devglossary`: Export the development glossary.

When specifying multiple options, simply include them separated by spaces.

## Imports

```yml
import:
  glossary:
    - from: <path>
      map: <list>
      merge: <string>
  - ...
```

Mappings are purely optional, and the only required parameter for the import is the file `from` which to load them and the `merge` option. If provided, mappings should use the [ISX style](mappings.md#isx-style). The `merge` option must be one of `ignore`, `overwrite`, `mergeignore`, or `mergeoverwrite`.

The order of importing is also important for glossary assets, since different asset types can be split across different XML files. You should always import in this order to ensure dependencies are met (will be done automatically if they are all included in a single export):

1. `label`
1. `category`
1. `term`
1. `information_governance_policy`
1. `information_governance_rule`

## Examples

```yml
export:
  glossary:
    - to: cache/bg_all_terms.xml
      options: "-includeassignedassets -includestewardship -includeassetcollections -includelabeledassets -devglossary"
      objects:
        - type: term
    - to: cache/bg_all_rules.xml
      options: "-includeassignedassets -includestewardship"
      objects:
        - type: information_governance_rule
    - to: cache/bg_some.xml
      options: "-includelabeledassets -includetermhistory"
      categories: "Samples::A,Inspiration::Others"
      objects:
        - type: term
          changes_in_last_hours: 48
          conditions:
            - { property: "label.name", operator: "=", value: "Public" }
        - type: information_governance_rule
          changes_in_last_hours: 48

isx_mappings:
  - { type: "HostSystem", attr: "name", from: "MY_HOST", to: "YOUR_HOST" }

import:
  glossary:
    - from: cache/bg_all_terms.xml
      map: "{{ isx_mappings }}"
      merge: mergeoverwrite
    - from: cache/bg_all_rules.xml
      map: "{{ isx_mappings }}"
      merge: mergeoverwrite
    - from: cache/bg_some.xml
      map: "{{ isx_mappings }}"
      merge: mergeoverwrite
```

[<- Back to the overview](../README.md)
