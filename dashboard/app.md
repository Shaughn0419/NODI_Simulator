# `dashboard/app.py`

## 文件定位
- 类型：Dashboard 页面入口
- 模块摘要：dashboard/app.py — Streamlit 主入口
- 当前职责：Streamlit dashboard 主入口，负责页面配置、导航结构、session 初始化与顶层路由。

## 主要符号
- 顶层函数：`_default_data_prefix`、`_render_decision_summary`、`_render_engineering_windows`、`_render_mie_explorer`、`_render_interference_explorer`、`_render_noise_detection_explorer`、`_render_design_explorer`、`_render_case_inspector`、`_render_single_case_calculator`
- 顶层类：当前没有顶层类，或主要以函数式模块组织逻辑。

## 调用与使用
- 典型使用方式：通常通过 Streamlit 启动，例如从仓库根目录运行 `streamlit run dashboard/app.py`。
- 直接维护建议：这里适合放共享配置、结果加载和计算桥接逻辑；尽量避免把页面展示文案和大段 UI 拼装塞进来。

## 关联代码
- `dashboard/backend.py`
- `dashboard/config.py`
- `dashboard/panels/common.py`
- `dashboard/panels/explorer.py`
- `dashboard/panels/inspector.py`
- `dashboard/panels/interference_explorer.py`
- `dashboard/panels/mie_explorer.py`
- `dashboard/panels/noise_detection_explorer.py`
- `dashboard/panels/research_story.py`
- `dashboard/panels/single_case_calculator.py`

## 页面结构与原则

当前三层导航：
- 科研展示：`Decision Summary → Engineering Windows`
- 证据与机理：`Mie Explorer → Interference Explorer → Noise & Detection Explorer → Design Explorer → Case Inspector`
- 独立计算：`Single-Case Calculator`

当前原则：
1. 默认结果源优先读取当前标准 biomimetic full-range 主库。
2. `Single-Case Calculator` 是独立工具页，不与科研展示主线混在一起。
3. 启动脚本只负责启动与提示当前标准结果库状态，不触发旧预计算。

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
