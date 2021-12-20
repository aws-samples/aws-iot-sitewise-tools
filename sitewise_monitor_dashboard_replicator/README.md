# SiteWise Dashboard Replicator Tool

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


# SiteWise Dashboard Copy Tool

This tool is used to copy a dashboard from one project to another within a region in an account.

## Usage
Copy dashboard to another project.

`$python3 sitewise_dashboard_copy.py copy_dashboard --dashboard_id 3k34k663-b271-4d71-be95-aaaaaaaaa --project_id 2343242-6008-406e-87a4-aaaaaaaaaa`

Export the dashboard JSON definition (does not copy).

`$python3 sitewise_dashboard_copy.py copy_dashboard --dashboard_id 3k34k663-b271-4d71-be95-aaaaaaaaa --print_definition`

List dashboards available to copy in the region.

`$python3 sitewise_dashboard_copy.py list_dashboards`

List projects available in the region to copy a dashboard to.

`$python3 sitewise_dashboard_copy.py list_projects`

Specify AWS credential profile and/or region via the flags:

`--region`

`--profile`