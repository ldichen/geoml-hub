// 图片预加载工具
class ImagePreloader {
  constructor() {
    this.cache = new Map();
  }

  // 预加载单个图片
  preload(url) {
    if (this.cache.has(url)) {
      return this.cache.get(url);
    }

    const promise = new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(url);
      img.onerror = () => reject(new Error(`Failed to load image: ${url}`));
      img.src = url;
    });

    this.cache.set(url, promise);
    return promise;
  }

  // 批量预加载图片
  preloadBatch(urls) {
    return Promise.allSettled(urls.map(url => this.preload(url)));
  }

  // 清理缓存
  clear() {
    this.cache.clear();
  }

  // 获取缓存大小
  getCacheSize() {
    return this.cache.size;
  }
}

// 创建全局实例
export const imagePreloader = new ImagePreloader();

// 从仓库列表中提取头像URL
export function extractAvatarUrls(repositories) {
  return repositories
    .map(repo => repo.owner?.avatar_url)
    .filter(Boolean)
    .filter((url, index, arr) => arr.indexOf(url) === index); // 去重
}