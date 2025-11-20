import * as universal from '../entries/pages/trending/_page.js';

export const index = 23;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/trending/_page.svelte.js')).default;
export { universal };
export const universal_id = "src/routes/trending/+page.js";
export const imports = ["_app/immutable/nodes/23.907dafa0.js","_app/immutable/chunks/scheduler.cc6cbc02.js","_app/immutable/chunks/index.cf161fb4.js","_app/immutable/chunks/each.61c71743.js","_app/immutable/chunks/singletons.434e14c9.js","_app/immutable/chunks/runtime.d95da1ca.js","_app/immutable/chunks/api.ecdb55f2.js","_app/immutable/chunks/preload-helper.a4192956.js","_app/immutable/chunks/paths.f059e082.js","_app/immutable/chunks/RepositoryCard.a398c680.js","_app/immutable/chunks/index.740a659d.js","_app/immutable/chunks/Icon.46e6b690.js","_app/immutable/chunks/UserAvatar.7db75443.js","_app/immutable/chunks/lock.d73067bf.js","_app/immutable/chunks/chevron-right.b4e336e6.js","_app/immutable/chunks/Loading.1b4bc8d5.js","_app/immutable/chunks/trending-up.a9655000.js","_app/immutable/chunks/filter.60664ee3.js"];
export const stylesheets = ["_app/immutable/assets/RepositoryCard.5ea517bc.css"];
export const fonts = [];
