# Data classes

[<- Back to the overview](../README.md)

## Exports

The export will be generate an ISX file that could be separately processed through the `istool` command-line.

```yml
export:
  dataclass:
    - to: <path>
      changes_in_last_hours: <int>
      conditions:
        - { property: "<string>", operator: "<string>", value: "<value>" }
        - ...
    - ...
```

[`conditions`](conditions.md) are purely optional and are currently always AND'd (all conditions must be met).

`changes_in_last_hours` is also optional; if used, specify the number of hours prior to the playbook running from which to identify (and extract) any changes.

## Imports

```yml
import:
  dataclass:
    - from: <path>
      options: <string>
      map: <list>
      overwrite: <boolean>
    - ...
```

Mappings are purely optional, and the only required parameter for the import is the file `from` which to load them. If provided, mappings should use the [ISX style](mappings.md#isx-style).

Available `options` are:

- `-allowDuplicates`: Allows import when duplicates exists in the imported metadata or when imported metadata matches duplicate objects in the repository.

## Examples

```yml
export:
  dataclass:
    - to: cache/dc_startsWith_MY_changed_in_last48hrs.isx
      changes_in_last_hours: 48
      conditions:
        - { property: "name", operator: "like {0}%", value: "MY" }

isx_mappings:
  - { type: "HostSystem", attr: "name", from: "MY_HOST", to: "YOUR_HOST" }

import:
  dataclass:
    - from: cache/dc_startsWith_MY_changed_in_last48hrs.isx
      map: "{{ isx_mappings }}"
      overwrite: True
```

[<- Back to the overview](../README.md)
