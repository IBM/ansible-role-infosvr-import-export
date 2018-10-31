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
module: igc_extract_openigc_assets

short_description: Extracts OpenIGC assets from IBM Information Governance Catalog

description:
  - Extracts OpenIGC assets from IBM Information Governance Catalog.
  - Extracts based on the criteria provided.

version_added: "2.4"

author:
  - Christopher Grote (@cmgrote)

options:
  host:
    description:
      - Hostname of the domain tier of the Information Analyzer environment
    required: true
    type: str
  port:
    description:
      - Port of the domain tier of the Information Analyzer environment
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
  bundle_name:
    description:
      - The name of the OpenIGC bundle for which to retrieve assets
    required: true
    type: str
  dest:
    description:
      - The (remote) file in which to capture the results of the assets retrieval
    required: true
    type: path
  assets_to_keep:
    description:
      - A list of assets to keep in the extract
    required: true
    type: list
  cert:
    description:
      - The path to a certificate file to use for SSL verification against the server
    required: false
    type: path

requirements:
  - requests
'''

EXAMPLES = '''
- name: retrieve all assets changed in last 2 days for 'JSON_Schema'
  igc_extract_openigc_assets:
    host: infosvr.vagrant.ibm.com
    port: 9446
    user: isadmin
    password: isadmin
    bundle_name: JSON_Schema
    dest: /tmp/igc-x-json_schema-assets.xml
    assets_to_keep:
      - "6662c0f2.e1b1ec6c.kr1ln91jg.luh344a.s06cl0.6k98oeiknhrlo4o4vskpn"
      - "6662c0f2.e1b1ec6c.kr1lcdf12.96sa892.mikeko.a3ksv27ro2a3ufb69h7o5"
'''

RETURN = '''
asset_count:
  description: A numeric indication of the number of assets that were extracted
  type: int
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes, to_native
from ansible.module_utils.ia_rest import RestIA
from ansible.module_utils.openigc_handler import OpenIGCHandler
import os
import os.path
import tempfile


def main():

    module_args = dict(
        host=dict(type='str', required=True),
        port=dict(type='str', required=True),
        user=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        bundle_name=dict(type='str', required=True),
        dest=dict(type='path', required=True),
        assets_to_keep=dict(type='list', required=True),
        cert=dict(type='path', required=False),
        unsafe_writes=dict(type='bool', required=False, default=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        asset_count=0
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

    # Execute the retrieval
    xmlResults = igcrest.getOpenIGCAssets(module.params['bundle_name'])

    # Ensure search worked before proceeding
    if not xmlResults:
        module.fail_json(msg='Retrieval of OpenIGC assets failed', **result)

    # Write temporary file with the full XML output to operate against
    try:
        tmpfd_full, tmpfile_full = tempfile.mkstemp()
        f = os.fdopen(tmpfd_full, 'wb')
        f.write(xmlResults)
        f.close()
    except IOError:
        module.fail_json(msg='Unable to create temporary file to output OpenIGC assets', **result)

    assets_to_keep = module.params['assets_to_keep']
    oigc_xml = OpenIGCHandler(module, result, tmpfile_full)

    all_assets_to_keep = []
    assets_to_drop = []

    for rid in assets_to_keep:
        all_assets_to_keep.append(rid)
        a_ancestors = oigc_xml.getAncestralAssetRids(e_asset)
        for ancenstor in a_ancestors:
            if ancenstor not in all_assets_to_keep:
                all_assets_to_keep.append(ancenstor)
        a_children = oigc_xml.getAssetChildrenRids(rid)
        for child in a_children:
            if child not in all_assets_to_keep:
                all_assets_to_keep.append(child)

    for e_asset in oigc_xml.getAssets():
        rid = oigc_xml.getRid(e_asset)
        if rid not in all_assets_to_keep:
            oigc_xml.dropAsset(e_asset)
        else:
            result['asset_count'] += 1

    # Remove the interim temporary file
    os.unlink(tmpfile_full)

    # Write a new temporary file with the revised XML output,
    # and then move to specified dest location
    try:
        tmpfd, tmpfile = tempfile.mkstemp()
        f = os.fdopen(tmpfd, 'wb')
        oigc_xml.writeCustomizedXML(tmpfile)
        f.close()
    except IOError:
        module.fail_json(msg='Unable to create temporary file to output project details', **result)

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


if __name__ == '__main__':
    main()
