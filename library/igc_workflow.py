#!/usr/bin/python

###
# Copyright 2018 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: igc_workflow

short_description: Progresses assets through an IBM IGC workflow

description:
  - Progresses assets through an IBM IGC workflow.
  - Based on the specified conditions and workflow state.

version_added: "2.4"

author:
  - Christopher Grote (@cmgrote)

options:
  host:
    description:
      - Hostname of the domain tier of the IGC environment
    required: true
    type: str
  port:
    description:
      - Port of the domain tier of the IGC environment
    required: true
    type: int
  user:
    description:
      - Username to use to access IGC REST API
    required: true
    type: str
  password:
    description:
      - Password to use to access IGC REST API
    required: true
    type: str
  asset_type:
    description:
      - The IGC REST asset type (eg. C(term)) to progress through the workflow.
      - Must be business metadata type (those that participate in workflow).
    required: true
    type: str
    choices: [ "category", "term", "information_governance_policy", "information_governance_rule" ]
  from_state:
    description:
      - The originating state in the workflow from which to progress.
      - Will default to C(ALL) (will apply target regardless of current state).
    required: false
    type: str
    choices: [ "ALL", "DRAFT", "WAITING_APPROVAL", "APPROVED" ]
  action:
    description:
      - The action in the workflow to take against the asset.
    required: true
    type: str
    choices: [ "discard", "return", "request", "approve", "publish" ]
  comment:
    description:
      - The comment to log as part of the workflow progression.
    required: false
    type: str
  conditions:
    description:
      - A list conditions by which to query the assets in the workflow.
      - Could be left empty if you want to progress all assets of a given type.
    required: false
    type: list
    default: []
    suboptions:
      property:
        description:
          - The property of the I(asset_type) to set the condition against.
          - (See "GET /ibm/iis/igc-rest/v1/types/<asset_type>?showViewProperties=true" in your environment.)
        required: true
        type: str
      operator:
        description:
          - The comparison operation to use for the condition
        required: true
        type: str
        choices: [ "=", ">", "<", ">=", "<=", "in", "like", "between" ]
      value:
        description:
          - The value to compare the I(property) to, based on the I(operator)
        required: true
        type: str
  condition_join:
    description:
      - How the conditions should be considered.
      - Only required when a set of I(conditions) has been provided; will default to C(AND).
    required: false
    type: str
    choices: [ "AND", "OR" ]
  cert:
    description:
      - The path to a certificate file to use for SSL verification against the server.
    required: false
    type: path
  batch:
    description:
      - The number of assets to retrieve per REST API call.
    required: false
    type: int
    default: 100

requirements:
  - requests
'''

EXAMPLES = '''
- name: publish all terms two levels under category 'Samples'
  igc_workflow:
    host: infosvr.vagrant.ibm.com
    port: 9446
    user: isadmin
    password: isadmin
    asset_type: term
    action: publish
    conditions:
      - property: "parent_category.parent_category.name"
        operator: "="
        value: "Samples"
'''

RETURN = '''
queries:
  description:
    - The JSON queries used to retrieve the assets.
  returned: always
  type: list
asset_count:
  description:
    - A numeric indication of the number of assets that were acted upon using the provided criteria.
  type: int
  returned: always
assets:
  description:
    - A list of JSON objects representing the assets acted upon using the provided criteria.
  type: list
  returned: always
workflow_actions:
  description:
    - A list of JSON objects providing action results.
  type: list
  returned: always
workflow_failed:
  description:
    - A list of JSON objects providing any failed actions.
  type: list
  returned: always
workflow_enabled:
  description:
    - An indication of whether the workflow is even enabled in the environment or not.
  type: bool
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.igc_rest import RestIGC


