/**
 * 格式化工具函数
 */

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的文件大小
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 格式化时间距离
 * @param {string|Date} date - 日期
 * @returns {string} 格式化后的时间距离
 */
export function formatTimeAgo(date) {
  if (!date) return '未知时间';
  
  const now = new Date();
  const targetDate = typeof date === 'string' ? new Date(date) : date;
  const diffMs = now - targetDate;
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffSeconds < 60) {
    return '刚刚';
  } else if (diffMinutes < 60) {
    return `${diffMinutes}分钟前`;
  } else if (diffHours < 24) {
    return `${diffHours}小时前`;
  } else if (diffDays < 30) {
    return `${diffDays}天前`;
  } else {
    return targetDate.toLocaleDateString('zh-CN');
  }
}

/**
 * 格式化数字
 * @param {number} num - 数字
 * @returns {string} 格式化后的数字
 */
export function formatNumber(num) {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

/**
 * 格式化百分比
 * @param {number} value - 值
 * @param {number} total - 总数
 * @returns {string} 百分比字符串
 */
export function formatPercentage(value, total) {
  if (total === 0) return '0%';
  return Math.round((value / total) * 100) + '%';
}

/**
 * 截断文本
 * @param {string} text - 文本
 * @param {number} maxLength - 最大长度
 * @returns {string} 截断后的文本
 */
export function truncateText(text, maxLength = 100) {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

/**
 * 格式化Git提交哈希
 * @param {string} hash - 完整哈希
 * @returns {string} 短哈希
 */
export function formatCommitHash(hash) {
  if (!hash) return '';
  return hash.substring(0, 8);
}

/**
 * 格式化日期时间
 * @param {string|Date} date - 日期
 * @param {boolean} showTime - 是否显示时间
 * @returns {string} 格式化后的日期时间
 */
export function formatDateTime(date, showTime = true) {
  if (!date) return '未知时间';
  
  const targetDate = typeof date === 'string' ? new Date(date) : date;
  
  if (showTime) {
    return targetDate.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } else {
    return targetDate.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  }
}

/**
 * 格式化相对时间 (与formatTimeAgo类似，但更详细)
 * @param {string|Date} date - 日期
 * @returns {string} 相对时间字符串
 */
export function formatRelativeTime(date) {
  if (!date) return '未知时间';
  
  const now = new Date();
  const targetDate = typeof date === 'string' ? new Date(date) : date;
  const diffMs = now - targetDate;
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);
  const diffWeeks = Math.floor(diffDays / 7);
  const diffMonths = Math.floor(diffDays / 30);
  const diffYears = Math.floor(diffDays / 365);
  
  if (diffSeconds < 60) {
    return '刚刚';
  } else if (diffMinutes < 60) {
    return `${diffMinutes}分钟前`;
  } else if (diffHours < 24) {
    return `${diffHours}小时前`;
  } else if (diffDays < 7) {
    return `${diffDays}天前`;
  } else if (diffWeeks < 4) {
    return `${diffWeeks}周前`;
  } else if (diffMonths < 12) {
    return `${diffMonths}个月前`;
  } else {
    return `${diffYears}年前`;
  }
}

/**
 * 格式化日期为相对时间或绝对时间
 * @param {string|Date} date - 日期
 * @param {boolean} useRelative - 是否使用相对时间
 * @returns {string} 格式化后的时间
 */
export function formatDate(date, useRelative = true) {
  if (useRelative) {
    return formatRelativeTime(date);
  } else {
    return formatDateTime(date, false);
  }
}