#!/usr/bin/python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import asset_model_shapes
import boto3
import pprint
import json
import re
import uuid
import argparse
from botocore.config import Config

pp = pprint.PrettyPrinter(compact=True)
parser = argparse.ArgumentParser(description='Asset Model Export Tool for SiteWise.')
parser.add_argument('--profile', action='store', help='Credentials profile for the AWS account')
parser.add_argument('--region', action='store', help='Specify the AWS region you would like to target')
args = parser.parse_args()

#Setup the AWS SiteWise boto3 client
if args.profile:
    boto3.setup_default_session(profile_name=args.profile)
if args.region:
    my_config = Config(region_name=args.region)
else:
    my_config = Config()
client = boto3.client('iotsitewise', config=my_config)

#hierarchy lookup table to use later
hierarchy_id_lookup = {}
#property and hierarchy lookup tables to deal with cross ref logical ids in the second pass.
property_logical_id_lookup = {}
hierarchy_logical_id_lookup = {}

#Create the base CFN dictionary that we will add to and then dump out as JSON
cfn_base ={
    'AWSTemplateFormatVersion' : '2010-09-09',
    'Description' : 'SiteWise Export',
    'Resources' : {}
}

#Recursive function to do a first pass walk of the dictionary response from the describe call.
#Function needs:
# - an object to recurse over
# - a case_handler function
# = a shape_filter dictionary to filter the describe response to match the CFN shape
def walk_dict_filter(dictionary, case_handler, shape_filter):
    if isinstance(dictionary, dict):
        return {k[0].upper() + k[1:]: walk_dict_filter(case_handler(k,v), case_handler, shape_filter) for k, v in dictionary.items() if k[0].upper() + k[1:] in shape_filter}
    elif isinstance(dictionary, list):
        return [walk_dict_filter(item, case_handler, shape_filter) for item in dictionary]
    else:
        return dictionary

#Recursive function to do a second pass walk of the CFN shape created in the first pass. This is to replace IDs with LogicalIDs
def walk_dict(dictionary, case_handler, **kwargs):
    if isinstance(dictionary, dict):
        return {k: walk_dict(case_handler(k,v, **kwargs), case_handler, **kwargs) for k, v in dictionary.items()}
    elif isinstance(dictionary, list):
        return [walk_dict(item, case_handler, **kwargs) for item in dictionary]
    else:
        return dictionary

#Function to handle special cases on the first pass where the api response does not match the CFN shape
def case_handler_1st_pass(k,v):
    if k == 'type' and isinstance(v, dict):
        if 'measurement' in v:
            return {'TypeName': 'Measurement'}
        if 'transform' in v:
            return {'TypeName': 'Transform', 'Transform':v['transform']}
        if 'attribute' in v:
            return {'TypeName': 'Attribute', 'Attribute':v['attribute']}
        if 'metric' in v:
            return {'TypeName': 'Metric', 'Metric':v['metric']}
    if k == 'value' and isinstance(v, dict):
        if 'hierarchyId' in v and 'propertyId' in v:
            #Return the new dictionary structure with original IDs...we will replace these in the second pass
            return {'PropertyLogicalId':v['propertyId'], 'HierarchyLogicalId':v['hierarchyId']}  
        if 'propertyId' in v:
            #Same as above but only when we find propertyId
            return {'PropertyLogicalId':v['propertyId']}

    if k == 'assetModelProperties' and isinstance(v, list):     
          tmp = []
          for d in v:
            logical_id = re.sub(r'[^A-Za-z0-9]+', '', d['name']).lower()
            logical_id_with_hash = logical_id+uuid.uuid4().hex[:8]
            tmp.append({**d,**{'LogicalId':logical_id_with_hash}})
            #update the property lookup table with the id so we can use it during our second pass
            property_logical_id_lookup.update({d['id']:logical_id_with_hash})
          return tmp
        
    if k == 'assetModelHierarchies' and isinstance(v, list):
          tmp = []
          for d in v:
            #Create our LogicalIds for Hierarchies and then populate a lookup table that we will use in the second pass.   
            d['childAssetModelId'] = {'Ref': hierarchy_id_lookup[d['childAssetModelId']]}
            logical_id = re.sub(r'[^A-Za-z0-9]+', '', d['name']).lower()
            tmp.append({**d,**{'LogicalId':logical_id}})
            #update the hierarchy logical id lookup table with the logical_id
            hierarchy_logical_id_lookup.update({d['id']:logical_id})
          return tmp          
    else:
        return v

