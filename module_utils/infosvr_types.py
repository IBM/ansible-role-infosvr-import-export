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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

common_properties = ["modified_on"]

# TODO: known missing asset types:
#  - standardization_object (related to QualityStage specifications)
#  - dsstage_type (related to adding your own stages in DataStage)
#  - data_element (covered by table_definition, which will be modified when an element is modified)
#  - (ds)data_connection (related to DCNs -- not clear how these are addressed in DataStage)
asset_type_to_properties = {
    "dsjob": ["type"] + common_properties,
    "routine": common_properties,
    "shared_container": ["type"] + common_properties,
    "table_definition": ["data_store", "data_schema", "data_source_name"] + common_properties,
    "parameter_set": common_properties,
    "data_class": ["class_code"] + common_properties,
    "extension_mapping_document": ["file_name", "parent_folder"] + common_properties,
    "application": common_properties,
    "file": common_properties,
    "stored_procedure_definition": common_properties,
    "data_rule_definition": ["project"] + common_properties,
    "data_rule_set_definition": ["project"] + common_properties,
    "data_rule": ["project"] + common_properties,
    "data_rule_set": ["project"] + common_properties,
    "metric": ["project"] + common_properties
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

ia_asset_type_to_extract_type = {
    "data_rule_definition": "DataRuleDefinitions/DataRuleDefinition",
    "data_rule_set_definition": "DataRuleDefinitions/RuleSetDefinition",
    "data_rule": "DataRuleDefinitions/DataRuleDefinition/ExecutableRules/ExecutableRule",
    "data_rule_set": "DataRuleDefinitions/RuleSetDefinition/ExecutableRules/ExecutableRule",
    "metric": "Metrics/Metric"
}

# Necessary to avoid trying to export default objects that are there as part of vanilla Information Server installation
asset_blacklists = {
    "table_definition": [
        "Examples\\\\Folder",
        "WebSphere MQ Connector\\\\MQMessage",
        "Examples\\\\SOAPbody",
        "Distributed Transaction\\\\TransactionStatus"
    ]
}


def get_properties(asset_type):
    if asset_type in asset_type_to_properties:
        return asset_type_to_properties[asset_type]
    else:
        return common_properties


def get_asset_extract_object(asset_type, rest_result):
    if asset_type == 'dsjob':
        return _getDsJobExtractObjects(rest_result)
    elif asset_type == 'routine':
        return _getDsRoutineExtractObjects(rest_result)
    elif asset_type == 'shared_container':
        return _getDsSharedContainerExtractObjects(rest_result)
    elif asset_type == 'table_definition':
        return _getDsTableDefinitionExtractObjects(rest_result)
    elif asset_type == 'parameter_set':
        return _getDsParameterSetExtractObjects(rest_result)
    elif asset_type == 'data_class':
        return _getDataClassExtractObjects(rest_result)
    elif asset_type == 'extension_mapping_document':
        return _getExtensionMappingDocumentExtractObjects(rest_result)
    elif asset_type == 'application' or asset_type == 'file' or asset_type == 'stored_procedure_definition':
        return _getExternalAssetExtractObjects(rest_result)
    elif asset_type == 'category' or asset_type == 'term' or asset_type == 'information_governance_policy' or asset_type == 'information_governance_rule' or asset_type == 'label':
        return _getRidOnly(rest_result)
    elif asset_type == 'data_rule_definition' or asset_type == 'data_rule_set_definition' or asset_type == 'data_rule' or asset_type == 'data_rule_set' or asset_type == 'metric':
        return _getInfoAnalyzerExtractObjects(rest_result)
    else:
        return "UNIMPLEMENTED"


def _getRidOnly(rest_result):
    return rest_result['_id']


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
    elif rest_result['type'] == "Sequence":
        extract['jobs'] += ".qjb"
    elif rest_result['type'] == "Server":
        extract['jobs'] += ".sjb"
    else:
        extract['jobs'] += ".*"
    return extract


def _getDsRoutineExtractObjects(rest_result):
    # https://www.ibm.com/support/knowledgecenter/en/SSZJPZ_11.7.0/com.ibm.swg.im.iis.iisinfsv.assetint.doc/topics/depasset.html
    # Note: because routines must be universally unique in naming within a project (irrespective of folder)
    # we can safely ignore the folder altogether (just wildcard it)
    extract = {
        "host": rest_result['_context'][0]['_name'],
        "project": rest_result['_context'][1]['_name'],
        "folder": "*",
        "jobs": rest_result['_name']
    }
    # TODO: not currently any way to distinguish between Parallel and Server routines
    # from the REST API results (?) -- so just wildcard the extension for now...
    extract['jobs'] += ".*"
    return extract


def _getDsSharedContainerExtractObjects(rest_result):
    # https://www.ibm.com/support/knowledgecenter/en/SSZJPZ_11.7.0/com.ibm.swg.im.iis.iisinfsv.assetint.doc/topics/depasset.html
    # Note: because shared containres must be universally unique in naming within a project (irrespective of folder)
    # we can safely ignore the folder altogether (just wildcard it)
    extract = {
        "host": rest_result['_context'][0]['_name'],
        "project": rest_result['_context'][1]['_name'],
        "folder": "*",
        "jobs": rest_result['_name']
    }
    if rest_result['type'] == "PARALLEL":
        extract['jobs'] += ".psc"
    elif rest_result['type'] == "SERVER":
        extract['jobs'] += ".ssc"
    else:
        extract['jobs'] += ".*"
    return extract


def _getQualifiedNameForTableDefinition(rest_result):
    qualifiedName = rest_result['_name']
    if rest_result['data_source_name'] != '':
        qualifiedName = rest_result['data_source_name'] + '\\\\' + qualifiedName
    if rest_result['data_store'] != '':
        qualifiedName = rest_result['data_store'] + '\\\\' + qualifiedName
    if qualifiedName not in asset_blacklists['table_definition']:
        return qualifiedName + ".tbd"
    else:
        return ""


def _getDsTableDefinitionExtractObjects(rest_result):
    # https://www.ibm.com/support/knowledgecenter/en/SSZJPZ_11.7.0/com.ibm.swg.im.iis.iisinfsv.assetint.doc/topics/depasset.html
    # Note: because table definitions must be universally unique in naming within a project (irrespective of folder)
    # we can safely ignore the folder altogether (just wildcard it)
    extract = {
        "host": rest_result['_context'][0]['_name'],
        "project": rest_result['_context'][1]['_name'],
        "folder": "*",
        "jobs": _getQualifiedNameForTableDefinition(rest_result)
    }
    if extract['jobs'] != '':
        return extract


def _getDsParameterSetExtractObjects(rest_result):
    # https://www.ibm.com/support/knowledgecenter/en/SSZJPZ_11.7.0/com.ibm.swg.im.iis.iisinfsv.assetint.doc/topics/depasset.html
    # Note: because parameter sets must be universally unique in naming within a project (irrespective of folder) we can
    # safely ignore the folder altogether (just wildcard it)
    extract = {
        "host": rest_result['_context'][0]['_name'],
        "project": rest_result['_context'][1]['_name'],
        "folder": "*",
        "jobs": rest_result['_name']
    }
    extract['jobs'] += ".pst"
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
        extract['type'] = xa_asset_type_to_extract_type[rest_result['_type']]
    return extract


def _getInfoAnalyzerExtractObjects(rest_result):
    extract = {
        "project": rest_result['project'][0],
        "name": rest_result['_name']
    }
    if rest_result['_type'] in ia_asset_type_to_extract_type:
        extract['type'] = ia_asset_type_to_extract_type[rest_result['_type']]
    return extract
