# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import os
import json

from os import listdir
from os.path import isfile, join

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# New assets name:id map
asset_dictionary = {}

# New Properties name:id map
property_dictionary = {}

# Maps of old and new id
asset_id_mapping = {}
property_id_mapping = {}

cfn_base = {
    'AWSTemplateFormatVersion': '2010-09-09',
    'Description': 'SiteWise Dashboards Export',
    'Resources': {}
}

#############################################################################
# backup_dashboards function discover all projects and dashboards under     #
# portal_name in the source account                                         #
#############################################################################


def backup_dashboards(clt, portal_name):
    portals = clt.list_portals()
    for portal in portals['portalSummaries']:
        if portal['name'] == portal_name:
            projects = clt.list_projects(portalId=portal['id'])
            for project in projects['projectSummaries']:
                dashboards = clt.list_dashboards(projectId=project['id'])
                for dashboard in dashboards['dashboardSummaries']:
                    save_dashboard_description(clt, dashboard['id'])


#############################################################################
# save_dashboard_description function creates temporal json files to keep   #
# dashboards basic information needed to re-create them and a metadata file #
# to map objects IDs with names, hash table is used latter to replace       #
# source account IDs with destination account IDs base in objects names     #
#############################################################################


def save_dashboard_description(clt, dashboard_id):
    dashboard = clt.describe_dashboard(dashboardId=dashboard_id)
    metadata = {}
    for widget in json.loads(dashboard['dashboardDefinition'])['widgets']:
        for metric in widget['metrics']:
            item = clt.describe_asset_property(assetId=metric['assetId'], propertyId=metric['propertyId'])
            metadata[item['assetId']] = item['assetName']
            metadata[item['assetProperty']['id']] = item['assetProperty']['name']

    if not os.path.exists('dashboards'):
        os.makedirs('dashboards')
    dashboard.pop('dashboardCreationDate')
    dashboard.pop('dashboardLastUpdateDate')
    dash = json.dumps(dashboard)
    f = open("dashboards/{}.json".format(dashboard['dashboardName']), "w")
    f.write(dash)
    f.close()

    if not os.path.exists('metadata'):
        os.makedirs('metadata')
    dash_meta = json.dumps(metadata)
    f = open("metadata/{}.json".format(dashboard['dashboardName']), "w")
    f.write(dash_meta)
    f.close()


#############################################################################
# generate_asset_property_dictionary function generate 2 maps to look-up,   #
# between Names and IDs in the destination account                          #
#############################################################################


def generate_asset_property_dictionary(clt, model_id):
    model = clt.describe_asset_model(assetModelId=model_id)

    if len(model['assetModelHierarchies']) > 0:
        for child in model['assetModelHierarchies']:
            generate_asset_property_dictionary(clt, child['childAssetModelId'])
    assets = clt.list_assets(assetModelId=model_id, filter='ALL')['assetSummaries']
    for asset in assets:
        asset_dictionary[asset['name']] = asset['id']
        properties = clt.describe_asset(assetId=asset['id'])['assetProperties']
        for asset_property in properties:
            property_dictionary[asset['name']+'+'+asset_property['name']] = asset_property['id']


###################################################################################
# map_ids function generate 2 maps to look-up base in old assets and property ids #
# the new ids in the new environment based in assets and property names.          #
###################################################################################


def map_ids():
    files = [f for f in listdir('dashboards') if isfile(join('dashboards', f))]

    for file in files:
        with open('dashboards/{}'.format(file)) as dashboard_file:
            dashboard = json.load(dashboard_file)
            with open('metadata/{}'.format(file)) as metadata_file:
                dashboard_metadata = json.load(metadata_file)
                for widget in json.loads(dashboard['dashboardDefinition'])['widgets']:
                    for metric in widget['metrics']:
                        asset_id_mapping[metric['assetId']] = asset_dictionary[dashboard_metadata[metric['assetId']]]
                        property_id_mapping[metric['propertyId']] = \
                            property_dictionary[dashboard_metadata[metric['assetId']]
                                                + '+'
                                                + dashboard_metadata[metric['propertyId']]]


###################################################################################
# create_cfn function find destination project ID to use in the CFN and triggers  #
# file creation.                                                                  #
###################################################################################


