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
module: igc_query

short_description: Queries an IBM IGC environment using an arbitrary set of conditions

description:
  - Retrieves a listing of assets from an IBM IGC environment, based on the criteria provided.
  - Use number of assets that match the criteria to validate an IGC environment meets certain conditions.

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
      - The IGC REST asset type (eg. C(term)) for which to query.
      - (See "GET /ibm/iis/igc-rest/v1/types" in your environment for choices.)
    required: true
    type: str
  properties:
    description:
      - The list of properties to retrieve for the I(asset_type).
    required: false
    type: list
  conditions:
    description:
      - A list conditions by which to query the assets.
      - Could be left empty if you want to simply retrieve all assets of a given type.
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
  extract_all:
    description:
      - Whether to extract all assets C(True) or only the first page C(False).
      - Will default to C(False).
    required: false
    type: bool

requirements:
  - requests
'''

EXAMPLES = '''
- name: retrieve DataStage jobs in the 'dstage1' project
  igc_query:
    host: infosvr.vagrant.ibm.com
    port: 9446
    user: isadmin
    password: isadmin
    asset_type: dsjob
    conditions:
      - { "property": "transformation_project.name", "operator": "=", "value": "dstage1" }
  register: dsjobs_in_dstage1
'''

RETURN = '''
queries:
  description:
    - The JSON queries used to retrieve the assets.
  returned: always
  type: list
asset_count:
  description:
    - A numeric indication of the number of assets that were found based on the provided criteria.
  type: int
  returned: always
assets:
  description:
    - A list of JSON objects representing the assets retrieved based on the provided criteria.
    - Note that if I(extract_all) is C(False), this will only contain the first page (up to I(batch)) of results.
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
        properties=dict(type='list', required=False, default=['name']),
        conditions=dict(type='list', required=False, default=[]),
        condition_join=dict(type='str', required=False, default='AND'),
        cert=dict(type='path', required=False),
        batch=dict(type='int', required=False, default=100),
        extract_all=dict(type='bool', required=False, default=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        queries=[],
        asset_count=0,
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
    properties = module.params['properties']
    extract_all = module.params['extract_all']

    # Basic query
    reqJSON = {
        "properties": properties,
        "types": [asset_type],
        "pageSize": module.params['batch']
    }

    if len(conditions) > 0:
        reqJSON['where'] = {
            "conditions": conditions,
            "operator": module.params['condition_join'].lower()
        }

    jsonResults = igcrest.search(reqJSON, extract_all)

    # Ensure search worked before proceeding
    if jsonResults == '':
        module.fail_json(msg='IGC query failed', **result)

    if extract_all:
        result['asset_count'] = len(jsonResults)
        result['assets'] = jsonResults
    else:
        result['asset_count'] = jsonResults['paging']['numTotal']
        result['assets'] = jsonResults['items']

    # Close the IGC REST API session
    igcrest.closeSession()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
