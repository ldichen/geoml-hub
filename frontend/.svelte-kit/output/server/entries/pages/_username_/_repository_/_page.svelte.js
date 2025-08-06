import { s as subscribe } from "../../../../chunks/utils.js";
import { c as create_ssr_component, v as validate_component, a as createEventDispatcher, b as add_attribute, e as escape, d as each } from "../../../../chunks/ssr.js";
import { p as page } from "../../../../chunks/stores.js";
import "marked";
import "../../../../chunks/runtime.esm.js";
import { u as user } from "../../../../chunks/auth.js";
import { i as isOwner } from "../../../../chunks/auth2.js";
import { L as Loading } from "../../../../chunks/Loading.js";
import { I as Icon } from "../../../../chunks/Icon.js";
import { X } from "../../../../chunks/x.js";
const Alert_circle = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["circle", { "cx": "12", "cy": "12", "r": "10" }],
    [
      "line",
      {
        "x1": "12",
        "x2": "12",
        "y1": "8",
        "y2": "12"
      }
    ],
    [
      "line",
      {
        "x1": "12",
        "x2": "12.01",
        "y1": "16",
        "y2": "16"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "alert-circle" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const AlertCircle = Alert_circle;
const Cpu = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "rect",
      {
        "x": "4",
        "y": "4",
        "width": "16",
        "height": "16",
        "rx": "2"
      }
    ],
    [
      "rect",
      {
        "x": "9",
        "y": "9",
        "width": "6",
        "height": "6"
      }
    ],
    ["path", { "d": "M15 2v2" }],
    ["path", { "d": "M15 20v2" }],
    ["path", { "d": "M2 15h2" }],
    ["path", { "d": "M2 9h2" }],
    ["path", { "d": "M20 15h2" }],
    ["path", { "d": "M20 9h2" }],
    ["path", { "d": "M9 2v2" }],
    ["path", { "d": "M9 20v2" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "cpu" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Cpu$1 = Cpu;
const Hard_drive = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "line",
      {
        "x1": "22",
        "x2": "2",
        "y1": "12",
        "y2": "12"
      }
    ],
    [
      "path",
      {
        "d": "M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"
      }
    ],
    [
      "line",
      {
        "x1": "6",
        "x2": "6.01",
        "y1": "16",
        "y2": "16"
      }
    ],
    [
      "line",
      {
        "x1": "10",
        "x2": "10.01",
        "y1": "16",
        "y2": "16"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "hard-drive" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const HardDrive = Hard_drive;
const Info = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["circle", { "cx": "12", "cy": "12", "r": "10" }],
    ["path", { "d": "M12 16v-4" }],
    ["path", { "d": "M12 8h.01" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "info" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Info$1 = Info;
const Settings = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"
      }
    ],
    ["circle", { "cx": "12", "cy": "12", "r": "3" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "settings" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Settings$1 = Settings;
const Shield = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "shield" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Shield$1 = Shield;
const Zap = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "polygon",
      {
        "points": "13 2 3 14 12 14 11 22 21 10 12 10 13 2"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "zap" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Zap$1 = Zap;
const ServiceCreateModal_svelte_svelte_type_style_lang = "";
const css$1 = {
  code: '@keyframes svelte-1ny6h8j-slideIn{from{opacity:0;transform:translateY(-10px) scale(0.95)}to{opacity:1;transform:translateY(0) scale(1)}}@keyframes svelte-1ny6h8j-fadeIn{from{opacity:0}to{opacity:1}}.fixed.inset-0.svelte-1ny6h8j.svelte-1ny6h8j{animation:svelte-1ny6h8j-fadeIn 0.2s ease-out}.fixed.inset-0.svelte-1ny6h8j>div.svelte-1ny6h8j{animation:svelte-1ny6h8j-slideIn 0.3s ease-out}input[type="radio"].svelte-1ny6h8j:checked+div.svelte-1ny6h8j{box-shadow:0 0 0 2px rgba(59, 130, 246, 0.5)}input[type="checkbox"].svelte-1ny6h8j.svelte-1ny6h8j:indeterminate{background-color:#3b82f6;border-color:#3b82f6}.overflow-y-auto.svelte-1ny6h8j.svelte-1ny6h8j::-webkit-scrollbar{width:6px}.overflow-y-auto.svelte-1ny6h8j.svelte-1ny6h8j::-webkit-scrollbar-track{background:transparent}.overflow-y-auto.svelte-1ny6h8j.svelte-1ny6h8j::-webkit-scrollbar-thumb{background:rgba(156, 163, 175, 0.5);border-radius:3px}.overflow-y-auto.svelte-1ny6h8j.svelte-1ny6h8j::-webkit-scrollbar-thumb:hover{background:rgba(156, 163, 175, 0.7)}',
  map: null
};
const ServiceCreateModal = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { isOpen = false } = $$props;
  let { loading = false } = $$props;
  let { availableImages = [] } = $$props;
  createEventDispatcher();
  let formElement;
  const resourceConfigs = {
    "lightweight": {
      cpu: "0.1",
      memory: "128Mi",
      label: "轻量配置",
      icon: "eco",
      color: "green"
    },
    "recommended": {
      cpu: "0.3",
      memory: "256Mi",
      label: "推荐配置",
      icon: "zap",
      color: "blue"
    },
    "performance": {
      cpu: "0.5",
      memory: "512Mi",
      label: "性能配置",
      icon: "rocket",
      color: "purple"
    }
  };
  const priorityOptions = [
    { value: 1, label: "1 (最高)" },
    { value: 2, label: "2 (默认)" },
    { value: 3, label: "3 (最低)" }
  ];
  let formData = {
    description: "",
    resource_config: "recommended",
    // 资源配置预设选择
    cpu_limit: "0.3",
    memory_limit: "256Mi",
    is_public: false,
    priority: 2,
    selected_image_id: null
    // 当选择已有镜像时使用
  };
  let errors = {};
  if ($$props.isOpen === void 0 && $$bindings.isOpen && isOpen !== void 0)
    $$bindings.isOpen(isOpen);
  if ($$props.loading === void 0 && $$bindings.loading && loading !== void 0)
    $$bindings.loading(loading);
  if ($$props.availableImages === void 0 && $$bindings.availableImages && availableImages !== void 0)
    $$bindings.availableImages(availableImages);
  $$result.css.add(css$1);
  return ` ${isOpen ? ` <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm svelte-1ny6h8j"> <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-3xl w-full mx-4 max-h-[100vh] overflow-hidden border border-gray-200 dark:border-gray-700 svelte-1ny6h8j"> <div class="relative bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-700 px-6 py-5 border-b border-gray-200 dark:border-gray-600"><div class="flex items-center space-x-3"><div class="flex items-center justify-center w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-xl">${validate_component(Settings$1, "Settings").$$render(
    $$result,
    {
      class: "w-5 h-5 text-blue-600 dark:text-blue-400"
    },
    {},
    {}
  )}</div> <div data-svelte-h="svelte-41nbwf"><h3 class="text-xl font-bold text-gray-900 dark:text-white">创建模型服务</h3> <p class="text-sm text-gray-600 dark:text-gray-300 mt-1">配置并部署您的机器学习模型服务</p></div></div> <button class="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-all duration-200" ${loading ? "disabled" : ""}>${validate_component(X, "X").$$render($$result, { class: "w-5 h-5" }, {}, {})}</button></div>  <form${add_attribute("this", formElement, 0)}><div class="overflow-y-auto max-h-[calc(90vh-120px)] svelte-1ny6h8j"><div class="p-4 space-y-6"> <div class="bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-gray-800 dark:to-gray-700 rounded-xl p-6 border border-indigo-200 dark:border-gray-600"><h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4" data-svelte-h="svelte-62gyqe">选择创建方式</h4> <div class="grid grid-cols-1 md:grid-cols-2 gap-4"> <label class="relative"><input type="radio" name="creationMode" value="docker-upload" class="sr-only svelte-1ny6h8j" ${loading ? "disabled" : ""}${add_attribute("checked", true, 1)}> <div class="${"flex flex-col p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 hover:shadow-md " + escape(
    "border-blue-500 bg-blue-50 dark:bg-blue-900/20",
    true
  ) + " svelte-1ny6h8j"}"><div class="flex items-center justify-between mb-2" data-svelte-h="svelte-lu6wuq"><span class="font-medium text-sm text-gray-900 dark:text-white">上传Docker镜像</span> <span class="text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 px-2 py-1 rounded-full">传统方式</span></div> <p class="text-xs text-gray-600 dark:text-gray-400" data-svelte-h="svelte-16ef5i2">直接上传Docker tar包创建服务</p></div></label>  <label class="relative"><input type="radio" name="creationMode" value="existing-image" class="sr-only svelte-1ny6h8j" ${loading || availableImages.length === 0 ? "disabled" : ""}${""}> <div class="${"flex flex-col p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 hover:shadow-md " + escape(
    "border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500",
    true
  ) + " " + escape(
    availableImages.length === 0 ? "opacity-50 cursor-not-allowed" : "",
    true
  ) + " svelte-1ny6h8j"}"><div class="flex items-center justify-between mb-2" data-svelte-h="svelte-1cbbv9x"><span class="font-medium text-sm text-gray-900 dark:text-white">使用已有镜像</span> <span class="text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 px-2 py-1 rounded-full">推荐</span></div> <p class="text-xs text-gray-600 dark:text-gray-400">${escape(availableImages.length > 0 ? `从 ${availableImages.length} 个可用镜像中选择` : "暂无可用镜像")}</p></div></label></div></div>  ${`<div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-xl p-6"><div class="flex items-start space-x-3"><div class="flex-shrink-0">${validate_component(Info$1, "Info").$$render(
    $$result,
    {
      class: "w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5"
    },
    {},
    {}
  )}</div> <div class="flex-1" data-svelte-h="svelte-pxmi1m"><h4 class="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2">Docker镜像要求</h4> <div class="text-sm text-blue-800 dark:text-blue-200 space-y-2"><p>您的Docker镜像必须包含以下文件结构（位于镜像的根目录）：</p> <ul class="list-disc list-inside ml-2 space-y-1"><li><code class="bg-blue-100 dark:bg-blue-800 px-1.5 py-0.5 rounded text-xs font-mono">gogogo.py</code> - 模型服务的启动文件</li> <li><code class="bg-blue-100 dark:bg-blue-800 px-1.5 py-0.5 rounded text-xs font-mono">mc.json</code> - 配置文件</li> <li><code class="bg-blue-100 dark:bg-blue-800 px-1.5 py-0.5 rounded text-xs font-mono">model/</code> - 模型文件夹</li></ul> <p class="mt-2">可选文件：</p> <ul class="list-disc list-inside ml-2"><li><code class="bg-blue-100 dark:bg-blue-800 px-1.5 py-0.5 rounded text-xs font-mono">examples/</code> - 用于展示的样例数据文件夹（可后续上传）</li></ul> <p class="mt-2 text-xs"><strong>注意</strong>：上传的容器应是完全可运行的，不允许存在依赖缺失或环境配置错误。</p></div></div></div></div>`}  ${``}  <div class="bg-gray-50 dark:bg-gray-800/50 rounded-xl p-6 border border-gray-200 dark:border-gray-700"><div class="flex items-center space-x-2 mb-4"><div class="flex items-center justify-center w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-lg">${validate_component(Info$1, "Info").$$render(
    $$result,
    {
      class: "w-4 h-4 text-blue-600 dark:text-blue-400"
    },
    {},
    {}
  )}</div> <h4 class="text-lg font-semibold text-gray-900 dark:text-white" data-svelte-h="svelte-1qjd48v">基本信息</h4></div>  ${`<div class="space-y-3"><label class="block text-sm font-medium text-gray-700 dark:text-gray-300" data-svelte-h="svelte-selqp9">Docker镜像tar包 <span class="text-red-500">*</span></label> ${` <div class="${"border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center hover:border-gray-400 dark:hover:border-gray-500 transition-colors " + escape(errors.docker_tar ? "border-red-500" : "", true)}"><input type="file" accept=".tar,.tar.gz,.tgz" class="hidden" ${loading ? "disabled" : ""}> <svg class="mx-auto h-16 w-16 text-gray-400 dark:text-gray-500" stroke="currentColor" fill="none" viewBox="0 0 48 48"><path d="M24 8v24m8-12l-8-8-8 8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path></svg> <div class="mt-4"><button type="button" class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium text-base" ${loading ? "disabled" : ""}>点击选择Docker镜像tar包</button> <p class="text-sm text-gray-500 dark:text-gray-400 mt-2" data-svelte-h="svelte-9bh2sb">支持 TAR, TAR.GZ, TGZ 格式</p> <p class="text-xs text-gray-400 dark:text-gray-500 mt-1" data-svelte-h="svelte-1ozovnv">最大文件大小: 2GB</p></div></div> ${errors.docker_tar ? `<p class="text-sm text-red-600 dark:text-red-400 flex items-center space-x-1">${validate_component(AlertCircle, "AlertCircle").$$render($$result, { class: "w-4 h-4" }, {}, {})} <span>${escape(errors.docker_tar)}</span></p>` : ``}`}</div>`}  <div class="md:col-span-3 space-y-2"><label for="description" class="block text-sm font-medium text-gray-700 dark:text-gray-300" data-svelte-h="svelte-dw9ihe">服务描述</label> <textarea id="description" rows="3" class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white transition-all duration-200 resize-none" placeholder="描述这个服务的功能和用途..." ${loading ? "disabled" : ""}>${escape("")}</textarea></div>  ${`<div class="md:col-span-3 space-y-2"><label class="block text-sm font-medium text-gray-700 dark:text-gray-300" data-svelte-h="svelte-6fhd7w">示例数据 <span class="text-gray-500">(可选)</span></label> ${` <div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center hover:border-gray-400 dark:hover:border-gray-500 transition-colors"><input type="file" accept=".zip,.tar,.tar.gz,.tgz" class="hidden" ${loading ? "disabled" : ""}> <svg class="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" stroke="currentColor" fill="none" viewBox="0 0 48 48"><path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path></svg> <div class="mt-4"><button type="button" class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium text-sm" ${loading ? "disabled" : ""}>点击选择示例数据压缩包</button> <p class="text-sm text-gray-500 dark:text-gray-400 mt-2" data-svelte-h="svelte-bhmxw8">支持 ZIP, TAR, TAR.GZ 格式，最大100MB</p> <p class="text-xs text-gray-400 dark:text-gray-500 mt-1" data-svelte-h="svelte-1efcw6u">可以在服务创建后通过文件更新功能添加</p></div></div>`}</div>`}</div>  <div class="bg-gray-50 dark:bg-gray-800/50 rounded-xl p-6 border border-gray-200 dark:border-gray-700"><div class="flex items-center space-x-2 mb-4"><div class="flex items-center justify-center w-8 h-8 bg-purple-100 dark:bg-purple-900 rounded-lg">${validate_component(Settings$1, "Settings").$$render(
    $$result,
    {
      class: "w-4 h-4 text-purple-600 dark:text-purple-400"
    },
    {},
    {}
  )}</div> <h4 class="text-lg font-semibold text-gray-900 dark:text-white" data-svelte-h="svelte-oimdmz">资源选项</h4></div> <div class="flex gap-6"> <div class="lg:col-span-2 space-y-2"><label for="resource_config" class="block text-sm font-medium text-gray-700 dark:text-gray-300" data-svelte-h="svelte-xxlrn2">资源配置 <span class="text-red-500">*</span></label> <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">${each(Object.entries(resourceConfigs), ([key, config]) => {
    return `<label class="relative"><input type="radio" name="resource_config"${add_attribute("value", key, 0)} class="sr-only svelte-1ny6h8j" ${loading ? "disabled" : ""}${key === formData.resource_config ? add_attribute("checked", true, 1) : ""}> <div class="${"flex flex-col p-2 border-2 rounded-lg cursor-pointer transition-all duration-200 hover:shadow-md " + escape(
      formData.resource_config === key ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20" : "border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500",
      true
    ) + " svelte-1ny6h8j"}"><div class="flex items-center justify-between mb-2"><span class="font-medium text-sm py-1 text-gray-900 dark:text-white">${escape(config.label)}</span> ${key === "recommended" ? `<span class="text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 px-2 py-1 rounded-full" data-svelte-h="svelte-jqzslb">推荐</span>` : ``}</div> <div class="flex items-center space-x-3 text-xs text-gray-600 dark:text-gray-400"><div class="flex items-center space-x-1">${validate_component(Cpu$1, "Cpu").$$render($$result, { class: "w-3 h-3" }, {}, {})} <span>${escape(config.cpu)}</span></div> <div class="flex items-center space-x-1">${validate_component(HardDrive, "HardDrive").$$render($$result, { class: "w-3 h-3" }, {}, {})} <span>${escape(config.memory)}</span></div> </div></div> </label>`;
  })}</div> ${errors.resource_config ? `<p class="text-sm text-red-600 dark:text-red-400 flex items-center space-x-1">${validate_component(AlertCircle, "AlertCircle").$$render($$result, { class: "w-4 h-4" }, {}, {})} <span>${escape(errors.resource_config)}</span></p>` : ``} <div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 mt-3"><p class="text-sm text-blue-800 dark:text-blue-200 flex items-center space-x-2">${validate_component(Info$1, "Info").$$render($$result, { class: "w-4 h-4" }, {}, {})} <span>当前配置：CPU ${escape(formData.cpu_limit)} cores，内存 ${escape(formData.memory_limit)}</span></p></div></div>  <div> <div class="space-y-2"><label for="priority" class="block text-sm font-medium text-gray-700 dark:text-gray-300" data-svelte-h="svelte-mtibqx">启动优先级</label> <select id="priority" class="${"w-full px-4 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white transition-all duration-200 " + escape(
    errors.priority ? "border-red-500 focus:ring-red-500" : "",
    true
  )}" ${loading ? "disabled" : ""}>${each(priorityOptions, (option) => {
    return `<option${add_attribute("value", option.value, 0)}>${escape(option.label)} </option>`;
  })}</select> ${errors.priority ? `<p class="text-sm text-red-600 dark:text-red-400 flex items-center space-x-1">${validate_component(AlertCircle, "AlertCircle").$$render($$result, { class: "w-4 h-4" }, {}, {})} <span>${escape(errors.priority)}</span></p>` : ``} <p class="text-xs text-gray-500 dark:text-gray-400" data-svelte-h="svelte-mcpl6x">数值越小优先级越高</p></div>  <div class="bg-gradient-to-r mt-2 from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg py-2 px-4 border border-green-200 dark:border-green-700"><div class="flex items-start space-x-3"><input type="checkbox" id="is_public" class="mt-1 h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded transition-colors svelte-1ny6h8j" ${loading ? "disabled" : ""}${add_attribute("checked", formData.is_public, 1)}> <div class="flex-1"><label for="is_public" class="block text-sm font-medium text-gray-900 dark:text-white"><div class="flex items-center space-x-2">${validate_component(Shield$1, "Shield").$$render(
    $$result,
    {
      class: "w-4 h-4 text-green-600 dark:text-green-400"
    },
    {},
    {}
  )} <span data-svelte-h="svelte-a332zn">公开访问</span></div></label> <p class="text-xs text-gray-600 dark:text-gray-400" data-svelte-h="svelte-1nu170b">允许任何人访问和使用此服务</p></div></div></div></div></div></div></div></div>  <div class="sticky bottom-0 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 px-6 py-4"><div class="flex items-center justify-between"><div class="text-sm text-gray-500 dark:text-gray-400">${loading ? `<div class="flex items-center space-x-2" data-svelte-h="svelte-aplymk"><div class="animate-spin w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full"></div> <span>正在创建服务...</span></div>` : `确保所有配置正确后点击创建`}</div> <div class="flex space-x-3"><button type="button" class="px-6 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-600 hover:bg-gray-200 dark:hover:bg-gray-500 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed" ${loading ? "disabled" : ""}>取消</button> <button type="submit" class="px-6 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98]" ${loading ? "disabled" : ""}>${loading ? `<div class="flex items-center space-x-2" data-svelte-h="svelte-1u85jfe"><div class="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div> <span>创建中...</span></div>` : `<div class="flex items-center space-x-2">${validate_component(Zap$1, "Zap").$$render($$result, { class: "w-4 h-4" }, {}, {})} <span>${escape(
    "上传并创建服务"
  )}</span></div>`}</button></div></div></div></form></div></div>` : ``}`;
});
const ImageCard_svelte_svelte_type_style_lang = "";
const DropZone_svelte_svelte_type_style_lang = "";
const ImageUploadModal_svelte_svelte_type_style_lang = "";
const Toast_svelte_svelte_type_style_lang = "";
const ImageList_svelte_svelte_type_style_lang = "";
const ServiceFromImageModal_svelte_svelte_type_style_lang = "";
const ImageDetailModal_svelte_svelte_type_style_lang = "";
const _page_svelte_svelte_type_style_lang = "";
const css = {
  code: ".prose.svelte-1bwzabq{max-width:none}.prose.svelte-1bwzabq h1{font-size:1.875rem;line-height:2.25rem;font-weight:700;margin-top:2rem;margin-bottom:1rem}.prose.svelte-1bwzabq h2{font-size:1.5rem;line-height:2rem;font-weight:600;margin-top:1.5rem;margin-bottom:0.75rem}.prose.svelte-1bwzabq h3{font-size:1.25rem;line-height:1.75rem;font-weight:600;margin-top:1.25rem;margin-bottom:0.5rem}.prose.svelte-1bwzabq p{margin-bottom:1rem;line-height:1.75}.prose.svelte-1bwzabq ul{margin-bottom:1rem;padding-left:1.5rem}.prose.svelte-1bwzabq li{margin-bottom:0.5rem}.prose.svelte-1bwzabq code{color:#1e293b;font-size:0.875rem;font-family:'Fira Code', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace}.prose.svelte-1bwzabq pre{background-color:#f1f5f9;color:#1e293b;padding:1.25rem;border-radius:0.5rem;overflow-x:auto;margin-bottom:1.5rem;border:1px solid #e2e8f0;font-family:'Fira Code', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;line-height:1.5}.model-card-content.svelte-1bwzabq{min-height:60vh;width:100%;overflow-wrap:break-word;word-wrap:break-word;padding-bottom:2rem}.model-card-content.svelte-1bwzabq table{display:table;width:max-content;min-width:100%;border-collapse:collapse;margin-bottom:1rem;white-space:nowrap}.model-card-content.svelte-1bwzabq .table-container{overflow-x:auto;margin-bottom:1rem;border:1px solid #e5e7eb;border-radius:0.375rem;scrollbar-width:thin;scrollbar-color:#64748b #f1f5f9}.model-card-content.svelte-1bwzabq .table-container::-webkit-scrollbar{height:8px}.model-card-content.svelte-1bwzabq .table-container::-webkit-scrollbar-track{background:#f1f5f9;border-radius:4px}.model-card-content.svelte-1bwzabq .table-container::-webkit-scrollbar-thumb{background:#64748b;border-radius:4px}.model-card-content.svelte-1bwzabq .table-container::-webkit-scrollbar-thumb:hover{background:#94a3b8}.model-card-content.svelte-1bwzabq table th,.model-card-content.svelte-1bwzabq table td{border:1px solid #e5e7eb;padding:0.75rem;text-align:left;white-space:nowrap;min-width:120px}.model-card-content.svelte-1bwzabq table th{background-color:#f8fafc;font-weight:600}.model-card-content.svelte-1bwzabq img{max-width:100%;height:auto}.model-card-content.svelte-1bwzabq p,.model-card-content.svelte-1bwzabq div,.model-card-content.svelte-1bwzabq span{word-wrap:break-word;overflow-wrap:break-word}",
  map: null
};
function buildFileTree(files2) {
  const tree = {};
  const result = [];
  files2.forEach((file) => {
    const filePath = file.file_path || file.filename;
    const pathParts = filePath.split("/");
    if (pathParts.length === 1) {
      result.push({
        type: "file",
        name: pathParts[0],
        path: filePath,
        data: file,
        level: 0
      });
    } else {
      const folderName = pathParts[0];
      if (!tree[folderName]) {
        tree[folderName] = {
          type: "folder",
          name: folderName,
          path: folderName,
          files: [],
          level: 0
        };
      }
      tree[folderName].files.push({
        type: "file",
        name: pathParts.slice(1).join("/"),
        path: filePath,
        data: file,
        level: 1
      });
    }
  });
  Object.values(tree).forEach((folder) => {
    result.push(folder);
  });
  return result.sort((a, b) => {
    if (a.type === "folder" && b.type === "file")
      return -1;
    if (a.type === "file" && b.type === "folder")
      return 1;
    return a.name.localeCompare(b.name);
  });
}
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let username;
  let repoName;
  let $currentUser, $$unsubscribe_currentUser;
  let $page, $$unsubscribe_page;
  $$unsubscribe_currentUser = subscribe(user, (value) => $currentUser = value);
  $$unsubscribe_page = subscribe(page, (value) => $page = value);
  let repository = null;
  let files = [];
  let availableImages = [];
  let showCreateServiceModal = false;
  let serviceModalLoading = false;
  $$result.css.add(css);
  username = $page.params.username;
  repoName = $page.params.repository;
  $currentUser && repository && isOwner(repository.owner?.username || repository.owner?.id);
  files ? buildFileTree(files) : [];
  $$unsubscribe_currentUser();
  $$unsubscribe_page();
  return `${$$result.head += `<!-- HEAD_svelte-dliw8c_START -->${$$result.title = `<title>${escape(username)}/${escape(repoName)} - GeoML Hub</title>`, ""}<meta name="description"${add_attribute("content", `${username}/${repoName} 仓库`, 0)}><!-- HEAD_svelte-dliw8c_END -->`, ""} <div class="bg-gray-50 dark:bg-gray-900">${`<div class="flex items-center justify-center py-12">${validate_component(Loading, "Loading").$$render($$result, { size: "lg" }, {}, {})}</div>`}</div>  ${validate_component(ServiceCreateModal, "ServiceCreateModal").$$render(
    $$result,
    {
      isOpen: showCreateServiceModal,
      loading: serviceModalLoading,
      availableImages
    },
    {},
    {}
  )}  ${``}  ${``}  ${``}  ${``}  ${``}  ${``}`;
});
export {
  Page as default
};
