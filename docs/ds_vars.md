# DataStage project variables

[<- Back to the overview](../README.md)

## Exports

The export will be generate a YAML file that can only be processed through the `ingest` action of this Ansible role.

```yml
export:
  ds_vars:
    - into: <path>
      from_project: <string>
      limited_to:
        - ...
    - ...
```

The only required parameters for the export are the file `into` which to extract the variables and their values and the `from_project` project name from which to export them. The `limited_to` list is optional, to specify which variables should be included; if not specified, all variables are included.

## Ingests

```yml
ingest:
  ds_vars:
    - from: <path>
      into_project: <string>
    - ...
```

Both the file `from` which to load the variables and the `into_project` project name into which to load them are required. The ingest process will look for the `from` file within your playbook's `vars` directory.

## Examples

```yml
export:
  ds_vars:
    - into: vars/ds_dstage1_vars.yml
      from_project: dstage1
      limited_to:
        - ODPPLL
        - TMPDIR

ingest:
  ds_vars:
    - from: ds_dstage1_vars.yml
      into_project: dstage1
```

[<- Back to the overview](../README.md)
