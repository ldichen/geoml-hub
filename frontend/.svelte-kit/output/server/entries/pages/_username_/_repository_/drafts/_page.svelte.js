import { s as subscribe } from "../../../../../chunks/utils.js";
import { c as create_ssr_component, e as escape, v as validate_component } from "../../../../../chunks/ssr.js";
import { p as page } from "../../../../../chunks/stores.js";
import { b as base } from "../../../../../chunks/paths.js";
import "../../../../../chunks/runtime.js";
import { B as Button } from "../../../../../chunks/Button.js";
import { L as Loading } from "../../../../../chunks/Loading.js";
const DraftManager_svelte_svelte_type_style_lang = "";
const _page_svelte_svelte_type_style_lang = "";
const css = {
  code: ".drafts-page.svelte-pq7omz{min-height:100vh;background:#f8f9fa}",
  map: null
};
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let username;
  let repositoryName;
  let draftStats;
  let $page, $$unsubscribe_page;
  $$unsubscribe_page = subscribe(page, (value) => $page = value);
  let userDrafts = [];
  let isLoading = true;
  $$result.css.add(css);
  username = $page.params.username;
  repositoryName = $page.params.repository;
  draftStats = {
    total: userDrafts.length,
    auto: userDrafts.filter((d) => d.is_auto_save).length,
    manual: userDrafts.filter((d) => !d.is_auto_save).length,
    totalSize: userDrafts.reduce((sum, d) => sum + new TextEncoder().encode(d.draft_content || "").length, 0)
  };
  $$unsubscribe_page();
  return `${$$result.head += `<!-- HEAD_svelte-1fc3bsc_START -->${$$result.title = `<title>草稿管理 - ${escape(repositoryName)} - GeoML-Hub</title>`, ""}<!-- HEAD_svelte-1fc3bsc_END -->`, ""} ${``} <div class="drafts-page svelte-pq7omz"> ${``}  <div class="bg-white border-b border-gray-200"><div class="container mx-auto px-4 py-6"><div class="flex items-center justify-between"><div><nav class="flex items-center space-x-2 text-sm text-gray-600 mb-2"><a href="${escape(base, true) + "/" + escape(username, true) + "/" + escape(repositoryName, true)}" class="hover:text-blue-600">${escape(repositoryName)}</a> <span data-svelte-h="svelte-ocknwt">/</span> <span class="text-blue-600 font-medium" data-svelte-h="svelte-1sqwzow">草稿管理</span></nav> <h1 class="text-2xl font-bold text-gray-900" data-svelte-h="svelte-1li02j4">草稿管理</h1> <p class="text-gray-600 mt-1" data-svelte-h="svelte-713ivd">管理您在此仓库中的所有草稿文件</p></div> <div class="flex items-center space-x-2">${validate_component(Button, "Button").$$render(
    $$result,
    {
      variant: "outline",
      size: "sm",
      disabled: isLoading
    },
    {},
    {
      default: () => {
        return `🔄 刷新`;
      }
    }
  )} ${validate_component(Button, "Button").$$render(
    $$result,
    {
      variant: "outline",
      size: "sm",
      disabled: userDrafts.length === 0
    },
    {},
    {
      default: () => {
        return `📤 导出`;
      }
    }
  )} ${validate_component(Button, "Button").$$render(
    $$result,
    {
      variant: "outline",
      size: "sm",
      disabled: draftStats.auto === 0
    },
    {},
    {
      default: () => {
        return `🗑️ 清理自动草稿`;
      }
    }
  )}</div></div></div></div>  <div class="bg-gray-50 border-b border-gray-200"><div class="container mx-auto px-4 py-4"><div class="grid grid-cols-2 md:grid-cols-4 gap-4"><div class="bg-white rounded-lg p-4 border border-gray-200"><div class="text-2xl font-bold text-gray-900">${escape(draftStats.total)}</div> <div class="text-sm text-gray-600" data-svelte-h="svelte-kulvng">总草稿数</div></div> <div class="bg-white rounded-lg p-4 border border-gray-200"><div class="text-2xl font-bold text-blue-600">${escape(draftStats.auto)}</div> <div class="text-sm text-gray-600" data-svelte-h="svelte-1i9t1fk">自动保存</div></div> <div class="bg-white rounded-lg p-4 border border-gray-200"><div class="text-2xl font-bold text-green-600">${escape(draftStats.manual)}</div> <div class="text-sm text-gray-600" data-svelte-h="svelte-129ahk3">手动保存</div></div> <div class="bg-white rounded-lg p-4 border border-gray-200"><div class="text-2xl font-bold text-purple-600">${escape(Math.round(draftStats.totalSize / 1024 * 100) / 100)}</div> <div class="text-sm text-gray-600" data-svelte-h="svelte-1uxg4v2">总大小 (KB)</div></div></div></div></div>  <div class="bg-white border-b border-gray-200"><div class="container mx-auto px-4 py-3"><div class="flex items-center space-x-4"><span class="text-sm font-medium text-gray-700" data-svelte-h="svelte-5btotz">筛选:</span> <div class="flex space-x-1">${validate_component(Button, "Button").$$render(
    $$result,
    {
      variant: "primary",
      size: "sm"
    },
    {},
    {
      default: () => {
        return `全部 (${escape(draftStats.total)})`;
      }
    }
  )} ${validate_component(Button, "Button").$$render(
    $$result,
    {
      variant: "ghost",
      size: "sm"
    },
    {},
    {
      default: () => {
        return `自动保存 (${escape(draftStats.auto)})`;
      }
    }
  )} ${validate_component(Button, "Button").$$render(
    $$result,
    {
      variant: "ghost",
      size: "sm"
    },
    {},
    {
      default: () => {
        return `手动保存 (${escape(draftStats.manual)})`;
      }
    }
  )}</div></div></div></div>  <div class="container mx-auto px-4 py-6">${`${validate_component(Loading, "Loading").$$render($$result, { message: "加载草稿中..." }, {}, {})}`}</div> </div>`;
});
export {
  Page as default
};
