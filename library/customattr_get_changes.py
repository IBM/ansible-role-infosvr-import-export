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
module: customattr_get_changes

short_description: Retrieves changed custom attribute definitions from IBM Information Governance Catalog

description:
  - "Retrieves a listing of changed custom attribute definitions from an IBM IGC environment."
  - "Based on the criteria provided."

version_added: "2.4"

author:
  - Christopher Grote (@cmgrote)

options:
  src:
    description:
      - Custom attribute XML file from which to identify changes
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
  model_ver:
    description:
      - The ASCLCustomAttribute model version for the Information Server environment (release-specific)
      - This is setup automatically by 'setup_mappings' of the role, and put into __ibm_infosvr_impexp_model_versions
    required: true
    type: str
  names:
    description:
      - A list of names of custom attributes to include
    required: false
    type: list
'''

EXAMPLES = '''
- name: retrieve all custom attribute definitions changed over the last 48-hours
  customattr_get_changes:
    src: "/somewhere/GlossaryExtensions/BusinessCategory/GlossaryExtensions.BusinessCategory.cd"
    from_time: >
              {{ ( (ansible_date_time.epoch | int) * 1000) - (48 * 3600 * 1000) ) | int }}
    to_time: >
              {{ ansible_date_time.epoch * 1000 | int }}
    model_ver: __ibm_infosvr_impexp_model_versions
  register: customattrs_changed_in_last_48hrs
'''

RETURN = '''
ca_count:
  description: The number of custom attribute definitions that were found based on the provided criteria
  type: int
  returned: always
ca_names:
  description: A list of names of the custom attribute definitions that match the provided criteria
  type: list
  returned: always
ca_dropped:
  description: A list of the names of custom attribute definitions that were dropped
  type: list
  returned: always
ca_dropped_classes:
  description: A list of the names of classes that were dropped
  type: list
  returned: always
ca_dropped_enums:
  description: A list of the names of enumerations that were dropped
  type: list
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.customattr_handler import CustomAttrHandler


def main():

    module_args = dict(
        src=dict(type='path', required=True),
        from_time=dict(type='int', required=True),
        to_time=dict(type='int', required=True),
        model_ver=dict(type='str', required=True),
        names=dict(type='list', required=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        ca_count=0,
        ca_names=[],
        ca_dropped=[],
        ca_dropped_classes=[],
        ca_dropped_enums=[]
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    ca_src = module.params['src']
    names_to_keep = module.params['names']
    from_time = module.params['from_time']
    to_time = module.params['to_time']
    model_ver = module.params['model_ver']

    ca_xml = CustomAttrHandler(module, result, ca_src, model_ver)

    for attr_defn in ca_xml.getCustomAttributeDefinitions():
        mod_time = ca_xml.getDefinitionModTime(attr_defn)
        attr_name = ca_xml.getDefinitionName(attr_defn)
        if mod_time >= from_time and mod_time <= to_time:
            if names_to_keep is None or len(names_to_keep) == 0:
                result['ca_count'] += 1
                result['ca_names'].append(attr_name)
                ca_xml.keepDefinition(attr_defn)
            elif attr_name in names_to_keep:
                result['ca_count'] += 1
                result['ca_names'].append(attr_name)
                ca_xml.keepDefinition(attr_defn)

    ca_xml.writeCustomizedXML(ca_src)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
