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
module: igc_extract_openigc_bundle

short_description: Extracts OpenIGC bundles from an IBM Information Governance Catalog environment

description:
  - Extracts OpenIGC bundles from an IBM Information Governance Catalog environment.
  - Extracts based on the criteria provided.

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
  bundle_name:
    description:
      - The name of the OpenIGC bundle to extract.
      - (See "GET /ibm/iis/igc-rest/v1/bundles" in your environment for choices.)
    required: true
    type: str
  dest:
    description:
      - The (remote) file in which to capture the results of the relationship retrieval
    required: true
    type: path
  cert:
    description:
      - The path to a certificate file to use for SSL verification against the server.
    required: false
    type: path

requirements:
  - requests
'''

EXAMPLES = '''
- name: retrieve OpenIGC bundle for JSON_Schema
  igc_extract_openigc_bundle:
    host: infosvr.vagrant.ibm.com
    port: 9446
    user: isadmin
    password: isadmin
    bundle_name: JSON_Schema
    dest: /tmp/ibm-igc-x-json_schema.zip
'''

RETURN = '''
bundle_count:
  description: A numeric indication of the number of bundles that were extracted
  type: int
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes, to_native
from ansible.module_utils.igc_rest import RestIGC
from io import BytesIO
import os
import os.path
import tempfile
import json


def main():

    module_args = dict(
        host=dict(type='str', required=True),
        port=dict(type='str', required=True),
        user=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        bundle_name=dict(type='str', required=True),
        dest=dict(type='path', required=True),
        cert=dict(type='path', required=False),
        unsafe_writes=dict(type='bool', required=False, default=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        bundle_count=0
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

    bundle_name = module.params['bundle_name']

    bundle = igcrest.downloadOpenIGCBundle(bundle_name)
    if not bundle:
        module.fail_json(msg='Unable to download bundle: ' + bundle_name, **result)

    result['bundle_count'] = 1

    # Close the IGC REST API session
    igcrest.closeSession()

    # Write temporary file with the ZIP output,
    # and then move to specified dest location
    try:
        tmpfd, tmpfile = tempfile.mkstemp()
        f = os.fdopen(tmpfd, 'wb')
        f.write(bundle)
        f.close()
    except IOError:
        module.fail_json(msg='Unable to create temporary file to output bundle', **result)

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
