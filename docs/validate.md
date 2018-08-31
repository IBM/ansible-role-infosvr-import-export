# Validation framework

[<- Back to the overview](../README.md)

A simple validation framework is provided to, for example, confirm the expected results of a load of metadata.  In essence the framework takes an arbitrary set of [conditions](conditions.md) and uses the IGC REST API to confirm that those conditions exist in the environment in question.

```yml
validate:
  that:
    - number_of: <string>
      meeting_any_conditions | meeting_all_conditions:
        - { property: "<string>", operator: "<string>", value: "<string>" }
        - ...
      is: <int>
    - ...
```

Each set of [conditions](conditions.md) applies to only a single asset type, but multiple asset types and sets of conditions can be defined -- all as subsets under a `validate.that` variable.  The suboptions are:
- `number_of`: defines the asset type that should be counted (eg. `term`, `database_column`, etc)
- `meeting_any_conditions`: does a logical OR of the specified conditions
- `meeting_all_conditions`: does a logical AND of the specified conditions (takes precedence over `meeting_any_conditions` if both are specified)
- `is`: defines the expected count of assets that should meet the specified criteria

The complete set of criteria will be run through an Ansible assertion -- any failure of the criteria being met in the environment will result in a failed assertion (so a failure in Ansible), giving details of each assertion that failed.

## Examples

```yml
validate:
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

[<- Back to the overview](../README.md)
