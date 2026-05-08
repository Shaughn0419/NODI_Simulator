# `dashboard/panels/inspector.py`

## 文件定位
- 类型：Dashboard 页面模块
- 模块摘要：dashboard/panels/inspector.py — Case Inspector 页面
- 当前职责：Case Inspector 页面，负责对单个候选点做 verdict、机制统计与 trace 复核。

## 主要符号
- 顶层函数：`_build_case_trend_notes`、`_build_inspector_verdict_frame`、`render_inspector`
- 顶层类：当前没有顶层类，或主要以函数式模块组织逻辑。

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：优先在这里维护页面叙事、显示顺序和文案；涉及数据读取、重算或统计口径时，应尽量下沉到 backend 层。

## 关联代码
- `dashboard/backend.py`
- `dashboard/config.py`
- `dashboard/panels/common.py`

## 页面定位
**这页回答：** 某个候选点为什么被推荐、被挡住，或者只适合作为观察对象。

- 负责单 case verdict、blocker、freeze、trace 复核；不负责全局找平台（先在 Explorer 做）
- 适合在锁定候选点后做最终复核
- 页面现在是顺序单页：verdict、机制统计、单事件 trace
- 旧的 tabs、教学说明和图表解读区已移除
- 关键字段：`decision_summary`、`engineering_gate_*`、`observation_freeze_status`、单事件 trace 和 batch 波动

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
