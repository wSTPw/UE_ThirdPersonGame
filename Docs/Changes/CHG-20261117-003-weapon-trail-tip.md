# CHG-20261117-003：刀光第二版（收至刀尖 + 淡红自发光）与版本切换

- 状态：completed
- 日期：2026-11-17
- 需求摘要：在保留第一版整刀刀光的前提下，新增"只有刀尖划过"的刀光并带轻微红色自发光，两种效果可顺畅切换
- 关联 PLAN / ADR / 问题 / 接口 ID：[CHG-20261117-002](CHG-20261117-002-weapon-trail-damage-numbers.md)、MHWI-017
- Git：工作区变更，未提交

## 原因与结果

第一版刀光覆盖整条刀刃（宽白弧）。本版把"外观"从组件里抽成可切换的两份 `FMHWIWeaponTrailLook`：

- `FullBlade`（第一版，现为备用）：`BandStart 0.35 / BandEnd 1`、冷白 `(0.86,0.94,1.0)`、强度 0.55、寿命 0.08 秒、`bSoftBothEdges`。首版权威值是 0→1 / 1.4 / 0.15（见 CHG-002），实测在低采样帧数下叠成不透明白帆，见下。
- `TipOnly`（本版新增）：`BandStart 0.97 / BandEnd 1`，只取刀尖约 4 cm（实测刀身 142–150 cm 的报告值见 CHG-002）、淡红 `(1.0,0.34,0.30)`、强度 1.8、寿命 0.26 秒、`bSoftBothEdges=true`（两侧渐隐成一条发光细线）。加法混合下这条色带即"轻微红色自发光"，不改材质、不加光源，也不改刀身材质。

三轮修订（都来自用户实机反馈，保留在此便于追溯）：

1. 首轮刀尖带 0.85→1（≈22 cm）、单边渐隐、寿命 0.13 秒 → 用户判断**太粗**，像宽带而不是"只有刀尖划过"。
2. 改为 0.97→1（≈4 cm）+ `bSoftBothEdges` + 寿命 0.26 秒 → 细线成立；但默认外观仍是 `FullBlade`，用户实机看到的还是第一版的宽带。
3. 把默认 `Style` 切到 `TipOnly`，并把 `FullBlade` 从 0→1 / 1.4 / 0.15 收敛到 0.35→1 / 0.55 / 0.08 + 柔边——原参数在低采样帧数下会叠成一张不透明白帆（用户截图即为该状态）。

参数都在组件 `TipOnly` / `FullBlade` 上，可在 Details 继续调，不需要重编。

切换是**先清样本再换外观**：旧样本描述的是另一条色带，若直接沿用会在挥砍中途把整刀带子瞬间压到刀尖（视觉跳变）。`SetStyle` 先 `ClearTrail()` 再切，下一次采样从干净状态重建，因此中途切换只丢一瞬尾迹，不会出现半截错带。

尾迹收缩也改为在**带内**收敛：`Start = Lerp(BandStart, BandEnd, (1-Age)*0.35)`。整刀版仍是"尾部向刀尖收"，刀尖版不会把带子重新拉回刀根。

## 修改清单

| 文件/资产完整路径 | 类/符号或关键属性 | 修改原因与效果 |
| --- | --- | --- |
| `Source/IntroCpp/MHWI/MHWIWeaponTrailComponent.h` | 新增 `EMHWIWeaponTrailStyle`、`FMHWIWeaponTrailLook`（含 `bSoftBothEdges`）；`Style`、`FullBlade`、`TipOnly`、`SetStyle`、`GetStyle` | 外观与几何带成为数据；原 `Color/Intensity/Lifetime` 三个散字段并入 look |
| `Source/IntroCpp/MHWI/MHWIWeaponTrailComponent.cpp` | `Rebuild` 按 `ActiveLook()` 取带范围/颜色/强度/寿命；`Start` 在带内收敛 | 两种外观共用同一套采样、三角面与材质 |
| `Source/IntroCpp/MHWI/MHWICharacter.h/.cpp` | `SetWeaponTrailStyle`、`GetWeaponTrailStyle`、`MHWITrailStyle(int32)`（Exec） | 蓝图可切；PIE 中控制台 `MHWITrailStyle 0|1` 现场对比 |
| `Source/IntroCpp/MHWIUI/MHWIHUD.cpp` | 左上状态面板新增 `TRAIL FULL/TIP`，`SLINGER` 右移 | 切换结果可直接在画面确认 |
| `Scripts/MHWI/pie_trail_damage_numbers.py` | 增加 TipOnly 一轮：切换清样本 → 再挥砍 → 采样/扣血/数字 | 两版都跑真实 PIE，不只验一版 |

