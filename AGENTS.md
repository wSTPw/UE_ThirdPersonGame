# IntroCpp：AI 开发与文档约定

本文件适用于整个项目。按用户当前指令推进；日常实现和文档维护不增加额外审批步骤。

## 先定位再修改

1. 阅读 [技术文档入口](Docs/README.md)，按任务选择相关系统文档与接口。
2. 运行 `git status --short`，辨别已有修改；不要覆盖用户未提交的资产。
3. 实际构建源码在 `Source/`。`C++ Source/` 是另一份参考副本，不是 UBT 编译入口。
4. 配置、C++ 实现、实际蓝图/关卡设置是现状依据。旧设计稿中的计划不能视为已实现功能。
5. 涉及蓝图、DataAsset、Montage、Widget 时，核对完整 `/Game/...` 路径、父类和实际属性；仅文件名相同不代表同一资产。

## 每次有实质修改时同步记录

- 修改前：复杂功能用 [功能方案模板](Docs/Templates/Feature-Plan.md) 建立 `Docs/Plans/PLAN-YYYYMMDD-NNN-主题.md`；小修复直接使用变更记录即可。
- 修改中：接口签名、返回语义、事件、资产路径或配置变化，同步更新对应现状文档；跨模块长期决策才新增 ADR。
- 修改后：使用 [变更记录模板](Docs/Templates/Change-Record.md)，新增 `Docs/Changes/CHG-YYYYMMDD-NNN-主题.md`，更新 [记录索引](Docs/Changes/README.md)。同日编号先检查已有文件。
- 新系统/关键入口变更：维护 [模块索引](Docs/Reference/modules.json)。新发现或解决的问题维护 [已知问题](Docs/Known-Issues.md)。
- 明确写出“已实现、方案中、待验证、静态发现、运行验证”的区别；禁止把历史测试写成此次已执行。
- 记录改动原因、源文件/符号、接口及蓝图影响、验证命令和实际结果、未验证项、回退方法。记录定位信息，不复制整份源码或敏感配置。
- 已完成的变更记录保留历史含义；后续行为改变应新建记录并更新现状页。

## 实现边界

- 当前 UE 5.8 项目主要为本地玩法；`HasAuthority()` 的局部判断不表示已实现多人同步。
- 物品/快捷栏、动画通知、委托生命周期的既有边界见系统文档和已知问题；不要按旧注释假定事务性或幂等性。
- 动态委托目标需 `UFUNCTION()`；修改反射字段/类名时同时检查蓝图、数据资产和重定向迁移。
- Unreal UObject、Actor、Widget 的修改按游戏线程处理。异步回调核对对象生命周期。
- `Plugins/UE_MCP_Bridge` 与 `Tools/ue-mcp` 属于第三方工具集；业务功能优先落在项目源码，修改第三方时单独说明本地补丁与更新影响。

## 完成检查

遵循 [开发与验证流程](Docs/Development.md)，只执行与变更相称的验证。文档改动运行：

```powershell
python Scripts/Docs/check_docs.py
git diff --check
```

C++/反射/蓝图行为改变再按需编译、PIE 或 MCP 验证。不要仅为文档改动重新完整编译引擎。
