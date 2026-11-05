# CHG-20261022-004：MHWI 动画与普通攻击派生修正

- 状态：completed，已保存并完成针对性 PIE 与磁盘重载核对
- 日期：2026-10-22
- 需求摘要：修正纳刀走路、气刃第二段姿势、左键连续攻击第二段。
- 关联问题 / 接口：R-ANIM-004；MHWI-001、MHWI-005
- Git：工作区变更，未提交

## 原因与结果

纳刀步行原引用 co00_00_034，其源根轨迹垂直向上约 171.58 cm，实际为攀爬循环；035 是向下攀爬，037 明显压低身体，也不适合作为当前地面跑步。现在使用站立前行循环 203/090，保留位移速度 180/420 cm/s，以 RateScale 匹配源步频。

用户明确“重击第二段”指连续左键的第二段。原 DrawSlash/StepSlash 的 Light 出口直接接 Thrust，与源 FSM 的踏込斬り → 縦斬り不符；现接 OverheadSlash，之后接突刺、上挑、纵斩循环。

用户对照进一步指出气刃 II 与 Rising Slash 互换。源姿态审计排除了缺轨、FBX 残留姿态和参考骨基底；107 原始动作本来就是单手抬刀。现气刃 II 使用 106，上挑使用 107，重算对应命中窗口与取消入口。原表为推断标签，本次采用用户识别与 UE 实际姿态对照修正，没有全局改写第三方解析器。

## 修改清单

| 文件/资产完整路径 | 关键变化 |
| --- | --- |
| `/Game/MHWI/Montages/M_SpiritII` | 段改为 `/Game/MHWI/Animations/LongSword/A_w03_00_106`，总长 2.0 秒 |
| `/Game/MHWI/Montages/M_RisingSlash` | 段改为 `/Game/MHWI/Animations/LongSword/A_w03_00_107`，总长 2.266667 秒 |
| `/Game/MHWI/Data/DA_MHWI_LongSword`，父类 `UMHWIMovesetData` | II 窗口 33–41 帧，上挑 22–29 帧；Light 出口、纳刀走跑引用同步修正；气刃 II 正式消耗保持 12 |
| `/Game/MHWI/Animations/BS_MHWI_Sheathed` | 180/420 两样本改为 203/090，0 速样本仍 001；保留平滑参数 |
| `/Game/MHWI/Animations/Common/A_co00_00_203`、`A_co00_00_090` | 新增正式走跑序列，原猎人 Skeleton；锁根 REF_POSE，RateScale 1.332921/1.149071 |
| `/Game/MHWI/Animations/Common/A_co00_00_039`、`A_co00_00_089` | 新增保留的姿态对照资源，未接玩法；034/035/037 原资源保留 |
| `/Game/MHWI/Blueprints/ABP_MHWI_Hunter`，父类 `UMHWIAnimInstance` | 重新编译保存；图结构未改变 |
| `Scripts/MHWI/author_assets.py` | 更新再制作默认映射/路由/速度；增加局部 `animation_corrections()`，保留其他动作调校 |
| `Scripts/MHWI/moveset_mapping.json`、`extract_moveset_mapping.py` | 修正片段标签与源事件归属，记录被排除的攀爬/低姿态循环和源速度 |
| `Scripts/MHWI/export_common.py` | 默认导出四条正式 Common；支持 `--` 指定增量片段 |
| `Scripts/MHWI/pie_animation_corrections.py`、`read_correction_data.py` | 新增真实输入/姿态/伤害回归与磁盘重载核对 |
| `Scripts/MHWI/animation_pose_preview.py`、`audit_source_tracks.py`、`review_animation_assets.py` | 源轨道/UE 姿态调查与固定帧预览；临时动作参数先复制 Map，禁止零成本值污染原资产 |

## 接口、事件与资源影响

仅修改 MHWI 独立模组资产、再制作与检查脚本。没有修改 `Source/` C++、原 Ninja、默认地图或武器挂接参数。保留用户原有未提交改动。没有反射签名变更；命中时间仍为 Montage 秒，缓冲返回语义不变。攻击继续使用根运动；地面走跑继续使用 CharacterMovement 与锁根序列。

MCP `animation.set_montage_sequence` 显式更新既有 Montage 段与长度，`animation.set_blend_sample` 更新纳刀 BS 第 1/2 项，然后运行 `author_assets.animation_corrections()` 保存对应数据；未全量重建其他动作或地图。

## 实际验证

