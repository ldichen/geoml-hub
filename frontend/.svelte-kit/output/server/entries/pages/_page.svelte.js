import { s as subscribe } from "../../chunks/utils.js";
import { c as create_ssr_component, a as createEventDispatcher, v as validate_component, b as add_attribute, d as each, e as escape } from "../../chunks/ssr.js";
import { S as Search, R as RepositoryCard } from "../../chunks/RepositoryCard.js";
import { $ as $format } from "../../chunks/runtime.esm.js";
import { X } from "../../chunks/x.js";
import { L as Loading } from "../../chunks/Loading.js";
import { i as isAuthenticated, u as user } from "../../chunks/auth.js";
import { T as TrendingUp } from "../../chunks/trending-up.js";
import { S as Star } from "../../chunks/star.js";
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
  return `<div class="relative"><div class="relative"><div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">${validate_component(Search, "Search").$$render($$result, { class: "h-5 w-5 text-gray-400" }, {}, {})}</div> <input type="text" class="block w-full pl-10 pr-20 py-3 text-gray-900 dark:text-white bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"${add_attribute("placeholder", placeholder || $_("search.placeholder"), 0)}${add_attribute("value", value, 0)}> ${value ? `<div class="absolute inset-y-0 right-16 pr-3 flex items-center"><button type="button" class="p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">${validate_component(X, "X").$$render($$result, { class: "h-4 w-4 text-gray-400" }, {}, {})}</button></div>` : ``}</div> <div class="absolute right-2 top-1/2 transform -translate-y-1/2"><button type="button" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2" data-svelte-h="svelte-1m21zv5">Search</button></div></div>`;
});
const _page_svelte_svelte_type_style_lang = "";
const css = {
  code: ".bg-gradient-to-r.svelte-ypm7ls{background:linear-gradient(to right, var(--tw-gradient-stops))}.line-clamp-2.svelte-ypm7ls{overflow:hidden;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2}",
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
  let $user, $$unsubscribe_user;
  $$unsubscribe_isAuthenticated = subscribe(isAuthenticated, (value) => value);
  $$unsubscribe_user = subscribe(user, (value) => $user = value);
  let currentUser = null;
  let featuredRepositories = [];
  let classifications = [];
  let searchQuery = "";
  let selectedClassifications = /* @__PURE__ */ new Set();
  let trendingRepositories = [];
  $$result.css.add(css);
  let $$settled;
  let $$rendered;
  let previous_head = $$result.head;
  do {
    $$settled = true;
    $$result.head = previous_head;
    currentUser = $user;
    allClassifications = getAllClassifications(classifications);
    level1Classifications = classifications.filter((c) => c.level === 1);
    level2Classifications = allClassifications.filter((c) => c.level === 2);
    level3Classifications = allClassifications.filter((c) => c.level === 3);
    $$rendered = `${$$result.head += `<!-- HEAD_svelte-1yua285_START -->${$$result.title = `<title>GeoML Hub - 地理科学机器学习模型库</title>`, ""}<meta name="description" content="为地理科学设计的机器学习模型库，发现、分享和部署地理空间AI模型"><!-- HEAD_svelte-1yua285_END -->`, ""} <div class="min-h-screen dark:bg-gray-900"> <div class="bg-gradient-to-r from-blue-600 to-indigo-700 dark:from-blue-800 dark:to-indigo-900 svelte-ypm7ls"><div class="container py-10"><div class="text-center"><h1 class="text-4xl sm:text-5xl font-bold text-white mb-4" data-svelte-h="svelte-d38mhq">🌍 GeoML Hub</h1> <p class="text-xl text-blue-100 mb-8 max-w-3xl mx-auto" data-svelte-h="svelte-1gh81ez">地理科学设计的机器学习模型库 - 发现、分享和部署地理空间AI模型</p>  <div class="max-w-2xl mx-auto mb-4">${validate_component(SearchBar, "SearchBar").$$render(
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
    )}</div></div></div></div> <div class="container bg-white"> ${featuredRepositories.length > 0 ? `<div class="mb-12 pt-8"><div class="flex items-center justify-between mb-6"><h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center">${validate_component(TrendingUp, "TrendingUp").$$render($$result, { class: "h-6 w-6 mr-2" }, {}, {})}
            精选仓库</h2></div> <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">${each(featuredRepositories, (repo) => {
      return `${validate_component(RepositoryCard, "RepositoryCard").$$render($$result, { repo, currentUser, compact: true }, {}, {})}`;
    })}</div></div>` : ``}  <div class="flex flex-col lg:flex-row gap-6"> <div class="lg:w-[25%] border-gray-100 lg:border-r pt-8 flex-shrink-0 min-h-screen sidebar-gradient-left"><div class="p-2"> <div class="border-b border-gray-200 dark:border-gray-700 mb-6"><nav class="flex space-x-6" aria-label="Tabs"><button class="${"py-2 px-1 border-b-2 font-medium text-sm " + escape(
      "border-blue-500 text-blue-600 dark:text-blue-400",
      true
    )}">Main</button> <button class="${"py-2 px-1 border-b-2 font-medium text-sm " + escape(
      "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300",
      true
    )}">Class</button> <button class="${"py-2 px-1 border-b-2 font-medium text-sm " + escape(
      "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300",
      true
    )}">Tags</button> <button class="${"py-2 px-1 border-b-2 font-medium text-sm " + escape(
      "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300",
      true
    )}">Licenses</button></nav></div>  ${` <div class="space-y-6"> ${level1Classifications.length > 0 ? `<div><div class="flex items-center justify-between mb-3"><h4 class="text-sm font-medium text-gray-700 dark:text-gray-300" data-svelte-h="svelte-12lo0le">一级分类</h4> ${level1Classifications.some((c) => selectedClassifications.has(c.id)) ? `<button class="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors" data-svelte-h="svelte-1ja9559"><svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                        Reset</button>` : ``}</div> <div class="flex flex-wrap gap-2">${each(
      level1Classifications.slice(0, 10),
      (classification) => {
        return `<button class="${"inline-flex items-center px-3 py-1 rounded-md text-sm font-medium transition-colors border " + escape(
          selectedClassifications.has(classification.id) ? "bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-700" : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700",
          true
        )}">${escape(classification.name)} </button>`;
      }
    )} ${level1Classifications.length > 10 ? `<button class="inline-flex items-center px-3 py-1 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors">${escape(`+ ${level1Classifications.length - 10}`)}</button>` : ``}</div></div>` : ``}  ${level2Classifications.length > 0 ? `<div><div class="flex items-center justify-between mb-3"><h4 class="text-sm font-medium text-gray-700 dark:text-gray-300" data-svelte-h="svelte-uvkxuu">二级分类</h4> ${level2Classifications.some((c) => selectedClassifications.has(c.id)) ? `<button class="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors" data-svelte-h="svelte-16zt2su"><svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                        Reset</button>` : ``}</div> <div class="flex flex-wrap gap-2">${each(
      level2Classifications.slice(0, 10),
      (classification) => {
        return `<button class="${"inline-flex items-center px-3 py-1 rounded-md text-sm font-medium transition-colors border " + escape(
          selectedClassifications.has(classification.id) ? "bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-700" : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700",
          true
        )}">${escape(classification.name)} </button>`;
      }
    )} ${level2Classifications.length > 10 ? `<button class="inline-flex items-center px-3 py-1 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors">${escape(`+ ${level2Classifications.length - 10}`)}</button>` : ``}</div></div>` : ``}  ${level3Classifications.length > 0 ? `<div><div class="flex items-center justify-between mb-3"><h4 class="text-sm font-medium text-gray-700 dark:text-gray-300" data-svelte-h="svelte-1gtc6at">三级分类</h4> ${level3Classifications.some((c) => selectedClassifications.has(c.id)) ? `<button class="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors" data-svelte-h="svelte-nkw91f"><svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                        Reset</button>` : ``}</div> <div class="flex flex-wrap gap-2">${each(
      level3Classifications.slice(0, 10),
      (classification) => {
        return `<button class="${"inline-flex items-center px-3 py-1 rounded-md text-sm font-medium transition-colors border " + escape(
          selectedClassifications.has(classification.id) ? "bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-700" : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700",
          true
        )}">${escape(classification.name)} </button>`;
      }
    )} ${level3Classifications.length > 10 ? `<button class="inline-flex items-center px-3 py-1 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors">${escape(`+ ${level3Classifications.length - 10}`)}</button>` : ``}</div></div>` : ``}</div>`}</div></div>  <div class="lg:w-[50%] pt-8 flex-1 repository-list">${`<div class="flex items-center justify-center py-12">${validate_component(Loading, "Loading").$$render($$result, { size: "lg" }, {}, {})}</div>`}</div>  <div class="lg:w-[25%] border-gray-100 lg:border-l pt-8 flex-shrink-0 min-h-screen sidebar-gradient-right"><div class="p-2"> <div class="mb-6"><div class="flex items-center"><div class="flex items-center space-x-2">${validate_component(TrendingUp, "TrendingUp").$$render(
      $$result,
      {
        class: "h-5 w-5 text-gray-500 dark:text-gray-400"
      },
      {},
      {}
    )} <h3 class="text-xl font-semibold text-gray-900 dark:text-white" data-svelte-h="svelte-k51wpr">Trending</h3></div> <span class="text-xs font-semibold text-gray-600 dark:text-gray-400 dark:bg-gray-700 px-2 py-1 ml-4" data-svelte-h="svelte-1bbv6mc">last 7 days</span></div></div>  <div class="border-b border-gray-200 dark:border-gray-700 mb-6"><nav class="flex space-x-6" aria-label="Trending Tabs"><button class="${"py-2 px-1 border-b-2 font-medium text-sm " + escape(
      "border-blue-500 text-blue-600 dark:text-blue-400",
      true
    )}">精选</button> <button class="${"py-2 px-1 border-b-2 font-medium text-sm " + escape(
      "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300",
      true
    )}">热门</button> <button class="${"py-2 px-1 border-b-2 font-medium text-sm " + escape(
      "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300",
      true
    )}">最新</button> <button class="${"py-2 px-1 border-b-2 font-medium text-sm " + escape(
      "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300",
      true
    )}">推荐</button></nav></div>  <div class="space-y-3">${`${trendingRepositories.length > 0 ? `${each(trendingRepositories, (repo, index) => {
      return `<div class="group"><a href="${"/" + escape(repo.owner?.username, true) + "/" + escape(repo.name, true)}" class="block p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"><div class="flex items-start space-x-3"> <div class="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center"><span class="text-xs font-medium text-blue-600 dark:text-blue-300">${escape(repo.name.charAt(0).toUpperCase())} </span></div>  <div class="flex-1 min-w-0"><div class="flex items-center space-x-1 mb-1"><span class="text-xs font-medium text-gray-500 dark:text-gray-400">#${escape(index + 1)}</span> <span class="text-sm font-medium text-gray-900 dark:text-white truncate">${escape(repo.owner?.username)}/${escape(repo.name)} </span></div> ${repo.description ? `<p class="text-xs text-gray-600 dark:text-gray-400 line-clamp-2 mb-2 svelte-ypm7ls">${escape(repo.description)} </p>` : ``}  <div class="flex items-center space-x-3 text-xs text-gray-500 dark:text-gray-400">${`<div class="flex items-center space-x-1">${validate_component(Star, "Star").$$render($$result, { class: "h-3 w-3" }, {}, {})} <span>${escape(repo.stars_count || 0)}</span> </div>`} ${``} ${``} <span data-svelte-h="svelte-7hh8jk">•</span> <span data-svelte-h="svelte-1s0h32k">about 16 hours ago</span> </div></div> </div></a> </div>`;
    })}` : `<div class="text-center py-8"><div class="text-gray-400 mb-2">${`${validate_component(TrendingUp, "TrendingUp").$$render($$result, { class: "h-8 w-8 mx-auto" }, {}, {})}`}</div> <p class="text-sm text-gray-500 dark:text-gray-400" data-svelte-h="svelte-e0wvqg">暂无数据</p></div>`}`}</div></div></div></div></div> </div>`;
  } while (!$$settled);
  $$unsubscribe_isAuthenticated();
  $$unsubscribe_user();
  return $$rendered;
});
export {
  Page as default
};
