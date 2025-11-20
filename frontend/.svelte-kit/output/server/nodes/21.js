import * as universal from '../entries/pages/register/_page.js';

export const index = 21;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/register/_page.svelte.js')).default;
export { universal };
export const universal_id = "src/routes/register/+page.js";
export const imports = ["_app/immutable/nodes/21.a26a563c.js","_app/immutable/chunks/scheduler.cc6cbc02.js","_app/immutable/chunks/index.cf161fb4.js","_app/immutable/chunks/paths.f059e082.js","_app/immutable/chunks/singletons.434e14c9.js","_app/immutable/chunks/auth.9aaca404.js","_app/immutable/chunks/preload-helper.a4192956.js","_app/immutable/chunks/runtime.d95da1ca.js"];
export const stylesheets = [];
export const fonts = [];
