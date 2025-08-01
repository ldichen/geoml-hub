// @ts-nocheck
import { browser } from '$app/environment';
import { goto } from '$app/navigation';

import { PUBLIC_API_BASE_URL } from '$env/static/public';
import { dev } from '$app/environment';

// 环境适配：开发环境使用代理，生产环境使用完整URL
const API_BASE_URL = dev ? '' : (PUBLIC_API_BASE_URL || 'http://localhost:8000');

class ApiClient {
	constructor() {
		this.baseUrl = API_BASE_URL;
	}

	// Authentication helpers
	getToken() {
		if (!browser) return null;
		return localStorage.getItem('authToken');
	}

	setToken(token) {
		if (!browser) return;
		if (token) {
			localStorage.setItem('authToken', token);
		} else {
			localStorage.removeItem('authToken');
		}
	}

	clearToken() {
		if (!browser) return;
		localStorage.removeItem('authToken');
		localStorage.removeItem('user');
	}

	async request(endpoint, options = {}) {
		const url = `${this.baseUrl}${endpoint}`;

		const config = {
			headers: {
				'Content-Type': 'application/json',
				...options.headers
			},
			...options
		};

		// Add authentication token if available
		const token = this.getToken();
		if (token) {
			config.headers.Authorization = `Bearer ${token}`;
		}

		if (config.body && typeof config.body === 'object') {
			config.body = JSON.stringify(config.body);
		}

		try {
			const response = await fetch(url, config);

			if (response.status === 401) {
				// Token expired or invalid, clear it and redirect to login
				this.clearToken();
				if (browser) {
					goto('/login');
				}
				throw new Error('Authentication required');
			}

			if (!response.ok) {
				const error = await response.json().catch(() => ({}));
				throw new Error(error.message || `HTTP ${response.status}`);
			}

			return await response.json();
		} catch (error) {
			console.error('API request failed:', error);
			throw error;
		}
	}

	// Upload file helper
	async uploadFile(endpoint, file, onProgress = null) {
		const formData = new FormData();
		formData.append('file', file);

		const config = {
			method: 'POST',
			body: formData,
			headers: {}
		};

		// Add authentication token if available
		const token = this.getToken();
		if (token) {
			config.headers.Authorization = `Bearer ${token}`;
		}

		// Remove Content-Type header to let browser set it with boundary
		delete config.headers['Content-Type'];

		if (onProgress) {
			// Use XMLHttpRequest for progress tracking
			return new Promise((resolve, reject) => {
				const xhr = new XMLHttpRequest();

				xhr.upload.addEventListener('progress', (e) => {
					if (e.lengthComputable) {
						onProgress(Math.round((e.loaded / e.total) * 100));
					}
				});

				xhr.addEventListener('load', () => {
					if (xhr.status >= 200 && xhr.status < 300) {
						resolve(JSON.parse(xhr.responseText));
					} else {
						reject(new Error(`HTTP ${xhr.status}`));
					}
				});

				xhr.addEventListener('error', () => {
					reject(new Error('Upload failed'));
				});

				xhr.open('POST', `${this.baseUrl}${endpoint}`);
				if (token) {
					xhr.setRequestHeader('Authorization', `Bearer ${token}`);
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

	// Classifications (legacy support)
	async getClassifications(params = {}) {
		const searchParams = new URLSearchParams();

		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
				searchParams.append(key, value);
			}
		});

		return this.request(`/api/classifications?${searchParams}`);
	}

	async getClassificationTree(level = null) {
		const params = level ? `?level=${level}` : '';
		return this.request(`/api/classifications/tree${params}`);
	}

	async getClassification(id) {
		return this.request(`/api/classifications/${id}`);
	}

	// Users API
	async getUsers(params = {}) {
		const searchParams = new URLSearchParams();

		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
				searchParams.append(key, value);
			}
		});

