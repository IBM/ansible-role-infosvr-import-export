# Custom attribute definitions

[<- Back to the overview](../README.md)

## Exports

The export will be generate an ISX file that could be separately processed through the `istool` command-line.

```yml
export:
  customattrs:
    - into: <path>
      from_area: <string>
      from_type: <string>
      from_attr: <string>
      limited_to:
        changes_in_last_hours: <int>
        names:
          - <string>
          - ...
    - ...
```

The wildcard for `from_area`, `from_type` and `from_attr` is `"*"`. Be aware that the area and type are defined by the internal model of IGC rather than its REST API types. Some examples:

- For business terms: `from_area` = GlossaryExtensions, `from_type` = BusinessTerm, `from_attr` = GlossaryExtensions.BusinessTerm
- For categories: `from_area` = GlossaryExtensions, `from_type` = BusinessCategory, `from_attr` = GlossaryExtensions.BusinessCategory
- For database tables: `from_area` = ASCLModel, `from_type` = DataCollection, `from_attr` = ASCLModel.DatabaseTable
- For an OpenIGC class "$MyBundle-ClassName": `from_area` = MwbExtensions, `from_type` = ExtensionDataSource, `from_attr` = MwbExtensions.Xt_MyBundle__ClassName

If in doubt, do an export of all custom attributes (providing `"*"` for area, type and attr), unzip the produced ISX file and look for the custom attribute(s) of interest. The directory structure of the extracted ISX file defines the `from_area` and `from_type`.

The options under `limited_to` are all optional:

- `changes_in_last_hours` specifies the number of hours prior to the playbook running from which to identify (and extract) any changes.
- `names` defines list of the specific custom attributes of that type to extract, by their name.

## Imports

```yml
import:
  customattrs:
    - from: <path>
      with_options:
        overwrite: <boolean>
        transformed_by: <list>
    - ...
```

The options under `with_options` are all optional:

- `overwrite` specifies whether to overwrite any existing assets with the same identities.
- `transformed_by` specifies a list of mappings that can be used to transform the assets; if provided, mappings should use the [ISX style](mappings.md#isx-style).

## Examples

```yml
export:
  customattrs:
    - into: cache/cadefs_openigc.isx
      from_area: MwbExtensions
      from_type: ExtensionDataSource
      from_attr: "*"
      limited_to:
        names:
          - A Custom Relationship
          - Another Custom Relationship
    - into: cache/cadefs_terms_in_last_48hrs.isx
      from_area: GlossaryExtensions
      from_type: BusinessTerm
      from_attr: "*"
      limited_to:
        changes_in_last_hours: 48

isx_mappings:
  - { type: "HostSystem", attr: "name", from: "MY_HOST", to: "YOUR_HOST" }

import:
  customattrs:
    - from: cadefs_openigc.isx
      with_options:
        transformed_by: "{{ isx_mappings }}"
        overwrite: True
```

[<- Back to the overview](../README.md)
