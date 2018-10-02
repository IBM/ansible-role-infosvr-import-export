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
module: igc_merge_relationships

short_description: Merge multiple relationship files into one

description:
  - "Merge multiple relationship files into one"

version_added: "2.4"

author:
  - Christopher Grote (@cmgrote)

options:
  src:
    description:
      - A list of files to be merged
    required: true
    type: list
  dest:
    description:
      - The destination file into which to merge the files
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
'''

EXAMPLES = '''
- name: merge relationships into all.json
  igc_merge_relationships:
    src:
      - a.json
      - b.json
    dest: all.json
  register: igc_merged_relations
'''

RETURN = '''
merge_count:
  description: A numeric indication of the number of total merged assets
  type: int
  returned: always
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes
from ansible.module_utils.infosvr_types import get_mapped_identity
import os
import os.path
import tempfile
import json


def main():

    module_args = dict(
        src=dict(type='list', required=True),
        dest=dict(type='path', required=True),
        mappings=dict(type='list', required=False, default=[]),
        unsafe_writes=dict(type='bool', required=False, default=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        merge_count=0
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    src = module.params['src']
    dest = module.params['dest']
    mappings = module.params['mappings']

    mergedAssets = {}
    relnsForId = {}

    for filename in src:
        if os.path.isdir(filename):
            module.fail_json(rc=256, msg='Src %s is a directory !' % filename)

        src_exists = os.path.exists(filename)
        if not src_exists:
            module.fail_json(rc=257, msg='Src %s does not exist !' % filename)

        f = open(to_bytes(filename), 'rb')
        allAssetsFromFile = json.load(f)
        f.close()

        for asset in allAssetsFromFile:
            mapped_asset = get_mapped_identity(asset, mappings)
            asset_id = json.dumps(mapped_asset)
            if asset_id not in mergedAssets:
                mergedAssets[asset_id] = mapped_asset
            for prop in asset:
                bRelation = isinstance(asset[prop], list)
                if not prop.startswith('_'):
                    if bRelation:
                        if asset_id not in relnsForId:
                            relnsForId[asset_id] = {}
                        if prop not in mergedAssets[asset_id]:
                            mergedAssets[asset_id][prop] = []
                        if prop not in relnsForId[asset_id]:
                            relnsForId[asset_id][prop] = []
                        for reln in asset[prop]:
                            mapped_reln = get_mapped_identity(reln, mappings)
                            reln_id = json.dumps(mapped_reln)
                            if reln_id not in relnsForId[asset_id][prop]:
                                mergedAssets[asset_id][prop].append(mapped_reln)
                                relnsForId[asset_id][prop].append(reln_id)
                    else:
                        mergedAssets[asset_id][prop] = asset[prop]

    consolidatedAssets = []
    for asset_id in mergedAssets:
        asset = mergedAssets[asset_id]
        consolidatedAssets.append(asset)

    # Write temporary file with the JSON output,
    # and then move to specified dest location
    try:
        tmpfd, tmpfile = tempfile.mkstemp()
        f = os.fdopen(tmpfd, 'wb')
        json.dump(consolidatedAssets, f)
        f.close()
    except IOError:
        module.fail_json(msg='Unable to create temporary file to output merged relationships', **result)

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
