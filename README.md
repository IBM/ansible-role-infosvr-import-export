# ansible-role-infosvr-import-export

Ansible role for automating the import and export of content and structures within IBM InfoSphere Information Server.

## Requirements

- Ansible v2.4.x
- Root-become-able network access to an IBM Information Server environment
- Inventory group names setup the same as `IBM.infosvr` role

## Role Variables

See `defaults/main.yml` for inline documentation, and the example below for the main variables needed. For any clarification on the sub-types for the various files, refer to the `defaults/main.yml` file.

## Example Playbook

The role includes the ability to both export and import a number of different asset types in Information Server. The role can be imported into another playbook providing only the variables of interest in order to restrict the assets to include in either an import or export (empty variables will mean the role will skip any processing of those asset types). (Thus the need for Ansible v2.4.x and the `import_role` module.)

Use `tasks_from` to define whether to run an `import` or an `export` -- or leave it off entirely to run both (export will run first so you could use this to eg. first do a backup of certain structures and content prior to importing).

For example:

```yml
- import_role:
    name: IBM.infosvr-import-export
    tasks_from: import
  vars:
    ibm_infosvr_impexp_ds_import:
      - { src: "/some/directory/file1.isx", project: "dstage1", overwrite: True }
    ibm_infosvr_impexp_cm_mappings:
      - { type: "HostSystem", attr: "name", from: "MY_HOST", to "YOUR_HOST" }
    ibm_infosvr_impexp_cm_import:
      - { src: "file2.isx", map: "{{ ibm_infosvr_impexp_cm_mappings }}", overwrite: True }
```

... will import the common metadata from a file `file2.isx` expected in your playbook's `/files/` directory, renaming any hostnames from `MY_HOST` to `YOUR_HOST`, and overwriting any existing assets with the same identities. It will then import the DataStage assets from `/some/directory/file1.isx` into the `dstage1` project, overwriting any existing assets with the same identities.

Note that the order in which the variables are defined does not matter: the role will take care of exporting and importing objects in the appropriate order to ensure dependencies between objects are handled (ie. that common and business metadata are loaded before relationships, etc). However, the order of multiple objects defined within a given variable _may_ matter, depending on your own dependencies.

By default, the role will do SSL verification of self-signed certificates by first retrieving the root certificate directly from the domain tier of the environment. This is controlled by the `ibm_infosvr_impexp_verify_selfsigned_ssl` variable of the role: if you want to only verify against properly signed and trusted SSL certificates, you can set this variable to `False` and any self-signed domain tier certificate will no longer be trusted.

# Possible variables and expected structures

The following describes all of the object types currently covered by the this role, and the expected structures of the variables. You can generally write the variables using any form supported by Ansible, eg. these are all equivalent and simply up to your personal preference:

```yml
var_name: [ { a: "", b: "", c: "" }, { d: "", e: "", f: "" } ]

var_name:
  - { a: "", b: "", c: "" }
  - { d: "", e: "", f: "" }

var_name:
  - a: ""
    b: ""
    c: ""
  - d: ""
    e: ""
    f: ""
```

This section will document each variable using the middle style, simply for a balance between brevity and clarity.

## Custom attribute definitions

**Imports**:

```yml
ibm_infosvr_impexp_cadefs_mappings:
  - { type: "<string>", attr: "<string>", from: "<value>", to: "<value>" }
  - ...

ibm_infosvr_impexp_cadefs_import:
  - { src: "<path>", options: "<string>", map: "<list>", overwrite: <boolean> }
  - ...
```

Mappings are purely optional, and the only required parameter for the import is the `src` file from which to load them.

**Exports**:

```yml
ibm_infosvr_impexp_cadefs_export:
  - dest: "<path>"
    changes_in_last_hours: <int>
    area: "<string>"
    type: "<string>"
    attr: "<string>"
    names:
      - "<string>"
      - ...
  - ...
```

The wildcard for `area`, `type` and `attr` is `"*"`. Be aware that the area and type are defined by the internal model of IGC rather than its REST API types. Some examples:

- For business terms: `area` = GlossaryExtensions, `type` = BusinessTerm, `attr` = GlossaryExtensions.BusinessTerm
- For categories: `area` = GlossaryExtensions, `type` = BusinessCategory, `attr` = GlossaryExtensions.BusinessCategory
- For database tables: `area` = ASCLModel, `type` = DataCollection, `attr` = ASCLModel.DatabaseTable
- For an OpenIGC class "$MyBundle-ClassName": `area` = MwbExtensions, `type` = ExtensionDataSource, `attr` = MwbExtensions.Xt_MyBundle__ClassName

