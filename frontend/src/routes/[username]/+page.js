/*
 * @Author: DiChen
 * @Date: 2025-11-18
 * @LastEditors: DiChen
 * @LastEditTime: 2025-11-18
 */

// 用户页面 - 客户端渲染(动态内容)
export const prerender = false;
export const ssr = false;

export async function load({ params, fetch }) {
	// 这会在客户端执行
	try {
		const response = await fetch(`/api/users/${params.username}`);
		if (!response.ok) {
			return {
				user: null,
				error: 'User not found'
			};
		}
		const user = await response.json();
		return {
			user,
			meta: {
				title: `${user.username} - GeoML-Hub`,
				description: user.bio || `${user.username} 的模型仓库`,
				keywords: `${user.username},用户主页,模型仓库`
			}
		};
	} catch (error) {
		return {
			user: null,
			error: error.message
		};
	}
}
