import { s as subscribe } from "../../../chunks/utils.js";
import { c as create_ssr_component, v as validate_component, a as createEventDispatcher, e as escape, d as each, b as add_attribute } from "../../../chunks/ssr.js";
import { p as page } from "../../../chunks/stores.js";
import { $ as $format } from "../../../chunks/runtime.esm.js";
import { a as api } from "../../../chunks/api.js";
import { C as ChevronRight, S as Search, R as RepositoryCard, U as UserAvatar } from "../../../chunks/RepositoryCard.js";
import { L as Loading } from "../../../chunks/Loading.js";
import { I as Icon } from "../../../chunks/star.js";
import { F as Filter } from "../../../chunks/filter.js";
const Arrow_down_wide_narrow = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["path", { "d": "m3 16 4 4 4-4" }],
    ["path", { "d": "M7 20V4" }],
    ["path", { "d": "M11 4h10" }],
    ["path", { "d": "M11 8h7" }],
    ["path", { "d": "M11 12h4" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "arrow-down-wide-narrow" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const SortDesc = Arrow_down_wide_narrow;
const Arrow_up_narrow_wide = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["path", { "d": "m3 8 4-4 4 4" }],
    ["path", { "d": "M7 4v16" }],
    ["path", { "d": "M11 12h4" }],
    ["path", { "d": "M11 16h7" }],
    ["path", { "d": "M11 20h10" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "arrow-up-narrow-wide" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const SortAsc = Arrow_up_narrow_wide;
const Chevron_left = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [["path", { "d": "m15 18-6-6 6-6" }]];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "chevron-left" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const ChevronLeft = Chevron_left;
const Grid_3x3 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "rect",
      {
        "width": "18",
        "height": "18",
        "x": "3",
        "y": "3",
        "rx": "2"
      }
    ],
    ["path", { "d": "M3 9h18" }],
    ["path", { "d": "M3 15h18" }],
    ["path", { "d": "M9 3v18" }],
    ["path", { "d": "M15 3v18" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "grid-3x3" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Grid = Grid_3x3;
const List = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "line",
      {
        "x1": "8",
        "x2": "21",
        "y1": "6",
        "y2": "6"
      }
    ],
    [
      "line",
      {
        "x1": "8",
        "x2": "21",
        "y1": "12",
        "y2": "12"
      }
    ],
    [
      "line",
      {
        "x1": "8",
        "x2": "21",
        "y1": "18",
        "y2": "18"
      }
    ],
    [
      "line",
      {
        "x1": "3",
        "x2": "3.01",
        "y1": "6",
        "y2": "6"
      }
    ],
    [
      "line",
      {
        "x1": "3",
        "x2": "3.01",
        "y1": "12",
        "y2": "12"
      }
    ],
    [
      "line",
      {
        "x1": "3",
        "x2": "3.01",
        "y1": "18",
        "y2": "18"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "list" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const List$1 = List;
const Pagination = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let startItem;
  let endItem;
  let hasNext;
  let hasPrev;
  let visiblePages;
  let $_, $$unsubscribe__;
  $$unsubscribe__ = subscribe($format, (value) => $_ = value);
  let { currentPage = 1 } = $$props;
  let { totalPages = 1 } = $$props;
  let { total = 0 } = $$props;
  let { pageSize: pageSize2 = 20 } = $$props;
  let { showSummary = true } = $$props;
  createEventDispatcher();
  function getVisiblePages() {
    const delta = 2;
    const range = [];
    const rangeWithDots = [];
    for (let i = Math.max(2, currentPage - delta); i <= Math.min(totalPages - 1, currentPage + delta); i++) {
      range.push(i);
    }
    if (currentPage - delta > 2) {
      rangeWithDots.push(1, "...");
    } else {
      rangeWithDots.push(1);
    }
    rangeWithDots.push(...range);
    if (currentPage + delta < totalPages - 1) {
      rangeWithDots.push("...", totalPages);
    } else {
      rangeWithDots.push(totalPages);
    }
    return rangeWithDots;
  }
  if ($$props.currentPage === void 0 && $$bindings.currentPage && currentPage !== void 0)
    $$bindings.currentPage(currentPage);
  if ($$props.totalPages === void 0 && $$bindings.totalPages && totalPages !== void 0)
    $$bindings.totalPages(totalPages);
  if ($$props.total === void 0 && $$bindings.total && total !== void 0)
    $$bindings.total(total);
  if ($$props.pageSize === void 0 && $$bindings.pageSize && pageSize2 !== void 0)
    $$bindings.pageSize(pageSize2);
  if ($$props.showSummary === void 0 && $$bindings.showSummary && showSummary !== void 0)
    $$bindings.showSummary(showSummary);
  startItem = (currentPage - 1) * pageSize2 + 1;
  endItem = Math.min(currentPage * pageSize2, total);
  hasNext = currentPage < totalPages;
  hasPrev = currentPage > 1;
  visiblePages = getVisiblePages();
  $$unsubscribe__();
  return `${totalPages > 1 ? `<div class="flex flex-col sm:flex-row items-center justify-between space-y-4 sm:space-y-0"> ${showSummary ? `<div class="text-sm text-secondary-600 dark:text-dark-500">${escape($_("pagination.showing", {
    values: { from: startItem, to: endItem, total }
  }))}</div>` : ``}  <div class="flex items-center space-x-1"> <button class="flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-md border border-secondary-300 dark:border-secondary-600 bg-white dark:bg-dark-50 text-secondary-700 dark:text-dark-600 hover:bg-secondary-50 dark:hover:bg-secondary-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors" ${!hasPrev ? "disabled" : ""}>${validate_component(ChevronLeft, "ChevronLeft").$$render($$result, { class: "w-4 h-4" }, {}, {})} <span class="hidden sm:inline">${escape($_("pagination.previous"))}</span></button>  <div class="flex items-center space-x-1">${each(visiblePages, (page2) => {
    return `${page2 === "..." ? `<span class="px-3 py-2 text-sm text-secondary-500 dark:text-dark-400" data-svelte-h="svelte-lstmma">...
            </span>` : `<button class="${"px-3 py-2 text-sm font-medium rounded-md transition-colors " + escape(
      page2 === currentPage ? "bg-primary-600 text-white" : "bg-white dark:bg-dark-50 text-secondary-700 dark:text-dark-600 hover:bg-secondary-50 dark:hover:bg-secondary-800 border border-secondary-300 dark:border-secondary-600",
      true
    )}">${escape(page2)} </button>`}`;
  })}</div>  <button class="flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-md border border-secondary-300 dark:border-secondary-600 bg-white dark:bg-dark-50 text-secondary-700 dark:text-dark-600 hover:bg-secondary-50 dark:hover:bg-secondary-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors" ${!hasNext ? "disabled" : ""}><span class="hidden sm:inline">${escape($_("pagination.next"))}</span> ${validate_component(ChevronRight, "ChevronRight").$$render($$result, { class: "w-4 h-4" }, {}, {})}</button></div></div>` : ``}`;
});
let pageSize = 20;
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $_, $$unsubscribe__;
  let $page, $$unsubscribe_page;
  $$unsubscribe__ = subscribe($format, (value) => $_ = value);
  $$unsubscribe_page = subscribe(page, (value) => $page = value);
  let searchQuery = "";
  let searchType = "repositories";
  let repositories = [];
  let users = [];
  let loading = false;
  let error = "";
  let totalResults = 0;
  let currentPage = 1;
  let filters = {
    repo_type: "",
    // model, dataset, space
    classification_id: null,
    tags: "",
    verified_only: false,
    sort_by: "relevance",
    order: "desc"
  };
  async function performSearch() {
    if (!searchQuery.trim())
      return;
    loading = true;
    error = "";
    try {
      if (searchType === "repositories" || searchType === "all") {
        const repoResponse = await api.search.repositories(searchQuery, {
          repo_type: filters.repo_type || void 0,
          classification_id: filters.classification_id || void 0,
          tags: filters.tags || void 0,
          sort_by: filters.sort_by,
          order: filters.order,
          skip: (currentPage - 1) * pageSize,
          limit: pageSize
        });
        repositories = repoResponse.data || repoResponse;
        totalResults = repoResponse.total || repositories.length;
      }
      if (searchType === "users" || searchType === "all") {
        const userResponse = await api.search.users(searchQuery, {
          verified_only: filters.verified_only,
          sort_by: filters.sort_by === "relevance" ? "relevance" : "created",
          order: filters.order,
          skip: (currentPage - 1) * pageSize,
          limit: pageSize
        });
        users = userResponse.data || userResponse;
      }
    } catch (err) {
      console.error("Search failed:", err);
      error = $_("error.network_error");
    } finally {
      loading = false;
    }
  }
  const repoTypes = [
    { value: "", label: "search.all_types" },
    {
      value: "model",
      label: "repository.model"
    },
    {
      value: "dataset",
      label: "repository.dataset"
    },
    {
      value: "space",
      label: "repository.space"
    }
  ];
  const sortOptions = [
    {
      value: "relevance",
      label: "search.relevance"
    },
    {
      value: "updated",
      label: "search.updated"
    },
    {
      value: "created",
      label: "search.created"
    },
    { value: "stars", label: "search.stars" },
    {
      value: "downloads",
      label: "search.downloads"
    }
  ];
  {
    if ($page.url.searchParams.get("q")) {
      searchQuery = $page.url.searchParams.get("q") || "";
      searchType = $page.url.searchParams.get("type") || "repositories";
      filters.repo_type = $page.url.searchParams.get("repo_type") || "";
      filters.sort_by = $page.url.searchParams.get("sort") || "relevance";
      filters.order = $page.url.searchParams.get("order") || "desc";
      if (searchQuery) {
        performSearch();
      }
    }
  }
  $$unsubscribe__();
  $$unsubscribe_page();
  return `${$$result.head += `<!-- HEAD_svelte-ps9ygr_START -->${$$result.title = `<title>${escape($_("search.search"))} - GeoML-Hub</title>`, ""}<meta name="description"${add_attribute("content", $_("search.search_description"), 0)}><!-- HEAD_svelte-ps9ygr_END -->`, ""} <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"> <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6 mb-6"><form class="space-y-4"> <div class="flex space-x-4"><div class="flex-1"><label for="search" class="sr-only">${escape($_("search.search"))}</label> <div class="relative"><div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">${validate_component(Search, "Search").$$render($$result, { class: "h-5 w-5 text-gray-400" }, {}, {})}</div> <input id="search" type="text"${add_attribute("placeholder", $_("search.search_placeholder"), 0)} class="input pl-10 w-full"${add_attribute("value", searchQuery, 0)}></div></div> <button type="submit" class="btn btn-primary">${escape($_("search.search"))}</button></div>  <div class="flex space-x-4"><div class="flex space-x-2">${each(["repositories", "users", "all"], (type) => {
    return `<label class="flex items-center"><input type="radio"${add_attribute("value", type, 0)} class="form-radio h-4 w-4 text-primary-600"${type === searchType ? add_attribute("checked", true, 1) : ""}> <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">${escape($_(`search.${type}`))}</span> </label>`;
  })}</div></div></form></div>  <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-4 mb-6"><div class="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0"> <div class="flex flex-wrap items-center space-x-4">${searchType === "repositories" || searchType === "all" ? ` <div class="flex items-center space-x-2">${validate_component(Filter, "Filter").$$render($$result, { class: "h-4 w-4 text-gray-400" }, {}, {})} <select class="input-sm">${each(repoTypes, (type) => {
    return `<option${add_attribute("value", type.value, 0)}>${escape($_(type.label))}</option>`;
  })}</select></div>` : ``} ${searchType === "users" || searchType === "all" ? ` <label class="flex items-center"><input type="checkbox" class="form-checkbox h-4 w-4 text-primary-600"${add_attribute("checked", filters.verified_only, 1)}> <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">${escape($_("user.verified_only"))}</span></label>` : ``}  <div class="flex items-center space-x-2"><select class="input-sm">${each(sortOptions, (option) => {
    return `<option${add_attribute("value", option.value, 0)}>${escape($_(option.label))}</option>`;
  })}</select> <button class="btn btn-sm btn-secondary">${filters.order === "desc" ? `${validate_component(SortDesc, "SortDesc").$$render($$result, { class: "h-4 w-4" }, {}, {})}` : `${validate_component(SortAsc, "SortAsc").$$render($$result, { class: "h-4 w-4" }, {}, {})}`}</button></div></div>  <div class="flex items-center space-x-2"><button class="${"p-2 rounded " + escape(
    "bg-primary-100 text-primary-600",
    true
  )}">${validate_component(Grid, "Grid").$$render($$result, { class: "h-4 w-4" }, {}, {})}</button> <button class="${"p-2 rounded " + escape(
    "text-gray-400 hover:text-gray-600",
    true
  )}">${validate_component(List$1, "List").$$render($$result, { class: "h-4 w-4" }, {}, {})}</button></div></div></div>  ${loading ? `<div class="flex justify-center py-12">${validate_component(Loading, "Loading").$$render($$result, {}, {}, {})}</div>` : `${error ? `<div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6"><p class="text-red-800 dark:text-red-200">${escape(error)}</p></div>` : `${searchQuery ? ` <div class="mb-6"><p class="text-sm text-gray-600 dark:text-gray-400">${searchType === "repositories" || searchType === "all" ? `${escape($_("search.found"))} ${escape(totalResults)} ${escape($_("search.repositories"))}` : ``} ${searchType === "users" || searchType === "all" ? `${escape(users.length)} ${escape($_("search.users"))}` : ``} ${searchQuery ? `${escape($_("search.for"))} &quot;${escape(searchQuery)}&quot;` : ``}</p></div>  ${(searchType === "repositories" || searchType === "all") && repositories.length > 0 ? `<div class="mb-8"><h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">${escape($_("search.repositories"))}</h2> ${`<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">${each(repositories, (repository) => {
    return `${validate_component(RepositoryCard, "RepositoryCard").$$render($$result, { repository }, {}, {})}`;
  })}</div>`}</div>` : ``}  ${(searchType === "users" || searchType === "all") && users.length > 0 ? `<div class="mb-8"><h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">${escape($_("search.users"))}</h2> <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">${each(users, (user) => {
    return `<a href="${"/" + escape(user.username, true)}" class="block"><div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow"><div class="flex items-center space-x-4">${validate_component(UserAvatar, "UserAvatar").$$render($$result, { user, size: "lg" }, {}, {})} <div class="flex-1 min-w-0"><h3 class="text-lg font-semibold text-gray-900 dark:text-white truncate">${escape(user.username)}</h3> ${user.full_name ? `<p class="text-sm text-gray-600 dark:text-gray-400 truncate">${escape(user.full_name)} </p>` : ``} ${user.bio ? `<p class="text-sm text-gray-500 dark:text-gray-400 mt-2 line-clamp-2">${escape(user.bio)} </p>` : ``} <div class="flex items-center space-x-4 mt-2 text-xs text-gray-500 dark:text-gray-400"><span>${escape(user.repositories_count || 0)} ${escape($_("user.repositories"))}</span> <span>${escape(user.followers_count || 0)} ${escape($_("user.followers"))}</span> </div></div> </div></div> </a>`;
  })}</div></div>` : ``}  ${repositories.length === 0 && users.length === 0 ? `<div class="text-center py-12">${validate_component(Search, "Search").$$render(
    $$result,
    {
      class: "h-12 w-12 text-gray-300 mx-auto mb-4"
    },
    {},
    {}
  )} <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">${escape($_("search.no_results"))}</h3> <p class="text-gray-500 dark:text-gray-400">${escape($_("search.try_different_keywords"))}</p></div>` : ``}  ${totalResults > pageSize ? `<div class="mt-8">${validate_component(Pagination, "Pagination").$$render(
    $$result,
    {
      current: currentPage,
      total: Math.ceil(totalResults / pageSize)
    },
    {},
    {}
  )}</div>` : ``}` : ` <div class="text-center py-12">${validate_component(Search, "Search").$$render(
    $$result,
    {
      class: "h-16 w-16 text-gray-300 mx-auto mb-4"
    },
    {},
    {}
  )} <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">${escape($_("search.search_models_datasets"))}</h2> <p class="text-gray-500 dark:text-gray-400">${escape($_("search.search_hint"))}</p></div>`}`}`}</div>`;
});
export {
  Page as default
};