If in doubt, do an export of all custom attributes (providing `"*"` for area, type and attr), unzip the produced ISX file and look for the custom attribute(s) of interest. The directory structure of the extracted ISX file defines the `area` and `type`.

The (optional) array of `names` can be used to define which specific custom attributes of that type to extract, by their name.

**Examples**:

```yml
ibm_infosvr_impexp_cadefs_mappings:
  - { type: "HostSystem", attr: "name", from: "MY_HOST", to: "YOUR_HOST" }

ibm_infosvr_impexp_cadefs_import:
  - { src: "import.isx", options: "-allowDup", map: "{{ ibm_infosvr_impexp_cadefs_mappings }}", overwrite: True }

ibm_infosvr_impexp_cadefs_export:
  - dest: "cache/cadefs_openigc.isx"
    area: "MwbExtensions"
    type: "ExtensionDataSource"
    attr: "*"
    names:
      - A Custom Relationship
      - Another Custom Relationship
  - dest: "cache/cadefs_terms_in_last_48hrs.isx"
    changes_in_last_hours: 48
    area: "GlossaryExtensions"
    type: "BusinessTerm"
    attr: "*"
```

## Common metadata

**Note**: Common metadata export and import should really only be used when you need to load metadata into an environment where that environment will not have any of its own direct connectivity to the source of the metadata.  For example, to load metadata about a database when the instance into which you're loading the metadata has no connection of its own to the database in order to crawl it directly.  When such connectivity is possible, it will be more robust to directly index the metadata through IBM Metadata Asset Manager, which can be automated through the [IBM.infosvr-metadata-asset-manager](https://galaxy.ansible.com/IBM/infosvr-metadata-asset-manager) role.  IBM Metadata Asset Manager will ensure that accurate metadata is recorded, and can be periodically refreshed (re-imported) to be kept up-to-date, including staging potentially destructive changes for review.  The re-importing is handled automatically as part of the [IBM.infosvr-metadata-asset-manager](https://galaxy.ansible.com/IBM/infosvr-metadata-asset-manager) role, so can also be automated (and will warn if there is a potentially destructive change that has been stage and requires review before it can be published).

**Imports**:

```yml
ibm_infosvr_impexp_cm_mappings:
  - { type: "<string>", attr: "<string>", from: "<value>", to: "<value>" }
  - ...

ibm_infosvr_impexp_cm_import:
  - { src: "<path>", options: "<string>", map: "<list>", overwrite: <boolean> }
  - ...
```

Mappings are purely optional, and the only required parameter for the import is the `src` file from which to load them.

**Exports**:

```yml
ibm_infosvr_impexp_cm_export:
  - { dest: "<path>", path: "<string>" }
```

The wildcard for `path`, is `"*"`.

**Examples**:

```yml
ibm_infosvr_impexp_cm_mappings:
  - { type: "HostSystem", attr: "name", from: "MY_HOST", to: "YOUR_HOST" }

ibm_infosvr_impexp_cm_import:
  - { src: "import.isx", options: "-allowDup", map: "{{ ibm_infosvr_impexp_cm_mappings }}", overwrite: True }

ibm_infosvr_impexp_cm_export:
  - { dest: "cache/cm_hosts.isx", path: "/*.hst" }
  - { dest: "cache/cm_databases.isx", path: "/*/*.db" }
  - { dest: "cache/cm_schemas.isx", path: "/*/*/*.sch" }
  - { dest: "cache/cm_tables.isx", path: "/*/*/*/*.tbl" }
  - { dest: "cache/cm_procedures.isx", path: "/*/*/*/*.sp" }
  - { dest: "cache/cm_columns.isx", path: "/*/*/*/*/*.sdd" }
  - { dest: "cache/cm_file_folders.isx", path: "/*/*/*.fdr" }
  - { dest: "cache/cm_files.isx", path: "/*/*/*.fl" }
  - { dest: "cache/cm_file_structures.isx", path: "/*/*/*/*.dcl" }
  - { dest: "cache/cm_file_domains.isx", path: "/*/*/*/*/*.fdd" }
  - { dest: "cache/cm_file_defs.isx", path: "/*/*.fd" }
  - { dest: "cache/cm_file_def_structures.isx", path: "/*/*/*.fdl" }
  - { dest: "cache/cm_file_def_domains.isx", path: "/*/*/*/*.ddd" }
  - { dest: "cache/cm_fields.isx", path: "/*/*.did" }
  - { dest: "cache/cm_pdms.isx", path: "/*/*.pm" }
  - { dest: "cache/cm_pdm_tables.isx", path: "/*/*/*.dtl" }
  - { dest: "cache/cm_pdm_procedures.isx", path: "/*/*/*.dp" }
  - { dest: "cache/cm_pdm_domains.isx", path: "/*/*/*/*.pdd" }
  - { dest: "cache/cm_bi_servers.isx", path: "/*.srv" }
  - { dest: "cache/cm_bi_folders.isx", path: "/*/*/*.fld" }
  - { dest: "cache/cm_bi_models.isx", path: "/*/*/*.oml" }
  - { dest: "cache/cm_bi_collections.isx", path: "/*/*/*/*/*.ocl" }
  - { dest: "cache/cm_bi_cubes.isx", path: "/*/*/*/*/*.ocb" }
  - { dest: "cache/cm_bi_reports.isx", path: "/*/*/*.rdf" }
  - { dest: "cache/cm_bi_queries.isx", path: "/*/*/*/*/*.rds" }
  - { dest: "cache/cm_dataconnections.isx", path: "/*/*.dcn" }
  - { dest: "cache/cm_contract_libraries.isx", path: "/*.cl" }
```

