# CHG-20261104-002：Approx 层编译修复（五项修复批次从未编译成功）

- 日期：2026-11-04。
- 起因：写 AI 交接文档时核对构建产物时间戳，发现 `MHWIRathianApproxPawn.cpp`（2026-11-02 21:18）**晚于**最后一次成功构建的 DLL（19:49），而 21:21 的构建日志为 `Result: Failed`——即 2026-11-02 那批"五项体验修复"**从未通过编译**，此前无任何记录。
- 关联：[AI 交接文档](../Archive/MHWI/Plans/MHWI-Rathian-AI-Handoff-20261104.md) §4.2/§4.4、[B1 方案](../Archive/MHWI/Plans/PLAN-20261102-002-rathian-approximate-profile.md)、[CHG-20261102-004](../Archive/MHWI/Changes/CHG-20261102-004-rathian-approx-implementation.md)（原批次记录，其"构建通过"结论仅对 19:49 那一版成立，不覆盖 21:18 的五项修复）。

## 修改文件

| 文件 | 改动 |
| --- | --- |
| `Source/IntroCpp/MHWI/Monsters/Approx/MHWIRathianApproxPawn.h` | ① `#include "MHWIContactResponse.h"` → `"MHWI/MHWIContactResponse.h"`；② 补 `bool bGroundBlockedLogged = false;`；③ `RuntimeMontages` 补 `UPROPERTY(Transient)` |
| `Source/IntroCpp/MHWI/Monsters/Approx/MHWIRathianApproxPawn.cpp` | ① `GetOrBuildMontage` 改走 `UAnimMontage::CreateSlotAnimationAsDynamicMontage` 静态工厂（原手工填 `FAnimSegment` 不可行）；② 攻击启动由 `Body->PlayAnimMontage` 改为 `Body->SetAnimation(Montage)`；③ `Montage_GetIsPlaying` → `Montage_IsPlaying`（2 处）；④ 攻击日志字段 `play=` 改为 `blendIn=` |

## 错误与修法（UE 5.8 实际报错）

| 错误 | 原因 | 修法 |
| --- | --- | --- |
| `C1083` 无法打开 `MHWIContactResponse.h` | Approx 子目录不在包含搜索路径 | 模块根相对写法（`Build.cs` 的 `PublicIncludePaths` 含 `"IntroCpp"`） |
| `C2039` `PlayAnimMontage` 不是 `USkeletalMeshComponent` 成员 | 5.8 移除组件级播放方法 | SingleNode 模式 `SetAnimation(Montage)`；`UAnimSingleNodeInstance::SetAnimation` 内部注册槽位并 `RestartMontage`（`AnimSingleNodeInstance.cpp`） |
| `C2248` `FAnimSegment::AnimReference` protected / `C2039` `EndPos`、`PlayingRate` 不存在 | 手工拼 Montage 段落在 5.8 不可行 | `UAnimMontage::CreateSlotAnimationAsDynamicMontage(Seq, TEXT("DefaultSlot"), 0.15f, 0.15f, 1.f, 1, 0.15f)`（`AnimMontage.h:978`） |
| `C2039` `Montage_GetIsPlaying` 不是 `UAnimInstance` 成员 | 5.8 改名 | `Montage_IsPlaying`（`AnimInstance.h:692`）；`Montage_GetPosition:`700、`Montage_Stop:`639 未变 |
| `C2065` `bGroundBlockedLogged` 未声明 | 漏成员声明 | 头文件补成员 |

## 验证（实际执行）

```powershell
& 'E:/UE/UE_5.8/Engine/Build/BatchFiles/Build.bat' IntroCppEditor Win64 Development `
  '-Project=E:/Unreal Projects/IntorCpp/IntroCpp.uproject' -WaitMutex -NoHotReloadFromIDE -NoUBA
```

- 修复前：`Result: Failed (OtherCompilationError)`，7 条 error，均在上表。
- 修复后：**`Result: Succeeded`，Total execution time 57.12s**（日志 `Saved/MHWI-Rathian-FirstChain/build-handoff-20261104.log`）。
- 构建必须带 `-NoUBA`：本机 UBA 存储服务写损坏，不带该参数会出 LNK1201/LNK1136 且日志可能无诊断输出。

## 未验证项

- **PIE 未执行**：咬击是否真按动态 Montage 播放、BlendIn/Out 观感、贴地/转向/受击表现是否达预期，全部待用户 PIE 实测。
- 运行时动态 Montage 在 SingleNode 模式下的表现依据是引擎源码路径（`SetAnimation`→`RestartMontage`→`Montage_Play`），**属静态推断，未运行验证**。若 PIE 中攻击播不出来，`TickAttack` 会因 `Montage_IsPlaying==false` 立即 `FinishMove` 回到 Idle（优雅降级，不卡死），此时应改用 SingleNode 直接播 Sequence。
- 受击等级固定 `Medium` 仍是工程近似（EM_DMG 未解，E06）。

## 回退

回退两文件到 2026-11-02 21:18 版本即恢复"未编译"状态——不建议。若只需回退动画播放方式：把 `Body->SetAnimation(Montage)` 换回 `Body->SetAnimation(Sequence)`（保留其余修复），即可绕过动态 Montage，硬切播放。