		return this.request(`/api/users?${searchParams}`);
	}

	async getUser(username) {
		return this.request(`/api/users/${username}`);
	}

	async createUser(data) {
		return this.request('/api/users/', {
			method: 'POST',
			body: data
		});
	}

	async updateUser(username, data) {
		return this.request(`/api/users/${username}`, {
			method: 'PUT',
			body: data
		});
	}

	async getUserRepositories(username, params = {}) {
		const searchParams = new URLSearchParams();

		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
				searchParams.append(key, value);
			}
		});

		return this.request(`/api/users/${username}/repositories?${searchParams}`);
	}

	async getUserFollowers(username, params = {}) {
		const searchParams = new URLSearchParams();

		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
				searchParams.append(key, value);
			}
		});

		return this.request(`/api/users/${username}/followers?${searchParams}`);
	}

	async getUserFollowing(username, params = {}) {
		const searchParams = new URLSearchParams();

		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
				searchParams.append(key, value);
			}
		});

		return this.request(`/api/users/${username}/following?${searchParams}`);
	}

	async followUser(username) {
		return this.request(`/api/users/${username}/follow`, {
			method: 'POST'
		});
	}

	async unfollowUser(username) {
		return this.request(`/api/users/${username}/follow`, {
			method: 'DELETE'
		});
	}

	async getUserStats(username) {
		return this.request(`/api/users/${username}/stats`);
	}

	async getUserStorage(username) {
		return this.request(`/api/users/${username}/storage`);
	}

	// Repositories API
	async getRepositories(params = {}) {
		const searchParams = new URLSearchParams();

		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
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
		return this.request('/api/repositories/', {
			method: 'POST',
			body: data
		});
	}

	async updateRepository(owner, repo, data) {
		return this.request(`/api/repositories/${owner}/${repo}`, {
			method: 'PUT',
			body: data
		});
	}

	async deleteRepository(owner, repo) {
		return this.request(`/api/repositories/${owner}/${repo}`, {
			method: 'DELETE'
		});
	}

	async getRepositoryFiles(owner, repo, params = {}) {
		const searchParams = new URLSearchParams();

		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
				searchParams.append(key, value);
			}
		});

		return this.request(`/api/repositories/${owner}/${repo}/files?${searchParams}`);
	}

	async getRepositoryStars(owner, repo, params = {}) {
		const searchParams = new URLSearchParams();

		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
				searchParams.append(key, value);
			}
		});

		return this.request(`/api/repositories/${owner}/${repo}/stars?${searchParams}`);
	}

	async getRepositoryStats(owner, repo) {
		return this.request(`/api/repositories/${owner}/${repo}/stats`);
	}

	async incrementRepositoryView(owner, repo) {
		return this.request(`/api/repositories/${owner}/${repo}/view`, {
			method: 'POST'
		});
	}

	async starRepository(owner, repo) {
		return this.request(`/api/repositories/${owner}/${repo}/star`, {
			method: 'POST'
		});
	}

	async unstarRepository(owner, repo) {
		return this.request(`/api/repositories/${owner}/${repo}/star`, {
			method: 'DELETE'
		});
	}

	async uploadRepositoryFile(owner, repo, file, onProgress = null) {
		// 使用文件名作为文件路径
		const filePath = encodeURIComponent(file.name);
		return this.uploadFile(`/api/repositories/${owner}/${repo}/upload?file_path=${filePath}`, file, onProgress);
	}

	// File download
	async getDownloadUrl(owner, repo, filePath) {
		const response = await fetch(`${this.baseUrl}/api/repositories/${owner}/${repo}/download/${filePath}`, {
			headers: {
				Authorization: `Bearer ${this.getToken()}`
			}
		});

		if (!response.ok) {
			throw new Error(`Download failed: ${response.status}`);
		}

		return response.json();
	}

	// File delete
	async deleteFile(fileId) {
		return this.request(`/api/files/${fileId}`, {
			method: 'DELETE'
		});
	}

	// Note: V1.0 Model API methods removed in V2.0
	// All model functionality has been moved to repositories
	// Legacy methods are no longer supported

	async createService(data) {
		return this.request('/api/services/', {
			method: 'POST',
			body: data
		});
	}

	async updateService(id, data) {
		return this.request(`/api/services/${id}`, {
			method: 'PUT',
			body: data
		});
	}

	async deleteService(id) {
		return this.request(`/api/services/${id}`, {
			method: 'DELETE'
		});
	}

	async getServiceHealth(id) {
		return this.request(`/api/services/${id}/health`);
	}

	// Notifications API
	async getNotifications(params = {}) {
		const searchParams = new URLSearchParams();

		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
				searchParams.append(key, value);
			}
		});

		return this.request(`/api/notifications?${searchParams}`);
	}

	async getUnreadNotificationsCount() {
		return this.request('/api/notifications/unread/count');
	}

	async markNotificationAsRead(id) {
		return this.request(`/api/notifications/${id}/read`, {
			method: 'POST'
		});
	}

	async markAllNotificationsAsRead() {
		return this.request('/api/notifications/read-all/', {
			method: 'POST'
		});
	}

	async deleteNotification(id) {
		return this.request(`/api/notifications/${id}`, {
			method: 'DELETE'
		});
	}

	// Comments API
	async getComments(resourceType, resourceId, params = {}) {
		const searchParams = new URLSearchParams();

		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
				searchParams.append(key, value);
			}
		});

		return this.request(`/api/comments/${resourceType}/${resourceId}?${searchParams}`);
	}

	async createComment(resourceType, resourceId, data) {
		return this.request(`/api/comments/${resourceType}/${resourceId}`, {
			method: 'POST',
			body: data
		});
	}

	async updateComment(id, data) {
		return this.request(`/api/comments/${id}`, {
			method: 'PUT',
			body: data
		});
	}

	async deleteComment(id) {
		return this.request(`/api/comments/${id}`, {
			method: 'DELETE'
		});
	}

	async likeComment(id) {
		return this.request(`/api/comments/${id}/like`, {
			method: 'POST'
		});
	}

	async unlikeComment(id) {
		return this.request(`/api/comments/${id}/like`, {
			method: 'DELETE'
		});
	}

	// Activities API
	async getActivities(params = {}) {
		const searchParams = new URLSearchParams();

		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
				searchParams.append(key, value);
			}
		});

		return this.request(`/api/activities?${searchParams}`);
	}
}

