// @ts-nocheck
import { browser } from '$app/environment';
import { goto } from '$app/navigation';

import { PUBLIC_API_BASE_URL } from '$env/static/public';
import { dev } from '$app/environment';
import { ErrorHandler, parseApiError, getUserFriendlyMessage } from './error-handler.js';

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
		localStorage.removeItem('refreshToken');
	}

	async handleTokenExpired() {
		if (!browser) return { success: false, error: 'Not in browser environment' };

		try {
			// 动态导入以避免循环依赖
			const { refreshTokenSilently } = await import('$lib/utils/auth.js');
			return await refreshTokenSilently();
		} catch (error) {
			console.error('Failed to handle token expiration:', error);
			return { success: false, error: error.message };
		}
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
				// Token expired or invalid, try to refresh first
				const refreshResult = await this.handleTokenExpired();

				if (refreshResult.success) {
					// Token刷新成功，重试原请求
					const retryConfig = {
						...config,
						headers: {
							...config.headers,
							Authorization: `Bearer ${localStorage.getItem('authToken')}`
						}
					};
					return await fetch(url, retryConfig);
				} else {
					// 刷新失败，清除token并跳转登录
					this.clearToken();
					if (browser) {
						const { logout } = await import('$lib/stores/auth.js');
						logout();
						goto('/login');
					}

					// 创建统一的认证错误
					const authError = new Error('Authentication required');
					authError.response = { status: 401, data: {} };
					throw authError;
				}
			}

			if (!response.ok) {
				// 尝试解析错误响应
				const errorData = await response.json().catch(() => ({}));

				// 创建包含完整错误信息的错误对象
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
			// 使用统一错误处理器处理错误
			const apiError = ErrorHandler.handleApiError(error, {
				showNotification: false, // 在API层不显示通知，让组件层处理
				logError: true
			});

			// 检查是否需要重新认证
			if (ErrorHandler.needsReauth(apiError)) {
				this.clearToken();
				if (browser) {
					goto('/login');
				}
			}

			throw apiError;
		}
	}

	// Upload file helper with progress support
	async uploadFile(endpoint, file, onProgress = null) {
		const formData = new FormData();
		formData.append('file', file);
		return this.uploadFormData(endpoint, formData, onProgress);
	}

	// Generic upload with progress support using XMLHttpRequest
	async uploadFormData(endpoint, formData, onProgress = null) {
		const url = `${this.baseUrl}${endpoint}`;

		return new Promise((resolve, reject) => {
			const xhr = new XMLHttpRequest();

			// Set up progress tracking
			if (onProgress && typeof onProgress === 'function') {
				xhr.upload.addEventListener('progress', (event) => {
					if (event.lengthComputable) {
						const progress = Math.round((event.loaded / event.total) * 100);
						onProgress(progress);
					}
				});
			}

			// Set up response handling
			xhr.onload = async () => {
				try {
					if (xhr.status === 401) {
						// Token expired or invalid, try to refresh first
						const refreshResult = await this.handleTokenExpired();

						if (refreshResult.success) {
							// Token刷新成功，这里XMLHttpRequest比较难重试，提示用户重新操作
							console.log('Token refreshed, please retry your upload');
							reject(new Error('Token was refreshed, please retry the upload'));
						} else {
							// 刷新失败，清除token并跳转登录
							if (browser) {
								localStorage.removeItem('authToken');
								localStorage.removeItem('user');
								localStorage.removeItem('refreshToken');
								const { logout } = await import('$lib/stores/auth.js');
								logout();
								goto('/login');
							}
							reject(new Error('Authentication required'));
						}
						return;
					}

					if (xhr.status >= 200 && xhr.status < 300) {
						try {
							const data = JSON.parse(xhr.responseText);
							resolve({
								success: true,
								data: data,
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
						error: error.message || '请求失败',
						status: xhr.status
					});
				}
			};

			xhr.onerror = () => {
				resolve({
					success: false,
					error: '网络错误，请检查连接',
					status: 0
				});
			};

			xhr.ontimeout = () => {
				resolve({
					success: false,
					error: '请求超时',
					status: 0
				});
			};

			// Set up request
			xhr.open('POST', url);
			xhr.timeout = 300000; // 5 minutes timeout

			// Add authorization header if token exists
			const token = this.getToken();
			if (token) {
				xhr.setRequestHeader('Authorization', `Bearer ${token}`);
			}

			// Send request
			xhr.send(formData);
		});
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
			const response = await this.request('/api/auth/refresh', {
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
		const params = new URLSearchParams();

		// Handle each parameter, especially arrays
		for (const [key, value] of Object.entries(options)) {
			if (value === undefined || value === null) {
				continue;
			}

			// Handle array parameters (like classification_ids)
			if (Array.isArray(value)) {
				value.forEach(item => {
					if (item !== undefined && item !== null) {
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
		return this.request('/api/repositories/', {
			method: 'POST',
			body: data
		});
	}

	async createRepositoryWithReadme(formData) {
		return this.request('/api/repositories/with-readme', {
			method: 'POST',
			body: formData
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

	async getRepositoryTrend(owner, name, params = {}) {
		const searchParams = new URLSearchParams();

		// 默认查询最近30天
		const endDate = params.end_date || new Date().toISOString().split('T')[0];
		const startDate = params.start_date || (() => {
			const date = new Date();
			date.setDate(date.getDate() - 30);
			return date.toISOString().split('T')[0];
		})();

		searchParams.append('start_date', startDate);
		searchParams.append('end_date', endDate);
		searchParams.append('interval', params.interval || 'daily');

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
			method: 'POST'
		});
	}

	async checkUploadConflict(owner, name, fileName) {
		const filePath = encodeURIComponent(fileName);
		return this.request(`/api/repositories/${owner}/${name}/check-upload?file_path=${filePath}`, {
			method: 'POST'
		});
	}

	async uploadRepositoryFile(owner, name, file, options = {}) {
		const { onProgress = null, confirmed = false } = options;
		const filePath = encodeURIComponent(file.name);
		const confirmParam = confirmed ? '&confirmed=true' : '';
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

	async createService(owner, name, data, onProgress = null) {
		// If it's FormData, use uploadFormData for progress support
		if (data instanceof FormData) {
			return this.uploadFormData(
				`/api/services/${owner}/${name}/create_service_from_image`,
				data,
				onProgress
			);
		}
		return this.request(`/api/services/${owner}/${name}/create_service_from_image`, {
			method: 'POST',
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

	async uploadImage(repositoryId, formData, onProgress = null) {
		return this.uploadFormData(
			`/api/images/repositories/${repositoryId}/upload`,
			formData,
			onProgress
		);
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
			method: 'PUT',
			body: {
				content: content,
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
			method: 'POST',
			body: {
				old_path: oldPath,
				new_filename: newFilename,
				commit_message: commitMessage
			}
		});
	}

	// ================== Admin API ==================
	async getAdminDashboard() {
		return this.request('/api/admin/dashboard');
	}

	async getAdminUsers(params = {}) {
		const searchParams = new URLSearchParams();
		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
				searchParams.append(key, value);
			}
		});
		return this.request(`/api/admin/users?${searchParams}`);
	}

	async updateAdminUserStatus(userId, data) {
		const params = new URLSearchParams();
		Object.entries(data).forEach(([key, value]) => {
			if (value !== undefined && value !== null) {
				params.append(key, value);
			}
		});
		return this.request(`/api/admin/users/${userId}/status?${params}`, {
			method: 'PUT'
		});
	}

	async getAdminRepositories(params = {}) {
		const searchParams = new URLSearchParams();
		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
				searchParams.append(key, value);
			}
		});
		return this.request(`/api/admin/repositories?${searchParams}`);
	}

	async getAdminRepositoryStats() {
		return this.request('/api/admin/repositories/stats');
	}

	async updateAdminRepositoryStatus(repositoryId, data) {
		const params = new URLSearchParams();
		Object.entries(data).forEach(([key, value]) => {
			if (value !== undefined && value !== null) {
				params.append(key, value);
			}
		});
		return this.request(`/api/admin/repositories/${repositoryId}/status?${params}`, {
			method: 'PUT'
		});
	}

	async restoreAdminRepository(repositoryId) {
		return this.request(`/api/admin/repositories/${repositoryId}/restore`, {
			method: 'POST'
		});
	}

	async hardDeleteAdminRepository(repositoryId, confirm = false) {
		return this.request(`/api/admin/repositories/${repositoryId}/hard-delete?confirm=${confirm}`, {
			method: 'DELETE'
		});
	}

	async getAdminStorageStats() {
		return this.request('/api/admin/storage/stats');
	}

	async performAdminStorageCleanup(options = {}) {
		const params = new URLSearchParams();
		Object.entries(options).forEach(([key, value]) => {
			if (value !== undefined && value !== null) {
				params.append(key, value);
			}
		});
		return this.request(`/api/admin/storage/cleanup?${params}`, {
			method: 'POST'
		});
	}

	async getAdminSystemHealth() {
		return this.request('/api/admin/system/health');
	}

	async getAdminSystemLogs(params = {}) {
		const searchParams = new URLSearchParams();
		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined && value !== null && value !== '') {
				searchParams.append(key, value);
			}
		});
		return this.request(`/api/admin/logs?${searchParams}`);
	}

	async getAdminSystemConfig() {
		return this.request('/api/admin/system/config');
	}

	async getAdminSystemInfo() {
		return this.request('/api/admin/system/info');
	}

	async updateAdminSystemConfig(config) {
		return this.request('/api/admin/system/config', {
			method: 'PUT',
			body: config
		});
	}

	async setAdminMaintenanceMode(enabled, message = '') {
		return this.request('/api/admin/system/maintenance', {
			method: 'POST',
			body: { enabled, message }
		});
	}

	// Repository classification management
	repositories = {
		// Add sphere classification to repository
		addClassification: async (owner, repoName, classificationId) => {
			return this.request(`/api/repositories/${owner}/${repoName}/classifications?classification_id=${classificationId}`, {
				method: 'POST'
			});
		},

		// Remove all sphere classifications from repository
		removeClassifications: async (owner, repoName) => {
			return this.request(`/api/repositories/${owner}/${repoName}/classifications`, {
				method: 'DELETE'
			});
		},

		// Add task classification to repository
		addTaskClassification: async (owner, repoName, taskClassificationId) => {
			return this.request(`/api/repositories/${owner}/${repoName}/task-classifications?task_classification_id=${taskClassificationId}`, {
				method: 'POST'
			});
		},

		// Remove task classification from repository
		removeTaskClassification: async (owner, repoName, taskClassificationId) => {
			return this.request(`/api/repositories/${owner}/${repoName}/task-classifications/${taskClassificationId}`, {
				method: 'DELETE'
			});
		},

		// Get repository task classifications
		getTaskClassifications: async (owner, repoName) => {
			return this.request(`/api/repositories/${owner}/${repoName}/task-classifications`);
		}
	};
}

// Create and export the API instance
export const api = new ApiClient();
