# Extension mapping documents

[<- Back to the overview](../README.md)

## Exports

The export will be generate a ZIP file containing CSV files that could be separately loaded through the `istool` command-line or the IGC web user interface.

```yml
export:
  extensionmaps:
    - to: <path>
      changes_in_last_hours: <int>
    - ...
```

The `changes_in_last_hours` is optional; if used, specify the number of hours prior to the playbook running from which to identify (and extract) any changes.

## Imports

```yml
import:
  extensionmaps:
    - from: <path>
      folder: root/<string>
      overwrite: <boolean>
    - ...
```

The only required parameter for the import is the file `from` which to load them. If provided, the `folder` must always start with `root/` (using `/` as the subsequent separator for the rest of the folder structure). Folders are created if they do not already exist.

## Examples

```yml
export:
  extensionmaps:
    - to: cache/xm_changed_in_last48hrs.zip
      changes_in_last_hours: 48

import:
  extensionmaps:
    - from: cache/xm_changed_in_last48hrs.zip
      folder: root/Some/Folder
      overwrite: True
```

[<- Back to the overview](../README.md)
