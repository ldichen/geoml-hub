export { matchers } from './matchers.js';

export const nodes = [
	() => import('./nodes/0'),
	() => import('./nodes/1'),
	() => import('./nodes/2'),
	() => import('./nodes/3'),
	() => import('./nodes/4'),
	() => import('./nodes/5'),
	() => import('./nodes/6'),
	() => import('./nodes/7'),
	() => import('./nodes/8'),
	() => import('./nodes/9'),
	() => import('./nodes/10'),
	() => import('./nodes/11'),
	() => import('./nodes/12'),
	() => import('./nodes/13'),
	() => import('./nodes/14'),
	() => import('./nodes/15'),
	() => import('./nodes/16'),
	() => import('./nodes/17'),
	() => import('./nodes/18'),
	() => import('./nodes/19'),
	() => import('./nodes/20'),
	() => import('./nodes/21'),
	() => import('./nodes/22'),
	() => import('./nodes/23')
];

export const server_loads = [];

export const dictionary = {
		"/": [3],
		"/admin": [11,[2]],
		"/admin/classifications": [12,[2]],
		"/admin/dashboard": [13,[2]],
		"/admin/repositories": [14,[2]],
		"/admin/settings": [15,[2]],
		"/admin/storage": [16,[2]],
		"/admin/system": [17,[2]],
		"/admin/users": [18,[2]],
		"/login": [19],
		"/new": [20],
		"/register": [21],
		"/search": [22],
		"/trending": [23],
		"/[username]": [4],
		"/[username]/[repository]": [5],
		"/[username]/[repository]/blob/[...file_path]": [6],
		"/[username]/[repository]/commits/[...file_path]": [7],
		"/[username]/[repository]/drafts": [8],
		"/[username]/[repository]/edit/[...file_path]": [9],
		"/[username]/[repository]/upload": [10]
	};

export const hooks = {
	handleError: (({ error }) => { console.error(error) }),
};

export { default as root } from '../root.svelte';