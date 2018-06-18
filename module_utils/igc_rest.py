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

import requests
import json
import logging
import re

class RestIGC(object):
  def __init__(self, module, result, username, password, host, port):
    self.module = module
    self.result = result
    self.username = username
    self.password = password
    self.host = host
    self.port = port
    self.session = requests.Session()
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
      verify=False,
      auth=(self.username, self.password)
    )

  def getNextPage(self, paging):
    if 'next' in paging:
      r = self.session.request(
        "GET",
        paging['next'],
        verify=False,
        auth=(self.username, self.password)
      )
      if r.status_code == 200:
        return r.json()
      else:
        self.module.warn("Unable to retrieve next page of results -- " + json.dumps(paging))
        return { 'items': [] }
    else:
      return { 'items': [] }
  
  def getAllPages(self, items, paging):
    results = self.getNextPage(paging)
    if len(results['items']) > 0:
      return self.getAllPages(items + results['items'], results['paging'])
    else:
      return items

  def update(self, rid, value):
    self.result['updates'].append({ "rid": rid, "value": value });
    r = self.session.request(
      "PUT",
      self.baseURL + "/ibm/iis/igc-rest/v1/assets/" + rid,
      json=value,
      verify=False,
      auth=(self.username, self.password)
    )
    return r.status_code, r.json()

  def search(self, query):
    self.result['queries'].append(query);
    r = self.session.request(
      "POST",
      self.baseURL + "/ibm/iis/igc-rest/v1/search",
      json=query,
      verify=False,
      auth=(self.username, self.password)
    )
    if r.status_code == 200:
      first_results = r.json()
      return self.getAllPages(first_results['items'], first_results['paging'])
    else:
      return ""

  def getContextForItem(self, rid, asset_type):
    q = {
      "properties": [ "name" ],
          "types": [ asset_type ],
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
    # BI object relationships are insufficient for this kind of search, so drop these highest-level qualifiers
    # (TODO: at risk of returning multiple objects (warning elsewhere when that occurs)...)
    elif ctx_type == 'bi_root_folder' or ctx_type == 'bi_server':
      self.module.warn("bi_root_folder / bi_server is not currently translated")
      new_type = "";
    # OpenIGC objects need to have their precedeing '$BundleID-' removed
    elif ctx_type.startswith('$'):
      new_type = '$' + ctx_type[(ctx_type.index('-') + 1):]

    return new_type

  def _getMappedValue(self, from_type, from_property, from_value, mappings):
    for mapping in mappings:
      if from_type == mapping['type'] and from_property == mapping['property']:
        # change name based on regex and 'to' provided in mapping
        mapRE = re.compile(mappings['from'])
        return mapRE.sub(mappings['to'], from_value)
    # default case: return the originally-provided value
    return from_value

  def getMappedItem(self, restItem, mappings):
    q = {
      "properties": [ "name" ],
      "types": [ restItem['_type'] ],
      "pageSize": 2,
      "where": {
        "conditions": [{
          "value": restItem['_name'],
          "operator": "=",
          "property": "name"
        }],
        "operator": "and"
      }
    }
    ctx_path = "";
    folder_path = "";
    pre_host_path = "";
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
        if ctx_type != "":
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

  def addRelationshipsToAsset(self, from_asset, to_asset_rids, reln_property, mode, replace_type="", conditions=[], batch=100):
    qAll = {
      "properties": [ reln_property ],
      "types": [ from_asset['_type'] ],
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
    qReplace = {
      "properties": [ "name" ],
      "types": [ replace_type ],
      "where": {
        "conditions": conditions,
        "operator": "and"
      },
      "pageSize": batch
    }
    if mode == 'REPLACE_SOME':
      # If only replacing some of the relationships, we need to splice together the update ourselves
      # First get all of the existing relationships for this asset
      allRelationsForAsset = self.search(qAll)
      aReplacementRIDs = [];
      aAllRelnRIDs = [];
      for item in allRelationsForAsset:
        if replace_type == item['_type']:
          aReplacementRIDs.append(item['_id'])
        aAllRelnRIDs.append(item['_id'])
      qReplace['where']['conditions'].append({
        "value": aReplacementRIDs,
        "operator": "in",
        "property": "_id"
      })
      allReplacementsForAsset = self.search(qReplace)
      for item in allReplacementsForAsset:
        u = {};
        u[reln_property] = {
          "items": [],
          "mode": "replace"
        }
        aRidsToDrop = [x["_id"] for x in allReplacementsForAsset]
        u[reln_property]['items'] = set(aAllRelnRIDs) - set(aRidsToDrop)
        return self.update(from_asset['_id'], u)
    else:
      # If a simple append or replace all, just do the update directly
      u = {};
      u[reln_property] = {
        "items": to_asset_rids,
        "mode": ('replace' if mode == 'REPLACE_ALL' else 'append')
      }
      return self.update(from_asset['_id'], u)
