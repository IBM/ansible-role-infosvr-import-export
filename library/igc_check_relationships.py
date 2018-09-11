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
module: igc_check_relationships

short_description: Determines whether relationships are custom or native

description:
  - "Determines whether relationships in a file are custom or native"

version_added: "2.4"

author:
  - Christopher Grote (@cmgrote)

options:
  src:
    description:
      - The (remote) file that contains the relationships to be converted
    required: true
    type: path
'''

EXAMPLES = '''
- name: check relationships in all.json
  igc_check_relationships:
    src: /tmp/all.json
  register: igc_relations
'''

RETURN = '''
asset_type_is_supported_by_import_asset_values:
  description: Indication of whether the asset type is supported through 'import asset values' of istool
  type: bool
  returned: always
native_simple_relations:
  description: A list of the native (out-of-the-box) relationship properties that refer to only a single asset type
  type: list
  returned: always
native_multi_relations:
  description: A list of the native (out-of-the-box) relationship properties that could refer to more than one type
  type: list
  returned: always
native_attributes:
  description: A list of the native (out-of-the-box) non-relationship properties
  type: int
  returned: always
custom_relations:
  description: A list of the custom relationship properties
  type: list
  returned: always
custom_attributes:
  description: A list of the custom non-relationship properties
  type: list
  returned: always
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes
from ansible.module_utils.infosvr_types import is_simple_native_relationship, is_supported_by_import_asset_values
import os.path
import json


def main():

    module_args = dict(
        src=dict(type='path', required=True),
        unsafe_writes=dict(type='bool', required=False, default=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        asset_type_is_supported_by_import_asset_values=False,
        native_simple_relations=[],
        native_multi_relations=[],
        native_attributes=[],
        custom_relations=[],
        custom_attributes=[]
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    src = module.params['src']

    if os.path.isdir(src):
        module.fail_json(rc=256, msg='Src %s is a directory !' % src)

    src_exists = os.path.exists(src)
    if not src_exists:
        module.fail_json(rc=257, msg='Src %s does not exist !' % src)

    f = open(to_bytes(src), 'rb')
    allAssets = json.load(f)
    f.close()

    for asset in allAssets:
        asset_type = asset['_type']
        result['asset_type_is_supported_by_import_asset_values'] = is_supported_by_import_asset_values(asset_type)
        for prop in asset:
            bRelation = isinstance(asset[prop], list)
            if prop.startswith('custom_'):
                if bRelation and prop not in result['custom_relations']:
                    result['custom_relations'].append(prop)
                elif not bRelation and prop not in result['custom_attributes']:
                    result['custom_attributes'].append(prop)
            elif not prop.startswith('_'):
                if bRelation:
                    bSimple = is_simple_native_relationship(prop)
                    if bSimple and prop not in result['native_simple_relations']:
                        result['native_simple_relations'].append(prop)
                    elif not bSimple and prop not in result['native_multi_relations']:
                        result['native_multi_relations'].append(prop)
                elif prop not in result['native_attributes']:
                    result['native_attributes'].append(prop)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