## Logical model metadata

**Note**: As with common metadata, logical model metadata export and import should really only be used when you need to load metadata into an environment where that environment will not have access to the original model files or a metadata interchange server capable of loading them.  When possible, it will be more robust to directly load the metadata through IBM Metadata Asset Manager, which can be automated through the [IBM.infosvr-metadata-asset-manager](https://galaxy.ansible.com/IBM/infosvr-metadata-asset-manager) role.  IBM Metadata Asset Manager will ensure that accurate metadata is recorded, and can be periodically refreshed (re-imported) to be kept up-to-date, including staging potentially destructive changes for review.  The re-importing is handled automatically as part of the [IBM.infosvr-metadata-asset-manager](https://galaxy.ansible.com/IBM/infosvr-metadata-asset-manager) role, so can also be automated (and will warn if there is a potentially destructive change that has been stage and requires review before it can be published).

**Imports**:

```yml
ibm_infosvr_impexp_lm_mappings:
  - { type: "<string>", attr: "<string>", from: "<value>", to: "<value>" }
  - ...

ibm_infosvr_impexp_lm_import:
  - { src: "<path>", options: "<string>", map: "<list>", overwrite: <boolean> }
  - ...
```

Mappings are purely optional, and the only required parameter for the import is the `src` file from which to load them.

**Exports**:

```yml
ibm_infosvr_impexp_lm_export:
  - { dest: "<path>", path: "<string>" }
```

The wildcard for `path`, is `"*"`.

**Examples**:

```yml
ibm_infosvr_impexp_lm_mappings:
  - { type: "HostSystem", attr: "name", from: "MY_HOST", to: "YOUR_HOST" }

ibm_infosvr_impexp_lm_import:
  - { src: "import.isx", options: "-allowDup", map: "{{ ibm_infosvr_impexp_lm_mappings }}", overwrite: True }

ibm_infosvr_impexp_lm_export:
  - { dest: "cache/ldms.isx", path: "/*/*.lm" }
  - { dest: "cache/ldm_entities.isx", path: "/*/*/*.ent" }
  - { dest: "cache/ldm_relationships.isx", path: "/*/*/*/*/*.rel" }
  - { dest: "cache/ldm_generalizations.isx", path: "/*/*/*/*/*/*.gen" }
  - { dest: "cache/ldm_domains.isx", path: "/*/*/*/*.dom" }
  - { dest: "cache/ldm_subjectareas.isx", path: "/*/*/*.sa" }
```

## Master data management model metadata

**Note**: As with common metadata, master data management model metadata export and import should really only be used when you need to load metadata into an environment where that environment will not have access to the original model files or a metadata interchange server capable of loading them.  When possible, it will be more robust to directly load the metadata through IBM Metadata Asset Manager, which can be automated through the [IBM.infosvr-metadata-asset-manager](https://galaxy.ansible.com/IBM/infosvr-metadata-asset-manager) role.  IBM Metadata Asset Manager will ensure that accurate metadata is recorded, and can be periodically refreshed (re-imported) to be kept up-to-date, including staging potentially destructive changes for review.  The re-importing is handled automatically as part of the [IBM.infosvr-metadata-asset-manager](https://galaxy.ansible.com/IBM/infosvr-metadata-asset-manager) role, so can also be automated (and will warn if there is a potentially destructive change that has been stage and requires review before it can be published).

**Imports**:

```yml
ibm_infosvr_impexp_mdm_mappings:
  - { type: "<string>", attr: "<string>", from: "<value>", to: "<value>" }
  - ...

ibm_infosvr_impexp_mdm_import:
  - { src: "<path>", options: "<string>", map: "<list>", overwrite: <boolean> }
  - ...
```

Mappings are purely optional, and the only required parameter for the import is the `src` file from which to load them.

**Exports**:

```yml
ibm_infosvr_impexp_mdm_export:
  - { dest: "<path>", path: "<string>" }
```

The wildcard for `path`, is `"*"`.

**Examples**:

```yml
ibm_infosvr_impexp_mdm_mappings:
  - { type: "HostSystem", attr: "name", from: "MY_HOST", to: "YOUR_HOST" }

ibm_infosvr_impexp_mdm_import:
  - { src: "import.isx", options: "-allowDup", map: "{{ ibm_infosvr_impexp_mdm_mappings }}", overwrite: True }

ibm_infosvr_impexp_mdm_export:
  - { dest: "cache/mdm.isx", path: "/*/*.mdm" }
```

## Data classes

**Imports**:

```yml
ibm_infosvr_impexp_dc_mappings:
  - { type: "<string>", attr: "<string>", from: "<value>", to: "<value>" }
  - ...

ibm_infosvr_impexp_dc_import:
  - { src: "<path>", options: "<string>", map: "<list>", overwrite: <boolean> }
  - ...
```

Mappings are purely optional, and the only required parameter for the import is the `src` file from which to load them.

**Exports**:

```yml
ibm_infosvr_impexp_dc_export:
  - dest: "<path>"
    changes_in_last_hours: <int>
    conditions:
      - { property: "<string>", operator: "<string>", value: "<value>" }
      - ...
  - ...
```

Conditions are purely optional, take the form of the IGC REST API's conditions (see http://www.ibm.com/support/docview.wss?uid=swg27047054) and are currently always AND'd (all conditions must be met). The `changes_in_last_hours` is also optional; if used, specify the number of hours prior to the playbook running from which to identify (and extract) any changes.

**Examples**:

```yml
ibm_infosvr_impexp_dc_mappings:
  - { type: "HostSystem", attr: "name", from: "MY_HOST", to: "YOUR_HOST" }

ibm_infosvr_impexp_dc_import:
  - { src: "import.isx", options: "-allowDup", map: "{{ ibm_infosvr_impexp_dc_mappings }}", overwrite: True }

ibm_infosvr_impexp_dc_export:
  - dest: "cache/dc_startsWith_MY_changed_in_last48hrs.isx"
    changes_in_last_hours: 48
    conditions:
      - { property: "name", operator: "like {0}%", value: "MY" }
```

## DataStage assets

**Imports**:

```yml
ibm_infosvr_impexp_ds_import:
  - { src: "<path>", project: "<string>", overwrite: <boolean> }
  - ...
```

The only required parameters for the import are the `src` file from which to and the `project` into which to load them.

**Exports**:

```yml
ibm_infosvr_impexp_ds_export:
  - dest: "<path>"
    changes_in_last_hours: <int>
    type: "<string>"
    conditions:
      - { property: "<string>", operator: "<string>", value: "<value>" }
      - ...
  - ...
```

Conditions are purely optional, take the form of the IGC REST API's conditions (see http://www.ibm.com/support/docview.wss?uid=swg27047054) and are currently always AND'd (all conditions must be met). The `changes_in_last_hours` is also optional; if used, specify the number of hours prior to the playbook running from which to identify (and extract) any changes.

The `type` should be one of `dsjob`, `routine`, `shared_container`, `table_definition` or `parameter_set`, and any conditions specified should be within the context of that specified asset type.

Note that because design-time lineage depends on the resolution of job parameters, `parameter_set`s should be imported before any other DataStage asset types to ensure that eg. `dsjob` import picks up the design time parameters for appropriate design-time lineage.

**Examples**:

```yml
ibm_infosvr_impexp_ds_import:
  - { src: "import.isx", project: "dstage1", overwrite: True }

ibm_infosvr_impexp_ds_export:
  - dest: "cache/ds_dstage1_jobs_changes_in_last48hrs.isx"
    changes_in_last_hours: 48
    type: "dsjob"
    conditions:
      - { property: "transformation_project.name", operator: "=", value: "dstage1" }
```

## DataStage project variables

**Imports**:

```yml
ibm_infosvr_impexp_ds_vars_import:
  - { src: "<path>", project: "<string>" }
  - ...
```

The only required parameters for the import are the `src` file from which to and the `project` into which to load them. The import process will look for the `src` file within your playbook's `vars` directory.

**Exports**:

```yml
ibm_infosvr_impexp_ds_vars_export:
  - dest: "<path>"
    project: "<string>"
    vars:
      - ...
```

The only required parameters for the export are the `dest` file into which to capture the variables and their values and the `project` from which to export them. The `vars` list is optional, to specify which variables should be included; if not specified, all variables are included.

**Examples**:

```yml
ibm_infosvr_impexp_ds_vars_import:
  - { src: "ds_dstage1_vars.yml", project: "dstage1" }

ibm_infosvr_impexp_ds_vars_export:
  - dest: "vars/ds_dstage1_vars.yml"
    project: "dstage1"
    vars:
      - ODPPLL
      - TMPDIR
```

## Information Analyzer assets

**Imports**:

```yml
ibm_infosvr_impexp_ia_mappings:
  - { type: "<string>", attr: "<string>", from: "<value>", to: "<value>" }
  - ...

ibm_infosvr_impexp_ia_import:
  - { src: "<path>", project: "<string>", map: "<list>" }
  - ...
```

Mappings are purely optional, and the only required parameters for the import are the `src` file from which to load the project and the `project` name.

**Exports**:

```yml
ibm_infosvr_impexp_ia_export:
  - dest: "<path>"
    project: "<string>"
    objects:
      - type: data_rule_definition
        changes_in_last_hours: <int>
        conditions:
          - { property: "<string>", operator: "<string>", value: "<value>" }
          - ...
      - type: data_rule_set_definition
        changes_in_last_hours: <int>
        conditions:
          - { property: "<string>", operator: "<string>", value: "<value>" }
          - ...
      - type: data_rule
        changes_in_last_hours: <int>
        conditions:
          - { property: "<string>", operator: "<string>", value: "<value>" }
          - ...
      - type: data_rule_set
        changes_in_last_hours: <int>
        conditions:
          - { property: "<string>", operator: "<string>", value: "<value>" }
          - ...
      - type: metric
        changes_in_last_hours: <int>
        conditions:
          - { property: "<string>", operator: "<string>", value: "<value>" }
          - ...
```

Objects that can be conditionally exported include `data_rule_definition`, `data_rule_set_definition`, `data_rule`, `data_rule_set`, and `metric`.  For executable objects (`data_rule`, `data_rule_set` and `metric`), any execution of those rules within the conditions specified (ie. changes_in_last_hours) will also be included.  Other objects within the project (virtual tables, virtual columns, folders, etc) are all always exported.

**Examples**:

```yml
ibm_infosvr_impexp_ia_mappings:
  - { type: "DataSource", attr: "host", from: "MY_HOST", to: "YOUR_HOST" }
  - { type: "DataSource", attr: "name", from: "MYDB", to: "YOURDB" }
  - { type: "Schema", attr: "name", from: "MY_SCH", to: "YOUR_SCH" }

ibm_infosvr_impexp_ia_import:
  - src: "/tmp/ia_fullproject.xml"
    project: "UGDefaultWorkspace"
    map: "{{ ibm_infosvr_impexp_ia_mappings }}"

ibm_infosvr_impexp_ia_export:
  - dest: "cache/ia_fullproject.xml"
    project: "UGDefaultWorkspace"
    objects:
      - type: data_rule_definition
      - type: data_rule_set_definition
      - type: data_rule
      - type: data_rule_set
      - type: metric

ibm_infosvr_impexp_ia_export:
  - dest: "cache/ia_project_delta.xml"
    project: "UGDefaultWorkspace"
    objects:
      - type: data_rule_definition
        changes_in_last_hours: 48
      - type: data_rule_set_definition
        changes_in_last_hours: 48
      - type: data_rule
        changes_in_last_hours: 48
      - type: data_rule_set
        changes_in_last_hours: 48
      - type: metric
        changes_in_last_hours: 48
```

## Extended data sources

**Imports**:

```yml
ibm_infosvr_impexp_xa_import:
  - { src: "<path>", overwrite: <boolean> }
  - ...
```

The only required parameter for the import is the `src` file from which to load them.

**Exports**:

```yml
ibm_infosvr_impexp_xa_export:
  - dest: "<path>"
    changes_in_last_hours: <int>
    type: "<string>"
    conditions:
      - { property: "<string>", operator: "<string>", value: "<value>" }
      - ...
  - ...
```

Conditions are purely optional, take the form of the IGC REST API's conditions (see http://www.ibm.com/support/docview.wss?uid=swg27047054) and are currently always AND'd (all conditions must be met). Furthermore, they must currently be common amongst all sub-types of the extended data source objects (eg. "name", "short_description", "assigned_to_terms", etc). The `changes_in_last_hours` is also optional; if used, specify the number of hours prior to the playbook running from which to identify (and extract) any changes.

The `type` is required, and must be one of `application`, `file`, or `stored_procedure_definition`. When using change-detection, the export automatically looks for any changes to sub-objects of these (eg. any changed `method`s for `application`), but will always extract the full outer containment object. For example, if only one `method` of an `application` has changed, it will still extract the entire `application` with all of its `method`s and other sub-objects.

**Examples**:

```yml
ibm_infosvr_impexp_xa_import:
  - { src: "import.csv", overwrite: True }

ibm_infosvr_impexp_xa_export:
  - dest: "cache/xa_apps_changed_in_last48hrs.csv"
    changes_in_last_hours: 48
    type: application
  - dest: "cache/xa_files_changed_in_last48hrs.csv"
    changes_in_last_hours: 48
    type: file
  - dest: "cache/xa_sprocs_changed_in_last48hrs.csv"
    changes_in_last_hours: 48
    type: stored_procedure_definition
```

## Extension mapping documents

**Imports**:

```yml
ibm_infosvr_impexp_xm_import:
  - { src: "<path>", folder: "root/<string>", overwrite: <boolean> }
  - ...
```

The only required parameter for the import is the `src` file from which to load them. If provided, the `folder` must always start with `root/` (using `/` as the subsequent separator for the rest of the folder structure). Folders are created if they do not already exist.

**Exports**:

```yml
ibm_infosvr_impexp_xm_export:
  - dest: "<path>"
    changes_in_last_hours: <int>
  - ...
```

The `changes_in_last_hours` is optional; if used, specify the number of hours prior to the playbook running from which to identify (and extract) any changes.

**Examples**:

```yml
ibm_infosvr_impexp_xm_import:
  - { src: "import.csv", folder: "root/Some/Folder", overwrite: True }

ibm_infosvr_impexp_xm_export:
  - dest: "cache/xm_changed_in_last48hrs.zip"
    changes_in_last_hours: 48
```

## Glossary assets

**Imports**:

```yml
ibm_infosvr_impexp_bg_mappings:
  - { type: "<string>", attr: "<string>", from: "<value>", to: "<value>" }
  - ...

ibm_infosvr_impexp_bg_import:
  - { src: "<path>", map: "<list>", merge: "<string>" }
  - ...
```

Mappings are purely optional, and the only required parameters for the import are the `src` file from which to load them and the `merge` option, which must be one of `ignore`, `overwrite`, `mergeignore`, or `mergeoverwrite`.

The order of importing is also important for glossary assets, since different asset types can be split across different XML files. You should always import in this order to ensure dependencies are met:

1. `label`
1. `category`
1. `term`
1. `information_governance_policy`
1. `information_governance_rule`

**Exports**:

```yml
ibm_infosvr_impexp_bg_export:
  - dest: "<path>"
    categories: "<string>"
    options: "<string>"
    objects:
      - type: "<string>"
        changes_in_last_hours: <int>
        conditions:
          - { property: "<string>", operator: "<string>", value: "<value>" }
          - ...
      - ...
```

The required parameters for an export are the `dest` file into which to capture and `type` of assets to export (under `object`). `type` must be one of `category`, `term`, `information_governance_policy`, `information_governance_rule`, or `label`.

Because of the way the export for these assets works, you may be able to improve the efficiency by using the optional `categories` limiter. This will not be considered in coordination with the `conditions`, so should be used only for optimisation purposes: to limit the amount of content exported, you can specify multiple categories as comma-separated in the `categories` string. The path separator for categories is `::`. (Leaving this option out will export all categories initially, and later restrict these based on the `type`s and `conditions` specified by the other options.)

**Examples**:

```yml
ibm_infosvr_impexp_bg_mappings:
  - { type: "HostSystem", attr: "name", from: "MY_HOST", to: "YOUR_HOST" }

ibm_infosvr_impexp_bg_import:
  - { src: "import.isx", map: "{{ ibm_infosvr_impexp_bg_mappings }}", merge: "mergeoverwrite" }

ibm_infosvr_impexp_bg_export:
  - dest: "cache/bg_all_terms.xml"
    options: "-includeassignedassets -includestewardship -includeassetcollections -includelabeledassets -includetermhistory -allpoliciesrules -devglossary"
    objects:
      - type: "term"
  - dest: "cache/bg_all_rules.xml"
    options: "-includeassignedassets -includestewardship"
    objects:
      - type: "information_governance_rule"
  - dest: "cache/bg_some.xml"
    options: "-includelabeledassets -includetermhistory"
    categories: "Samples::A,Inspiration::Others"
    objects:
      - type: "term"
        changes_in_last_hours: 48
        conditions:
          - { property: "label.name", operator: "=", value: "Public" }
      - type: "information_governance_rule"
        changes_in_last_hours: 48
```

## IGC metadata relationships

**Imports**:

```yml
ibm_infosvr_impexp_igc_relns_mappings:
  - { type: "<string>", property: "<string>", from: "<value>", to: "<value>" }
  - ...

ibm_infosvr_impexp_igc_relns_import:
  - src: "<path>"
    type: "<string>"
    relationship: "<string>"
    map: "<list>"
    mode: "<string>"
    replace_type: "<string>"
    conditions:
      - { property: "<string>", operator: "<string>", value: "<value>" }
      - ...
  - ...
```

The required parameters for the import are the `src` file from which to load them, the `type` of the asset for which to load relationships, the `relationship` property to load and the `mode` to use when loading them.

Mappings are optional, but when specified take a slightly different form from mappings for other asset types. The `type` should match the REST API asset type string (see `GET /ibm/iis/igc-rest/v1/types` in your environment for choices) while the `property` should match the REST API asset property string (see `GET /ibm/iis/igc-rest/v1/types/<asset_type>?showEditProperties=true&showViewProperties=true&showCreateProperties=true` in your environment for choices). The `from` can be a Python regular expression against which all matches will be replaced by the `to`.

The `mode` must be one of the following:

- `APPEND` - only add these relationships to the asset, don't change any existing relationships
- `REPLACE_ALL` - replace all relationships on the specified asset (`type`) and property (`relationship`) with the ones being loaded
- `REPLACE_SOME` - replace only a portion of the relationships. For this option, you must additionally specify at least the `replace_type`, giving a REST API asset type specifying the related asset types you want to replace. You can also optionally provide a further list of `conditions` that apply to the `replace_type` asset. For example, if you specify `database_column` as the `replace_type`, and a condition of `name = XYZ` the import will only replace related database columns where the name of the database column is XYZ and leave all other relationships alone.

**Exports**:

```yml
ibm_infosvr_impexp_igc_relns_export:
  - dest: "<path>"
    changes_in_last_hours: <int>
    type: "<string>"
    relationship: "<string>"
    limit:
      - "<string>"
      - ...
    conditions:
      - { property: "<string>", operator: "<string>", value: "<value>" }
      - ...
  - ...
```

The `dest`, `type` and `relationship` are required, and follow the same meaning and options as described above for the import. (`dest` describes where the relationships should be stored, equivalent of `src` for the import.)

Conditions are purely optional, take the form of the IGC REST API's conditions (see http://www.ibm.com/support/docview.wss?uid=swg27047054) and are currently always AND'd (all conditions must be met). The `changes_in_last_hours` is also optional; if used, specify the number of hours prior to the playbook running from which to identify (and extract) any changes.

Finally, `limit` is also optional: when used it should provide a list of the related asset types to retain as relationships.

**Examples**:

```yml
ibm_infosvr_impexp_igc_relns_mappings:
  - { type: "host", property: "name", from: "MY", to: "YOUR" }

ibm_infosvr_impexp_igc_relns_import:
  - src: terms2assets.json
    type: term
    relationship: assigned_assets
    map: "{{ ibm_infosvr_impexp_igc_relns_mappings }}"
    mode: REPLACE_SOME
    replace_type: database_column
    conditions:
      - { property: "database_table_or_view.name", operator: "=", value: "MYTABLE" }

ibm_infosvr_impexp_igc_relns_export:
  - dest: cache/terms2assets_underSomeCategory_changed_in_last48hrs_only_dbcols.json
    type: term
    relationship: assigned_assets
    changes_in_last_hours: 48
    limit:
      - database_column
    conditions:
      - { property: "category_path._id", operator: "=", value: "6662c0f2.ee6a64fe.ko15n9ej3.cq2arq8.ld2q5u.2qonhvupr4m3b68ouj93c" }
```

## Operational metadata (OMD)

**Imports**:

```yml
ibm_infosvr_impexp_omd_import:
  - src: "<path>"
  - ...
```

The only required parameter for the import is the `src` directory from which to load the operational metadata flow files. (This should refer to a directory rather than an individual file.)

As part of the import process, the following actions will be taken:

- The original engine tier's host will be replaced by the target engine tier's host -- this is the only way to ensure the operational metadata can be loaded into the target environment. Note that the project and job that the operational metadata refers to should already exist as well in the target environment (ie. ensure you import the jobs through the ibm_infosvr_impexp_ds_import variable; the role will ensure those are loaded before trying to import this operational metadata).
- Lineage will be enabled on any projects referred to by the operational metadata flows being imported -- if lineage is not enabled on the project, then the lineage that is loaded through the OMD import will not show up.

**Exports**:

```yml
ibm_infosvr_impexp_omd_export:
  - dest: "<path>"
    changes_in_last_hours: <int>
  - ...
```

The `dest` is required, and describes where the operational metadata flow files should be stored, equivalent of `src` for the import. (The `dest` should refer to a directory rather than an individual file.)

**Examples**:

```yml
ibm_infosvr_impexp_omd_import:
  - src: cache/omd_exports/

ibm_infosvr_impexp_omd_export:
  - dest: cache/omd_exports/
    changes_in_last_hours: 48
```

## Validation framework

A simple validation framework is also provided to, for example, confirm the expected results of a load of metadata.  In essence the framework takes an arbitrary set of conditions and uses the IGC REST API to confirm that those conditions exist in the environment in question.

```yml
ibm_infosvr_impexp_validate:
  that:
    - number_of: "<string>"
      meeting_any_conditions | meeting_all_conditions:
        - { property: "<string>", operator: "<string>", value: "<string>" }
        - ...
      is: <int>
    - ...
```

Each set of conditions applies to only a single asset type, but multiple asset types and sets of conditions can be defined -- all as subsets under an `ibm_infosvr_impexp_validate.that` variable.  The suboptions are:
- `number_of`: defines the asset type that should be counted (eg. `term`, `database_column`, etc)
- `meeting_any_conditions`: does a logical OR of the specified conditions
- `meeting_all_conditions`: does a logical AND of the specified conditions (takes precedence over `meeting_any_conditions` if both are specified)
- `is`: defines the expected count of assets that should meet the specified criteria

**Examples**:

```yml
ibm_infosvr_impexp_validate:
  that:
    - number_of: category
      meeting_any_conditions:
        - { property: "parent_category.name", operator: "=", value: "Samples" }
        - { property: "parent_category.parent_category.name", operator: "=", value: "Samples" }
        - { property: "parent_category.parent_category.parent_category.name", operator: "=", value: "Samples" }
      is: 20
    - number_of: term
      meeting_all_conditions:
        - { property: "category_path._id", operator: "=", value: "6662c0f2.ee6a64fe.ko15n9ej3.cq2arq8.ld2q5u.2qonhvupr4m3b68ouj93c" }
      is: 1200
    - number_of: database_column
      meeting_all_conditions:
        - { property: "database_table_or_view.database_schema.database.host.name", operator: "=", value: "MY_HOST.SOMEWHERE.COM" }
        - { property: "database_table_or_view.database_schema.database.name", operator: "=", value: "MYDB" }
        - { property: "database_table_or_view.database_schema.name", operator: "=", value: "MYSCH" }
        - { property: "assigned_to_terms.category_path._id", operator: "=", value: "6662c0f2.ee6a64fe.ko15n9ej3.cq2arq8.ld2q5u.2qonhvupr4m3b68ouj93c" }
      is: 1000
```

In the example above:
- the first validation is that there are a total of 20 categories up to 3 levels deep under the `Samples` category
- the second validation is that there are 1200 terms under a category with RID `6662c0f2.ee6a64fe.ko15n9ej3.cq2arq8.ld2q5u.2qonhvupr4m3b68ouj93c`
- the third validation is that there are 1000 database columns in in the `MYSCH` schema of the `MYDB` database on the `MY_HOST.SOMEWHERE.COM` system which are assigned to terms somewhere under the category with RID `6662c0f2.ee6a64fe.ko15n9ej3.cq2arq8.ld2q5u.2qonhvupr4m3b68ouj93c`

## License

Apache 2.0

## Author Information

Christopher Grote
