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
import time


ns = {
    'xmi': 'http://www.omg.org/XMI',
    'ASCLCustomAttribute': 'http:///2.3/ASCLCustomAttribute.ecore',
    'XMetaImportExport': 'http:///com/ibm/xmeta/shared/model/3/XMetaImportExport.ecore'
}
# Note we exlude TZ offset as this isn't supported on Python 2 without a non-standard library
t_format = "%Y-%m-%dT%H:%M:%S.%f"


class CustomAttrHandler(object):
    def __init__(self, module, result, cafile):
        self.module = module
        self.result = result
        self.tree = etree.parse(cafile)
        for key in ns:
            etree.register_namespace(key, ns[key])
        self.root = self.tree.getroot()
        self.caIDs_keep = []
        self.classIDs_keep = []
        self.enumIDs_keep = []

    def _getClassDescriptors(self):
        return self.root.xpath("./ASCLCustomAttribute:ClassDescriptor", namespaces=ns)

    def _getValidEnumerations(self):
        return self.root.xpath("./ASCLCustomAttribute:ValidEnumeration", namespaces=ns)

    def _getSeedObjectRids(self):
        return self.root.xpath("./XMetaImportExport:AssetDataDescriptor/seedObjectRids/text()", namespaces=ns)

    def _getAssetDataDescriptors(self):
        return self.root.xpath("./XMetaImportExport:AssetDataDescriptor", namespaces=ns)

    def _getElementId(self, elem):
        return elem.xpath("./@xmi:id", namespaces=ns)[0]

    def getCustomAttributeDefinitions(self):
        # Only retrieve custom attribute directly defined for this asset type
        seedRid = self._getSeedObjectRids()[0]
        root_class = self.root.xpath("./ASCLCustomAttribute:ClassDescriptor[@_xmeta_repos_object_id='" + seedRid + "']", namespaces=ns)[0]
        return root_class.xpath("./has_CustomAttribute")

    def _keepDefinitionSrcClassId(self, e_customattr):
        if "hasSource_ClassDescriptor" in e_customattr.attrib:
            for classId in e_customattr.get("hasSource_ClassDescriptor").split():
                self.classIDs_keep.append(classId)

    def _keepDefinitionTgtClassId(self, e_customattr):
        if "hasTarget_ClassDescriptor" in e_customattr.attrib:
            for classId in e_customattr.get("hasTarget_ClassDescriptor").split():
                self.classIDs_keep.append(classId)

    def _keepDefinitionEnumId(self, e_customattr):
        if "has_ValidValues" in e_customattr.attrib:
            for enumId in e_customattr.get("has_ValidValues").split():
                self.enumIDs_keep.append(enumId)

    def getDefinitionModTime(self, e_customattr):
        # Take only the portion of the timestamp up to the TZ offset
        return time.mktime(time.strptime(e_customattr.get("_xmeta_modification_timestamp")[:-5], t_format)) * 1000

    def getDefinitionName(self, e_customattr):
        return e_customattr.get("name")

    def getDefinitionType(self, e_customattr):
        return e_customattr.get("dataType")

    def keepDefinition(self, e_customattr):
        self.caIDs_keep.append(self._getElementId(e_customattr))
        self._keepDefinitionSrcClassId(e_customattr)
        self._keepDefinitionTgtClassId(e_customattr)
        self._keepDefinitionEnumId(e_customattr)

    def dropDefinition(self, e_customattr):
        parent = e_customattr.getparent()
        parent.remove(e_customattr)

    def _dropUnusedPieces(self):
        seedRid = self._getSeedObjectRids()
        # Drop any unused classes
        for e_class in self._getClassDescriptors():
            classId = self._getElementId(e_class)
            classRid = e_class.get("_xmeta_repos_object_id")
            if classId not in self.classIDs_keep and classRid not in seedRid:
                self.dropDefinition(e_class)
                self.result['changed'] = True
            else:
                # Remove references to dropped custom attributes as source
                if 'isSourceOf_CustomAttribute' in e_class.attrib:
                    a_newSources = []
                    for id_source in e_class.get("isSourceOf_CustomAttribute").split():
                        if id_source in self.caIDs_keep:
                            a_newSources.append(id_source)
                    if len(a_newSources) > 0:
                        e_class.set("isSourceOf_CustomAttribute", " ".join(a_newSources))
                    else:
                        e_class.attrib.pop("isSourceOf_CustomAttribute")
                # Remove references to dropped custom attributes as target
                if 'isTargetOf_CustomAttribute' in e_class.attrib:
                    a_newTargets = []
                    for id_target in e_class.get("isTargetOf_CustomAttribute").split():
                        if id_target in self.caIDs_keep:
                            a_newTargets.append(id_target)
                    if len(a_newTargets) > 0:
                        e_class.set("isTargetOf_CustomAttribute", " ".join(a_newTargets))
                    else:
                        e_class.attrib.pop("isTargetOf_CustomAttribute")
        # Drop any unused enumerated valid values
        for e_enum in self._getValidEnumerations():
            enumId = self._getElementId(e_enum)
            if enumId not in self.enumIDs_keep:
                self.dropDefinition(e_enum)
                self.result['changed'] = True

    def writeCustomizedXML(self, filename):
        self._dropUnusedPieces()
        return self.tree.write(filename, encoding='UTF-8', xml_declaration=True)
