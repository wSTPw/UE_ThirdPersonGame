# MHW 太刀素材采集与转换工具

本工具目录用于从用户提供的本机《Monster Hunter World: Iceborne》安装读取原始素材。不是 UE 插件，不会修改游戏安装、项目 Content 或角色动画绑定。

## 工具来源

- [JodoZT/MHWNoChunk](https://github.com/JodoZT/MHWNoChunk)：MIT；分块索引、数据读取和密钥顺序参考。保留下载的原始源码，不修改上游。
- [Feuleur MHW tool suite 1.3.9](https://github.com/Feuleur/blender-mhworld-tools-suite/releases/tag/1.3.9)：MIT；MOD3、MRL3、TEX 和 LMT 导入，使用作者发布包，不修改上游。
- [Blender 4.5.0 Windows portable](https://download.blender.org/release/Blender4.5/blender-4.5.0-windows-x64.zip)：项目本地便携运行时，没有安装到系统目录。
- Oodle：直接加载本机 UE5.8 的 `Engine/Binaries/DotNET/UnrealBuildTool/runtimes/win-x64/native/oo2core.dll`，不复制或随工具分发。MHWNoChunk 指定的 Warframe 官方依赖下载返回 HTTP 403，因此未采用该下载。

下载地址、大小和 SHA256 见 [tool-sources.json](tool-sources.json)，MIT 文本保存在 `Licenses/`。工具许可证不改变 Capcom 游戏素材的权利归属。

## 本地目录

`Downloads/` 为下载归档，`Source/` 为 MHWNoChunk 源码，`BlenderAddons/` 为 Feuleur 发布包，`Runtime/` 为便携 Blender。上述缓存、日志和实际游戏素材已加入根 `.gitignore`，不会作为常规源码提交。

结果位于 [MHWLongSword](../../ArtSource/ThirdParty/MHWLongSword/README.md)。采集元数据保留在项目内，游戏原始文件与转换文件留在本机。

## 脚本与命令

| 脚本 | 用途 |
| --- | --- |
| [extract_resources.py](extract_resources.py) | 只读解析 Iceborne chunk 索引；同路径按数字排序后采用最新包；按正则选择文件并限制总输出体积，记录来源和 SHA256 |
| [inspect_source_assets.py](inspect_source_assets.py) | 转换准备：读取模型骨骼、LMT 动作条目和材质贴图依赖，生成 `source-inventory.json`；不是 UE 运行验证 |
| [build_asset_bundle.py](build_asset_bundle.py) | 组装猎人统一骨架、载入动作、转换角色/武器 FBX 和 Blender 文件；`--export-longsword` 逐条导出太刀 FBX |
| [finish_materials.py](finish_materials.py) | 转换全部采集贴图为 PNG，制作可由 FBX 携带的基础材质，重新保存模型和 Blender 素材包；不重新导出动画 |
| [describe_rigs.py](describe_rigs.py) | 制作过程读取部件绑定矩阵，定位头部原点与护甲附加骨的差异 |

以下命令从项目根目录运行；路径是本机配置，换机器需调整。先恢复上述工具缓存，再执行：

```powershell
python Tools/MHW/extract_resources.py `
  --game 'F:\PCprogram\Steam\steamapps\common\Monster Hunter World' `
  --oodle 'E:\UE\UE_5.8\Engine\Binaries\DotNET\UnrealBuildTool\runtimes\win-x64\native\oo2core.dll' `
  --output 'ArtSource/ThirdParty/MHWLongSword' `
  --pattern '^(hm/wp/wp03/|hm/common/mot/co00_00/|wp/swo/mot/|wp/swo/swo001/|pl/m_equip/pl001_0000/|pl/m_face/face001/)' `
  --max-mb 256

& 'Tools/MHW/Runtime/blender-4.5.0-windows-x64/blender.exe' `
  --background --factory-startup --python-exit-code 1 `
  --python 'Tools/MHW/inspect_source_assets.py'
```

上述首轮输出不包含全部共享贴图。按 `source-inventory.json` 的 `texture_dependencies` 加入提取选择；保留首轮路径集合，第二轮输出清单才覆盖所有素材。本次实际选择见 `extraction-manifest.json` 的 `pattern`。

```powershell
& 'Tools/MHW/Runtime/blender-4.5.0-windows-x64/blender.exe' `
  --background --factory-startup --python-exit-code 1 `
  --python 'Tools/MHW/build_asset_bundle.py' -- --export-longsword

& 'Tools/MHW/Runtime/blender-4.5.0-windows-x64/blender.exe' `
  --background --factory-startup --python-exit-code 1 `
  --python 'Tools/MHW/finish_materials.py'
```

转换脚本保留动作使用的 `bone_###` 原编号和统一的 `bone_root`，不连骨、不自动改名。头部以 `bone_003` 对齐身体绑定原点，并同步移动顶点；腰甲与腿甲重复的非动画附加骨150–153加部件前缀，共享骨骼保持身体父子层级。对齐后头部导入器生成的临时 `bone_root` 偏移属于部件原点信息，合并时使用身体的统一根骨，不替换它。其余共享骨骼静止矩阵差异写入转换报告，不能据编号覆盖就断言运行姿态正确。每个太刀 FBX 只导出当前 Action，不含其他 Action/NLA，不添加叶骨。输出按 60 FPS 生成；具体动作名称、玩法意义和 UE 导入后的根位移仍需后续适配确认。

可移植材质只连接原始颜色和法线贴图，RMT、染色、毛发、积雪等原游戏材质效果保留原始文件待适配，未宣称完整复现。PNG 图集没有拼接为一张 atlas，保留来源目录关系。

重新制作前先辨别 `Converted/` 中有无手工调整：Blender 转换命令会重写该目录的同名产物。原始采集脚本遇到不同内容的同名目标会拒绝覆盖。

## UE 接入脚本

源素材工具仍不写 Content；后续独立接入位于 [Scripts/MHWI](../../Scripts/MHWI)，当前使用说明见 [MHWI 模组](../../Docs/Systems/MHWI-LongSword.md)。当前九条 Common FBX 加 164 条太刀共 173 条动画导入独立原生角色骨架，其中 Common 正式使用 001/203/090/130。034/035 是攀爬动作，不能按循环标志推断地面走跑。气刃II/上挑现为 106/107，旧推断标签已在[动画修正](../../Docs/Changes/CHG-20261022-004-mhwi-animation-corrections.md)更正。

2026-10-24新增源采样旁路：项目 [native_animation_source.py](../../Scripts/MHWI/native_animation_source.py) 仅加载 [wowo-dot/mhw-anim-tools](https://github.com/wowo-dot/mhw-anim-tools) 的 CPU reader/pose evaluation 模块（MIT，缓存为v1.1.0），不安装/注册或修改该插件。工具和依赖逐文件SHA256记录在 `ArtSource/ThirdParty/MHWLongSword/NativeFidelity/export-manifest.json`；保留上游 LICENSE，更新缓存后须重新资格验证，不能将旧报告用于新版本。

[export_native_animation.py](../../Scripts/MHWI/export_native_animation.py) / [verify_native_animation.py](../../Scripts/MHWI/verify_native_animation.py) 在独立 NativeFidelity 目录制作/重读FBX；[native_weapon_export.py](../../Scripts/MHWI/native_weapon_export.py) / [native_weapon_verify.py](../../Scripts/MHWI/native_weapon_verify.py) 处理独立武器骨架。原 Converted、LMT 和源 blend 不覆盖。UE 接入由 [author_native_fidelity.py](../../Scripts/MHWI/author_native_fidelity.py) 完成，先备份，再校验哈希/时长/骨架；只迁移指定的合格 Montage 段。当前36段合格，309/310/311因NeedsParent缺外部姿态保留原资源。[资格检查](../../Scripts/MHWI/qualify_native_assets.py) 的原生根参考由 [export_native_root_reference.py](../../Scripts/MHWI/export_native_root_reference.py) 生成。运行结果与边界见 [实施记录](../../Docs/Changes/CHG-20261024-002-mhwi-native-fidelity-implementation.md)。

后续三色309/310/311已通过共享骨轨资格证明，正式Montage复用Native308，未声称通用NeedsParent求值已解，见 [CHG-003](../../Docs/Changes/CHG-20261024-003-mhwi-defense-routes-transfer.md)。

## 原始参数批处理（2026-10-24）

用户改为参数优先。独立 `NativeParameters/` 提取48项资源，原始安装只读；[固定格式来源](native-parameter-sources.json)保存Synthlight/MHW-Editor的commit/5文件SHA256，[extract_native_longsword_params.py](../../Scripts/MHWI/extract_native_longsword_params.py)显式`--fetch-layout`可恢复缺失缓存，不运行或修改第三方插件。Node.js的OpenSSL legacy provider仅用于按公开格式读取Blowfish资源，未安装全局依赖。

[build_native_action_database.py](../../Scripts/MHWI/build_native_action_database.py)一次汇总425字段、164动作、完整FSM/TIML和4条IK链；[extract_native_equipment_params.py](../../Scripts/MHWI/extract_native_equipment_params.py)保留IK成员偏移和原生关节号。[author_native_parameters.py](../../Scripts/MHWI/author_native_parameters.py)在UE内预览/备份后将17招式属性+4全局属性写入正式DA，保留引用和路由。完整操作、原始字段和未解消费者见 [参数批处理说明](../../Docs/Reference/MHWI-Native-Parameter-Pipeline.md)，结果见 [CHG-004](../../Docs/Changes/CHG-20261024-004-mhwi-native-parameter-pipeline.md)。未知位域不自动变成取消窗，CMS已确认为相机设置。

## R06 B10开发重建（2026-10-25）

R06剩余三项开发完成，未编译/测试；[现状与资源清单](../../Docs/Reference/MHWI-R06-Remaining-Development.md)、[本批记录](../../Docs/Changes/CHG-20261025-005-mhwi-r06-remaining.md)。稳定数据：`native-r06-source-owners.json`、`native-r06-remaining-evidence.json`、`native-link-motion-policy.json`、`r06-runtime-adapter.json`；保留原始身份、请求门控、MotionTree行、时钟链及32个新增资源对象路径。

源码/资料生成顺序：`extract_r06_remaining.py` → `build_native_link_policy.py` → `build_link_runtime_data.py` → `build_r06_remaining_data.py` → `record_r06_remaining_progress.py`，脚本均在`Scripts/MHWI/`；这些入口只制作数据/记录，不运行测试。输出B10目录，不覆盖B09历史。Blender执行`export_r06_remaining.py`制作FBX，MCP使用`import_r06_staging.run`并传R06Remaining manifest、B10 journal、目标目录`/Game/MHWI/Animations/R06Remaining`；已有包/journal拒绝覆盖。
