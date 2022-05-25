# AWS IoT SiteWise Tools

This repository contains tools that can be used to automate various tasks in the AWS IoT SiteWise service. Please see the README for each tool for details and instructions. 

Note: These tools use the AWS SDK for SiteWise (mostly Boto3) they assume you have the SDKs installed and have AWS credentials setup on your machine that will give you access to the various API operations the tools require. 

## Table of Contents

### SiteWise Export Tools V2
Contains an Asset and Asset Model export tool that will generate a CloudFormation template of all assets and asset models (including the hierarchy information) for a given region in an AWS account. You have the option to export only the asset model or both the asset models and asset(s). 

### SiteWise Monitor Dashboard Replicator
Contains a CLI tool that replicates a dashboard of a given asset for all assets of the same asset model. This useful if you have dashboards for each machine and want to copy and keep them in sync for all machines of the same type.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