| 检查/命令 | 实际结果 | 证据 |
| --- | --- | --- |
| 原 LMT/Blender 与 FBX 只读姿态审计 | 107 双臂旋转轨道齐全；原 blend 与重新导入 FBX 的 42 个骨位置最大差约 0.000056 cm。源 034/035 为垂直运动 | `Saved/MHWIImport/source-track-audit.json`、`spirit-source-audit.json`、`spirit-fbx-audit.json` |
| `export_common.py -- co00_00_089 co00_00_090 co00_00_203 co00_00_039`，本机 portable Blender | 四条 FBX 导出并导入原猎人 Skeleton；比较后选 203/090 正式接入 | `Saved/MHWIImport/export-gaits.log`、`import-state.json` |
| `editor.run_python_file` → `pie_animation_corrections.py`，UE 5.8 真 PIE | **39 项通过**。真实 Enhanced Input 走路 194.06 cm / 180 cm/s，奔跑 445.96 cm / 420 cm/s；站立头高/非攀爬手势、背负挂点通过；六次左键共 124 伤害、54 槽；气刃完整链共 132 伤害、槽 42→30→18→6，回旋升白刃并纳刀；随后输入和打断正常 | `Saved/MHWIImport/PIE-animation-corrections.json` |
| 同次 PIE 比较运行头/双腕与实际源 Sequence | RisingSlash → 107，SpiritII → 106；三骨最大位置差约 **0.0037 cm**，证明实际出姿态而非仅交换名称 | 同上 `poses` |
| 修正后固定帧视觉检查 | 气刃 II 双手挥斩与上挑单手抬刀已区分；这是姿态检查用临时零消耗夹具，不计入正式战斗回归 | `spiritII-corrected-f37.png`、`rising-corrected-f24.png`，位于 `Saved/MHWIImport` |
| `read_correction_data.reload_and_verify()`，结束 PIE 后仅重载干净的 8 个受影响包 | **12 项通过**；正式消耗 12、Montage 时长、Light 路由、走跑引用、倍率及 REF_POSE 锁根均从磁盘重载后保留 | `Saved/MHWIImport/animation-persistence.json` |
| 重载后 MCP `list_montage_segments` / `read_blendspace` | 核对 106/107 实际段、203/090 实际样本；最终内容/关卡无脏包 | MCP 返回及最终编辑器状态 |
| `python Scripts/Docs/check_docs.py` | PASS：46 个 Markdown、334 个本地链接、12 个模块及编辑器快照 JSON | 本轮控制台输出 |
| Python AST + JSON 映射断言；`git diff --check -- Docs Scripts/MHWI Tools/MHW/README.md` | 8 个受影响 Python 脚本语法与 106/107 映射断言通过；文本 diff 检查退出 0 | 本轮控制台输出 |

首次针对性 PIE 的动作/伤害/姿态检查通过，但发现预览脚本通过 Unreal Map 活视图将 SpiritII 临时消耗 0 留入内存，导致槽断言失败。已改为复制 Map 的所有结构体条目并恢复正式消耗 12，随后完整重跑得到上述 39 项通过；安全预览后再重载磁盘，确认无残留。失败原证据保留为 `PIE-animation-corrections-first-run.json`，没有将其当作通过。

本轮未重新编译 C++（未改 C++/反射），未重跑历史全部 73 项居合/登龙/死亡测试；既往战斗与 45 项挂接验证仅为历史引用。未逐条人工校准全部 164 条太刀动作。

## 风险、遗留与回退

修正范围为用户列出的三类问题；其他源片段的语义仍含推断，不声称全部等同原版精确动画混合与取消帧。地形适配、双手 IK、完整原游戏 shader/特效等原有边界不变。

变更前四个受影响既有资源的定向备份位于 `Saved/MHWIImport/Backup-CHG004`，包含 DataAsset、纳刀 BlendSpace、两个 Montage，保留相对路径。回退时先停止编辑器使用这些包，按路径恢复，并同步恢复脚本/JSON 的旧映射与路由；不要全仓库重置以覆盖用户其他改动。新增 203/090/039/089 和源 FBX 可保留为资源库；删除前先解除引用。

## 已同步文档

[模组现状](../Systems/MHWI-LongSword.md)、[接口](../Interfaces.md)、[模块索引](../Reference/modules.json)、[已知问题](../Known-Issues.md)、[记录索引](README.md)、[素材工具](../../Tools/MHW/README.md)。
