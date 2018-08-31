# Mappings

[<- Back to the overview](../README.md)

As part of importing assets, many asset types can have a mapping optionally applied. Mappings can be used to rename objects and change their containment hierarchy -- particularly useful when moving assets from one environment to another and certain characteristics (ie. host name where the asset resides) may need to change to reflect the new target environment.

Currently, different styles of mappings are applied depending on the asset type. A general recommendation is to build playbooks that define both style of mappings between values, and abstract the need for users of the playbooks to worry about the differences by simply requesting the users to provide target values for their import. (The source values should be known by you when writing the playbook, given static content that's being loaded.)

## ISX-style

ISX-style mappings make use of the `mapping.xml` file format used by the `istool` command. With this approach, only a limited set of assets and their properties can be mapped / renamed: the full list is documented at https://www.ibm.com/support/knowledgecenter/en/SSZJPZ_11.7.0/com.ibm.swg.im.iis.iisinfsv.assetint.doc/topics/r_using_mapping_file.html

These mappings are specified using:

```yml
map:
  - { type: "", attr: "", from: "", to: "" }
```

Where the `type` is equivalent to the `classname` from the documentation linked above, and the `attr` is equivalent to the `attrname`. The `from` defines the existing value that should be matched, and the `to` defines the value that should be used as a replacement. All values are taken as literal strings; regular expressions are not allowed for these mappings.

The role will automatically take care of applying the correct model versions within the `mapping.xml` based on the target environment to which the asset are being loaded.

## REST-style

REST-style mappings apply renaming and mapping as part of the role itself, before loading to the target system. These apply to certain assets only; however, with this approach virtually any asset and its properties can be mapped / renamed. For the names of the properties of various asset types, check the REST API type documentation for your release at: https://github.com/IBM/node-igc-rest/tree/master/doc

These mappings are specified using:

```yml
map:
  - { type: "", property: "", from: "", to: "" }
```

Where the `type` is the REST API asset type, and `property` the name of the REST API asset property from the documentation linked above. The `from` defines the existing value that should be matched, and the `to` defines the value that should be used as a replacement. Both the `from` and `to` can make use of Python regular expressions for matching and replacement.

For example, the following will match the complete name of a data rule, and then replace it by pre-pending it with the value of a variable followed by `_XYZ_`. So if the value of `some_variable` were `MYNAME` and the name of the `data_rule` were `DR_123` the replacement would be `MYNAME_XYZ_DR_123`.

```yml
map:
  - { type: "data_rule", property: "name", from: "(.*)", to: "{{ some_variable }}_XYZ_\\1" }
```

## Information Analyzer-style

Information Analyzer-style mappings apply renaming and mapping as part of the role itself, before loading to the target system, but only to Information Analyzer objects. These are based on the XML elements and attributes of the documented [Information Analyzer REST API's schema](https://www.ibm.com/support/knowledgecenter/en/SSZJPZ_11.7.0/com.ibm.swg.im.iis.ia.restapi.doc/topics/c_xsd.html)

These mappings are specified using:

```yml
map:
  - { type: "", attr: "", from: "", to: "" }
```

Where the `type` is one of the XML elements, and `attr` is an XML attribute from the schema linked above. The `from` defines the existing value that should be matched, and the `to` defines the value that should be used as a replacement. Both the `from` and `to` can make use of Python regular expressions for matching and replacement.

For example, the following will match the complete name of a data rule or data rule set, and then replace it by pre-pending it with the value of a variable followed by `_XYZ_`. So if the value of `some_variable` were `MYNAME` and the name of the data rule (set) were `DR_123` the replacement would be `MYNAME_XYZ_DR_123`.

```yml
map:
  - { type: "ExecutableRule", property: "name", from: "(.*)", to: "{{ some_Variable }}_XYZ_\\1" }
```

[<- Back to the overview](../README.md)