## 接口、事件与资源影响

- `UMHWIWeaponTrailComponent` 移除 `Color/Intensity/Lifetime` 三个 UPROPERTY，改为 `FullBlade/TipOnly` 两份 look + `Style`。这两个资产级字段只被本组件与 PIE 脚本读取，未在任何蓝图里手工设值；组件由 `AMHWICharacter` 构造，`BP_MHWI_Hunter` 不需要改。
- 新增 `SetWeaponTrailStyle/GetWeaponTrailStyle/MHWITrailStyle`，只影响表现层；`MHWITrailStyle` 是 Exec，仅控制台可用，不占用输入映射。
- 材质与命中数字没有改动。

## 实际验证

| 检查/命令 | 环境 | 实际结果 | 证据路径 |
| --- | --- | --- | --- |
| `Build.bat IntroCppEditor Win64 Development` | UE 5.8，编辑器关闭 | Succeeded | 本记录 |
| `Build.bat IntroCpp Win64 Development` | 同上 | Succeeded（Game 目标，用于区分"源码问题"与"编辑器目标中间产物问题"） | 本记录 |
| `node Scripts/MHWI/run_presentation_pie.mjs` | `L_MHWI_Training`，PIE，时间膨胀 0.05 | **19/19 全 PASS**，含：初始为 FullBlade、整刀版采样/扣血/数字/过期、切换后样本清零、TipOnly 挥砍采样/扣血/数字、整轮切换后外观保持 TipOnly | `Saved/MHWIPresentation/PIE-presentation.json` |
| 截图 `MHWI_04_tip_trail` | 同上 | 收成一条贴刀尖的细线、两侧渐隐、偏红白；HUD 显示 `TRAIL TIP`；接触点出现橙色数字 | `Saved/Screenshots/WindowsEditor/`（不入库） |

**构建故障排查（记录一条真实踩坑）**：本轮第一次全量编译时所有 TU 都以 `error code 1` 失败且**无任何编译器诊断**（`-NoUBA` 同样静默），但把单文件用同一份 `.rsp` 手工跑 `cl.exe` 却能通过，Game 目标也能通过。根因是 `Intermediate/Build/Win64/x64/UnrealEditor/Development/IntroCpp/` 里的中间产物陈旧（含旧 `LiveCodingInfo.json`/rsp 状态被反复复用），整目录改名后重建即 Succeeded。以后遇到"全部 TU 瞬间失败且无诊断"，先清该模块中间目录，不要先怀疑源码。

未执行：60 FPS 常规帧率观感验收（同 CHG-002，后台编辑器只有 2–3 FPS，靠时间膨胀采样）。

## 风险、遗留与回退

- 红色是项目选定的外观预设，不是从原作 `wp03_*.efx` 取证的颜色；原作 EFX 轨仍未取证，切换只是"两版并存的工程对比"，不宣称哪一版等于原作。
- 两版共用命中窗口，切换不改变触发时机；若把 `TipOnly.BandStart` 调到 1.0，带宽会退化为 0（不可见），改参时注意。
- 回退：`git` 回退本记录涉及的 5 个文件即可；`Style` 默认 `FullBlade`，回到第一版不需要改资产。

## 已同步文档

[太刀系统](../Systems/MHWI-LongSword.md)、[接口 MHWI-017](../Interfaces.md)、[开发流程](../Development.md)、[变更索引](README.md)。
