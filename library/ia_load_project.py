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
module: ia_load_project

short_description: Loads project information into IBM Information Analyzer

description:
  - Loads project information into IBM Information Analyzer.
  - Based on the criteria provided.

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
  project:
    description:
      - The name of the Information Analyzer project into which to load
    required: true
    type: str
  src:
    description:
      - The (remote) file that contains the project to be loaded
    required: true
    type: path
  mappings:
    description:
      - A list of mappings to be applied to any of the assets in the project.
      - For example: host names, database names, etc.
    required: false
    type: list
    default: []
    suboptions:
      type:
        description:
          - The type of asset for which to define a mapping.
          - Essentially this is the name of the XML element within the project XML file.
        required: true
        type: str
      attr:
        description:
          - The attribute of the asset I(type) to map.
          - Essentially this is the name of the XML attribute within the element (I(type)).
          - In almost all cases you would use C(name).
          - For I(type) of "DataSource" you may also use C(host).
        required: true
        type: str
        choices: [ "name", "host" ]
      from:
        description:
          - The original value of the I(attr) to look for (and replace / map)
        required: true
        type: str
      to:
        description:
          - The replacement value for the I(attr) to use
        required: true
        type: str
  cert:
    description:
      - The path to a certificate file to use for SSL verification against the server
    required: false
    type: path

requirements:
  - requests
'''

EXAMPLES = '''
- name: retrieve all project details for 'UGDefaultWorkspace'
  ia_load_project:
    host: infosvr.vagrant.ibm.com
    port: 9446
    user: isadmin
    password: isadmin
    project: UGDefaultWorkspace
    src: /tmp/UGDefaultWorkspace.xml
    mappings:
      - { type: "DataSource", attr: "host", from: "LocalServer01", to: "CentralServer01" }
      - { type: "DataSource", attr: "name", from: "LocalDB", to: "CentralDB" }
      - { type: "Schema", attr: "name", from: "SCH_1", to: "SCH_2" }
'''

RETURN = '''
replacements:
  description: A numeric indication of the number of assets that were updated via mapping
  type: int
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ia_rest import RestIA
from ansible.module_utils.ia_handler import IAHandler


def main():

    module_args = dict(
        host=dict(type='str', required=True),
        port=dict(type='str', required=True),
        user=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        project=dict(type='str', required=True),
        src=dict(type='path', required=True),
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
        replacements=0
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    # Setup REST API connectivity via module_utils.igc_rest class
    iarest = RestIA(
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
    project = module.params['project']

    ia_xml = IAHandler(module, result, src)

    # Check if project already exists (to determine whether to CREATE or UPDATE)
    prjlistXML = iarest.getProjectList()
    existing_projects = ia_xml.getProjectNamesFromList(prjlistXML)
    bUpdate = False
    if existing_projects:
        bUpdate = (project in existing_projects)

    ia_xml.replaceProjectName(project)
    ia_xml.applyMappings(mappings)

    xmlToSend = ia_xml.getCustomizedXMLAsString()
    if not xmlToSend:
        module.fail_json(msg='Retrieval of modified project XML failed', **result)
    elif bUpdate:
        iarest.update(xmlToSend)
        result['changed'] = True
    else:
        iarest.create(xmlToSend)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
