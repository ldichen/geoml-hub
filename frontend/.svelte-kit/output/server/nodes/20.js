import * as universal from '../entries/pages/new/_page.js';

export const index = 20;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/new/_page.svelte.js')).default;
export { universal };
export const universal_id = "src/routes/new/+page.js";
export const imports = ["_app/immutable/nodes/20.6f265ac3.js","_app/immutable/chunks/scheduler.cc6cbc02.js","_app/immutable/chunks/index.cf161fb4.js","_app/immutable/chunks/each.61c71743.js","_app/immutable/chunks/paths.f059e082.js","_app/immutable/chunks/singletons.434e14c9.js","_app/immutable/chunks/runtime.d95da1ca.js","_app/immutable/chunks/api.ecdb55f2.js","_app/immutable/chunks/preload-helper.a4192956.js","_app/immutable/chunks/Loading.1b4bc8d5.js"];
export const stylesheets = ["_app/immutable/assets/ClassificationSelector.9f969cb0.css"];
export const fonts = [];
