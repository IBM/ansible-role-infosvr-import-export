# Data classes

[<- Back to the overview](../README.md)

## Exports

The export will be generate an ISX file that could be separately processed through the `istool` command-line.

```yml
export:
  dataclass:
    - into: <path>
      limited_to:
        changes_in_last_hours: <int>
        only_wwith_conditions:
          - { property: "<string>", operator: "<string>", value: "<value>" }
          - ...
    - ...
```

The options under `limited_to` are all optional:

- `only_with_conditions` defines [conditions](conditions.md) that are currently always AND'd (all conditions must be met).
- `changes_in_last_hours` specifies the number of hours prior to the playbook running from which to identify (and extract) any changes.

## Imports

```yml
import:
  dataclass:
    - from: <path>
      with_options:
        overwrite: <boolean>
        transformed_by: <list>
        args: <string>
    - ...
```

The only required parameter for the import is the file `from` which to load them.

The options under `with_options` are all optional:

- `overwrite` specifies whether to overwrite any existing assets with the same identities.
- `transformed_by` specifies a list of mappings that can be used to transform the assets; if provided, mappings should use the [ISX style](mappings.md#isx-style).
- `args` provides additional arguments to the export command; currently the following are possible:
  - `-allowDuplicates`: Allows import when duplicates exists in the imported metadata or when imported metadata matches duplicate objects in the repository.

## Examples

```yml
export:
  dataclass:
    - into: cache/dc_startsWith_MY_changed_in_last48hrs.isx
      limited_to:
        changes_in_last_hours: 48
        only_with_conditions:
          - { property: "name", operator: "like {0}%", value: "MY" }

isx_mappings:
  - { type: "HostSystem", attr: "name", from: "MY_HOST", to: "YOUR_HOST" }

import:
  dataclass:
    - from: cache/dc_startsWith_MY_changed_in_last48hrs.isx
      with_options:
        transformed_by: "{{ isx_mappings }}"
        overwrite: True
```

[<- Back to the overview](../README.md)
