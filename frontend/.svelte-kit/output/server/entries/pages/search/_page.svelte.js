import { s as subscribe } from "../../../chunks/utils.js";
import { c as create_ssr_component, v as validate_component, e as escape, d as add_attribute, a as each, b as createEventDispatcher } from "../../../chunks/ssr.js";
import { p as page } from "../../../chunks/stores.js";
import { b as base } from "../../../chunks/paths.js";
import { $ as $format } from "../../../chunks/runtime.js";
import { B as BROWSER } from "../../../chunks/false.js";
import { P as PATHS } from "../../../chunks/paths2.js";
import { user } from "../../../chunks/auth.js";
import { formatDistanceToNow } from "date-fns";
import zhCN from "date-fns/locale/zh-CN/index.js";
import { I as Icon } from "../../../chunks/Icon.js";
/* empty css                                                            */import { S as Star, D as Download, E as Eye } from "../../../chunks/star.js";
import { C as Calendar, F as Filter } from "../../../chunks/filter.js";
import { L as Loading } from "../../../chunks/Loading.js";
import { S as Search } from "../../../chunks/search.js";
const browser = BROWSER;
function client_method(key) {
  {
    if (key === "before_navigate" || key === "after_navigate" || key === "on_navigate") {
      return () => {
      };
    } else {
      const name_lookup = {
        disable_scroll_handling: "disableScrollHandling",
        preload_data: "preloadData",
        preload_code: "preloadCode",
        invalidate_all: "invalidateAll"
      };
      return () => {
        throw new Error(`Cannot call ${name_lookup[key] ?? key}(...) on the server`);
      };
    }
  }
}
const goto = /* @__PURE__ */ client_method("goto");
const PUBLIC_API_BASE_URL = "/geoml-hub-backend";
class ApiError extends Error {
  constructor(message, code, status, context = null, requestId = null) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.context = context;
    this.requestId = requestId;
  }
}
const ERROR_CODES = {
  // 通用错误
  INTERNAL_SERVER_ERROR: "INTERNAL_SERVER_ERROR",
  VALIDATION_ERROR: "VALIDATION_ERROR",
  AUTHENTICATION_ERROR: "AUTHENTICATION_ERROR",
  AUTHORIZATION_ERROR: "AUTHORIZATION_ERROR",
  NOT_FOUND: "NOT_FOUND",
  CONFLICT: "CONFLICT",
  BAD_REQUEST: "BAD_REQUEST",
  // 仓库相关错误
  REPOSITORY_NOT_FOUND: "REPOSITORY_NOT_FOUND",
  REPOSITORY_ALREADY_EXISTS: "REPOSITORY_ALREADY_EXISTS",
  REPOSITORY_CREATE_FAILED: "REPOSITORY_CREATE_FAILED",
  INVALID_REPOSITORY_NAME: "INVALID_REPOSITORY_NAME",
  // 文件相关错误
  FILE_NOT_FOUND: "FILE_NOT_FOUND",
  FILE_UPLOAD_FAILED: "FILE_UPLOAD_FAILED",
  INVALID_FILE_TYPE: "INVALID_FILE_TYPE",
  FILE_TOO_LARGE: "FILE_TOO_LARGE",
  // 用户相关错误
  USER_NOT_FOUND: "USER_NOT_FOUND",
  INVALID_CREDENTIALS: "INVALID_CREDENTIALS",
  USER_ALREADY_EXISTS: "USER_ALREADY_EXISTS",
  // 存储相关错误
  STORAGE_ERROR: "STORAGE_ERROR",
  // 外部服务错误
  EXTERNAL_SERVICE_ERROR: "EXTERNAL_SERVICE_ERROR",
  // 数据库错误
  DATABASE_ERROR: "DATABASE_ERROR",
  DUPLICATE_RESOURCE: "DUPLICATE_RESOURCE",
  FOREIGN_KEY_VIOLATION: "FOREIGN_KEY_VIOLATION"
};
const ERROR_MESSAGES = {
  [ERROR_CODES.INTERNAL_SERVER_ERROR]: "服务器内部错误，请稍后重试",
  [ERROR_CODES.VALIDATION_ERROR]: "输入数据格式错误，请检查后重试",
  [ERROR_CODES.AUTHENTICATION_ERROR]: "需要登录才能进行此操作",
  [ERROR_CODES.AUTHORIZATION_ERROR]: "您没有权限进行此操作",
  [ERROR_CODES.NOT_FOUND]: "请求的资源不存在",
  [ERROR_CODES.CONFLICT]: "操作冲突，请刷新页面后重试",
  [ERROR_CODES.BAD_REQUEST]: "请求参数错误",
  [ERROR_CODES.REPOSITORY_NOT_FOUND]: "仓库不存在",
  [ERROR_CODES.REPOSITORY_ALREADY_EXISTS]: "仓库名已存在",
  [ERROR_CODES.REPOSITORY_CREATE_FAILED]: "创建仓库失败",
  [ERROR_CODES.INVALID_REPOSITORY_NAME]: "仓库名格式错误",
  [ERROR_CODES.FILE_NOT_FOUND]: "文件不存在",
  [ERROR_CODES.FILE_UPLOAD_FAILED]: "文件上传失败",
  [ERROR_CODES.INVALID_FILE_TYPE]: "不支持的文件类型",
  [ERROR_CODES.FILE_TOO_LARGE]: "文件过大",
  [ERROR_CODES.USER_NOT_FOUND]: "用户不存在",
  [ERROR_CODES.INVALID_CREDENTIALS]: "用户名或密码错误",
  [ERROR_CODES.USER_ALREADY_EXISTS]: "用户已存在",
  [ERROR_CODES.STORAGE_ERROR]: "存储服务错误",
  [ERROR_CODES.EXTERNAL_SERVICE_ERROR]: "外部服务暂时不可用",
  [ERROR_CODES.DATABASE_ERROR]: "数据库操作失败",
  [ERROR_CODES.DUPLICATE_RESOURCE]: "资源已存在",
  [ERROR_CODES.FOREIGN_KEY_VIOLATION]: "引用的资源不存在"
};
function parseApiError(error) {
  if (error instanceof ApiError) {
    return error;
  }
  if (error.response) {
    const response = error.response;
    const data = response.data || {};
    if (data.error) {
      return new ApiError(
        data.error.message,
        data.error.code,
        response.status,
        data.error.context,
        data.request_id
      );
    }
    const message = data.detail || data.message || `HTTP ${response.status}`;
    const code = mapStatusToErrorCode(response.status);
    return new ApiError(message, code, response.status);
  }
  if (error.message) {
    return new ApiError(
      error.message,
      ERROR_CODES.INTERNAL_SERVER_ERROR,
      0
    );
  }
  return new ApiError(
    "未知错误，请稍后重试",
    ERROR_CODES.INTERNAL_SERVER_ERROR,
    0
  );
}
function getUserFriendlyMessage(error) {
  const apiError = parseApiError(error);
  if (apiError.message && apiError.message !== apiError.code) {
    return apiError.message;
  }
  return ERROR_MESSAGES[apiError.code] || "未知错误，请稍后重试";
}
function mapStatusToErrorCode(status) {
  const mapping = {
    400: ERROR_CODES.BAD_REQUEST,
    401: ERROR_CODES.AUTHENTICATION_ERROR,
    403: ERROR_CODES.AUTHORIZATION_ERROR,
    404: ERROR_CODES.NOT_FOUND,
    409: ERROR_CODES.CONFLICT,
    422: ERROR_CODES.VALIDATION_ERROR,
    500: ERROR_CODES.INTERNAL_SERVER_ERROR
  };
  return mapping[status] || ERROR_CODES.INTERNAL_SERVER_ERROR;
}
class ErrorHandler {
  /**
   * 处理API错误
   * @param {Error} error - 原始错误对象
   * @param {Object} options - 处理选项
   * @returns {ApiError} 处理后的错误对象
   */
  static handleApiError(error, options = {}) {
    const { showNotification = true, logError = true } = options;
    const apiError = parseApiError(error);
    if (logError) {
      console.error("API Error:", {
        message: apiError.message,
        code: apiError.code,
        status: apiError.status,
        context: apiError.context,
        requestId: apiError.requestId
      });
    }
    if (showNotification && typeof window !== "undefined") {
      console.warn("Error notification:", getUserFriendlyMessage(apiError));
    }
    return apiError;
  }
  /**
   * 处理表单验证错误
   * @param {ApiError} error - API错误对象
   * @returns {Object} 字段错误映射
   */
  static handleValidationError(error) {
    const errors = {};
    if (error.code === ERROR_CODES.VALIDATION_ERROR && error.context?.validation_errors) {
      error.context.validation_errors.forEach((validationError) => {
        errors[validationError.field] = validationError.message;
      });
    }
    return errors;
  }
  /**
   * 检查是否需要重新登录
   * @param {ApiError} error - API错误对象
   * @returns {boolean} 是否需要重新登录
   */
  static needsReauth(error) {
    return error.code === ERROR_CODES.AUTHENTICATION_ERROR;
  }
  /**
   * 检查是否应该重试请求
   * @param {ApiError} error - API错误对象
   * @returns {boolean} 是否应该重试
   */
  static shouldRetry(error) {
    return error.status >= 500 || error.status === 0;
  }
}
const API_BASE_URL = PUBLIC_API_BASE_URL;
class ApiClient {
  constructor() {
    this.baseUrl = API_BASE_URL;
  }
  // ================== Authentication helpers ==================
  getToken() {
    return null;
  }
  setToken(token) {
    return;
  }
  clearToken() {
    return;
  }
  async handleTokenExpired() {
    return { success: false, error: "Not in browser environment" };
  }
  // ================== Base request method ==================
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      headers: {
        ...options.headers
      },
      ...options
    };
    if (!(config.body instanceof FormData)) {
      config.headers["Content-Type"] = "application/json";
    }
    const token = this.getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    if (config.body && typeof config.body === "object" && !(config.body instanceof FormData)) {
      config.body = JSON.stringify(config.body);
    }
    try {
      const response = await fetch(url, config);
      if (response.status === 401) {
        const refreshResult = await this.handleTokenExpired();
        if (refreshResult.success) {
          const retryConfig = {
            ...config,
            headers: {
              ...config.headers,
              Authorization: `Bearer ${localStorage.getItem("authToken")}`
            }
          };
          return await fetch(url, retryConfig);
        } else {
          this.clearToken();
          if (browser)
            ;
          const authError = new Error("Authentication required");
          authError.response = { status: 401, data: {} };
          throw authError;
        }
      }
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error = new Error(
          errorData.error?.message || errorData.message || `HTTP ${response.status}`
        );
        error.response = {
          status: response.status,
          data: errorData
        };
        throw error;
      }
      return await response.json();
    } catch (error) {
      const apiError = ErrorHandler.handleApiError(error, {
        showNotification: false,
        // 在API层不显示通知，让组件层处理
        logError: true
      });
      if (ErrorHandler.needsReauth(apiError)) {
        this.clearToken();
      }
      throw apiError;
    }
  }
  // Upload file helper with progress support
  async uploadFile(endpoint, file, onProgress = null) {
    const formData = new FormData();
    formData.append("file", file);
    return this.uploadFormData(endpoint, formData, onProgress);
  }
  // Generic upload with progress support using XMLHttpRequest
  async uploadFormData(endpoint, formData, onProgress = null) {
    const url = `${this.baseUrl}${endpoint}`;
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      if (onProgress && typeof onProgress === "function") {
        xhr.upload.addEventListener("progress", (event) => {
          if (event.lengthComputable) {
            const progress = Math.round(event.loaded / event.total * 100);
            onProgress(progress);
          }
        });
      }
      xhr.onload = async () => {
        try {
          if (xhr.status === 401) {
            const refreshResult = await this.handleTokenExpired();
            if (refreshResult.success) {
              console.log("Token refreshed, please retry your upload");
              reject(new Error("Token was refreshed, please retry the upload"));
            } else {
              if (browser)
                ;
              reject(new Error("Authentication required"));
            }
            return;
          }
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const data = JSON.parse(xhr.responseText);
              resolve({
                success: true,
                data,
                status: xhr.status
              });
            } catch {
              resolve({
                success: true,
                data: { content: xhr.responseText },
                status: xhr.status
              });
            }
          } else {
            let errorData;
            try {
              errorData = JSON.parse(xhr.responseText);
            } catch {
              errorData = { message: xhr.statusText };
            }
            resolve({
              success: false,
              error: errorData?.detail || errorData?.message || `HTTP ${xhr.status}`,
              status: xhr.status
            });
          }
        } catch (error) {
          resolve({
            success: false,
            error: error.message || "请求失败",
            status: xhr.status
          });
        }
      };
      xhr.onerror = () => {
        resolve({
          success: false,
          error: "网络错误，请检查连接",
          status: 0
        });
      };
      xhr.ontimeout = () => {
        resolve({
          success: false,
          error: "请求超时",
          status: 0
        });
      };
      xhr.open("POST", url);
      xhr.timeout = 3e5;
      const token = this.getToken();
      if (token) {
        xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      }
      xhr.send(formData);
    });
  }
  // ================== Authentication API ==================
  async mockExternalAuth(email, password) {
    try {
      const response = await this.request("/api/auth/mock-external-auth", {
        method: "POST",
        body: { email, password }
      });
      return { success: true, data: response };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
  async login(externalToken) {
    try {
      const response = await this.request("/api/auth/login", {
        method: "POST",
        body: { external_token: externalToken }
      });
      if (response.access_token) {
        this.setToken(response.access_token);
      }
      return { success: true, data: response };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
  async register(email, password, username = null, fullName = null) {
    try {
      const response = await this.request("/api/auth/register", {
        method: "POST",
        body: {
          email,
          password,
          username,
          full_name: fullName
        }
      });
      if (response.access_token) {
        this.setToken(response.access_token);
      }
      return { success: true, data: response };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
  async loginWithCredentials(email, password) {
    try {
      const response = await this.request("/api/auth/login/credentials", {
        method: "POST",
        body: { email, password }
      });
      if (response.access_token) {
        this.setToken(response.access_token);
      }
      return { success: true, data: response };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
  async verify() {
    try {
      const response = await this.request("/api/auth/verify", {
        method: "POST"
      });
      return { success: true, data: response };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
  async logout() {
    try {
      await this.request("/api/auth/logout", {
        method: "POST",
        body: { token: this.getToken() }
      });
      this.clearToken();
      return { success: true };
    } catch (error) {
      this.clearToken();
      return { success: false, error: error.message };
    }
  }
  async getCurrentUser() {
    try {
      const response = await this.request("/api/auth/me");
      return { success: true, data: response };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
  async refreshToken(refreshToken) {
    try {
      const response = await this.request("/api/auth/refresh", {
        method: "POST",
        body: { refresh_token: refreshToken }
      });
      this.setToken(response.access_token);
      return { success: true, data: response };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
  // ================== Search API ==================
  async searchRepositories(query, options = {}) {
    const params = new URLSearchParams({
      q: query,
      ...options
    });
    return this.request(`/api/search/repositories?${params}`);
  }
  async searchUsers(query, options = {}) {
    const params = new URLSearchParams({
      q: query,
      ...options
    });
    return this.request(`/api/search/users?${params}`);
  }
  async getTrending(options = {}) {
    const params = new URLSearchParams(options);
    return this.request(`/api/search/trending?${params}`);
  }
  async getSearchSuggestions(query, options = {}) {
    const params = new URLSearchParams({
      q: query,
      ...options
    });
    return this.request(`/api/search/suggestions?${params}`);
  }
  async getSearchStats() {
    return this.request("/api/search/stats");
  }
  // ================== Users API ==================
  async getUserByUsername(username) {
    return this.request(`/api/users/${username}`);
  }
  async getUserRepositoriesByUsername(username, options = {}) {
    const params = new URLSearchParams(options);
    return this.request(`/api/users/${username}/repositories?${params}`);
  }
  async getUserFollowers(username, options = {}) {
    const params = new URLSearchParams(options);
    return this.request(`/api/users/${username}/followers?${params}`);
  }
  async getUserFollowing(username, options = {}) {
    const params = new URLSearchParams(options);
    return this.request(`/api/users/${username}/following?${params}`);
  }
  async followUserByUsername(username) {
    return this.request(`/api/users/${username}/follow`, {
      method: "POST"
    });
  }
  async unfollowUserByUsername(username) {
    return this.request(`/api/users/${username}/follow`, {
      method: "DELETE"
    });
  }
  async getUserStatsByUsername(username) {
    return this.request(`/api/users/${username}/stats`);
  }
  async getUserStarredRepositories(username, params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== void 0 && value !== null && value !== "") {
        searchParams.append(key, value);
      }
    });
    return this.request(`/api/users/${username}/starred?${searchParams}`);
  }
  async getUserStorage(username) {
    return this.request(`/api/users/${username}/storage`);
  }
  // ================== Repositories API ==================
  async listRepositories(options = {}) {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(options)) {
      if (value === void 0 || value === null) {
        continue;
      }
      if (Array.isArray(value)) {
        value.forEach((item) => {
          if (item !== void 0 && item !== null) {
            params.append(key, item);
          }
        });
      } else {
        params.append(key, value);
      }
    }
    return this.request(`/api/repositories/?${params}`);
  }
  async getRepository(owner, name) {
    return this.request(`/api/repositories/${owner}/${name}`);
  }
  async createRepository(data) {
    return this.request("/api/repositories", {
      method: "POST",
      body: data
    });
  }
  async createRepositoryWithReadme(formData) {
    return this.request("/api/repositories/with-readme", {
      method: "POST",
      body: formData
    });
  }
  async updateRepository(owner, name, data) {
    return this.request(`/api/repositories/${owner}/${name}`, {
      method: "PUT",
      body: data
    });
  }
  async deleteRepository(owner, name) {
    return this.request(`/api/repositories/${owner}/${name}`, {
      method: "DELETE"
    });
  }
  async getRepositoryFiles(owner, name, path = "") {
    const params = new URLSearchParams({ path });
    return this.request(`/api/repositories/${owner}/${name}/files?${params}`);
  }
  async getRepositoryFileContent(owner, name, filePath) {
    return this.request(`/api/repositories/${owner}/${name}/blob/${encodeURIComponent(filePath)}`);
  }
  async starRepository(owner, name) {
    return this.request(`/api/repositories/${owner}/${name}/star`, {
      method: "POST"
    });
  }
  async unstarRepository(owner, name) {
    return this.request(`/api/repositories/${owner}/${name}/star`, {
      method: "DELETE"
    });
  }
  async getRepositoryTrend(owner, name, params = {}) {
    const searchParams = new URLSearchParams();
    const endDate = params.end_date || (/* @__PURE__ */ new Date()).toISOString().split("T")[0];
    const startDate = params.start_date || (() => {
      const date = /* @__PURE__ */ new Date();
      date.setDate(date.getDate() - 30);
      return date.toISOString().split("T")[0];
    })();
    searchParams.append("start_date", startDate);
    searchParams.append("end_date", endDate);
    searchParams.append("interval", params.interval || "daily");
    return this.request(`/api/repositories/${owner}/${name}/stats/trend?${searchParams}`);
  }
  async getRepositoryStars(owner, name, options = {}) {
    const params = new URLSearchParams(options);
    return this.request(`/api/repositories/${owner}/${name}/stars?${params}`);
  }
  async getRepositoryStats(owner, name) {
    return this.request(`/api/repositories/${owner}/${name}/stats`);
  }
  async incrementRepositoryView(owner, name) {
    return this.request(`/api/repositories/${owner}/${name}/view`, {
      method: "POST"
    });
  }
  async checkUploadConflict(owner, name, fileName) {
    const filePath = encodeURIComponent(fileName);
    return this.request(`/api/repositories/${owner}/${name}/check-upload?file_path=${filePath}`, {
      method: "POST"
    });
  }
  async uploadRepositoryFile(owner, name, file, options = {}) {
    const { onProgress = null, confirmed = false } = options;
    const filePath = encodeURIComponent(file.name);
    const confirmParam = confirmed ? "&confirmed=true" : "";
    return this.uploadFile(
      `/api/repositories/${owner}/${name}/upload?file_path=${filePath}${confirmParam}`,
      file,
      onProgress
    );
  }
  async getDownloadUrl(owner, name, filePath) {
    const response = await fetch(
      `${this.baseUrl}/api/repositories/${owner}/${name}/download/${filePath}`,
      {
        headers: {
          Authorization: `Bearer ${this.getToken()}`
        }
      }
    );
    if (!response.ok) {
      throw new Error(`Download failed: ${response.status}`);
    }
    return response.json();
  }
  async deleteFile(fileId) {
    return this.request(`/api/files/${fileId}`, {
      method: "DELETE"
    });
  }
  // ================== Services API ==================
  async getRepositoryServices(owner, name, params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== void 0 && value !== null && value !== "") {
        searchParams.append(key, value);
      }
    });
    return this.request(`/api/services/servicelists/${owner}/${name}?${searchParams}`);
  }
  async createService(owner, name, data, onProgress = null) {
    if (data instanceof FormData) {
      return this.uploadFormData(
        `/api/services/${owner}/${name}/create_service_from_image`,
        data,
        onProgress
      );
    }
    return this.request(`/api/services/${owner}/${name}/create_service_from_image`, {
      method: "POST",
      body: data
    });
  }
  async createServiceWithDockerTar(owner, name, formData, onProgress = null) {
    return this.uploadFormData(
      `/api/services/${owner}/${name}/create_service_with_docker_tar`,
      formData,
      onProgress
    );
  }
  async getService(serviceId) {
    return this.request(`/api/services/${serviceId}`);
  }
  async updateService(serviceId, data) {
    return this.request(`/api/services/${serviceId}`, {
      method: "PUT",
      body: data
    });
  }
  async deleteService(serviceId) {
    return this.request(`/api/services/${serviceId}`, {
      method: "DELETE"
    });
  }
  async startService(serviceId, data = { force_restart: false }) {
    return this.request(`/api/services/${serviceId}/start`, {
      method: "POST",
      body: data
    });
  }
  async stopService(serviceId, data = {}) {
    return this.request(`/api/services/${serviceId}/stop`, {
      method: "POST",
      body: data
    });
  }
  async restartService(serviceId) {
    return this.request(`/api/services/${serviceId}/restart`, {
      method: "POST"
    });
  }
  async getServiceStatus(serviceId) {
    return this.request(`/api/services/${serviceId}/status`);
  }
  async getServiceLogs(serviceId, params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== void 0 && value !== null && value !== "") {
        searchParams.append(key, value);
      }
    });
    return this.request(`/api/services/${serviceId}/logs?${searchParams}`);
  }
  async getServiceHealth(serviceId) {
    return this.request(`/api/services/${serviceId}/health`);
  }
  async triggerHealthCheck(serviceId) {
    return this.request(`/api/services/${serviceId}/health-check`, {
      method: "POST"
    });
  }
  async getServiceMetrics(serviceId) {
    return this.request(`/api/services/${serviceId}/metrics`);
  }
  async getServiceResourceUsage(serviceId) {
    return this.request(`/api/services/${serviceId}/resource-usage`);
  }
  async getServiceDemo(serviceId) {
    return this.request(`/api/services/${serviceId}/demo`);
  }
  async generateAccessToken(serviceId, data) {
    return this.request(`/api/services/${serviceId}/access-token`, {
      method: "POST",
      body: data
    });
  }
  async updateServiceVisibility(serviceId, data) {
    return this.request(`/api/services/${serviceId}/visibility`, {
      method: "PUT",
      body: data
    });
  }
  async updateServiceFiles(serviceId, formData) {
    return this.request(`/api/services/${serviceId}/files/update`, {
      method: "POST",
      body: formData
    });
  }
  async getServiceContainerInfo(serviceId) {
    return this.request(`/api/services/${serviceId}/container-info`);
  }
  async validateServiceEnvironment(serviceId) {
    return this.request(`/api/services/${serviceId}/validate-environment`, {
      method: "POST"
    });
  }
  // Batch service operations
  async batchStartServices(owner, name, serviceIds) {
    return this.request(`/api/services/${owner}/${name}/batch/start`, {
      method: "POST",
      body: { service_ids: serviceIds }
    });
  }
  async batchStopServices(owner, name, serviceIds) {
    return this.request(`/api/services/${owner}/${name}/batch/stop`, {
      method: "POST",
      body: { service_ids: serviceIds }
    });
  }
  async batchDeleteServices(owner, name, serviceIds) {
    return this.request(`/api/services/${owner}/${name}/batch`, {
      method: "DELETE",
      body: { service_ids: serviceIds }
    });
  }
  // Admin service endpoints
  async getServicesHealthSummary() {
    return this.request("/api/services/health-summary");
  }
  async getServiceStatistics() {
    return this.request("/api/services/admin/statistics");
  }
  async getServicesOverview() {
    return this.request("/api/services/admin/overview");
  }
  async performSystemMaintenance(data = {}) {
    return this.request("/api/services/admin/maintenance", {
      method: "POST",
      body: data
    });
  }
  // ================== Images API ==================
  async getRepositoryImages(repositoryId) {
    return this.request(`/api/images/repositories/${repositoryId}`);
  }
  async uploadImage(repositoryId, formData, onProgress = null) {
    return this.uploadFormData(
      `/api/images/repositories/${repositoryId}/upload`,
      formData,
      onProgress
    );
  }
  async deleteImage(imageId, force = false) {
    return this.request(`/api/images/${imageId}?force=${force}`, {
      method: "DELETE"
    });
  }
  async getImageServices(imageId) {
    return this.request(`/api/images/${imageId}/services`);
  }
  async createServiceFromImage(imageId, formData) {
    return this.request(`/api/images/${imageId}/services/create`, {
      method: "POST",
      body: formData
    });
  }
  async getImageBuildLogs(imageId, limit = 100) {
    return this.request(`/api/images/${imageId}/build-logs?limit=${limit}`);
  }
  // ================== Notifications API ==================
  async getNotifications(params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== void 0 && value !== null && value !== "") {
        searchParams.append(key, value);
      }
    });
    return this.request(`/api/notifications?${searchParams}`);
  }
  async getUnreadNotificationsCount() {
    return this.request("/api/notifications/unread/count");
  }
  async markNotificationAsRead(id) {
    return this.request(`/api/notifications/${id}/read`, {
      method: "POST"
    });
  }
  async markAllNotificationsAsRead() {
    return this.request("/api/notifications/read-all", {
      method: "POST"
    });
  }
  async deleteNotification(id) {
    return this.request(`/api/notifications/${id}`, {
      method: "DELETE"
    });
  }
  // ================== Comments API ==================
  async getComments(resourceType, resourceId, params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== void 0 && value !== null && value !== "") {
        searchParams.append(key, value);
      }
    });
    return this.request(`/api/comments/${resourceType}/${resourceId}?${searchParams}`);
  }
  async createComment(resourceType, resourceId, data) {
    return this.request(`/api/comments/${resourceType}/${resourceId}`, {
      method: "POST",
      body: data
    });
  }
  async updateComment(id, data) {
    return this.request(`/api/comments/${id}`, {
      method: "PUT",
      body: data
    });
  }
  async deleteComment(id) {
    return this.request(`/api/comments/${id}`, {
      method: "DELETE"
    });
  }
  async likeComment(id) {
    return this.request(`/api/comments/${id}/like`, {
      method: "POST"
    });
  }
  async unlikeComment(id) {
    return this.request(`/api/comments/${id}/like`, {
      method: "DELETE"
    });
  }
  // ================== Activities API ==================
  async getActivities(params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== void 0 && value !== null && value !== "") {
        searchParams.append(key, value);
      }
    });
    return this.request(`/api/activities?${searchParams}`);
  }
  // ================== Classifications API ==================
  async getClassificationTree() {
    return this.request("/api/classifications/tree");
  }
  // ================== File Editing API ==================
  /**
   * 更新文件内容
   * @param {string} username - 用户名
   * @param {string} repositoryName - 仓库名
   * @param {string} filePath - 文件路径
   * @param {string} content - 文件内容
   * @param {string} commitMessage - 提交信息
   */
  async updateFileContent(username, repositoryName, filePath, content, commitMessage) {
    return this.request(`/api/repositories/${username}/${repositoryName}/blob/${filePath}`, {
      method: "PUT",
      body: {
        content,
        commit_message: commitMessage
      }
    });
  }
  /**
   * 重命名文件
   * @param {string} username - 用户名
   * @param {string} repositoryName - 仓库名
   * @param {string} oldPath - 旧文件路径
   * @param {string} newFilename - 新文件名
   * @param {string} commitMessage - 提交信息
   */
  async renameRepositoryFile(username, repositoryName, oldPath, newFilename, commitMessage) {
    return this.request(`/api/repositories/${username}/${repositoryName}/files/rename`, {
      method: "POST",
      body: {
        old_path: oldPath,
        new_filename: newFilename,
        commit_message: commitMessage
      }
    });
  }
  // ================== Admin API ==================
  async getAdminDashboard() {
    return this.request("/api/admin/dashboard");
  }
  async getAdminUsers(params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== void 0 && value !== null && value !== "") {
        searchParams.append(key, value);
      }
    });
    return this.request(`/api/admin/users?${searchParams}`);
  }
  async updateAdminUserStatus(userId, data) {
    const params = new URLSearchParams();
    Object.entries(data).forEach(([key, value]) => {
      if (value !== void 0 && value !== null) {
        params.append(key, value);
      }
    });
    return this.request(`/api/admin/users/${userId}/status?${params}`, {
      method: "PUT"
    });
  }
  async getAdminRepositories(params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== void 0 && value !== null && value !== "") {
        searchParams.append(key, value);
      }
    });
    return this.request(`/api/admin/repositories?${searchParams}`);
  }
  async getAdminRepositoryStats() {
    return this.request("/api/admin/repositories/stats");
  }
  async updateAdminRepositoryStatus(repositoryId, data) {
    const params = new URLSearchParams();
    Object.entries(data).forEach(([key, value]) => {
      if (value !== void 0 && value !== null) {
        params.append(key, value);
      }
    });
    return this.request(`/api/admin/repositories/${repositoryId}/status?${params}`, {
      method: "PUT"
    });
  }
  async restoreAdminRepository(repositoryId) {
    return this.request(`/api/admin/repositories/${repositoryId}/restore`, {
      method: "POST"
    });
  }
  async hardDeleteAdminRepository(repositoryId, confirm = false) {
    return this.request(`/api/admin/repositories/${repositoryId}/hard-delete?confirm=${confirm}`, {
      method: "DELETE"
    });
  }
  async getAdminStorageStats() {
    return this.request("/api/admin/storage/stats");
  }
  async performAdminStorageCleanup(options = {}) {
    const params = new URLSearchParams();
    Object.entries(options).forEach(([key, value]) => {
      if (value !== void 0 && value !== null) {
        params.append(key, value);
      }
    });
    return this.request(`/api/admin/storage/cleanup?${params}`, {
      method: "POST"
    });
  }
  async getAdminSystemHealth() {
    return this.request("/api/admin/system/health");
  }
  async getAdminSystemLogs(params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== void 0 && value !== null && value !== "") {
        searchParams.append(key, value);
      }
    });
    return this.request(`/api/admin/logs?${searchParams}`);
  }
  async getAdminSystemConfig() {
    return this.request("/api/admin/system/config");
  }
  async getAdminSystemInfo() {
    return this.request("/api/admin/system/info");
  }
  async updateAdminSystemConfig(config) {
    return this.request("/api/admin/system/config", {
      method: "PUT",
      body: config
    });
  }
  async setAdminMaintenanceMode(enabled, message = "") {
    return this.request("/api/admin/system/maintenance", {
      method: "POST",
      body: { enabled, message }
    });
  }
  // Repository classification management
  repositories = {
    // Add sphere classification to repository
    addClassification: async (owner, repoName, classificationId) => {
      return this.request(
        `/api/repositories/${owner}/${repoName}/classifications?classification_id=${classificationId}`,
        {
          method: "POST"
        }
      );
    },
    // Remove all sphere classifications from repository
    removeClassifications: async (owner, repoName) => {
      return this.request(`/api/repositories/${owner}/${repoName}/classifications`, {
        method: "DELETE"
      });
    },
    // Add task classification to repository
    addTaskClassification: async (owner, repoName, taskClassificationId) => {
      return this.request(
        `/api/repositories/${owner}/${repoName}/task-classifications?task_classification_id=${taskClassificationId}`,
        {
          method: "POST"
        }
      );
    },
    // Remove task classification from repository
    removeTaskClassification: async (owner, repoName, taskClassificationId) => {
      return this.request(
        `/api/repositories/${owner}/${repoName}/task-classifications/${taskClassificationId}`,
        {
          method: "DELETE"
        }
      );
    },
    // Get repository task classifications
    getTaskClassifications: async (owner, repoName) => {
      return this.request(`/api/repositories/${owner}/${repoName}/task-classifications`);
    }
  };
}
const api = new ApiClient();
const Arrow_down_wide_narrow = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["path", { "d": "m3 16 4 4 4-4" }],
    ["path", { "d": "M7 20V4" }],
    ["path", { "d": "M11 4h10" }],
    ["path", { "d": "M11 8h7" }],
    ["path", { "d": "M11 12h4" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "arrow-down-wide-narrow" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const SortDesc = Arrow_down_wide_narrow;
const Arrow_up_narrow_wide = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["path", { "d": "m3 8 4-4 4 4" }],
    ["path", { "d": "M7 4v16" }],
    ["path", { "d": "M11 12h4" }],
    ["path", { "d": "M11 16h7" }],
    ["path", { "d": "M11 20h10" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "arrow-up-narrow-wide" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const SortAsc = Arrow_up_narrow_wide;
const Chevron_left = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [["path", { "d": "m15 18-6-6 6-6" }]];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "chevron-left" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const ChevronLeft = Chevron_left;
const Chevron_right = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [["path", { "d": "m9 18 6-6-6-6" }]];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "chevron-right" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const ChevronRight = Chevron_right;
const Grid_3x3 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "rect",
      {
        "width": "18",
        "height": "18",
        "x": "3",
        "y": "3",
        "rx": "2"
      }
    ],
    ["path", { "d": "M3 9h18" }],
    ["path", { "d": "M3 15h18" }],
    ["path", { "d": "M9 3v18" }],
    ["path", { "d": "M15 3v18" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "grid-3x3" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Grid = Grid_3x3;
const List = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "line",
      {
        "x1": "8",
        "x2": "21",
        "y1": "6",
        "y2": "6"
      }
    ],
    [
      "line",
      {
        "x1": "8",
        "x2": "21",
        "y1": "12",
        "y2": "12"
      }
    ],
    [
      "line",
      {
        "x1": "8",
        "x2": "21",
        "y1": "18",
        "y2": "18"
      }
    ],
    [
      "line",
      {
        "x1": "3",
        "x2": "3.01",
        "y1": "6",
        "y2": "6"
      }
    ],
    [
      "line",
      {
        "x1": "3",
        "x2": "3.01",
        "y1": "12",
        "y2": "12"
      }
    ],
    [
      "line",
      {
        "x1": "3",
        "x2": "3.01",
        "y1": "18",
        "y2": "18"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "list" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const List$1 = List;
const Lock = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "rect",
      {
        "width": "18",
        "height": "11",
        "x": "3",
        "y": "11",
        "rx": "2",
        "ry": "2"
      }
    ],
    ["path", { "d": "M7 11V7a5 5 0 0 1 10 0v4" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "lock" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Lock$1 = Lock;
const User = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"
      }
    ],
    ["circle", { "cx": "12", "cy": "7", "r": "4" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "user" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const User$1 = User;
const UserAvatar = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let sizeClasses;
  let iconSizeClasses;
  let textSizeClasses;
  let userInitials;
  let userColor;
  let { user: user2 = null } = $$props;
  let { size = "md" } = $$props;
  let { showName = false } = $$props;
  let { showUsername = false } = $$props;
  let { clickable = true } = $$props;
  const sizeClassMap = {
    xs: "h-5 w-5",
    sm: "h-7 w-7",
    md: "h-9 w-9",
    lg: "h-11 w-11",
    xl: "h-14 w-14"
  };
  const iconSizeClassMap = {
    xs: "h-3 w-3",
    sm: "h-4 w-4",
    md: "h-5 w-5",
    lg: "h-6 w-6",
    xl: "h-8 w-8"
  };
  const textSizeClassMap = {
    xs: "text-xs",
    sm: "text-sm",
    md: "text-base",
    lg: "text-lg",
    xl: "text-xl"
  };
  const colors = [
    "bg-red-500",
    "bg-yellow-500",
    "bg-green-500",
    "bg-blue-500",
    "bg-indigo-500",
    "bg-purple-500",
    "bg-pink-500",
    "bg-orange-500",
    "bg-teal-500",
    "bg-cyan-500"
  ];
  let imageError = false;
  if ($$props.user === void 0 && $$bindings.user && user2 !== void 0)
    $$bindings.user(user2);
  if ($$props.size === void 0 && $$bindings.size && size !== void 0)
    $$bindings.size(size);
  if ($$props.showName === void 0 && $$bindings.showName && showName !== void 0)
    $$bindings.showName(showName);
  if ($$props.showUsername === void 0 && $$bindings.showUsername && showUsername !== void 0)
    $$bindings.showUsername(showUsername);
  if ($$props.clickable === void 0 && $$bindings.clickable && clickable !== void 0)
    $$bindings.clickable(clickable);
  sizeClasses = sizeClassMap[size] || sizeClassMap.md;
  iconSizeClasses = iconSizeClassMap[size] || iconSizeClassMap.md;
  textSizeClasses = textSizeClassMap[size] || textSizeClassMap.md;
  userInitials = user2?.full_name ? user2.full_name.split(" ").map((word) => word.charAt(0)).join("").toUpperCase().slice(0, 2) : user2?.username?.charAt(0).toUpperCase() || "";
  userColor = user2?.username ? (() => {
    let hash = 0;
    for (let i = 0; i < user2.username.length; i++) {
      hash = user2.username.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
  })() : "bg-gray-500";
  return `<div class="flex items-center space-x-2"> <div class="relative">${clickable && user2 ? `<a href="${escape(base, true) + "/" + escape(user2.username, true)}" class="block"><div class="${"relative " + escape(sizeClasses, true) + " rounded-lg overflow-hidden bg-gray-200 dark:bg-gray-700 flex items-center justify-center"}">${user2?.avatar_url && !imageError ? ` <div class="h-full w-full relative">${` <div class="${"h-full w-full flex items-center justify-center text-white font-semibold " + escape(userColor, true) + " " + escape(textSizeClasses, true)}">${escape(userInitials)}</div>`} <img${add_attribute("src", user2.avatar_url, 0)}${add_attribute("alt", user2.full_name || user2.username, 0)} class="${"h-full w-full object-cover " + escape("opacity-0", true) + " transition-opacity duration-200"}" loading="lazy"></div>` : `${user2 ? ` <div class="${"h-full w-full flex items-center justify-center text-white font-semibold " + escape(userColor, true) + " " + escape(textSizeClasses, true)}">${escape(userInitials)}</div>` : ` ${validate_component(User$1, "User").$$render(
    $$result,
    {
      class: "text-gray-500 dark:text-gray-400 " + iconSizeClasses
    },
    {},
    {}
  )}`}`}</div></a>` : `<div class="${"relative " + escape(sizeClasses, true) + " rounded-lg overflow-hidden bg-gray-200 dark:bg-gray-700 flex items-center justify-center"}">${user2?.avatar_url && !imageError ? ` <div class="h-full w-full relative">${` <div class="${"h-full w-full flex items-center justify-center text-white font-semibold " + escape(userColor, true) + " " + escape(textSizeClasses, true)}">${escape(userInitials)}</div>`} <img${add_attribute("src", user2.avatar_url, 0)}${add_attribute("alt", user2.full_name || user2.username, 0)} class="${"h-full w-full object-cover " + escape("opacity-0", true) + " transition-opacity duration-200"}" loading="lazy"></div>` : `${user2 ? ` <div class="${"h-full w-full flex items-center justify-center text-white font-semibold " + escape(userColor, true) + " " + escape(textSizeClasses, true)}">${escape(userInitials)}</div>` : ` ${validate_component(User$1, "User").$$render(
    $$result,
    {
      class: "text-gray-500 dark:text-gray-400 " + iconSizeClasses
    },
    {},
    {}
  )}`}`}</div>`}</div>  ${(showName || showUsername) && user2 ? `<div class="flex flex-col">${showName && user2.full_name ? `<span class="${"font-medium text-gray-900 dark:text-white " + escape(textSizeClasses, true)}">${escape(user2.full_name)}</span>` : ``} ${showUsername ? `<span class="${"text-gray-500 dark:text-gray-400 " + escape(size === "xs" ? "text-xs" : "text-sm", true)}">@${escape(user2.username)}</span>` : ``}</div>` : ``}</div>`;
});
const css = {
  code: ".repository-card.svelte-1z00mnd{background:linear-gradient(to right, var(--color-gray-100), var(--color-white))}.repository-card.svelte-1z00mnd:hover{background:linear-gradient(to right, var(--color-gray-200), var(--color-gray-50));box-shadow:var(--tw-shadow-hover);cursor:pointer}.line-clamp-2.svelte-1z00mnd{display:-webkit-box;-webkit-line-clamp:2;line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.line-clamp-3.svelte-1z00mnd{display:-webkit-box;-webkit-line-clamp:3;line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}",
  map: null
};
function formatFileSize(bytes) {
  if (bytes === 0)
    return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}
const RepositoryCard = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { repo } = $$props;
  let { currentUser = null } = $$props;
  let { showOwner = true } = $$props;
  let { compact = false } = $$props;
  console.log(repo);
  if ($$props.repo === void 0 && $$bindings.repo && repo !== void 0)
    $$bindings.repo(repo);
  if ($$props.currentUser === void 0 && $$bindings.currentUser && currentUser !== void 0)
    $$bindings.currentUser(currentUser);
  if ($$props.showOwner === void 0 && $$bindings.showOwner && showOwner !== void 0)
    $$bindings.showOwner(showOwner);
  if ($$props.compact === void 0 && $$bindings.compact && compact !== void 0)
    $$bindings.compact(compact);
  $$result.css.add(css);
  return `<div class="repository-card group rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 transition-all duration-200 svelte-1z00mnd"><div class="flex items-start justify-between"><div class="flex-1 min-w-0"> <div class="flex items-center mb-2">${showOwner && repo.owner ? `${validate_component(UserAvatar, "UserAvatar").$$render($$result, { user: repo.owner, size: "sm" }, {}, {})} <span class="text-lg font-mono text-black ml-3 truncate group-hover:text-blue-500 transition-colors">${escape(repo.owner.username)}</span> <span class="text-lg font-mono text-black truncate group-hover:text-blue-500 transition-colors" data-svelte-h="svelte-1yxvov6">/</span>` : ``} <a href="${escape(base, true) + "/" + escape(repo.owner?.username || "unknown", true) + "/" + escape(repo.name, true)}" class="text-lg font-mono text-black truncate group-hover:text-blue-500 transition-colors">${escape(repo.name)}</a> ${repo.visibility === "private" ? `${validate_component(Lock$1, "Lock").$$render($$result, { class: "h-4 w-4 text-gray-400" }, {}, {})}` : ``}</div>  ${repo.description ? `<p class="${"text-gray-700 dark:text-gray-300 text-sm mb-3 " + escape(compact ? "line-clamp-2" : "line-clamp-3", true) + " svelte-1z00mnd"}">${escape(repo.description)}</p>` : ``}</div></div>  <div class="flex items-center justify-between gap-4"> <div class="flex items-center gap-2 flex-wrap flex-1 min-w-0"> ${repo.task_classifications_data && repo.task_classifications_data.length > 0 ? `${each(repo.task_classifications_data, (task) => {
    return `<span class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-purple-50 text-purple-700 border border-purple-100 dark:bg-purple-950 dark:text-purple-300 dark:border-purple-900 shadow-sm">${escape(task.name)} </span>`;
  })}` : ``}  ${repo.classification_path && repo.classification_path.length > 0 ? `<div class="flex items-center">${each(repo.classification_path, (classification, index) => {
    return `<span class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-blue-50 text-blue-700 border border-blue-100 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-900 dark:hover:bg-blue-900 shadow-sm">${escape(classification)}</span> ${index < repo.classification_path.length - 1 ? `${validate_component(ChevronRight, "ChevronRight").$$render(
      $$result,
      {
        class: "h-4 w-4 font-medium text-gray-900"
      },
      {},
      {}
    )}` : ``}`;
  })}</div>` : ``}  ${repo.license ? `<span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-green-50 hover:bg-green-100 transition-colors duration-200 dark:bg-green-950 dark:hover:bg-green-900 shadow-sm border border-green-100 dark:border-green-900"><svg class="w-3 h-3 text-gray-500 dark:text-gray-400" fill="currentColor" viewBox="0 0 16 16"><path d="M8.75.75V2h.985c.304 0 .603.08.867.231l1.29.736c.038.022.08.033.124.033h2.234a.75.75 0 0 1 0 1.5h-.427l2.111 4.692a.75.75 0 0 1-.154.838l-.53-.53.529.531-.001.002-.002.002-.006.006-.006.005-.01.01-.045.04c-.21.176-.441.327-.686.45C14.556 10.78 13.88 11 13 11a4.498 4.498 0 0 1-2.023-.454 3.544 3.544 0 0 1-.686-.45l-.045-.04-.016-.015-.006-.006-.004-.004v-.001a.75.75 0 0 1-.154-.838L12.178 4.5h-.162c-.305 0-.604-.079-.868-.231l-1.29-.736a.245.245 0 0 0-.124-.033H8.75V13h2.5a.75.75 0 0 1 0 1.5h-6.5a.75.75 0 0 1 0-1.5h2.5V3.5h-.984a.245.245 0 0 0-.124.033l-1.289.737c-.265.15-.564.23-.869.23h-.162l2.112 4.692a.75.75 0 0 1-.154.838l-.53-.53.529.531-.001.002-.002.002-.006.006-.016.015-.045.04c-.21.176-.441.327-.686.45C4.556 10.78 3.88 11 3 11a4.498 4.498 0 0 1-2.023-.454 3.544 3.544 0 0 1-.686-.45l-.045-.04-.016-.015-.006-.006-.004-.004v-.001a.75.75 0 0 1-.154-.838L2.178 4.5H1.75a.75.75 0 0 1 0-1.5h2.234a.249.249 0 0 0 .125-.033l1.288-.737c.265-.15.564-.23.869-.23h.984V.75a.75.75 0 0 1 1.5 0Zm2.945 8.477c.285.135.718.273 1.305.273s1.02-.138 1.305-.273L13 6.327Zm-10 0c.285.135.718.273 1.305.273s1.02-.138 1.305-.273L3 6.327Z"></path></svg>  <span class="text-green-700 dark:text-green-300">${escape(repo.license)}</span></span>` : ``}</div>  <div class="flex items-center gap-4 flex-shrink-0"> <div class="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400"><div class="flex items-center space-x-1">${validate_component(Star, "Star").$$render($$result, { class: "h-4 w-4" }, {}, {})} <span>${escape(repo.stars_count)}</span></div> <div class="flex items-center space-x-1">${validate_component(Download, "Download").$$render($$result, { class: "h-4 w-4" }, {}, {})} <span>${escape(repo.downloads_count)}</span></div> <div class="flex items-center space-x-1">${validate_component(Eye, "Eye").$$render($$result, { class: "h-4 w-4" }, {}, {})} <span>${escape(repo.views_count)}</span></div> ${repo.total_size > 0 ? `<div class="flex items-center space-x-1"><span>${escape(formatFileSize(repo.total_size))}</span></div>` : ``}</div>  <div class="flex items-center space-x-1 text-xs text-gray-500 dark:text-gray-400">${validate_component(Calendar, "Calendar").$$render($$result, { class: "h-3 w-3" }, {}, {})} <span>${escape(formatDistanceToNow(new Date(repo.updated_at), { addSuffix: true, locale: zhCN }))}</span></div></div></div> </div>`;
});
const Pagination = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let startItem;
  let endItem;
  let hasNext;
  let hasPrev;
  let visiblePages;
  let $_, $$unsubscribe__;
  $$unsubscribe__ = subscribe($format, (value) => $_ = value);
  let { currentPage = 1 } = $$props;
  let { totalPages = 1 } = $$props;
  let { total = 0 } = $$props;
  let { pageSize: pageSize2 = 20 } = $$props;
  let { showSummary = true } = $$props;
  createEventDispatcher();
  function getVisiblePages() {
    const delta = 2;
    const range = [];
    const rangeWithDots = [];
    for (let i = Math.max(2, currentPage - delta); i <= Math.min(totalPages - 1, currentPage + delta); i++) {
      range.push(i);
    }
    if (currentPage - delta > 2) {
      rangeWithDots.push(1, "...");
    } else {
      rangeWithDots.push(1);
    }
    rangeWithDots.push(...range);
    if (currentPage + delta < totalPages - 1) {
      rangeWithDots.push("...", totalPages);
    } else {
      rangeWithDots.push(totalPages);
    }
    return rangeWithDots;
  }
  if ($$props.currentPage === void 0 && $$bindings.currentPage && currentPage !== void 0)
    $$bindings.currentPage(currentPage);
  if ($$props.totalPages === void 0 && $$bindings.totalPages && totalPages !== void 0)
    $$bindings.totalPages(totalPages);
  if ($$props.total === void 0 && $$bindings.total && total !== void 0)
    $$bindings.total(total);
  if ($$props.pageSize === void 0 && $$bindings.pageSize && pageSize2 !== void 0)
    $$bindings.pageSize(pageSize2);
  if ($$props.showSummary === void 0 && $$bindings.showSummary && showSummary !== void 0)
    $$bindings.showSummary(showSummary);
  startItem = (currentPage - 1) * pageSize2 + 1;
  endItem = Math.min(currentPage * pageSize2, total);
  hasNext = currentPage < totalPages;
  hasPrev = currentPage > 1;
  visiblePages = getVisiblePages();
  $$unsubscribe__();
  return `${totalPages > 1 ? `<div class="flex flex-col sm:flex-row items-center justify-between space-y-4 sm:space-y-0"> ${showSummary ? `<div class="text-sm text-secondary-600 dark:text-dark-500">${escape($_("pagination.showing", {
    values: { from: startItem, to: endItem, total }
  }))}</div>` : ``}  <div class="flex items-center space-x-1"> <button class="flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-md border border-secondary-300 dark:border-secondary-600 bg-white dark:bg-dark-50 text-secondary-700 dark:text-dark-600 hover:bg-secondary-50 dark:hover:bg-secondary-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors" ${!hasPrev ? "disabled" : ""}>${validate_component(ChevronLeft, "ChevronLeft").$$render($$result, { class: "w-4 h-4" }, {}, {})} <span class="hidden sm:inline">${escape($_("pagination.previous"))}</span></button>  <div class="flex items-center space-x-1">${each(visiblePages, (page2) => {
    return `${page2 === "..." ? `<span class="px-3 py-2 text-sm text-secondary-500 dark:text-dark-400" data-svelte-h="svelte-lstmma">...
            </span>` : `<button class="${"px-3 py-2 text-sm font-medium rounded-md transition-colors " + escape(
      page2 === currentPage ? "bg-primary-600 text-white" : "bg-white dark:bg-dark-50 text-secondary-700 dark:text-dark-600 hover:bg-secondary-50 dark:hover:bg-secondary-800 border border-secondary-300 dark:border-secondary-600",
      true
    )}">${escape(page2)} </button>`}`;
  })}</div>  <button class="flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-md border border-secondary-300 dark:border-secondary-600 bg-white dark:bg-dark-50 text-secondary-700 dark:text-dark-600 hover:bg-secondary-50 dark:hover:bg-secondary-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors" ${!hasNext ? "disabled" : ""}><span class="hidden sm:inline">${escape($_("pagination.next"))}</span> ${validate_component(ChevronRight, "ChevronRight").$$render($$result, { class: "w-4 h-4" }, {}, {})}</button></div></div>` : ``}`;
});
let pageSize = 20;
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $page, $$unsubscribe_page;
  let $_, $$unsubscribe__;
  let $currentUser, $$unsubscribe_currentUser;
  $$unsubscribe_page = subscribe(page, (value) => $page = value);
  $$unsubscribe__ = subscribe($format, (value) => $_ = value);
  $$unsubscribe_currentUser = subscribe(user, (value) => $currentUser = value);
  let searchQuery = "";
  let searchType = "repositories";
  let repositories = [];
  let users = [];
  let loading = false;
  let error = "";
  let totalResults = 0;
  let currentPage = 1;
  let filters = {
    repo_type: "",
    // model, dataset, space
    classification_id: null,
    tags: "",
    verified_only: false,
    sort_by: "relevance",
    order: "desc"
  };
  async function performSearch() {
    if (!searchQuery.trim())
      return;
    loading = true;
    error = "";
    try {
      if (searchType === "repositories" || searchType === "all") {
        const repoResponse = await api.listRepositories({
          q: searchQuery,
          repo_type: filters.repo_type || void 0,
          classification_id: filters.classification_id || void 0,
          tags: filters.tags || void 0,
          sort_by: filters.sort_by,
          sort_order: filters.order,
          page: currentPage,
          per_page: pageSize
        });
        repositories = repoResponse.items || repoResponse;
        totalResults = repoResponse.total || repositories.length;
      }
      if (searchType === "users" || searchType === "all") {
        const userResponse = await api.getUsers({
          q: searchQuery,
          verified_only: filters.verified_only,
          sort_by: filters.sort_by === "relevance" ? "relevance" : "created_at",
          sort_order: filters.order,
          page: currentPage,
          per_page: pageSize
        });
        users = userResponse.items || userResponse;
      }
    } catch (err) {
      console.error("Search failed:", err);
      error = "网络错误，请稍后重试";
    } finally {
      loading = false;
    }
  }
  const repoTypes = [
    { value: "", label: "所有类型" },
    { value: "model", label: "模型" },
    { value: "dataset", label: "数据集" },
    { value: "space", label: "空间" }
  ];
  const sortOptions = [
    { value: "relevance", label: "相关度" },
    { value: "updated_at", label: "更新时间" },
    { value: "created_at", label: "创建时间" },
    { value: "stars_count", label: "星标数" },
    { value: "downloads_count", label: "下载数" }
  ];
  {
    if ($page.url.searchParams.get("q")) {
      searchQuery = $page.url.searchParams.get("q") || "";
      searchType = $page.url.searchParams.get("type") || "repositories";
      filters.repo_type = $page.url.searchParams.get("repo_type") || "";
      filters.sort_by = $page.url.searchParams.get("sort") || "relevance";
      filters.order = $page.url.searchParams.get("order") || "desc";
      if (searchQuery) {
        performSearch();
      }
    }
  }
  $$unsubscribe_page();
  $$unsubscribe__();
  $$unsubscribe_currentUser();
  return `${$$result.head += `<!-- HEAD_svelte-ps9ygr_START -->${$$result.title = `<title>${escape($_("search.search"))} - GeoML-Hub</title>`, ""}<meta name="description"${add_attribute("content", $_("search.search_description"), 0)}><!-- HEAD_svelte-ps9ygr_END -->`, ""} <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"> <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6 mb-6"><form class="space-y-4"> <div class="flex space-x-4"><div class="flex-1"><label for="search" class="sr-only">${escape($_("search.search"))}</label> <div class="relative"><div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">${validate_component(Search, "Search").$$render($$result, { class: "h-5 w-5 text-gray-400" }, {}, {})}</div> <input id="search" type="text"${add_attribute("placeholder", $_("search.search_placeholder"), 0)} class="input pl-10 w-full"${add_attribute("value", searchQuery, 0)}></div></div> <button type="submit" class="btn btn-primary">${escape($_("search.search"))}</button></div>  <div class="flex space-x-4"><div class="flex space-x-2">${each(["repositories", "users", "all"], (type) => {
    return `<label class="flex items-center"><input type="radio"${add_attribute("value", type, 0)} class="form-radio h-4 w-4 text-primary-600"${type === searchType ? add_attribute("checked", true, 1) : ""}> <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">${escape($_(`search.${type}`))}</span> </label>`;
  })}</div></div></form></div>  <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-4 mb-6"><div class="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0"> <div class="flex flex-wrap items-center space-x-4">${searchType === "repositories" || searchType === "all" ? ` <div class="flex items-center space-x-2">${validate_component(Filter, "Filter").$$render($$result, { class: "h-4 w-4 text-gray-400" }, {}, {})} <select class="input-sm">${each(repoTypes, (type) => {
    return `<option${add_attribute("value", type.value, 0)}>${escape(type.label)}</option>`;
  })}</select></div>` : ``} ${searchType === "users" || searchType === "all" ? ` <label class="flex items-center"><input type="checkbox" class="form-checkbox h-4 w-4 text-primary-600"${add_attribute("checked", filters.verified_only, 1)}> <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">${escape($_("user.verified_only"))}</span></label>` : ``}  <div class="flex items-center space-x-2"><select class="input-sm">${each(sortOptions, (option) => {
    return `<option${add_attribute("value", option.value, 0)}>${escape(option.label)}</option>`;
  })}</select> <button class="btn btn-sm btn-secondary">${filters.order === "desc" ? `${validate_component(SortDesc, "SortDesc").$$render($$result, { class: "h-4 w-4" }, {}, {})}` : `${validate_component(SortAsc, "SortAsc").$$render($$result, { class: "h-4 w-4" }, {}, {})}`}</button></div></div>  <div class="flex items-center space-x-2"><button class="${"p-2 rounded " + escape(
    "bg-primary-100 text-primary-600",
    true
  )}">${validate_component(Grid, "Grid").$$render($$result, { class: "h-4 w-4" }, {}, {})}</button> <button class="${"p-2 rounded " + escape(
    "text-gray-400 hover:text-gray-600",
    true
  )}">${validate_component(List$1, "List").$$render($$result, { class: "h-4 w-4" }, {}, {})}</button></div></div></div>  ${loading ? `<div class="flex justify-center py-12">${validate_component(Loading, "Loading").$$render($$result, {}, {}, {})}</div>` : `${error ? `<div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6"><p class="text-red-800 dark:text-red-200">${escape(error)}</p></div>` : `${searchQuery ? ` <div class="mb-6"><p class="text-sm text-gray-600 dark:text-gray-400">${searchType === "repositories" || searchType === "all" ? `${escape($_("search.found"))} ${escape(totalResults)} ${escape($_("search.repositories"))}` : ``} ${searchType === "users" || searchType === "all" ? `${escape(users.length)} ${escape($_("search.users"))}` : ``} ${searchQuery ? `${escape($_("search.for"))} &quot;${escape(searchQuery)}&quot;` : ``}</p></div>  ${(searchType === "repositories" || searchType === "all") && repositories.length > 0 ? `<div class="mb-8"><h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">${escape($_("search.repositories"))}</h2> ${`<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">${each(repositories, (repository) => {
    return `${validate_component(RepositoryCard, "RepositoryCard").$$render(
      $$result,
      {
        repo: repository,
        currentUser: $currentUser,
        compact: true
      },
      {},
      {}
    )}`;
  })}</div>`}</div>` : ``}  ${(searchType === "users" || searchType === "all") && users.length > 0 ? `<div class="mb-8"><h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">${escape($_("search.users"))}</h2> <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">${each(users, (user2) => {
    return `<a href="${escape(base, true) + "/" + escape(user2.username, true)}" class="block"><div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow"><div class="flex items-center space-x-4">${validate_component(UserAvatar, "UserAvatar").$$render($$result, { user: user2, size: "lg" }, {}, {})} <div class="flex-1 min-w-0"><h3 class="text-lg font-semibold text-gray-900 dark:text-white truncate">${escape(user2.username)}</h3> ${user2.full_name ? `<p class="text-sm text-gray-600 dark:text-gray-400 truncate">${escape(user2.full_name)} </p>` : ``} ${user2.bio ? `<p class="text-sm text-gray-500 dark:text-gray-400 mt-2 line-clamp-2">${escape(user2.bio)} </p>` : ``} <div class="flex items-center space-x-4 mt-2 text-xs text-gray-500 dark:text-gray-400"><span>${escape(user2.repositories_count || 0)} ${escape($_("user.repositories"))}</span> <span>${escape(user2.followers_count || 0)} ${escape($_("user.followers"))}</span> </div></div> </div></div> </a>`;
  })}</div></div>` : ``}  ${repositories.length === 0 && users.length === 0 ? `<div class="text-center py-12">${validate_component(Search, "Search").$$render(
    $$result,
    {
      class: "h-12 w-12 text-gray-300 mx-auto mb-4"
    },
    {},
    {}
  )} <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">${escape($_("search.no_results"))}</h3> <p class="text-gray-500 dark:text-gray-400">${escape($_("search.try_different_keywords"))}</p></div>` : ``}  ${totalResults > pageSize ? `<div class="mt-8">${validate_component(Pagination, "Pagination").$$render(
    $$result,
    {
      current: currentPage,
      total: Math.ceil(totalResults / pageSize)
    },
    {},
    {}
  )}</div>` : ``}` : ` <div class="text-center py-12">${validate_component(Search, "Search").$$render(
    $$result,
    {
      class: "h-16 w-16 text-gray-300 mx-auto mb-4"
    },
    {},
    {}
  )} <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">${escape($_("search.search_models_datasets"))}</h2> <p class="text-gray-500 dark:text-gray-400">${escape($_("search.search_hint"))}</p></div>`}`}`}</div>`;
});
export {
  Page as default
};
