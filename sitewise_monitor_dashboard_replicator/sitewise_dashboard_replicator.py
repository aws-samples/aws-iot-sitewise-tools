#!/usr/bin/python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import json
import re
import argparse
from botocore.config import Config

parser = argparse.ArgumentParser(description='SiteWise Dashboard Replicator')

parser.add_argument('--profile', action='store', help='Credentials profile for the AWS account')
parser.add_argument('--region', action='store', help='Specify the AWS region you would like to target')
source_group = parser.add_mutually_exclusive_group(required=True)
source_group.add_argument('--all',action='store_true', help='Replicate all dashboards with source tag')
source_group.add_argument('--dashboard_id',action='store', help='Replicate individual dashboard by ID')
parser.add_argument('--source_tag', action='store', help='provide a custom source dashboard tag')
args = parser.parse_args()

#Setup the AWS SiteWise boto3 client
if args.profile:
    boto3.setup_default_session(profile_name=args.profile)
if args.region:
    my_config = Config(region_name=args.region)
else:
    my_config = Config()
client = boto3.client('iotsitewise', config=my_config)

#Setup the source dashbard name identifier tag 
if args.source_tag:
    source_tag = args.source_tag
else:
    source_tag = "{source}"

def list_portals():
    portals = []
    portals_paginator = client.get_paginator("list_portals")
    pages = portals_paginator.paginate()
    for page in pages:
        if page['portalSummaries']:
            for project in page['portalSummaries']:
                portals.append(project['id'])
    return portals

def list_projects(portal_id):
    projects = []
    projects_paginator = client.get_paginator("list_projects")
    pages = projects_paginator.paginate(portalId=portal_id)
    for page in pages:
        if page['projectSummaries']:
            for project in page['projectSummaries']:
                # if project['name'] == '{templates}':
                projects.append({"id": project['id'], 'name':project['name']})
    return projects

def list_dashboards(project_id):
    dashboards = []
    dashboard_paginator = client.get_paginator("list_dashboards")
    pages = dashboard_paginator.paginate(projectId=project_id)
    for page in pages:
        if page['dashboardSummaries']:
            for dashboard in page['dashboardSummaries']:
                dashboards.append({"id": dashboard['id'], 'name':dashboard['name']})
    return dashboards

def list_assets(assetModelId):
    asset_list = []
    asset_paginator = client.get_paginator("list_assets")
    pages = asset_paginator.paginate(assetModelId=assetModelId)
    for page in pages:
        for asset in page['assetSummaries']:
            asset_list.append(asset)
    return asset_list

def walk_dict(dictionary, case_handler, **kwargs):
    if isinstance(dictionary, dict):
        return {k: walk_dict(case_handler(k,v, **kwargs), case_handler, **kwargs) for k, v in dictionary.items()}
    elif isinstance(dictionary, list):
        return [walk_dict(item, case_handler, **kwargs) for item in dictionary]
    else:
        return dictionary

def update_definition(definition, asset_id, label_name):
    def update_definition_case_handler(k,v):
        if k == 'metrics' and isinstance(v, list):
            for metric in v:
                metric['assetId'] = asset_id
                metric['label'] = re.sub(r'\(.*\)', '({})'.format(label_name), metric['label'])
            return v
        else:
            return v
    return walk_dict(definition, update_definition_case_handler)

def source_asset_id_check(definition):
    temp_set = set()
    def asset_id_check_case_handler(k,v):
        if k == 'assetId':
            temp_set.add(v)
            return v
        else:
            return v
    walk_dict(definition, asset_id_check_case_handler)

    if len(temp_set) != 1:
        raise ValueError('Dashboard contains properties from more than one asset')
    return (next(iter(temp_set)))        

def get_source_dashboard(dashboard_id):
    dashboards_dict = {'source_dashboard':{}, 'update':{}}
    dash_details = client.describe_dashboard(dashboardId=dashboard_id)
    definition = json.loads(dash_details['dashboardDefinition'])
    name = dash_details['dashboardName']
    arn = dash_details['dashboardArn']
    if source_tag in name:
        print('Found Source Dashboard:')
        print('- Name:'+name)
        print('- ID: '+dashboard_id)
        source_asset_id = source_asset_id_check(definition)
        source_asset_details = client.describe_asset(assetId=source_asset_id)
        source_asset_model_id = source_asset_details['assetModelId']
        source_asset_siblings = list_assets(assetModelId=source_asset_model_id)
        if 'dashboardDescription' in dash_details:
            description = dash_details['dashboardDescription']
        else:
            description = name
        dash = {
            'definition':definition, 
            'name':name, 
            'description':description, 
            'arn':arn,
            'project_id':dash_details['projectId'], 
            'source_asset_id':source_asset_id,
            'source_asset_model_id':source_asset_model_id,
            'source_asset_siblings':source_asset_siblings
            }
        dashboards_dict['source_dashboard'].update(dash)
    else:
        raise ValueError('Dashboard not tagged as '+source_tag)
    
    #build a list of dashboards to update rather than create
    check_update = list_dashboards(dash_details['projectId'])
    for dashboard in check_update:
        dash_details = client.describe_dashboard(dashboardId=dashboard['id'])
        tags_response = client.list_tags_for_resource(
            resourceArn=dash_details['dashboardArn']
        )
        if 'assetId' in tags_response['tags']:
            dashboards_dict['update'].update({tags_response['tags']['assetId']:dash_details['dashboardId']})
    return dashboards_dict   



def dashboard_sync(dashboard):
        for asset_sibling in dashboard['source_dashboard']['source_asset_siblings']:
            name_merge = dashboard['source_dashboard']['name']
            name_merge = name_merge.replace(source_tag, asset_sibling['name'])
            dash_new = {
                'definition':update_definition(dashboard['source_dashboard']['definition'], asset_sibling['id'], asset_sibling['name']), 
                'name':asset_sibling['name'], 
                'description':dashboard['source_dashboard']['description'],
                'asset_id':asset_sibling['id']
            }

            #Check if the asset_id is in the dashboard update list. 
            #If it is update the dashboard rather than create a new one.
            if dash_new['asset_id'] in dashboard['update']:
                response = client.update_dashboard(
                    dashboardId=dashboard['update'][dash_new['asset_id']],
                    dashboardName=name_merge,
                    dashboardDescription=dash_new['description'],
                    dashboardDefinition=json.dumps(dash_new['definition'])
                )
                print('Dashboard update success:')
                print('- Name: '+name_merge)

            #Create a new dashboard for the asset_id if it isn't in the update list.
            else:
                create_dashboard_response = client.create_dashboard(
                    projectId=dashboard['source_dashboard']['project_id'],
                    dashboardName=name_merge,
                    dashboardDescription=dash_new['description'],
                    dashboardDefinition=json.dumps(dash_new['definition']),
                    tags={
                        'assetId': dash_new['asset_id']
                    }
                )
                print('Dashboard create success:')
                print('- Name: '+name_merge)

if __name__ == '__main__':
    if args.all:
        for portal in list_portals():
            for project in list_projects(portal):
                for dashboard in list_dashboards(project['id']):
                    if source_tag in dashboard['name']:
                        source = get_source_dashboard(dashboard['id'])
                        dashboard_sync(source)

    if args.dashboard_id:
        source = get_source_dashboard(args.dashboard_id)
        dashboard_sync(source)