# DataStage assets

[<- Back to the overview](../README.md)

## Exports

The export will be generate an ISX file that could be separately processed through the `istool` command-line.

```yml
export:
  datastage:
    - into: <path>
      including_objects:
        - type: <string>
          changes_in_last_hours: <int>
          only_with_conditions:
            - { property: "<string>", operator: "<string>", value: "<value>" }
            - ...
        - ...
    - ...
```

In addition to the file `into` which to extract the assets, at least one `type` should be specified under `including_objects`. Each `type` must be one of `dsjob`, `routine`, `shared_container`, `table_definition` or `parameter_set`.

- `only_with_conditions` are purely optional and are currently always AND'd (all conditions must be met). Any [conditions](conditions.md) specified should be within the context of the specified asset `type`.
- `changes_in_last_hours` is also optional; if used, specify the number of hours prior to the playbook running from which to identify (and extract) any changes of the specified `type`.

## Imports

```yml
import:
  datastage:
    - from: <path>
      into_project: <string>
      with_options:
        overwrite: <boolean>
    - ...
```

The only required parameters for the import are the file `from` which to load the assets and the `into_project` project name into which to load them.

The options under `with_options` are all optional:

- `overwrite` specifies whether to overwrite any existing assets with the same identities.

Note that because design-time lineage depends on the resolution of job parameters, `parameter_set`s should be imported before any other DataStage asset types to ensure that eg. `dsjob` import picks up the design time parameters for appropriate design-time lineage.

## Examples

```yml
export:
  datastage:
    - into: cache/ds_dstage1_jobs_changes_in_last48hrs.isx
      including_objects:
        - type: dsjob
          changes_in_last_hours: 48
          only_with_conditions:
            - { property: "transformation_project.name", operator: "=", value: "dstage1" }

import:
  datastage:
    - from: cache/ds_dstage1_jobs_changes_in_last48hrs.isx
      into_project: dstage1
      with_options:
        overwrite: True
```

[<- Back to the overview](../README.md)
