import * as universal from '../entries/pages/login/_page.js';

export const index = 19;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/login/_page.svelte.js')).default;
export { universal };
export const universal_id = "src/routes/login/+page.js";
export const imports = ["_app/immutable/nodes/19.a2aa2b5e.js","_app/immutable/chunks/scheduler.cc6cbc02.js","_app/immutable/chunks/index.cf161fb4.js","_app/immutable/chunks/paths.f059e082.js","_app/immutable/chunks/singletons.434e14c9.js","_app/immutable/chunks/auth.9aaca404.js","_app/immutable/chunks/preload-helper.a4192956.js","_app/immutable/chunks/runtime.d95da1ca.js"];
export const stylesheets = ["_app/immutable/assets/19.d6a1033e.css"];
export const fonts = [];
