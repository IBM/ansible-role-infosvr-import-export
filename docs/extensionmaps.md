# Extension mapping documents

[<- Back to the overview](../README.md)

## Exports

The export will be generate a ZIP file containing CSV files that could be separately loaded through the `istool` command-line or the IGC web user interface.

```yml
export:
  extensionmaps:
    - into: <path>
      limited_to:
        changes_in_last_hours: <int>
    - ...
```

The options under `limited_to` are all optional:

- `changes_in_last_hours` specifies the number of hours prior to the playbook running from which to identify (and extract) any changes.

## Imports

```yml
import:
  extensionmaps:
    - from: <path>
      with_options:
        folder: root/<string>
        overwrite: <boolean>
    - ...
```

The only required parameter for the import is the file `from` which to load them.

The options under `with_options` are all optional:

- `folder` specifies the folder location into which to load the extension mappings; if provided, it must always start with `root/` (using `/` as the subsequent separator for the rest of the folder structure). Folders are created if they do not already exist.
- `overwrite` specifies whether to overwrite any existing assets with the same identities.

## Examples

```yml
export:
  extensionmaps:
    - into: cache/xm_changed_in_last48hrs.zip
      limited_to:
        changes_in_last_hours: 48

import:
  extensionmaps:
    - from: cache/xm_changed_in_last48hrs.zip
      with_options:
        folder: root/Some/Folder
        overwrite: True
```

[<- Back to the overview](../README.md)
