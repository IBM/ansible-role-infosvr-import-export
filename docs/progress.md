# Workflow progression

[<- Back to the overview](../README.md)

You can use the following variable and its settings to automate the progression (or regression) of items within the workflow.

```yml
progress:
  - type: <string>
    from_state: <string>
    action: <string>
    comment: <string>
    conditions:
      - { property: "<string>", operator: "<string>", value: "<string>" }
      - ...
  - ...
```

The required inputs are:

- `type` -- which must be one of: `category`, `term`, `information_governance_policy`, `information_governance_rule`
- `action` -- which must be one of: `discard`, `return`, `request`, `approve`, `publish`

The optional `from_state` can limit the objects that are progressed based on their current state in the workflow (one of `DRAFT`, `WAITING_APPROVAL`, `APPROVED`, or `ALL`). If not specified the default of `ALL` is used, and assets are progressed potentially multiple states in order to achieve the final state specified by `action`.

The optional `comment` will be used as the workflow comment for each state change that is made.

Finally, the optional [`conditions`](conditions.md) specify which items within the workflow should be acted upon.  This can be expressed as a matter of one or more [conditions](conditions.md) that are relative to the `type` specified. Note that if you specify a RID in any of these, it needs to be a development-glossary-specific RID.

## Examples

The following will publish any terms in the workflow (in any state) with the label "Public", and use the comment "Auto-publication by an import process" for each state change.

```yml
progress:
  - type: term
    action: publish
    comment: "Auto-publication by an import process"
    conditions:
      - { property: "label.name", operator: "=", value: "Public" }
```

[<- Back to the overview](../README.md)