// Search API - Fixed to maintain proper 'this' context
ApiClient.prototype.searchRepositories = async function (query, options = {}) {
	const params = new URLSearchParams({
		q: query,
		...options
	});

	return this.request(`/api/search/repositories?${params}`);
};

ApiClient.prototype.searchUsers = async function (query, options = {}) {
	const params = new URLSearchParams({
		q: query,
		...options
	});

	return this.request(`/api/search/users?${params}`);
};

ApiClient.prototype.getTrending = async function (options = {}) {
	const params = new URLSearchParams(options);
	return this.request(`/api/search/trending?${params}`);
};

ApiClient.prototype.getSearchSuggestions = async function (query, options = {}) {
	const params = new URLSearchParams({
		q: query,
		...options
	});

	return this.request(`/api/search/suggestions?${params}`);
};

ApiClient.prototype.getSearchStats = async function () {
	return this.request('/api/search/stats');
};

// Users API (v2.0) - Fixed to maintain proper 'this' context
ApiClient.prototype.getUserByUsername = async function (username) {
	return this.request(`/api/users/${username}`);
};

ApiClient.prototype.getUserRepositoriesByUsername = async function (username, options = {}) {
	const params = new URLSearchParams(options);
	return this.request(`/api/users/${username}/repositories?${params}`);
};

ApiClient.prototype.getUserFollowers = async function (username, options = {}) {
	const params = new URLSearchParams(options);
	return this.request(`/api/users/${username}/followers?${params}`);
};

ApiClient.prototype.getUserFollowing = async function (username, options = {}) {
	const params = new URLSearchParams(options);
	return this.request(`/api/users/${username}/following?${params}`);
};

ApiClient.prototype.followUserByUsername = async function (username) {
	return this.request(`/api/users/${username}/follow`, {
		method: 'POST'
	});
};

