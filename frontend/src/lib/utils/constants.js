export const FRAMEWORK_OPTIONS = [
  'pytorch',
  'tensorflow',
  'keras',
  'scikit-learn',
  'xgboost',
  'lightgbm',
  'catboost',
  'huggingface',
  'onnx',
  'other'
];

export const MODEL_TYPE_OPTIONS = [
  'classification',
  'regression',
  'segmentation',
  'detection',
  'clustering',
  'simulation',
  'prediction',
  'other'
];

export const DATA_TYPE_OPTIONS = [
  'raster',
  'vector',
  'point',
  'trajectory',
  'time-series',
  'text',
  'image',
  'other'
];

export const LICENSE_OPTIONS = [
  'MIT',
  'Apache-2.0',
  'BSD-3-Clause',
  'GPL-3.0',
  'LGPL-3.0',
  'CC-BY-4.0',
  'CC-BY-SA-4.0',
  'Other'
];

export const SORT_OPTIONS = [
  { value: 'created_at', label: '按创建时间' },
  { value: 'updated_at', label: '按更新时间' },
  { value: 'view_count', label: '按浏览量' },
  { value: 'download_count', label: '按下载量' },
  { value: 'like_count', label: '按点赞数' },
  { value: 'name', label: '按名称' }
];

export const DEFAULT_PAGINATION = {
  page: 1,
  size: 20,
  total: 0,
  has_next: false,
  has_prev: false
};

export const THEMES = {
  LIGHT: 'light',
  DARK: 'dark',
  SYSTEM: 'system'
};

export const LOCALES = {
  ZH_CN: 'zh-CN',
  EN_US: 'en-US'
};

export const STORAGE_KEYS = {
  THEME: 'geoml-theme',
  LOCALE: 'geoml-locale',
  FILTERS: 'geoml-filters'
};

export const HEALTH_STATUS = {
  HEALTHY: 'healthy',
  UNHEALTHY: 'unhealthy',
  UNKNOWN: 'unknown'
};

export const MODEL_STATUS = {
  ACTIVE: 'active',
  INACTIVE: 'inactive',
  DEPRECATED: 'deprecated'
};