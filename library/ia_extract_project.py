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
module: ia_extract_project

short_description: Extracts project information from IBM Information Analyzer

description:
  - Extracts project information from IBM Information Analyzer.
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
  project:
    description:
      - The name of the Information Analyzer project for which to retrieve details
    required: true
    type: str
  dest:
    description:
      - The (remote) file in which to capture the results of the project retrieval
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
- name: retrieve all project details for 'UGDefaultWorkspace'
  ia_extract_project:
    host: infosvr.vagrant.ibm.com
    port: 9446
    user: isadmin
    password: isadmin
    project: UGDefaultWorkspace
    dest: /tmp/UGDefaultWorkspace.xml
    assets_to_keep:
      - { project: "UGDefaultWorkspace", name: "RuleDefn1", type: "DataRuleDefinitions/DataRuleDefinition" }
      - { project: "UGDefaultWorkspace", name: "DataRule1", type: "DataRuleDefinitions/DataRuleDefinition/ExecutableRules/ExecutableRule" }
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
from ansible.module_utils.ia_handler import IAHandler
import os
import os.path
import tempfile
from lxml import etree


def main():

    module_args = dict(
        host=dict(type='str', required=True),
        port=dict(type='str', required=True),
        user=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        project=dict(type='str', required=True),
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
    iarest = RestIA(
        module,
        result,
        username=module.params['user'],
        password=module.params['password'],
        host=module.params['host'],
        port=module.params['port'],
        cert=module.params['cert']
    )

    # Execute the retrieval
    xmlResults = iarest.getProjectDetails(module.params['project'])

    # Ensure search worked before proceeding
    if not xmlResults:
        module.fail_json(msg='Retrieval of IA project details failed', **result)

    assets_to_keep = module.params['assets_to_keep']
    ia_xml = IAHandler(module, result, xmlResults)

    drd_to_keep = []
    drsd_to_keep = []
    dr_to_keep = []
    drs_to_keep = []
    m_to_keep = []

    # Group the assets to keep by their asset type
    for asset in assets_to_keep:
        if asset.type == 'data_rule_definition':
            drd_to_keep.append(asset.name)
        elif asset.type == 'data_rule_set_definition':
            drsd_to_keep.append(asset.name)
        elif asset.type == 'data_rule':
            dr_to_keep.append(asset.name)
        elif asset.type == 'data_rule_set':
            drs_to_keep.append(asset.name)
        elif asset.type == 'metric':
            m_to_keep.append(asset.name)

    # Remove executables first, since they're nested in the definitions
    for e_exec in ia_xml.getDataRules():
        name = ia_xml.getName(e_exec)
        if name not in dr_to_keep and name not in drs_to_keep:
            ia_xml.dropAsset(e_exec)
        else:
            result['asset_count'] += 1
    for e_metric in ia_xml.getMetrics():
        if ia_xml.getName(e_metric) not in m_to_keep:
            ia_xml.dropAsset(e_metric)
        else:
            result['asset_count'] += 1

    # Only remove definitions that have no executables AND are not keepers
    for e_defn in ia_xml.getDataRuleDefinitions():
        e_executables = ia_xml.getExecutables(e_defn)
        if ia_xml.getName(e_defn) not in drd_to_keep and len(e_executables) == 0:
            ia_xml.dropAsset(e_defn)
        else:
            result['asset_count'] += 1
    for e_defn in ia_xml.getRuleSetDefinitions():
        e_executables = ia_xml.getExecutables(e_defn)
        if ia_xml.getName(e_defn) not in drsd_to_keep and len(e_executables) == 0:
            ia_xml.dropAsset(e_defn)
        else:
            result['asset_count'] += 1

    # Close the IA REST API session
    iarest.closeSession()

    # Write temporary file with the XML output,
    # and then move to specified dest location
    try:
        tmpfd, tmpfile = tempfile.mkstemp()
        f = os.fdopen(tmpfd, 'wb')
        #json.dump(jsonResults, f) # TODO: ensure XML equivalent below actually works
        ia_xml.writeCustomizedXML(tmpfile)
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
