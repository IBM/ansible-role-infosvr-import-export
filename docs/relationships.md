# IGC metadata relationships

[<- Back to the overview](../README.md)

## Exports

The export will be generate a JSON file that can currently only be loaded through the `ingest` action of this Ansible role.

```yml
export:
  relationships:
    - into: <path>
      from_type: <string>
      via_properties:
        - <string>
        - ...
      limited_to:
        only_with_conditions:
          - { property: "<string>", operator: "<string>", value: "<value>" }
          - ...
        changes_in_last_hours: <int>
        only_including_related_types:
          - <string>
          - ...
    - ...
```

The `into`, `from_type` and `via_properties` are required:

- `into` defines the file to which to extract the relationships
- `from_type` defines the type of asset for which to extract relationships
- `via_properties` defines one or more relationship properties to extract

For the names of the `from_type`s and their `via_properties` relationship properties, check the REST API type documentation for your release at: https://github.com/IBM/node-igc-rest/tree/master/doc

The options under `limited_to` are all optional:

- `only_with_conditions` defines [conditions](conditions.md) that are currently always AND'd (all conditions must be met) and are relative to the `from_type` specified.
- `changes_in_last_hours` specifies the number of hours prior to the playbook running from which to identify (and extract) any changes.
- `only_including_related_types` provides a list of the related asset types to retain as relationships.

Be aware that all relationships in IGC are bi-directional, so it is usually possible to achieve the extraction of the same relationship in two different ways (depending on the `from_type` and `via_properties` used). For example, the `assigned_assets` on a `term` is also represented by the `assigned_to_terms` on a `database_column`, `database_table`, `data_file_field`, etc. Depending on the intended ingest mode (see below), one of the directions may be significantly more efficient to load than the other.

## Merges

```yml
merge:
  relationships:
    - into: <path>
      from:
        - <path>
        - ...
      with_options:
        transformed_by: <list>
    - ...
```

The required parameters for the merge are the file `into` which to store the merged results and the list of files `from` which to do the merging.

The options under `with_options` are all optional:

- `transformed_by` specifies a list of mappings that can be used to transform the relationships; if provided, they should use the [REST style](mappings.md#rest-style).

It is important to remember:

- if you are applying transformations to the ingest, you will want to apply those same transformations to the merge: in order to ensure that the merge is done correctly (post-transformation, rather than pre-transformation)
- since ingest works optimally against a single relationship property at a time, be aware of whether the files you are merging all use the same relationship property or could result in a merged file with multiple relationship properties

## Ingests

```yml
ingest:
  relationships:
    - from: <path>
      using_mode: <string>
      with_options:
        transformed_by: <list>
        replacing_type: <string>
        only_with_conditions:
          - { property: "<string>", operator: "<string>", value: "<value>" }
          - ...
    - ...
```

The required parameters for the ingest are the file `from` which to load them and the `using_mode` to use when loading them.

The `using_mode` must be one of the following:

- `APPEND` - only add these relationships to the asset, don't change any existing relationships. (If the relationship already exists it will simply be retained, not duplicated.)
- `REPLACE_ALL` - replace all relationships on the assets in the file with the relationship properties included in the file.
- `REPLACE_SOME` - replace only a portion of the relationships. For this option, you must additionally specify at least the `with_options.replace_type`, giving a REST API asset type specifying the related asset types you want to replace.

The options under `with_options` are all optional:

- `transformed_by` specifies a list of mappings that can be used to transform the relationships; if provided, they should use the [REST style](mappings.md#rest-style).
- `replacing_type` limits the type of asset that should be replaced when using `REPLACE_SOME`.
- `only_with_conditions` further limits the assets that are replaced when using `REPLACE_SOME`.

For example, if you specify `database_column` as the `with_options.replacing_type`, and `with_options.only_with_conditions` of `name = XYZ` the ingest will only replace related database columns where the name of the database column is XYZ and leave all other relationships alone.

As noted above in the export, be aware of your intended ingest mode. It will be more efficient to export relationships in one direction (eg. `assigned_to_terms` from `database_column`) and use `REPLACE_ALL` then it is to use `REPLACE_SOME` (eg. with `assigned_assets` from `term`).

The intestion will attempt to automatically optimise, to use a batch import mechanism when possible. This is generally only possible for certain relationships, only when the `using_mode` is not `REPLACE_SOME`, when there is only a single relationship property in the file, and when there are no custom relationship properties involved.

## Examples

```yml
export:
  relationships:
    - into: cache/terms2assets_underSomeCategory_changed_in_last48hrs_only_dbcols.json
      from_type: term
      via_properties:
        - assigned_assets
      limited_to:
        changes_in_last_hours: 48
        only_with_conditions:
          - { property: "category_path._id", operator: "=", value: "6662c0f2.ee6a64fe.ko15n9ej3.cq2arq8.ld2q5u.2qonhvupr4m3b68ouj93c" }
        only_including_related_types:
          - database_column
    - into: cache/same_as_above_but_more_efficient_to_import.json
      from_type: database_column
      via_properties:
        - assigned_to_terms
      limited_to:
        changes_in_last_hours: 48
        only_with_conditions:
          - { property: "assigned_to_terms.category_path._id", operator: "=", value: "6662c0f2.ee6a64fe.ko15n9ej3.cq2arq8.ld2q5u.2qonhvupr4m3b68ouj93c" }

rest_mappings:
  - { type: "host", property: "name", from: "MY", to: "YOUR" }

merge:
  relationships:
    - into: cache/merged_terms2assets.json
      from:
        - cache/terms2assets_underSomeCategory_changed_in_last48hrs_only_dbcols.json
        - cache/terms2assets_someOtherFile.json
      with_options:
        transformed_by: "{{ rest_mappings }}"

ingest:
  relationships:
    - from: cache/terms2assets_underSomeCategory_changed_in_last48hrs_only_dbcols.json
      using_mode: REPLACE_SOME
      with_options:
        transformed_by: "{{ rest_mappings }}"
        replacing_type: database_column
        only_with_conditions:
          - { property: "database_table_or_view.name", operator: "=", value: "MYTABLE" }
    - from: cache/same_as_above_but_more_efficient_to_import.json
      using_mode: REPLACE_ALL
      with_options:
        transformed_by: "{{ rest_mappings }}"
    - from: cache/merged_terms2assets.json
      using_mode: REPLACE_SOME
      with_options:
        transformed_by: "{{ rest_mappings }}"
        replacing_type: database_column
        only_with_conditions:
          - { property: "database_table_or_view.name", operator: "=", value: "MYTABLE" }
```

[<- Back to the overview](../README.md)
