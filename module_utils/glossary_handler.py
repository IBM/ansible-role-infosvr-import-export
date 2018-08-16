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
"""
This module adds generic utility functions for interacting with Custom Attribute definition (XML) files
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from lxml import etree


ns = {
    'x': 'http://www.ibm.com/is/bg/importexport'
}
rest_to_type = {
    "term": "TERM",
    "category": "CATEGORY",
    "information_governance_policy": "POLICY",
    "information_governance_rule": "RULE",
    "label": "LABEL"
}


class GlossaryHandler(object):
    def __init__(self, module, result, glossaryfile):
        self.module = module
        self.result = result
        self.tree = etree.parse(glossaryfile)
        self.root = self.tree.getroot()

    def getCustomAttributeDefinitions(self):
        return self.root.xpath("./x:customAttributesDefinitions/x:customAttributeDef", namespaces=ns)

    def getCategories(self):
        return self.root.xpath("./x:categories/x:category", namespaces=ns)

    def getTerms(self):
        return self.root.xpath("./x:terms/x:term", namespaces=ns)

    def getSynonymGroups(self):
        return self.root.xpath("./x:synonymGroups/x:synonymGroup", namespaces=ns)

    def getSynonyms(self, elemSG):
        return elemSG.xpath("./x:synonyms/x:termRef", namespaces=ns)

    def getPolicies(self):
        return self.root.xpath("./x:policies/x:policy", namespaces=ns)

    def getRules(self):
        return self.root.xpath("./x:rules/x:rule", namespaces=ns)

    def getLabels(self):
        return self.root.xpath("./x:labelDefinitions/x:labelDefinition", namespaces=ns)

    def getCustomAttributes(self, elem):
        return elem.xpath("./x:customAttributes/x:customAttributeValue", namespaces=ns)

    def getCustomAttrName(self, elem):
        return elem.xpath("./@customAttribute", namespaces=ns)[0]

    def getName(self, elem):
        return elem.xpath("./@name", namespaces=ns)[0]

    def isRelationship(self, elem):
        return elem.xpath("boolean(./x:customAttributeReferences)", namespaces=ns)

    def customAttrAppliesToThisType(self, elem, typename):
        applies_to_types = elem.xpath("./x:appliesTo/x:classType/@value", namespaces=ns)
        return (rest_to_type[typename] in applies_to_types)

    def getRid(self, elem):
        return elem.xpath("./@rid", namespaces=ns)[0]

    def dropAsset(self, e_asset):
        parent = e_asset.getparent()
        parent.remove(e_asset)
        self.result['changed'] = True

    def dropSection(self, section):
        for to_delete in self.root.xpath("./x:" + section, namespaces=ns):
            parent = to_delete.getparent()
            parent.remove(to_delete)
            self.result['changed'] = True

    def writeCustomizedXML(self, filename):
        return self.tree.write(filename, encoding='UTF-8', xml_declaration=True)
