import { s as subscribe } from "../../../../../../chunks/utils.js";
import { c as create_ssr_component, o as onDestroy, e as escape, v as validate_component } from "../../../../../../chunks/ssr.js";
import { p as page } from "../../../../../../chunks/stores.js";
import { u as user } from "../../../../../../chunks/auth.js";
import "../../../../../../chunks/runtime.esm.js";
import { B as Button } from "../../../../../../chunks/Button.js";
import { L as Loading } from "../../../../../../chunks/Loading.js";
const EditorToolbar_svelte_svelte_type_style_lang = "";
const EditorStatusBar_svelte_svelte_type_style_lang = "";
const EditorSidebar_svelte_svelte_type_style_lang = "";
const FileEditor_svelte_svelte_type_style_lang = "";
const _page_svelte_svelte_type_style_lang = "";
const css = {
  code: ".file-edit-page.svelte-1km4msp{background:#f8f9fa}.metadata-block .yaml-key{color:#9cdcfe;font-weight:600}.metadata-block .yaml-value{color:#ce9178}.metadata-block .yaml-comment{color:#6a9955;font-style:italic}.metadata-block{box-shadow:0 1px 3px rgba(0, 0, 0, 0.1)}.metadata-block pre{margin:0;line-height:1.4}",
  map: null
};
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let repositoryName;
  let $$unsubscribe_currentUser;
  let $page, $$unsubscribe_page;
  $$unsubscribe_currentUser = subscribe(user, (value) => value);
  $$unsubscribe_page = subscribe(page, (value) => $page = value);
  let isModified = false;
  onDestroy(() => {
    window.removeEventListener("beforeunload", handleBeforeUnload);
  });
  function handleBeforeUnload(event) {
  }
  $$result.css.add(css);
  $page.params.username;
  repositoryName = $page.params.repository;
  $page.params.file_path;
  $$unsubscribe_currentUser();
  $$unsubscribe_page();
  return `${$$result.head += `<!-- HEAD_svelte-1tvqyyz_START -->${$$result.title = `<title>编辑 ${escape("文件")} - ${escape(repositoryName)} - GeoML-Hub</title>`, ""}<!-- HEAD_svelte-1tvqyyz_END -->`, ""} ${``} <div class="file-edit-page h-screen flex flex-col svelte-1km4msp"> ${``}  <div class="bg-white border-b border-gray-200"> ${` <div class="container px-4 py-2 flex items-center justify-between"><div class="flex items-center space-x-4"><div class="text-sm text-gray-600" data-svelte-h="svelte-1wm5ki3">编辑模式</div>  ${``}</div> <div class="flex items-center space-x-2">${validate_component(Button, "Button").$$render($$result, { variant: "outline", size: "sm" }, {}, {
    default: () => {
      return `返回`;
    }
  })} ${validate_component(Button, "Button").$$render(
    $$result,
    {
      variant: "primary",
      size: "sm",
      disabled: !isModified
    },
    {},
    {
      default: () => {
        return `${escape("保存更改")}`;
      }
    }
  )}</div></div>`}</div>  <div class="container border-r border-l border-b rounded-lg flex-1 mb-4 overflow-hidden" style="padding-right: 0;">${`${validate_component(Loading, "Loading").$$render($$result, { message: "加载编辑器中..." }, {}, {})}`}</div></div>  ${``}  ${``}  ${``}`;
});
export {
  Page as default
};
