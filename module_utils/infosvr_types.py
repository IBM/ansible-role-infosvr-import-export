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
This module adds generic utility functions for translating between Information Server asset types
"""

import json

common_properties = [ "modified_on" ]

asset_type_to_properties = {
  "dsjob": [ "type" ] + common_properties,
  "data_class": [ "class_code" ] + common_properties,
  "extension_mapping_document": [ "file_name", "parent_folder" ] + common_properties,
  "application": common_properties,
  "file": common_properties,
  "stored_procedure_definition": common_properties
}

xa_asset_type_to_extract_type = {
  "application": "Application",
  "file": "File",
  "stored_procedure_definition": "StoredProcedure",
  "in_parameter": "InParameter",
  "out_parameter": "OutParameter",
  "inout_parameter": "InOutParameter",
  "result_column": "ResultColumn",
  "object_type": "ObjectType",
  "method": "Method",
  "input_parameter": "InputParameter",
  "output_value": "OutputValue"
}

def get_properties(asset_type):
  if asset_type in asset_type_to_properties:
    return asset_type_to_properties[asset_type]
  else:
    return common_properties

def get_asset_extract_object(asset_type, rest_result):
  if asset_type == 'dsjob':
    return _getDsJobExtractObjects(rest_result)
  elif asset_type == 'data_class':
    return _getDataClassExtractObjects(rest_result)
  elif asset_type == 'extension_mapping_document':
    return _getExtensionMappingDocumentExtractObjects(rest_result)
  elif asset_type == 'application' or asset_type == 'file' or asset_type == 'stored_procedure_definition':
    return _getExternalAssetExtractObjects(rest_result)
  else:
    return "UNIMPLEMENTED"

def _getDsJobExtractObjects(rest_result):
  # https://www.ibm.com/support/knowledgecenter/en/SSZJPZ_11.7.0/com.ibm.swg.im.iis.iisinfsv.assetint.doc/topics/depasset.html
  # Note: the "folder" returned by REST API does not include certain information (eg. the "/Jobs/..." portion);
  # furthermore because jobs must be universally unique in naming within a project (irrespective of folder) we can
  # safely ignore the folder altogether (just wildcard it)
  extract = {
    "host": rest_result['_context'][0]['_name'],
    "project": rest_result['_context'][1]['_name'],
    "folder": "*",
    "jobs": rest_result['_name']
  }
  # TODO: figure out all potential extensions based on different "type" settings
  if rest_result['type'] == "Parallel":
    extract['jobs'] += ".pjb"
  else:
    extract['jobs'] += ".*"
  return extract

def _getDataClassExtractObjects(rest_result):
  if len(rest_result['_context']) == 0:
    extract = {
      "class_code": rest_result['class_code']
    }
    return extract

def _getExtensionMappingDocumentExtractObjects(rest_result):
  extract = {
    "name": rest_result['_name'],
    "folder": rest_result['parent_folder']['_name'],
    "file": rest_result['file_name']
  }
  return extract

def _getExternalAssetExtractObjects(rest_result):
  extract = {
    "name": rest_result['_name']
  }
  if rest_result['_type'] in xa_asset_type_to_extract_type:
    extract['type'] = xa_asset_type_to_extract_type[ rest_result['_type'] ]
  return extract
