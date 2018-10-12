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
import copy
from ansible.module_utils.infosvr_types import get_mapped_value


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
        self.workflow_types = ["category", "term", "information_governance_policy", "information_governance_rule"]
        self.ctxForTypeCounters = {}
        self.ctxCacheByRID = {}
        self.fullCacheByRID = {}
        self.ctxCacheByIdentity = {}
        self.ctxCacheByIdentityDev = {}
        self.propertyMapCache = {}
        self.assetTypeNameCache = {}

    '''
    common code for setting up interactivity with IGC REST API
    '''

    def isWorkflowType(self, asset_type):
        return asset_type in self.workflow_types

    # Note: not using v11.7-specific API so that
    # we are backwards-compatible with v11.5
    def isWorkflowEnabled(self):
        wflCheck = {
            "pageSize": 1,
            "workflowMode": "draft",
            "properties": ["name"],
            "types": ["category", "term", "information_governance_policy", "information_governance_rule"]
        }
        wflResults = self.search(wflCheck, False)
        return (wflResults != '' and wflResults['paging']['numTotal'] > 0)

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
        if r.status_code == 200:
            return r.status_code, r.json()
        else:
            return r.status_code, ""

    def search(self, query, get_all=True):
        self.result['queries'].append(query)
        r = self.session.request(
            "POST",
            self.baseURL + "/ibm/iis/igc-rest/v1/search",
            json=query,
            auth=(self.username, self.password)
        )
        if r.status_code == 200:
            first_results = r.json()
            if get_all:
                return self.getAllPages(first_results['items'], first_results['paging'])
            else:
                return first_results
        else:
            return ""

    def getFullAssetById(self, rid):
        r = self.session.request(
            "GET",
            self.baseURL + "/ibm/iis/igc-rest/v1/assets/" + rid,
            auth=(self.username, self.password)
        )
        if r.status_code == 200:
            return r.json()
        else:
            return ""

    def getPropertyMap(self, asset_type):
        url = "/ibm/iis/igc-rest/v1/types/" + asset_type
        url += "?showEditProperties=true"
        if asset_type in self.propertyMapCache and asset_type in self.assetTypeNameCache:
            return self.assetTypeNameCache[asset_type], self.propertyMapCache[asset_type]
        else:
            r = self.session.request(
                "GET",
                self.baseURL + url,
                auth=(self.username, self.password)
            )
            if r.status_code == 200:
                result = r.json()
                typeName = result['_name']
                self.assetTypeNameCache[asset_type] = typeName
                mapping = {}
                for prop in result['editInfo']['properties']:
                    name = prop['name']
                    display = prop['displayName']
                    mapping[name] = display
                self.propertyMapCache[asset_type] = mapping
                return typeName, mapping
            else:
                return asset_type, {}

    def takeWorkflowAction(self, rids, action, comment=''):
        payload = {
            "ids": rids,
            "comment": comment
        }
        r = self.session.request(
            "POST",
            self.baseURL + "/ibm/iis/igc-rest/v1/workflow/" + action.lower(),
            json=payload,
            auth=(self.username, self.password)
        )
        return (r.status_code == 200)

    def _cacheContexts(self, into_cache, asset_type, workflow, batch=100):
        q = {
            "properties": ["name"],
            "types": [asset_type],
            "pageSize": batch
        }
        if workflow and self.isWorkflowType(asset_type):
            q['workflowMode'] = "draft"
            # Lines below are to see if the item is already in the
            # dev glossary -- unnecessary, as any update needs to go
            # against the dev glossary RID, whether it is already in
            # the workflow or not...
            # q['properties'].append("workflow_current_state")
            # q['where']['conditions'].append({
            #     "property": "workflow_current_state",
            #     "operator": "isNull",
            #     "negated": True
            # })
        allAssetsOfType = self.search(q)
        into_cache[asset_type] = {}
        for asset in allAssetsOfType:
            asset_rid = asset['_id']
            into_cache[asset_type][asset_rid] = asset['_context']

    def getContextForItem(self, asset, workflow, batch=100, limit=5, cache=True):
        rid = asset['_id']
        asset_type = asset['_type']
        assetWithCtx = ""
        # If it is already cached, return it directly
        if cache and asset_type in self.ctxCacheByRID:
            if rid in self.ctxCacheByRID[asset_type]:
                assetWithCtx = self.ctxCacheByRID[asset_type][rid]
            return assetWithCtx
        # Otherwise increase the counters that will trigger caching
        elif asset_type not in self.ctxForTypeCounters:
            self.ctxForTypeCounters[asset_type] = 1
        else:
            self.ctxForTypeCounters[asset_type] += 1
        # If we want to cache, wait until we're above the limit
        if cache and self.ctxForTypeCounters[asset_type] > limit:
            self._cacheContexts(self.ctxCacheByRID, asset_type, workflow, batch)
            if rid in self.ctxCacheByRID[asset_type]:
                assetWithCtx = self.ctxCacheByRID[asset_type][rid]
        # Otherwise do a one-off query for the asset
        else:
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
            if workflow and self.isWorkflowType(asset_type):
                q['workflowMode'] = "draft"
            itemWithCtx = self.search(q, False)
            if 'items' in itemWithCtx and len(itemWithCtx['items']) == 1:
                assetWithCtx = itemWithCtx['items'][0]['_context']
            elif 'items' in itemWithCtx and len(itemWithCtx['items']) > 1:
                self.module.warn("Multiple items found when expecting only one -- " + json.dumps(q))
                assetWithCtx = itemWithCtx['items'][0]['_context']
        return assetWithCtx

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

    def _getIdentity(self, aCtx, name, delim='::'):
        identity = ''
        for ctx in aCtx:
            identity += ctx['_name'] + delim
        identity += name
        return identity

    def _cacheAssets(self, into_cache, asset_type, workflow, batch=100):
        q = {
            "properties": ["name"],
            "types": [asset_type],
            "pageSize": batch
        }
        if workflow and self.isWorkflowType(asset_type):
            q['workflowMode'] = "draft"
            # Lines below are to see if the item is already in the
            # dev glossary -- unnecessary, as any update needs to go
            # against the dev glossary RID, whether it is already in
            # the workflow or not...
            # q['properties'].append("workflow_current_state")
            # q['where']['conditions'].append({
            #     "property": "workflow_current_state",
            #     "operator": "isNull",
            #     "negated": True
            # })
        allAssetsOfType = self.search(q)
        into_cache[asset_type] = {}
        for asset in allAssetsOfType:
            asset_identity = self._getIdentity(asset['_context'], asset['_name'])
            if asset_identity in into_cache[asset_type]:
                self.module.warn("Multiple items with same identity: " + asset_identity)
            else:
                into_cache[asset_type][asset_identity] = asset

    def _getMappedItemPublished(self, asset_type, identity, query, workflow, batch=100, limit=5, cache=True):
        mappedAsset = ""
        # If it is already cached, return it directly
        if cache and asset_type in self.ctxCacheByIdentity:
            if identity in self.ctxCacheByIdentity[asset_type]:
                mappedAsset = self.ctxCacheByIdentity[asset_type][identity]
            return mappedAsset
        # Otherwise increase the counters that will trigger caching
        elif asset_type not in self.ctxForTypeCounters:
            self.ctxForTypeCounters[asset_type] = 1
        else:
            self.ctxForTypeCounters[asset_type] += 1
        # If we want to cache, wait until we're above the limit
        if cache and self.ctxForTypeCounters[asset_type] > limit:
            self._cacheAssets(self.ctxCacheByIdentity, asset_type, workflow, batch)
            if identity in self.ctxCacheByIdentity[asset_type]:
                mappedAsset = self.ctxCacheByIdentity[asset_type][identity]
        # Otherwise do a one-off query for the asset
        else:
            resSearch = self.search(query)
            if len(resSearch) == 1:
                mappedAsset = resSearch[0]
            elif len(resSearch) > 1:
                self.module.warn("Multiple items found when expecting only one -- " + json.dumps(query))
                mappedAsset = resSearch[0]
        return mappedAsset

    def _getMappedItemDevelopment(self, asset_type, identity, query, workflow, batch=100, limit=5, cache=True):
        qDev = copy.deepcopy(query)
        qDev['properties'].append('workflow_current_state')
        mappedAsset = ""
        # If it is already cached, return it directly
        if cache and asset_type in self.ctxCacheByIdentityDev:
            if identity in self.ctxCacheByIdentityDev[asset_type]:
                mappedAsset = self.ctxCacheByIdentityDev[asset_type][identity]
            return mappedAsset
        # Otherwise increase the counters that will trigger caching
        elif asset_type not in self.ctxForTypeCounters:
            self.ctxForTypeCounters[asset_type] = 1
        else:
            self.ctxForTypeCounters[asset_type] += 1
        # If we want to cache, wait until we're above the limit
        if cache and self.ctxForTypeCounters[asset_type] > limit:
            self._cacheAssets(self.ctxCacheByIdentityDev, asset_type, workflow, batch)
            if identity in self.ctxCacheByIdentityDev[asset_type]:
                mappedAsset = self.ctxCacheByIdentityDev[asset_type][identity]
        # Otherwise do a one-off query for the asset
        else:
            if workflow and self.isWorkflowType(asset_type):
                qDev['workflowMode'] = "draft"
                # Lines below are to see if the item is already in the
                # dev glossary -- unnecessary, as any update needs to go
                # against the dev glossary RID, whether it is already in
                # the workflow or not...
                # qDev['properties'].append("workflow_current_state")
                # qDev['where']['conditions'].append({
                #     "property": "workflow_current_state",
                #     "operator": "isNull",
                #     "negated": True
                # })
                resDev = self.search(qDev)
                if len(resDev) == 1:
                    mappedAsset = resDev[0]
                elif len(resDev) > 1:
                    self.module.warn("Multiple items found in workflow -- " + json.dumps(qDev))
                    mappedAsset = resDev[0]
        return mappedAsset

    # Returns the modifiable asset based on the criteria provided
    # (ie. if workflow is enabled & the asset type participates in the workflow
    # it returns the development glossary item; otherwise the
    # published glossary item)
    def getMappedItem(self, restItem, mappings, workflow, batch=100, limit=5, cache=True):
        # Map the item itself (ie. renaming)
        asset_type = restItem['_type']
        renamed = get_mapped_value(asset_type, "name", restItem['_name'], mappings)
        q = {
            "properties": ["name"],
            "types": [asset_type],
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
        aMappedCtx = []
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
                ctx_value = get_mapped_value(ctx_type, 'name', ctx_value, mappings)
                aMappedCtx.insert(0, {"_type": ctx_type, "_name": ctx_value})
                if ctx_type == 'host_(engine)' and asset_type.startswith("data_file"):
                    pre_host_path = ctx_path
                ctx_type = self._getCtxQueryParamName(asset_type, ctx_type)
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
            mappedPath = get_mapped_value('data_file', 'path', folder_path[1:-1], mappings)
            q['where']['conditions'].append({
                "value": mappedPath,
                "operator": "=",
                "property": pre_host_path + ".path"
            })
            # Add folder path to identity from 1st position (0 = host)
            # TODO: anything special to handle for root directory '/' ?
            for path_component in mappedPath.split('/'):
                aMappedCtx.insert(1, {"_type": "data_file_folder", "_name": path_component})
        identity = self._getIdentity(aMappedCtx, renamed)
        mappedItem = ""
        # Attempt to retrieve the item from the development glossary first
        # (ie. if workflow is enabled and the type of asset we're processing
        # participates in the workflow)
        if workflow and self.isWorkflowType(asset_type):
            mappedItem = self._getMappedItemDevelopment(asset_type, identity, q, workflow, batch, limit, cache)
        # Otherwise just grab the item from the published glossary
        else:
            mappedItem = self._getMappedItemPublished(asset_type, identity, q, workflow, batch, limit, cache)
        return mappedItem

    def _cacheFullAssets(self, into_cache, asset_type, workflow, batch=100):
        # Note that this propertyMap includes only editable attributes;
        # should be fine for our purposes (includes name and _context anyway)
        asset_name, propertyMap = self.getPropertyMap(asset_type)
        q = {
            "properties": propertyMap.keys(),
            "types": [asset_type],
            "pageSize": batch
        }
        if workflow and self.isWorkflowType(asset_type):
            q['workflowMode'] = "draft"
            # Lines below are to see if the item is already in the
            # dev glossary -- unnecessary, as any update needs to go
            # against the dev glossary RID, whether it is already in
            # the workflow or not...
            # q['properties'].append("workflow_current_state")
            # q['where']['conditions'].append({
            #     "property": "workflow_current_state",
            #     "operator": "isNull",
            #     "negated": True
            # })
        allAssetsOfType = self.search(q)
        for asset in allAssetsOfType:
            asset_rid = asset['_id']
            into_cache[asset_rid] = asset

    # Retrieve all pages of relationships for an asset
    # - should only call this for assets we need to look at;
    #   not any benefit to trying to cache this (will be potential unnecessary work)
    def _getAllRelationshipsForAsset(self, assetObj):
        for prop in assetObj:
            if isinstance(assetObj[prop], dict) and 'paging' in assetObj[prop]:
                assetObj[prop]['items'] = self.getAllPages(assetObj[prop]['items'], assetObj[prop]['paging'])

    # Retrieves the full definition of an asset
    # (ie. ALL of its properties and relationships)
    def getFullAsset(self, min_asset, workflow, batch=100, limit=5, cache=True):
        fullAsset = ""
        asset_type = min_asset['_type']
        asset_rid = min_asset['_id']
        # If it is already cached, return it directly
        if cache and asset_rid in self.fullCacheByRID:
            fullAsset = self.fullCacheByRID[asset_rid]
            self._getAllRelationshipsForAsset(fullAsset)
            return fullAsset
        # Otherwise increase the counters that will trigger caching
        elif asset_type not in self.ctxForTypeCounters:
            self.ctxForTypeCounters[asset_type] = 1
        else:
            self.ctxForTypeCounters[asset_type] += 1
        # If we want to cache, wait until we're above the limit
        if cache and self.ctxForTypeCounters[asset_type] > limit:
            self._cacheFullAssets(self.fullCacheByRID, asset_type, workflow, batch)
            if asset_rid in self.fullCacheByRID:
                fullAsset = self.fullCacheByRID[asset_rid]
                self._getAllRelationshipsForAsset(fullAsset)
        # Otherwise do a one-off query for the asset
        else:
            # Note that this propertyMap includes only editable attributes;
            # should be fine for our purposes (includes name and _context anyway)
            asset_name, propertyMap = self.getPropertyMap(asset_type)
            q = {
                "properties": propertyMap.keys(),
                "types": [asset_type],
                "pageSize": 2,
                "where": {
                    "conditions": [{
                        "value": asset_rid,
                        "operator": "=",
                        "property": "_id"
                    }],
                    "operator": "and"
                }
            }
            if workflow and self.isWorkflowType(asset_type):
                q['workflowMode'] = "draft"
                # Lines below are to see if the item is already in the
                # dev glossary -- unnecessary, as any update needs to go
                # against the dev glossary RID, whether it is already in
                # the workflow or not...
                # q['properties'].append("workflow_current_state")
                # q['where']['conditions'].append({
                #     "property": "workflow_current_state",
                #     "operator": "isNull",
                #     "negated": True
                # })
            res = self.search(q)
            if len(res) == 1:
                fullAsset = res[0]
                self._getAllRelationshipsForAsset(fullAsset)
            elif len(res) > 1:
                self.module.warn("Multiple items found in workflow -- " + json.dumps(q))
                fullAsset = res[0]
                self._getAllRelationshipsForAsset(fullAsset)
        return fullAsset

    # Ensure the asset is put into an editable state
    # (ie. if it is in the workflow and not in DRAFT status, return it to
    # draft status)
    def _returnToEditableState(self, asset):
        if 'workflow_current_state' in asset and 'DRAFT' not in asset['workflow_current_state']:
            return self.takeWorkflowAction([asset['_id']], 'return', 'Returning to draft to update relationships')
        else:
            return True

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
                    if self._returnToEditableState(from_asset):
                        return self.update(from_asset['_id'], u)
                    else:
                        403, "Cannot update asset to add relationships: " + json.dumps(from_asset)
                elif len(to_asset_rids) > 0:
                    # No relationships to replace, we should just add these
                    u = {}
                    u[reln_property] = {
                        "items": to_asset_rids,
                        "mode": 'append'
                    }
                    if self._returnToEditableState(from_asset):
                        return self.update(from_asset['_id'], u)
                    else:
                        403, "Cannot update asset to add relationships: " + json.dumps(from_asset)
                else:
                    return 200, "No relationships to add"
            elif len(to_asset_rids) > 0:
                # No relationships at all, we should just add these
                u = {}
                u[reln_property] = {
                    "items": to_asset_rids,
                    "mode": 'append'
                }
                if self._returnToEditableState(from_asset):
                    return self.update(from_asset['_id'], u)
                else:
                    403, "Cannot update asset to add relationships: " + json.dumps(from_asset)
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
            if self._returnToEditableState(from_asset):
                return self.update(from_asset['_id'], u)
            else:
                403, "Cannot update asset to add relationships: " + json.dumps(from_asset)
        elif len(to_asset_rids) > 0:
            # If a simple append, just do the update directly (only if there
            # are actually any RIDs to append)
            u = {}
            u[reln_property] = {
                "items": to_asset_rids,
                "mode": ('replace' if mode == 'REPLACE_ALL' else 'append')
            }
            if self._returnToEditableState(from_asset):
                return self.update(from_asset['_id'], u)
            else:
                403, "Cannot update asset to add relationships: " + json.dumps(from_asset)
        else:
            # Otherwise it's an append, with no assets, so it is a NOOP
            return 200, "No relationships to add"
