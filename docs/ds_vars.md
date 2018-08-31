# DataStage project variables

[<- Back to the overview](../README.md)

## Exports

The export will be generate a YAML file that can only be processed through the `import` action of this Ansible role.

```yml
export:
  ds_vars:
    - to: <path>
      project: <string>
      vars:
        - ...
    - ...
```

The only required parameters for the export are the file `to` which to extract the variables and their values and the `project` from which to export them. The `vars` list is optional, to specify which variables should be included; if not specified, all variables are included.

## Imports

```yml
import:
  ds_vars:
    - from: <path>
      project: <string>
    - ...
```

Both the `file` from which to load the variables and the `project` into which to load them are required. The import process will look for the `from` file within your playbook's `vars` directory.

## Examples

```yml
export:
  ds_vars:
    - to: vars/ds_dstage1_vars.yml
      project: dstage1
      vars:
        - ODPPLL
        - TMPDIR

import:
  ds_vars:
    - from: ds_dstage1_vars.yml
      project: dstage1
```

[<- Back to the overview](../README.md)
