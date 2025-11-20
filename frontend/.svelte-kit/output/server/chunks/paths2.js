import { b as base } from "./paths.js";
const PATHS = {
  // 主要页面
  HOME: base || "/",
  LOGIN: `${base}/login`,
  REGISTER: `${base}/register`,
  TRENDING: `${base}/trending`,
  SEARCH: `${base}/search`,
  NEW_REPO: `${base}/new`,
  ADMIN: `${base}/admin`,
  SETTINGS: `${base}/settings`,
  // 动态路径生成函数
  /**
   * 用户主页路径
   * @param {string} username - 用户名
   * @returns {string} 用户主页路径
   */
  user: (username) => `${base}/${username}`,
  /**
   * 仓库路径
   * @param {string} username - 用户名
   * @param {string} repoName - 仓库名
   * @returns {string} 仓库路径
   */
  repo: (username, repoName) => `${base}/${username}/${repoName}`,
  /**
   * 仓库文件路径
   * @param {string} username - 用户名
   * @param {string} repoName - 仓库名
   * @returns {string} 仓库文件路径
   */
  repoFiles: (username, repoName) => `${base}/${username}/${repoName}/files`,
  /**
   * 仓库版本路径
   * @param {string} username - 用户名
   * @param {string} repoName - 仓库名
   * @returns {string} 仓库版本路径
   */
  repoVersions: (username, repoName) => `${base}/${username}/${repoName}/versions`,
  /**
   * 仓库社区路径
   * @param {string} username - 用户名
   * @param {string} repoName - 仓库名
   * @returns {string} 仓库社区路径
   */
  repoCommunity: (username, repoName) => `${base}/${username}/${repoName}/community`,
  /**
   * 仓库设置路径
   * @param {string} username - 用户名
   * @param {string} repoName - 仓库名
   * @returns {string} 仓库设置路径
   */
  repoSettings: (username, repoName) => `${base}/${username}/${repoName}/settings`,
  /**
   * 仓库上传路径
   * @param {string} username - 用户名
   * @param {string} repoName - 仓库名
   * @returns {string} 仓库上传路径
   */
  repoUpload: (username, repoName) => `${base}/${username}/${repoName}/upload`,
  /**
   * 仓库草稿箱路径
   * @param {string} username - 用户名
   * @param {string} repoName - 仓库名
   * @returns {string} 仓库草稿箱路径
   */
  repoDrafts: (username, repoName) => `${base}/${username}/${repoName}/drafts`
};
export {
  PATHS as P
};
