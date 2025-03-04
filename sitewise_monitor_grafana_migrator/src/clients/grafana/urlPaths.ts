export const GrafanaPath = {
  CreateDatasource: '/api/datasources',
  CreateDashboard: '/api/dashboards/db',
  CreateFolder: '/api/folders',
  GetDatasource: (name: string) => `/api/datasources/name/${name}`,
  GetFolder: '/api/folders',
  InstallPlugin: (id: string) => `/api/plugins/${id}/install`,
  Search: '/api/search',
};