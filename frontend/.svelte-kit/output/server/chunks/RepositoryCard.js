import { c as create_ssr_component, v as validate_component, e as escape, b as add_attribute, a as createEventDispatcher, d as each } from "./ssr.js";
import { I as Icon } from "./Icon.js";
import { formatDistanceToNow } from "date-fns";
import { zhCN } from "date-fns/locale";
import { s as subscribe } from "./utils.js";
import { $ as $format } from "./runtime.esm.js";
import { S as Star, D as Download, E as Eye, C as Calendar } from "./star.js";
/* empty css                                              */const Chevron_right = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [["path", { "d": "m9 18 6-6-6-6" }]];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "chevron-right" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const ChevronRight = Chevron_right;
const Git_fork = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["circle", { "cx": "12", "cy": "18", "r": "3" }],
    ["circle", { "cx": "6", "cy": "6", "r": "3" }],
    ["circle", { "cx": "18", "cy": "6", "r": "3" }],
    [
      "path",
      {
        "d": "M18 9v2c0 .6-.4 1-1 1H7c-.6 0-1-.4-1-1V9"
      }
    ],
    ["path", { "d": "M12 12v3" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "git-fork" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const GitFork = Git_fork;
const Heart = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "heart" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Heart$1 = Heart;
const Lock = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "rect",
      {
        "width": "18",
        "height": "11",
        "x": "3",
        "y": "11",
        "rx": "2",
        "ry": "2"
      }
    ],
    ["path", { "d": "M7 11V7a5 5 0 0 1 10 0v4" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "lock" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Lock$1 = Lock;
const Search = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["circle", { "cx": "11", "cy": "11", "r": "8" }],
    ["path", { "d": "m21 21-4.3-4.3" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "search" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Search$1 = Search;
const Share_2 = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["circle", { "cx": "18", "cy": "5", "r": "3" }],
    ["circle", { "cx": "6", "cy": "12", "r": "3" }],
    ["circle", { "cx": "18", "cy": "19", "r": "3" }],
    [
      "line",
      {
        "x1": "8.59",
        "x2": "15.42",
        "y1": "13.51",
        "y2": "17.49"
      }
    ],
    [
      "line",
      {
        "x1": "15.41",
        "x2": "8.59",
        "y1": "6.51",
        "y2": "10.49"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "share-2" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Share2 = Share_2;
const User_minus = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"
      }
    ],
    ["circle", { "cx": "9", "cy": "7", "r": "4" }],
    [
      "line",
      {
        "x1": "22",
        "x2": "16",
        "y1": "11",
        "y2": "11"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "user-minus" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const UserMinus = User_minus;
const User_plus = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"
      }
    ],
    ["circle", { "cx": "9", "cy": "7", "r": "4" }],
    [
      "line",
      {
        "x1": "19",
        "x2": "19",
        "y1": "8",
        "y2": "14"
      }
    ],
    [
      "line",
      {
        "x1": "22",
        "x2": "16",
        "y1": "11",
        "y2": "11"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "user-plus" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const UserPlus = User_plus;
const User = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"
      }
    ],
    ["circle", { "cx": "12", "cy": "7", "r": "4" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "user" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const User$1 = User;
const UserAvatar = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let sizeClasses;
  let iconSizeClasses;
  let textSizeClasses;
  let userInitials;
  let userColor;
  let { user = null } = $$props;
  let { size = "md" } = $$props;
  let { showName = false } = $$props;
  let { showUsername = false } = $$props;
  let { clickable = true } = $$props;
  const sizeClassMap = {
    xs: "h-6 w-6",
    sm: "h-8 w-8",
    md: "h-10 w-10",
    lg: "h-12 w-12",
    xl: "h-16 w-16"
  };
  const iconSizeClassMap = {
    xs: "h-3 w-3",
    sm: "h-4 w-4",
    md: "h-5 w-5",
    lg: "h-6 w-6",
    xl: "h-8 w-8"
  };
  const textSizeClassMap = {
    xs: "text-xs",
    sm: "text-sm",
    md: "text-base",
    lg: "text-lg",
    xl: "text-xl"
  };
  const colors = [
    "bg-red-500",
    "bg-yellow-500",
    "bg-green-500",
    "bg-blue-500",
    "bg-indigo-500",
    "bg-purple-500",
    "bg-pink-500",
    "bg-orange-500",
    "bg-teal-500",
    "bg-cyan-500"
  ];
  let imageError = false;
  if ($$props.user === void 0 && $$bindings.user && user !== void 0)
    $$bindings.user(user);
  if ($$props.size === void 0 && $$bindings.size && size !== void 0)
    $$bindings.size(size);
  if ($$props.showName === void 0 && $$bindings.showName && showName !== void 0)
    $$bindings.showName(showName);
  if ($$props.showUsername === void 0 && $$bindings.showUsername && showUsername !== void 0)
    $$bindings.showUsername(showUsername);
  if ($$props.clickable === void 0 && $$bindings.clickable && clickable !== void 0)
    $$bindings.clickable(clickable);
  sizeClasses = sizeClassMap[size] || sizeClassMap.md;
  iconSizeClasses = iconSizeClassMap[size] || iconSizeClassMap.md;
  textSizeClasses = textSizeClassMap[size] || textSizeClassMap.md;
  userInitials = user?.full_name ? user.full_name.split(" ").map((word) => word.charAt(0)).join("").toUpperCase().slice(0, 2) : user?.username?.charAt(0).toUpperCase() || "";
  userColor = user?.username ? (() => {
    let hash = 0;
    for (let i = 0; i < user.username.length; i++) {
      hash = user.username.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
  })() : "bg-gray-500";
  return `<div class="flex items-center space-x-2"> <div class="relative">${clickable && user ? `<a href="${"/" + escape(user.username, true)}" class="block"><div class="${"relative " + escape(sizeClasses, true) + " rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700 flex items-center justify-center"}">${user?.avatar_url && !imageError ? ` <div class="h-full w-full relative">${` <div class="${"h-full w-full flex items-center justify-center text-white font-semibold " + escape(userColor, true) + " " + escape(textSizeClasses, true)}">${escape(userInitials)}</div>`} <img${add_attribute("src", user.avatar_url, 0)}${add_attribute("alt", user.full_name || user.username, 0)} class="${"h-full w-full object-cover " + escape("opacity-0", true) + " transition-opacity duration-200"}" loading="lazy"></div>` : `${user ? ` <div class="${"h-full w-full flex items-center justify-center text-white font-semibold " + escape(userColor, true) + " " + escape(textSizeClasses, true)}">${escape(userInitials)}</div>` : ` ${validate_component(User$1, "User").$$render(
    $$result,
    {
      class: "text-gray-500 dark:text-gray-400 " + iconSizeClasses
    },
    {},
    {}
  )}`}`}</div></a>` : `<div class="${"relative " + escape(sizeClasses, true) + " rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700 flex items-center justify-center"}">${user?.avatar_url && !imageError ? ` <div class="h-full w-full relative">${` <div class="${"h-full w-full flex items-center justify-center text-white font-semibold " + escape(userColor, true) + " " + escape(textSizeClasses, true)}">${escape(userInitials)}</div>`} <img${add_attribute("src", user.avatar_url, 0)}${add_attribute("alt", user.full_name || user.username, 0)} class="${"h-full w-full object-cover " + escape("opacity-0", true) + " transition-opacity duration-200"}" loading="lazy"></div>` : `${user ? ` <div class="${"h-full w-full flex items-center justify-center text-white font-semibold " + escape(userColor, true) + " " + escape(textSizeClasses, true)}">${escape(userInitials)}</div>` : ` ${validate_component(User$1, "User").$$render(
    $$result,
    {
      class: "text-gray-500 dark:text-gray-400 " + iconSizeClasses
    },
    {},
    {}
  )}`}`}</div>`}</div>  ${(showName || showUsername) && user ? `<div class="flex flex-col">${showName && user.full_name ? `<span class="${"font-medium text-gray-900 dark:text-white " + escape(textSizeClasses, true)}">${escape(user.full_name)}</span>` : ``} ${showUsername ? `<span class="${"text-gray-500 dark:text-gray-400 " + escape(size === "xs" ? "text-xs" : "text-sm", true)}">@${escape(user.username)}</span>` : ``}</div>` : ``}</div>`;
});
function getSizeClasses(size) {
  switch (size) {
    case "sm":
      return "px-2 py-1 text-xs";
    case "md":
      return "px-3 py-1.5 text-sm";
    case "lg":
      return "px-4 py-2 text-base";
    default:
      return "px-3 py-1.5 text-sm";
  }
}
function getIconSizeClasses(size) {
  switch (size) {
    case "sm":
      return "h-3 w-3";
    case "md":
      return "h-4 w-4";
    case "lg":
      return "h-5 w-5";
    default:
      return "h-4 w-4";
  }
}
function getVariantClasses(variant, type, active) {
  const baseClasses = "inline-flex items-center justify-center space-x-1 rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2";
  if (variant === "ghost") {
    if (active) {
      switch (type) {
        case "star":
          return `${baseClasses} text-yellow-600 dark:text-yellow-400 hover:bg-yellow-50 dark:hover:bg-yellow-900/20`;
        case "follow":
          return `${baseClasses} text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20`;
        case "like":
          return `${baseClasses} text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20`;
        default:
          return `${baseClasses} text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20`;
      }
    } else {
      return `${baseClasses} text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800`;
    }
  }
  if (variant === "outline") {
    if (active) {
      switch (type) {
        case "star":
          return `${baseClasses} border border-yellow-300 dark:border-yellow-600 text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 hover:bg-yellow-100 dark:hover:bg-yellow-900/30`;
        case "follow":
          return `${baseClasses} border border-red-300 dark:border-red-600 text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30`;
        case "like":
          return `${baseClasses} border border-red-300 dark:border-red-600 text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30`;
        default:
          return `${baseClasses} border border-blue-300 dark:border-blue-600 text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/30`;
      }
    } else {
      return `${baseClasses} border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700`;
    }
  }
  if (active) {
    switch (type) {
      case "star":
        return `${baseClasses} bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 hover:bg-yellow-200 dark:hover:bg-yellow-900/40`;
      case "follow":
        return `${baseClasses} bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 hover:bg-red-200 dark:hover:bg-red-900/40`;
      case "like":
        return `${baseClasses} bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 hover:bg-red-200 dark:hover:bg-red-900/40`;
      default:
        return `${baseClasses} bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-900/40`;
    }
  } else {
    switch (type) {
      case "follow":
        return `${baseClasses} bg-blue-600 dark:bg-blue-500 text-white hover:bg-blue-700 dark:hover:bg-blue-600`;
      default:
        return `${baseClasses} bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600`;
    }
  }
}
const SocialButton = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let Icon2;
  let label;
  let buttonClasses;
  let iconClasses;
  let $_, $$unsubscribe__;
  $$unsubscribe__ = subscribe($format, (value) => $_ = value);
  createEventDispatcher();
  let { type = "star" } = $$props;
  let { active = false } = $$props;
  let { count = null } = $$props;
  let { disabled = false } = $$props;
  let { size = "md" } = $$props;
  let { variant = "default" } = $$props;
  let { loading = false } = $$props;
  function getIcon(type2) {
    switch (type2) {
      case "star":
        return Star;
      case "follow":
        return active ? UserMinus : UserPlus;
      case "like":
        return Heart$1;
      case "share":
        return Share2;
      case "fork":
        return GitFork;
      default:
        return Star;
    }
  }
  function getLabel(type2, active2) {
    switch (type2) {
      case "star":
        return active2 ? $_("repository.unstar") : $_("repository.star");
      case "follow":
        return active2 ? $_("user.unfollow") : $_("user.follow");
      case "like":
        return active2 ? $_("social.unlike") : $_("social.like");
      case "share":
        return $_("social.share");
      case "fork":
        return $_("repository.fork");
      default:
        return "";
    }
  }
  if ($$props.type === void 0 && $$bindings.type && type !== void 0)
    $$bindings.type(type);
  if ($$props.active === void 0 && $$bindings.active && active !== void 0)
    $$bindings.active(active);
  if ($$props.count === void 0 && $$bindings.count && count !== void 0)
    $$bindings.count(count);
  if ($$props.disabled === void 0 && $$bindings.disabled && disabled !== void 0)
    $$bindings.disabled(disabled);
  if ($$props.size === void 0 && $$bindings.size && size !== void 0)
    $$bindings.size(size);
  if ($$props.variant === void 0 && $$bindings.variant && variant !== void 0)
    $$bindings.variant(variant);
  if ($$props.loading === void 0 && $$bindings.loading && loading !== void 0)
    $$bindings.loading(loading);
  Icon2 = getIcon(type);
  label = getLabel(type, active);
  buttonClasses = `${getVariantClasses(variant, type, active)} ${getSizeClasses(size)}`;
  iconClasses = getIconSizeClasses(size);
  $$unsubscribe__();
  return `<button class="${[
    escape(buttonClasses, true),
    (disabled || loading ? "opacity-50" : "") + " " + (disabled || loading ? "cursor-not-allowed" : "")
  ].join(" ").trim()}" ${disabled ? "disabled" : ""}${add_attribute("aria-label", label, 0)}>${loading ? `<div class="${"animate-spin rounded-full border-2 border-current border-t-transparent " + escape(iconClasses, true)}"></div>` : `${validate_component(Icon2, "Icon").$$render(
    $$result,
    {
      class: iconClasses,
      fill: active && (type === "star" || type === "like") ? "currentColor" : "none"
    },
    {},
    {}
  )}`} <span>${escape(label)}</span> ${count !== null && count > 0 ? `<span class="ml-1 px-1.5 py-0.5 text-xs bg-black/10 dark:bg-white/10 rounded-full">${escape(count)}</span>` : ``}</button>`;
});
const css = {
  code: ".repository-card.svelte-uvbnuc{background:linear-gradient(to right, var(--color-gray-50), var(--color-white))}.repository-card.svelte-uvbnuc:hover{background:linear-gradient(to right, var(--color-gray-100), var(--color-gray-50));box-shadow:var(--tw-shadow-hover);cursor:pointer}.line-clamp-2.svelte-uvbnuc{display:-webkit-box;-webkit-line-clamp:2;line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.line-clamp-3.svelte-uvbnuc{display:-webkit-box;-webkit-line-clamp:3;line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}",
  map: null
};
function formatFileSize(bytes) {
  if (bytes === 0)
    return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}
const RepositoryCard = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { repo } = $$props;
  let { currentUser = null } = $$props;
  let { showOwner = true } = $$props;
  let { compact = false } = $$props;
  if ($$props.repo === void 0 && $$bindings.repo && repo !== void 0)
    $$bindings.repo(repo);
  if ($$props.currentUser === void 0 && $$bindings.currentUser && currentUser !== void 0)
    $$bindings.currentUser(currentUser);
  if ($$props.showOwner === void 0 && $$bindings.showOwner && showOwner !== void 0)
    $$bindings.showOwner(showOwner);
  if ($$props.compact === void 0 && $$bindings.compact && compact !== void 0)
    $$bindings.compact(compact);
  $$result.css.add(css);
  return `<div class="repository-card rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 transition-all duration-200 svelte-uvbnuc"><div class="flex items-start justify-between"><div class="flex-1 min-w-0"> <div class="flex items-center space-x-3 mb-2">${showOwner && repo.owner ? `${validate_component(UserAvatar, "UserAvatar").$$render($$result, { user: repo.owner, size: "sm" }, {}, {})} <span class="text-sm text-gray-600 dark:text-gray-400">${escape(repo.owner.username)}</span> <span class="text-gray-400 dark:text-gray-600" data-svelte-h="svelte-pb799c">/</span>` : ``} <a href="${"/" + escape(repo.owner?.username || "unknown", true) + "/" + escape(repo.name, true)}" class="text-lg font-semibold text-blue-600 dark:text-blue-400 hover:underline truncate">${escape(repo.name)}</a> ${repo.visibility === "private" ? `${validate_component(Lock$1, "Lock").$$render($$result, { class: "h-4 w-4 text-gray-400" }, {}, {})}` : ``}</div>  ${repo.classification_path && repo.classification_path.length > 0 ? `<div class="flex items-center space-x-1 mb-2">${each(repo.classification_path, (classification, index) => {
    return `<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200">${escape(classification)}</span> ${index < repo.classification_path.length - 1 ? `${validate_component(ChevronRight, "ChevronRight").$$render($$result, { class: "h-3 w-3 text-gray-400" }, {}, {})}` : ``}`;
  })}</div>` : ``}  ${repo.description ? `<p class="${"text-gray-700 dark:text-gray-300 text-sm mb-3 " + escape(compact ? "line-clamp-2" : "line-clamp-3", true) + " svelte-uvbnuc"}">${escape(repo.description)}</p>` : ``}  <div class="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400"><div class="flex items-center space-x-1">${validate_component(Star, "Star").$$render($$result, { class: "h-4 w-4" }, {}, {})} <span>${escape(repo.stars_count)}</span></div> <div class="flex items-center space-x-1">${validate_component(Download, "Download").$$render($$result, { class: "h-4 w-4" }, {}, {})} <span>${escape(repo.downloads_count)}</span></div> <div class="flex items-center space-x-1">${validate_component(Eye, "Eye").$$render($$result, { class: "h-4 w-4" }, {}, {})} <span>${escape(repo.views_count)}</span></div> ${repo.total_size > 0 ? `<div class="flex items-center space-x-1"><span>${escape(formatFileSize(repo.total_size))}</span></div>` : ``}</div></div>  <div class="flex flex-col items-end space-y-2 ml-4">${currentUser && repo.owner?.username !== currentUser.username ? `${validate_component(SocialButton, "SocialButton").$$render(
    $$result,
    {
      type: "star",
      active: repo.is_starred,
      count: repo.stars_count
    },
    {},
    {}
  )}` : ``}  <div class="flex items-center space-x-1 text-xs text-gray-500 dark:text-gray-400">${validate_component(Calendar, "Calendar").$$render($$result, { class: "h-3 w-3" }, {}, {})} <span>更新于 ${escape(formatDistanceToNow(new Date(repo.updated_at), { addSuffix: true, locale: zhCN }))}</span></div></div></div> </div>`;
});
export {
  ChevronRight as C,
  RepositoryCard as R,
  Search$1 as S,
  UserAvatar as U
};
