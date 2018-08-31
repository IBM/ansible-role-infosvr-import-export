# Operational metadata (OMD)

[<- Back to the overview](../README.md)

## Exports

```yml
export:
  omd:
    - to: <path>
      changes_in_last_hours: <int>
    - ...
```

The directory `to` which the operational metadata flow files should be stored is required.

`changes_in_last_hours` is also optional; if used, specify the number of hours prior to the playbook running from which to identify (and extract) any operational metadata flows.

## Imports

```yml
import:
  omd:
    - from: <path>
    - ...
```

The only required parameter for the import is the directory `from` which to load the operational metadata flow files. (This should refer to a directory rather than an individual file.)

As part of the import process, the following actions will be taken:

- The original engine tier's host will be replaced by the target engine tier's host -- this is the only way to ensure the operational metadata can be loaded into the target environment. Note that the project and job that the operational metadata refers to should already exist as well in the target environment (ie. ensure you import the jobs through the [datastage](datastage.md) option; the role will ensure those are loaded before trying to import this operational metadata).
- Lineage will be enabled on any projects referred to by the operational metadata flows being imported -- if lineage is not enabled on the project, then the lineage that is loaded through the OMD import will not show up.

## Examples

```yml
export:
  omd:
    - to: cache/omd_exports/
      changes_in_last_hours: 48

import:
  omd:
    - from: cache/omd_exports/
```

[<- Back to the overview](../README.md)
