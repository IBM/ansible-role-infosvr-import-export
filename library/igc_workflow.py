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
  compared_to_published:
    description:
      - Take action only when the the development is the SAME as or DIFFERENT to the published asset.
    required: false
    type: str
    choices: [ "SAME", "DIFFERENT" ]
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
import six
import json


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
        compared_to_published=dict(type='str', required=False, default=''),
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
    compared_to_published = module.params['compared_to_published']
    batch = module.params['batch']

    # First check whether workflow is even enabled
    # (if not, we can return immediately as this module becomes a NOOP)
    if igcrest.isWorkflowEnabled():
        result['workflow_enabled'] = True
    else:
        igcrest.closeSession()
        module.exit_json(**result)

    incomparable_keys = [
        'history',
        'development_log',
        'modified_by',
        'modified_on',
        'created_by',
        'created_on',
        '_url'
    ]

    # Basic query
    reqJSON = {
        "pageSize": batch,
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

    same_assets = []
    changed_assets = []

    for asset in jsonResults:
        # For some reason 'workflow_current_state' is an array
        # (but should only ever have one entry, so always take first?)
        current_state = asset['workflow_current_state'][0]
        assets_by_state[current_state].append(asset['_id'])
        if compared_to_published != '':
            if sameAsPublishedAsset(igcrest, module, incomparable_keys, asset, batch):
                same_assets.append(asset['_id'])
            else:
                changed_assets.append(asset['_id'])

    # Easy case: we're only moving from a particular state
    if from_state != 'ALL':
        assets_to_move = assets_by_state[from_state]
        action_to_take = getNextAction(action,
                                       from_state)
        if compared_to_published == '':
            moveToNextState(igcrest,
                            result,
                            assets_to_move,
                            from_state,
                            action_to_take,
                            action,
                            comment)
        else:
            intersected_assets = []
            if compared_to_published == 'SAME':
                intersected_assets = list(set(assets_to_move) & set(same_assets))
            elif compared_to_published == 'DIFFERENT':
                intersected_assets = list(set(assets_to_move) & set(changed_assets))
            moveToNextState(igcrest,
                            result,
                            intersected_assets,
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
            if compared_to_published == '':
                moveToNextState(igcrest,
                                result,
                                draft_assets,
                                'DRAFT',
                                action_to_take,
                                action,
                                comment)
            else:
                intersected_assets = []
                if compared_to_published == 'SAME':
                    intersected_assets = list(set(draft_assets) & set(same_assets))
                elif compared_to_published == 'DIFFERENT':
                    intersected_assets = list(set(draft_assets) & set(changed_assets))
                moveToNextState(igcrest,
                                result,
                                intersected_assets,
                                'DRAFT',
                                action_to_take,
                                action,
                                comment)
        waiting_assets = assets_by_state['WAITING_APPROVAL']
        if len(waiting_assets) > 0:
            action_to_take = getNextAction(action, 'WAITING_APPROVAL')
            if compared_to_published == '':
                moveToNextState(igcrest,
                                result,
                                waiting_assets,
                                'WAITING_APPROVAL',
                                action_to_take,
                                action,
                                comment)
            else:
                intersected_assets = []
                if compared_to_published == 'SAME':
                    intersected_assets = list(set(waiting_assets) & set(same_assets))
                elif compared_to_published == 'DIFFERENT':
                    intersected_assets = list(set(waiting_assets) & set(changed_assets))
                moveToNextState(igcrest,
                                result,
                                intersected_assets,
                                'WAITING_APPROVAL',
                                action_to_take,
                                action,
                                comment)
        approved_assets = assets_by_state['APPROVED']
        if len(approved_assets) > 0:
            action_to_take = getNextAction(action, 'APPROVED')
            if compared_to_published == '':
                moveToNextState(igcrest,
                                result,
                                approved_assets,
                                'APPROVED',
                                action_to_take,
                                action,
                                comment)
            else:
                intersected_assets = []
                if compared_to_published == 'SAME':
                    intersected_assets = list(set(approved_assets) & set(same_assets))
                elif compared_to_published == 'DIFFERENT':
                    intersected_assets = list(set(approved_assets) & set(changed_assets))
                moveToNextState(igcrest,
                                result,
                                intersected_assets,
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
            result['changed'] = True
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


def _sameDict(igcrest, module, d1, d2):
    same = (list(d1.keys()).sort() == list(d2.keys()).sort())
    if same:
        # If it's an IGC type and not business metadata, we can simply
        # directly compare the RIDs to test for equality
        if '_type' in d1 and not igcrest.isWorkflowType(d1['_type']):
            same = (d1['_id'] == d2['_id'])
        else:
            for prop in d1:
                if prop not in ['_id', '_url']:
                    d1_val = d1[prop]
                    d2_val = d2[prop]
                    # If a simple type, just directly compare for equality
                    if isinstance(d1_val, (six.string_types, bool, int, long, float)):
                        same = (d1_val == d2_val)
                    elif isinstance(d1_val, list):
                        same = _sameList(igcrest, module, d1_val, d2_val)
                    elif isinstance(d1_val, dict):
                        same = _sameDict(igcrest, module, d1_val, d2_val)
                # Short-circuit the checks if we found a difference
                if not same:
                    break
    return same


# Assumptions:
# - order shouldn't be directly relevant to lists -- so we will
#   sort them prior to comparison
def _sameList(igcrest, module, l1, l2):
    same = (len(l1) == len(l2))
    if same and len(l1) > 0:
        sorted_list_l1 = l1
        sorted_list_l2 = l2
        # Check the types in the list based on the first entry...
        if isinstance(l1[0], (six.string_types, bool, int, long, float)):
            sorted_list_l1 = sorted(l1)
            sorted_list_l2 = sorted(l2)
        if isinstance(l1[0], list):
            module.warn("Never expected to reach here -- double-nested list?" + json.dumps(l1))
        if isinstance(l1[0], dict):
            # Sort the sub-objects by concatenation of _type, _name and _id
            sorted_list_l1 = sorted(l1, key=lambda x: (x['_type'] + "::" + x['_name'] + "::" + x['_id']))
            sorted_list_l2 = sorted(l2, key=lambda x: (x['_type'] + "::" + x['_name'] + "::" + x['_id']))
        for idx, l1_val in enumerate(sorted_list_l1):
            l2_val = sorted_list_l2[idx]
            # If a simple type, just directly compare for equality
            if isinstance(l1_val, (six.string_types, bool, int, long, float)):
                same = (l1_val == l2_val)
            elif isinstance(l1_val, list):
                same = _sameList(igcrest, module, l1_val, l2_val)
            elif isinstance(l1_val, dict):
                same = _sameDict(igcrest, module, l1_val, l2_val)
            # Short-circuit the checks if we found a difference
            if not same:
                break
    return same


# Assumptions:
# - dev_asset is a development glossary asset (workflow participant)
def sameAsPublishedAsset(igcrest, module, rm_keys, dev_asset, batch):

    bSame = True

    full_dev_asset = igcrest.getFullAsset(dev_asset, True, batch)
    pub_asset = igcrest.getMappedItem(dev_asset, [], False, batch)
    full_pub_asset = igcrest.getFullAsset(pub_asset, False, batch)

    # Remove any attributes that will never be comparable
    for attr in rm_keys:
        if attr in pub_asset:
            del pub_asset[attr]
        if attr in dev_asset:
            del dev_asset[attr]

    # Initial check: set of sorted keys is identical between the two
    # ... and if we pass this point, we know the keys are identical so
    # we only ever need to loop over one set of keys (not both)
    bSame = _sameDict(igcrest, module, full_dev_asset, full_pub_asset)

    return bSame


if __name__ == '__main__':
    main()
