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
module: omd_get_changes

short_description: Retrieves a listing of changed OMD flows from an IBM Information Governance Catalog environment

description:
  - "Retrieves a listing of changed OMD flows from an IBM IGC environment, based on the criteria provided"

version_added: "2.4"

author:
  - Christopher Grote (@cmgrote)

options:
  dir:
    description:
      - Directory on the Information Governance Catalog engine tier containing OMD flows
    required: true
    type: path
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
'''

EXAMPLES = '''
- name: retrieve all OMD flows processed over the last 48-hours
  omd_get_changes:
    dir: "{{ ibm_infosvr_impexp_omd_backup_dir }}"
    from_time: >
              {{ ( (ansible_date_time.epoch | int) * 1000) - (48 * 3600 * 1000) ) | int }}
    to_time: >
              {{ ansible_date_time.epoch * 1000 | int }}
  register: omd_processed_in_last_48hrs
'''

RETURN = '''
flow_count:
  description: A numeric indication of the number of OMD flows that were found based on the provided criteria
  type: int
  returned: always
flow_files:
  description: A list of filenames for the OMD flows that match the provided criteria
  type: list
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.omd_handler import OMDHandler

import os
import os.path
import time


def main():

    module_args = dict(
        dir=dict(type='path', required=True),
        from_time=dict(type='int', required=True),
        to_time=dict(type='int', required=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        flow_count=0,
        flow_files=[]
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    omd_dir = module.params['dir']

    # For each file...
    for file in os.listdir(omd_dir):
        if os.path.isfile(omd_dir + os.sep + file):
            # If the completion time falls between the "from_time" and "to_time", add it to the file list
            omd = OMDHandler(module, result, omd_dir + os.sep + file)
            omd_epoch = time.mktime(time.strptime(omd._getRunCompletion(), "%Y-%m-%dT%H:%M:%S")) * 1000
            if omd_epoch >= module.params['from_time'] and omd_epoch <= module.params['to_time']:
                result['flow_count'] += 1
                result['flow_files'].append(file)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
