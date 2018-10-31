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

import re

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
    "table_definition": ["data_store", "data_schema", "data_source_name", "data_source_type"] + common_properties,
    "parameter_set": common_properties,
    "data_class": [
        "class_code",
        "provider",
        "parent_data_class.class_code",
        "parent_data_class.provider",
        "parent_data_class.parent_data_class.class_code",
        "parent_data_class.parent_data_class.provider"
    ] + common_properties,
    "extension_mapping_document": ["file_name", "parent_folder"] + common_properties,
    "application": common_properties,
    "file": common_properties,
    "stored_procedure_definition": common_properties,
    "data_rule_definition": ["project"] + common_properties,
    "data_rule_set_definition": ["project"] + common_properties,
    "data_rule": ["project"] + common_properties,
    "data_rule_set": ["project"] + common_properties,
    "metric": ["project"] + common_properties,
    "label": ["name"],
    "logical_data_model": ["namespace"] + common_properties,
    "physical_data_model": ["namespace"] + common_properties,
    "database": common_properties,
    "database_schema": common_properties,
    "data_file": common_properties
}

asset_relationship_properties_to_single_types = {
    "labels",
    "stewards",
    "assigned_to_terms",
    "implements_rules",
    "governed_by_rules"
}

# Up-to-date as of v11.7.0.2
asset_types_for_import_asset_values = {
    "application": "MwbExtensions.EDS_Application",
    "attribute": "MDM.IISMDMMemberAttribute",
    "attribute_type_field": "MDM.IISMDMSegmentField",
    "attribute_type": "MDM.IISMDMSegment",
    "bi_collection": "ASCLBI.OLAPCollection",
    "bi_collection_member": "ASCLBI.OLAPMember",
    "bi_cube": "ASCLBI.OLAPCube",
    "bi_model": "ASCLBI.OLAPModel",
    "bi_report": "ASCLBI.ReportDef",
    "composite_view": "MDM.IISMDMCompositeView",
    "database_alias": "ASCLModel.DatabaseAlias",
    "database": "ASCLModel.Database",
    "database_column": "ASCLModel.DatabaseField",
    "database_schema": "ASCLModel.DataSchema",
    "database_table": "ASCLModel.DatabaseTable",
    "data_class": "ASCLAnalysis.DataClass",
    "data_file": "ASCLModel.DefaultDataFile",
    "data_file_definition": "ASCLModel.DataFileDef",
    "data_file_definition_field": "ASCLModel.DataFileAttributeDef",
    "data_file_definition_record": "ASCLModel.DataFileElementDef",
    "data_file_field": "ASCLModel.DataFileAttribute",
    "data_file_folder": "ASCLModel.DataFileFolder_noBucket",
    "data_file_record": "ASCLModel.DataFileElement",
    "data_science_model": "dsx.AnalyticsModel",
    "data_science_project": "dsx.AnalyticsProject",
    "design_column": "ASCLModel.PhysicalAttribute",
    "design_stored_procedure": "ASCLModel.StoredProcedure_Model",
    "design_stored_procedure_parameter": "ASCLModel.ParameterDef_SPModel",
    "design_table": "ASCLModel.PhysicalEntity",
    "design_view": "ASCLModel.DesignView",
    "endpoint": "StreamsEndPoint.EndPoint",
    "entity_attribute": "ASCLLogicalModel.Attribute",
    "entity_type": "MDM.IISMDMEntity",
    "extension_mapping_document": "MwbExtensions.MappingDoc_User",
    "extension_mapping": "MwbExtensions.Mapping",
    "file": "MwbExtensions.EDS_File",
    "filter": "siq.Filter",
    "host": "ASCLModel.HostSystem",
    "idoc_field": "ASCLModel.SAP_IDOC_Field",
    "idoc_segment_type": "ASCLModel.SAP_IDOC_SegmentType",
    "idoc_type": "ASCLModel.SAP_IDOC_TYPE",
    "infoset": "siq.Infoset",
    "inout_parameter": "MwbExtensions.EDS_InOutParameter",
    "in_parameter": "MwbExtensions.EDS_InParameter",
    "input_parameter": "MwbExtensions.EDS_InputParameter",
    "instance": "siq.SIQInstance",
    "logical_data_model": "ASCLLogicalModel.LogicalModel",
    "logical_entity": "ASCLLogicalModel.Entity",
    "mdm_model": "MDM.IISMDMModel",
    "member_type": "MDM.IISMDMMember",
    "method": "MwbExtensions.EDS_Method",
    "notebook": "dsx.Notebook",
    "object_type": "MwbExtensions.EDS_ObjectType",
    "out_parameter": "MwbExtensions.EDS_OutParameter",
    "output_value": "MwbExtensions.EDS_OutputValue",
    "physical_data_model": "ASCLModel.PhysicalModel",
    "physical_object_attribute": "MDM.IISMDMPhysicalObjectAttribute",
    "physical_object": "MDM.IISMDMPhysicalObject",
    "rshiny_app": "dsx.RShinyApp",
    "schema": "ASCLModel.DataSchema",
    "stored_procedure": "ASCLModel.StoredProcedure_Schema",
    "stored_procedure_definition": "MwbExtensions.EDS_StoredProcedure",
    "stored_procedure_parameter": "ASCLModel.ParameterDef_SPSchema",
    "tuple_attribute": "StreamsEndPoint.Attribute",
    "view": "ASCLModel.DatabaseView",
    "volume": "siq.Volume",
    "xml_schema_definition": "XSDModel.XSDSchema",
    "xsd_attribute_group": "XSDModel.XSDAttributeGroup",
    "xsd_attribute": "XSDModel.XSDAttribute_ProperAttribute",
    "xsd_complex_type": "XSDModel.XSDComplexType",
    "xsd_element_group": "XSDModel.XSDElementGroup",
    "xsd_element": "XSDModel.XSDElement_ProperElement",
    "xsd_simple_type": "XSDModel.XSDSimpleType"
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

# Necessary to avoid trying to export default objects that are there as part of vanilla Information Server installation
asset_blacklists = {
    "table_definition": [
        "Built-In\\\\Examples\\\\Folder",
        "Real Time\\\\WebSphere MQ Connector\\\\MQMessage",
        "Built-In\\\\Examples\\\\SOAPbody",
        "Database\\\\Distributed Transaction\\\\TransactionStatus"
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
    elif (asset_type == 'application' or
          asset_type == 'file' or
          asset_type == 'stored_procedure_definition'):
        return _getExternalAssetExtractObjects(rest_result)
    elif (asset_type == 'category' or
          asset_type == 'term' or
          asset_type == 'information_governance_policy' or
          asset_type == 'information_governance_rule' or
          asset_type == 'label' or
          asset_type.startswith('$')):
        return _getRidOnly(rest_result)
    elif (asset_type == 'data_rule_definition' or
          asset_type == 'data_rule_set_definition' or
          asset_type == 'data_rule' or
          asset_type == 'data_rule_set' or
          asset_type == 'metric'):
        return _getInfoAnalyzerExtractObjects(rest_result)
    elif (asset_type == 'logical_data_model' or
          asset_type == 'physical_data_model'):
        return _getDataModelExtractObjects(rest_result)
    elif (asset_type == 'database' or
          asset_type == 'database_schema'):
        return _getDatabaseExtractObjects(rest_result)
    elif asset_type == 'data_file':
        return _getDataFileExtractObjects(rest_result)
    else:
        return "UNIMPLEMENTED"


def get_mapped_value(from_type, from_property, from_value, mappings):
    # default case: return the originally-provided value
    mapped_value = from_value
    for mapping in mappings:
        # Do not return straight away from a match, as there could be multiple
        # mappings for a particular type (ensure we either have a match before returning,
        # or have exhausted all possibilities)
        if from_type == mapping['type'] and from_property == mapping['property']:
            if re.search(mapping['from'], from_value):
                # change name based on regex and 'to' provided in mapping, only
                # if there was a match (if no match, we might clobber a previous match)
                mapped_value = re.sub(mapping['from'], mapping['to'], from_value)
    return mapped_value


def is_simple_native_relationship(prop_name):
    return prop_name in asset_relationship_properties_to_single_types


def is_supported_by_import_asset_values(asset_type):
    return asset_type in asset_types_for_import_asset_values


def get_mapped_identity(json_object, mappings=[]):
    new_obj = {}
    _type = json_object['_type']
    _name = get_mapped_value(_type, 'name', json_object['_name'], mappings)
    new_obj['_type'] = _type
    new_obj['_name'] = _name
    new_obj['_context'] = []
    for ctx in json_object['_context']:
        _ctx = get_mapped_value(ctx['_type'], 'name', ctx['_name'], mappings)
        new_obj['_context'].append({
            '_type': ctx['_type'],
            '_name': _ctx
        })
    return new_obj


def _getRidOnly(rest_result):
    return rest_result['_id']


def _getContextPath(rest_result, delim='/'):
    path = ""
    for item in rest_result['_context']:
        path = path + delim + item['_name']
    return path[1:]


def _getDsJobExtractObjects(rest_result):
    # https://www.ibm.com/support/knowledgecenter/en/SSZJPZ_11.7.0/com.ibm.swg.im.iis.iisinfsv.assetint.doc/topics/depasset.html
    # Note: the "folder" returned by REST API does not include certain information (eg. the "/Jobs/..." portion);
    # furthermore because jobs must be universally unique in naming within a project (irrespective of folder) we can
    # safely ignore the folder altogether (just wildcard it)
    jobname = rest_result['_name']
    # TODO: figure out all potential extensions based on different "type" settings
    if rest_result['type'] == "Parallel":
        jobname += ".pjb"
    elif rest_result['type'] == "Sequence":
        jobname += ".qjb"
    elif rest_result['type'] == "Server":
        jobname += ".sjb"
    else:
        jobname += ".*"
    return rest_result['_context'][0]['_name'] + "/" + rest_result['_context'][1]['_name'] + "/*/" + jobname


def _getDsRoutineExtractObjects(rest_result):
    # https://www.ibm.com/support/knowledgecenter/en/SSZJPZ_11.7.0/com.ibm.swg.im.iis.iisinfsv.assetint.doc/topics/depasset.html
    # Note: because routines must be universally unique in naming within a project (irrespective of folder)
    # we can safely ignore the folder altogether (just wildcard it)
    # TODO: not currently any way to distinguish between Parallel and Server routines
    # from the REST API results (?) -- so just wildcard the extension for now...
    jobname = rest_result['_name'] + ".*"
    return rest_result['_context'][0]['_name'] + "/" + rest_result['_context'][1]['_name'] + "/*/" + jobname


def _getDsSharedContainerExtractObjects(rest_result):
    # https://www.ibm.com/support/knowledgecenter/en/SSZJPZ_11.7.0/com.ibm.swg.im.iis.iisinfsv.assetint.doc/topics/depasset.html
    # Note: because shared containres must be universally unique in naming within a project (irrespective of folder)
    # we can safely ignore the folder altogether (just wildcard it)
    jobname = rest_result['_name']
    if rest_result['type'] == "PARALLEL":
        jobname += ".psc"
    elif rest_result['type'] == "SERVER":
        jobname += ".ssc"
    else:
        jobname += ".*"
    return rest_result['_context'][0]['_name'] + "/" + rest_result['_context'][1]['_name'] + "/*/" + jobname


def _getQualifiedNameForTableDefinition(rest_result):
    qualifiedName = rest_result['_name']
    if rest_result['data_source_name'] != '':
        qualifiedName = rest_result['data_source_name'].replace('/', '\\/') + '\\\\' + qualifiedName
    if rest_result['data_source_type'] != '':
        qualifiedName = rest_result['data_source_type'].replace('/', '\\/') + '\\\\' + qualifiedName
    if qualifiedName not in asset_blacklists['table_definition']:
        return qualifiedName + ".tbd"
    else:
        return ""


def _getDsTableDefinitionExtractObjects(rest_result):
    # https://www.ibm.com/support/knowledgecenter/en/SSZJPZ_11.7.0/com.ibm.swg.im.iis.iisinfsv.assetint.doc/topics/depasset.html
    # Note: because table definitions must be universally unique in naming within a project (irrespective of folder)
    # we can safely ignore the folder altogether (just wildcard it)
    tablename = _getQualifiedNameForTableDefinition(rest_result)
    if tablename != '':
        return rest_result['_context'][0]['_name'] + "/" + rest_result['_context'][1]['_name'] + "/*/" + tablename


def _getDsParameterSetExtractObjects(rest_result):
    # https://www.ibm.com/support/knowledgecenter/en/SSZJPZ_11.7.0/com.ibm.swg.im.iis.iisinfsv.assetint.doc/topics/depasset.html
    # Note: because parameter sets must be universally unique in naming within a project (irrespective of folder) we can
    # safely ignore the folder altogether (just wildcard it)
    ctx = rest_result['_context']
    return ctx[0]['_name'] + "/" + ctx[1]['_name'] + "/*/" + rest_result['_name'] + ".pst"


def _getDataClassExtractObjects(rest_result):
    # Per KC, parent data classes include their sub-data classes,
    # and sub-data classes cannot be exported by themselves
    # TODO: for now we'll assume no more than 2 levels of nesting of
    # data classes
    if (rest_result['parent_data_class.parent_data_class.class_code'] != '' and
            rest_result['parent_data_class.parent_data_class.provider'] != 'IBM'):
        return "/" + rest_result['parent_data_class.parent_data_class.class_code'] + ".dc"
    elif (rest_result['parent_data_class.class_code'] != '' and
          rest_result['parent_data_class.provider'] != 'IBM'):
        return "/" + rest_result['parent_data_class.class_code'] + ".dc"
    elif (rest_result['parent_data_class.class_code'] == '' and
          rest_result['provider'] != 'IBM'):
        return "/" + rest_result['class_code'] + ".dc"


def _getExtensionMappingDocumentExtractObjects(rest_result):
    path = _getContextPath(rest_result)
    file = rest_result['file_name']
    if path.find('/') >= 0:
        path = path[(path.find('/') + 1):]
        file = path + "/" + file
    extract = {
        "name": rest_result['_name'],
        "file": file
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
    # Unfortunately it appears that the project can be a string or an array
    # in different scenarios (though should only ever be a single value?)
    projectName = rest_result['project'][0] if isinstance(rest_result['project'], list) else rest_result['project']
    # data_rule_definition queries may return various sub-types of data rule definitions:
    # published_data_rule_definition, non_published_data_rule_definition, etc
    objtype = rest_result['_type']
    if objtype.endswith('data_rule_definition'):
        objtype = "data_rule_definition"
    elif (objtype == 'inv_data_rule_set' or
          objtype == 'non_published_data_rule_set' or
          objtype == 'published_data_rule_set' or
          objtype == 'inv_data_rule_set_definition'):
        objtype = "data_rule_set_definition"
    extract = {
        "project": projectName,
        "name": rest_result['_name'],
        "type": objtype
    }
    return extract


def _escapeModelName(name):
    return re.sub('/', '_', name)


def _getDataModelExtractObjects(rest_result):
    namespace = rest_result['namespace']
    name = _escapeModelName(rest_result['_name'])
    model_type = rest_result['_type']
    if len(rest_result['_context']) > 0:
        name = _escapeModelName(rest_result['_context'][0]['_name'])
    if model_type == 'physical_data_model':
        model_type = "pm"
    elif model_type == 'logical_data_model':
        model_type = "lm"
    return "/" + namespace + "/" + name + "." + model_type


def _getDatabaseExtractObjects(rest_result):
    obj_type = rest_result['_type']
    if obj_type == 'database':
        obj_type = "db"
    elif obj_type == 'database_schema':
        obj_type = "sch"
    return "/" + _getContextPath(rest_result) + "/" + rest_result['_name'] + "." + obj_type


def _escapeFilePath(name):
    return re.sub('/', '\\/', name)


def _getDataFileExtractObjects(rest_result):
    path = _getContextPath(rest_result)
    host = path
    folder = path
    if path.find('/') > 0:
        host = path[0:path.find('/')]
        folder = path[(path.find('/') + 1):]
        if folder.startswith('//'):
            folder = folder[1:]
    return "/" + host + "/" + _escapeFilePath(folder) + "/" + rest_result['_name'] + ".fl"
