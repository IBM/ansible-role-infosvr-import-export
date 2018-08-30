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
module: igc_get_changed_assets

short_description: Retrieves a listing of changed assets from an IBM Information Governance Catalog environment

description:
  - "Retrieves a listing of changed assets from an IBM IGC environment, based on the criteria provided"

version_added: "2.4"

author:
  - Christopher Grote (@cmgrote)

options:
  host:
    description:
      - Hostname of the domain tier of the Information Governance Catalog environment
    required: true
    type: str
  port:
    description:
      - Port of the domain tier of the Information Governance Catalog environment
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
      - The IGC REST asset type (eg. C(term)) for which to retrieve relationships.
      - (See "GET /ibm/iis/igc-rest/v1/types" in your environment for choices.)
    required: true
    type: str
  from_time:
    description:
      - The time (UNIX epoch style, in milliseconds) from which to consider changes
    required: true
    type: int
  to_time:
    description:
      - The time (UNIX epoch style, in milliseconds) up to which to consider changes
    required: true
    type: int
  conditions:
    description:
      - A list of other conditions by which to limit the assets retrieved
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
  batch:
    description:
      - The number of assets to retrieve per REST API call
    required: false
    type: int
    default: 100
  cert:
    description:
      - The path to a certificate file to use for SSL verification against the server.
    required: false
    type: path

requirements:
  - requests
'''

EXAMPLES = '''
- name: retrieve all changed DataStage jobs over the last 48-hours
  igc_get_changed_assets:
    host: infosvr.vagrant.ibm.com
    port: 9446
    user: isadmin
    password: isadmin
    asset_type: dsjob
    from_time: >
              {{ ( (ansible_date_time.epoch | int) * 1000) - (48 * 3600 * 1000) ) | int }}
    to_time: >
              {{ ansible_date_time.epoch * 1000 | int }}
  register: dsjobs_changed_in_last_48hrs

- name: retrieve changed DataStage jobs over the last 48-hours, only in 'dstage1' project
  igc_get_changed_assets:
    host: infosvr.vagrant.ibm.com
    port: 9446
    user: isadmin
    password: isadmin
    asset_type: dsjob
    from_time: >
              {{ ( (ansible_date_time.epoch | int) * 1000) - (48 * 3600 * 1000) ) | int }}
    to_time: >
              {{ ansible_date_time.epoch * 1000 | int }}
    conditions:
      - { "property": "transformation_project.name", "operator": "=", "value": "dstage1" }
  register: dsjobs_in_dstage1_changed_in_last_48hrs
'''

RETURN = '''
queries:
  description: A list of JSON query criteria used to retrieve the assets for which to extract relationships
  returned: always
  type: list
asset_count:
  description: A numeric indication of the number of assets that were found based on the provided criteria
  type: int
  returned: always
assets:
  description: A list of JSON objects representing the assets retrieved based on the provided criteria
  type: list
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.igc_rest import RestIGC
from ansible.module_utils.infosvr_types import get_properties, get_asset_extract_object


