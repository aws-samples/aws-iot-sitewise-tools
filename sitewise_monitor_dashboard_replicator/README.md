# SiteWise Dashboard Replicator

This tool is used to replicate dashboards for individual assets. It take a source or template dashboard for a given asset and then replicates it for all assets that share the same asset model. Source dashboards are identified by a {source} tag in the Dashboard name. All properties in the source dashboard must come from the same asset. 

## Usage
Replicate all tagged dashboards in a region

`$python3 sitewise_dashboard_replicator.py --all`

Replicate all tagged dashboards in a region with custom source tag

`$python3 sitewise_dashboard_replicator.py --all --source_tag ANY_STRING`

Replicate a single tagged dashboards in a region

`$python3 sitewise_dashboard_replicator.py --dashboard_id be3344f9-a33a-4412-a1dd-aaaaaaaa`

Specify AWS credential profile and/or region via the flags:

`--region`

`--profile`