#Function to handle special cases on the second pass, specifically cross referenced PropertyLogicalId and HierarchyLogicalId
def case_handler_2nd_pass(k,v):
    #Find the HierarchyLogicalId and PropertyLogicalId keys inside Value dictionary. We need to use our lookup tables we populated in the first pass to replace IDs with logical IDs. 
    if k == 'Value' and isinstance(v, dict):
          if 'HierarchyLogicalId' in v and 'PropertyLogicalId' in v:
              return {'PropertyLogicalId':property_logical_id_lookup[v['PropertyLogicalId']], 'HierarchyLogicalId':hierarchy_logical_id_lookup[v['HierarchyLogicalId']]}  
          if 'PropertyLogicalId' in v:
              return {'PropertyLogicalId':property_logical_id_lookup[v['PropertyLogicalId']]}
          else:
                return v
    else:
          return v

def get_models():
    model_list = []
    #list all the asset models
    response = client.list_asset_models()
    for id in response['assetModelSummaries']:
        asset_model_name = id['name']
        asset_model_name = asset_model_name.replace(" ","")
        asset_model_id = id['id']

        #update the hierarchy_id_lookup table (this is a side effect that should be cleaned up)
        global hierarchy_id_lookup
        hierarchy_id_lookup.update({asset_model_id:asset_model_name})

        #describe the asset model
        asset_model_response = client.describe_asset_model(assetModelId=id['id'])
        model_list.append(asset_model_response)
    return model_list 

if __name__ == '__main__':
    for model_detail in get_models():    
        #base cfn model shape dictionary we will be building out.
        asset_model_base_cfn = {
            'Type' : 'AWS::IoTSiteWise::AssetModel',
            'Properties' : {}
        }
        
        #this is a repeat of the hierarchy lookup table need to streamline
        asset_model_name = model_detail['assetModelName']
        asset_model_name = asset_model_name.replace(" ","")

        #Recurse over the describe response and filter/transform the response to match the CFN shape
        asset_model_base_cfn['Properties'] = walk_dict_filter(
            model_detail,
            case_handler_1st_pass,
            {
                **asset_model_shapes.AssetModel['Properties'], 
                **asset_model_shapes.AssetModelProperty,
                **asset_model_shapes.AssetModelCompositeModel, 
                **asset_model_shapes.PropertyType,
                **asset_model_shapes.Transform,
                **asset_model_shapes.ExpressionVariable,
                **asset_model_shapes.VariableValue,
                **asset_model_shapes.Metric,
                **asset_model_shapes.MetricWindow,
                **asset_model_shapes.TumblingWindow,
                **asset_model_shapes.Attribute,
                **asset_model_shapes.AssetModelHierarchy,
                **asset_model_shapes.AssetModelCompositeModel,
                **asset_model_shapes.Tag,
                **asset_model_shapes.Ref
                } 
            )

        cfn_base['Resources'].update({asset_model_name : asset_model_base_cfn})

    #Create the valid cloudformation
    #First run a second pass over the CFN structure to update cross referenced Logical IDs
    cfn_base = walk_dict(cfn_base, case_handler_2nd_pass)

    #print the json just output a template file: python3 AssetModelExporter.py > mytemplate.template
    print(json.dumps(cfn_base, indent=1))