def main():

    module_args = dict(
        host=dict(type='str', required=True),
        port=dict(type='str', required=True),
        user=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        asset_type=dict(type='str', required=True),
        from_time=dict(type='int', required=True),
        to_time=dict(type='int', required=True),
        conditions=dict(type='list', required=False, default=[]),
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
        assets=[]
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

    # Basic query
    reqJSON = {
        "properties": get_properties(module.params['asset_type']),
        "types": [module.params['asset_type']],
        "where": {
            "conditions": [],
            "operator": "and"
        },
        "pageSize": module.params['batch']
    }

    # Handle extended data sources in special way (to catch any changes in their underlying
    # granular assets as well) -- requires nested OR'd conditions to check for changes
    if asset_type == 'application':
        reqJSON['where']['conditions'].append({"conditions": [], "operator": "or"})
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "object_types.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "object_types.methods.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "object_types.methods.input_parameters.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "object_types.methods.output_values.modified_on",
            "operator": "between"
        })
    # Handle stored procedures in special way (to catch any changes in their underlying
    # granular assets as well) -- requires nested OR'd conditions to check for changes
    elif asset_type == 'stored_procedure_definition':
        reqJSON['where']['conditions'].append({"conditions": [], "operator": "or"})
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "in_parameters.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "out_parameters.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "inout_parameters.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "result_columns.modified_on",
            "operator": "between"
        })
    # Handle IA data rules in special way (to catch any changes in underlying execution runs)
    # -- requires nested OR'd condition to check for changes
    elif asset_type == 'data_rule' or asset_type == 'data_rule_set' or asset_type == 'metric':
        reqJSON['where']['conditions'].append({"conditions": [], "operator": "or"})
        reqJSON['where']['conditions'][0]['conditions'].append({
            "property": "execution_history",
            "operator": "isNull"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "execution_history.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "modified_on",
            "operator": "between"
        })
    # Handle LDM objects in special way (to catch any changes in underlying objects)
    # -- requires nested OR'd condition to check for changes
    elif asset_type == 'logical_data_model':
        reqJSON['where']['conditions'].append({"conditions": [], "operator": "or"})
        reqJSON['where']['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "contains_logical_data_models.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "subject_areas.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "logical_entities.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "logical_domains.modified_on",
            "operator": "between"
        })
    # Handle PDM objects in special way (to catch any changes in underlying objects)
    # -- requires nested OR'd condition to check for changes
    elif asset_type == 'physical_data_model':
        reqJSON['where']['conditions'].append({"conditions": [], "operator": "or"})
        reqJSON['where']['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "contains_physical_models.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "contains_design_tables.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "contains_design_views.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "contains_design_stored_procedures.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "physical_domains.modified_on",
            "operator": "between"
        })
    # Handle Database objects in special way (to catch any changes in underlying objects)
    # -- requires nested OR'd condition to check for changes
    elif asset_type == 'database':
        reqJSON['where']['conditions'].append({"conditions": [], "operator": "or"})
        reqJSON['where']['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "database_schemas.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "database_schemas.stored_procedures.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "database_schemas.views.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "database_schemas.database_tables.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "database_schemas.database_tables.database_columns.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "database_schemas.views.database_columns.modified_on",
            "operator": "between"
        })
    # Handle Schema objects in special way (to catch any changes in underlying objects)
    # -- requires nested OR'd condition to check for changes
    elif asset_type == 'database_schema':
        reqJSON['where']['conditions'].append({"conditions": [], "operator": "or"})
        reqJSON['where']['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "stored_procedures.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "views.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "database_tables.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "database_tables.database_columns.modified_on",
            "operator": "between"
        })
        reqJSON['where']['conditions'][0]['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "views.database_columns.modified_on",
            "operator": "between"
        })
    # Skip delta detection on the assets named in this condition, as they have no 'modified_on' to query against
    elif asset_type != 'label':
        reqJSON['where']['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "modified_on",
            "operator": "between"
        })

    # Extend basic query with any optional conditions (in the outer, AND'd portion)
    if len(conditions) > 0:
        reqJSON['where']['conditions'] += conditions

    jsonResults = igcrest.search(reqJSON)

    # Ensure search worked before proceeding
    if jsonResults == '':
        module.fail_json(msg='Initial IGC REST API search failed', **result)

    result['asset_count'] = len(jsonResults)

    # Translate the retrieved item details into exportable strings
    for item in jsonResults:
        result_obj = get_asset_extract_object(module.params['asset_type'], item)
        if result_obj == "UNIMPLEMENTED":
            module.fail_json(msg='Unable to convert asset_type "' + module.params['asset_type'] + '"', **result)
        elif result_obj is not None:
            result['assets'].append(result_obj)

    # Close the IGC REST API session
    igcrest.closeSession()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
