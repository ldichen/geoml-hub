import { s as subscribe } from "../../chunks/utils.js";
import { c as create_ssr_component, e as escape, a as each, v as validate_component, b as createEventDispatcher, d as add_attribute } from "../../chunks/ssr.js";
import { $ as $format } from "../../chunks/runtime.js";
/* empty css                                                         */import { formatDistanceToNow } from "date-fns";
import zhCN from "date-fns/locale/zh-CN/index.js";
import { b as base } from "../../chunks/paths.js";
import { S as Star, D as Download, E as Eye } from "../../chunks/star.js";
import { S as Search } from "../../chunks/search.js";
import { X } from "../../chunks/x.js";
import { L as Loading } from "../../chunks/Loading.js";
import { isAuthenticated, user } from "../../chunks/auth.js";
import { T as TrendingUp } from "../../chunks/trending-up.js";
const MiniRepositoryCard_svelte_svelte_type_style_lang = "";
const css$1 = {
  code: ".mini-repository-card.svelte-gwygt1{background:linear-gradient(to right, var(--color-gray-50), var(--color-white))}.mini-repository-card.svelte-gwygt1:hover{background:linear-gradient(to right, var(--color-gray-100), var(--color-gray-50))}.line-clamp-2.svelte-gwygt1{display:-webkit-box;-webkit-line-clamp:2;line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}",
  map: null
};
const MiniRepositoryCard = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { repo } = $$props;
  if ($$props.repo === void 0 && $$bindings.repo && repo !== void 0)
    $$bindings.repo(repo);
  $$result.css.add(css$1);
  return `<a href="${escape(base, true) + "/" + escape(repo.owner?.username || "unknown", true) + "/" + escape(repo.name, true)}" class="mini-repository-card group block rounded-lg border border-gray-200 dark:border-gray-700 p-3 transition-all duration-200 svelte-gwygt1"> <div class="flex items-center mb-2"><span class="text-sm font-mono font-medium text-gray-700 dark:text-gray-300 truncate group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">${escape(repo.name)}</span></div>  ${repo.description ? `<p class="text-xs text-gray-600 dark:text-gray-400 mb-2 line-clamp-2 svelte-gwygt1">${escape(repo.description)}</p>` : ``}  <div class="flex items-center justify-between gap-4"> <div class="flex items-center gap-1.5 flex-wrap flex-1 min-w-0">${repo.task_classifications_data && repo.task_classifications_data.length > 0 ? `${each(repo.task_classifications_data, (task) => {
    return `<span class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-purple-50 text-purple-700 border border-purple-100 dark:bg-purple-950 dark:text-purple-300 dark:border-purple-900 shadow-sm">${escape(task.name)} </span>`;
  })}` : ``}</div>  <div class="flex items-center gap-3 flex-shrink-0"> <div class="flex items-center space-x-3 text-xs text-gray-500 dark:text-gray-400"><div class="flex items-center space-x-1">${validate_component(Star, "Star").$$render($$result, { class: "h-3 w-3" }, {}, {})} <span>${escape(repo.stars_count)}</span></div> <div class="flex items-center space-x-1">${validate_component(Download, "Download").$$render($$result, { class: "h-3 w-3" }, {}, {})} <span>${escape(repo.downloads_count)}</span></div> <div class="flex items-center space-x-1">${validate_component(Eye, "Eye").$$render($$result, { class: "h-3 w-3" }, {}, {})} <span>${escape(repo.views_count)}</span></div></div>  <span class="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">${escape(formatDistanceToNow(new Date(repo.updated_at), { addSuffix: true, locale: zhCN }))}</span></div></div> </a>`;
});
const SearchBar = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $_, $$unsubscribe__;
  $$unsubscribe__ = subscribe($format, (value2) => $_ = value2);
  let { value = "" } = $$props;
  let { placeholder = "" } = $$props;
  createEventDispatcher();
  if ($$props.value === void 0 && $$bindings.value && value !== void 0)
    $$bindings.value(value);
  if ($$props.placeholder === void 0 && $$bindings.placeholder && placeholder !== void 0)
    $$bindings.placeholder(placeholder);
  $$unsubscribe__();
  return `<div class="relative"><div class="relative"><div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">${validate_component(Search, "Search").$$render($$result, { class: "h-5 w-5 text-gray-400" }, {}, {})}</div> <input type="text" class="block w-full pl-10 pr-20 py-3 text-gray-900 dark:text-white bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"${add_attribute("placeholder", placeholder || $_("search.placeholder"), 0)}${add_attribute("value", value, 0)}> ${value ? `<div class="absolute inset-y-0 right-16 pr-3 flex items-center"><button type="button" class="p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">${validate_component(X, "X").$$render($$result, { class: "h-4 w-4 text-gray-400" }, {}, {})}</button></div>` : ``}</div> <div class="absolute right-2 top-1/2 transform -translate-y-1/2"><button type="button" class="px-4 py-2 bg-blue-500 hover:bg-blue-700 text-white font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2" data-svelte-h="svelte-1rc527y">Search</button></div></div>`;
});
const _page_svelte_svelte_type_style_lang = "";
const css = {
  code: ".bg-gradient-to-r.svelte-13o7pik{background:linear-gradient(to right, var(--tw-gradient-stops))}",
  map: null
};
function getAllClassifications(classifications2, result = []) {
  for (const classification of classifications2) {
    result.push(classification);
    if (classification.children && classification.children.length > 0) {
      getAllClassifications(classification.children, result);
    }
  }
  return result;
}
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let allClassifications;
  let level1Classifications;
  let level2Classifications;
  let level3Classifications;
  let $$unsubscribe_isAuthenticated;
  let $$unsubscribe_user;
  $$unsubscribe_isAuthenticated = subscribe(isAuthenticated, (value) => value);
  $$unsubscribe_user = subscribe(user, (value) => value);
  let classifications = [];
  let taskClassifications = [];
  let searchQuery = "";
  let selectedClassifications = /* @__PURE__ */ new Set();
  let selectedTaskClassifications = /* @__PURE__ */ new Set();
  let selectedTags = /* @__PURE__ */ new Set();
  let selectedLicenses = /* @__PURE__ */ new Set();
  let trendingRepositories = [];
  const commonTags = [
    "Pytorch",
    "TensorFlow",
    "JAX",
    "Transformers",
    "Diffusers",
    "Safetensors",
    "ONNX",
    "GGUF",
    "keras",
    "timm"
  ];
  const commonLicenses = [
    "MIT",
    "Apache-2.0",
    "GPL-3.0",
    "BSD-3-Clause",
    "BSD-2-Clause",
    "LGPL-3.0",
    "MPL-2.0",
    "ISC",
    "AGPL-3.0",
    "Unlicense",
    "CC-BY-4.0",
    "CC-BY-SA-4.0",
    "CC0-1.0",
    "WTFPL",
    "Zlib"
  ];
  $$result.css.add(css);
  let $$settled;
  let $$rendered;
  let previous_head = $$result.head;
  do {
    $$settled = true;
    $$result.head = previous_head;
    allClassifications = getAllClassifications(classifications);
    level1Classifications = classifications.filter((c) => c.level === 1);
    level2Classifications = allClassifications.filter((c) => c.level === 2);
    level3Classifications = allClassifications.filter((c) => c.level === 3);
    $$rendered = `${$$result.head += `<!-- HEAD_svelte-1b3igg2_START -->${$$result.title = `<title>GeoML Hub - 地理科学机器学习模型库</title>`, ""}<meta name="description" content="为地理科学设计的机器学习模型库，发现、分享和部署地理空间AI模型"><!-- HEAD_svelte-1b3igg2_END -->`, ""} <div class="min-h-screen dark:bg-gray-900"> <div class="bg-white"><div class="container py-4"><div class="text-center"><h1 class="text-4xl sm:text-4xl font-bold text-black mb-2" data-svelte-h="svelte-6w5s67">🌍 GeoML Hub</h1> <p class="text-l text-gray-500 mb-2 max-w-3xl mx-auto" data-svelte-h="svelte-1biq0jl">地理科学设计的机器学习模型库 - 发现、分享和部署地理空间AI模型</p>  <div class="max-w-2xl mx-auto">${validate_component(SearchBar, "SearchBar").$$render(
      $$result,
      {
        placeholder: "搜索模型、数据集、用户...",
        value: searchQuery
      },
      {
        value: ($$value) => {
          searchQuery = $$value;
          $$settled = false;
        }
      },
      {}
    )}</div></div></div></div>  <div class="border-t border-gray-200"></div> <div class="container bg-white">   <div class="flex flex-col lg:flex-row gap-6"> <div class="lg:w-[25%] border-gray-100 lg:border-r pt-8 flex-shrink-0 min-h-screen sidebar-gradient-left"><div class="p-2"> <div class="border-b border-gray-200 dark:border-gray-700 mb-6"><nav class="flex w-full" aria-label="Tabs"><button class="${"flex-1 py-2 px-0.5 sm:px-1 border-b-2 font-semibold text-sm " + escape(
      "border-blue-500 text-blue-600 dark:text-blue-400",
      true
    )}">Main</button> <button class="${"flex-1 py-2 px-0.5 sm:px-1 border-b-2 font-semibold text-sm " + escape(
      "border-transparent text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-300",
      true
    )}">Class</button> <button class="${"flex-1 py-2 px-0.5 sm:px-1 border-b-2 font-semibold text-sm " + escape(
      "border-transparent text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-300",
      true
    )}">Tasks</button> <button class="${"flex-1 py-2 px-0.5 sm:px-1 border-b-2 font-semibold text-sm " + escape(
      "border-transparent text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-300",
      true
    )}">Libraries</button> <button class="${"flex-1 py-2 px-0.5 sm:px-1 border-b-2 font-semibold text-sm " + escape(
      "border-transparent text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-300",
      true
    )}">Licenses</button></nav></div>  ${`<div class="space-y-6"> ${level1Classifications.length > 0 ? `<div><div class="flex items-center justify-between mb-3"><h4 class="text-sm font-medium text-gray-500 dark:text-gray-300" data-svelte-h="svelte-1qo5ypo">一级分类</h4> ${level1Classifications.some((c) => selectedClassifications.has(c.id)) ? `<button class="inline-flex items-center text-sm font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors" data-svelte-h="svelte-ar102a"><svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
												Reset</button>` : ``}</div> <div class="flex flex-wrap gap-2">${each(
      level1Classifications.slice(0, 10),
      (classification) => {
        return `<button class="${"inline-flex items-center px-3 py-1 rounded-md text-sm font-medium transition-colors border " + escape(
          selectedClassifications.has(classification.id) ? "bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-700" : "bg-white text-gray-700 border-gray-300 hover:bg-gray-100 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700",
          true
        )}">${escape(classification.name)} </button>`;
      }
    )} ${level1Classifications.length > 10 ? `<button class="inline-flex items-center px-3 py-1 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors">${escape(`+ ${level1Classifications.length - 10}`)}</button>` : ``}</div></div>` : ``}  ${level2Classifications.length > 0 ? `<div><div class="flex items-center justify-between mb-3"><h4 class="text-sm font-medium text-gray-500 dark:text-gray-300" data-svelte-h="svelte-16b1j74">二级分类</h4> ${level2Classifications.some((c) => selectedClassifications.has(c.id)) ? `<button class="inline-flex items-center text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors" data-svelte-h="svelte-2rzmgg"><svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
												Reset</button>` : ``}</div> <div class="flex flex-wrap gap-2">${each(
      level2Classifications.slice(0, 10),
      (classification) => {
        return `<button class="${"inline-flex items-center px-3 py-1 rounded-md text-sm font-medium transition-colors border " + escape(
          selectedClassifications.has(classification.id) ? "bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-700" : "bg-white text-gray-700 border-gray-300 hover:bg-gray-100 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700",
          true
        )}">${escape(classification.name)} </button>`;
      }
    )} ${level2Classifications.length > 10 ? `<button class="inline-flex items-center px-3 py-1 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors">${escape(`+ ${level2Classifications.length - 10}`)}</button>` : ``}</div></div>` : ``}  ${level3Classifications.length > 0 ? `<div><div class="flex items-center justify-between mb-3"><h4 class="text-sm font-medium text-gray-500 dark:text-gray-300" data-svelte-h="svelte-1lucbt3">三级分类</h4> ${level3Classifications.some((c) => selectedClassifications.has(c.id)) ? `<button class="inline-flex items-center text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors" data-svelte-h="svelte-7eipkr"><svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
												Reset</button>` : ``}</div> <div class="flex flex-wrap gap-2">${each(
      level3Classifications.slice(0, 10),
      (classification) => {
        return `<button class="${"inline-flex items-center px-3 py-1 rounded-md text-sm font-medium transition-colors border " + escape(
          selectedClassifications.has(classification.id) ? "bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-700" : "bg-white text-gray-700 border-gray-300 hover:bg-gray-100 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700",
          true
        )}">${escape(classification.name)} </button>`;
      }
    )} ${level3Classifications.length > 10 ? `<button class="inline-flex items-center px-3 py-1 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors">${escape(`+ ${level3Classifications.length - 10}`)}</button>` : ``}</div></div>` : ``}  ${taskClassifications.length > 0 ? `<div><div class="flex items-center justify-between mb-3"><h4 class="text-sm font-medium text-gray-500 dark:text-gray-300" data-svelte-h="svelte-18svehg">Tasks</h4> ${selectedTaskClassifications.size > 0 ? `<button class="inline-flex items-center text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors" data-svelte-h="svelte-1k7ojy5"><svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
												Reset</button>` : ``}</div> <div class="flex flex-wrap gap-2">${each(taskClassifications, (task) => {
      return `<button class="${"inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-sm font-medium transition-colors border " + escape(
        selectedTaskClassifications.has(task.id) ? "bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-700" : "bg-white text-gray-700 border-gray-300 hover:bg-gray-100 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700",
        true
      )}"><span>${escape(task.name)}</span> </button>`;
    })}</div></div>` : ``}  ${commonTags.length > 0 ? `<div><div class="flex items-center justify-between mb-3"><h4 class="text-sm font-medium text-gray-500 dark:text-gray-300" data-svelte-h="svelte-14x0yel">Libraries</h4> ${selectedTags.size > 0 ? `<button class="inline-flex items-center text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors" data-svelte-h="svelte-bu22yy"><svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
												Reset</button>` : ``}</div> <div class="flex flex-wrap gap-2">${each(commonTags.slice(0, 10), (tag) => {
      return `<button class="${"inline-flex items-center px-3 py-1 rounded-md text-sm font-medium transition-colors border " + escape(
        selectedTags.has(tag) ? "bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-700" : "bg-white text-gray-700 border-gray-300 hover:bg-gray-100 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700",
        true
      )}">${escape(tag)} </button>`;
    })} ${commonTags.length > 10 ? `<button class="inline-flex items-center px-3 py-1 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors">${escape(`+ ${commonTags.length - 10}`)}</button>` : ``}</div></div>` : ``}  ${commonLicenses.length > 0 ? `<div><div class="flex items-center justify-between mb-3"><h4 class="text-sm font-medium text-gray-500 dark:text-gray-300" data-svelte-h="svelte-wu18ea">Licenses</h4> ${selectedLicenses.size > 0 ? `<button class="inline-flex items-center text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors" data-svelte-h="svelte-1wviumv"><svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
												Reset</button>` : ``}</div> <div class="flex flex-wrap gap-2">${each(
      commonLicenses.slice(0, 10),
      (license) => {
        return `<button class="${"inline-flex items-center px-3 py-1 rounded-md text-sm font-medium transition-colors border " + escape(
          selectedLicenses.has(license) ? "bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-700" : "bg-white text-gray-700 border-gray-300 hover:bg-gray-100 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700",
          true
        )}">${escape(license)} </button>`;
      }
    )} ${commonLicenses.length > 10 ? `<button class="inline-flex items-center px-3 py-1 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors">${escape(`+ ${commonLicenses.length - 10}`)}</button>` : ``}</div></div>` : ``}</div>`}</div></div>  <div class="lg:w-[50%] pt-8 flex-1 repository-list">${`<div class="flex items-center justify-center py-12">${validate_component(Loading, "Loading").$$render($$result, { size: "lg" }, {}, {})}</div>`}</div>  <div class="lg:w-[25%] border-gray-100 lg:border-l pt-8 flex-shrink-0 min-h-screen sidebar-gradient-right"><div class="p-2"> <div class="mb-6"><div class="flex items-center"><div class="flex items-center space-x-2">${validate_component(TrendingUp, "TrendingUp").$$render(
      $$result,
      {
        class: "h-5 w-5 text-gray-500 dark:text-gray-400"
      },
      {},
      {}
    )} <h3 class="text-xl font-semibold text-gray-900 dark:text-white" data-svelte-h="svelte-k51wpr">Trending</h3></div> <span class="text-xs font-semibold text-gray-600 dark:text-gray-400 dark:bg-gray-700 px-2 py-1 ml-4" data-svelte-h="svelte-fl3kq2">last 7 days</span></div></div>  <div class="border-b border-gray-200 dark:border-gray-700 mb-6"><nav class="flex space-x-2 sm:space-x-4 lg:space-x-6" aria-label="Trending Tabs"><button class="${"py-2 px-0.5 sm:px-1 border-b-2 font-medium text-xs sm:text-sm " + escape(
      "border-blue-500 text-blue-600 dark:text-blue-400",
      true
    )}">精选</button> <button class="${"py-2 px-0.5 sm:px-1 border-b-2 font-medium text-xs sm:text-sm " + escape(
      "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300",
      true
    )}">热门</button> <button class="${"py-2 px-0.5 sm:px-1 border-b-2 font-medium text-xs sm:text-sm " + escape(
      "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300",
      true
    )}">最新</button> <button class="${"py-2 px-0.5 sm:px-1 border-b-2 font-medium text-xs sm:text-sm " + escape(
      "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300",
      true
    )}">推荐</button></nav></div>  <div class="space-y-3">${`${trendingRepositories.length > 0 ? `${each(trendingRepositories, (repo) => {
      return `${validate_component(MiniRepositoryCard, "MiniRepositoryCard").$$render($$result, { repo }, {}, {})}`;
    })}` : `<div class="text-center py-8"><div class="text-gray-400 mb-2">${`${validate_component(TrendingUp, "TrendingUp").$$render($$result, { class: "h-8 w-8 mx-auto" }, {}, {})}`}</div> <p class="text-sm text-gray-500 dark:text-gray-400" data-svelte-h="svelte-e0wvqg">暂无数据</p></div>`}`}</div></div></div></div></div> </div>`;
  } while (!$$settled);
  $$unsubscribe_isAuthenticated();
  $$unsubscribe_user();
  return $$rendered;
});
export {
  Page as default
};
