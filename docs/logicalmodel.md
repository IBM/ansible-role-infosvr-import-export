# Logical model metadata

[<- Back to the overview](../README.md)

**Note**: logical model metadata export and ingest should really only be used when you need to load metadata into an environment where that environment will not have access to the original model files or a metadata interchange server capable of loading them.  When possible, it will be more robust to directly load the metadata through IBM Metadata Asset Manager, which can be automated through the [IBM.infosvr-metadata-asset-manager](https://galaxy.ansible.com/IBM/infosvr-metadata-asset-manager) role.  IBM Metadata Asset Manager will ensure that accurate metadata is recorded, and can be periodically refreshed (re-ingested) to be kept up-to-date, including staging potentially destructive changes for review.  The re-ingesting is handled automatically as part of the [IBM.infosvr-metadata-asset-manager](https://galaxy.ansible.com/IBM/infosvr-metadata-asset-manager) role, so can also be automated (and will warn if there is a potentially destructive change that has been stage and requires review before it can be published).

## Exports

The export will be generate an ISX file that could be separately processed through the `istool` command-line.

```yml
export:
  logicalmodel:
    - into: <path>
      limited_to:
        changes_in_last_hours: <int>
        only_with_conditions:
          - { property: "<string>", operator: "<string>", value: "<value>" }
          - ...
    - ...
```

The options under `limited_to` are all optional:

- `only_with_conditions` defines [conditions](conditions.md) that are currently always AND'd (all conditions must be met). The conditions should be relative to the top-level logical_data_model object(s) you wish to include.
- `changes_in_last_hours` specifies the number of hours prior to the playbook running from which to identify (and extract) any changes. Changes to sub-objects of the logical model -- its contained logical models, subject areas, logical entities and logical domains -- will automatically be checked as well.

## Ingests

```yml
ingest:
  logicalmodel:
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
  logicalmodel:
    - into: cache/ldm_sample_changed_in_last_2_days.isx
      limited_to:
        changes_in_last_hours: 48
        only_with_conditions:
          - { property: "name", operator: "=", value: "Sample" }
          - { property: "namespace", operator: "=", value: "SampleNamespace" }

isx_mappings:
  - { type: "HostSystem", attr: "name", from: "MY_HOST", to: "YOUR_HOST" }

ingest:
  logicalmodel:
    - from: cache/ldm_sample_changed_in_last_2_days.isx
      with_options:
        transformed_by: "{{ isx_mappings }}"
        overwrite: True
```

[<- Back to the overview](../README.md)