def main():

    module_args = dict(
        host=dict(type='str', required=True),
        port=dict(type='str', required=True),
        user=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        asset_type=dict(type='str', required=True),
        from_state=dict(type='str', required=False, default='ALL'),
        action=dict(type='str', required=True),
        comment=dict(type='str', required=False, default=''),
        conditions=dict(type='list', required=False, default=[]),
        condition_join=dict(type='str', required=False, default='AND'),
        cert=dict(type='path', required=False),
        batch=dict(type='int', required=False, default=100)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        queries=[],
        asset_count=0,
        assets=[],
        workflow_actions=[],
        workflow_failed=[],
        workflow_enabled=False
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    # Setup REST API connectivity via module_utils.igc_rest class
    igcrest = RestIGC(
        module,
        result,
        username=module.params['user'],
        password=module.params['password'],
        host=module.params['host'],
        port=module.params['port'],
        cert=module.params['cert']
    )

    conditions = module.params['conditions']
    asset_type = module.params['asset_type']
    from_state = module.params['from_state']
    action = module.params['action']
    comment = module.params['comment']

    # First check whether workflow is even enabled
    if igcrest.isWorkflowEnabled():
        result['workflow_enabled'] = True
    else:
        module.exit_json(**result)

    # Basic query
    reqJSON = {
        "pageSize": module.params['batch'],
        "workflowMode": "draft",
        "properties": ['name', 'workflow_current_state'],
        "types": [asset_type],
        "where": {
            "conditions": [],
            "operator": "and"
        }
    }

    if from_state == 'ALL':
        reqJSON['where']['conditions'].append({"property": "workflow_current_state",
                                               "operator": "isNull",
                                               "negated": True})
    else:
        reqJSON['where']['conditions'].append({"property": "workflow_current_state",
                                               "operator": "=",
                                               "value": from_state.upper()})

    # If conditions have been provided, nest them within the outer
    # workflow state condition
    if len(conditions) > 0:
        reqJSON['where']['conditions'].append({"conditions": conditions,
                                               "operator": module.params['condition_join'].lower()})

    jsonResults = igcrest.search(reqJSON)

    # Ensure search worked before proceeding
    if jsonResults == '':
        module.fail_json(msg='IGC query failed', **result)

    result['asset_count'] = len(jsonResults)
    result['assets'] = jsonResults

    assets_by_state = {
        "DRAFT": [],
        "WAITING_APPROVAL": [],
        "APPROVED": []
    }

    for item in jsonResults:
        # For some reason 'workflow_current_state' is an array
        # (but should only ever have one item, so always take first?)
        current_state = item['workflow_current_state'][0]
        assets_by_state[current_state].append(item['_id'])

    # Easy case: we're only moving from a particular state
    if from_state != 'ALL':
        assets_to_move = assets_by_state[from_state]
        action_to_take = getNextAction(action,
                                       from_state)
        moveToNextState(igcrest,
                        result,
                        assets_to_move,
                        from_state,
                        action_to_take,
                        action,
                        comment)
    # More complicated case: we want to move from all states
    else:
        # Need to iterate state-by-state...
        draft_assets = assets_by_state['DRAFT']
        if len(draft_assets) > 0:
            action_to_take = getNextAction(action, 'DRAFT')
            moveToNextState(igcrest,
                            result,
                            draft_assets,
                            'DRAFT',
                            action_to_take,
                            action,
                            comment)
        waiting_assets = assets_by_state['WAITING_APPROVAL']
        if len(waiting_assets) > 0:
            action_to_take = getNextAction(action, 'WAITING_APPROVAL')
            moveToNextState(igcrest,
                            result,
                            waiting_assets,
                            'WAITING_APPROVAL',
                            action_to_take,
                            action,
                            comment)
        approved_assets = assets_by_state['APPROVED']
        if len(approved_assets) > 0:
            action_to_take = getNextAction(action, 'APPROVED')
            moveToNextState(igcrest,
                            result,
                            waiting_assets,
                            'APPROVED',
                            action_to_take,
                            action,
                            comment)

    # Close the IGC REST API session
    igcrest.closeSession()

    module.exit_json(**result)


def getNextAction(final_action,
                  current_state):
    # List of states mapped to next actions (progressive state always in [0])
    workflow_states_to_actions = {
        "DRAFT": ['request', 'discard'],
        "WAITING_APPROVAL": ['approve', 'return'],
        "APPROVED": ['publish', 'return']
    }
    next_action = final_action
    if final_action in ['request', 'approve', 'publish']:
        next_action = workflow_states_to_actions[current_state][0]
    elif final_action in ['return', 'discard']:
        next_action = workflow_states_to_actions[current_state][1]
    return next_action


def moveToNextState(igcrest,
                    result,
                    assets_to_act_upon,
                    current_state,
                    action_to_take,
                    final_action,
                    comment):
    workflow_actions_to_states = {
        "request": "WAITING_APPROVAL",
        "approve": "APPROVED",
        "return": "DRAFT",
        "discard": None,
        "publish": None
    }
    new_state = workflow_actions_to_states[action_to_take]
    if current_state != new_state:
        if igcrest.takeWorkflowAction(assets_to_act_upon, action_to_take, comment):
            result['workflow_actions'].append({"items": assets_to_act_upon,
                                               "action": action_to_take})
        else:
            result['workflow_failed'].append({"items": assets_to_act_upon,
                                              "action": action_to_take})
        if new_state and action_to_take != final_action:
            next_action = getNextAction(final_action,
                                        new_state)
            moveToNextState(igcrest,
                            result,
                            assets_to_act_upon,
                            new_state,
                            next_action,
                            final_action,
                            comment)


if __name__ == '__main__':
    main()
