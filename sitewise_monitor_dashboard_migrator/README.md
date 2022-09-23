# SiteWise Dashboards Migration Tool

This tool is used to migrate AWS SiteWise Monitor Dashboards from a source AWS Account into a destination AWS Account.

This is useful for customers following (or looking to follow) DevOps and CI/CD practices in their IoT projects where automation is job zero and dashboards have to be promoted between dev, test and production environments.

# Problem Addressed

AWS SiteWise Monitor Dashboards, as many other dashboarding tools, rely on datasource objects ids.
In AWS SiteWise these are Assets and Properties ids.
This means that, while you can backup dashboards using AWS SiteWise APIs, the backed up dashboard will not work in a different AWS Account or Region within the same AWS Account, because the SiteWise Assets and corresponding Property ids will be different.

This makes SiteWise Monitor dashboard development, automation, and portability between environments(dev, testing, prod, etc) difficult. 

# Pre-requisites

1. Assets and Properties names in source and destination environment have to be identical. This usually shouldn't be a problem for customers following DevOps and CI/CD practices where environment deployments and infrastructure operations is automated but worth calling out if you plan on prefixing names with a unique identifier.  
2. A SiteWise Portal and a project with the previously mentioned asset (at least those used in the dashboards) assigned to the project. Please see the `sitewise_export_tools` folder in this repository for scripts to export/import Models and Assets to other accounts and/or regions.  
3. Credentials with permissions to call AWS SiteWise APIs in both source and destination accounts  are needed.

# Use

This script is developed as an AWS Lambda function. For simplicity, we set source and destination credentials as Lambda environmental variables.
---
If you are planning to use this script for something else other than testing, please store your keys in AWS Secret Manager.
https://docs.aws.amazon.com/code-samples/latest/catalog/python-secretsmanager-secretsmanager_basics.py.html
---

To use this script you have to provided following parameters:

`SOURCE_AWS_SERVER_PUBLIC_KEY: key required to connect with the account where the dashboards to be exported exists`

`SOURCE_AWS_SERVER_SECRET_KEY: secret required to connect with the account where the dashboards to be exported exists`

`SOURCE_REGION_NAME: region where the dashboards to be exported exists`

`SOURCE_PORTAL: SiteWise portal name where the dashboards exists`

`DESTINATION_AWS_SERVER_PUBLIC_KEY: key required to connect with the account where the dashboards will be created`

`DESTINATION_AWS_SERVER_SECRET_KEY: secret required to connect with the account where the dashboards will be created`

`DESTINATION_REGION_NAME: region where the dashboards will be created`

`DESTINATION_ROOT_MODEL_ID: SiteWise model id of the hieger level model used in the dashbaords`

`DESTINATION_PORTAL_NAME: SiteWise portal name where the dashboards will be created`

`DESTINATION_PROJECT_NAME: SiteWise project name into the portal where the dashboards will be created`

if you would like to test this script locally (instead of creating an AWS Lambda function),
you can uncomment the lines in the bottom of the script and provide these parameters in there and run

`$python3 export_dashboards.py`