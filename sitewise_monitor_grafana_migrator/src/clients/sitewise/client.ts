import { DashboardSummary, IoTSiteWise, ProjectSummary } from '@aws-sdk/client-iotsitewise';

// Used to easily reference a project and its contents
export type PortalResourceMap = {
  [projectId: string]: {
    projectSummary: ProjectSummary,
    dashboardSummaries: DashboardSummary[]
  },
};

/**
 * IotSiteWiseClient is a wrapper for interacting with SiteWise resources for a given portal.
 */
export class IotSiteWiseClient {

  private sitewiseClient: IoTSiteWise;

  private portalId: string;

  constructor ({
    region,
    portalId,
  }: {
    region: string;
    portalId: string;
  }) {
    this.sitewiseClient = new IoTSiteWise({
      region,
    });
    this.portalId = portalId;
  }

  // Creates a PortalResourceMap with all projects and dashboards
  public getPortalResources = async () => {
    const projects = await this.listProjects();
    const resourceMap: PortalResourceMap = {};

    for (const projectSummary of projects) {
      if (projectSummary.id) {
        const dashboards = await this.listDashboards(projectSummary.id);
        resourceMap[projectSummary.id] = {
          projectSummary,
          dashboardSummaries: dashboards
        };
      }
    }

    return resourceMap;
  }

  // Lists all projects in a portal
  private listProjects = async () => {
    let nextToken: string | undefined;
    let projects: ProjectSummary[] = [];
    do {
      const listProjectsResponse = await this.sitewiseClient.listProjects({
        portalId: this.portalId,
      });

      if (listProjectsResponse.projectSummaries) {
        projects = projects.concat(listProjectsResponse.projectSummaries);
      }

      nextToken = listProjectsResponse.nextToken;
    } while (!!nextToken);

    return projects;
  }

  // Lists all dashboards in a project
  private listDashboards = async (projectId: string) => {
    let nextToken: string | undefined;
    let dashboards: DashboardSummary[] = [];
    do {
      const listDashboardsResponse = await this.sitewiseClient.listDashboards({
        projectId: projectId,
      });

      if (listDashboardsResponse.dashboardSummaries) {
        dashboards = dashboards.concat(listDashboardsResponse.dashboardSummaries);
      }

      nextToken = listDashboardsResponse.nextToken;
    } while (!!nextToken);

    return dashboards;
  }
}