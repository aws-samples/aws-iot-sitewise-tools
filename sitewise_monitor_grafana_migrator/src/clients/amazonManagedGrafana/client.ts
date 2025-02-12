import { Grafana } from '@aws-sdk/client-grafana';
import { GrafanaClient } from '../grafana/client';
import { PortalResourceMap } from '../sitewise/client';
import { DashboardSummary, ProjectSummary } from '@aws-sdk/client-iotsitewise';

const SERVICE_ACCOUNT_NAME = 'IoT_SiteWise_Monitor_Migration_Service_Account';
const SERVICE_ACCOUNT_TOKEN_NAME = 'IoT_SiteWise_Monitor_Migration_Temporary_Token';
const SITEWISE_DATASOURCE_NAME = 'SiteWise_Migrated_Datasource';

/**
 * AmazonManagedGrafanaClient handles interaction with Amazon Managed Grafana resources (e.g. workspace)
 * and Grafana resources (e.g. datasources, folders, dashboards).
 * 
 * Has initialize() and tearDown() functions to set up and clean up auth for the Grafana HTTP APIs.
 * 
 * Handles high level resource migration from SiteWise Monitor portals to Grafana.
 */
export class AmazonManagedGrafanaClient {

  private amazonManagedGrafanaClient: Grafana;
  private grafanaClient: GrafanaClient;

  private region: string;
  private workspaceId: string;
  private workspaceEndpoint: string;
  private grafanaToken: string;
  private grafanaTokenId: string;
  private serviceAccountId: string;

  constructor ({
    region,
    workspaceId,
  }: {
    region: string;
    workspaceId: string;
  }) {
    this.amazonManagedGrafanaClient = new Grafana({
      region,
    });
    this.region = region;
    this.workspaceId = workspaceId;
  }

  /**
   * Handles the creation of all Grafana resources - datasource, folders, dashboards
   * given SiteWise Monitor portal resources - projects, dashboards
   * @param portalResourceMap is a map of projects to the project and dashboard summaries
   */
  public migrateToGrafanaResources = async (portalResourceMap: PortalResourceMap) => {
    try {
      // Initialize Grafana auth token and get workspace info 
      await this.initialize();

      // Install SiteWise plugin in the workspace
      await this.grafanaClient.installPlugin();

      // Create a datasource instance if it doesn't exist
      const datasourceUid = await this.createDatasource(SITEWISE_DATASOURCE_NAME);

      // Create a Grafana folder for each SiteWise project
      const portalResources = Object.values(portalResourceMap);
      const projectSummaries = portalResources.map(({ projectSummary }) => projectSummary);
      const projectsToFoldersMap = await this.migrateProjectsToFolders(projectSummaries);

      // Create a Grafana dashboard for each dashboard in each project
      for (const project of portalResources) {
        if (project.projectSummary.id) {
          await this.migrateDashboards({
            dashboards: project.dashboardSummaries,
            folderUid: projectsToFoldersMap[project.projectSummary.id],
          });
        }
      }

      // When migration is done clean up resources
      await this.tearDown();
    } catch (e) {
      // On any error attempt to clean up resources
      await this.tearDown();
      throw e;
    }
  }

