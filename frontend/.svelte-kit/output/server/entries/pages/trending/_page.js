const prerender = true;
async function load() {
  return {
    meta: {
      title: "探索模型 - GeoML-Hub",
      description: "探索最新和最热门的地理科学机器学习模型",
      keywords: "模型探索,热门模型,趋势,GeoML"
    }
  };
}
export {
  load,
  prerender
};
