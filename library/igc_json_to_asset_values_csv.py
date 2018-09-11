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
module: igc_json_to_asset_values_csv

short_description: Converts a JSON relationship file to one that is importable by istool CLI

description:
  - "Converts a JSON relationship file to a CSV format that is importable by istool CLI"

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
      - The (remote) file that contains the relationships to be converted
    required: true
    type: path
  dest:
    description:
      - The (remote) file into which the CSV format of relationships should be written
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
  cert:
    description:
      - The path to a certificate file to use for SSL verification against the server.
    required: false
    type: path

requirements:
  - requests
'''

EXAMPLES = '''
- name: convert relationships in all.json to CSV format
  igc_json_to_asset_values_csv:
    src: /tmp/all.json
    dest: /tmp/all.csv
    mappings:
      - { type: "host", property: "name", from: "LocalServer01", to: "CentralServer01" }
'''

RETURN = '''
asset_count:
  description: A numeric indication of the number of assets that were converted
  type: int
  returned: always
untranslated_assets:
  description: A list of the untranslated assets (did not match provided type)
  type: list
  returned: always
untranslated_relationships:
  description: A list of the untranslated relationships (did not match provided relationship property)
  type: list
  returned: always
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes, to_native
from ansible.module_utils.igc_rest import RestIGC
from ansible.module_utils.infosvr_types import get_mapped_value
import tempfile
import os
import os.path
import json
import csv


def main():

    module_args = dict(
        host=dict(type='str', required=True),
        port=dict(type='str', required=True),
        user=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        src=dict(type='path', required=True),
        dest=dict(type='path', required=True),
        mappings=dict(type='list', required=False, default=[]),
        cert=dict(type='path', required=False),
        unsafe_writes=dict(type='bool', required=False, default=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        asset_count=0,
        untranslated_assets=[],
        untranslated_relationships=[]
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
    dest = module.params['dest']

    if os.path.isdir(src):
        module.fail_json(rc=256, msg='Src %s is a directory !' % src)

    src_exists = os.path.exists(src)
    if not src_exists:
        module.fail_json(rc=257, msg='Src %s does not exist !' % src)

    f = open(to_bytes(src), 'rb')
    allAssets = json.load(f)
    f.close()

    if len(allAssets) > 0:
        asset_type = allAssets[0]['_type']
        # Retrieve descriptive asset properties to populate headers
        asset_name, propertyMap = igcrest.getPropertyMap(asset_type)
        aRows = []
        aHeader = []
        for asset in allAssets:

            aRow = {}
            if 'Name' not in aHeader:
                aHeader.append('Name')
            aRow['Name'] = asset['_name']
            # Start by translating context of the asset itself
            for ctx in asset['_context']:
                mappedCtx = get_mapped_value(ctx['_type'], 'name', ctx['_name'], mappings)
                ctxName, ctxMap = igcrest.getPropertyMap(ctx['_type'])
                if ctxName == 'Host (Engine)':
                    ctxName = 'Host'
                if ctxName not in aHeader:
                    aHeader.append(ctxName)
                aRow[ctxName] = mappedCtx
            result['asset_count'] += 1

            for reln_property in asset:
                if not reln_property.startswith('_'):
                    aRelations = []
                    relnName = propertyMap[reln_property]
                    if relnName not in aHeader:
                        aHeader.append(relnName)
                    for reln in asset[reln_property]:
                        # Translate the context of each related asset
                        sRelation = '"'
                        for relnCtx in reln['_context']:
                            mappedRelnCtx = get_mapped_value(relnCtx['_type'], 'name', relnCtx['_name'], mappings)
                            sRelation += mappedRelnCtx + ">>"
                            # relnCtxName, relnCtxMap = igcrest.getPropertyMap(relnCtx['_type'])
                        sRelation += reln['_name'] + '"'
                        aRelations.append(sRelation)
                    if len(aRelations) > 0:
                        aRow[relnName] = "[" + ";".join(aRelations) + "]"
                    else:
                        aRow[relnName] = ""
            if len(aRow) > 0:
                aRows.append(aRow)
            else:
                result['untranslated_assets'].append(asset)

    # Close the IGC REST API session
    igcrest.closeSession()

    # Write temporary file with the JSON output,
    # and then move to specified dest location
    try:
        tmpfd, tmpfile = tempfile.mkstemp()
        f = os.fdopen(tmpfd, 'wb')
        f.write("+++ " + asset_name + " - begin +++\n")
        writer = csv.DictWriter(f, fieldnames=aHeader)
        writer.writeheader()
        for row in aRows:
            writer.writerow(row)
        f.write("+++ " + asset_name + " - end +++\n\n")
        f.close()
    except IOError:
        module.fail_json(msg='Unable to create temporary file to output transformed relationships', **result)

    # Checksumming to identify change...
    checksum_src = module.sha1(tmpfile)
    checksum_dest = None
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
