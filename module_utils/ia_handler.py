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
This module adds generic utility functions for interacting with Information Analyzer XML files
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from lxml import etree
import time
import re


ns = {
    'iaapi': 'http://www.ibm.com/investigate/api/iaapi'
}
# Note we exlude TZ offset as this isn't supported on Python 2 without a non-standard library
t_format = "%Y-%m-%dT%H:%M:%S"


class IAHandler(object):
    def __init__(self, module, result, iafile):
        self.module = module
        self.result = result
        self.tree = etree.parse(iafile)
        for key in ns:
            etree.register_namespace(key, ns[key])
        self.root = self.tree.getroot()

    def getProjectNamesFromList(self, listxml):
        # Trim off the encoding header, since lxml's parser does not like them
        trimmed_xml = "\n".join(listxml.split("\n")[1:])
        root = etree.fromstring(trimmed_xml)
        return root.xpath("./Project/@name")

    def getProjectName(self):
        return self.root.get("name")

    def getDataSources(self):
        return self.root.xpath("./DataSources/DataSource", namespaces=ns)

    def getDataRuleDefinitionsSection(self):
        return self.root.xpath("./DataRuleDefinitions", namespaces=ns)

    def getDataRuleDefinitions(self):
        return self.root.xpath("./DataRuleDefinitions/DataRuleDefinition", namespaces=ns)

    def getRuleSetDefinitions(self):
        return self.root.xpath("./DataRuleDefinitions/RuleSetDefinition", namespaces=ns)

    def getDataRules(self):
        return self.root.xpath(".//ExecutableRule", namespaces=ns)

    def getMetricSection(self):
        return self.root.xpath("./Metrics", namespaces=ns)

    def getMetrics(self):
        return self.root.xpath("./Metrics/Metric", namespaces=ns)

    def getExecutables(self, e_definition):
        return e_definition.xpath("./ExecutableRules/ExecutableRule", namespaces=ns)

    def getName(self, e_asset):
        return e_asset.get("name")

    def dropAsset(self, e_asset):
        parent = e_asset.getparent()
        parent.remove(e_asset)
        self.result['changed'] = True

    def dropSection(self, section):
        for to_delete in self.root.xpath("./" + section, namespaces=ns):
            parent = to_delete.getparent()
            parent.remove(to_delete)
            self.result['changed'] = True

    def replaceProjectName(self, new_name):
        self.root.set("name", new_name)
        self.result['replacements'] += 1

    def _getMappedValue(self, from_type, from_property, from_value, mappings):
        for mapping in mappings:
            if from_type == mapping['type'] and from_property == mapping['property']:
                # change name based on regex and 'to' provided in mapping
                mapRE = re.compile(mappings['from'])
                return mapRE.sub(mappings['to'], from_value)
        # default case: return the originally-provided value
        return from_value

    def _replaceFolder(self, elements, from_value, to_value):
        for element in elements:
            a_new_folders = []
            a_org_folders = element.get("folder").split(",")
            for folder in a_org_folders:
                # TODO: this is likely to be error-prone replacement (not specific enough)
                # should only replace complete words between '/'s or at beginning or end
                if from_value in folder:
                    a_new_folders.append(folder.replace(from_value, to_value))
                else:
                    a_new_folders.append(folder)
            element.set("folder", ",".join(a_new_folders))

    def _replaceAttr(self, elements, attr_name, from_value, to_value):
        for element in elements:
            value = element.get(attr_name)
            if value == from_value:
                element.set(attr_name, to_value)

    def _replaceText(self, elements, from_value, to_value):
        for element in elements:
            value = element.text
            if from_value in value:
                # TODO: this is likely to be error-prone replacement (not specific enough)
                # should only replace complete words
                element.text = value.replace(from_value, to_value)

    def _replaceQualifiedName(self, elements, from_value, to_value):
        for element in elements:
            value = element.text
            if from_value in value:
                # TODO: this is likely to be error-prone replacement (not specific enough)
                # should only replace complete words (between '.'s or at beginning / end)
                element.text = value.replace(from_value, to_value)

    def _replaceQualifiedNameInAttr(self, elements, attr_name, from_value, to_value):
        for element in elements:
            value = element.get(attr_name)
            if from_value in value:
                # TODO: this is likely to be error-prone replacement (not specific enough)
                # should only replace complete words (between '.'s or at beginning / end)
                element.set(attr_name, value.replace(from_value, to_value))

    def _propagateMapping(self, data_type, attribute, from_value, to_value):
        # based on any @name changes to [Table, VirtualTable]:
        #if attribute == 'name' and (data_type == 'Table' or data_type == 'VirtualTable'):
            # TODO -- not yet implemented
            # - @baseTable in DataSource/Schema/VirtualTable
            # - //ExecutableRule/BoundExpression
            # - @value in //ExecutableRule/OutputDefinition/OutputColumn
            # - @name in //ExecutableRule/Bindings/Binding/Column
            # - @leftKey, @rightKey in //ExecutableRule/JoinConditions/JoinCondition
            # - @name in //RuleSetDefinition/Variables/Binding/Column
        # based on any @host, @name changes to any of [DataSource, Schema]
        if (attribute == 'name' or attribute == 'host') and (data_type == 'DataSource' or data_type == 'Schema'):
            # - //ExecutableRule/BoundExpression
            self._replaceQualifiedName(self.root.xpath(".//ExecutableRule/BoundExpression"), from_value, to_value)
            # - @value in //ExecutableRule/OutputDefinition/OutputColumn
            output_cols = self.root.xpath(".//ExecutableRule/OutputDefinition/OutputColumn")
            self._replaceQualifiedNameInAttr(output_cols, "value", from_value, to_value)
            # - @name in //ExecutableRule/Bindings/Binding/Column
            binding_cols = self.root.xpath(".//ExecutableRule/Bindings/Binding/Column")
            self._replaceQualifiedNameInAttr(binding_cols, "name", from_value, to_value)
            # - @leftKey, @rightKey in //ExecutableRule/JoinConditions/JoinCondition
            join_conds = self.root.xpath(".//ExecutableRule/JoinConditions/JoinCondition")
            self._replaceQualifiedNameInAttr(join_conds, "leftKey", from_value, to_value)
            self._replaceQualifiedNameInAttr(join_conds, "rightKey", from_value, to_value)
            # - @name in //RuleSetDefinition/Variables/Binding/Column
            rs_bindings = self.root.xpath(".//RuleSetDefinition/Variables/Binding/Column")
            self._replaceQualifiedNameInAttr(rs_bindings, "name", from_value, to_value)
        # based on any @name changes to //Folder/...
        elif data_type == 'Folder' and attribute == 'name':
            # - @folder in //DataRuleDefinition, //RuleSetDefinition, //ExecutableRule -- 
            self._replaceFolder(self.root.xpath(".//DataRuleDefinition", namespaces=ns), from_value, to_value)
            self._replaceFolder(self.root.xpath(".//RuleSetDefinition", namespaces=ns), from_value, to_value)
            self._replaceFolder(self.root.xpath(".//ExecutableRule", namespaces=ns), from_value, to_value)
        # based on any @name changes to //ExecutableRule
        elif data_type == 'ExecutableRule' and attribute == 'name':
            # - //Metric/expression
            m_expressions = self.root.xpath(".//Metric/expression", namespaces=ns)
            self._replaceText(m_expressions, from_value, to_value)
            # - @ruleName in //RuleSetExecutionResult/RuleExecutionResult
            rs_exec = self.root.xpath(".//RuleSetExecutionResult/RuleExecutionResult", namespaces=ns)
            self._replaceAttr(rs_exec, "ruleName", from_value, to_value)
        # based on any @name changes to //DataRuleDefinition, //RuleSetDefinition?
        elif attribute == 'name' and (data_type == 'DataRuleDefinition' or data_type == 'RuleSetDefinition'):
            # - @ruleName in //RuleSetDefinition/RuleDefinitionReference
            rule_refs = self.root.xpath(".//RuleSetDefinition/RuleDefinitionReference")
            self._replaceAttr(rule_refs, "ruleName", from_value, to_value)

    def applyMappings(self, mappings):
        for mapping in mappings:
            s_element = mapping['type']
            s_attr = mapping['attr']
            mapRE = re.compile(mapping['from'])
            elements = self.root.xpath(".//" + s_element, namespaces=ns)
            for element in elements:
                from_value = element.get(s_attr)
                new_value = mapRE.sub(mapping['to'], from_value)
                element.set(s_attr, new_value)
                self.result['replacements'] += 1
                self._propagateMapping(s_element, s_attr, from_value, new_value)

    def writeCustomizedXML(self, filename):
        return self.tree.write(filename, encoding='UTF-8', xml_declaration=True)

    def getCustomizedXMLAsString(self):
        return etree.tostring(self.root, encoding='UTF-8', xml_declaration=True)
