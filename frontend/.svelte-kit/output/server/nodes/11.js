

export const index = 11;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/admin/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/11.038a2313.js","_app/immutable/chunks/scheduler.cc6cbc02.js","_app/immutable/chunks/index.cf161fb4.js","_app/immutable/chunks/paths.f059e082.js","_app/immutable/chunks/singletons.434e14c9.js"];
export const stylesheets = [];
export const fonts = [];
