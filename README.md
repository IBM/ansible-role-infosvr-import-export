# ansible-role-infosvr-import-export

Ansible role for automating the import and export of content and structures within IBM InfoSphere Information Server.

## Requirements

- Ansible v2.4.x
- `dsadm`-become-able network access to an IBM Information Server environment
- Inventory group names setup the same as `IBM.infosvr` role

The role optionally uses privilege escalation to root to automate very few setup tasks. If your environment does not allow this privilege escalation, please ensure these pre-requisites are already fulfilled manually in your environment and change the `defaults/main.yml` variable `ibm_infosvr_impexp_priv_escalate` to `False` (this will skip any attempts at privilege escalation to root).

In case you set the escalation to false, ensure that the following are done in your target environment prior to running the role:

- Installation of the `python-requests` library (eg. via `yum`)
- Installation of the `python-lxml` library (eg. via `yum`)
- The `{IS_HOME}/ASBServer/logs` directory of the domain tier must be write-able by the user running the role (as well as each of the `.log` files in that directory)

## Role Variables

See `defaults/main.yml` for inline documentation, and the example below for the main variables needed. For any clarification on the expected action variables and sub-structures for the various object types, refer to the documentation below.

By default, the role will do SSL verification of self-signed certificates by first retrieving the root certificate directly from the domain tier of the environment. This is controlled by the `ibm_infosvr_impexp_verify_selfsigned_ssl` variable of the role: if you want to only verify against properly signed and trusted SSL certificates, you can set this variable to `False` and any self-signed domain tier certificate will no longer be trusted.

## Example Playbook

The role includes the ability to both export and import a number of different asset types in Information Server. The role can be imported into another playbook providing only the variables of interest in order to restrict the assets to include in either an import or export (empty variables will mean the role will skip any processing of those asset types). (Thus the need for Ansible v2.4.x and the `import_role` module.)

The first level of variables provided to the role define the broad actions to take, and will always run in this order regardless of the order in which they're specified:

1. `gather` - retrieve details about the environment (ie. version numbers)
1. `export` - extract assets from an environment into file(s)
1. `import` - load assets into an environment from file(s)
1. `progress` - move assets through a workflow (will do nothing if workflow is not enabled)
1. `validate` - validate an environment is in an expected state using objective asset counts

Any missing variables will simply skip that set of actions.

For example:

```yml
- import_role: name=IBM.infosvr-import-export
  vars:
    isx_mappings:
      - { type: "HostSystem", attr: "name", from: "MY_HOST", to "YOUR_HOST" }
    gather: True
    import:
      datastage:
        - from: /some/directory/file1.isx
          into_project: dstage1
          with_options:
            overwrite: True
      common:
        - from: file2.isx
          with_options:
            transformed_by: "{{ isx_mappings }}"
            overwrite: True
    validate:
      that:
        - number_of: dsjob
          meeting_all_conditions:
            - { property: "transformation_project.name", operator: "=", value: "dstage1" }
          is: 5
        - number_of: database_table
          meeting_all_conditions:
            - { property: "database_schema.database.host.name", operator: "=", value: "YOUR_HOST" }
          is: 10
```

... will start by gathering environment details from the environment the playbook is running against.

It will then import the common metadata from a file `file2.isx` (expected a `files/` sub-directory relative to your playbook), renaming any hostnames from `MY_HOST` to `YOUR_HOST`, and overwriting any existing assets with the same identities. It will then import the DataStage assets from `/some/directory/file1.isx` into the `dstage1` project, overwriting any existing assets with the same identities.

Note that the order in which the variables are defined does not matter: the role will take care of exporting and importing objects in the appropriate order to ensure dependencies between objects are handled (ie. that common and business metadata are loaded before relationships, etc). However, the order of multiple objects defined within a given type _may_ matter, depending on your own dependencies.

Finally, the playbook will validate the load has resulted in the expected assets in the target environment: 5 DataStage jobs in the `dstage1` project and 10 database tables in some combination of schemas and databases on the `YOUR_HOST` server.

(Since neither `progress` nor `export` actions are specified, they will not be run.)

## Action (and object) structures

The following describes all of the actions and object types currently covered by this role, and their expected structures.

1. `gather` - [environment detail gathering](docs/gather.md)
1. `export` / `import` metadata asset types (as with the actions above, the ordering below defines the order in which these object types will be extracted and loaded -- irrespective of the order in which they appear within an action)
    1. `customattrs` - [custom attribute definitions](docs/customattrs.md)
    1. `common` - [common metadata](docs/common.md) (should be considered low-level, and where possible avoided by using one of the type-specific options)
    1. `logicalmodel` - [logical model metadata](docs/logicalmodel.md)
    1. `physicalmodel` - [physical model metadata](docs/physicalmodel.md)
    1. `mdm` - [master data management model metadata](docs/mdm.md)
    1. `database` - [database metadata](docs/database.md)
    1. `datafile` - [data file metadata](docs/datafile.md)
    1. `dataclass` - [data class metadata](docs/dataclass.md)
    1. `datastage` - [DataStage assets](docs/datastage.md)
    1. `ds_vars` - [DataStage project variables](docs/ds_vars.md)
    1. `infoanalyzer` - [Information Analyzer assets](docs/infoanalyzer.md)
    1. `extendedsource` - [extended data sources](docs/extendedsource.md)
    1. `extensionmap` - [extension mapping documents](docs/extensionmap.md)
    1. `glossary` - [glossary assets](docs/glossary.md)
    1. `relationships` - [metadata relationships](docs/relationships.md)
    1. `omd` - [operational metadata](docs/omd.md)
1. `progress` - [progressing the workflow](docs/progress.md)
1. `validate` - [validation framework](docs/validate.md)

For the `export` and `import`, [mappings](docs/mappings.md) can be applied to transform metadata between environments (eg. renaming, changing containment, etc), and most asset types can also be limited through the use of [conditions](docs/conditions.md).

Note that you can generally write these variable structures using any form supported by Ansible, eg. these are all equivalent and simply up to your personal preference:

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

## License

Apache 2.0

## Author Information

Christopher Grote
