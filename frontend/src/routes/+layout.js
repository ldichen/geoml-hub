/*
 * @Author: DiChen
 * @Date: 2025-07-10 11:01:27
 * @LastEditors: DiChen
 * @LastEditTime: 2025-11-18 11:44:46
 */
import '$lib/i18n';

export const prerender = true;

export async function load({ fetch }) {
	// 如果需要数据，可以在这里获取
	// 构建时会调用这个函数
	return {
		meta: {
			title: 'GeoML-Hub - 地理科学机器学习模型仓库',
			description: '首个专注于地理科学的机器学习模型中心'
		}
	};
}
