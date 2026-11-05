# CHG-20261019-002：暗黑幻想标题页

- 状态：completed
- 日期：2026-10-19
- 需求摘要：参考所附黑场标题页构图，新建独立 UW 完成原创暗黑幻想标题界面，并接入开始关卡。
- 关联 PLAN / ADR / 问题 / 接口 ID：[PLAN-20261019-002](../Plans/PLAN-20261019-002-dark-fantasy-title-screen.md)、`UUW_MainHUD`
- Git：工作区变更，未提交

## 原因与结果

用户希望在不继续修改上一版像素菜单的前提下，参考所附标题页重构一套新 UI。已新增 `/Game/MyStuff/MyUI/UW_MainTitle_DarkFantasy`，采用近黑烟尘背景、原创暗金符文、中央大标题、开发提示、版本信息和底部进入按钮。`Lvl_Start` 已切换为创建新 Widget；旧 `/Game/MyStuff/MyUI/UW_MainHUD` 保留。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `ArtSource/UI/DarkFantasyTitle/DarkTitle_Background.png` | 16:9 PNG | 原创近黑烟尘背景 |
| `ArtSource/UI/DarkFantasyTitle/DarkTitle_Sigil.png` | 透明 PNG | 原创破碎日蚀、黑曜石菱形暗金符文 |
| `/Game/MyStuff/MyUI/DarkFantasyTitle/Textures/T_DarkTitle_*` | Texture2D | UI 压缩、NoMipmaps、Nearest、sRGB、NeverStream |
| `/Game/MyStuff/MyUI/UW_MainTitle_DarkFantasy` | 父类 `UUW_MainHUD` | 新标题页 Widget；开始按钮可见，两个测试按钮折叠 |
| `/Game/MyStuff/Lvl_Start` | Level Blueprint CreateWidget Class | 从 `UW_MainHUD` 切换到 `UW_MainTitle_DarkFantasy` |
| `Docs/Architecture.md`、`Docs/Systems/UI-Assets.md` | 运行入口和 UI 契约 | 记录当前创建链、资产路径和行为边界 |

## 接口、事件与资源影响

C++ 签名、反射字段和事件顺序无变化。新 Widget 的 `Button_StartGame`、`Button_1`、`Button_2` 均满足父类必需 BindWidget；开始按钮仍调用 `UUW_MainHUD::OnButton_StartGameClicked()`。提示使用“点击进入世界”，没有声称支持尚未实现的任意键输入。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| UE-MCP `widget.get_bind_widget_contract` | UE 5.8 编辑器 | required 3、satisfied 3、missing 0、wrongType 0、compiles true | `/Game/MyStuff/MyUI/UW_MainTitle_DarkFantasy` |
| UE-MCP `blueprint.compile_all` | UE 5.8 编辑器 | 新 Widget 与 `Lvl_Start` 均 compiled，failed 0、warnings 0 | 对应两个资产 |
| Level Blueprint 节点读回 | UE 5.8 编辑器 | CreateWidget Class 为 `UW_MainTitle_DarkFantasy_C` | `/Game/MyStuff/Lvl_Start` EventGraph |
| PIE 运行时 Widget 枚举 | UE 5.8、单客户端本地 PIE | 视口中唯一根 Widget 为 `UW_MainTitle_DarkFantasy_C_0`；开始按钮可见且完整位于视口 | 运行时检查输出 |
| PIE 1280×722 截图 | UE 5.8、单客户端本地 PIE | 黑金标题页、提示文字和按钮完整显示，无明显裁切 | `Saved/UIPlan/UW_MainTitle_DarkFantasy-final2.png` |
| `python Scripts/Docs/check_docs.py` | Windows / Python | PASS：28 个 Markdown、139 个本地链接、10 个模块和 editor snapshot JSON | 控制台输出 |
| `git -c filter.lfs.process= -c filter.lfs.required=false diff --check` | Windows / Git；禁用本机异常的 LFS filter-process | 通过；仅输出既有 LF→CRLF 提示 | 控制台输出 |

## 风险、遗留与回退

当前只实现鼠标点击进入，没有任意键或手柄任意键处理。标题使用引擎 Roboto 字体，而非参考图字体。回退时将 `Lvl_Start` CreateWidget Class 恢复为 `/Game/MyStuff/MyUI/UW_MainHUD.UW_MainHUD_C`，再删除新 Widget、纹理与源 PNG；旧像素菜单未被覆盖。

## 已同步文档

- [项目架构与运行入口](../Architecture.md)
- [UI、输入与蓝图资产契约](../Systems/UI-Assets.md)
- [方案索引](../Plans/README.md)
- [变更记录索引](README.md)
