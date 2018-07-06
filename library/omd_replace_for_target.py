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
module: omd_replace_for_target

short_description: Replaces necessary parameters in OMD flows to be loadable in a target environment

description:
  - "Replaces necessary parameters in OMD flows to be loadable in a target environment."
  - "In particular, the engine hostname of the source with the engine hostname of the target system."

version_added: "2.4"

author:
  - Christopher Grote (@cmgrote)

options:
  file:
    description:
      - The OMD flow file for which to do the replacements
    required: true
    type: path
  host:
    description:
      - The target hostname to use as the replacement
      - (The source hostname will be determined automatically from the flow file)
    required: true
    type: str
'''

EXAMPLES = '''
- name: replace hostnames in flow
  omd_replace_for_target:
    file: "{{ ibm_infosvr_impexp_omd_backup_dir }}/a.flow"
    host: "{{ group_vars[...][0] }}"
'''

RETURN = '''
src_host:
  description: The original hostname that was identified within the flow
  type: str
  returned: always
replacements:
  description: A numeric indication of the number of replacements that were made
  type: int
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes
from ansible.module_utils.omd_handler import OMDHandler

import os
import os.path
import time


def main():

    module_args = dict(
        file=dict(type='path', required=True),
        host=dict(type='str', required=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        src_host="",
        replacements=0
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    filename = module.params['file']

    omd = OMDHandler(module, result, filename)
    omd.replaceHostname(module.params['host'])
    result['src_host'] = omd.getOriginalHost()
    omd.writeCustomizedOMD(filename)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