ApiClient.prototype.unfollowUserByUsername = async function (username) {
	return this.request(`/api/users/${username}/follow`, {
		method: 'DELETE'
	});
};

ApiClient.prototype.getUserStatsByUsername = async function (username) {
	return this.request(`/api/users/${username}/stats`);
};

// Notifications API (v2.0) - Fixed to maintain proper 'this' context
ApiClient.prototype.notifications = {
	async list(options = {}) {
		const params = new URLSearchParams(options);
		return api.request(`/api/notifications?${params}`);
	},

	async getUnreadCount() {
		return api.request('/api/notifications/unread/count');
	},

	async markAsRead(id) {
		return api.request(`/api/notifications/${id}/read`, {
			method: 'POST'
		});
	},

	async markAllAsRead() {
		return api.request('/api/notifications/read-all', {
			method: 'POST'
		});
	},

	async delete(id) {
		return api.request(`/api/notifications/${id}`, {
			method: 'DELETE'
		});
	}
};

// Comments API (v2.0) - Fixed to maintain proper 'this' context
ApiClient.prototype.comments = {
	async list(resourceType, resourceId, options = {}) {
		const params = new URLSearchParams(options);
		return api.request(`/api/comments/${resourceType}/${resourceId}?${params}`);
	},

	async create(resourceType, resourceId, data) {
		return api.request(`/api/comments/${resourceType}/${resourceId}`, {
			method: 'POST',
			body: data
		});
	},

	async update(id, data) {
		return api.request(`/api/comments/${id}`, {
			method: 'PUT',
			body: data
		});
	},

	async delete(id) {
		return api.request(`/api/comments/${id}`, {
			method: 'DELETE'
		});
	},

	async like(id) {
		return api.request(`/api/comments/${id}/like`, {
			method: 'POST'
		});
	},

	async unlike(id) {
		return api.request(`/api/comments/${id}/like`, {
			method: 'DELETE'
		});
	}
};

// Activities API (v2.0) - Fixed to maintain proper 'this' context
ApiClient.prototype.activities = {
	async list(options = {}) {
		const params = new URLSearchParams(options);
		return api.request(`/api/activities?${params}`);
	}
};

