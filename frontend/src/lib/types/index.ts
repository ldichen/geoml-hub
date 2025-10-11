// User types
export interface User {
  id: number;
  external_user_id: string;
  username: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  bio?: string;
  website?: string;
  location?: string;
  followers_count: number;
  following_count: number;
  public_repos_count: number;
  storage_quota: number;
  storage_used: number;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  last_active_at: string;
}

export interface UserCreate {
  external_user_id: string;
  username: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  bio?: string;
  website?: string;
  location?: string;
}

export interface UserUpdate {
  full_name?: string;
  avatar_url?: string;
  bio?: string;
  website?: string;
  location?: string;
}

// UserPublic interface matching backend schema
export interface UserPublic {
  id: number;
  username: string;
  full_name?: string;
  avatar_url?: string;
  bio?: string;
  website?: string;
  location?: string;
  followers_count: number;
  following_count: number;
  public_repos_count: number;
  is_verified: boolean;
  created_at: string;
}

// UserProfile interface for user profile pages
export interface UserProfile extends User {
  // These fields are not part of the backend schema
  // They need to be fetched/computed separately
  is_following?: boolean;
  is_followed_by?: boolean;
}

export interface UserFollow {
  id: number;
  follower: UserPublic;
  following: UserPublic;
  created_at: string;
}

export interface UserStorage {
  id: number;
  user_id: number;
  total_files: number;
  total_size: number;
  model_files_count: number;
  model_files_size: number;
  dataset_files_count: number;
  dataset_files_size: number;
  image_files_count: number;
  image_files_size: number;
  document_files_count: number;
  document_files_size: number;
  other_files_count: number;
  other_files_size: number;
  last_calculated_at: string;
}

// Repository types
export interface Repository {
  id: number;
  name: string;
  full_name: string;
  description?: string;
  owner_id: number;
  owner: UserPublic;
  repo_type: 'model' | 'dataset' | 'space';
  visibility: 'public' | 'private';
  repo_metadata?: Record<string, any>;
  readme_content?: string;
  tags?: string[];
  license?: string;
  stars_count: number;
  downloads_count: number;
  views_count: number;
  forks_count: number;
  total_files: number;
  total_size: number;
  is_active: boolean;
  is_featured: boolean;
  created_at: string;
  updated_at: string;
  last_commit_at?: string;
  // These fields are not part of the backend schema
  // They need to be fetched/computed separately
  is_starred?: boolean;
  is_owned?: boolean;
  classification_path?: string[]; // 分类路径
  task_classifications_data?: TaskClassification[]; // 任务分类列表
}

