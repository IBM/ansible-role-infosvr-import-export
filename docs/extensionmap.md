# Extension mapping documents

[<- Back to the overview](../README.md)

## Exports

The export will be generate a ZIP file containing CSV files that could be separately loaded through the `istool` command-line or the IGC web user interface.

```yml
export:
  extensionmap:
    - into: <path>
      limited_to:
        changes_in_last_hours: <int>
    - ...
```

The options under `limited_to` are all optional:

- `changes_in_last_hours` specifies the number of hours prior to the playbook running from which to identify (and extract) any changes.

## Ingests

```yml
ingest:
  extensionmap:
    - from: <path>
      with_options:
        folder: root/<string>
        overwrite: <boolean>
        args: <string>
    - ...
```

The only required parameter for the ingest is the file `from` which to load them.

The options under `with_options` are all optional:

- `folder` specifies the folder location into which to load the extension mappings; if provided, it must always start with `root/` (using `/` as the subsequent separator for the rest of the folder structure). Folders are created if they do not already exist.
- `overwrite` specifies whether to overwrite any existing assets with the same identities.
- `args` provides additional arguments to the ingest command; currently the following are possible:
  - `-description`: Long description for all mapping documents (defaults to none)
  - `-shortDescription`: Short description for all mapping documents (defaults to none)
  - `-type`: Type for all mapping documents (defaults to none)
  - `-srcprefix`: Prefix for all sources for imported mapping documents (defaults to none)
  - `-trgprefix`: Prefix for all targets for imported mapping documents (defaults to none)

When specifying multiple `args`, simply include them all separated by spaces.

**Important note**: ingestion will _not_ fail when a given mapping's source or target metadata does not exist in the environment. Currently the only way to check for this condition is to use the `validate` step to confirm that the outcome in the environment is as expected.

## Examples

```yml
export:
  extensionmap:
    - into: cache/xm_changed_in_last48hrs.zip
      limited_to:
        changes_in_last_hours: 48

ingest:
  extensionmap:
    - from: cache/xm_changed_in_last48hrs.zip
      with_options:
        folder: root/Some/Folder
        overwrite: True
```

[<- Back to the overview](../README.md)
