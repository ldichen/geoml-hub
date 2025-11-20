const prerender = true;
async function load() {
  return {
    meta: {
      title: "GeoML-Hub - 地理科学机器学习模型仓库",
      description: "首个专注于地理科学的机器学习模型中心，提供模型发现、共享和部署服务",
      keywords: "地理科学,机器学习,模型仓库,GeoML,深度学习"
    }
  };
}
export {
  load,
  prerender
};