export interface TaskClassification {
  id: number;
  name: string;
  name_zh?: string;
  description?: string;
  icon?: string;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RepositoryCreate {
  name: string;
  description?: string;
  repo_type: 'model' | 'dataset' | 'space';
  visibility: 'public' | 'private';
  tags?: string[];
  license?: string;
  readme_content?: string;
  repo_metadata?: Record<string, any>;
  classification_id?: number;
}

export interface RepositoryUpdate {
  description?: string;
  visibility?: 'public' | 'private';
  tags?: string[];
  license?: string;
  readme_content?: string;
  repo_metadata?: Record<string, any>;
  classification_id?: number;
}

export interface RepositoryFile {
  id: number;
  repository_id: number;
  filename: string;
  file_path: string;
  file_type?: string;
  mime_type?: string;
  file_size: number;
  file_hash?: string;
  version: string;
  download_count: number;
  created_at: string;
  updated_at: string;
  // Extended properties for file tree display
  is_directory?: boolean;
  path?: string; // alias for file_path
  type?: string; // alias for file_type
}

export interface RepositoryStar {
  id: number;
  user: UserPublic;
  repository_id: number;
  created_at: string;
}

export interface RepositoryView {
  id: number;
  repository_id: number;
  user?: UserPublic;
  ip_address?: string;
  user_agent?: string;
  referer?: string;
  view_type: string;
  target_path?: string;
  created_at: string;
}

export interface RepositoryClassification {
  id: number;
  repository_id: number;
  classification_id: number;
  level: number;
  created_at: string;
  classification?: Classification;
}

// File storage types
export interface FileUploadSession {
  id: number;
  session_id: string;
  user_id: number;
  repository_id?: number;
  filename: string;
  file_path: string;
  file_size: number;
  mime_type?: string;
  file_hash?: string;
  chunk_size: number;
  total_chunks: number;
  uploaded_chunks: number;
  chunk_status?: Record<string, any>;
  minio_bucket?: string;
  minio_object_key?: string;
  minio_upload_id?: string;
  status: 'pending' | 'uploading' | 'completed' | 'failed' | 'cancelled';
  progress_percentage: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  expires_at?: string;
}

export interface FileDownload {
  id: number;
  file_id: number;
  user_id?: number;
  ip_address?: string;
  user_agent?: string;
  referer?: string;
  download_method: string;
  bytes_downloaded: number;
  is_completed: boolean;
  started_at: string;
  completed_at?: string;
}

// Classification types (legacy support)
export interface Classification {
  id: number;
  name: string;
  level: number;
  parent_id?: number;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  parent?: Classification;
  children?: Classification[];
}

// Model types (legacy support)
export interface Model {
  id: number;
  name: string;
  version: string;
  summary: string;
  author?: string;
  organization?: string;
  license?: string;
  base_model?: string;
  model_card_markdown?: string;
  tags?: string[];
  download_count: number;
  like_count: number;
  view_count: number;
  thumbnail_url?: string;
  status: string;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

// API response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface SearchFilters {
  q?: string;
  repo_type?: 'model' | 'dataset' | 'space';
  visibility?: 'public' | 'private';
  license?: string;
  tags?: string[];
  classification_id?: number;
  author?: string;
  organization?: string;
  sort_by?: 'created_at' | 'updated_at' | 'stars_count' | 'downloads_count' | 'views_count';
  sort_order?: 'asc' | 'desc';
  page?: number;
  per_page?: number;
}

export interface UserStats {
  total_repositories: number;
  total_stars_received: number;
  total_downloads: number;
  total_views: number;
  total_followers: number;
  total_following: number;
  total_storage_used: number;
  recent_activity: any[];
}

export interface RepositoryStats {
  total_files: number;
  total_size: number;
  stars_count: number;
  downloads_count: number;
  views_count: number;
  forks_count: number;
  recent_downloads: any[];
  recent_views: any[];
  star_history: any[];
}

// Form types
export interface LoginForm {
  username: string;
  password: string;
}

export interface SignupForm {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface RepositoryForm {
  name: string;
  description?: string;
  repo_type: 'model' | 'dataset' | 'space';
  visibility: 'public' | 'private';
  license?: string;
  tags?: string[];
  readme_content?: string;
}

// Upload types
export interface UploadProgress {
  filename: string;
  progress: number;
  status: 'uploading' | 'completed' | 'failed';
  error?: string;
}

export interface FileUploadOptions {
  onProgress?: (progress: number) => void;
  onComplete?: (file: RepositoryFile) => void;
  onError?: (error: string) => void;
}

// Theme types
export interface Theme {
  mode: 'light' | 'dark';
  primary: string;
  secondary: string;
  background: string;
  surface: string;
  text: string;
}

// Navigation types
export interface NavItem {
  label: string;
  href: string;
  icon?: string;
  badge?: string | number;
  active?: boolean;
  external?: boolean;
}

// Notification types
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  timeout?: number;
  actions?: NotificationAction[];
}

export interface NotificationAction {
  label: string;
  action: () => void;
  style?: 'primary' | 'secondary' | 'danger';
}

// Event types
export interface CustomEvent<T = any> {
  type: string;
  detail: T;
}

// Store types
export interface AppStore {
  user: User | null;
  theme: Theme;
  notifications: Notification[];
  loading: boolean;
  error: string | null;
}

export interface RepositoryStore {
  current: Repository | null;
  files: RepositoryFile[];
  stars: RepositoryStar[];
  loading: boolean;
  error: string | null;
}

export interface UserStore {
  current: User | null;
  repositories: Repository[];
  followers: UserFollow[];
  following: UserFollow[];
  stats: UserStats | null;
  loading: boolean;
  error: string | null;
}