// Repositories API (v2.0) - Fixed to maintain proper 'this' context
ApiClient.prototype.repositories = {
	async list(options = {}) {
		const params = new URLSearchParams(options);
		return api.request(`/api/repositories?${params}`);
	},

	async get(owner, name) {
		return api.request(`/api/repositories/${owner}/${name}`);
	},

	async create(data) {
		return api.request('/api/repositories/', {
			method: 'POST',
			body: data
		});
	},

	async update(owner, name, data) {
		return api.request(`/api/repositories/${owner}/${name}`, {
			method: 'PUT',
			body: data
		});
	},

	async delete(owner, name) {
		return api.request(`/api/repositories/${owner}/${name}`, {
			method: 'DELETE'
		});
	},

	async getFiles(owner, name, path = '') {
		const params = new URLSearchParams({ path });
		return api.request(`/api/repositories/${owner}/${name}/files?${params}`);
	},

	async getFileContent(owner, name, filePath) {
		return api.request(`/api/repositories/${owner}/${name}/blob/${encodeURIComponent(filePath)}`);
	},

	async uploadFile(owner, name, file, options = {}) {
		const formData = new FormData();
		formData.append('file', file);

		return api.uploadFile(`/api/repositories/${owner}/${name}/upload`, file, options.onProgress);
	},

	async star(owner, name) {
		return api.request(`/api/repositories/${owner}/${name}/star`, {
			method: 'POST'
		});
	},

	async unstar(owner, name) {
		return api.request(`/api/repositories/${owner}/${name}/star`, {
			method: 'DELETE'
		});
	},

	async getStars(owner, name, options = {}) {
		const params = new URLSearchParams(options);
		return api.request(`/api/repositories/${owner}/${name}/stars?${params}`);
	},

	async getStats(owner, name) {
		return api.request(`/api/repositories/${owner}/${name}/stats`);
	},

	// 添加文件树API
	async getTree(owner, name, path = 'main') {
		return api.request(`/api/repositories/${owner}/${name}/tree/${path}`);
	},

	// Model Services API for repositories
	async getServices(owner, name, params = {}) {
		const searchParams = new URLSearchParams();
		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
				searchParams.append(key, value);
			}
		});
		return api.request(`/api/${owner}/${name}/services?${searchParams}`);
	},

	async createService(owner, name, data) {
		return api.request(`/api/${owner}/${name}/services`, {
			method: 'POST',
			body: data
		});
	},

	async updateService(serviceId, data) {
		return api.request(`/api/services/${serviceId}`, {
			method: 'PUT',
			body: data
		});
	},

	async deleteService(serviceId) {
		return api.request(`/api/services/${serviceId}`, {
			method: 'DELETE'
		});
	},

	async getService(serviceId) {
		return api.request(`/api/services/${serviceId}`);
	},

	async startService(serviceId, data = {}) {
		return api.request(`/api/services/${serviceId}/start`, {
			method: 'POST',
			body: data
		});
	},

	async stopService(serviceId, data = {}) {
		return api.request(`/api/services/${serviceId}/stop`, {
			method: 'POST',
			body: data
		});
	},

	async restartService(serviceId) {
		return api.request(`/api/services/${serviceId}/restart`, {
			method: 'POST'
		});
	},

	async getServiceStatus(serviceId) {
		return api.request(`/api/services/${serviceId}/status`);
	},

	async getServiceLogs(serviceId, params = {}) {
		const searchParams = new URLSearchParams();
		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
				searchParams.append(key, value);
			}
		});
		return api.request(`/api/services/${serviceId}/logs?${searchParams}`);
	},

	async getServiceHealthHistory(serviceId, params = {}) {
		const searchParams = new URLSearchParams();
		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
				searchParams.append(key, value);
			}
		});
		return api.request(`/api/services/${serviceId}/health?${searchParams}`);
	},

	async triggerHealthCheck(serviceId) {
		return api.request(`/api/services/${serviceId}/health-check`, {
			method: 'POST'
		});
	},

	async getServiceMetrics(serviceId) {
		return api.request(`/api/services/${serviceId}/metrics`);
	},

	async getServiceResourceUsage(serviceId) {
		return api.request(`/api/services/${serviceId}/resource-usage`);
	},

	async accessServiceDemo(serviceId) {
		return api.request(`/api/services/${serviceId}/demo`);
	},

	async regenerateAccessToken(serviceId, data = {}) {
		return api.request(`/api/services/${serviceId}/access-token`, {
			method: 'POST',
			body: data
		});
	},

	async updateServiceVisibility(serviceId, data) {
		return api.request(`/api/services/${serviceId}/visibility`, {
			method: 'PUT',
			body: data
		});
	},

	// Batch operations
	async batchStartServices(owner, name, serviceIds) {
		return api.request(`/api/${owner}/${name}/services/batch/start`, {
			method: 'POST',
			body: { service_ids: serviceIds }
		});
	},

	async batchStopServices(owner, name, serviceIds) {
		return api.request(`/api/${owner}/${name}/services/batch/stop`, {
			method: 'POST',
			body: { service_ids: serviceIds }
		});
	},

	async batchDeleteServices(owner, name, serviceIds) {
		return api.request(`/api/${owner}/${name}/services/batch`, {
			method: 'DELETE',
			body: { service_ids: serviceIds }
		});
	},

	// Container file management API
	async updateServiceFiles(serviceId, formData) {
		return api.request(`/api/services/${serviceId}/files/update`, {
			method: 'POST',
			body: formData,
			headers: {
				// Remove Content-Type to let browser set it with boundary for FormData
			}
		});
	},

	async createServiceWithTar(formData) {
		return api.request('/api/services/create-with-tar', {
			method: 'POST',
			body: formData,
			headers: {
				// Remove Content-Type to let browser set it with boundary for FormData
			}
		});
	},

	async getServiceContainerInfo(serviceId) {
		return api.request(`/api/services/${serviceId}/container-info`);
	},

	async validateServiceEnvironment(serviceId) {
		return api.request(`/api/services/${serviceId}/validate-environment`, {
			method: 'POST'
		});
	}
};

