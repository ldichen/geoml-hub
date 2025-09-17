/**
 * 统一错误处理工具
 */

/**
 * 标准错误响应格式
 */
export class ApiError extends Error {
	constructor(message, code, status, context = null, requestId = null) {
		super(message);
		this.name = 'ApiError';
		this.code = code;
		this.status = status;
		this.context = context;
		this.requestId = requestId;
	}
}

/**
 * 错误代码常量
 */
export const ERROR_CODES = {
	// 通用错误
	INTERNAL_SERVER_ERROR: 'INTERNAL_SERVER_ERROR',
	VALIDATION_ERROR: 'VALIDATION_ERROR',
	AUTHENTICATION_ERROR: 'AUTHENTICATION_ERROR',
	AUTHORIZATION_ERROR: 'AUTHORIZATION_ERROR',
	NOT_FOUND: 'NOT_FOUND',
	CONFLICT: 'CONFLICT',
	BAD_REQUEST: 'BAD_REQUEST',

	// 仓库相关错误
	REPOSITORY_NOT_FOUND: 'REPOSITORY_NOT_FOUND',
	REPOSITORY_ALREADY_EXISTS: 'REPOSITORY_ALREADY_EXISTS',
	REPOSITORY_CREATE_FAILED: 'REPOSITORY_CREATE_FAILED',
	INVALID_REPOSITORY_NAME: 'INVALID_REPOSITORY_NAME',

	// 文件相关错误
	FILE_NOT_FOUND: 'FILE_NOT_FOUND',
	FILE_UPLOAD_FAILED: 'FILE_UPLOAD_FAILED',
	INVALID_FILE_TYPE: 'INVALID_FILE_TYPE',
	FILE_TOO_LARGE: 'FILE_TOO_LARGE',

	// 用户相关错误
	USER_NOT_FOUND: 'USER_NOT_FOUND',
	INVALID_CREDENTIALS: 'INVALID_CREDENTIALS',
	USER_ALREADY_EXISTS: 'USER_ALREADY_EXISTS',

	// 存储相关错误
	STORAGE_ERROR: 'STORAGE_ERROR',

	// 外部服务错误
	EXTERNAL_SERVICE_ERROR: 'EXTERNAL_SERVICE_ERROR',

	// 数据库错误
	DATABASE_ERROR: 'DATABASE_ERROR',
	DUPLICATE_RESOURCE: 'DUPLICATE_RESOURCE',
	FOREIGN_KEY_VIOLATION: 'FOREIGN_KEY_VIOLATION'
};

/**
 * 用户友好的错误消息映射
 */
const ERROR_MESSAGES = {
	[ERROR_CODES.INTERNAL_SERVER_ERROR]: '服务器内部错误，请稍后重试',
	[ERROR_CODES.VALIDATION_ERROR]: '输入数据格式错误，请检查后重试',
	[ERROR_CODES.AUTHENTICATION_ERROR]: '需要登录才能进行此操作',
	[ERROR_CODES.AUTHORIZATION_ERROR]: '您没有权限进行此操作',
	[ERROR_CODES.NOT_FOUND]: '请求的资源不存在',
	[ERROR_CODES.CONFLICT]: '操作冲突，请刷新页面后重试',
	[ERROR_CODES.BAD_REQUEST]: '请求参数错误',

	[ERROR_CODES.REPOSITORY_NOT_FOUND]: '仓库不存在',
	[ERROR_CODES.REPOSITORY_ALREADY_EXISTS]: '仓库名已存在',
	[ERROR_CODES.REPOSITORY_CREATE_FAILED]: '创建仓库失败',
	[ERROR_CODES.INVALID_REPOSITORY_NAME]: '仓库名格式错误',

	[ERROR_CODES.FILE_NOT_FOUND]: '文件不存在',
	[ERROR_CODES.FILE_UPLOAD_FAILED]: '文件上传失败',
	[ERROR_CODES.INVALID_FILE_TYPE]: '不支持的文件类型',
	[ERROR_CODES.FILE_TOO_LARGE]: '文件过大',

	[ERROR_CODES.USER_NOT_FOUND]: '用户不存在',
	[ERROR_CODES.INVALID_CREDENTIALS]: '用户名或密码错误',
	[ERROR_CODES.USER_ALREADY_EXISTS]: '用户已存在',

	[ERROR_CODES.STORAGE_ERROR]: '存储服务错误',
	[ERROR_CODES.EXTERNAL_SERVICE_ERROR]: '外部服务暂时不可用',
	[ERROR_CODES.DATABASE_ERROR]: '数据库操作失败',
	[ERROR_CODES.DUPLICATE_RESOURCE]: '资源已存在',
	[ERROR_CODES.FOREIGN_KEY_VIOLATION]: '引用的资源不存在'
};

/**
 * 解析API响应错误
 */
export function parseApiError(error) {
	// 如果已经是 ApiError，直接返回
	if (error instanceof ApiError) {
		return error;
	}

	// 处理 fetch API 错误
	if (error.response) {
		const response = error.response;
		const data = response.data || {};

		// 检查是否是标准错误响应格式
		if (data.error) {
			return new ApiError(
				data.error.message,
				data.error.code,
				response.status,
				data.error.context,
				data.request_id
			);
		}

		// 处理其他格式的错误响应
		const message = data.detail || data.message || `HTTP ${response.status}`;
		const code = mapStatusToErrorCode(response.status);

		return new ApiError(message, code, response.status);
	}

	// 处理网络错误等
	if (error.message) {
		return new ApiError(
			error.message,
			ERROR_CODES.INTERNAL_SERVER_ERROR,
			0
		);
	}

	// 默认错误
	return new ApiError(
		'未知错误，请稍后重试',
		ERROR_CODES.INTERNAL_SERVER_ERROR,
		0
	);
}

/**
 * 获取用户友好的错误消息
 */
export function getUserFriendlyMessage(error) {
	const apiError = parseApiError(error);

	// 优先使用服务端返回的消息
	if (apiError.message && apiError.message !== apiError.code) {
		return apiError.message;
	}

	// 使用预定义的友好消息
	return ERROR_MESSAGES[apiError.code] || '未知错误，请稍后重试';
}

/**
 * 将HTTP状态码映射到错误代码
 */
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

/**
 * 错误处理工具类
 */
export class ErrorHandler {
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
			console.error('API Error:', {
				message: apiError.message,
				code: apiError.code,
				status: apiError.status,
				context: apiError.context,
				requestId: apiError.requestId
			});
		}

		// 这里可以集成通知系统
		if (showNotification && typeof window !== 'undefined') {
			// 可以在这里调用通知组件
			console.warn('Error notification:', getUserFriendlyMessage(apiError));
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
			error.context.validation_errors.forEach(validationError => {
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
		// 服务器错误可以重试，客户端错误不应重试
		return error.status >= 500 || error.status === 0;
	}
}