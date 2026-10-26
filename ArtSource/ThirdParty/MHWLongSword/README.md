# Monster Hunter World 太刀与配套角色素材

- 日期：2026-10-22。
- 来源：用户提供的本机 `F:/PCprogram/Steam/steamapps/common/Monster Hunter World`，从 `chunk/chunkG*.bin` 读取，按数字顺序合并最新版资源。未读取 `nativePC` 中已有 MOD 作为原版素材。
- 状态：原始素材已采集，Blender/FBX 转换已输出；材质整理见 [conversion-report.json](conversion-report.json)。已追加独立 `/Game/MHWI` 导入与玩法接入，详见文末 UE 更新；未替换现用 Ninja。
- 工具与复现命令：[Tools/MHW](../../../Tools/MHW/README.md)。游戏素材的权利归 Capcom 等原权利人，工具 MIT 许可不构成游戏素材再分发或商用许可。

## R06 B10新增来源与专用片段（2026-10-25）

`R06Remaining-20261025/export-manifest.json`记录32段源采样FBX：29段w03_00、3段co00_00，导入到`/Game/MHWI/Animations/R06Remaining`并由角色CDO硬引用。规范Step、弹刀恢复、投射器连射、SpiritI/StepSlash专用入口及四向翻滚使用这些序列。完整对象路径、制作失败与恢复、重建和回退见[B10交付](../../../Docs/Reference/MHWI-R06-Remaining-Development.md)。资产已制作，未做完工后测试或新的读回验证；原始文件未修改。

## 可用文件

| 本目录下的路径 | 内容与边界 |
| --- | --- |
| `Converted/Animations/w03_00_*.fbx` | 164 条太刀动作，每条一个 FBX，使用同一猎人骨架；名称保留源动作编号，未逐条人工命名为具体招式 |
| `Converted/SK_MHW_Hunter_pl001.fbx` | 原版男性猎人：`pl001_0000` 五个护甲部件与 `m_face001`，组装为单一225骨骨架、多网格；不是已创建的 UE SkeletalMesh |
| `Converted/swo001.fbx`、`Converted/saya001.fbx` | 配套太刀与刀鞘；尚未接入 UE 武器挂点和拔刀/收刀时序 |
| `Converted/MHW_Hunter_LongSword_Actions.blend` | 猎人、武器与482条 Action：164 条太刀 + 318 条通用动作。通用动作当前保存在 Blender 和原始 LMT 中，未逐条导出通用动作 FBX |
| `Converted/Textures/` | 71张PNG，18个基础颜色/法线材质；完整游戏染色、RMT、毛发、积雪等 shader 尚未复现。1张BC6 HDR环境贴图由工具限制保留TEX原文件，具体项见转换报告 |
| `nativePC/hm/wp/wp03/mot/w03_00/w03_00.lmt` | 原版太刀动作库，含 Iceborne 动作数据；从数据条目获取164条有效动作，并非全部槽位都有动作 |
| `nativePC/hm/common/mot/co00_00/co00_00.lmt` | 318 条通用动作库；不是已按项目走跑/攻击等状态分类的资产 |
| `nativePC/pl/`、`nativePC/wp/`、`nativePC/Assets/` | MOD3 模型、MRL3 材质、TEX 贴图以及附属武器/动画数据；保持源路径 |

原始提取共140个文件，约49.60 MiB。缓存、原始二进制和转换产物由项目 `.gitignore` 排除，仍保存在本机；元数据与制作脚本可纳入版本管理。

## 骨架、根运动与转换约定

- 使用原骨骼编号 `bone_###`，对象名 `Armature`，骨架数据名 `MHW_Hunter_Skeleton`，统一根骨 `bone_root`。保留源 LMT 的根轨迹，不制作 In Place 替代版本；源482条动作中467条具有根轨道，其余不能宣称有位移。
- 六个角色部件按身体骨架合并，共225骨。保留身体原有父子关系；头部源模型在头部原点居中，基于 `bone_003` 同时平移绑定矩阵和网格顶点。腰甲与腿甲重用的非动画附加骨150–153加部件前缀，避免合并为同一骨。
- 转换报告仍保留头部临时 `bone_root` 的源原点偏移诊断；该临时根被身体统一根替代，不作为第二个动画根导出。没有用这条诊断宣称 UE 中姿态已验证。
- 按60 FPS生成，按帧烘焙太刀 FBX，关闭全部 Action/NLA混合导出与额外叶骨，未进行动画曲线精简。Blender素材保留稀疏源动作。
- 已在独立 `/Game/MHWI` 接入地面招式、气刃、见切、居合和登龙；源碰撞窗口已映射，取消/反击帧为项目调校；当前 `/Game/MyStuff/Animation/Ninja` 等现用资产没有切换。