  /**
   * Need auth tokens for the Grafana HTTP request headers
   * Create a service account in the Grafana workspace and then the token in that service account.
   * Used to initialize the Grafana HTTP client.
   */
  private initialize = async () => {
    // Get Amazon Managed Grafana workspace details
    const describeWorkspaceResponse = await this.amazonManagedGrafanaClient.describeWorkspace({
      workspaceId: this.workspaceId,
    });

    if (!describeWorkspaceResponse.workspace?.endpoint) {
      throw new Error(`Failed to describe the Amazon Managed Grafana workspace ${this.workspaceId}. Unable to find the workspace endpoint.`);
    }

    this.workspaceEndpoint = describeWorkspaceResponse.workspace.endpoint;

    // Create service account and token for authorizing Grafana commands
    const createServiceAccountResponse = await this.amazonManagedGrafanaClient.createWorkspaceServiceAccount({
      workspaceId: this.workspaceId,
      grafanaRole: 'ADMIN',
      name: SERVICE_ACCOUNT_NAME,
    });

    if (!createServiceAccountResponse.id) {
      throw new Error(`Failed to create a service account for the Amazon Managed Grafana workspace ${this.workspaceId}. Unable to find the service account ID.`);
    }

    this.serviceAccountId = createServiceAccountResponse.id;

    const createServiceAccountTokenResponse = await this.amazonManagedGrafanaClient.createWorkspaceServiceAccountToken({
      workspaceId: this.workspaceId,
      serviceAccountId: this.serviceAccountId,
      name: SERVICE_ACCOUNT_TOKEN_NAME,
      secondsToLive: 900,
    });

    if (!createServiceAccountTokenResponse.serviceAccountToken?.key || !createServiceAccountTokenResponse.serviceAccountToken?.id) {
      throw new Error(`Failed to create a service account token for the Amazon Managed Grafana workspace ${this.workspaceId}. Unable to find the token.`);
    }

    this.grafanaToken = createServiceAccountTokenResponse.serviceAccountToken.key;
    this.grafanaTokenId = createServiceAccountTokenResponse.serviceAccountToken.id;

    this.grafanaClient = new GrafanaClient({
      authToken: this.grafanaToken,
      workspaceEndpoint: this.workspaceEndpoint,
      region: this.region,
    });
  };

  // Clean up service account and token
  private tearDown = async () => {
    console.log('Cleaning up temporary resources...');

    if (this.grafanaToken && this.serviceAccountId) {
      await this.amazonManagedGrafanaClient.deleteWorkspaceServiceAccountToken({
        workspaceId: this.workspaceId,
        serviceAccountId: this.serviceAccountId,
        tokenId: this.grafanaTokenId,
      });
    }

    if (this.serviceAccountId) {
      await this.amazonManagedGrafanaClient.deleteWorkspaceServiceAccount({
        workspaceId: this.workspaceId,
        serviceAccountId: this.serviceAccountId,
      });
    }
  }

  private createDatasource = async (name: string) => {
    // Check if datasource instance is already created
    let datasourceUid = await this.grafanaClient.getDatasourceByName(name);

    if (!datasourceUid) {
      // Create a SiteWise datasource instance in the workspace
      datasourceUid = await this.grafanaClient.createDatasource(name);
    }

    if (!datasourceUid) {
      throw new Error('Unable to create a datasource in the Amazon Managed Grafana workspace.');
    }

    return datasourceUid;
  }

  private migrateProjectsToFolders = async (projects: ProjectSummary[]) => {
    // Compare existing folders so we don't try creating ones that already exist
    const folders = await this.grafanaClient.listFolders();

    // Keep map of SiteWise projects to Grafana folders
    const projectsToFoldersMap: {
      [projectId: string]: string;
    } = {};

    for (const projectSummary of projects) {
      if (projectSummary.name && projectSummary.id) {
        // Try to find matching folder and project
        const folder = folders.find((folder) => folder.title === projectSummary.name);
        let folderUid: string | undefined;
        // Create a new folder if there's no match
        if (!folder) {
          folderUid = await this.grafanaClient.createFolder(projectSummary.name);
        } else {
          folderUid = folder.uid;
        }
        
        if (folderUid) {
          projectsToFoldersMap[projectSummary.id] = folderUid;
        }
      }
    }
    return projectsToFoldersMap;
  }

  private migrateDashboards = async (
    { dashboards, folderUid }:
    { dashboards: DashboardSummary[], folderUid: string }
  ) => {
    // Compare existing dashboards so we don't try creating ones that already exist
    const grafanaDashboards = await this.grafanaClient.listDashboards();

    for (const dashboardSummary of dashboards) {
      if (dashboardSummary.name) {
        // Try to find matching Grafana dashboard
        const dashboard = grafanaDashboards.find((grafanaDashboard) => grafanaDashboard.title === dashboardSummary.name);
        if (!dashboard) {
          await this.grafanaClient.createDashboard({
            dashboardName: dashboardSummary.name,
            folderUid,
          })
        }
      }
    }
  }
}