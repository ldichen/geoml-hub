import sys
import os

# 添加父目录到路径，以便可以导入app模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.classification import Classification


def init_classifications():
    """初始化分类数据"""
    db = SessionLocal()

    try:
        # 检查是否已经初始化过
        existing = db.query(Classification).first()
        if existing:
            print("分类数据已存在，跳过初始化")
            return

        # 定义分类数据结构
        classifications_data = [
            # 遥感影像解译
            {
                "name": "遥感影像解译",
                "level": 1,
                "sort_order": 1,
                "children": [
                    {
                        "name": "土地覆盖与土地利用",
                        "level": 2,
                        "sort_order": 1,
                        "children": [
                            {"name": "土地覆盖分类", "level": 3, "sort_order": 1},
                            {"name": "农作物类型识别", "level": 3, "sort_order": 2},
                            {"name": "城市功能区划分", "level": 3, "sort_order": 3},
                            {"name": "植被覆盖度估算", "level": 3, "sort_order": 4},
                            {"name": "不透水面提取", "level": 3, "sort_order": 5},
                            {"name": "建设用地识别", "level": 3, "sort_order": 6},
                            {"name": "耕地质量评估", "level": 3, "sort_order": 7},
                            {"name": "草地退化监测", "level": 3, "sort_order": 8},
                        ],
                    },
                    {
                        "name": "目标检测与识别",
                        "level": 2,
                        "sort_order": 2,
                        "children": [
                            {"name": "建筑物检测", "level": 3, "sort_order": 1},
                            {"name": "车辆计数", "level": 3, "sort_order": 2},
                            {"name": "船舶监测", "level": 3, "sort_order": 3},
                            {"name": "基础设施识别", "level": 3, "sort_order": 4},
                            {"name": "道路网络提取", "level": 3, "sort_order": 5},
                            {"name": "油罐检测", "level": 3, "sort_order": 6},
                            {"name": "飞机识别", "level": 3, "sort_order": 7},
                        ],
                    },
                    {
                        "name": "光谱分析应用",
                        "level": 2,
                        "sort_order": 3,
                        "children": [
                            {"name": "矿物识别", "level": 3, "sort_order": 1},
                            {"name": "水质参数反演", "level": 3, "sort_order": 2},
                            {"name": "土壤有机质估算", "level": 3, "sort_order": 3},
                            {"name": "植被生化参数反演", "level": 3, "sort_order": 4},
                            {"name": "岩石类型分类", "level": 3, "sort_order": 5},
                            {"name": "大气成分反演", "level": 3, "sort_order": 6},
                        ],
                    },
                    {
                        "name": "场景分析",
                        "level": 2,
                        "sort_order": 4,
                        "children": [
                            {"name": "地貌类型分类", "level": 3, "sort_order": 1},
                            {"name": "景观格局分析", "level": 3, "sort_order": 2},
                            {"name": "生态系统类型识别", "level": 3, "sort_order": 3},
                            {"name": "土地利用强度评估", "level": 3, "sort_order": 4},
                        ],
                    },
                ],
            },
            # 气象水文预测
            {
                "name": "气象水文预测",
                "level": 1,
                "sort_order": 2,
                "children": [
                    {
                        "name": "天气预报",
                        "level": 2,
                        "sort_order": 1,
                        "children": [
                            {"name": "短期天气预报", "level": 3, "sort_order": 1},
                            {"name": "降水临近预报", "level": 3, "sort_order": 2},
                            {"name": "极端天气预警", "level": 3, "sort_order": 3},
                            {"name": "数值预报后处理", "level": 3, "sort_order": 4},
                            {"name": "雷暴预报", "level": 3, "sort_order": 5},
                            {"name": "能见度预报", "level": 3, "sort_order": 6},
                            {"name": "台风路径预报", "level": 3, "sort_order": 7},
                        ],
                    },
                    {
                        "name": "水文预报",
                        "level": 2,
                        "sort_order": 2,
                        "children": [
                            {"name": "河流流量预报", "level": 3, "sort_order": 1},
                            {"name": "洪水预报", "level": 3, "sort_order": 2},
                            {"name": "干旱监测预警", "level": 3, "sort_order": 3},
                            {"name": "地下水位预测", "level": 3, "sort_order": 4},
                            {"name": "径流预报", "level": 3, "sort_order": 5},
                            {"name": "水库调度优化", "level": 3, "sort_order": 6},
                            {"name": "蒸散发估算", "level": 3, "sort_order": 7},
                        ],
                    },
                    {
                        "name": "气候建模",
                        "level": 2,
                        "sort_order": 3,
                        "children": [
                            {"name": "气候降尺度", "level": 3, "sort_order": 1},
                            {"name": "气候变化检测", "level": 3, "sort_order": 2},
                            {"name": "极端事件分析", "level": 3, "sort_order": 3},
                            {"name": "气候情景预估", "level": 3, "sort_order": 4},
                            {"name": "季节预报", "level": 3, "sort_order": 5},
                            {"name": "气候模式评估", "level": 3, "sort_order": 6},
                        ],
                    },
                    {
                        "name": "大气物理",
                        "level": 2,
                        "sort_order": 4,
                        "children": [
                            {"name": "边界层建模", "level": 3, "sort_order": 1},
                            {"name": "辐射传输计算", "level": 3, "sort_order": 2},
                            {"name": "云微物理过程", "level": 3, "sort_order": 3},
                            {"name": "大气化学模拟", "level": 3, "sort_order": 4},
                        ],
                    },
                ],
            },
            # 地表过程建模
            {
                "name": "地表过程建模",
                "level": 1,
                "sort_order": 3,
                "children": [
                    {
                        "name": "地质灾害",
                        "level": 2,
                        "sort_order": 1,
                        "children": [
                            {"name": "滑坡易发性评价", "level": 3, "sort_order": 1},
                            {"name": "滑坡识别", "level": 3, "sort_order": 2},
                            {"name": "地面沉降监测", "level": 3, "sort_order": 3},
                            {"name": "地震风险评估", "level": 3, "sort_order": 4},
                            {"name": "泥石流预警", "level": 3, "sort_order": 5},
                            {"name": "岩溶塌陷预测", "level": 3, "sort_order": 6},
                            {"name": "地裂缝监测", "level": 3, "sort_order": 7},
                        ],
                    },
                    {
                        "name": "水土流失与侵蚀",
                        "level": 2,
                        "sort_order": 2,
                        "children": [
                            {"name": "土壤侵蚀建模", "level": 3, "sort_order": 1},
                            {"name": "沟蚀发育预测", "level": 3, "sort_order": 2},
                            {"name": "泥沙输移模拟", "level": 3, "sort_order": 3},
                            {"name": "坡面径流模拟", "level": 3, "sort_order": 4},
                            {"name": "风蚀模拟", "level": 3, "sort_order": 5},
                            {"name": "化学风化建模", "level": 3, "sort_order": 6},
                        ],
                    },
                    {
                        "name": "海岸带动力学",
                        "level": 2,
                        "sort_order": 3,
                        "children": [
                            {"name": "海岸线变化监测", "level": 3, "sort_order": 1},
                            {"name": "海浪预报", "level": 3, "sort_order": 2},
                            {"name": "风暴潮模拟", "level": 3, "sort_order": 3},
                            {"name": "海岸侵蚀预测", "level": 3, "sort_order": 4},
                            {"name": "潮汐建模", "level": 3, "sort_order": 5},
                            {"name": "海滩演化模拟", "level": 3, "sort_order": 6},
                        ],
                    },
                    {
                        "name": "地貌演化",
                        "level": 2,
                        "sort_order": 4,
                        "children": [
                            {"name": "河流地貌演化", "level": 3, "sort_order": 1},
                            {"name": "山地地貌建模", "level": 3, "sort_order": 2},
                            {"name": "冰川地貌分析", "level": 3, "sort_order": 3},
                            {"name": "喀斯特地貌建模", "level": 3, "sort_order": 4},
                        ],
                    },
                    {
                        "name": "构造地质",
                        "level": 2,
                        "sort_order": 5,
                        "children": [
                            {"name": "断层活动性评价", "level": 3, "sort_order": 1},
                            {"name": "地应力场分析", "level": 3, "sort_order": 2},
                            {"name": "构造变形建模", "level": 3, "sort_order": 3},
                        ],
                    },
                ],
            },
            # 环境监测评估
            {
                "name": "环境监测评估",
                "level": 1,
                "sort_order": 4,
                "children": [
                    {
                        "name": "大气环境",
                        "level": 2,
                        "sort_order": 1,
                        "children": [
                            {"name": "空气质量预报", "level": 3, "sort_order": 1},
                            {"name": "污染源识别", "level": 3, "sort_order": 2},
                            {"name": "气溶胶光学厚度反演", "level": 3, "sort_order": 3},
                            {"name": "温室气体监测", "level": 3, "sort_order": 4},
                            {"name": "酸雨预测", "level": 3, "sort_order": 5},
                            {"name": "雾霾成因分析", "level": 3, "sort_order": 6},
                            {"name": "臭氧层监测", "level": 3, "sort_order": 7},
                        ],
                    },
                    {
                        "name": "水环境",
                        "level": 2,
                        "sort_order": 2,
                        "children": [
                            {"name": "水质监测", "level": 3, "sort_order": 1},
                            {"name": "富营养化评估", "level": 3, "sort_order": 2},
                            {"name": "水华预警", "level": 3, "sort_order": 3},
                            {"name": "地下水污染评估", "level": 3, "sort_order": 4},
                            {"name": "重金属污染检测", "level": 3, "sort_order": 5},
                            {"name": "水体自净能力评价", "level": 3, "sort_order": 6},
                            {"name": "饮用水安全评估", "level": 3, "sort_order": 7},
                        ],
                    },
                    {
                        "name": "生态环境",
                        "level": 2,
                        "sort_order": 3,
                        "children": [
                            {"name": "植被健康监测", "level": 3, "sort_order": 1},
                            {"name": "生物多样性评估", "level": 3, "sort_order": 2},
                            {"name": "碳汇监测", "level": 3, "sort_order": 3},
                            {"name": "生态系统服务评估", "level": 3, "sort_order": 4},
                            {"name": "物种栖息地适宜性", "level": 3, "sort_order": 5},
                            {"name": "生态廊道分析", "level": 3, "sort_order": 6},
                            {"name": "外来物种入侵监测", "level": 3, "sort_order": 7},
                        ],
                    },
                    {
                        "name": "土壤环境",
                        "level": 2,
                        "sort_order": 4,
                        "children": [
                            {"name": "土壤污染评估", "level": 3, "sort_order": 1},
                            {"name": "土壤肥力评价", "level": 3, "sort_order": 2},
                            {"name": "土壤盐渍化监测", "level": 3, "sort_order": 3},
                            {"name": "土壤重金属检测", "level": 3, "sort_order": 4},
                            {"name": "土壤微生物分析", "level": 3, "sort_order": 5},
                        ],
                    },
                    {
                        "name": "噪声环境",
                        "level": 2,
                        "sort_order": 5,
                        "children": [
                            {"name": "噪声污染评估", "level": 3, "sort_order": 1},
                            {"name": "噪声源识别", "level": 3, "sort_order": 2},
                            {"name": "噪声传播建模", "level": 3, "sort_order": 3},
                        ],
                    },
                ],
            },
            # 变化检测制图
            {
                "name": "变化检测制图",
                "level": 1,
                "sort_order": 5,
                "children": [
                    {
                        "name": "土地利用变化",
                        "level": 2,
                        "sort_order": 1,
                        "children": [
                            {"name": "土地利用变化检测", "level": 3, "sort_order": 1},
                            {"name": "城市扩张监测", "level": 3, "sort_order": 2},
                            {"name": "森林变化监测", "level": 3, "sort_order": 3},
                            {"name": "农业种植结构变化", "level": 3, "sort_order": 4},
                            {"name": "建设用地扩张", "level": 3, "sort_order": 5},
                            {"name": "土地整理效果评估", "level": 3, "sort_order": 6},
                            {"name": "违法用地识别", "level": 3, "sort_order": 7},
                        ],
                    },
                    {
                        "name": "环境变化",
                        "level": 2,
                        "sort_order": 2,
                        "children": [
                            {"name": "荒漠化监测", "level": 3, "sort_order": 1},
                            {"name": "湿地动态监测", "level": 3, "sort_order": 2},
                            {"name": "冰川变化监测", "level": 3, "sort_order": 3},
                            {"name": "海平面上升影响", "level": 3, "sort_order": 4},
                            {"name": "植被覆盖变化", "level": 3, "sort_order": 5},
                            {"name": "水体面积变化", "level": 3, "sort_order": 6},
                            {"name": "雪线变化监测", "level": 3, "sort_order": 7},
                        ],
                    },
                    {
                        "name": "灾害影响评估",
                        "level": 2,
                        "sort_order": 3,
                        "children": [
                            {"name": "地震灾害评估", "level": 3, "sort_order": 1},
                            {"name": "洪水影响评估", "level": 3, "sort_order": 2},
                            {"name": "火灾损失评估", "level": 3, "sort_order": 3},
                            {"name": "台风影响评估", "level": 3, "sort_order": 4},
                            {"name": "旱灾影响评估", "level": 3, "sort_order": 5},
                            {"name": "雪灾影响评估", "level": 3, "sort_order": 6},
                        ],
                    },
                    {
                        "name": "时序分析",
                        "level": 2,
                        "sort_order": 4,
                        "children": [
                            {"name": "植被物候监测", "level": 3, "sort_order": 1},
                            {"name": "作物生长监测", "level": 3, "sort_order": 2},
                            {"name": "水体季节变化", "level": 3, "sort_order": 3},
                            {"name": "温度时空变化", "level": 3, "sort_order": 4},
                        ],
                    },
                ],
            },
            # 多源数据融合
            {
                "name": "多源数据融合",
                "level": 1,
                "sort_order": 6,
                "children": [
                    {
                        "name": "传感器数据融合",
                        "level": 2,
                        "sort_order": 1,
                        "children": [
                            {"name": "光学+SAR融合分类", "level": 3, "sort_order": 1},
                            {"name": "多光谱+高光谱融合", "level": 3, "sort_order": 2},
                            {"name": "遥感+地面观测融合", "level": 3, "sort_order": 3},
                            {"name": "激光雷达+光学融合", "level": 3, "sort_order": 4},
                            {"name": "热红外+可见光融合", "level": 3, "sort_order": 5},
                            {"name": "微波+光学融合", "level": 3, "sort_order": 6},
                        ],
                    },
                    {
                        "name": "多时相数据集成",
                        "level": 2,
                        "sort_order": 2,
                        "children": [
                            {"name": "时间序列重构", "level": 3, "sort_order": 1},
                            {"name": "物候期提取", "level": 3, "sort_order": 2},
                            {"name": "长时间序列趋势分析", "level": 3, "sort_order": 3},
                            {"name": "时间序列聚类", "level": 3, "sort_order": 4},
                            {"name": "周期性分析", "level": 3, "sort_order": 5},
                            {"name": "异常时期检测", "level": 3, "sort_order": 6},
                        ],
                    },
                    {
                        "name": "多尺度数据集成",
                        "level": 2,
                        "sort_order": 3,
                        "children": [
                            {"name": "空间尺度转换", "level": 3, "sort_order": 1},
                            {"name": "时间尺度转换", "level": 3, "sort_order": 2},
                            {"name": "多分辨率融合", "level": 3, "sort_order": 3},
                            {"name": "尺度效应分析", "level": 3, "sort_order": 4},
                        ],
                    },
                ],
            },
        ]

        # 递归创建分类
        def create_classifications(data, parent_id=None):
            created_items = {}
            for item in data:
                classification = Classification(
                    name=item["name"],
                    level=item["level"],
                    parent_id=parent_id,
                    sort_order=item["sort_order"],
                    is_active=True,
                )
                db.add(classification)
                db.flush()  # 获取ID但不提交

                created_items[item["name"]] = classification
                print(
                    f"创建{item['level']}级分类: {item['name']} (ID: {classification.id})"
                )

                # 递归创建子分类
                if "children" in item:
                    create_classifications(item["children"], classification.id)

            return created_items

        # 开始创建分类
        print("开始初始化分类数据...")
        create_classifications(classifications_data)

        # 提交事务
        db.commit()
        print("分类数据初始化完成！")

        # 统计信息
        level1_count = (
            db.query(Classification).filter(Classification.level == 1).count()
        )
        level2_count = (
            db.query(Classification).filter(Classification.level == 2).count()
        )
        level3_count = (
            db.query(Classification).filter(Classification.level == 3).count()
        )

        print(f"统计信息:")
        print(f"- 一级分类: {level1_count}")
        print(f"- 二级分类: {level2_count}")
        print(f"- 三级分类: {level3_count}")
        print(f"- 总计: {level1_count + level2_count + level3_count}")

    except Exception as e:
        print(f"初始化分类数据时发生错误: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_classifications()
