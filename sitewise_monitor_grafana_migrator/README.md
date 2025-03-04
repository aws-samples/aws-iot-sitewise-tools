# SWM Grafana Migration

This tool is used to migrate SiteWise Monitor Classic (v1) portals to Amazon Managed Grafana. Input a source portal and destination Amazon Managed Grafana workspace and all of the source projects and dashboards are converted to Grafana folders and dashboards. 

In the future:
1. A new Amazon Managed Grafana workspace will be created for you.
2. All IAM Identity Center users and permissions from the source portal are migrated to the Amazon Managed Grafana workspace.

## Usage

### Prerequisites

1. Configure AWS credentials in your environment for the AWS CLI: https://docs.aws.amazon.com/cli/v1/userguide/cli-chap-configure.html
2. Install script dependencies

```
npm install
```

### Commands

Help command

```
npx ts-node src/index.ts --help
```

Migrate SiteWise Monitor portal resources to an Amazon Managed Grafana workspace

```
npx ts-node src/index.ts --region <REGION> --portalId <PORTAL_ID> --workspaceId <WORKSPACE_ID>
```

Example:

```
npx ts-node src/index.ts --region us-east-1 --portalId 12345678-9012-3456-7890-abcdef123456 --workspaceId g-1234567890
```
