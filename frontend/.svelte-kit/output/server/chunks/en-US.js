const app = {
  name: "GeoML-Hub",
  description: "The First Machine Learning Model Repository for Geographic Sciences",
  version: "Version {version}"
};
const navigation = {
  home: "Home",
  models: "Models",
  categories: "Categories",
  about: "About",
  login: "Login",
  register: "Register",
  profile: "Profile",
  admin: "Admin",
  logout: "Logout"
};
const common = {
  search: "Search",
  filter: "Filter",
  sort: "Sort",
  loading: "Loading...",
  error: "Error",
  success: "Success",
  warning: "Warning",
  info: "Info",
  confirm: "Confirm",
  cancel: "Cancel",
  save: "Save",
  "delete": "Delete",
  edit: "Edit",
  create: "Create",
  update: "Update",
  submit: "Submit",
  reset: "Reset",
  clear: "Clear",
  back: "Back",
  next: "Next",
  previous: "Previous",
  finish: "Finish",
  close: "Close",
  open: "Open",
  view: "View",
  download: "Download",
  upload: "Upload",
  copy: "Copy",
  share: "Share",
  like: "Like",
  favorite: "Favorite",
  comment: "Comment",
  report: "Report"
};
const model = {
  title: "Model",
  list: "Model List",
  detail: "Model Details",
  create: "Create Model",
  edit: "Edit Model",
  "delete": "Delete Model",
  name: "Model Name",
  displayName: "Display Name",
  version: "Version",
  summary: "Summary",
  description: "Description",
  author: "Author",
  organization: "Organization",
  license: "License",
  framework: "Framework",
  modelType: "Model Type",
  dataType: "Data Type",
  tags: "Tags",
  category: "Category",
  subcategory: "Subcategory",
  geographicCoverage: "Geographic Coverage",
  temporalCoverage: "Temporal Coverage",
  coordinateSystem: "Coordinate System",
  spatialResolution: "Spatial Resolution",
  temporalResolution: "Temporal Resolution",
  thumbnail: "Thumbnail",
  modelCard: "Model Card",
  services: "Services",
  statistics: "Statistics",
  viewCount: "View Count",
  downloadCount: "Download Count",
  likeCount: "Like Count",
  createdAt: "Created At",
  updatedAt: "Updated At",
  status: "Status",
  featured: "Featured",
  active: "Active",
  inactive: "Inactive",
  deprecated: "Deprecated"
};
const service = {
  title: "Service",
  name: "Service Name",
  description: "Service Description",
  url: "Service URL",
  pageUrl: "Service Page",
  status: "Status",
  health: "Health Status",
  healthy: "Healthy",
  unhealthy: "Unhealthy",
  unknown: "Unknown",
  responseTime: "Response Time",
  successRate: "Success Rate",
  lastCheck: "Last Check",
  visitService: "Visit Service",
  testService: "Test Service",
  configure: "Configure",
  apiConfig: "API Configuration",
  requestExample: "Request Example",
  responseExample: "Response Example"
};
const category = {
  title: "Category",
  all: "All",
  physicalGeography: "Physical Geography",
  humanGeography: "Human Geography",
  geographicInformationScience: "Geographic Information Science",
  earthSystemScience: "Earth System Science",
  climatology: "Climatology",
  hydrology: "Hydrology",
  geomorphology: "Geomorphology",
  biogeography: "Biogeography",
  pedology: "Pedology",
  urbanGeography: "Urban Geography",
  economicGeography: "Economic Geography",
  populationGeography: "Population Geography",
  culturalGeography: "Cultural Geography",
  politicalGeography: "Political Geography",
  remoteSensing: "Remote Sensing",
  gis: "Geographic Information Systems",
  cartography: "Cartography",
  spatialAnalysis: "Spatial Analysis",
  atmosphericScience: "Atmospheric Science",
  oceanography: "Oceanography",
  glaciology: "Glaciology",
  globalChange: "Global Change"
};
const search = {
  placeholder: "Search models...",
  results: "Search Results",
  noResults: "No models found",
  total: "{count} results",
  filters: "Filters",
  clearFilters: "Clear Filters",
  sortBy: "Sort By",
  sortByName: "Sort by Name",
  sortByDate: "Sort by Date",
  sortByViews: "Sort by Views",
  sortByDownloads: "Sort by Downloads",
  sortByLikes: "Sort by Likes",
  order: "Order",
  orderAsc: "Ascending",
  orderDesc: "Descending"
};
const form = {
  basicInfo: "Basic Information",
  modelCard: "Model Card",
  serviceConfig: "Service Configuration",
  preview: "Preview",
  required: "Required",
  optional: "Optional",
  placeholder: {
    name: "Enter model name",
    displayName: "Enter display name",
    summary: "Enter model summary",
    author: "Enter author name",
    organization: "Enter organization name",
    tags: "Enter tags, separated by commas"
  },
  validation: {
    required: "This field is required",
    minLength: "Minimum {min} characters required",
    maxLength: "Maximum {max} characters allowed",
    email: "Please enter a valid email address",
    url: "Please enter a valid URL",
    pattern: "Invalid format"
  },
  steps: {
    basicInfo: "Basic Info",
    modelCard: "Model Card",
    services: "Services",
    review: "Review"
  }
};
const theme = {
  light: "Light Mode",
  dark: "Dark Mode",
  system: "System",
  toggle: "Toggle Theme"
};
const language = {
  chinese: "中文",
  english: "English",
  "switch": "Switch Language"
};
const error = {
  "404": "Page Not Found",
  "500": "Server Error",
  network: "Network Connection Failed",
  permission: "Permission Denied",
  validation: "Validation Failed",
  unknown: "Unknown Error"
};
const pagination = {
  previous: "Previous",
  next: "Next",
  first: "First",
  last: "Last",
  page: "Page {page}",
  of: "of {total}",
  items: "{total} items",
  showing: "Showing {from} - {to} of {total} items"
};
const openGMS = {
  openGMS: "OpenGMS"
};
const enUS = {
  app,
  navigation,
  common,
  model,
  service,
  category,
  search,
  form,
  theme,
  language,
  error,
  pagination,
  openGMS
};
export {
  app,
  category,
  common,
  enUS as default,
  error,
  form,
  language,
  model,
  navigation,
  openGMS,
  pagination,
  search,
  service,
  theme
};
