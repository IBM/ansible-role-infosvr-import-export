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
module: igc_load_relationships

short_description: Loads metadata relationships into an IBM Information Governance Catalog environment

description:
  - "Loads metadata relationships into an IBM IGC environment, based on the criteria provided"

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
  src:
    description:
      - The (remote) file that contains the relationships to be loaded
    required: true
    type: path
  mappings:
    description:
      - A list of mappings to be applied to any of the assets that compose the relationships.
      - For example: host names, database names, etc.
    required: false
    type: list
    default: []
    suboptions:
      type:
        description:
          - The type of asset for which to define a mapping.
          - (See "GET /ibm/iis/igc-rest/v1/types" in your environment for choices.)
        required: true
        type: str
      property:
        description:
          - The attribute of the asset I(type) to map.
          - In almost all cases you would use C(name), but for C(data_file) you may also use C(path).
        required: true
        type: str
        choices: [ "name", "path" ]
      from:
        description:
          - The original value of the I(property) to look for (and replace / map)
        required: true
        type: str
      to:
        description:
          - The replacement value for the I(property) to use
        required: true
        type: str
  mode:
    description:
      - Semantic to use for adding the relationship
    required: true
    type: str
    choices: [ "APPEND", "REPLACE_ALL", "REPLACE_SOME" ]
  replace_type:
    description:
      - Restrict replacement only to relationships to this specified asset type when I(mode) is C(REPLACE_SOME)
    required: false
    type: str
    default: ""
  conditions:
    description:
      - Additional conditions to restrict the replacement of the relationships when I(mode) is C(REPLACE_SOME).
      - Basically these are query criteria for the asset type specified by I(replace_type).
    required: false
    type: list
    default: []
    suboptions:
      property:
        description:
          - The property of the I(replace_type) to set the condition against.
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
- name: load all assigned_assets relationships for all terms
  igc_load_relationships:
    host: infosvr.vagrant.ibm.com
    port: 9446
    user: isadmin
    password: isadmin
    src: /tmp/all.json

- name: load assigned_assets for terms and mapping hostnames
  igc_load_relationships:
    host: infosvr.vagrant.ibm.com
    port: 9446
    user: isadmin
    password: isadmin
    src: /tmp/namedTestOnly.json
    mappings:
      - { type: "host", property: "name", from: "LocalServer01", to: "CentralServer01" }
'''

RETURN = '''
queries:
  description: A list of JSON query criteria used to retrieve assets (for mapping)
  returned: always
  type: list
updates:
  description: A list update requests that were made
  type: list
  returned: always
asset_update_count:
  description: A numeric indication of the number of assets that were updated
  type: int
  returned: always
relationship_update_count:
  description: A numeric indication of the number of relationships that were set
  type: int
  returned: always
unmapped_assets:
  description: A list of the assets for which no mapped item could be found
  returned: always
  type: list
unmapped_relations:
  description: A list of the assets for which no mapped relationship could be found
  returned: always
  type: list
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes
from ansible.module_utils.igc_rest import RestIGC
import os.path
import json


def main():

    module_args = dict(
        host=dict(type='str', required=True),
        port=dict(type='str', required=True),
        user=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        src=dict(type='path', required=True),
        mappings=dict(type='list', required=False, default=[]),
        mode=dict(type='str', required=True),
        replace_type=dict(type='str', required=False, default=""),
        conditions=dict(type='list', required=False, default=[]),
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
        updates=[],
        asset_update_count=0,
        relationship_update_count=0,
        unmapped_assets=[],
        unmapped_relations=[]
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

    mappings = module.params['mappings']
    src = module.params['src']
    batch = module.params['batch']

    if os.path.isdir(src):
        module.fail_json(rc=256, msg='Src %s is a directory !' % src)

    src_exists = os.path.exists(src)
    if not src_exists:
        module.fail_json(rc=257, msg='Src %s does not exist !' % src)

    f = open(to_bytes(src), 'rb')
    allAssets = json.load(f)
    f.close()

    wfl_enabled = igcrest.isWorkflowEnabled()

    for asset in allAssets:
        mappedItem = igcrest.getMappedItem(asset, mappings, wfl_enabled, batch=batch)
        if mappedItem == "":
            result['unmapped_assets'].append(asset)
            continue
        # Automatically detect the relationship properties, should be the only
        # ones that do NOT start with an underscore
        for relnprop in asset:
            if not relnprop.startswith('_'):
                aRelns = asset[relnprop]
                aMappedRelnRIDs = []
                for reln in aRelns:
                    if '_type' in reln:
                        mappedReln = igcrest.getMappedItem(reln, mappings, wfl_enabled, batch=batch)
                        reln_editable = True
                        # Need to ensure that any relationship to other business metadata
                        # is in an editable state in the workflow
                        if wfl_enabled and igcrest.isWorkflowType(mappedReln['_type']):
                            reln_editable = igcrest._returnToEditableState(mappedReln)
                        if mappedReln == "" or not reln_editable:
                            result['unmapped_relations'].append(reln)
                            continue
                        aMappedRelnRIDs.append(mappedReln['_id'])
                if len(aMappedRelnRIDs) > 0:
                    update_rc, update_msg = igcrest.addRelationshipsToAsset(
                        mappedItem,
                        aMappedRelnRIDs,
                        relnprop,
                        module.params['mode'],
                        replace_type=module.params['replace_type'],
                        conditions=module.params['conditions'],
                        batch=module.params['batch']
                    )
                    if update_rc != 200:
                        module.fail_json(rc=update_rc, msg='Update failed: %s' % json.dumps(update_msg), **result)
                    else:
                        result['changed'] = True
                    result['asset_update_count'] += 1
                    result['relationship_update_count'] += len(aMappedRelnRIDs)

    # Close the IGC REST API session
    igcrest.closeSession()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
