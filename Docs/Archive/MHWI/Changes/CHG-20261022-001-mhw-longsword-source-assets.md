# CHG-20261022-001：MHW 太刀与配套猎人素材采集

- 状态：completed（素材获取/转换）；UE 接入待实施，运行效果未验证。
- 日期：2026-10-22。
- 需求摘要：寻找《怪物猎人：世界》太刀动画与适配角色。网络未找到可直接取得的完整原版动画包；用户随后提供本机游戏目录，改从本机原始数据包提取。
- 关联问题：R-ANIM-003；不变更现有玩法接口。
- Git：工作区变更，未提交。

## 原因与结果

从用户指定的本机 Iceborne 安装，只读合并13个 chunk 包的最新路径，索引171615个文件，定向提取140个文件（约49.60 MiB），不混入已有 nativePC MOD。使用网上取得的MIT工具源码/发布包和官方便携Blender，制作原版太刀164个独立动画FBX、男性猎人模型FBX、太刀/刀鞘FBX，以及包含164太刀+318通用Action的Blender文件。

角色按原骨骼编号合并，修正头部绑定原点、腰甲附加骨ID冲突和局部骨架覆盖父子关系问题，输出225骨统一猎人骨架。源根轨迹保留，尚未在UE导入后确认Root Motion位移或重定向效果。基础材质与PNG整理状态见转换报告，原版完整shader未复现；BC6环境贴图原TEX保留。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `E:/Unreal Projects/IntorCpp/Tools/MHW/` | 提取、依赖读取、骨架组装、FBX/贴图转换脚本；上游包/许可/来源摘要 | 独立素材管线；第三方源码和发布包未打补丁 |
| `E:/Unreal Projects/IntorCpp/ArtSource/ThirdParty/MHWLongSword/` | 原始文件、转换产物、来源/制作元数据与README | 本机游戏素材隔离保存，不导入Content |
| `E:/Unreal Projects/IntorCpp/.gitignore` | 指定素材二进制、便携运行时、第三方缓存和日志 | 防止提交游戏素材和大型依赖，不忽略制作脚本/说明 |
| `E:/Unreal Projects/IntorCpp/Docs/README.md`、`Docs/Known-Issues.md`、`Docs/Changes/README.md` | 素材入口与待接入边界 | 便于后续AI接手，不将转换当成UE集成 |

## 接口、事件与资源影响

无C++/反射/蓝图接口变化。现用Ninja动画、ABP、BlendSpace、Montage、DataAsset、角色网格与游戏安装均未改。仓库已有大量源码和二进制工作区修改，未覆盖。第三方文件是独立原样缓存；项目自制脚本位于Tools/MHW，不修改UE_MCP工具。

## 实际执行与未验证项

| 操作 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| `extract_resources.py`索引/定向提取 | 用户提供的本机chunk；本机UE5.8 Oodle | 140文件成功输出；SHA256记录于清单，未全量解包游戏 | `ArtSource/ThirdParty/MHWLongSword/extraction-manifest.json` |
| `inspect_source_assets.py`源条目/依赖读取 | 项目内便携Blender4.5.0 | 164太刀、318通用；8个原始模型；首轮45个共享贴图引用已第二轮补齐 | 同目录`source-inventory.json` |
| `build_asset_bundle.py --export-longsword` | 同上 | 角色225骨；164动作FBX、3模型FBX、482 Action Blender文件输出 | 同目录`conversion-report.json`；`Tools/MHW/conversion.log` |
| `finish_materials.py` | 同上 | 制作71张PNG、18个基础材质；1张BC6环境贴图保留原TEX | 同目录`conversion-report.json`；`Tools/MHW/materials.log` |
| `python Scripts/Docs/check_docs.py` | 项目根目录 | 通过：41篇Markdown、278个本地链接、11个模块；仅文档引用检查 | 命令输出 |
| `git diff --check -- .gitignore Docs/README.md Docs/Known-Issues.md Docs/Changes/README.md` | 本次修改范围 | 通过；全工作区不带路径的命令先遇到`remote end hung up unexpectedly`，因此限定本轮文本范围；未追查用户已有二进制修改 | 命令输出 |
| 项目编译、UE导入、重定向、PIE、动画视觉回读 | UE5.8 | 未执行；遵循用户先前禁止完工后验证的要求 | 无 |

以上源数据读取和转换是素材制作过程，不是项目功能测试。工具制作中已修复一次Blender集合API调用错误；不把首轮旧骨架输出当成最终产物。未将历史自动化或PIE结果当成本轮结果。

## 风险、遗留与回退

R-ANIM-003：素材尚未接入UE；具体招式名称、根位移、绑定姿态、武器握持/收刀、通知与动作窗口需后续处理。基础材质不是原游戏shader完整复现，BC6环境贴图未转换。游戏素材权利不随MIT工具许可转移，二进制素材默认留本机。

回退只涉及本次新建的Tools/MHW、ArtSource/ThirdParty/MHWLongSword、文档与追加.gitignore条目；不回退用户已有修改。不修改游戏安装或现用Content，因此无需恢复它们。

## 已同步文档

- [素材说明](../../ArtSource/ThirdParty/MHWLongSword/README.md)
- [工具说明](../../Tools/MHW/README.md)
- [技术入口](../README.md)
- [已知问题](../Known-Issues.md)
- [记录索引](README.md)
