# CHG-20261024-002：源采样修复、独立武器轨道与公开资料路线

- 状态：partial；本轮源采样/武器轨道阶段已实施，完整原作还原未完成。
- 日期：2026-10-24。
- 需求摘要：用户要求执行源保真调查后的修复，随后要求换用较轻的方法，不配合原作进程采集。
- 关联：[PLAN-20261024-001](../Plans/PLAN-20261024-001-mhwi-native-fidelity-implementation.md)，MHWI-006，R-ANIM-007..009、R-COMBAT-009。
- Git：工作区变更，未提交。项目原有大量源码/资产修改保留；仅处理本轮MHWI文件，不恢复整个工作区。

## 原因与结果

旧转换器对压缩四元数和量化/插值的处理有差异，武器内部动作也未执行。新增只读原生采样旁路，36段平行猎人动画合格导入，正式Montage替换27处段引用；另接入当前型号六条独立武器动画，32个正式招式配置共19个源事件。拔纳刀/居合能消费内部手柄动作，结束、中断与死亡恢复确定姿态。

完整装配/换手/刀鞘接触并未由内部手柄轨道自动解决。309/310/311仍缺外部基姿态，保留原正式版本；不覆盖所有动画或旧Skeleton。取消/连接片段和精确原版节奏仍需逐路线校准。按用户最新要求，改用公开研究帧表、原作者教程及UE对照，保留未解码源结构作为辅助，不要求准备原作进程。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Source/IntroCpp/MHWI/MHWIMovesetData.h` | `FMHWIWeaponMotionEvent`、`WeaponMotionEvents`、`WeaponMotions` | 独立武器骨架Sequence和源Montage秒事件，负编号保持 |
| `Source/IntroCpp/MHWI/MHWICharacter.h/.cpp` | `SetSourceWeaponMotion`、`AdvanceSourceWeaponEvents`、`UpdateSourceWeaponPose`、两个getter | SingleNode停播，Actor拥有内部动画时钟；跨帧消费一次，真实秒追赶，73帧保持边界限幅，无额外Timer；清理时回0/1 |
| [native_animation_source.py](../../Scripts/MHWI/native_animation_source.py)、[export_native_animation.py](../../Scripts/MHWI/export_native_animation.py)、[verify_native_animation.py](../../Scripts/MHWI/verify_native_animation.py) | 原生CPU采样、绑定参考皮肤、矩阵/FBX资格 | 只读加载MIT上游，225骨绑定/尺度保留，源和工具SHA256追溯；不修改第三方插件 |
| [native_weapon_export.py](../../Scripts/MHWI/native_weapon_export.py)、[native_weapon_verify.py](../../Scripts/MHWI/native_weapon_verify.py) | EVWP家族/骨架对照、六条FBX | 当前swo001选择wg03_00，内部骨动画与整件挂接分开 |
| [author_native_fidelity.py](../../Scripts/MHWI/author_native_fidelity.py) | 预检/备份、导入、事件制作、逐Montage段迁移 | 先查来源哈希/时长/骨架及变体事件兼容；正式对象显式保存 |
| `/Game/MHWI/Animations/NativeFidelity/{LongSword,Common}/A_<源编号>` | 36个AnimSequence，原hunter Skeleton | 修复后的平行库；基础BlendSpace未迁移，部分Common仅作对照 |
| `/Game/MHWI/Animations/Weapons/A_wg03_00_000..005` | 六条独立武器Sequence，共255帧 | 原LongSword Skeleton；不向刀鞘或猎人骨架错套动画 |
| `/Game/MHWI/Montages/M_*`、`/Game/MHWI/Data/DA_MHWI_LongSword` | 27段引用、6个weapon map条目/19个源事件 | 保留Montage身份/段裁剪/倍率/通知与本轮前玩法数值；准确清单见hunter-promotion.json |
| [qualify_native_assets.py](../../Scripts/MHWI/qualify_native_assets.py)、[export_native_root_reference.py](../../Scripts/MHWI/export_native_root_reference.py)、[pie_native_weapon.py](../../Scripts/MHWI/pie_native_weapon.py) | 源→UE资格和真实PIE事件/生命周期 | 原生根参考、完整骨数量、旋转修复落地、实际输入/武器骨采样；可选10 FPS且恢复原上限 |
| [native_control_evidence.py](../../Scripts/MHWI/native_control_evidence.py)、[native_semantics_evidence.py](../../Scripts/MHWI/native_semantics_evidence.py) | 已有源控制数据复核/证据输出 | 记录未知输入位/LinkMotion与求值参考，不把标签推断写进运行逻辑 |

## 接口、事件与资源影响

新增 [MHWI-006](../Interfaces.md#mhwi独立太刀与预伤害)，不重命名现有反射字段。WeaponMesh运行时切到SingleNode，不需蓝图AnimClass；无配置的旧动作数据可继续工作。源事件先换算到Montage段坐标，独立动画时钟不随猎人变速错误放大；事件80不跨越特殊纳刀73保持帧。整件固定挂点和0.7比例未改。

`/Game/MHWI/Blueprints/BP_MHWI_Hunter`、`BP_MHWI_TrainingGameMode`、`ABP_MHWI_Hunter` 本轮显式编译均0错误/0警告。两个Skeleton与磁盘备份SHA256一致；正式保存后脏包为0，未丢弃用户包。Ninja、原项目主角和默认地图不在本轮迁移范围。

## 实际验证

统一证据根：`Saved/MHWIImport/NativeFidelity-20261024/`。实际构建入口为Source，不是C++ Source。

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| IntroCppEditor Win64 Development，`-WaitMutex -NoHotReloadFromIDE` | 关闭编辑器后UE5.8完整构建 | 首次C2039错误：SetPlaying不属于Mesh；改为SingleNodeInstance后Succeeded，91.54秒；此后二进制未改 | build-native-fidelity.log、build-native-fidelity-repair.log |
| `export_native_animation.py --resume --clips ...` 及FBX重读 | Blender4.5/固定指纹MIT采样器 | 36段通过，3段NeedsParent主动拒绝；源矩阵最大位置误差约0.000306cm，原LMT/blend未变 | ArtSource/ThirdParty/MHWLongSword/NativeFidelity/export-manifest.json；export-used-clips-remainder.log |
| 武器源/FBX对照 | 同上 | 六条/255帧，7骨层级与绑定兼容；骨002往返位置最大误差约0.00000763cm | weapon-family-evidence.json、weapon-fbx-verification.json |
| `qualify_native_assets.run()` | 真实编辑器 | 36段/508项检查通过，UE根轨迹对原生参考最大误差0.00000763cm；129/173压缩旋转修复进入UE；正式32招/6条武器引用有效 | ue-assets-qualification.json、native-root-reference.json |
| `pie_behavior_corrections.run('all')` | 全部27段迁移后的真实PIE/正式DA/Enhanced Input | 02:14:17–02:16:19通过409条断言，含重复采样；覆盖普通/气刃派生、方向、登龙、输入窗口及死亡中断 | Saved/MHWIImport/PIE-behavior-all.json |
| `pie_native_weapon.run(strict_source_hold=False)` | 最终重启后二进制/磁盘资产 | 02:29:51–02:30:11，通过4376条重复逐帧断言；覆盖拔纳刀/居合、事件边界、骨姿态、中断/死亡和过期回调 | weapon-pie-verification.json |
| `pie_native_weapon.run(max_fps=10)` | 实际10 FPS PIE，随后恢复原t.MaxFPS | 02:20:00–02:20:22通过799条断言，73帧保持与过期回调通过；不是799个独立场景 | weapon-pie-10fps.json |
| 关闭干净编辑器并重新启动；再次`qualify_native_assets.run()` | 新PID19420，MCP确认IntroCpp/5.8 | 磁盘读回36段/508检查再次通过，正式33处引用中27组唯一Montage/新Sequence匹配迁移清单；编辑器最终保留在训练地图，PIE结束、脏包0 | ue-assets-qualification.json、最终MCP状态 |
| `pie_training_damage.run('verify')` | 重启后的真实训练地图 | 02:29:09报告通过33项：三个默认被动目标、范围内站立/自身攻击不自伤、目标真实扣血、临时主动攻击和见切拦截 | Saved/MHWIImport/PIE-training-damage-verify.json |
| 文档、Python语法、diff | 本工作区 | `check_docs.py`通过64 Markdown/461链接/12模块；11个新增Python的AST检查通过；26个本轮文本文件含未跟踪文件的no-index空白检查通过；禁用本次调用LFS过滤器的`git diff --check`通过 | 命令输出；NativeFidelity-final-validation.json |

首次重启用沙箱子进程启动未能保留进程，没有新UE崩溃日志；按已授权的编辑器验证范围在正常桌面权限重新启动，MCP确认新PID和项目身份后继续。未结束其他项目或丢弃未保存包。

测试修正：首次武器夹具将blend-out期间GetCurrentActiveMontage=None误读成进度倒退，已改为保留最后已见进度，原失败报告保留；源根资格最初错误要求新旧中间轨迹接近，后发现旧插值本就是缺陷，改为原生参考+旧起止兼容，并按引擎FBX坐标约定反转Y。该调整没有改资产来迎合测试。批转换曾请求不存在的175槽导致中断，移除无效请求并续跑剩余项，未吞掉解码错误。

## 风险、遗留与回退

- R-ANIM-007：内部轨道已落地，整刀/刀鞘装配交接尚未完成；EVWP收纳缩放0不能未经验证直接解释为隐藏。
- R-ANIM-008：LinkMotion的完整调度和主段接入帧仍缺证据。
- R-ANIM-009：309/310/311外部基姿态、基础移动迁移未完成；本轮只修36段，未声明全库正确。
- R-COMBAT-009：公开表支持独立无敌/反击窗及资源规则校准，但尚未写入；逐路由取消表并不在这些资料内。速度保持线性，旧QUAD标签不足以改平方；也不能用float插值代码推断transition5位域。

回退按 `Backup/Content/...` 恢复本轮指定DA/Montage，不恢复整个Content。代码基线在 `Backup/CodeBaseline/`：因为开始编辑前未直接复制，这三份按本轮增量反向重建，并与此前Behavior-final-validation.json中的SHA256逐一吻合后保存；可验证，不伪称事前快照。先恢复引用和源码，再编译、确认新增平行Sequence无引用后移除。原素材、旧Sequence和第三方代码未覆盖。

## 已同步文档

[当前系统](../Systems/MHWI-LongSword.md)、[接口](../Interfaces.md)、[模块索引](../Reference/modules.json)、[已知问题](../Known-Issues.md)、[实施/公开资料说明](../Reference/MHWI-Native-Fidelity-Implementation.md)、[方案索引](../Plans/README.md)、[记录索引](README.md)、[入口](../README.md)、[工具说明](../../Tools/MHW/README.md)、[素材说明](../../ArtSource/ThirdParty/MHWLongSword/README.md)。