// 添加用户收藏仓库API
ApiClient.prototype.getUserStarredRepositories = async function (username, params = {}) {
	const searchParams = new URLSearchParams();

	Object.entries(params).forEach(([key, value]) => {
		if (value !== undefined && value !== null && value !== '') {
			searchParams.append(key, value);
		}
	});

	return this.request(`/api/users/${username}/starred?${searchParams}`);
};

// Create the API instance
export const api = new ApiClient();

// Add auth methods to the instance after creation
api.auth = {
	// Mock external authentication (development only)
	mockExternalAuth: async function (email, password) {
		try {
			const response = await api.request('/api/auth/mock-external-auth/', {
				method: 'POST',
				body: { email, password }
			});
			return { success: true, data: response };
		} catch (error) {
			return { success: false, error: error.message };
		}
	},

	login: async function (externalToken) {
		try {
			const response = await api.request('/api/auth/login/', {
				method: 'POST',
				body: { external_token: externalToken }
			});
			// Store the access token
			if (response.access_token) {
				api.setToken(response.access_token);
			}
			return { success: true, data: response };
		} catch (error) {
			return { success: false, error: error.message };
		}
	},

	// 使用OpenGMS用户服务器注册
	register: async function (email, password, username = null, fullName = null) {
		try {
			const response = await api.request('/api/auth/register/', {
				method: 'POST',
				body: { 
					email, 
					password, 
					username,
					full_name: fullName 
				}
			});
			// Store the access token
			if (response.access_token) {
				api.setToken(response.access_token);
			}
			return { success: true, data: response };
		} catch (error) {
			return { success: false, error: error.message };
		}
	},

	// 使用OpenGMS用户服务器登录
	loginWithCredentials: async function (email, password) {
		try {
			const response = await api.request('/api/auth/login/credentials/', {
				method: 'POST',
				body: { email, password }
			});
			// Store the access token
			if (response.access_token) {
				api.setToken(response.access_token);
			}
			return { success: true, data: response };
		} catch (error) {
			return { success: false, error: error.message };
		}
	},

	// 兼容原有的外部令牌登录方法（保留向后兼容性）
	loginWithExternalToken: async function (externalToken) {
		try {
			const response = await api.request('/api/auth/login/', {
				method: 'POST',
				body: { external_token: externalToken }
			});
			// Store the access token
			if (response.access_token) {
				api.setToken(response.access_token);
			}
			return { success: true, data: response };
		} catch (error) {
			return { success: false, error: error.message };
		}
	},

	// 便捷登录方法，用于开发环境（兼容性保留）
	loginWithCredentialsLegacy: async function (email, password) {
		try {
			// 1. 先调用模拟外部认证获取外部令牌
			const externalAuthResult = await this.mockExternalAuth(email, password);
			if (!externalAuthResult.success) {
				return externalAuthResult;
			}

			// 2. 使用外部令牌调用登录接口
			const externalToken = externalAuthResult.data.external_token;
			const loginResult = await this.login(externalToken);
			
			return loginResult;
		} catch (error) {
			return { success: false, error: error.message };
		}
	},

	verify: async function () {
		try {
			const response = await api.request('/api/auth/verify/', {
				method: 'POST'
			});
			return { success: true, data: response };
		} catch (error) {
			return { success: false, error: error.message };
		}
	},

	logout: async function () {
		try {
			await api.request('/api/auth/logout/', {
				method: 'POST',
				body: { token: api.getToken() }
			});
			api.clearToken();
			return { success: true };
		} catch (error) {
			// 即使请求失败也清除本地token
			api.clearToken();
			return { success: false, error: error.message };
		}
	},

	getCurrentUser: async function () {
		try {
			const response = await api.request('/api/auth/me');
			return { success: true, data: response };
		} catch (error) {
			return { success: false, error: error.message };
		}
	},

	me: async function () {
		return this.getCurrentUser();
	},

	refreshToken: async function (refreshToken) {
		try {
			const response = await api.request('/api/auth/refresh/', {
				method: 'POST',
				body: { refresh_token: refreshToken }
			});
			api.setToken(response.access_token);
			return { success: true, data: response };
		} catch (error) {
			return { success: false, error: error.message };
		}
	},

	syncUser: async function () {
		try {
			const response = await api.request('/api/auth/sync/', {
				method: 'POST'
			});
			return { success: true, data: response };
		} catch (error) {
			return { success: false, error: error.message };
		}
	},

	clearToken: function () {
		api.clearToken();
	}
};