## 追溯与后续接入

- [extraction-manifest.json](extraction-manifest.json)：每个原始文件的来源包、偏移、大小和SHA256。
- [source-inventory.json](source-inventory.json)：源模型骨骼编号、动作编号/帧范围和材质依赖。`texture_dependencies` 是首轮读取时发现并在第二轮提取补齐的清单，不代表最终仍缺失这些文件。
- [conversion-report.json](conversion-report.json)：实际输出、骨架调整、材质状态及保留原格式的贴图。

独立模组已接入；若进一步替换原角色，应另建迁移方案：先导入新 Skeleton 与 SkeletalMesh、确认厘米尺度/朝向和唯一根骨，再重定向或切换角色网格，设置 Root Motion、重建 Montage/通知窗口和动作数据。素材获取完成不等于这些步骤已完成。素材采集阶段未做运行验证；后续用户已取消限制，模组验证见新变更记录。

回退：仅移除本次新增素材目录与 `Tools/MHW` 及对应 `.gitignore` 条目；游戏安装与项目 Content 不需要恢复。若以后对转换文件手工修改，移除前先另存；重新运行转换脚本会重写同名产物。

## UE 接入更新（2026-10-22）

已导入 `/Game/MHWI`，新增训练地图、角色、ABP、Montage、动作数据与 HUD，详见 [当前模组](../../../Docs/Systems/MHWI-LongSword.md)。此前“尚未接入/禁止验证”的叙述仅描述素材采集阶段；用户随后已取消验证限制。本轮实际构建与 PIE 另记新的变更记录。锁根使用 REF_POSE 保留导入参考根骨的 -90° X 基底；ANIM_FIRST_FRAME 会使该批动画横躺。材质槽显式强制保存，避免 Python 结构体就地赋值未标脏造成重启后丢失。

## 源采样与武器轨道更新（2026-10-24）

`NativeFidelity/Animations`、`Common`、`Weapons` 是新采样平行FBX；`export-manifest.json` 保存36段猎人动作、逐文件来源/工具SHA256、整数及子帧矩阵、FBX重读与原文件未变证据。`rig-bind.json` 保存225骨绑定层级。原 Converted 产物未覆盖；309/310/311缺外部基姿态，未伪造合格版本。六条wg03_00武器动画对应swo001的内部手柄运动；不能把它们当作整刀或刀鞘的挂接Transform。

UE正式Montage已逐段迁移27处引用，原Montage身份/裁剪/倍率/通知保留；其余平行Common仅供对照，基础移动未迁移。磁盘备份和本轮验证位于 `Saved/MHWIImport/NativeFidelity-20261024/`，完整说明见 [当前实施与公开资料路线](../../../Docs/Reference/MHWI-Native-Fidelity-Implementation.md)。源码工具仍在 [Scripts/MHWI](../../../Scripts/MHWI)，上游MIT采样器只读加载约定见 [工具说明](../../../Tools/MHW/README.md)。完整装配、连接和取消时序未声称完成。

后续更新：三条有色居合依据与308共享完整骨轨块的证明改用合格Native308，累计30组正式引用迁移；颜色身份/速度/事件不变。通用NeedsParent语义仍未完整实现。

## 参数资源更新（2026-10-24）

`NativeParameters/nativePC/`另存48项/约0.23MiB只读提取的w03p、IK、动作树、碰撞/shell和相机参数，独立`extraction-manifest.json`保留来源包/偏移/SHA256，不覆盖首轮素材清单。原始w03p保持加密原样，解码结果只写Saved。

425字段/100具名参数、4条完整IK和全量TIML/FSM统一库在 `Saved/MHWIImport/NativeParameterResearch-20261024/`；21处支持属性已批量导入正式DA。[批处理说明](../../../Docs/Reference/MHWI-Native-Parameter-Pipeline.md)区分原始值、明确单位转换、项目调校及未知消费语义，避免把解包完成当成原作全系统已还原。
