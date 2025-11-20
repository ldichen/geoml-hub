import * as universal from '../entries/pages/admin/_layout.js';

export const index = 2;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/admin/_layout.svelte.js')).default;
export { universal };
export const universal_id = "src/routes/admin/+layout.js";
export const imports = ["_app/immutable/nodes/2.2e7775e1.js","_app/immutable/chunks/scheduler.cc6cbc02.js","_app/immutable/chunks/index.cf161fb4.js","_app/immutable/chunks/each.61c71743.js","_app/immutable/chunks/paths.f059e082.js","_app/immutable/chunks/singletons.434e14c9.js","_app/immutable/chunks/stores.67836202.js","_app/immutable/chunks/api.ecdb55f2.js","_app/immutable/chunks/preload-helper.a4192956.js"];
export const stylesheets = [];
export const fonts = [];
