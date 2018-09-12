# Operational metadata (OMD)

[<- Back to the overview](../README.md)

## Exports

```yml
export:
  omd:
    - into: <path>
      limited_to:
        changes_in_last_hours: <int>
      with_options:
        remove_once_exported: <boolean>
    - ...
```

The directory `into` which the operational metadata flow files should be stored is required.

The options under `limited_to` are all optional:

- `changes_in_last_hours` specifies the number of hours prior to the playbook running from which to identify (and extract) any operational metadata flows.

The options under `with_options` are all optional:

- `remove_once_exported` indicates that once exported, the operational metadata XML should be removed (if `True`) or should be left behind (if `False`); defaults to `False` if not specified.

## Ingests

```yml
ingest:
  omd:
    - from: <path>
    - ...
```

The only required parameter for the ingest is the directory `from` which to load the operational metadata flow files. (This should refer to a directory rather than an individual file.)

As part of the ingest process, the following actions will be taken:

- The original engine tier's host will be replaced by the target engine tier's host -- this is the only way to ensure the operational metadata can be loaded into the target environment. Note that the project and job that the operational metadata refers to should already exist as well in the target environment (ie. ensure you ingest the jobs through the [datastage](datastage.md) option; the role will ensure those are loaded before trying to ingest this operational metadata).
- Lineage will be enabled on any projects referred to by the operational metadata flows being ingested -- if lineage is not enabled on the project, then the lineage that is loaded through the OMD ingest will not show up.

## Examples

```yml
export:
  omd:
    - into: cache/omd_exports/
      limited_to:
        changes_in_last_hours: 48

ingest:
  omd:
    - from: cache/omd_exports/
```

[<- Back to the overview](../README.md)
