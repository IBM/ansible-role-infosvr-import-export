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
This module adds generic utility functions for interacting with IGC REST APIs
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import requests
import json
import logging
import re


class RestIGC(object):
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
    common code for setting up interactivity with IGC REST API
    '''

    def closeSession(self):
        self.session.request(
            "GET",
            self.baseURL + "/ibm/iis/igc-rest/v1/logout",
            auth=(self.username, self.password)
        )

    def getNextPage(self, paging):
        if 'next' in paging:
            r = self.session.request(
                "GET",
                paging['next'],
                auth=(self.username, self.password)
            )
            if r.status_code == 200:
                return r.json()
            else:
                self.module.warn("Unable to retrieve next page of results -- " + json.dumps(paging))
                return {'items': []}
        else:
            return {'items': []}

    def getAllPages(self, items, paging):
        results = self.getNextPage(paging)
        if len(results['items']) > 0:
            return self.getAllPages(items + results['items'], results['paging'])
        else:
            return items

    def update(self, rid, value):
        self.result['updates'].append({"rid": rid, "value": value})
        r = self.session.request(
            "PUT",
            self.baseURL + "/ibm/iis/igc-rest/v1/assets/" + rid,
            json=value,
            auth=(self.username, self.password)
        )
        return r.status_code, r.json()

    def search(self, query):
        self.result['queries'].append(query)
        r = self.session.request(
            "POST",
            self.baseURL + "/ibm/iis/igc-rest/v1/search",
            json=query,
            auth=(self.username, self.password)
        )
        if r.status_code == 200:
            first_results = r.json()
            return self.getAllPages(first_results['items'], first_results['paging'])
        else:
            return ""

    def getContextForItem(self, rid, asset_type):
        q = {
            "properties": ["name"],
            "types": [asset_type],
            "where": {
                "conditions": [{
                    "value": rid,
                    "operator": "=",
                    "property": "_id"
                }],
                "operator": "and"
            },
            "pageSize": 2
        }
        itemWithCtx = self.search(q)
        if len(itemWithCtx) == 1:
            return itemWithCtx[0]['_context']
        elif len(itemWithCtx) > 1:
            self.module.warn("Multiple items found when expecting only one -- " + json.dumps(q))
            return itemWithCtx[0]['_context']
        else:
            return ""

    def _getCtxQueryParamName(self, asset_type, ctx_type):
        new_type = ctx_type

        # 'host_(engine)' should be search by simply 'host', unless (possibly?) for a transformation_project (?)
        if ctx_type == 'host_(engine)' and asset_type != 'transformation_project':
            new_type = "host"
        # categories are always referred to as 'parent_category' as search properties
        elif ctx_type == 'category':
            new_type = "parent_category"
        # hierarchical data classes refer to 'parent_data_class' as search properties
        elif ctx_type == 'data_class':
            new_type = "parent_data_class"
        # PDM assets refer to a 'design_table_or_view' rather than design_table specifically
        elif ctx_type == 'design_table':
            new_type = "design_table_or_view"
        # BI object relationships are insufficient for this kind of search, so drop these highest-level qualifiers
        # (TODO: at risk of returning multiple objects (warning elsewhere when that occurs)...)
        elif ctx_type == 'bi_root_folder' or ctx_type == 'bi_server':
            self.module.warn("bi_root_folder / bi_server is not currently translated")
            new_type = ""
        # OpenIGC objects need to have their precedeing '$BundleID-' removed
        elif ctx_type.startswith('$'):
            new_type = '$' + ctx_type[(ctx_type.index('-') + 1):]

        return new_type

    def _getMappedValue(self, from_type, from_property, from_value, mappings):
        # default case: return the originally-provided value
        mapped_value = from_value
        for mapping in mappings:
            # Do not return straight away from a match, as there could be multiple
            # mappings for a particular type (ensure we either have a match before returning,
            # or have exhausted all possibilities)
            if from_type == mapping['type'] and from_property == mapping['property']:
                # change name based on regex and 'to' provided in mapping
                mapRE = re.compile(mapping['from'])
                mapped_value = mapRE.sub(mapping['to'], from_value)
        return mapped_value

    def getMappedItem(self, restItem, mappings):
        # Map the item itself (ie. renaming)
        renamed = self._getMappedValue(restItem['_type'], "name", restItem['_name'], mappings)
        q = {
            "properties": ["name"],
            "types": [restItem['_type']],
            "pageSize": 2,
            "where": {
                "conditions": [{
                    "value": renamed,
                    "operator": "=",
                    "property": "name"
                }],
                "operator": "and"
            }
        }
        ctx_path = ""
        folder_path = ""
        pre_host_path = ""
        # Map the context (ie. containment hierarchy)
        for idx, ctx_entry in enumerate(reversed(restItem['_context'])):
            ctx_type = ctx_entry['_type']
            ctx_value = ctx_entry['_name']
            if ctx_type == 'data_file_folder':
                folder_path = ctx_value + "/" + folder_path
            else:
                ctx_value = self._getMappedValue(ctx_type, 'name', ctx_value, mappings)
                if ctx_type == 'host_(engine)' and restItem['_type'].startswith("data_file"):
                    pre_host_path = ctx_path
                ctx_type = self._getCtxQueryParamName(restItem['_type'], ctx_type)
                if idx == 0:
                    ctx_path = ctx_type
                else:
                    ctx_path = ctx_path + "." + ctx_type
                # TODO: for now cannot include a physical_data_model relation as it refers to
                # generic `datagroup` -- ideally find a way around this eventually
                if ctx_type != "" and (ctx_path.find('design_table_or_view.physical_data_model') < 0):
                    q['where']['conditions'].append({
                        "value": ctx_value,
                        "operator": "=",
                        "property": ctx_path + ".name"
                    })
        if folder_path != "":
            # Strip off the preceding and trailing '/' of the folder_path
            mappedPath = self._getMappedValue('data_file', 'path', folder_path[1:-1], mappings)
            q['where']['conditions'].append({
                "value": mappedPath,
                "operator": "=",
                "property": pre_host_path + ".path"
            })
        resSearch = self.search(q)
        if len(resSearch) == 1:
            return resSearch[0]
        elif len(resSearch) > 1:
            self.module.warn("Multiple items found when expecting only one -- " + json.dumps(q))
            return resSearch[0]
        else:
            return ""

    def addRelationshipsToAsset(self,
                                from_asset,
                                to_asset_rids,
                                reln_property,
                                mode,
                                replace_type="",
                                conditions=[],
                                batch=100):
        qAll = {
            "properties": [reln_property],
            "types": [from_asset['_type']],
            "where": {
                "conditions": [{
                    "value": from_asset['_id'],
                    "operator": "=",
                    "property": "_id"
                }],
                "operator": "and"
            },
            "pageSize": batch
        }
        replace_conditions = list(conditions)
        qReplace = {
            "properties": ["name"],
            "types": [replace_type],
            "where": {
                "conditions": replace_conditions,
                "operator": "and"
            },
            "pageSize": batch
        }
        if mode == 'REPLACE_SOME':
            # If only replacing some of the relationships, we need to splice together the update ourselves
            # First get all of the existing relationships for this asset
            allRelationsForAsset = self.search(qAll)
            aReplacementRIDs = []
            aAllRelnRIDs = []
            if isinstance(allRelationsForAsset, list) and len(allRelationsForAsset) > 0:
                for item in allRelationsForAsset:
                    if replace_type == item['_type']:
                        aReplacementRIDs.append(item['_id'])
                    aAllRelnRIDs.append(item['_id'])
                allReplacementsForAsset = []
                if len(aReplacementRIDs) > 0:
                    qReplace['where']['conditions'].append({
                        "value": aReplacementRIDs,
                        "operator": "in",
                        "property": "_id"
                    })
                    allReplacementsForAsset = self.search(qReplace)
                if isinstance(allReplacementsForAsset, list) and len(allReplacementsForAsset) > 0:
                    u = {}
                    u[reln_property] = {
                        "items": [],
                        "mode": "replace"
                    }
                    aRidsToDrop = [x["_id"] for x in allReplacementsForAsset]
                    u[reln_property]['items'] = set(aAllRelnRIDs) - set(aRidsToDrop)
                    return self.update(from_asset['_id'], u)
                elif len(to_asset_rids) > 0:
                    # No relationships to replace, we should just add these
                    u = {}
                    u[reln_property] = {
                        "items": to_asset_rids,
                        "mode": 'append'
                    }
                    return self.update(from_asset['_id'], u)
                else:
                    return 200, "No relationships to add"
            elif len(to_asset_rids) > 0:
                # No relationships at all, we should just add these
                u = {}
                u[reln_property] = {
                    "items": to_asset_rids,
                    "mode": 'append'
                }
                return self.update(from_asset['_id'], u)
            else:
                return 200, "No relationships to add"
        elif mode == 'REPLACE_ALL':
            # If a simple replace all, just do the update directly
            # (and even if empty, to remove any existing relationships)
            u = {}
            u[reln_property] = {
                "items": to_asset_rids,
                "mode": 'replace'
            }
            return self.update(from_asset['_id'], u)
        elif len(to_asset_rids) > 0:
            # If a simple append, just do the update directly (only if there)
            # are actually any RIDs to append
            u = {}
            u[reln_property] = {
                "items": to_asset_rids,
                "mode": ('replace' if mode == 'REPLACE_ALL' else 'append')
            }
            return self.update(from_asset['_id'], u)
        else:
            # Otherwise it's an append, with no assets, so it is a NOOP
            return 200, "No relationships to add"
