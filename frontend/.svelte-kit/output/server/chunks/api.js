import { B as BROWSER } from "./false.js";
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
const API_BASE_URL = "http://localhost:8000";
class ApiClient {
  constructor() {
    this.baseUrl = API_BASE_URL;
  }
  // Authentication helpers
  getToken() {
    return null;
  }
  setToken(token) {
    return;
  }
  clearToken() {
    return;
  }
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      headers: {
        "Content-Type": "application/json",
        ...options.headers
      },
      ...options
    };
    const token = this.getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    if (config.body && typeof config.body === "object") {
      config.body = JSON.stringify(config.body);
    }
    try {
      const response = await fetch(url, config);
      if (response.status === 401) {
        this.clearToken();
        if (browser)
          ;
        throw new Error("Authentication required");
      }
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.message || `HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("API request failed:", error);
      throw error;
    }
  }
  // Upload file helper
  async uploadFile(endpoint, file, onProgress = null) {
    const formData = new FormData();
    formData.append("file", file);
    const config = {
      method: "POST",
      body: formData,
      headers: {}
    };
    const token = this.getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    delete config.headers["Content-Type"];
    if (onProgress) {
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.upload.addEventListener("progress", (e) => {
          if (e.lengthComputable) {
            onProgress(Math.round(e.loaded / e.total * 100));
          }
        });
        xhr.addEventListener("load", () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(JSON.parse(xhr.responseText));
          } else {
            reject(new Error(`HTTP ${xhr.status}`));
          }
        });
        xhr.addEventListener("error", () => {
          reject(new Error("Upload failed"));
        });
        xhr.open("POST", `${this.baseUrl}${endpoint}`);
        if (token) {
          xhr.setRequestHeader("Authorization", `Bearer ${token}`);
        }
        xhr.send(formData);
      });
    } else {
      const response = await fetch(`${this.baseUrl}${endpoint}`, config);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return await response.json();
    }
  }
  // Authentication API
  auth = {
    async login(credentials) {
      try {
        const response = await this.request("/api/auth/login", {
          method: "POST",
          body: credentials
        });
        return { success: true, data: response };
      } catch (error) {
        return { success: false, error: error.message };
      }
    },
    async register(userData) {
      try {
        const response = await this.request("/api/auth/register", {
          method: "POST",
          body: userData
        });
        return { success: true, data: response };
      } catch (error) {
        return { success: false, error: error.message };
      }
    },
    async logout() {
      try {
        await this.request("/api/auth/logout", {
          method: "POST"
        });
        this.clearToken();
        return { success: true };
      } catch (error) {
        this.clearToken();
        return { success: false, error: error.message };
      }
    },
    async getCurrentUser() {
      try {
        const response = await this.request("/api/auth/me");
        return { success: true, data: response };
      } catch (error) {
        return { success: false, error: error.message };
      }
    },
    async refreshToken() {
      try {
        const response = await this.request("/api/auth/refresh", {
          method: "POST"
        });
        this.setToken(response.access_token);
        return { success: true, data: response };
      } catch (error) {
        return { success: false, error: error.message };
      }
    },
    async forgotPassword(email) {
      try {
        const response = await this.request("/api/auth/forgot-password", {
          method: "POST",
          body: { email }
        });
        return { success: true, data: response };
      } catch (error) {
        return { success: false, error: error.message };
      }
    },
    async resetPassword(token, newPassword) {
      try {
        const response = await this.request("/api/auth/reset-password", {
          method: "POST",
          body: { token, new_password: newPassword }
        });
        return { success: true, data: response };
      } catch (error) {
        return { success: false, error: error.message };
      }
    }
  };
  // Classifications (legacy support)
  async getClassifications(params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== void 0 && value !== null && value !== "") {
        searchParams.append(key, value);
      }
    });
    return this.request(`/api/classifications?${searchParams}`);
  }
  async getClassificationTree(level = null) {
    const params = level ? `?level=${level}` : "";
    return this.request(`/api/classifications/tree${params}`);
  }
  async getClassification(id) {
    return this.request(`/api/classifications/${id}`);
  }
  // Users API
  async getUsers(params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== void 0 && value !== null && value !== "") {
        searchParams.append(key, value);
      }
    });
    return this.request(`/api/users?${searchParams}`);
  }
  async getUser(username) {
    return this.request(`/api/users/${username}`);
  }
  async createUser(data) {
    return this.request("/api/users", {
      method: "POST",
      body: data
    });
  }
  async updateUser(username, data) {
    return this.request(`/api/users/${username}`, {
      method: "PUT",
      body: data
    });
  }
  async getUserRepositories(username, params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== void 0 && value !== null && value !== "") {
        searchParams.append(key, value);
      }
    });
    return this.request(`/api/users/${username}/repositories?${searchParams}`);
  }
  async getUserFollowers(username, params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== void 0 && value !== null && value !== "") {
        searchParams.append(key, value);
      }
    });
    return this.request(`/api/users/${username}/followers?${searchParams}`);
  }
  async getUserFollowing(username, params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== void 0 && value !== null && value !== "") {
        searchParams.append(key, value);
      }
    });
    return this.request(`/api/users/${username}/following?${searchParams}`);
  }
  async followUser(username) {
    return this.request(`/api/users/${username}/follow`, {
      method: "POST"
    });
  }
  async unfollowUser(username) {
    return this.request(`/api/users/${username}/follow`, {
      method: "DELETE"
    });
  }
  async getUserStats(username) {
    return this.request(`/api/users/${username}/stats`);
  }
  // Repositories API
  async getRepositories(params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== void 0 && value !== null && value !== "") {
        if (Array.isArray(value)) {
          value.forEach((v) => searchParams.append(key, v));
        } else {
          searchParams.append(key, value);
        }
      }
    });
    return this.request(`/api/repositories?${searchParams}`);
  }
  async getRepository(owner, repo) {
    return this.request(`/api/repositories/${owner}/${repo}`);
  }
  async createRepository(data) {
    return this.request("/api/repositories", {
      method: "POST",
      body: data
    });
  }
  async updateRepository(owner, repo, data) {
    return this.request(`/api/repositories/${owner}/${repo}`, {
      method: "PUT",
      body: data
    });
  }
  async deleteRepository(owner, repo) {
    return this.request(`/api/repositories/${owner}/${repo}`, {
      method: "DELETE"
    });
  }
  async getRepositoryFiles(owner, repo, params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== void 0 && value !== null && value !== "") {
        searchParams.append(key, value);
      }
    });
    return this.request(`/api/repositories/${owner}/${repo}/files?${searchParams}`);
  }
  async getRepositoryStars(owner, repo, params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== void 0 && value !== null && value !== "") {
        searchParams.append(key, value);
      }
    });
    return this.request(`/api/repositories/${owner}/${repo}/stars?${searchParams}`);
  }
  async getRepositoryStats(owner, repo) {
    return this.request(`/api/repositories/${owner}/${repo}/stats`);
  }
  async starRepository(owner, repo) {
    return this.request(`/api/repositories/${owner}/${repo}/star`, {
      method: "POST"
    });
  }
  async unstarRepository(owner, repo) {
    return this.request(`/api/repositories/${owner}/${repo}/star`, {
      method: "DELETE"
    });
  }
  async uploadRepositoryFile(owner, repo, file, onProgress = null) {
    return this.uploadFile(`/api/repositories/${owner}/${repo}/upload`, file, onProgress);
  }
  // File download
  async downloadFile(owner, repo, filePath) {
    const response = await fetch(`${this.baseUrl}/api/repositories/${owner}/${repo}/files/${filePath}/download`, {
      headers: {
        Authorization: `Bearer ${this.getToken()}`
      }
    });
    if (!response.ok) {
      throw new Error(`Download failed: ${response.status}`);
    }
    return response.blob();
  }
  // Note: V1.0 Model API methods removed in V2.0
  // All model functionality has been moved to repositories
  // Legacy methods are no longer supported
  async createService(data) {
    return this.request("/api/services", {
      method: "POST",
      body: data
    });
  }
  async updateService(id, data) {
    return this.request(`/api/services/${id}`, {
      method: "PUT",
      body: data
    });
  }
  async deleteService(id) {
    return this.request(`/api/services/${id}`, {
      method: "DELETE"
    });
  }
  async getServiceHealth(id) {
    return this.request(`/api/services/${id}/health`);
  }
  // Notifications API
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
  // Comments API
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
  // Activities API
  async getActivities(params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== void 0 && value !== null && value !== "") {
        searchParams.append(key, value);
      }
    });
    return this.request(`/api/activities?${searchParams}`);
  }
}
ApiClient.prototype.search = {
  async repositories(query, options = {}) {
    const params = new URLSearchParams({
      q: query,
      ...options
    });
    return this.request(`/api/search/repositories?${params}`);
  },
  async users(query, options = {}) {
    const params = new URLSearchParams({
      q: query,
      ...options
    });
    return this.request(`/api/search/users?${params}`);
  },
  async trending(options = {}) {
    const params = new URLSearchParams(options);
    return this.request(`/api/search/trending?${params}`);
  },
  async suggestions(query, options = {}) {
    const params = new URLSearchParams({
      q: query,
      ...options
    });
    return this.request(`/api/search/suggestions?${params}`);
  },
  async stats() {
    return this.request("/api/search/stats");
  }
};
ApiClient.prototype.users = {
  async get(username) {
    return this.request(`/api/users/${username}`);
  },
  async getRepositories(username, options = {}) {
    const params = new URLSearchParams(options);
    return this.request(`/api/users/${username}/repositories?${params}`);
  },
  async getFollowers(username, options = {}) {
    const params = new URLSearchParams(options);
    return this.request(`/api/users/${username}/followers?${params}`);
  },
  async getFollowing(username, options = {}) {
    const params = new URLSearchParams(options);
    return this.request(`/api/users/${username}/following?${params}`);
  },
  async follow(username) {
    return this.request(`/api/users/${username}/follow`, {
      method: "POST"
    });
  },
  async unfollow(username) {
    return this.request(`/api/users/${username}/follow`, {
      method: "DELETE"
    });
  },
  async getStats(username) {
    return this.request(`/api/users/${username}/stats`);
  }
};
ApiClient.prototype.notifications = {
  async list(options = {}) {
    const params = new URLSearchParams(options);
    return this.request(`/api/notifications?${params}`);
  },
  async getUnreadCount() {
    return this.request("/api/notifications/unread/count");
  },
  async markAsRead(id) {
    return this.request(`/api/notifications/${id}/read`, {
      method: "POST"
    });
  },
  async markAllAsRead() {
    return this.request("/api/notifications/read-all", {
      method: "POST"
    });
  },
  async delete(id) {
    return this.request(`/api/notifications/${id}`, {
      method: "DELETE"
    });
  }
};
ApiClient.prototype.comments = {
  async list(resourceType, resourceId, options = {}) {
    const params = new URLSearchParams(options);
    return this.request(`/api/comments/${resourceType}/${resourceId}?${params}`);
  },
  async create(resourceType, resourceId, data) {
    return this.request(`/api/comments/${resourceType}/${resourceId}`, {
      method: "POST",
      body: data
    });
  },
  async update(id, data) {
    return this.request(`/api/comments/${id}`, {
      method: "PUT",
      body: data
    });
  },
  async delete(id) {
    return this.request(`/api/comments/${id}`, {
      method: "DELETE"
    });
  },
  async like(id) {
    return this.request(`/api/comments/${id}/like`, {
      method: "POST"
    });
  },
  async unlike(id) {
    return this.request(`/api/comments/${id}/like`, {
      method: "DELETE"
    });
  }
};
ApiClient.prototype.activities = {
  async list(options = {}) {
    const params = new URLSearchParams(options);
    return this.request(`/api/activities?${params}`);
  }
};
ApiClient.prototype.repositories = {
  async list(options = {}) {
    const params = new URLSearchParams(options);
    return this.request(`/api/repositories?${params}`);
  },
  async get(owner, name) {
    return this.request(`/api/repositories/${owner}/${name}`);
  },
  async create(data) {
    return this.request("/api/repositories", {
      method: "POST",
      body: data
    });
  },
  async update(owner, name, data) {
    return this.request(`/api/repositories/${owner}/${name}`, {
      method: "PUT",
      body: data
    });
  },
  async delete(owner, name) {
    return this.request(`/api/repositories/${owner}/${name}`, {
      method: "DELETE"
    });
  },
  async getFiles(owner, name, path = "") {
    const params = new URLSearchParams({ path });
    return this.request(`/api/repositories/${owner}/${name}/files?${params}`);
  },
  async getFileContent(owner, name, filePath) {
    return this.request(`/api/repositories/${owner}/${name}/files/${encodeURIComponent(filePath)}/content`);
  },
  async uploadFile(owner, name, file, options = {}) {
    const formData = new FormData();
    formData.append("file", file);
    return this.upload(`/api/repositories/${owner}/${name}/upload`, formData, options.onProgress);
  },
  async star(owner, name) {
    return this.request(`/api/repositories/${owner}/${name}/star`, {
      method: "POST"
    });
  },
  async unstar(owner, name) {
    return this.request(`/api/repositories/${owner}/${name}/star`, {
      method: "DELETE"
    });
  },
  async getStars(owner, name, options = {}) {
    const params = new URLSearchParams(options);
    return this.request(`/api/repositories/${owner}/${name}/stars?${params}`);
  },
  async getStats(owner, name) {
    return this.request(`/api/repositories/${owner}/${name}/stats`);
  }
};
const api = new ApiClient();
api.auth;
export {
  api as a
};
