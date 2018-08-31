# Custom attribute definitions

[<- Back to the overview](../README.md)

## Exports

The export will be generate an ISX file that could be separately processed through the `istool` command-line.

```yml
export:
  customattrs:
    - to: <path>
      changes_in_last_hours: <int>
      area: <string>
      type: <string>
      attr: <string>
      names:
        - <string>
        - ...
    - ...
```

The wildcard for `area`, `type` and `attr` is `"*"`. Be aware that the area and type are defined by the internal model of IGC rather than its REST API types. Some examples:

- For business terms: `area` = GlossaryExtensions, `type` = BusinessTerm, `attr` = GlossaryExtensions.BusinessTerm
- For categories: `area` = GlossaryExtensions, `type` = BusinessCategory, `attr` = GlossaryExtensions.BusinessCategory
- For database tables: `area` = ASCLModel, `type` = DataCollection, `attr` = ASCLModel.DatabaseTable
- For an OpenIGC class "$MyBundle-ClassName": `area` = MwbExtensions, `type` = ExtensionDataSource, `attr` = MwbExtensions.Xt_MyBundle__ClassName

If in doubt, do an export of all custom attributes (providing `"*"` for area, type and attr), unzip the produced ISX file and look for the custom attribute(s) of interest. The directory structure of the extracted ISX file defines the `area` and `type`.

The (optional) array of `names` can be used to define which specific custom attributes of that type to extract, by their name.

## Imports

```yml
import:
  customattrs:
    - from: <path>
      map: <list>
      overwrite: <boolean>
    - ...
```

Mappings are purely optional, and the only required parameter for the import is the file `from` which to load them. If provided, mappings should use the [ISX style](mappings.md#isx-style).

## Examples

```yml
export:
  customattrs:
    - to: cache/cadefs_openigc.isx
      area: MwbExtensions
      type: ExtensionDataSource
      attr: "*"
      names:
        - A Custom Relationship
        - Another Custom Relationship
    - to: cache/cadefs_terms_in_last_48hrs.isx
      changes_in_last_hours: 48
      area: GlossaryExtensions
      type: BusinessTerm
      attr: "*"

isx_mappings:
  - { type: "HostSystem", attr: "name", from: "MY_HOST", to: "YOUR_HOST" }

import:
  customattrs:
    - from: cadefs_openigc.isx
      map: "{{ isx_mappings }}"
      overwrite: True
```

[<- Back to the overview](../README.md)
