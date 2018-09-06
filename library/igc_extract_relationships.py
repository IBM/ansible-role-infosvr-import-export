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
module: igc_extract_relationships

short_description: Extracts metadata relationships from an IBM Information Governance Catalog environment

description:
  - Extracts metadata relationships from an IBM Information Governance Catalog environment.
  - Extracts based on the criteria provided.

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
  relationships:
    description:
      - The IGC REST asset's property (eg. C(assigned_assets)) to use to retrieve relationships.
      - (See "GET /ibm/iis/igc-rest/v1/types/<asset_type>?showViewProperties=true" in your environment for choices.)
    required: true
    type: list
  dest:
    description:
      - The (remote) file in which to capture the results of the relationship retrieval
    required: true
    type: path
  from_time:
    description:
      - The time (UNIX epoch style, in milliseconds) from which to consider changes
    required: false
    type: int
  to_time:
    description:
      - The time (UNIX epoch style, in milliseconds) up to which to consider changes
    required: false
    type: int
  conditions:
    description:
      - A list of conditions to limit the assets for which to retrieve relationships
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
  limit:
    description:
      - A second IGC REST asset type (eg. C(database_column)) to which to limit the relationships that are retrieved.
      - (See "GET /ibm/iis/igc-rest/v1/types" in your environment for choices.)
      - As a list, so could be eg. [ C(database_column), C(design_column), C(entity_attribute) ]
    required: false
    type: list
    default: []
  batch:
    description:
      - The number of assets / relationships to retrieve per REST API call
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
- name: retrieve all assigned_assets relationships for all terms
  igc_extract_relationships:
    host: infosvr.vagrant.ibm.com
    port: 9446
    user: isadmin
    password: isadmin
    asset_type: term
    relationships:
      - assigned_assets
    dest: /tmp/all.json

- name: retrieve assigned_assets for terms named test
  igc_extract_relationships:
    host: infosvr.vagrant.ibm.com
    port: 9446
    user: isadmin
    password: isadmin
    asset_type: term
    relationships:
      - assigned_assets
    dest: /tmp/namedTestOnly.json
    conditions:
      - { "property": "name", "operator": "=", "value": "test" }

- name: retrieve only database_table assigned_assets relationships for all terms
  igc_extract_relationships:
    host: infosvr.vagrant.ibm.com
    port: 9446
    user: isadmin
    password: isadmin
    asset_type: term
    relationships:
      - assigned_assets
    limit:
      - database_table
    dest: /tmp/dbTablesOnly.json
'''

RETURN = '''
queries:
  description: A list of JSON query criteria used to retrieve the assets for which to extract relationships
  returned: always
  type: list
asset_count:
  description: A numeric indication of the number of assets that were extracted
  type: int
  returned: always
relationship_count:
  description: A numeric indication of the number of relationships that were extracted
  type: int
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes, to_native
from ansible.module_utils.igc_rest import RestIGC
import os
import os.path
import tempfile
import json


def main():

    module_args = dict(
        host=dict(type='str', required=True),
        port=dict(type='str', required=True),
        user=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        asset_type=dict(type='str', required=True),
        relationships=dict(type='list', required=True),
        dest=dict(type='path', required=True),
        from_time=dict(type='int', required=False, default=-1),
        to_time=dict(type='int', required=False),
        conditions=dict(type='list', required=False, default=[]),
        limit=dict(type='list', required=False, default=[]),
        batch=dict(type='int', required=False, default=100),
        cert=dict(type='path', required=False),
        unsafe_writes=dict(type='bool', required=False, default=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        queries=[],
        asset_count=0,
        relationship_count=0
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

    relnprops = module.params['relationships']
    limit = module.params['limit']

    # Basic query
    reqJSON = {
        "properties": relnprops,
        "types": [module.params['asset_type']],
        "pageSize": module.params['batch']
    }

    # Extend basic query with any optional conditions
    if len(module.params['conditions']) > 0:
        reqJSON['where'] = {
            "conditions": module.params['conditions'],
            "operator": "and"
        }
    if module.params['from_time'] != -1:
        if 'where' not in reqJSON:
            reqJSON['where'] = {
                "conditions": [],
                "operator": "and"
            }
        reqJSON['where']['conditions'].append({
            "min": module.params['from_time'],
            "max": module.params['to_time'],
            "property": "modified_on",
            "operator": "between"
        })

    result['queries'].append(reqJSON)

    # Execute the search
    jsonResults = igcrest.search(reqJSON)

    # Ensure search worked before proceeding
    if jsonResults == '':
        module.fail_json(msg='Initial IGC REST API search failed', **result)

    result['asset_count'] = len(jsonResults)

    for item in jsonResults:
        minifyItem(item)
        for itmCtx in item['_context']:
            minifyItem(itmCtx)
        for relnprop in relnprops:
            item[relnprop] = igcrest.getAllPages(item[relnprop]['items'], item[relnprop]['paging'])
            aRemoveIndices = []
            iIdx = 0
            for relation in item[relnprop]:
                # Limit included relationships to only those types of interest
                if (len(limit) > 0) and not (relation['_type'] in limit):
                    aRemoveIndices.append(iIdx)
                else:
                    relnCtx = igcrest.getContextForItem(relation['_id'], relation['_type'])
                    if relnCtx == '':
                        module.fail_json(msg='Unable to retieve context for search result', **result)
                    else:
                        minifyItem(relation)
                        for ctx in relnCtx:
                            minifyItem(ctx)
                        result['relationship_count'] += 1
                        relation['_context'] = relnCtx
                iIdx += 1
            for removal in aRemoveIndices:
                del item[relnprop][removal]

    # Close the IGC REST API session
    igcrest.closeSession()

    # Write temporary file with the JSON output,
    # and then move to specified dest location
    try:
        tmpfd, tmpfile = tempfile.mkstemp()
        f = os.fdopen(tmpfd, 'wb')
        json.dump(jsonResults, f)
        f.close()
    except IOError:
        module.fail_json(msg='Unable to create temporary file to output relationship results', **result)

    # Checksumming to identify change...
    checksum_src = module.sha1(tmpfile)
    checksum_dest = None
    dest = module.params['dest']
    b_dest = to_bytes(dest, errors='surrogate_or_strict')
    if os.access(b_dest, os.R_OK):
        checksum_dest = module.sha1(dest)

    # If the file does not already exist and/or checksums are different,
    # move the new file over the old one and mark it as changed; otherwise
    # leave the original file (delete the tmpfile) and that there was no change
    if checksum_src != checksum_dest:
        module.atomic_move(tmpfile,
                           to_native(os.path.realpath(b_dest), errors='surrogate_or_strict'),
                           unsafe_writes=module.params['unsafe_writes'])
        result['changed'] = True
    else:
        os.unlink(tmpfile)

    module.exit_json(**result)


def minifyItem(asset):
    del asset['_id']
    del asset['_url']


if __name__ == '__main__':
    main()
