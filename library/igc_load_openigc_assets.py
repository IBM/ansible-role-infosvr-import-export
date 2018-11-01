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
module: igc_load_openigc_assets

short_description: Loads OpenIGC asset instances into an IBM Information Governance Catalog environment

description:
  - Loads OpenIGC asset instances into an IBM IGC environment.
  - Based on the criteria provided.

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
      - The (remote) file that contains the assets to be loaded
    required: true
    type: path
  complete_types:
    description:
      - A list of type IDs for which complete changes should be processed.
      - If empty, every asset will be loaded as defined in the I(src) partials / completes.
    required: false
    type: list
  cert:
    description:
      - The path to a certificate file to use for SSL verification against the server.
    required: false
    type: path

requirements:
  - requests
'''

EXAMPLES = '''
- name: load all OpenIGC assets from the XML file
  igc_load_openigc_assets:
    host: infosvr.vagrant.ibm.com
    port: 9446
    user: isadmin
    password: isadmin
    src: /tmp/assets.xml
'''

RETURN = '''
rids:
  description: A list of RID mappings that were updated or created by the operation
  type: dict
  returned: always
uploaded_xml:
  description: the XML string that was used to load the assets
  type: string
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes
from ansible.module_utils.igc_rest import RestIGC
from ansible.module_utils.openigc_handler import OpenIGCHandler
import os.path
import json


def main():

    module_args = dict(
        host=dict(type='str', required=True),
        port=dict(type='str', required=True),
        user=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        src=dict(type='path', required=True),
        complete_types=dict(type='list', required=False, default=[]),
        cert=dict(type='path', required=False),
        unsafe_writes=dict(type='bool', required=False, default=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        rids={},
        uploaded_xml=""
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

    src = module.params['src']
    complete_types = module.params['complete_types']

    if os.path.isdir(src):
        module.fail_json(rc=256, msg='Src %s is a directory !' % src)

    src_exists = os.path.exists(src)
    if not src_exists:
        module.fail_json(rc=257, msg='Src %s does not exist !' % src)

    oigc_xml = OpenIGCHandler(module, result, src)

    partial_assets = []
    complete_assets = []

    for e_asset in oigc_xml.getAssets():
        rid = oigc_xml.getRid(e_asset)
        asset_type = oigc_xml.getType(e_asset)
        if asset_type in complete_types:
            complete_assets.append(rid)
        else:
            partial_assets.append(rid)

    oigc_xml.setImportActionPartials(partial_assets)
    oigc_xml.setImportActionCompletes(complete_assets)

    xmlToSend = oigc_xml.getCustomizedXMLAsString()
    if not xmlToSend:
        module.fail_json(msg='Retrieval of modified asset XML failed', **result)
    else:
        result['uploaded_xml'] = xmlToSend
        asset_details = igcrest.uploadOpenIGCAssets(xmlToSend)
        if asset_details is not None:
            result['rids'] = asset_details
            result['changed'] = True
        else:
            module.fail_json(msg='Failed to upload assets', **result)

    # Close the IGC REST API session
    igcrest.closeSession()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
