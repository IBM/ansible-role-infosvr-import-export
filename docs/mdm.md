# Master data management model metadata

[<- Back to the overview](../README.md)

**Note**: master data management model metadata export and import should really only be used when you need to load metadata into an environment where that environment will not have access to the original model files or a metadata interchange server capable of loading them.  When possible, it will be more robust to directly load the metadata through IBM Metadata Asset Manager, which can be automated through the [IBM.infosvr-metadata-asset-manager](https://galaxy.ansible.com/IBM/infosvr-metadata-asset-manager) role.  IBM Metadata Asset Manager will ensure that accurate metadata is recorded, and can be periodically refreshed (re-imported) to be kept up-to-date, including staging potentially destructive changes for review.  The re-importing is handled automatically as part of the [IBM.infosvr-metadata-asset-manager](https://galaxy.ansible.com/IBM/infosvr-metadata-asset-manager) role, so can also be automated (and will warn if there is a potentially destructive change that has been stage and requires review before it can be published).

## Exports

The export will be generate an ISX file that could be separately processed through the `istool` command-line.

```yml
export:
  mdm:
    - to: <path>
      path: <string>
    - ...
```

The wildcard for `path`, is `"*"`, and it is the asset path as defined at https://www.ibm.com/support/knowledgecenter/en/SSZJPZ_11.7.0/com.ibm.swg.im.iis.iisinfsv.assetint.doc/topics/cm_asset_types_id_strings.html#cm_asset_types_id_strings__mdm.

## Imports

```yml
import:
  mdm:
    - from: <path>
      options: <string>
      map: <list>
      overwrite: <boolean>
    - ...
```

Mappings are purely optional, and the only required parameter for the import is the file `from` which to load them. If provided, mappings should use the [ISX style](mappings.md#isx-style).

Available `options` are:

- `-allowDuplicates`: Allows import when duplicates exists in the imported metadata or when imported metadata matches duplicate objects in the repository.

## Examples

```yml
export:
  mdm:
    - to: cache/mdm.isx
      path: "/*/*.mdm"

isx_mappings:
  - { type: "HostSystem", attr: "name", from: "MY_HOST", to: "YOUR_HOST" }

import:
  mdm:
    - from: cache/mdm.isx
      map: "{{ isx_mappings }}"
      overwrite: True
```

[<- Back to the overview](../README.md)
