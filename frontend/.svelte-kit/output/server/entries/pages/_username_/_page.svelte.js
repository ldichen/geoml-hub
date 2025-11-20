import { s as subscribe } from "../../../chunks/utils.js";
import { c as create_ssr_component, v as validate_component, e as escape } from "../../../chunks/ssr.js";
import { p as page } from "../../../chunks/stores.js";
import "../../../chunks/runtime.js";
/* empty css                                                            */import { L as Loading } from "../../../chunks/Loading.js";
import { user } from "../../../chunks/auth.js";
const UserProfile_svelte_svelte_type_style_lang = "";
const css = {
  code: ".bg-gray-50.svelte-1v5vq1c{background-color:#f9fafb}",
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
  return `<div class="min-h-screen bg-gray-50 dark:bg-gray-900 svelte-1v5vq1c">${`<div class="flex items-center justify-center py-12">${validate_component(Loading, "Loading").$$render($$result, { size: "lg" }, {}, {})}</div>`} </div>`;
});
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $user, $$unsubscribe_user;
  let $page, $$unsubscribe_page;
  $$unsubscribe_user = subscribe(user, (value) => $user = value);
  $$unsubscribe_page = subscribe(page, (value) => $page = value);
  let currentUser = null;
  let username;
  username = $page.params.username;
  currentUser = $user;
  $$unsubscribe_user();
  $$unsubscribe_page();
  return `${$$result.head += `<!-- HEAD_svelte-ehn6az_START -->${$$result.title = `<title>@${escape(username)} - GeoML Hub</title>`, ""}<meta name="description" content="${"查看 @" + escape(username, true) + " 在 GeoML Hub 上的个人资料和仓库"}"><!-- HEAD_svelte-ehn6az_END -->`, ""} ${validate_component(UserProfile, "UserProfile").$$render($$result, { username, currentUser }, {}, {})}`;
});
export {
  Page as default
};
