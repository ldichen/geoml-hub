const prerender = true;
async function load() {
  return {
    meta: {
      title: "搜索模型 - GeoML-Hub",
      description: "搜索地理科学机器学习模型和数据集",
      keywords: "模型搜索,仓库搜索,GeoML"
    }
  };
}
export {
  load,
  prerender
};
