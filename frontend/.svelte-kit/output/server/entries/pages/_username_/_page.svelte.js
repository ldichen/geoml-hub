import { s as subscribe } from "../../../chunks/utils.js";
import { c as create_ssr_component, v as validate_component, e as escape } from "../../../chunks/ssr.js";
import { p as page } from "../../../chunks/stores.js";
import "../../../chunks/api.js";
import "../../../chunks/runtime.esm.js";
/* empty css                                                            */import { L as Loading } from "../../../chunks/Loading.js";
const UserProfile_svelte_svelte_type_style_lang = "";
const css = {
  code: ".bg-gray-50.svelte-x65247{background-color:#f9fafb}",
  map: null
};
const UserProfile = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { username } = $$props;
  let { currentUser = null } = $$props;
  if ($$props.username === void 0 && $$bindings.username && username !== void 0)
    $$bindings.username(username);
  if ($$props.currentUser === void 0 && $$bindings.currentUser && currentUser !== void 0)
    $$bindings.currentUser(currentUser);
  $$result.css.add(css);
  return `<div class="min-h-screen bg-gray-50 dark:bg-gray-900 svelte-x65247">${`<div class="flex items-center justify-center py-12">${validate_component(Loading, "Loading").$$render($$result, { size: "lg" }, {}, {})}</div>`} </div>`;
});
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $page, $$unsubscribe_page;
  $$unsubscribe_page = subscribe(page, (value) => $page = value);
  let currentUser = null;
  let username;
  username = $page.params.username;
  $$unsubscribe_page();
  return `${$$result.head += `<!-- HEAD_svelte-mc3r8t_START -->${$$result.title = `<title>@${escape(username)} - GeoML Hub</title>`, ""}<meta name="description" content="${"查看 @" + escape(username, true) + " 在 GeoML Hub 上的个人资料和仓库"}"><!-- HEAD_svelte-mc3r8t_END -->`, ""} ${validate_component(UserProfile, "UserProfile").$$render($$result, { username, currentUser }, {}, {})}`;
});
export {
  Page as default
};
