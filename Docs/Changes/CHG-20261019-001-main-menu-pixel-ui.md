# CHG-20261019-001：像素风格主菜单

- 状态：completed
- 日期：2026-10-19
- 需求摘要：规划并美化 `UW_MainHUD`，允许调整布局和新增 UI，生成并落地一套像素风格贴图。
- 关联 PLAN / ADR / 问题 / 接口 ID：[PLAN-20261019-001](../Plans/PLAN-20261019-001-main-menu-pixel-ui.md)、`UUW_MainHUD`
- Git：工作区变更，未提交

## 原因与结果

原开始菜单在实际 PIE 中仅显示纯灰背景和三个默认灰色按钮。当前菜单改为月夜遗迹像素背景、剑与法杖标题徽记、透明石质面板和三态像素按钮；新增标题、副标题、构建版本与操作提示，并将菜单重排到背景左侧暗区。三个 C++ BindWidget 名称及点击行为保持不变。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `ArtSource/UI/MainMenuPixel/MainMenu_Background.png` | 16:9 PNG 源图 | 月夜遗迹全屏背景 |
| `ArtSource/UI/MainMenuPixel/MainMenu_Crest.png` | 透明 PNG 源图 | 剑、法杖和符文标题徽记 |
| `ArtSource/UI/MainMenuPixel/MainMenu_Panel.png` | 透明 PNG 源图 | 左侧主菜单面板 |
| `ArtSource/UI/MainMenuPixel/MainMenu_ButtonStates.png` | 透明 PNG 图集 | Normal、Hover、Pressed 三态按钮 |
| `/Game/MyStuff/MyUI/MainMenu/Textures/T_MainMenu_*` | Texture2D | 导入四张源图并设置 UI 压缩、NoMipmaps、Nearest、sRGB、NeverStream |
| `/Game/MyStuff/MyUI/UW_MainHUD` | WidgetTree、CanvasPanelSlot、FButtonStyle | 新增装饰与文字、重排锚点、使用按钮图集 UVRegion |
| `Docs/Systems/UI-Assets.md` | 开始菜单视觉契约 | 记录路径、层级、纹理设置和行为边界 |

## 接口、事件与资源影响

C++ 签名、反射字段和事件顺序无变化。`Button_StartGame`、`Button_1`、`Button_2` 仍是同名 `Button` 且全部满足父类 `UUW_MainHUD` 的必需绑定。新增纹理被 `UW_MainHUD` 直接引用；源 PNG 用于重新导入。`Button_1` 和 `Button_2` 仍只记录日志，没有改造成设置或退出功能。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| UE-MCP `widget.get_bind_widget_contract` | UE 5.8 编辑器 | required 3、satisfied 3、missing 0、wrongType 0、compiles true | `/Game/MyStuff/MyUI/UW_MainHUD` |
| UE-MCP `blueprint.compile_all` | UE 5.8 编辑器 | compiled 1、failed 0、warnings 0，并保存资产 | `/Game/MyStuff/MyUI/UW_MainHUD` |
| UE-MCP 纹理属性读取/批量写入 | UE 5.8 编辑器 | 四张纹理均为 NoMipmaps；Filter 写入 TF_Nearest 并保存 | `/Game/MyStuff/MyUI/MainMenu/Textures` |
| PIE 运行与 1280×722 截图 | UE 5.8、单客户端本地 PIE | 背景、徽记、面板、按钮及中英文文字完整显示，无明显裁切 | `Saved/UIPlan/UW_MainHUD-after-v1.png` |
| `python Scripts/Docs/check_docs.py` | Windows / Python | PASS：26 个 Markdown、130 个本地链接、10 个模块和 editor snapshot JSON | 控制台输出 |
| `git -c filter.lfs.process= -c filter.lfs.required=false diff --check` | Windows / Git；禁用本机异常的 LFS filter-process 后执行同一空白检查 | 通过；仅输出既有 LF→CRLF 提示 | 控制台输出 |

## 风险、遗留与回退

测试按钮仍为开发占位功能。当前按钮使用同一图集的 UVRegion；替换图集时必须保持三段区域或同步更新 FButtonStyle。回退可恢复 `UW_MainHUD.uasset`，删除 `/Game/MyStuff/MyUI/MainMenu` 和 `ArtSource/UI/MainMenuPixel`；没有存档或玩家数据迁移。

## 已同步文档

- [UI、输入与蓝图资产契约](../Systems/UI-Assets.md)
- [方案索引](../Plans/README.md)
- [变更记录索引](README.md)
