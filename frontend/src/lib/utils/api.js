// @ts-nocheck
import { browser } from '$app/environment';
import { goto } from '$app/navigation';

import { PUBLIC_API_BASE_URL } from '$env/static/public';
import { dev } from '$app/environment';

// 环境适配：开发环境使用代理，生产环境使用完整URL
const API_BASE_URL = dev ? '' : PUBLIC_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
	constructor() {
		this.baseUrl = API_BASE_URL;
	}

	// ================== Authentication helpers ==================
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

	// ================== Base request method ==================
	async request(endpoint, options = {}) {
		const url = `${this.baseUrl}${endpoint}`;

		const config = {
			headers: {
				...options.headers
			},
			...options
		};

		// Only set Content-Type for non-FormData requests
		if (!(config.body instanceof FormData)) {
			config.headers['Content-Type'] = 'application/json';
		}

		// Add authentication token if available
		const token = this.getToken();
		if (token) {
			config.headers.Authorization = `Bearer ${token}`;
		}

		if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
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

		const url = `${this.baseUrl}${endpoint}`;

		try {
			const response = await fetch(url, config);

			if (response.status === 401) {
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
			console.error('Upload failed:', error);
			throw error;
		}
	}

	// ================== Authentication API ==================
	async mockExternalAuth(email, password) {
		try {
			const response = await this.request('/api/auth/mock-external-auth/', {
				method: 'POST',
				body: { email, password }
			});
			return { success: true, data: response };
		} catch (error) {
			return { success: false, error: error.message };
		}
	}

	async login(externalToken) {
		try {
			const response = await this.request('/api/auth/login/', {
				method: 'POST',
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
			const response = await this.request('/api/auth/register/', {
				method: 'POST',
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
			const response = await this.request('/api/auth/login/credentials/', {
				method: 'POST',
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
			const response = await this.request('/api/auth/verify/', {
				method: 'POST'
			});
			return { success: true, data: response };
		} catch (error) {
			return { success: false, error: error.message };
		}
	}

	async logout() {
		try {
			await this.request('/api/auth/logout/', {
				method: 'POST',
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
			const response = await this.request('/api/auth/me');
			return { success: true, data: response };
		} catch (error) {
			return { success: false, error: error.message };
		}
	}

	async refreshToken(refreshToken) {
		try {
			const response = await this.request('/api/auth/refresh/', {
				method: 'POST',
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
		return this.request('/api/search/stats');
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
			method: 'POST'
		});
	}

	async unfollowUserByUsername(username) {
		return this.request(`/api/users/${username}/follow`, {
			method: 'DELETE'
		});
	}

	async getUserStatsByUsername(username) {
		return this.request(`/api/users/${username}/stats`);
	}

	async getUserStarredRepositories(username, params = {}) {
		const searchParams = new URLSearchParams();
		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
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
		const params = new URLSearchParams(options);
		return this.request(`/api/repositories?${params}`);
	}

	async getRepository(owner, name) {
		return this.request(`/api/repositories/${owner}/${name}`);
	}

	async createRepository(data) {
		return this.request('/api/repositories/', {
			method: 'POST',
			body: data
		});
	}

	async updateRepository(owner, name, data) {
		return this.request(`/api/repositories/${owner}/${name}`, {
			method: 'PUT',
			body: data
		});
	}

	async deleteRepository(owner, name) {
		return this.request(`/api/repositories/${owner}/${name}`, {
			method: 'DELETE'
		});
	}

	async getRepositoryFiles(owner, name, path = '') {
		const params = new URLSearchParams({ path });
		return this.request(`/api/repositories/${owner}/${name}/files?${params}`);
	}

	async getRepositoryFileContent(owner, name, filePath) {
		return this.request(`/api/repositories/${owner}/${name}/blob/${encodeURIComponent(filePath)}`);
	}

	async starRepository(owner, name) {
		return this.request(`/api/repositories/${owner}/${name}/star`, {
			method: 'POST'
		});
	}

	async unstarRepository(owner, name) {
		return this.request(`/api/repositories/${owner}/${name}/star`, {
			method: 'DELETE'
		});
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
			method: 'POST'
		});
	}

	async uploadRepositoryFile(owner, name, file, onProgress = null) {
		const filePath = encodeURIComponent(file.name);
		return this.uploadFile(
			`/api/repositories/${owner}/${name}/upload?file_path=${filePath}`,
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
			method: 'DELETE'
		});
	}

	// ================== Services API ==================
	async getRepositoryServices(owner, name, params = {}) {
		const searchParams = new URLSearchParams();
		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
				searchParams.append(key, value);
			}
		});
		return this.request(`/api/services/${owner}/${name}?${searchParams}`);
	}

	async createService(owner, name, data) {
		return this.request(`/api/services/${owner}/${name}/create_service_from_image`, {
			method: 'POST',
			body: data
		});
	}

	async createServiceWithDockerTar(owner, name, formData) {
		return this.request(`/api/services/${owner}/${name}/create_service_with_docker_tar`, {
			method: 'POST',
			body: formData
		});
	}

	async getService(serviceId) {
		return this.request(`/api/services/${serviceId}`);
	}

	async updateService(serviceId, data) {
		return this.request(`/api/services/${serviceId}`, {
			method: 'PUT',
			body: data
		});
	}

	async deleteService(serviceId) {
		return this.request(`/api/services/${serviceId}`, {
			method: 'DELETE'
		});
	}

	async startService(serviceId, data = { force_restart: false }) {
		return this.request(`/api/services/${serviceId}/start`, {
			method: 'POST',
			body: data
		});
	}

	async stopService(serviceId, data = {}) {
		return this.request(`/api/services/${serviceId}/stop`, {
			method: 'POST',
			body: data
		});
	}

	async restartService(serviceId) {
		return this.request(`/api/services/${serviceId}/restart`, {
			method: 'POST'
		});
	}

	async getServiceStatus(serviceId) {
		return this.request(`/api/services/${serviceId}/status`);
	}

	async getServiceLogs(serviceId, params = {}) {
		const searchParams = new URLSearchParams();
		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
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
			method: 'POST'
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
			method: 'POST',
			body: data
		});
	}

	async updateServiceVisibility(serviceId, data) {
		return this.request(`/api/services/${serviceId}/visibility`, {
			method: 'PUT',
			body: data
		});
	}

	async updateServiceFiles(serviceId, formData) {
		return this.request(`/api/services/${serviceId}/files/update`, {
			method: 'POST',
			body: formData
		});
	}

	async getServiceContainerInfo(serviceId) {
		return this.request(`/api/services/${serviceId}/container-info`);
	}

	async validateServiceEnvironment(serviceId) {
		return this.request(`/api/services/${serviceId}/validate-environment`, {
			method: 'POST'
		});
	}

	// Batch service operations
	async batchStartServices(owner, name, serviceIds) {
		return this.request(`/api/services/${owner}/${name}/batch/start`, {
			method: 'POST',
			body: { service_ids: serviceIds }
		});
	}

	async batchStopServices(owner, name, serviceIds) {
		return this.request(`/api/services/${owner}/${name}/batch/stop`, {
			method: 'POST',
			body: { service_ids: serviceIds }
		});
	}

	async batchDeleteServices(owner, name, serviceIds) {
		return this.request(`/api/services/${owner}/${name}/batch`, {
			method: 'DELETE',
			body: { service_ids: serviceIds }
		});
	}

	// Admin service endpoints
	async getServicesHealthSummary() {
		return this.request('/api/services/health-summary');
	}

	async getServiceStatistics() {
		return this.request('/api/services/admin/statistics');
	}

	async getServicesOverview() {
		return this.request('/api/services/admin/overview');
	}

	async performSystemMaintenance(data = {}) {
		return this.request('/api/services/admin/maintenance', {
			method: 'POST',
			body: data
		});
	}

	// ================== Images API ==================
	async getRepositoryImages(repositoryId) {
		return this.request(`/api/images/repositories/${repositoryId}`);
	}

	async uploadImage(repositoryId, formData) {
		return this.request(`/api/images/repositories/${repositoryId}/upload`, {
			method: 'POST',
			body: formData
		});
	}

	async deleteImage(imageId, force = false) {
		return this.request(`/api/images/${imageId}?force=${force}`, {
			method: 'DELETE'
		});
	}

	async getImageServices(imageId) {
		return this.request(`/api/images/${imageId}/services`);
	}

	async createServiceFromImage(imageId, formData) {
		return this.request(`/api/images/${imageId}/services/create`, {
			method: 'POST',
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

	// ================== Comments API ==================
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

	// ================== Activities API ==================
	async getActivities(params = {}) {
		const searchParams = new URLSearchParams();
		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
				searchParams.append(key, value);
			}
		});
		return this.request(`/api/activities?${searchParams}`);
	}

	// ================== Classifications API ==================
	async getClassificationTree() {
		return this.request('/api/classifications/tree');
	}
}

// Create and export the API instance
export const api = new ApiClient();
