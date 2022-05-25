# SiteWise Export Tools

Note: On 05/25/2022 we released V2 of this tool that now supports exporting assets as well as asset models. Unless you have a sepecific reason to use this older version you should use V2 which is located in the sitewise_export_tools_v2 folder. 

## Asset Model Export Tool
Generates a CloudFormation template of all asset models (including the hierarchy information) for a given region in an AWS account. You can then take the CloudFormation template and create the same asset models and hierarchy in a different region and/or AWS account.

Note: The tool does not currently support alarms. 

### Usage
Export all models in given region/account based on your AWS credentials defaults

`$python3 asset_model_exporter.py`

Specify AWS credential profile and/or region via the flags:

`--region`

`--profile`