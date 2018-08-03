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
This module adds generic utility functions for interacting with IA REST APIs
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import requests
import logging


class RestIA(object):
    def __init__(self, module, result, username, password, host, port, cert):
        self.module = module
        self.result = result
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.session = requests.Session()
        # http://docs.python-requests.org/en/master/user/advanced/#ssl-cert-verification
        if cert:
            self.session.verify = cert
        self.baseURL = "https://" + host + ":" + port
        logging.getLogger("requests").setLevel(logging.ERROR)
        logging.getLogger("urllib3").setLevel(logging.ERROR)

    '''
    common code for setting up interactivity with IA REST API
    '''

    def closeSession(self):
# TODO: does this exist for IA REST API?
#        self.session.request(
#            "GET",
#            self.baseURL + "/ibm/iis/igc-rest/v1/logout",
#            auth=(self.username, self.password)
#        )

    def _makeRequest(self, method, url, params=None, payload=None):
        if payload:
            headers = {'Content-Type': 'application/xml'}
            return self.session.request(
                method,
                self.baseURL + url,
                data=payload,
                headers=headers,
                auth=(self.username, self.password)
            )
        else:
            return self.session.request(
                method,
                self.baseURL + url,
                params=params,
                auth=(self.username, self.password)
            )

    def getProjectList(self):
        r = self._makeRequest("GET", "/ibm/iis/ia/api/projects")
        if r.status_code == 200:
            return r.text
        else:
            self.module.warn("Unable to retrieve project list")
            return None

    def getProjectDetails(self, name):
        r = self._makeRequest("GET", "/ibm/iis/ia/api/project", params={"projectName": name})
        if r.status_code == 200:
            return r.text
        else:
            self.module.warn("Unable to retrieve project details for '" + name + "'")
            return None

    def getDataRuleDefinitionList(self, project):
        r = self._makeRequest("GET", "/ibm/iis/ia/api/ruleDefinitions", params={"projectName": project})
        if r.status_code == 200:
            return r.text
        else:
            self.module.warn("Unable to retrieve data rule definition list for '" + project + "'")

    def getDataRuleDefinition(self, project, name):
        payload = {
            "projectName": project,
            "ruleName": name
        }
        r = self._makeRequest("GET", "/ibm/iis/ia/api/ruleDefinition", params=payload)
        if r.status_code == 200:
            return r.text
        else:
            self.module.warn("Unable to retrieve data rule definition '" + name + "' from project '" + project + "'")
            return None

    def getDataRuleList(self, project):
        r = self._makeRequest("GET", "/ibm/iis/ia/api/executableRules", params={"projectName": project})
        if r.status_code == 200:
            return r.text
        else:
            self.module.warn("Unable to retrieve data rule list for '" + project + "'")

    def getDataRule(self, project, name):
        payload = {
            "projectName": project,
            "ruleName": name
        }
        r = self._makeRequest("GET", "/ibm/iis/ia/api/executableRule", params=payload)
        if r.status_code == 200:
            return r.text
        else:
            self.module.warn("Unable to retrieve data rule '" + name + "' from project '" + project + "'")
            return None

    def getDataRuleResults(self, project, name):
        payload = {
            "projectName": project,
            "ruleName": name
        }
        r = self._makeRequest("GET", "/ibm/iis/ia/api/executableRule/executionHistory", params=payload)
        if r.status_code == 200:
            return r.text
        else:
            self.module.warn("Unable to retrieve data rule results for '" + name + "' in project '" + project + "'")

    def getMetrics(self, project):
        payload = {
            "projectName": project
        }
        r = self._makeRequest("GET", "/ibm/iis/ia/api/metrics", params={"projectName": project})
        if r.status_code == 200:
            return r.text
        else:
            self.module.warn("Unable to retrieve metrics for project '" + project + "'")
            return None

    def getMetricResults(self, project, name):
        payload = {
            "projectName": project,
            "metricName": name
        }
        r = self._makeRequest("GET", "/ibm/iis/ia/api/metric/executionHistory", params=payload)
        if r.status_code == 200:
            return r.text
        else:
            self.module.warn("Unable to retrieve metric results for '" + name + "' in project '" + project + "'")
            return None

    def getGlobalVariables(self):
        r = self._makeRequest("GET", "/ibm/iis/ia/api/globalVariables")
        if r.status_code == 200:
            return r.text
        else:
            self.module.warn("Unable to retrieve global variables")
            return None

    # Same create endpoint for everything
    def create(self, payload):
        r = self._makeRequest("POST", "/ibm/iis/ia/api/create", payload=payload)
        if r.status_code == 200:
            return r.text
        else:
            self.module.warn("Unable to create objects in payload")
            return r.text

    # Same update endpoint for everything, but should in theory cover:
    # - virtual tables
    # - data rule definitions
    # - data rules
    # - metrics
    # - global variables
    def update(self, payload):
        r = self._makeRequest("POST", "/ibm/iis/ia/api/update", payload=payload)
        if r.status_code == 200:
            return r.text
        else:
            self.module.warn("Unable to update objects in payload")
            return r.text
