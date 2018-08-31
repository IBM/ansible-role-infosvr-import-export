# Conditions

[<- Back to the overview](../README.md)

For many asset types, conditions can optionally be specified to limit the assets that are extracted or loaded. The conditions should be specified in the form required by IGC's REST API (see http://www.ibm.com/support/docview.wss?uid=swg27047054), and should generally be relative to the asset type being extracted or loaded.

Note that in most of the examples, the simple `property`, `operator`, `value` conditions are used; however, as indicated in the link above (and examples below) the REST API is not limited to this paradigm. For any asset type where conditions can be specified, any of the options below can be used.

For the names of the properties of various asset types, check the REST API type documentation for your release at: https://github.com/IBM/node-igc-rest/tree/master/doc

## Exact matches

In the simplest form, a condition specifies that a given `property` has some match against a `value`, defined by some `operator`. For instance, this condition checks that the name of an asset is precisely "Some Name".

```yml
conditions:
  - { property: "name", operator: "=", value: "Some Name" }
```

## Substring matches

Other operators can be used to do substring matches:

- `like %{0}` = ends with
- `like {0}%` = starts with
- `like %{0}%` = contains

```yml
conditions:
  - { property: "name", operator: "like %{0}", value: "my" }
  - { property: "name", operator: "like {0}%", value: "my" }
  - { property: "name", operator: "like %{0}%", value: "my" }
```

## Related properties

It is also possible to check the value of related assets' properties indirectly, using dot-notation. For example, the following would check that the name of the host on which the database_table resides is "A.B.COM". (database_table as an asset type does not record a host name, but the database in which the schema in which the table resides does -- hence the dot-notation to traverse those relationships to get to the host name.)

```yml
conditions:
  - { property: "database_schema.database.host.name", operator: "=", value: "A.B.COM" }
```

## Other operators

Other operators also exist:

- `between` can be used with `min` and `max` to look for a numerical value within a range (note that dates are actually numerical epoch values to millisecond granularity)
- `isNull` can be used to check whether a particular value exists: particularly useful to check that a relationship does not exist
- `negated` can be applied to conditions (ie. `isNull`) to reverse the check (eg. check that a relationship does exist)

```yml
conditions:
  - { property: "created_on", operator: "between", min: -1, max: 1000000000 }
  - { property: "assigned_to_terms", operator: "isNull" }
  - { property: "assigned_to_terms", operator: "isNull", negated: True }
```

[<- Back to the overview](../README.md)
