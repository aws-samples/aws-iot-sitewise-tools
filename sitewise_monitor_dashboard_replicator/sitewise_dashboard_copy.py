#!/usr/bin/python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import boto3
import argparse
from botocore.config import Config

parser = argparse.ArgumentParser(description='SiteWise Dashboard Copy Tool')
parser.add_argument('--profile', action='store', help='Credentials profile for the AWS account')
parser.add_argument('--region', action='store', help='Specify the AWS region you would like to target')
subparsers = parser.add_subparsers(dest='cmd')

parser_dash_list = subparsers.add_parser('list_dashboards', help='Command to list dashboards in the region avaliable to copy')
parser_proj_list = subparsers.add_parser('list_projects',  help='Command to list the projects avaliable to copy a dashboard to')
parser_dash_copy = subparsers.add_parser('copy_dashboard', help='Command to copy dashboard to specified project')
parser_dash_copy.add_argument('--dashboard_id', type=str, required=True, help='Enter the source Dashboard ID you want to copy')
parser_dash_copy.add_argument('--project_id', type=str, help='Enter the target Project ID you want to copy the dashboard to')
parser_dash_copy.add_argument('--print_definition', action='store_true', help='if you only want the dashboard JSON definition instead of copying')

args = parser.parse_args()

#Setup the AWS SiteWise boto3 client
if args.profile:
    boto3.setup_default_session(profile_name=args.profile)
if args.region:
    my_config = Config(region_name=args.region)
else:
    my_config = Config()
client = boto3.client('iotsitewise', config=my_config)

def list_portals():
    portals = []
    portals_paginator = client.get_paginator("list_portals")
    pages = portals_paginator.paginate()
    for page in pages:
        if page['portalSummaries']:
            for portal in page['portalSummaries']:
                portals.append({'id': portal['id'], 'name': portal['name']})
    return portals

def list_projects(portal_id):
    projects = []
    projects_paginator = client.get_paginator("list_projects")
    pages = projects_paginator.paginate(portalId=portal_id)
    for page in pages:
        if page['projectSummaries']:
            for project in page['projectSummaries']:
                # if project['name'] == '{templates}':
                projects.append({'name':project['name'], "id": project['id']})
    return projects

def list_dashboards(project_id):
    dashboards = []
    dashboard_paginator = client.get_paginator("list_dashboards")
    pages = dashboard_paginator.paginate(projectId=project_id)
    for page in pages:
        if page['dashboardSummaries']:
            for dashboard in page['dashboardSummaries']:
                dashboards.append({'name':dashboard['name'], "id": dashboard['id'], 'project_id': project_id})
    return dashboards


if __name__ == '__main__':
    if args.cmd == 'list_dashboards' or args.cmd == 'list_projects':
        for portal in list_portals():
            for project in list_projects(portal['id']):
                if args.cmd == 'list_projects':
                    print(project)
                    break
                for dashboard in list_dashboards(project['id']):
                    print(dashboard)

    if args.cmd == 'copy_dashboard':
        dash_id = args.dashboard_id
        proj_id = args.project_id
        dash_details = client.describe_dashboard(dashboardId=dash_id)
        dashboard_name = dash_details['dashboardName']
        dashboard_description = dash_details['dashboardDescription']
        dashboard_definition = dash_details['dashboardDefinition']
        if args.print_definition:
            print(dashboard_definition)
        else:
            response = client.create_dashboard(
                    projectId=proj_id,
                    dashboardName=dashboard_name,
                    dashboardDescription=dashboard_description,
                    dashboardDefinition=dashboard_definition,
                )
            print(response)