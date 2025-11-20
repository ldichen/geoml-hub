export const manifest = (() => {
function __memo(fn) {
	let value;
	return () => value ??= (value = fn());
}

return {
	appDir: "_app",
	appPath: "geoml-hub/_app",
	assets: new Set([".DS_Store","favicon.ico","logo.png","logo_light.png"]),
	mimeTypes: {".png":"image/png"},
	_: {
		client: {"start":"_app/immutable/entry/start.493b5206.js","app":"_app/immutable/entry/app.9deaeeba.js","imports":["_app/immutable/entry/start.493b5206.js","_app/immutable/chunks/scheduler.cc6cbc02.js","_app/immutable/chunks/singletons.434e14c9.js","_app/immutable/entry/app.9deaeeba.js","_app/immutable/chunks/preload-helper.a4192956.js","_app/immutable/chunks/scheduler.cc6cbc02.js","_app/immutable/chunks/index.cf161fb4.js"],"stylesheets":[],"fonts":[]},
		nodes: [
			__memo(() => import('./nodes/0.js')),
			__memo(() => import('./nodes/1.js')),
			__memo(() => import('./nodes/2.js')),
			__memo(() => import('./nodes/3.js')),
			__memo(() => import('./nodes/4.js')),
			__memo(() => import('./nodes/5.js')),
			__memo(() => import('./nodes/6.js')),
			__memo(() => import('./nodes/7.js')),
			__memo(() => import('./nodes/8.js')),
			__memo(() => import('./nodes/9.js')),
			__memo(() => import('./nodes/10.js')),
			__memo(() => import('./nodes/11.js')),
			__memo(() => import('./nodes/12.js')),
			__memo(() => import('./nodes/13.js')),
			__memo(() => import('./nodes/14.js')),
			__memo(() => import('./nodes/15.js')),
			__memo(() => import('./nodes/16.js')),
			__memo(() => import('./nodes/17.js')),
			__memo(() => import('./nodes/18.js')),
			__memo(() => import('./nodes/19.js')),
			__memo(() => import('./nodes/20.js')),
			__memo(() => import('./nodes/21.js')),
			__memo(() => import('./nodes/22.js')),
			__memo(() => import('./nodes/23.js'))
		],
		routes: [
			{
				id: "/",
				pattern: /^\/$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 3 },
				endpoint: null
			},
			{
				id: "/admin",
				pattern: /^\/admin\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 11 },
				endpoint: null
			},
			{
				id: "/admin/classifications",
				pattern: /^\/admin\/classifications\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 12 },
				endpoint: null
			},
			{
				id: "/admin/dashboard",
				pattern: /^\/admin\/dashboard\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 13 },
				endpoint: null
			},
			{
				id: "/admin/repositories",
				pattern: /^\/admin\/repositories\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 14 },
				endpoint: null
			},
			{
				id: "/admin/settings",
				pattern: /^\/admin\/settings\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 15 },
				endpoint: null
			},
			{
				id: "/admin/storage",
				pattern: /^\/admin\/storage\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 16 },
				endpoint: null
			},
			{
				id: "/admin/system",
				pattern: /^\/admin\/system\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 17 },
				endpoint: null
			},
			{
				id: "/admin/users",
				pattern: /^\/admin\/users\/?$/,
				params: [],
				page: { layouts: [0,2,], errors: [1,,], leaf: 18 },
				endpoint: null
			},
			{
				id: "/login",
				pattern: /^\/login\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 19 },
				endpoint: null
			},
			{
				id: "/new",
				pattern: /^\/new\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 20 },
				endpoint: null
			},
			{
				id: "/register",
				pattern: /^\/register\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 21 },
				endpoint: null
			},
			{
				id: "/search",
				pattern: /^\/search\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 22 },
				endpoint: null
			},
			{
				id: "/trending",
				pattern: /^\/trending\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 23 },
				endpoint: null
			},
			{
				id: "/[username]",
				pattern: /^\/([^/]+?)\/?$/,
				params: [{"name":"username","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,], errors: [1,], leaf: 4 },
				endpoint: null
			},
			{
				id: "/[username]/[repository]",
				pattern: /^\/([^/]+?)\/([^/]+?)\/?$/,
				params: [{"name":"username","optional":false,"rest":false,"chained":false},{"name":"repository","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,], errors: [1,], leaf: 5 },
				endpoint: null
			},
			{
				id: "/[username]/[repository]/blob/[...file_path]",
				pattern: /^\/([^/]+?)\/([^/]+?)\/blob(?:\/(.*))?\/?$/,
				params: [{"name":"username","optional":false,"rest":false,"chained":false},{"name":"repository","optional":false,"rest":false,"chained":false},{"name":"file_path","optional":false,"rest":true,"chained":true}],
				page: { layouts: [0,], errors: [1,], leaf: 6 },
				endpoint: null
			},
			{
				id: "/[username]/[repository]/commits/[...file_path]",
				pattern: /^\/([^/]+?)\/([^/]+?)\/commits(?:\/(.*))?\/?$/,
				params: [{"name":"username","optional":false,"rest":false,"chained":false},{"name":"repository","optional":false,"rest":false,"chained":false},{"name":"file_path","optional":false,"rest":true,"chained":true}],
				page: { layouts: [0,], errors: [1,], leaf: 7 },
				endpoint: null
			},
			{
				id: "/[username]/[repository]/drafts",
				pattern: /^\/([^/]+?)\/([^/]+?)\/drafts\/?$/,
				params: [{"name":"username","optional":false,"rest":false,"chained":false},{"name":"repository","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,], errors: [1,], leaf: 8 },
				endpoint: null
			},
			{
				id: "/[username]/[repository]/edit/[...file_path]",
				pattern: /^\/([^/]+?)\/([^/]+?)\/edit(?:\/(.*))?\/?$/,
				params: [{"name":"username","optional":false,"rest":false,"chained":false},{"name":"repository","optional":false,"rest":false,"chained":false},{"name":"file_path","optional":false,"rest":true,"chained":true}],
				page: { layouts: [0,], errors: [1,], leaf: 9 },
				endpoint: null
			},
			{
				id: "/[username]/[repository]/upload",
				pattern: /^\/([^/]+?)\/([^/]+?)\/upload\/?$/,
				params: [{"name":"username","optional":false,"rest":false,"chained":false},{"name":"repository","optional":false,"rest":false,"chained":false}],
				page: { layouts: [0,], errors: [1,], leaf: 10 },
				endpoint: null
			}
		],
		matchers: async () => {
			
			return {  };
		}
	}
}
})();