// Admin API methods
api.admin = {
	// Dashboard
	async getDashboard() {
		return api.request('/api/admin/dashboard');
	},
	
	async getDashboardStats() {
		return api.request('/api/admin/dashboard');
	},

	async getSystemHealth() {
		return api.request('/api/admin/system/health');
	},

	// User management
	async getUsers(params = {}) {
		const searchParams = new URLSearchParams();
		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
				searchParams.append(key, value);
			}
		});
		return api.request(`/api/admin/users?${searchParams}`);
	},

	async updateUserStatus(userId, data) {
		const params = new URLSearchParams();
		Object.entries(data).forEach(([key, value]) => {
			if (value !== undefined && value !== null) {
				params.append(key, value);
			}
		});
		return api.request(`/api/admin/users/${userId}/status?${params}`, {
			method: 'PUT'
		});
	},

	// Repository management
	async getRepositories(params = {}) {
		const searchParams = new URLSearchParams();
		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
				searchParams.append(key, value);
			}
		});
		return api.request(`/api/admin/repositories?${searchParams}`);
	},

	async updateRepositoryStatus(repoId, data) {
		const params = new URLSearchParams();
		Object.entries(data).forEach(([key, value]) => {
			if (value !== undefined && value !== null) {
				params.append(key, value.toString());
			}
		});
		return api.request(`/api/admin/repositories/${repoId}/status?${params}`, {
			method: 'PUT'
		});
	},

	async softDeleteRepository(repoId) {
		return api.request(`/api/admin/repositories/${repoId}/soft-delete`, {
			method: 'POST'
		});
	},

	async restoreRepository(repoId) {
		return api.request(`/api/admin/repositories/${repoId}/restore`, {
			method: 'POST'
		});
	},

	async hardDeleteRepository(repoId, confirm = false) {
		return api.request(`/api/admin/repositories/${repoId}/hard-delete?confirm=${confirm}`, {
			method: 'DELETE'
		});
	},

	async getRepositoryStats() {
		return api.request('/api/admin/repositories/stats');
	},

	// Storage management
	async getStorageStats() {
		return api.request('/api/admin/storage/stats');
	},

	async performStorageCleanup(options = {}) {
		return api.request('/api/admin/storage/cleanup/', {
			method: 'POST',
			body: options
		});
	},

	// System monitoring
	async getSystemInfo() {
		return api.request('/api/admin/system/info');
	},

	async getSystemLogs(params = {}) {
		const searchParams = new URLSearchParams();
		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
				searchParams.append(key, value);
			}
		});
		return api.request(`/api/admin/system/logs?${searchParams}`);
	},

	// System settings
	async getSystemConfig() {
		return api.request('/api/admin/settings/config');
	},

	async updateSystemConfig(data) {
		return api.request('/api/admin/settings/config/', {
			method: 'PUT',
			body: data
		});
	},

	async getMaintenanceMode() {
		return api.request('/api/admin/settings/maintenance');
	},

	async setMaintenanceMode(enabled, message = '') {
		return api.request('/api/admin/settings/maintenance/', {
			method: 'PUT',
			body: { enabled, message }
		});
	}
};

// 绑定认证API到实例
export const authApi = api.auth;
