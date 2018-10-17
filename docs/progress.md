# Workflow progression

[<- Back to the overview](../README.md)

You can use the following variable and its settings to automate the progression (or regression) of items within the workflow.

```yml
progress:
  - assets_of_type: <string>
    using_action: <string>
    with_options:
      from_state: <string>
      only_with_conditions:
        - { property: "<string>", operator: "<string>", value: "<value>" }
        - ...
      with_comment: <string>
      only_when_compared_to_published: <string>
  - ...
```

The required inputs are:

- `assets_of_type` -- which must be one of: `category`, `term`, `information_governance_policy`, `information_governance_rule`
- `using_action` -- which must be one of: `discard`, `return`, `request`, `approve`, `publish`

The options under `with_options` are all optional:

- `from_state` limits the objects that are progressed based on their current state in the workflow (one of `DRAFT`, `WAITING_APPROVAL`, `APPROVED`, or `ALL`). If not specified the default of `ALL` is used, and assets are progressed potentially multiple states in order to achieve the final state specified by `using_action`.
- `with_comment` will be used as the workflow comment for each state change that is made.
- `only_with_conditions` specifies which items within the workflow should be acted upon.  This can be expressed as a matter of one or more [conditions](conditions.md) that are relative to the `assets_of_type` specified. Note that if you specify a RID in any of these, it needs to be a development-glossary-specific RID.
- `only_when_compared_to_published` must be one of the following:

  - `NEW`: specifies that only workflow entries that are new (have no published version) should be acted upon
  - `SAME`: specifies that only workflow entries that are the same as their published version should be acted upon
  - `SAME_OR_NEW`: specifies that only workflow entries that are either the same as their published version, or have no published version (are new) should be acted upon
  - `DIFFERENT`: specifies that only workflow entries that are different from their published version should be acted upon (including new entries that do not yet have a published version)

## Examples

The following will publish any terms in the workflow (in any state) with the label "Public", and use the comment "Auto-publication by an ingest process" for each state change.

```yml
progress:
  - assets_of_type: term
    using_action: publish
    with_options:
      with_comment: "Auto-publication by an ingest process"
      only_with_conditions:
        - { property: "label.name", operator: "=", value: "Public" }
```

[<- Back to the overview](../README.md)
