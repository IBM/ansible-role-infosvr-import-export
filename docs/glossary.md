# Glossary assets

[<- Back to the overview](../README.md)

## Exports

The export will be generate an XML file that could be separately loaded through the `istool` command-line or the IGC web user interface.

```yml
export:
  glossary:
    - into: <path>
      limited_to_categories: <string>
      with_options: <string>
      including_objects:
        - type: <string>
          changes_in_last_hours: <int>
          only_with_conditions:
            - { property: "<string>", operator: "<string>", value: "<value>" }
            - ...
        - ...
    - ...
```

The required parameters for an export are the file `into` which to extract and one or more `type` of assets to export (under `including_objects`). `type` must be one of `category`, `term`, `information_governance_policy`, `information_governance_rule`, or `label`.

- `only_with_conditions` are purely optional and are currently always AND'd (all conditions must be met). The [conditions](conditions.md) should be relative to the object `type` specified.
- `changes_in_last_hours` is also optional; if used, specify the number of hours prior to the playbook running from which to identify (and extract) any changes for that object `type`.

Because of the way the export for these assets works, you may be able to improve the efficiency by using the optional `limited_to_categories` limiter. This will not be considered in coordination with the `only_with_conditions`, so should be used only for optimisation purposes: to limit the amount of content exported. You can specify multiple categories as comma-separated in the `limited_to_categories` string. The path separator for categories is `::`. (Leaving this option out will export all categories initially, and later restrict these based on the `type`s and `only_with_conditions` specified by the other options.)

Options available for the `with_options` (which is itself optional) are:

- `-includeassignedassets`: Include links to assigned assets.
- `-includestewardship`: Include stewardship links.
- `-includeassetcollections`: Include Asset Collection links.
- `-includelabeledassets`: Include Labeled Asset links.
- `-devglossary`: Export the development glossary.

When specifying multiple options, simply include them separated by spaces.

## Ingests

```yml
ingest:
  glossary:
    - from: <path>
      merged_by: <string>
      with_options:
        transformed_by: <list>
  - ...
```

Mappings are purely optional, and the only required parameter for the ingest is the file `from` which to load them and the `merged_by` option. The `merged_by` option must be one of `ignore`, `overwrite`, `mergeignore`, or `mergeoverwrite`.

The options under `with_options` are all optional:

- `transformed_by` specifies a list of mappings that can be used to transform the relationships; if provided, they should use the [ISX style](mappings.md#isx-style).

The order of ingesting is also important for glossary assets, since different asset types can be split across different XML files. You should always ingest in this order to ensure dependencies are met (will be done automatically if they are all included in a single export):

1. `label`
1. `category`
1. `term`
1. `information_governance_policy`
1. `information_governance_rule`

## Examples

```yml
export:
  glossary:
    - into: cache/bg_all_terms.xml
      with_options: "-includeassignedassets -includestewardship -includeassetcollections -includelabeledassets -devglossary"
      including_objects:
        - type: term
    - into: cache/bg_all_rules.xml
      with_options: "-includeassignedassets -includestewardship"
      including_objects:
        - type: information_governance_rule
    - into: cache/bg_some.xml
      with_options: "-includelabeledassets -includetermhistory"
      limited_to_categories: "Samples::A,Inspiration::Others"
      including_objects:
        - type: term
          changes_in_last_hours: 48
          only_with_conditions:
            - { property: "label.name", operator: "=", value: "Public" }
        - type: information_governance_rule
          changes_in_last_hours: 48

isx_mappings:
  - { type: "HostSystem", attr: "name", from: "MY_HOST", to: "YOUR_HOST" }

ingest:
  glossary:
    - from: cache/bg_all_terms.xml
      merged_by: mergeoverwrite
      with_options:
        transformed_by: "{{ isx_mappings }}"
    - from: cache/bg_all_rules.xml
      merged_by: mergeoverwrite
      with_options:
        transformed_by: "{{ isx_mappings }}"
    - from: cache/bg_some.xml
      merged_by: mergeoverwrite
      with_options:
        transformed_by: "{{ isx_mappings }}"
```

[<- Back to the overview](../README.md)
