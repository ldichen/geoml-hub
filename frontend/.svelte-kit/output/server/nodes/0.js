import * as universal from '../entries/pages/_layout.js';

export const index = 0;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_layout.svelte.js')).default;
export { universal };
export const universal_id = "src/routes/+layout.js";
export const imports = ["_app/immutable/nodes/0.b21c7837.js","_app/immutable/chunks/preload-helper.a4192956.js","_app/immutable/chunks/runtime.d95da1ca.js","_app/immutable/chunks/singletons.434e14c9.js","_app/immutable/chunks/scheduler.cc6cbc02.js","_app/immutable/chunks/index.cf161fb4.js","_app/immutable/chunks/auth.9aaca404.js","_app/immutable/chunks/each.61c71743.js","_app/immutable/chunks/UserAvatar.7db75443.js","_app/immutable/chunks/Icon.46e6b690.js","_app/immutable/chunks/globe.205fd586.js","_app/immutable/chunks/plus.f9cebbd6.js","_app/immutable/chunks/settings.b929de90.js","_app/immutable/chunks/x.4163c2e3.js","_app/immutable/chunks/Toast.7c8dc121.js","_app/immutable/chunks/x-circle.ffb40c6b.js","_app/immutable/chunks/check-circle.fa3fed57.js"];
export const stylesheets = ["_app/immutable/assets/0.2a312129.css"];
export const fonts = [];
