import { RequestOptions } from 'https';
import { GrafanaPath } from './urlPaths';
import { HTTPMethod, httpsRequest } from '../https';

const SITEWISE_PLUGIN_ID = 'grafana-iot-sitewise-datasource';

/**
 * GrafanaClient is a wrapper for Grafana HTTP API requests.
 * APIs require an auth token in the header and the Grafana workspace URL.
 * 
 * This script uses resource UIDs to reference the resource instead of the ID.
 * From the Grafana documentation: 
 *    The uid allows having consistent URLs for accessing dashboards and when 
 *    syncing dashboards between multiple Grafana installs.
 */
export class GrafanaClient {

  private requestHeaders: RequestOptions;

  private workspaceEndpoint: string;
  private region: string;

  constructor ({
    authToken,
    workspaceEndpoint,
    region,
  }: {
    authToken: string;
    workspaceEndpoint: string;
    region: string;
  }) {
    // Same headers used for every request
    this.requestHeaders = {
      headers: {
        authorization: `Bearer ${authToken}`,
        'content-type': 'application/json',
        accept: 'application/json',
      },
    }
    this.workspaceEndpoint = workspaceEndpoint;
    this.region = region;
  }

  // Util for setting up the HTTP request options with the path to the API
  private requestOptions = (
    { path, method }:
    { path: string, method: string }
  ): RequestOptions => {
    const { hostname, pathname } = new URL(`https://${this.workspaceEndpoint}${path}`);
    return {
      ...this.requestHeaders,
      hostname,
      path: pathname,
      method,
    };
  }

  // Install the IoT SiteWise datasource plugin in the Grafana workspace
  public installPlugin = async () => {
    console.log(`Installing plugin with ID ${SITEWISE_PLUGIN_ID}...`);
    const installPluginOptions: RequestOptions = this.requestOptions(
      {
        path: GrafanaPath.InstallPlugin(SITEWISE_PLUGIN_ID),
        method: HTTPMethod.POST,
      }
    );

    const installPluginResponse = await httpsRequest(installPluginOptions);
    // There will only be a message if the plugin is already installed
    if (installPluginResponse && installPluginResponse.message) {
      console.log(installPluginResponse.message);
    }
  }

  // Get datasource instance by its name
  public getDatasourceByName = async (name: string) => {
    const getDatasourceOptions: RequestOptions = this.requestOptions(
      {
        path: GrafanaPath.GetDatasource(name),
        method: HTTPMethod.GET,
      }
    );

    const getDatasourceResponse = await httpsRequest(getDatasourceOptions);
    if (getDatasourceResponse) {
      return getDatasourceResponse.uid;
    }
  }

  // Create a SiteWise datasource instance with a given name
  public createDatasource = async (name: string) => {
    console.log(`Creating datasource instance with name ${name}...`);

    const createDatasourceOptions: RequestOptions = this.requestOptions(
      {
        path: GrafanaPath.CreateDatasource,
        method: HTTPMethod.POST,
      }
    );

    const data = {
      name,
      type: SITEWISE_PLUGIN_ID,
      access: 'proxy',
      jsonData: {
        authType: 'default',
        defaultRegion: this.region,
      }
    };
    
    const createDatasourceResponse = await httpsRequest(createDatasourceOptions, data);
    if (createDatasourceResponse) {
      if (createDatasourceResponse.message) {
        console.log(createDatasourceResponse.message);
      }
      return createDatasourceResponse.datasource?.uid;
    }
  }

  // List all folders in the Grafana workspace
  public listFolders = async () => {
    const listFoldersOptions: RequestOptions = this.requestOptions(
      {
        path: GrafanaPath.GetFolder,
        method: HTTPMethod.GET,
      }
    );

    const listFoldersResponse = await httpsRequest(listFoldersOptions);

    if (listFoldersResponse && listFoldersResponse.length > 0) {
      return [...listFoldersResponse];
    }
    return [];
  }

  // Create a folder with a given name
  public createFolder = async (name: string) => {
    console.log(`Creating folder with name ${name}...`);

    const createFolderOptions: RequestOptions = this.requestOptions(
      {
        path: GrafanaPath.CreateFolder,
        method: HTTPMethod.POST,
      }
    );

    const data = {
      title: name,
    };
    const createFolderResponse = await httpsRequest(createFolderOptions, data);
    if (createFolderResponse) {
      if (createFolderResponse.message) {
        console.log(createFolderResponse.message);
      }
      return createFolderResponse.uid;
    }
  }

  // List all dashboards in a Grafana workspace
  public listDashboards = async () => {
    const searchOptions: RequestOptions = this.requestOptions(
      {
        path: GrafanaPath.Search,
        method: HTTPMethod.GET,
      }
    );

    const searchResponse = await httpsRequest(searchOptions);
    return searchResponse.filter((dash) => dash.type === 'dash-db');
  }

  // Create a dashboard with a given name for a given folder
  // TODO: Migrate dashboard content
  public createDashboard = async (
    { dashboardName, folderUid }:
    { dashboardName: string, folderUid: string }
  ) => {
    console.log(`Creating dashboard with name ${dashboardName}...`);

    const createDashboardOptions: RequestOptions = this.requestOptions(
      {
        path: GrafanaPath.CreateDashboard,
        method: HTTPMethod.POST,
      }
    );

    const data = {
      dashboard: {
        title: dashboardName,
      },
      folderUid,
      message: 'IoT SiteWise auto-created dashboard', 
    };
    const createDashboardResponse = await httpsRequest(createDashboardOptions, data);
    if (createDashboardResponse) {
      if (createDashboardResponse.message) {
        console.log(createDashboardResponse.message);
      }
      return createDashboardResponse.uid;
    }
  }
}