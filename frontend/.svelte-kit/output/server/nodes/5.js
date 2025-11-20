import * as universal from '../entries/pages/_username_/_repository_/_page.js';

export const index = 5;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_username_/_repository_/_page.svelte.js')).default;
export { universal };
export const universal_id = "src/routes/[username]/[repository]/+page.js";
export const imports = ["_app/immutable/nodes/5.98ccd547.js","_app/immutable/chunks/scheduler.cc6cbc02.js","_app/immutable/chunks/index.cf161fb4.js","_app/immutable/chunks/globals.7f7f1b26.js","_app/immutable/chunks/each.61c71743.js","_app/immutable/chunks/stores.67836202.js","_app/immutable/chunks/singletons.434e14c9.js","_app/immutable/chunks/index.740a659d.js","_app/immutable/chunks/Icon.46e6b690.js","_app/immutable/chunks/runtime.d95da1ca.js","_app/immutable/chunks/marked.esm.da5dbf02.js","_app/immutable/chunks/api.ecdb55f2.js","_app/immutable/chunks/preload-helper.a4192956.js","_app/immutable/chunks/paths.f059e082.js","_app/immutable/chunks/UserAvatar.7db75443.js","_app/immutable/chunks/SocialButton.72205b7a.js","_app/immutable/chunks/Loading.1b4bc8d5.js","_app/immutable/chunks/trash-2.203bd6b4.js","_app/immutable/chunks/settings.b929de90.js","_app/immutable/chunks/plus.f9cebbd6.js","_app/immutable/chunks/x.4163c2e3.js","_app/immutable/chunks/x-circle.ffb40c6b.js","_app/immutable/chunks/check-circle.fa3fed57.js","_app/immutable/chunks/trending-up.a9655000.js","_app/immutable/chunks/search.ca89ca30.js","_app/immutable/chunks/filter.60664ee3.js","_app/immutable/chunks/upload.f8eea0db.js","_app/immutable/chunks/chevron-right.b4e336e6.js","_app/immutable/chunks/chevron-down.91abe687.js"];
export const stylesheets = ["_app/immutable/assets/5.3c9e612b.css","_app/immutable/assets/ClassificationSelector.9f969cb0.css"];
export const fonts = [];
