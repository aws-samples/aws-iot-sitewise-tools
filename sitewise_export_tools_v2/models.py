# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import logging

from shapes import model_shapes, common_shapes
from utils import cfn_string, walk_dict_filter, randomize, assert_sitewise_response

client = None

# lookup_model_id: model id to model name mapping
lookup_model_id = {}
# lookup_property_logical_id: property id to logical id mapping
lookup_property_logical_id = {}
# lookup_hierarchy_logical_id: hierarchy id to logical id mapping
lookup_hierarchy_logical_id = {}
# lookup_model_property: model and property id to logical id mapping
lookup_model_property = {}

model_base_cfn = {
    'Type': 'AWS::IoTSiteWise::AssetModel',
    'Properties': {}
}

logger = logging.getLogger()


def handle_model_fields(k, v, **kwargs):
    """
    Maps the SiteWise output definition of a model to CloudFormation model definitions.
    """
    if k == 'type' and isinstance(v, dict):
        if 'measurement' in v:
            return {'TypeName': 'Measurement'}
        if 'transform' in v:
            return {'TypeName': 'Transform', 'Transform': v['transform']}
        if 'attribute' in v:
            return {'TypeName': 'Attribute', 'Attribute': v['attribute']}
        if 'metric' in v:
            return {'TypeName': 'Metric', 'Metric': v['metric']}
    if k == 'value' and isinstance(v, dict):
        if 'hierarchyId' in v and 'propertyId' in v:
            """
            AWS::IoTSiteWise::AssetModel VariableValue (ExpressionVariable): 
            {
              "HierarchyLogicalId" : String,
              "PropertyLogicalId" : String
            }
            """
            return {'PropertyLogicalId': v['propertyId'], 'HierarchyLogicalId': v['hierarchyId']}
        if 'propertyId' in v:
            return {'PropertyLogicalId': v['propertyId']}
    if k == 'tags' and isinstance(v, dict):
        return [{'Key': tag[0], 'Value': tag[1]} for tag in v.items()]
    if k == 'assetModelProperties' and isinstance(v, list):
        tmp = []
        for d in sorted(v, key=lambda p: p['name']):
            property_logical_id = randomize(d['name'])
            tmp.append({**d, **{'LogicalId': property_logical_id}})

            # update the property lookup table with the id so we can use it during our second pass
            lookup_property_logical_id.update({d['id']: property_logical_id})

            # update model_property_lookup for the current model with the new id to property_logical_id mapping
            current_model = kwargs['current_model']
            if current_model not in lookup_model_property:
                lookup_model_property[current_model] = {}
            lookup_model_property[current_model][d['id']] = property_logical_id
        return tmp
    if k == 'assetModelHierarchies' and isinstance(v, list):
        tmp = []
        for d in sorted(v, key=lambda p: p['name']):
            d['childAssetModelId'] = {'Ref': lookup_model_id[d['childAssetModelId']]}
            hierarchy_logical_id = cfn_string(d['name'])
            tmp.append({**d, **{'LogicalId': hierarchy_logical_id}})
            # update lookup table with the original hierarchy-id to hierarchy-logical-id mapping
            lookup_hierarchy_logical_id.update({d['id']: hierarchy_logical_id})
        return tmp

    return v


def update_logical_ids(k, v, **kwargs):
    """
    Update the structure with logical id's of the properties and hierarchies
    """
    if k == 'Value' and isinstance(v, dict):
        if 'HierarchyLogicalId' in v and 'PropertyLogicalId' in v:
            return {'PropertyLogicalId': lookup_property_logical_id[v['PropertyLogicalId']],
                    'HierarchyLogicalId': lookup_hierarchy_logical_id[v['HierarchyLogicalId']]}
        if 'PropertyLogicalId' in v:
            return {'PropertyLogicalId': lookup_property_logical_id[v['PropertyLogicalId']]}
        else:
            return v
    else:
        return v


def list_asset_models_from_sitewise(sitewise, next_token=None):
    """
    Wrapper over list_asset_models that uses the previously returned token (if any)
    """
    if next_token is None:
        asset_model_lists_summary = sitewise.list_asset_models(maxResults=250)
    else:
        asset_model_lists_summary = sitewise.list_asset_models(nextToken=next_token, maxResults=250)

    assert_sitewise_response(asset_model_lists_summary, 'list_asset_models')
    return asset_model_lists_summary


def find_all_models(sitewise):
    """
    Generator that paginates over all SiteWise models
    """
    token = None
    first_execution = True
    while first_execution or token is not None:
        first_execution = False
        asset_model_list_result = list_asset_models_from_sitewise(sitewise, next_token=token)
        token = asset_model_list_result.get("nextToken")
        for asset_model in asset_model_list_result["assetModelSummaries"]:
            yield asset_model


def get_models(client):
    """
    Queries IoT SiteWise service to retrieve the model definitions
    :param client:
    :return: model definitions
    """
    model_list = []

    # list all the asset models
    for model in find_all_models(client):
        asset_model_name = cfn_string(model['name'])
        logger.info(f'Discovered model "{model["name"]}"')

        # update the hierarchy_id_lookup table (this is a side effect that should be cleaned up)
        global lookup_model_id
        lookup_model_id.update({model['id']: asset_model_name + 'Resource'})

        # describe the asset model
        model_def = client.describe_asset_model(assetModelId=model['id'])
        assert_sitewise_response(model_def, 'describe_asset_model')
        model_def.pop('ResponseMetadata')

        # add tags
        tags = client.list_tags_for_resource(resourceArn=model['arn'])
        assert_sitewise_response(tags, 'list_tags_for_resource')
        tags.pop('ResponseMetadata')
        if len(tags['tags']):
            model_def.update({**tags})

        model_list.append(model_def)
    return model_list


def extract_models(client):
    """
    Queries IoT SiteWise for Asset Models and parses the response to generate a valid CloudFormat Resources
    :param client: Boto3 IotSIteWise client
    :return: list of models, lookup_model_id, lookup_model_property
    """
    model_resources = {}

    logger.debug('Scanning SiteWise models ...')
    models = get_models(client)

    for model in models:
        current_model = cfn_string(model['assetModelName']) + 'Resource'

        # base cfn model shape dictionary we will be building out.
        model_cfn = model_base_cfn.copy()

        # Recurse over the describe response and filter/transform the response to match the CFN shape
        model_cfn['Properties'] = walk_dict_filter(
            model,
            handle_model_fields,
            shape_filter={
                **model_shapes.AssetModel['Properties'],
                **model_shapes.AssetModelProperty,
                **model_shapes.AssetModelCompositeModel,
                **model_shapes.PropertyType,
                **model_shapes.Transform,
                **model_shapes.ExpressionVariable,
                **model_shapes.VariableValue,
                **model_shapes.Metric,
                **model_shapes.MetricWindow,
                **model_shapes.TumblingWindow,
                **model_shapes.Attribute,
                **model_shapes.AssetModelHierarchy,
                **model_shapes.AssetModelCompositeModel,
                **common_shapes.Tag,
                **common_shapes.Ref
            },
            current_model=current_model
        )
        model_resources.update({current_model: model_cfn})

    # Run a second pass over the CFN structure to update the property and hierarchy id's
    model_resources = walk_dict_filter(model_resources, update_logical_ids)

    return model_resources, lookup_model_id, lookup_model_property
