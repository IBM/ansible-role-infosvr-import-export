# OpenIGC bundles and assets

[<- Back to the overview](../README.md)

## Exports

The export will be generate a ZIP file for each bundle, and an XML file for all assets in that bundle, each of which that could be separately processed through the IGC REST API.

```yml
export:
  openigc:
    bundles:
      - name: <string>
        into: <path>
      - ...
    assets:
      - from_bundle: <string>
        into: <path>
        limited_to:
          changes_in_last_hours: <int>
          only_with_conditions:
            - { property: "<string>", operator: "<string>", value: "<value>" }
            - ...
      - ...
```

The options under `limited_to` are all optional:

- `only_with_conditions` defines [conditions](conditions.md) that are currently always AND'd (all conditions must be met).
- `changes_in_last_hours` specifies the number of hours prior to the playbook running from which to identify (and extract) any changes.

Note that these exports will **not** contain any custom attribute definitions or values that have been created separately from the bundles themselves. These must be exported separately using the [customattrs](customattrs.md) and [relationships](relationships.md) directives (ie. for custom attributes of type relationship).

## Ingests

```yml
ingest:
  openigc:
    bundles:
      - from: <path>
      - ...
    assets:
      - from: <path>
        with_options:
          replace_types:
            - $<bundleId>-<class>
            - ...
      - ...
```

The required parameters for the ingest are simply the file `from` which to load the assets. For assets, you can also optionally specify the types that you would like to load as replacements under `with_options.replace_types`. Replacements will ensure that the assets of those types being loaded are a full replacement in the target environment -- any properties not in the file will be removed from the asset (if the asset exists) in the target environment.

Any types not listed here will be merged with any matching assets already in the target environment. (This includes merging not appending children to existing parents, but also merging attributes that may be missing in the file but are already present on the assets in the environment.)

## Examples

```yml
export:
  openigc:
    bundles:
      - name: JSON_Schema
        into: cache/igc-x-json_schema.zip
    assets:
      - from_bundle: JSON_Schema
        into: cache/igc-x-json_schema-assets.xml
        limited_to:
          changes_in_last_hours: 48
          only_with_conditions:
            - { property: "name", operator: "=", "MyJsonSchema" }

ingest:
  openigc:
    bundles:
      - from: cache/igc-x-json_schema.zip
    assets:
      - from: cache/igc-x-json_schema-assets.xml
        with_options:
          replace_types:
            - $JSON_Schema-JSchema
```

[<- Back to the overview](../README.md)
