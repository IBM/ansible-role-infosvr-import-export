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
This module adds generic utility functions for interacting with Operational Metadata (OMD)
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from lxml import etree


class OMDHandler(object):
    def __init__(self, module, result, flowfile):
        self.module = module
        self.result = result
        self.tree = etree.parse(flowfile)
        self.root = self.tree.getroot()
        self.orgvalues = {}

    def _getRunStatus(self):
        return self.root.get("StatusCode")

    def _getRunMessage(self):
        return self.root.get("Message")

    def _getRunCompletion(self):
        return self.root.get("FinishedAt")

    def _getDesign(self):
        return self.root.find("./Design/SoftwareResourceLocator")

    def _getExecutable(self):
        return self.root.find("./Deployment/SoftwareResourceLocator")

    def _getHostElement(self, element):
        return element.find("./LocatorComponent[@Class='Computer']")

    def _getReadEvent(self):
        return self.root.find("./Events/Event[@Type='Read']")

    def _getWriteEvent(self):
        return self.root.find("./Events/Event[@Type='Write']")

    def _getRowCount(self, event):
        return event.get("RowCount")

    def _getDataResourceForEvent(self, event):
        return event.find("./DataResourceLocator")

    def _getDataCollectionForEvent(self, event):
        refDC = event.find("./SoftwareResourceLocator").get("ReferenceDC")
        return self.root.find("./DataSchema/DataCollection[@Ident='" + refDC + "']")

    def _getDataResourceHost(self, resource):
        return resource.find("./LocatorComponent[@Class='Computer']").get("Name")

    def _getDataResourceStore(self, resource, conn_string):
        ds = resource.find("./LocatorComponent[@Class='DataStore']").get("Name")
        if ds.strip() == "":
            ds = conn_string
        return ds

    def _getDataResourceSchema(self, resource):
        return resource.find("./LocatorComponent[@Class='DataSchema']").get("Name")

    def _getDataResourceTable(self, resource):
        return resource.find("./LocatorComponent[@SubClass='Table']").get("Name")

    def _getDataResourceIdentity(self, resource, conn_string):
        host = self._getDataResourceHost(resource)
        db = self._getDataResourceStore(resource, conn_string)
        schema = self._getDataResourceSchema(resource)
        table = self._getDataResourceTable(resource)
        return host + "::" + db + "::" + schema + "::" + table

    def _getDataCollectionColumns(self, collection):
        aFields = []
        for field in collection.findall("./DataField"):
            aFields.append(field.get("Name"))
        return aFields

    def getProjectName(self):
        return self.root.find("./Design/SoftwareResourceLocator/LocatorComponent[@SubClass='Project']").get("Name")

    def getJobName(self):
        return self.root.find("./Design/SoftwareResourceLocator/LocatorComponent[@SubClass='Job']").get("Name")

    def getOriginalHost(self):
        return self.orgvalues['host']

    def replaceHostname(self, targethost):
        # NOTE: will only overwrite the host named in a parameter if it matches the original engine tier value
        eDeployment = self._getExecutable()
        eDeploymentHost = self._getHostElement(eDeployment)
        self.orgvalues['host'] = eDeploymentHost.get("Name")
        if self.orgvalues['host'] != targethost:
            eDeploymentHost.set("Name", targethost)
            self.result['replacements'] += 1
        for eParam in self.root.findall("./ActualParameters/ActualParameter"):
            eParamHost = self._getHostElement(eParam.find("./SoftwareResourceLocator"))
            sFormalParam = eParam.find("./SoftwareResourceLocator/LocatorComponent[@Class='FormalParameter']").get("Name")
            # If the parameter is for SourceConnectionString or TargetConnectionString,
            # we'll pre-pend the parameter with the old hostname to create a unique
            # connection string (which we can then use in connection mapping for lineage purposes)
            # NOTE: This seems to be a user-defined parameter name...
            # Need to ensure everyone uses exactly the same name for this?
            if sFormalParam == "SourceConnectionString" or sFormalParam == "TargetConnectionString":
                orgHost = eParamHost.get("Name")
                connString = eParam.get("Value")
                self.orgvalues[sFormalParam] = connString
                eParam.set("Value", orgHost + "__" + connString)
                self.result['changed'] = True
            if self.orgvalues['host'] == eParamHost.get("Name"):
                eParamHost.set("Name", targethost)
                self.result['replacements'] += 1
        eReadEvent = self._getReadEvent()
        eReadEventHost = self._getHostElement(eReadEvent.find("./DataResourceLocator"))
        if self.orgvalues['host'] == eReadEventHost.get("Name"):
            eReadEventHost.set("Name", targethost)
            self.result['replacements'] += 1
        eWriteEvent = self._getWriteEvent()
        eWriteEventHost = self._getHostElement(eWriteEvent.find("./DataResourceLocator"))
        if self.orgvalues['host'] == eWriteEventHost.get("Name"):
            eWriteEventHost.set("Name", targethost)
            self.result['replacements'] += 1

    def getUniqueRuntimeIdentity(self):
        evt_read = self._getReadEvent()
        evt_write = self._getWriteEvent()
        identity = {
            "project": self.getProjectName(),
            "job": self.getJobName(),
            "source": self._getDataResourceIdentity(self._getDataResourceForEvent(evt_read), self.orgvalues['SourceConnectionString']),
            "source_cols": self._getDataCollectionColumns(self._getDataCollectionForEvent(evt_read)),
            "target": self._getDataResourceIdentity(self._getDataResourceForEvent(evt_write), self.orgvalues['TargetConnectionString']),
            "target_cols": self._getDataCollectionColumns(self._getDataCollectionForEvent(evt_write))
        }
        return identity

    def writeCustomizedOMD(self, filename):
        return self.tree.write(filename, encoding='UTF-8', xml_declaration=True)
