# Common metadata

[<- Back to the overview](../README.md)

**Note**: Common metadata export and ingest should really only be used when you need to load metadata into an environment where that environment will not have any of its own direct connectivity to the source of the metadata.  For example, to load metadata about a database when the instance into which you're loading the metadata has no connection of its own to the database in order to crawl it directly.  When such connectivity is possible, it will be more robust to directly index the metadata through IBM Metadata Asset Manager, which can be automated through the [IBM.infosvr-metadata-asset-manager](https://galaxy.ansible.com/IBM/infosvr-metadata-asset-manager) role.  IBM Metadata Asset Manager will ensure that accurate metadata is recorded, and can be periodically refreshed (re-ingested) to be kept up-to-date, including staging potentially destructive changes for review.  The re-ingesting is handled automatically as part of the [IBM.infosvr-metadata-asset-manager](https://galaxy.ansible.com/IBM/infosvr-metadata-asset-manager) role, so can also be automated (and will warn if there is a potentially destructive change that has been stage and requires review before it can be published).

Furthermore, this method for exporting and ingesting metadata is rather low-level, and does not support various options like change-based detection. For most common asset types (database assets, data file assets, model assets, etc), you will likely want to instead use the dedicated export / ingest mechanism even when IMAM (as indicated above) is not an option.

This method remains simply for the sake of completeness in case there is not already a dedicated export / ingest mechanism for a given type. (If you'd prefer one were created, feel free to raise an issue in this Git repository with the request.)

## Exports

The export will be generate an ISX file that could be separately processed through the `istool` command-line.

```yml
export:
  common:
    - into: <path>
      with_path: <string>
    - ...
```

The wildcard for `with_path`, is `"*"`, and it is the asset path as defined at https://www.ibm.com/support/knowledgecenter/en/SSZJPZ_11.7.0/com.ibm.swg.im.iis.iisinfsv.assetint.doc/topics/cm_asset_types_id_strings.html.

## Ingests

```yml
ingest:
  common:
    - from: <path>
      with_options:
        overwrite: <boolean>
        transformed_by: <list>
        args: <string>
    - ...
```

The only required parameter for the ingest is the file `from` which to load them.

The options under `with_options` are all optional:

- `overwrite` specifies whether to overwrite any existing assets with the same identities.
- `transformed_by` specifies a list of mappings that can be used to transform the assets; if provided, mappings should use the [ISX style](mappings.md#isx-style).
- `args` provides additional arguments to the export command; currently the following are possible:
  - `-allowDuplicates`: Allows import when duplicates exists in the imported metadata or when imported metadata matches duplicate objects in the repository.

## Examples

```yml
export:
  common:
    - into: cache/cm_file_structures.isx
      with_path: "/*/*/*/*.dcl"
    - into: cache/cm_file_domains.isx
      with_path: "/*/*/*/*/*.fdd"
    - into: cache/cm_file_defs.isx
      with_path: "/*/*.fd"
    - into: cache/cm_file_def_structures.isx
      with_path: "/*/*/*.fdl"
    - into: cache/cm_file_def_domains.isx
      with_path: "/*/*/*/*.ddd"
    - into: cache/cm_fields.isx
      with_path: "/*/*.did"

isx_mappings:
  - { type: "HostSystem", attr: "name", from: "MY_HOST", to: "YOUR_HOST" }

ingest:
  common:
    - from: cache/cm_file_structures.isx
      with_options:
        transformed_by: "{{ isx_mappings }}"
        overwrite: True
    - from: cache/cm_file_domains.isx
      with_options:
        transformed_by: "{{ isx_mappings }}"
        overwrite: True
    - from: cache/cm_file_defs.isx
      with_options:
        transformed_by: "{{ isx_mappings }}"
        overwrite: True
    - from: cache/cm_file_def_structures.isx
      with_options:
        transformed_by: "{{ isx_mappings }}"
        overwrite: True
    - from: cache/cm_file_def_domains.isx
      with_options:
        transformed_by: "{{ isx_mappings }}"
        overwrite: True
    - from: cache/cm_fields.isx
      with_options:
        transformed_by: "{{ isx_mappings }}"
        overwrite: True
```

[<- Back to the overview](../README.md)
