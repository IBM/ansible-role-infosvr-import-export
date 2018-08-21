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
module: glossary_filter_changes

short_description: Filters changed business metadata from an IBM Information Governance Catalog export

description:
  - "Filters changed business metadata from an IBM IGC export (XML)."
  - "Based on the criteria provided."

version_added: "2.4"

author:
  - Christopher Grote (@cmgrote)

options:
  src:
    description:
      - Glossary XML file from which to identify changes
    required: true
    type: path
  type:
    description:
      - The type of business metadata to keep in the extract
    required: true
    type: str
  assets_to_keep:
    description:
      - A list of assets to keep in the extract
    required: true
    type: list
'''

EXAMPLES = '''
- name: retain business terms changed over the last 48-hours
  glossary_filter_changes:
    src: "/somewhere/business_glossary.xml"
    type: term
    assets_to_keep:
      - { rid: "6662c0f2.e1b1ec6c.kr1ln91jg.luh344a.s06cl0.6k98oeiknhrlo4o4vskpn" }
      - { rid: "6662c0f2.e1b1ec6c.kr1lcdf12.96sa892.mikeko.a3ksv27ro2a3ufb69h7o5" }
'''

RETURN = '''
asset_count:
  description: The number of business metadata assets that were retained based on the provided criteria
  type: int
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.glossary_handler import GlossaryHandler


def main():

    module_args = dict(
        src=dict(type='path', required=True),
        type=dict(type='str', required=True),
        assets_to_keep=dict(type='list', required=True)
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

    glossary_src = module.params['src']
    asset_type = module.params['type']
    assets_to_keep = module.params['assets_to_keep']

    glossary_xml = GlossaryHandler(module, result, glossary_src)

    keep_custom_attrs = []

    processAssets(glossary_xml, result, glossary_xml.getCategories(), assets_to_keep, keep_custom_attrs)
    processAssets(glossary_xml, result, glossary_xml.getTerms(), assets_to_keep, keep_custom_attrs)
    processAssets(glossary_xml, result, glossary_xml.getPolicies(), assets_to_keep, keep_custom_attrs)
    processAssets(glossary_xml, result, glossary_xml.getRules(), assets_to_keep, keep_custom_attrs)
    processAssets(glossary_xml, result, glossary_xml.getLabels(), assets_to_keep, keep_custom_attrs)

    custom_attrs = glossary_xml.getCustomAttributeDefinitions()
    for e_customattr in custom_attrs:
        e_ca_name = glossary_xml.getName(e_customattr)
        if not (e_ca_name in keep_custom_attrs):
            glossary_xml.dropAsset(e_customattr)
        elif not (glossary_xml.customAttrAppliesToThisType(e_customattr, asset_type)):
            glossary_xml.dropAsset(e_customattr)

    if asset_type == 'term':
        for e_sg in glossary_xml.getSynonymGroups():
            b_termRef = False
            for e_s in glossary_xml.getSynonyms(e_sg):
                refRid = glossary_xml.getRid(e_s)
                if refRid in assets_to_keep:
                    b_termRef = True
            if not b_termRef:
                glossary_xml.dropAsset(e_sg)

    categories = glossary_xml.getCategories()
    terms = glossary_xml.getTerms()
    policies = glossary_xml.getPolicies()
    rules = glossary_xml.getRules()
    labels = glossary_xml.getLabels()

    if not categories:
        glossary_xml.dropSection('categories')
    if not terms:
        glossary_xml.dropSection('terms')
        glossary_xml.dropSection('synonymGroups')
    if not policies:
        glossary_xml.dropSection('policies')
    if not rules:
        glossary_xml.dropSection('rules')
    if not labels:
        glossary_xml.dropSection('labelDefinitions')

    glossary_xml.writeCustomizedXML(glossary_src)

    module.exit_json(**result)


def processAssets(glossary_xml, result, assets, assets_to_keep, keep_custom_attrs):
    for e_asset in assets:
        rid = glossary_xml.getRid(e_asset)
        if rid not in assets_to_keep:
            glossary_xml.dropAsset(e_asset)
        else:
            result['asset_count'] += 1
            # Remove any reference-based custom attributes (these should be
            # handled by relationship-specific import / export)
            for e_customattr in glossary_xml.getCustomAttributes(e_asset):
                if glossary_xml.isRelationship(e_customattr):
                    glossary_xml.dropAsset(e_customattr)
                else:
                    ca_name = glossary_xml.getCustomAttrName(e_customattr)
                    if not (ca_name in keep_custom_attrs):
                        keep_custom_attrs.append(ca_name)


if __name__ == '__main__':
    main()
