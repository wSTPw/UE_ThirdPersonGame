# PLAN-20261019-002：暗黑幻想标题页

- 状态：implemented
- 日期：2026-10-19
- 用户需求：参考所附黑场、中央标题与底部进入提示的构图，新建独立 UW 并在新资产上重构，不覆盖现有 `UW_MainHUD`。
- 关联模块 / 接口 / 问题：`UUW_MainHUD`、`/Game/MyStuff/Lvl_Start`、`/Game/MyStuff/MyUI/UW_MainHUD`
- 实施记录：[CHG-20261019-002](../Changes/CHG-20261019-002-dark-fantasy-title-screen.md)。

## 现状与目标

`Lvl_Start` 的 Level Blueprint 已核实在 BeginPlay 创建 `/Game/MyStuff/MyUI/UW_MainHUD`，随后加入视口、显示鼠标并设置 UI Only 输入。现有 Widget 是上一版左侧像素菜单，需要保留。

目标是新增一个原创暗黑幻想标题 Widget：近黑背景、中央暗金符文、超大标题、左上开发提示、标题旁版本标识和底部进入提示。参考图只用于构图、留白、层级和色彩气氛，不复制其商标、文字、字体或标志性符号。

## 范围与验收标准

- 新建 `/Game/MyStuff/MyUI/UW_MainTitle_DarkFantasy`，父类为 `UUW_MainHUD`。
- 保留 `Button_StartGame`、`Button_1`、`Button_2` 三个必需 BindWidget；只显示开始按钮，另两个折叠。
- 生成原创近黑背景和透明暗金符文，导入独立纹理目录。
- `Lvl_Start` 改为创建新 Widget；旧 `/Game/MyStuff/MyUI/UW_MainHUD` 不修改、不删除。
- 新 Widget 和 Level Blueprint 编译保存成功，并通过 PIE 截图验证。

## 技术方案

使用 CanvasPanel 全屏布局。背景纹理铺满屏幕；原创符文居中作为低对比装饰；`INTRO CPP` 标题由 UMG 文本渲染，避免把项目名烘焙到图片中；底部 `Button_StartGame` 采用轻量暗金描边和发光提示。`Button_1`、`Button_2` 仅用于满足现有父类绑定并设为 Collapsed。

继续继承 `UUW_MainHUD`，从而复用 `OnButton_StartGameClicked()` 打开 `MyLevel` 的行为。提示文字使用“点击进入世界”，不宣称尚未实现的任意键输入。

## 接口与数据迁移

| 接口 ID / 路径 | 当前行为/值 | 目标行为/值 | 调用方/蓝图影响 | 迁移顺序 |
| --- | --- | --- | --- | --- |
| `/Game/MyStuff/Lvl_Start` CreateWidget Class | `/Game/MyStuff/MyUI/UW_MainHUD` | `/Game/MyStuff/MyUI/UW_MainTitle_DarkFantasy` | 开始关卡运行时显示新标题页 | 新 Widget 编译后再切换 |
| `Button_StartGame` | 点击打开 `MyLevel` | 行为不变，视觉改为底部进入提示 | 父类动态委托继续有效 | 保留精确名称和 Button 类型 |
| `Button_1`、`Button_2` | 点击输出测试日志 | 新 Widget 中折叠，行为实现仍存在 | 不删除以满足 BindWidget | 创建时加入并设 Collapsed |

无存档、网络或 C++ ABI 迁移。

## 实施步骤与依赖

1. 生成原创背景和透明符文源图，复制进项目源素材目录并导入 UE。
2. 新建 Widget Blueprint，搭建根 Canvas、背景、符文、标题、版本、提示和三个必需按钮。
3. 设置纹理 UI 参数、布局、文字和按钮状态样式，编译并校验 BindWidget。
4. 修改 `Lvl_Start` Level Blueprint 的 CreateWidget Class，编译并保存。
5. PIE 截图并确认进入提示可见、旧 Widget 未被修改。
6. 同步 UI 资产契约与变更记录。

## 验证计划

| 场景 | 方法/命令 | 期望结果 | 覆盖边界 |
| --- | --- | --- | --- |
| 新 Widget 合同 | UE-MCP BindWidget 检查与 Blueprint 编译 | 3 个必需按钮满足、0 编译失败 | 父类绑定 |
| 关卡接入 | 读取 Level Blueprint CreateWidget Class | 指向新 Widget | 仅 `Lvl_Start` |
| 实际画面 | 1280×720 PIE 截图 | 暗黑标题页完整显示、无商标或参考图文字 | 本地单客户端 |
| 文档检查 | `python Scripts/Docs/check_docs.py`、`git diff --check` | 通过 | 文档和空白 |

## 风险与回退

暗金细线可能在低分辨率下过暗；通过保留高对比标题和底部提示控制可读性。回退时把 `Lvl_Start` CreateWidget Class 恢复为 `/Game/MyStuff/MyUI/UW_MainHUD`，并删除新增 Widget、纹理与源 PNG。旧菜单资产全程保留。

## 文档同步清单

- `Docs/Systems/UI-Assets.md`
- `Docs/Plans/README.md`
- `Docs/Changes/CHG-20261019-002-dark-fantasy-title-screen.md`
- `Docs/Changes/README.md`
