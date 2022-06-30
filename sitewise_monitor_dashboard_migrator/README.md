# SiteWise Dashboards Migration Tool

This tool is used to migrate dashboards from a source account into a destination account.

This is useful for customers following (or looking to follow) DevOps and CI/CD practices in their IoT projects where
automation is job zero and dashboards have to be promoted between dev, test and production environments.

# Problem Addressed

AWS SiteWise Monitor Dashboards, as many other dashboarding tools, relay on datasource objects ids.
In AWS SiteWise these are Assets and Properties ids.
It means that, if well you can backup dashboards using AWS SiteWise APIs, the backup dashboard will not work in
a different account/region because Assets and Properties ids are going to be different.

This makes dashboards development, automation and portability between environments (dev, testing, prod, etc)
complicated. 

# Pre-requisites

1. Assets and Properties names in source and destination environment have to be identical. It is most of the time
   true in organizations following DevOps and CI/CD practices where environment deployments and infrastructure
   operations is automated
2. A SiteWise Portal and a project with the previously mentioned asset (at least those used in the dashboards) assigned
to the project.   
3. Credentials with permissions to call AWS SiteWise APIs in both, source and destination accounts,  are needed.

# Use

This script is developed as lambda function. For simplicity, we set source and destination credentials as Lambda
environmental variables.
---
If you are planning to use this script for something else than testing, please store your keys in AWS Secret Manager.
https://docs.aws.amazon.com/code-samples/latest/catalog/python-secretsmanager-secretsmanager_basics.py.html
---

To use this script you have to provided following parameter:

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