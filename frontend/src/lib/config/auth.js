/**
 * 认证配置
 * 用于在开发和生产环境间切换认证方式
 */

// 认证模式配置
export const AUTH_CONFIG = {
    // 认证模式: 'mock' | 'opengms'
    mode: 'mock', // 开发环境使用mock，生产环境改为'opengms'
    
    // OpenGMS配置（生产环境使用）
    opengms: {
        serverUrl: 'http://94.191.49.160:8080',
        clientId: 'test',
        clientSecret: 'zz'
    },
    
    // Mock认证配置（开发环境使用）
    mock: {
        enabled: true,
        users: {
            'admin@geoml-hub.com': 'admin123',
            'user@example.com': 'user123'
        }
    }
};

/**
 * 获取当前认证模式
 */
export function getAuthMode() {
    return AUTH_CONFIG.mode;
}

/**
 * 检查是否使用Mock认证
 */
export function isMockAuth() {
    return AUTH_CONFIG.mode === 'mock';
}

/**
 * 检查是否使用OpenGMS认证
 */
export function isOpenGMSAuth() {
    return AUTH_CONFIG.mode === 'opengms';
}