# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0`
import logging

import boto3

from shapes import asset_shapes, common_shapes
from utils import cfn_string, walk_dict_filter, assert_sitewise_response

# Lookup tables copied over from model extraction module
lookup_model_id, lookup_model_property = {}, {}

asset_base_cfn = {
    'Type': 'AWS::IoTSiteWise::Asset',
    'Properties': {}
}

logger = logging.getLogger()


def get_top_level_assets(client) -> list:
    """
    Queries SiteWise to retrieve the top-level assets
    """
    resp = client.list_assets(filter='TOP_LEVEL')
    assert_sitewise_response(resp, 'list_assets')
    return resp['assetSummaries']


def handle_asset_fields(k, v, **kwargs):
    """
    Applies a transformation over the field name (k) & values (v) in order to map the values to CFN expected format.
    """
    if k == 'assetModelId':
        # return a CFN reference to the model:
        return {'Ref': lookup_model_id[v]}

    if k == 'assetProperties' and isinstance(v, list):
        tmp = []
        for property in sorted(v, key=lambda prop: prop['name']):
            propertyDoc = {
                'LogicalId': lookup_model_property[lookup_model_id[kwargs['parent']['assetModelId']]][property['id']]
            }
            if property['notification']['state'] == 'ENABLED':
                propertyDoc.update({'NotificationState': 'ENABLED'})
            if 'alias' in property:
                propertyDoc.update({'Alias': property['alias']})
            tmp.append(propertyDoc)
        return tmp

    if k == 'tags' and isinstance(v, dict) and len(v):
        return [{'Key': tag[0], 'Value': tag[1]} for tag in v.items()]

    if k == 'assetHierarchies' and isinstance(v, list):
        tmp = []  # assetHierarchies
        for hierarchy in v:
            for child in sorted(hierarchy['children'], key=lambda h: h['name']):
                tmp.append({
                    'ChildAssetId': {'Ref': cfn_string(child['name'])},
                    'LogicalId': cfn_string(hierarchy['name'])
                })
        return tmp
    else:
        return v


def discover_assets(assets: list, client):
    """
    Makes IoT SiteWise API calls to extract asset definitions, tags and sub-assets (recursively), starting from the
    assets ids in provided list.
    :param ids: list of SiteWise Asset Ids
    :param client:
    :return:
    """
    ret = []

    for selected_asset_id in assets:
        try:
            asset = client.describe_asset(assetId=selected_asset_id)
        except Exception as e:
            logger.error(f'Failed to find assetId={selected_asset_id}: {e}')
            continue

        assert_sitewise_response(asset, 'describe_asset')
        asset.pop('ResponseMetadata')
        ret.append(asset)

        logger.info(f'Discovered asset "{asset["assetName"]}"')

        # add tags
        tags = client.list_tags_for_resource(resourceArn=asset['assetArn'])
        assert_sitewise_response(tags, 'list_tags_for_resource')
        if len(tags['tags']):
            tags.pop('ResponseMetadata')
            asset.update({**tags})

        # add children
        for idx, asset_hierarchy in enumerate(asset['assetHierarchies']):
            association = client.list_associated_assets(assetId=asset['assetId'], hierarchyId=asset_hierarchy['id'],
                                                        traversalDirection='CHILD')
            assert_sitewise_response(association, 'list_associated_assets')

            asset_hierarchy['children'] = sorted(association['assetSummaries'], key=lambda child: child['name'])
            ret.extend(discover_assets([child['id'] for child in asset_hierarchy['children']], client))

    return ret


def extract_assets(asset_ids: list, model_ids, model_properties, client=boto3.client('iotsitewise')) -> dict:
    """
    Extract all the SiteWise Asset definitions as CloudFormation resources
    :param asset_ids: list of asset ids from which to recursively extract asset definitions
    :param model_ids: reference to the lookup table of model id-to-name
    :param model_properties: reference to the lookup table of model-to-properties
    :param client: Boto3 IoTSiteWise client
    :return:
    """
    global lookup_model_id, lookup_model_property

    lookup_model_id, lookup_model_property = model_ids, model_properties
    cfn_resources = {}

    logger.debug('Scanning SiteWise Assets ...')
    list_of_assets = discover_assets(asset_ids, client)

    while list_of_assets:
        asset = list_of_assets.pop(0)

        asset_cfn = asset_base_cfn.copy()
        asset_name = cfn_string(asset['assetName'])

        asset_cfn['Properties'] = walk_dict_filter(
            asset,
            handle_asset_fields,
            shape_filter={
                **asset_shapes.Asset['Properties'],
                **asset_shapes.AssetHierarchy,
                **asset_shapes.AssetProperty,
                **common_shapes.Tag,
                **common_shapes.Ref
            },
            parent=None
        )
        cfn_resources.update({asset_name: asset_cfn})

    return cfn_resources
