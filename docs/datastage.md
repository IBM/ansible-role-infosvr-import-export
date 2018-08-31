# DataStage assets

[<- Back to the overview](../README.md)

## Exports

The export will be generate an ISX file that could be separately processed through the `istool` command-line.

```yml
export:
  datastage:
    - to: <path>
      changes_in_last_hours: <int>
      type: <string>
      conditions:
        - { property: "<string>", operator: "<string>", value: "<value>" }
        - ...
    - ...
```

[`conditions`](conditions.md) are purely optional and are currently always AND'd (all conditions must be met).

`changes_in_last_hours` is also optional; if used, specify the number of hours prior to the playbook running from which to identify (and extract) any changes.

The `type` should be one of `dsjob`, `routine`, `shared_container`, `table_definition` or `parameter_set`, and any [conditions](conditions.md) specified should be within the context of that specified asset type.

Note that because design-time lineage depends on the resolution of job parameters, `parameter_set`s should be imported before any other DataStage asset types to ensure that eg. `dsjob` import picks up the design time parameters for appropriate design-time lineage.

## Imports

```yml
import:
  datastage:
    - from: <path>
      project: <string>
      overwrite: <boolean>
    - ...
```

The only required parameters for the import are the `file` from which to load the assets and the `project` into which to load them.

## Examples

```yml
export:
  datastage:
    - to: cache/ds_dstage1_jobs_changes_in_last48hrs.isx
      changes_in_last_hours: 48
      type: dsjob
      conditions:
        - { property: "transformation_project.name", operator: "=", value: "dstage1" }

import:
  datastage:
    - from: cache/ds_dstage1_jobs_changes_in_last48hrs.isx
      project: dstage1
      overwrite: True
```

[<- Back to the overview](../README.md)