def create_cfn(clt, portal_name, project_name):
    portals = clt.list_portals()['portalSummaries']
    for portal in portals:
        if portal['name'] == portal_name:
            projects = clt.list_projects(portalId=portal['id'])
            for project in projects['projectSummaries']:
                if project['name'] == project_name:
                    create_file(project['id'])


###################################################################################
# create_file function uses the temporal files created based in source account    #
# dashboards information and, using the maps, replace sources IDs with            #
# destination IDs before create the CFN template                                  #
###################################################################################


def create_file(project_id):
    cfn = cfn_base.copy()
    files = [f for f in listdir('dashboards') if isfile(join('dashboards', f))]

    for file in files:
        with open('dashboards/{}'.format(file)) as dashboard_file:
            dashboard = json.load(dashboard_file)
            dashboard.pop('ResponseMetadata')
            dashboard.pop('dashboardId')
            dashboard.pop('dashboardArn')

            dashboard['projectId'] = project_id
            dashboard_definition = json.loads(dashboard['dashboardDefinition'])
            new_widgets = []
            for widget in dashboard_definition['widgets']:
                for i in range(len(widget['metrics'])):
                    widget['metrics'][i]['assetId'] = asset_id_mapping[widget['metrics'][i]['assetId']]
                    widget['metrics'][i]['propertyId'] = property_id_mapping[widget['metrics'][i]['propertyId']]
                new_widgets.append(widget)
            dashboard_definition['widgets'] = new_widgets
            dashboard['dashboardDefinition'] = json.dumps(dashboard_definition)

            new_dashboard = {
                f'Dashboard{dashboard["dashboardName"].replace(" ", "")}': {
                    "Type": "AWS::IoTSiteWise::Dashboard",
                    "Properties": {
                        "DashboardDefinition": json.dumps(dashboard_definition),
                        "DashboardDescription": dashboard['dashboardDescription'],
                        "DashboardName": dashboard['dashboardName'],
                        "ProjectId": dashboard['projectId']
                    }
                }
            }

            cfn['Resources'].update(new_dashboard)

    if not os.path.exists('cfnexport'):
        os.makedirs('cfnexport')

    f = open("cfnexport/dashboards_cfn.json".format(dashboard['dashboardName']), "w")
    f.write(json.dumps(cfn))
    f.close()


def lambda_handler(event, context):
    # connect to source environment
    # boto3.setup_default_session(profile_name=context['source_environment'])
    source_client = boto3.client('iotsitewise',
                                 aws_access_key_id=context['SOURCE_AWS_SERVER_PUBLIC_KEY'],
                                 aws_secret_access_key=context['SOURCE_AWS_SERVER_SECRET_KEY'],
                                 region_name=context['SOURCE_REGION_NAME'])

    backup_dashboards(source_client, context['SOURCE_PORTAL'])

    # switch context to destination environment
    # boto3.setup_default_session(profile_name=context['destination_environment'])
    destination_client = boto3.client('iotsitewise',
                                      aws_access_key_id=context['DESTINATION_AWS_SERVER_PUBLIC_KEY'],
                                      aws_secret_access_key=context['DESTINATION_AWS_SERVER_SECRET_KEY'],
                                      region_name=context['DESTINATION_REGION_NAME'])

    generate_asset_property_dictionary(destination_client, context['DESTINATION_ROOT_MODEL_ID'])
    map_ids()
    create_cfn(destination_client, context['DESTINATION_PORTAL_NAME'], context['DESTINATION_PROJECT_NAME'])


# For local testing
# lambda_handler({}, {'SOURCE_AWS_SERVER_PUBLIC_KEY': '...',
#                     'SOURCE_AWS_SERVER_SECRET_KEY': '...',
#                     'SOURCE_REGION_NAME': '...',
#                     'SOURCE_PORTAL': '...',
#                     'DESTINATION_AWS_SERVER_PUBLIC_KEY': '...',
#                     'DESTINATION_AWS_SERVER_SECRET_KEY': '...',
#                     'DESTINATION_REGION_NAME': '...',
#                     'DESTINATION_ROOT_MODEL_ID': '...',
#                     'DESTINATION_PORTAL_NAME': '...',
#                     'DESTINATION_PROJECT_NAME': '...'})
