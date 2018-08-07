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

    def writeCustomizedXML(self, filename):
        return self.tree.write(filename, encoding='UTF-8', xml_declaration=True)
