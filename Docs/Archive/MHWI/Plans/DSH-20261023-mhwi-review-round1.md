# Codex 独立审查 / 第一轮返修

2026-10-23，针对父会话 `session-e3dd6ab0-ccf0-45c3-bc57-21cdb1f6a567` 的初版。以下是明确证据和所需修复，尚未通过。优先由原A/B/C作者修改，父代理只协调。部分项目已被父代理同时发现并修正，核对最新版本即可，不必重复改回。

**执行来源说明**：`blender-link-audit.log`、`blender-link-direct.log`、`blender-link-wide.log`、`blender-root-link.log`、`root-link-readonly.json` 均由本轮Codex宿主执行产生，不是B代理突破沙箱执行。B报告“本代理未运行Blender”并没有造假，应追加“Codex独立验证结果”并引用日志。正在运行的完整构建同样由Codex执行；不要尝试修复DSH的Windows权限。构建日志为 `Saved/MHWIImport/Build-behavior-20261023-first.log`。

## A：下劈阶段、实例身份与低帧转向

1. **HelmStrikeStartTime用错动画。** 当前MaybeCommitHelmStrike等待HelmAir的CurrentPosition达到25/60，随后StartResolvedMove(SpiritHelmBreaker)在该片段0秒立即Velocity.Z=-HelmStrikeSpeed。25源帧是173的下劈举刀/碰撞入口，不是172的等待点。应在Air收到有效请求后进入Strike；保留自然物理轨迹、播放173的起手，再在**173自身Montage位置**达到HelmStrikeStartTime时一次提交快降和伤害/降色授权。太早撞地则无有效下劈七段。无输入Air自然落地仍不扣刃/不七段。不能只把等待加到Air掩盖Strike从0秒砸地。
2. **Tick不能跨派生继续使用旧FAnimMontageInstance指针。** 当前Instance在AdvanceAction/MaybeCommitHelmStrike后仍用于GetInstanceID，而上述函数可停止旧Montage并创建新实例。每个会切换动作的调用后核对ExecutionSerial/实例ID，切换即返回或重新取得当前实例；禁止解引用之前缓存的Instance。
3. **转向窗口跨帧。** ApplyTurnWindows只检查当前Position是否在窗口内，低帧从0跳到0.2会完全跳过0..0.12窗口。像取消窗口一样使用前后Montage区间交集，并按真实重叠时长限制转速/总偏角。补一个跨完整早期窗口的非镜像测试或明确运行验收。
4. 检查纳刀Roll窗口内Light：只有RequireDrawn路由时ResolveInput失败，FinishMove会清PendingInput，输入可能被吞。B可给Roll额外低优先级Light→DrawSlash回退，或A明确处理纳刀Roll。必须实际覆盖在Roll仍活跃时按LMB，不仅等中立再按。

## B：已执行的命令与错误

1. Codex运行 `Blender -b --python Scripts/MHWI/audit_behavior_links.py`，Blender进程退出0但脚本实际抛错，不能按进程退出码判成功。日志：`Saved/MHWIImport/DSH-20261022/blender-link-audit.log`。`mapping_check`约155行的events元素是track字典，应读取其frames，不应直接解包字典键。
2. **129结束帧/时长有一帧错误。** source_frame_count=30，实际样本帧0..29；按真实A_w03_00_129.get_play_length校准，不能写0..30=0.5秒。MCP尚未启动，精确时长稍后由Codex读回；预期29/60。统一纯计算/段JSON/默认制作/定向run/映射project_adapters所有引用，禁止用0.02容差掩盖一帧偏差。
3. **101入口37太早。** Codex已调用你写的bpy_candidates做只读实查，扩大候选到25..54：101第48帧与129末端的4个骨头头部平均误差仅0.5424cm，最大0.7904cm；45帧均差8.742cm，37更大。证据 `blender-link-wide.log`，范围受限时 `blender-link-direct.log`。建议入口48，保留55..66碰撞仍有7帧前摇。修复audit：逐动作重置骨基底、完整25..54搜索，同时记录129末端和101入口/末端根位置，实际残余前冲；用测得入口48重算段与窗口，不能继续用暂定37。
4. **run报告的UnrealMap不能直接JSON序列化。** `report['moves'][name]['play_rates']=definition.get_editor_property('source_play_rates')` 应先转普通dict及float，其他Name/Map/Struct同样序列化。当前json.dumps位于保存DA之后，可能保存成功后抛错，给出误导状态。
5. 扩展B文件所有权：允许修改 `Scripts/MHWI/extract_moveset_mapping.py` 的原始definitions（SpiritThrust170/node45；Foresight140/node28）。不得重新运行整体生成器覆盖用户已修106/107、203/090等标签；只改生成定义并静态核对即可，防止下次再制作回退。
6. 插入RMB循环语义：普通Thrust↔Rising已有；插入身份若按RMB也应回到相应普通链而不是吞输入，同时R续段资格仅留在插入身份内。至少SpiritComboThrust的RMB→RisingSlash、SpiritComboRisingSlash的RMB→Thrust，R仍各到II/III。回退不足槽是否与当前规则一致明确记录。

## C：实际输入验证不能丢移动输入

1. 当前dir_case_press在_press('fade')后立刻_stop_inputs()，下一次EnhancedInput处理时MoveCompleted可能先把MoveInput清0，从而全部走默认后退。保持移动注入，直到实际观察到Fade启动后再释放。
2. dir_case_start在中立先移动0.1秒，CharacterMovement会自动朝移动方向转身；固定expected表却假设角色仍Yaw0。例如相机0/S会让角色先转54度，对角色右轴投影就不再是后退。夹具应在触发前明确固定/恢复参考角色朝向，并记录当帧camera/world意图/actor基底；或从实际选择时基底独立计算期望。不要为测试改业务逻辑来匹配过时基底。保留真实输入与实际位移断言。
3. 覆盖A修正后的Strike时间：进入SpiritHelmBreaker后尚未到25源帧时不能已是-3000快降；跨25源帧才一次提交。无输入、太早接地/打断无免费七段/降色。纳刀Roll在活跃恢复窗口LMB应DrawSlash。保留正式成本。

## 必要的控制提示（扩展一个文件所有权）

A额外可修改 `Source/IntroCpp/MHWIUI/MHWIHUD.cpp` **仅Controls文字**：RMB现在是突刺/上挑循环；C为镜头相对方向；G命中起跳后空中LMB/RMB/R/G下劈，必须让玩家知道新的二次输入。不得改HUD布局/血条或其他UI业务。

## 命令执行与报告

Codex已对当前4个Python做AST语法检查，通过；这不等于UEAPI或运行通过。DSH pwsh仍不可用时不要修系统权限，也不要反复重试，继续直接文件工具。父/子报告记录本轮修复与未执行项；Codex之后完整构建、实际制作和PIE。
