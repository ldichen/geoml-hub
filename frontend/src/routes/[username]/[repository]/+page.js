/*
 * @Author: DiChen
 * @Date: 2025-11-18
 * @LastEditors: DiChen
 * @LastEditTime: 2025-11-18
 */

// 仓库页面 - 客户端渲染(动态内容)
export const prerender = false;
export const ssr = false;

export async function load({ params, fetch }) {
	// 这会在客户端执行
	try {
		const response = await fetch(`/api/repositories/${params.username}/${params.repository}`);
		if (!response.ok) {
			return {
				repository: null,
				error: 'Repository not found'
			};
		}
		const repository = await response.json();
		return {
			repository,
			meta: {
				title: `${params.username}/${params.repository} - GeoML-Hub`,
				description: repository.description || `${params.username}/${params.repository} 模型仓库`,
				keywords: `${params.repository},模型仓库,${params.username},机器学习模型`
			}
		};
	} catch (error) {
		return {
			repository: null,
			error: error.message
		};
	}
}
