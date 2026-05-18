# 近战多段连击系统 — 设计与实施文档

> 创建时间: 2026-05-12  
> 最后更新: 2026-05-14（方案 B 修正版）  
> 状态: **已定稿，待实施**

---

## 1. 概述

### 目标

为玩家角色实现数据驱动的近战多段连击系统（Combo System），支持：

- **N 段连续攻击**（每段独立伤害/判定/击退/窗口参数）
- **单段内多次判定**（SubHits 子判定数组，如双刀乱舞、长枪连刺）
- **输入缓冲**（窗口期内提前按下不丢失）
- **单 Montage + Section 跳转**模式（一把武器只需 1 个 Montage 资产）
- **连击超时自动重置**
- **可选末段循环**回第 1 段

### 当前项目基础（已有）

| 组件 | 文件 | 状态 |
|------|------|------|
| 武器数据资产 | `WeaponData.h` | ✅ 完整，需扩展 `MeleeComboData` 字段 |
| 动画类型枚举 | `EWeaponTypes.h` (`EWeaponAnimType`) | ✅ 已定义 |
| 敌人近战伤害实现 | `EnemyBase::ExecuteMeleeDamage()` | ✅ SphereTrace + ApplyDamage |
| 敌人 AnimNotify 模式 | `AnimNotify_EnemyAttack.h/.cpp` | ✅ 帧级触发模板 |
| 属性/伤害统一接口 | `AttributeComponent::ApplyDamage()` | ✅ 所有伤害入口 |
| 物品使用 AnimNotify | `AnimNotify_UseItemComplete.h/.cpp` | ✅ Notify→回调模式模板 |
| 玩家攻击入口 | `MyPlayerCharacter::Attack()` | ✅ 远程完成，近战分支待改造 |
| 装备/快捷栏切换 | `MyPlayerCharacter::EquipWeapon()` 等 | ✅ Minecraft 式完整实现 |

---

## 2. 架构设计

### 2.1 数据驱动结构（方案 B 核心）

```
UWeaponData (现有，需加 1 个字段)
├── bIsRangedWeapon = false        ← ★ 用这个判断是否走连击（不加 bIsMeleeWeapon）
├── WeaponAnimType = Slash_1H      ← 兼容 AttackMontageMap fallback
└── MeleeComboData ──→ UComboAttackData (新建 PrimaryDataAsset)
     ├── ComboMontage              ← ★ 单个 Montage（内含多个 Section）
     ├── Hits (TArray<FComboHitEntry>)  ← 每段攻击的完整配置
     ├── bLoopFromLastHit          ← 是否循环
     └── ComboResetTime            ← 全局超时
```

**动画挂载方式 — 单 Montage + Section**：

```
M_Combo_Slash_1H (一个 Montage 资产):
┌─── Section: "Hit1" ──────────────────────┐
│ [====预备====][★挥砍判定][~~收招~~]      │   0.0 ~ 0.50s
│         ↑ AnimNotify_MeleeHit @ 0.20s    │
└──────────────────────────────────────────┘
┌─── Section: "Hit2" ──────────────────────┐
│ [==上挑==][★顶点===][~~落地~~]           │   0.50 ~ 1.00s
│          ↑ AnimNotify_MeleeHit @ 0.72s   │
└──────────────────────────────────────────┘
┌─── Section: "Hit3" ──────────────────────┐
│ [下劈预备][=====下劈====][★触地]         │   1.00 ~ 1.60s
│                     ↑ AnimNotify_MeleeHit │
└──────────────────────────────────────────┘

播放代码: PlayAnimMontage(ComboMontage, 1.0f, SectionName)
```

**兼容性**：此 ComboMontage 可同时注册到角色的 `AttackMontageMap[Slash_1H]` 中作为默认单次攻击 fallback。

---

### 2.2 UComboAttackData（新建 PrimaryDataAsset）

```cpp
/**
 * 连击配置数据资产
 *
 * 定义一套完整的近战连击序列参数。
 * 一把近战武器引用一个 ComboAttackData，
 * 多把同类武器可共享同一套连击配置。
 */
UCLASS()
class INTROCPP_API UComboAttackData : public UPrimaryDataAsset
{
    GENERATED_BODY()

public:
    // ====== 基本信息 ======

    /** 连招名称（如"基础剑技三连"、"双刀乱舞五段"），用于日志和 UI 显示 */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combo")
    FText ComboName;

    /** 对应的武器动画类型，用于识别和 fallback 匹配 */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combo")
    EWeaponAnimType WeaponAnimType;

    // ====== 动画资源 ======

    /**
     * 整套连击序列的 Montage 资产（★ 核心字段）
     * 
     * 内含多个 Section（Hit1 / Hit2 / ...），每段对应一次攻击动作。
     * 通过 Hits[].SectionName 指定播放哪一段。
     * 
     * 设计意图：
     * - 整套连击只需 1 个 Montage 文件，编辑管理方便
     * - 可同时挂到 AttackMontageMap[WeaponAnimType] 作为非连击场景的默认动画
     */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combo|Animation")
    UAnimMontage* ComboMontage;

    // ====== 连击序列 ======

    /**
     * 各段攻击配置列表
     * 数组长度 = 连击段数（如填 3 个元素就是三连击）
     * 索引 0 = 第 1 段，索引 1 = 第 2 段，以此类推
     */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combo|Hits")
    TArray<FComboHitEntry> Hits;

    // ====== 全局行为 ======

    /**
     * 最后一段打完后是否循环回到第 1 段
     * true  → 无限连击循环（适合快速轻武器）
     * false → 打完最后一段后结束，回到 Idle
     */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combo|Behavior")
    bool bLoopFromLastHit = false;

    /**
     * 连击超时时间（秒）
     * 从每次按键开始计时，超时未按下 → 强制 ResetCombo 回到 Idle
     * 建议值：1.0 ~ 1.5 秒
     */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combo|Behavior")
    float ComboResetTime = 1.0f;
};
```

---

### 2.3 FComboHitEntry（单段攻击配置）

```cpp
/**
 * 单段攻击的完整参数包
 *
 * 每个 FComboHitEntry 代表连击序列中的一次攻击动作，
 * 包含动画定位、伤害数值、判定范围、输入窗口等全部信息。
 * 
 * 特殊情况：如果 SubHits 非空，则这段攻击内有多次独立判定（如双刀乱舞、长枪连刺）。
 * SubHits 为空时退化为标准单次判定模式。
 */
USTRUCT()
struct FComboHitEntry
{
    GENERATED_BODY()

    // ====== 动画定位 ======

    /** 在 ComboMontage 中对应的 Section 名称（如 "Hit1", "Hit2", "Hit3"）*/
    UPROPERTY(EditAnywhere, Category = "Animation")
    FName SectionName = TEXT("Hit1");

    // ====== 伤害数值 ======

    /** 基础伤害值（最终伤害 = BaseDamage × DamageMultiplier × 属性加成）*/
    UPROPERTY(EditAnywhere, Category = "Damage")
    float BaseDamage = 20.f;

    /** 伤害倍率（后段递增用，Hit1=1.0x, Hit2=1.3x, Hit3=1.8x 等）*/
    UPROPERTY(EditAnywhere, Category = "Damage")
    float DamageMultiplier = 1.0f;

    // ====== 判定参数 ======

    /** SphereTrace 检测半径（cm），值越大判定范围越宽 */
    UPROPERTY(EditAnywhere, Category = "Detection")
    float AttackSphereRadius = 50.f;

    /**
     * 判定点向前偏移距离（cm）
     * 从角色位置沿 ForwardVector 偏移此距离作为 SphereTrace 的终点
     * 值越大判定越靠前（长武器应设大一些）
     */
    UPROPERTY(EditAnywhere, Category = "Detection")
    float AttackForwardOffset = 50.f;

    // ====== 击退效果 ======

    /** 击退力度（LaunchCharacter 的速度参数）*/
    UPROPERTY(EditAnywhere, Category = "Impact")
    float KnockbackForce = 500.f;

    // ====== 输入窗口 ======

    /**
     * 窗口开启时间（相对于本段攻击开始，单位：秒）
     * 在此时间之前按下攻击键会被忽略（处于攻击预备期）
     * 通常设在攻击"蓄力完毕、即将出刀"的时刻
     */
    UPROPERTY(EditAnywhere, Category = "Input Window")
    float HitWindowStart = 0.3f;

    /**
     * 窗口关闭时间建议值（相对本段攻击开始，单位：秒）
     * 注意：实际窗口关闭由 MontageEnded 回调决定，
     * 此值仅作为编辑器中的参考标记，帮助策划把握手感节奏。
     * 实际逻辑：只要在 Montage 结束前按下了就算有效输入
     */
    UPROPERTY(EditAnywhere, Category = "Input Window")
    float HitWindowEnd = 0.8f;

    // ====== 子判定（高级，可选）======

    /**
     * 子判定列表
     * 
     * 【普通情况】留空（默认）→ 这段攻击只有 1 次 SphereTrace 判定，
     *   使用上面的 BaseDamage/DamageMultiplier/Radius 等主属性。
     *   适用场景：标准单次斩击、突刺、下劈等。
     * 
     * 【特殊情况】填写 N 个元素 → 这段攻击有 N 次独立伤害判定。
     *   每次判定的属性可单独覆盖（Override != 0 则覆盖父级，= 0 则继承）。
     *   Montage 的对应 Section 中需要放 N 个 AnimNotify_MeleeHit，
     *   按顺序依次触发 MeleeHitCheck() 并读取 SubHits[0]、SubHits[1]...
     *   
     * 适用场景：
     *   - 双刀乱舞（左斩+右斩，两次不同伤害）
     *   - 长枪三连刺（3 次小伤害累加）
     *   - 大剑横扫（先扫近处再扫远处，两次不同半径判定）
     * 
     * @note 此字段放在 AdvancedDisplay 中，不影响常规配置体验
     */
    UPROPERTY(EditAnywhere, AdvancedDisplay, Category = "Sub-Hits")
    TArray<FSubHitEntry> SubHits;
};
```

---

### 2.4 FSubHitEntry（子判定参数）

```cpp
/**
 * 单段攻击内的子判定覆盖参数
 *
 * 当 FComboHitEntry.SubHits 非空时，每次 AnimNotify_MeleeHit 触发
 * 会按顺序读取 SubHits[i]，用其中的 Override 值覆盖父级参数。
 * 
 * 所有 Override 字段的约定：
 *   = 0（或等效默认值）→ 继承父级 FComboHitEntry 的对应值
 *   != 0                  → 使用此处的覆盖值
 */
USTRUCT()
struct FSubHitEntry
{
    GENERATED_BODY()

    /** 伤害倍率覆盖（0 = 继承父级 HitEntry.DamageMultiplier）*/
    UPROPERTY(EditAnywhere, Category = "Sub-Hit Override")
    float DamageMultiplierOverride = 0.f;

    /** 判定半径覆盖（0 = 继承父级 HitEntry.AttackSphereRadius）*/
    UPROPERTY(EditAnywhere, Category = "Sub-Hit Override")
    float SphereRadiusOverride = 0.f;

    /** 向前偏移覆盖（0 = 继承父级 HitEntry.AttackForwardOffset）*/
    UPROPERTY(EditAnywhere, Category = "Sub-Hit Override")
    float ForwardOffsetOverride = 0.f;

    /** 击退力度覆盖（0 = 继承父级 HitEntry.KnockbackForce）*/
    UPROPERTY(EditAnywhere, Category = "Sub-Hit Override")
    float KnockbackOverride = 0.f;
};
```

---

## 3. 新建文件清单

| # | 文件名 | 类型 | 用途 |
|---|--------|------|------|
| 1 | `ComboAttackData.h` | C++ Header | `UComboAttackData` + `FComboHitEntry` + `FSubHitEntry` 定义 |
| 2 | `ComboAttackData.cpp` | C++ Source | 构造函数初始化（如有需要）|
| 3 | `AnimNotify_MeleeHit.h` | C++ Header | 近战命中帧通知类声明 |
| 4 | `AnimNotify_MeleeHit.cpp` | C++ Source | `Notify()` 实现 → 回调玩家角色 |

## 4. 修改文件清单

| 文件 | 修改内容 |
|------|---------|
| `WeaponData.h` | 新增 `TSoftObjectPtr<UComboAttackData> MeleeComboData` 字段（**不添加** bIsMeleeWeapon，用 !bIsRangedWeapon 替代）|
| `MyPlayerCharacter.h` | 新增连击状态机成员变量、Timer 句柄、方法声明；新增蓝图扩展点委托 |
| `MyPlayerCharacter.cpp` | 改造 `Attack()` 方法；实现完整连击状态机（Start/Advance/Reset/Window/Timeout）；改造 `MeleeHitCheck()` 支持 SubHits；修改 `EquipWeapon()`/`UnequipWeapon()`/`HandleQuickSlotSelectionChanged()` 加入连击清理逻辑 |

---

## 5. 核心流程

### 5.1 时序图（以三连击为例）

```
                    时间轴 →

Idle:            [等待攻击输入]
                 ↓ Attack() 首次按下
第1段 (Hit1):    [==预备(0~0.3)==][★判定@0.2][=收招(0.3~0.5)=]
                              ↑                    ↑
                        OnMeleeHitNotify       W-Open Timer 到期
                          ↓                     ↓
                   MeleeHitCheck()         bIsInComboWindow=true
                   (造成 Hit1 伤害)        (此时按键会被缓冲)
                                                   │
                                          玩家在 0.35s 按下！
                                                   │
                                              缓冲输入 ✅
                                                   │
                                         MontageEnded @ 0.5s
                                               │
                                    ┌────────────┴────────────┐
                                    │  有缓冲输入？             │
                                    │  YES → AdvanceToNextHit  │
                                    └────────────┬────────────┘
                                                 ↓ 重置 Timers
                                                 播放 Hit2 Section
第2段 (Hit2):    [==上挑(0.5~0.75)==][★判定@0.72][=落地(0.75~1.0)=]
                                     ↑                      ↑
                               OnMeleeHitNotify         W-Open 到期
                                 ↓                       │
                          MeleeHitCheck()          窗口开启
                          (造成 Hit2 伤)                │
                                                           │
                                                  玩家没按...
                                                           │
                                                 MontageEnded @ 1.0s
                                                       │
                                           ┌────────────┴────────────┐
                                           │  有缓冲输入？             │
                                           │  NO → ResetCombo()      │
                                           │      bIsAttacking=false │
                                           └─────────────────────────┘
                                                              ↓
                                                          回到 Idle
```

### 5.2 三层 Timer 协作图

```
┌──────────────────────────────────────────────────────────────────┐
│  Attack() 按下                                                    │
└───────────────────────────────┬──────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│  StartComboHit() — 播放当前段动画                                  │
│                                                                    │
│  ① PlayAnimMontage(ComboMontage, 1.0f, Hits[Index].SectionName)  │
│                                                                    │
│  ② 启动 ComboResetTimer (全局超时)                                │
│     ┌────────────────────────────┐                               │
│     │ 时长 = ComboResetTime (1s) │ ← 始终运行                     │
│     │ 到期 → OnComboResetTimeout │                                │
│     │       → ResetCombo()       │                                │
│     │ 每次 AdvanceToNextHit 重置  │                                │
│     └────────────────────────────┘                               │
│                                                                    │
│  ③ 启动 WindowOpenTimer (延迟开启输入窗口)                         │
│     ┌────────────────────────────┐                               │
│     │ 延迟 = HitWindowStart      │ ← 只跑一次/段                  │
│     │ 到期 → bIsInComboWindow=T  │                                │
│     └────────────────────────────┘                               │
│                                                                    │
│  ④ 注册 MontageEnded 回调                                         │
│     → OnAttackMontageEnded_Combo()                                 │
└───────────────────────────────┬──────────────────────────────────┘
                                │
              ┌─────────────────┼─────────────────────┐
              ▼                 ▼                       ▼
     [OnComboWindowOpen]  [Montage Ended]      [Combo Timeout]
     bIsInComboWindow=T   检查缓冲输入？        强制重置
     开始接受按键缓冲       ├─有→Advance        回到 Idle
                           └─无→Reset
```

### 5.3 状态转换图

```
          ┌──────────────────┐
          │     Idle(空闲)    │ ◄── ComboTimeout / 无缓冲输入
          │  ComboIdx=0      │      MontageEnded 且无缓存
          │  bIsAttacking=F  │      外部中断(受伤/切武器)
          └───────┬──────────┘
                  │ Attack() 按下 & !bIsAttacking
                  ▼
          ┌──────────────────┐
          │   PlayingHitN    │ ◄──────────────────────┐
          │  (播放第N段)      │                        │
          └───────┬──────────┘                        │
                  │                                   │
        ┌─────────┴─────────┐                         │
        ▼                   ▼                         │
  [OnMeleeHitNotify]  [MontageEnded]                  │
       │                   │                         │
  MeleeHitCheck()          │                         │
       │                   ▼                         │
       │          ┌─────────────────┐                │
       │          │ 有缓冲输入？     │                │
       │          └───────┬─────────┘                │
       │               Yes↙    No↘                   │
       │                 ▼      ▼                    │
       │         AdvanceToNext  ResetCombo ──────────┘
       │         (Idx++/循环)   │
       │                └───────┘
       │                        │
       └────────────────────────► 播放下一段 Montage
                                  (重新启动两个 Timer)
```

---

## 6. MyPlayerCharacter 修改详情

### 6.1 头文件新增（MyPlayerCharacter.h）

在 `// 攻击系统` 区域之后，新增以下内容：

```cpp
// ==============================================
// 连击系统（仅近战武器使用）
// ==============================================

private:
    // ---- 连击状态变量 ----

    /** 当前正在执行第几段攻击（0-based，0 = 第一段）*/
    int32 CurrentComboIndex = 0;

    /** 是否处于输入窗口期内（true = 此时按键会被缓冲）*/
    bool bIsInComboWindow = false;

    /** 是否有缓冲的攻击输入（在窗口期内提前按下了但还没处理）*/
    bool bHasBufferedInput = false;

    /** 当前段内的子判定计数器（用于 SubHits 多判定场景）*/
    int32 CurrentSubHitIndex = 0;

    // ---- Timer 句柄 ----

    /** 连击全局超时 Timer（超时未按键 → 强制 ResetCombo）*/
    FTimerHandle ComboResetTimer;

    /** 输入窗口开启延迟 Timer（预备期结束后才开放按键响应）*/
    FTimerHandle WindowOpenTimer;

    // ---- 数据缓存 ----

    /**
     * 当前武器的连击配置缓存（软引用加载后的强指针持有）
     * 
     * 在 EquipWeapon() 时预加载（LoadSynchronous），
     * 避免首次攻击时卡帧。切换/卸下武器时清空。
     * 使用 TWeakObjectPtr 避免阻止 GC 回收无效数据。
     */
    TWeakObjectPtr<UComboAttackData> ActiveComboDataCache;

    // ---- 核心连击方法 ----

    /**
     * 确保连击数据已就绪
     * 
     * 从 CurrentWeaponData->MeleeComboData 加载并缓存到 ActiveComboDataCache。
     * 如果数据无效或不是近战武器，返回 false。
     * 
     * @return true = 可以继续连击流程; false = 应终止
     */
    bool EnsureComboDataReady();

    /**
     * 开始播放当前段的攻击动画
     * 
     * 执行操作：
     * 1. PlayAnimMontage(ComboMontage, 1.0f, SectionName)
     * 2. 设置 bIsAttacking = true
     * 3. 启动 ComboResetTimer
     * 4. 启动 WindowOpenTimer（延迟 HitWindowStart 秒）
     * 5. 注册 MontageEnded 回调
     * 6. 重置 bIsInComboWindow / bHasBufferedInput / CurrentSubHitIndex
     */
    void StartComboHit();

    /** 推进到下一段攻击（或循环回第一段 / 结束连击）*/
    void AdvanceToNextHit();

    /** 完整重置所有连击状态（清除 Timer、停止 Montage、归零所有索引）*/
    void ResetCombo(bool bInterrupted = false);

    // ---- Timer 回调 ----

    /** 窗口开启 Timer 到期回调 → 设置 bIsInComboWindow = true */
    UFUNCTION()
    void OnComboWindowOpen();

    /** 全局超时 Timer 到期回调 → 强制 ResetCombo */
    UFUNCTION()
    void OnComboResetTimeout();

    /** Montage 播放结束回调 → 检查缓冲输入决定衔接或结束 */
    UFUNCTION()
    void OnAttackMontageEnded_Combo(UAnimMontage* Montage, bool bInterrupted);

    // ---- Notify 回调 ----

    /**
     * 近战命中 AnimNotify 回调入口
     * 由 AnimNotify_MeleeHit::Notify() 在精确帧调用
     */
    void OnMeleeHitNotify();

public:
    // ---- 外部查询接口 ----

    /** 获取当前连击段数（0-based，外部用于 UI 显示等）*/
    int32 GetCurrentComboIndex() const { return CurrentComboIndex; }

    /** 是否正处于连击攻击过程中（含任意段）*/
    bool IsInComboAttack() const { return CurrentComboIndex > 0 || bIsAttacking; }

    // ---- 蓝图扩展点 ----

    /**
     * 近战攻击命中时的蓝图扩展点
     * 
     * 在 MeleeHitCheck() SphereTrace 命中目标后调用。
     * 蓝图中可在此添加命中特效、打击音效、屏幕震动、
     * 帧冻结(Hit Stop)、连击计数UI刷新等效果。
     * 
     * @param HitResult       SphereTrace 的命中结果（含位置/法线/Actor 等）
     * @param ComboHitIndex   当前是第几段（0-based）
     * @param SubHitIndex     当前是该段内第几次子判定（0-based, 无 SubHits 时恒为 0）
     * @param FinalDamage     本次造成的最终伤害值
     */
    UFUNCTION(BlueprintImplementableEvent, Category = "Combat|Combo",
        meta = (DisplayName = "On Melee Attack Hit"))
    void BP_OnMeleeAttackHit(const FHitResult& HitResult, int32 ComboHitIndex, int32 SubHitIndex, float FinalDamage);

    /**
     * 连击段推进时的蓝图扩展点
     * 
     * 在 AdvanceToNextHit() 成功推进后调用。
     * 蓝图中可添加段切换特效、音效变化、
     * 连击数字弹出等反馈效果。
     * 
     * @param NewComboIndex 推进后的新段数
     */
    UFUNCTION(BlueprintImplementableEvent, Category = "Combat|Combo",
        meta = (DisplayName = "On Combo Advanced"))
    void BP_OnComboAdvanced(int32 NewComboIndex);

    /**
     * 连击重置时的蓝图扩展点
     * 
     * 在 ResetCombo() 中调用（无论超时/中断/正常结束都会触发）。
     * 蓝图中可清理连击相关 UI、停止连击音效等。
     * 
     * @param bWasInterrupted 是否被外部因素打断（受伤、切武器等）
     */
    UFUNCTION(BlueprintImplementableEvent, Category = "Combat|Combo",
        meta = (DisplayName = "On Combo Reset"))
    void BP_OnComboReset(bool bWasInterrupted);
```

---

### 7. MyPlayerCharacter.cpp 实现细节

#### 7.1 Attack() 方法改造

**改造前**（简化示意）：
```cpp
void AMyPlayerCharacter::Attack()
{
    if (bIsAttacking) return;
    if (!CurrentWeaponData) return;

    // 取 Montage → Play → 设置冷却 → 完成
}
```

**改造后**：
```cpp
void AMyPlayerCharacter::Attack()
{
    // === 前置检查（不变）===
    if (!CurrentWeaponData) return;

    // ====== 分支：远程 vs 近战（连击）======

    // --- 远程武器：保持原有逻辑完全不变 ---
    if (CurrentWeaponData->bIsRangedWeapon)
    {
        // [原有远程攻击代码原封不动]
        // MP 检查 → 冷却检查 → 播放 Montage → 设置 bIsAttacking → Timer
        return;
    }

    // --- 近战武器：走连击系统 ---
    // 1. 确保连击数据已加载且有效
    if (!EnsureComboDataReady())
    {
        // 没有连击配置的近战武器 → 降级为单次攻击或提示
        UE_LOG(LogTemp, Warning, TEXT("[Combo] No combo data for current melee weapon"));
        return;
    }

    // 2. 正在攻击中时的输入处理
    if (bIsAttacking)
    {
        if (bIsInComboWindow)
        {
            // ✅ 窗口期内按下 → 缓存输入，等待当前段 MontageEnded 后衔接
            bHasBufferedInput = true;
            UE_LOG(LogTemp, Log,
                TEXT("[Combo] Input buffered at hit %d (waiting for montage end)"),
                CurrentComboIndex);
        }
        else
        {
            // ❌ 不在窗口期内（还在预备阶段）→ 忽略此次按键
            UE_LOG(LogTemp, Log,
                TEXT("[Combo] Input ignored - not in window (hit %d, attacking)"),
                CurrentComboIndex);
        }
        return;  // 无论哪种情况都不打断当前动画
    }

    // 3. 不在攻击中 → 开始新的攻击段（首击或中断后重新开始）
    StartComboHit();
}
```

#### 7.2 EnsureComboDataReady()

```cpp
bool AMyPlayerCharacter::EnsureComboDataReady()
{
    // 已有有效缓存 → 直接使用
    if (ActiveComboDataCache.IsValid()) return true;

    // 无武器数据 → 失败
    if (!CurrentWeaponData) return false;

    // 不是近战武器（防御性检查，理论上前面已过滤）
    if (CurrentWeaponData->bIsRangedWeapon) return false;

    // 加载软引用
    UComboAttackData* LoadedData = CurrentWeaponData->MeleeComboData.LoadSynchronous();
    if (!LoadedData)
    {
        UE_LOG(LogTemp, Warning,
            TEXT("[Combo] Failed to load MeleeComboData for weapon: %s"),
            *CurrentWeaponData->GetFName().ToString());
        return false;
    }

    // 校验数据完整性
    if (!LoadedData->ComboMontage || LoadedData->Hits.Num() == 0)
    {
        UE_LOG(LogTemp, Warning,
            TEXT("[Combo] Combo data incomplete: Montage=%p, Hits=%d"),
            LoadedData->ComboMontage, LoadedData->Hits.Num());
        return false;
    }

    ActiveComboDataCache = LoadedData;
    return true;
}
```

#### 7.3 StartComboHit()

```cpp
void AMyPlayerCharacter::StartComboHit()
{
    check(ActiveComboDataCache.IsValid());

    // 取当前段的配置
    const FComboHitEntry& HitCfg = ActiveComboDataCache->Hits[CurrentComboIndex];

    // ① 播放对应 Section 的 Montage
    float Duration = PlayAnimMontage(
        ActiveComboDataCache->ComboMontage,   // 单个共享 Montage
        1.0f,                                  // 播放速率
        HitCfg.SectionName                    // 跳转到指定 Section
    );

    if (Duration <= 0.f)
    {
        UE_LOG(LogTemp, Error,
            TEXT("[Combo] Failed to play montage section '%s' for hit %d"),
            *HitCfg.SectionName.ToString(), CurrentComboIndex);
        ResetCombo();
        return;
    }

    // ② 设置状态标志
    bIsAttacking = true;
    bIsInComboWindow = false;       // 还没到窗口期（等 WindowOpenTimer）
    bHasBufferedInput = false;
    CurrentSubHitIndex = 0;         // 重置子判定索引

    // ③ 启动全局超时 Timer
    GetWorldTimerManager().SetTimer(
        ComboResetTimer,
        this,
        &AMyPlayerCharacter::OnComboResetTimeout,
        ActiveComboDataCache->ComboResetTime,
        false  // 不循环
    );

    // ④ 启动窗口开启延迟 Timer
    GetWorldTimerManager().SetTimer(
        WindowOpenTimer,
        this,
        &AMyPlayerCharacter::OnComboWindowOpen,
        HitCfg.HitWindowStart,      // 这段时间内按键被忽略
        false  // 不循环
    );

    // ⑤ 注册 Montage 播放结束回调
    FOnMontageEnded BlendOutDelegate;
    BlendOutDelegate.BindUObject(this, &AMyPlayerCharacter::OnAttackMontageEnded_Combo);
    GetMesh()->GetAnimInstance()->Montage_SetBlendingOutDelegate(
        BlendOutDelegate,
        ActiveComboDataCache->ComboMontage
    );

    UE_LOG(LogTemp, Log,
        TEXT("[Combo] ▶ Playing hit %d (section '%s'), window opens in %.2fs"),
        CurrentComboIndex, *HitCfg.SectionName.ToString(), HitCfg.HitWindowStart);
}
```

#### 7.4 MeleeHitCheck() — 核心伤害检测（支持 SubHits）

```cpp
void AMyPlayerCharacter::MeleeHitCheck()
{
    // 安全检查
    if (!ActiveComboDataCache.IsValid())
    {
        // 没有连击数据时走原有逻辑（如果有）或直接返回
        UE_LOG(LogTemp, Warning, TEXT("[MeleeHitCheck] No active combo data"));
        return;
    }

    // 边界保护
    if (CurrentComboIndex < 0 ||
        CurrentComboIndex >= ActiveComboDataCache->Hits.Num())
    {
        UE_LOG(LogTemp, Warning,
            TEXT("[MeleeHitCheck] Invalid combo index %d (hits count: %d)"),
            CurrentComboIndex, ActiveComboDataCache->Hits.Num());
        return;
    }

    // 取当前段的基础配置
    const FComboHitEntry& HitCfg = ActiveComboDataCache->Hits[CurrentComboIndex];

    // ====== 解析本次判定的实际参数 ======
    float FinalMultiplier = HitCfg.DamageMultiplier;
    float FinalRadius     = HitCfg.AttackSphereRadius;
    float FinalOffset      = HitCfg.AttackForwardOffset;
    float FinalKnockback   = HitCfg.KnockbackForce;

    // 如果有 SubHits 配置 → 用当前子判定索引读取覆盖值
    bool bIsSubHit = false;
    int32 DisplaySubIndex = 0;  // 用于日志/UI 显示

    if (HitCfg.SubHits.Num() > 0)
    {
        bIsSubHit = true;

        // 边界安全 clamp
        int32 ClampedSubIdx = FMath::Clamp(CurrentSubHitIndex, 0, HitCfg.SubHits.Num() - 1);
        const FSubHitEntry& Sub = HitCfg.SubHits[ClampedSubIdx];
        DisplaySubIndex = ClampedSubIdx;

        // Override 规则：!= 0 则覆盖，= 0 继承父级
        if (Sub.DamageMultiplierOverride > 0.f)
            FinalMultiplier = Sub.DamageMultiplierOverride;
        if (Sub.SphereRadiusOverride > 0.f)
            FinalRadius = Sub.SphereRadiusOverride;
        if (Sub.ForwardOffsetOverride > 0.f)
            FinalOffset = Sub.ForwardOffsetOverride;
        if (Sub.KnockbackOverride > 0.f)
            FinalKnockback = Sub.KnockbackOverride;

        // 推进到下一个子判定（下次 Notify 触发时使用）
        CurrentSubHitIndex++;
        if (CurrentSubHitIndex >= HitCfg.SubHits.Num())
        {
            CurrentSubHitIndex = 0;  // 循环回第一个（或停在最后一个，看需求）
        }
    }

    // 计算最终伤害
    float FinalDamage = HitCfg.BaseDamage * FinalMultiplier;

    // ====== SphereTrace 伤害检测 ======

    // 判定起点：角色胸口高度
    FVector StartLocation = GetActorLocation();
    StartLocation.Z += 80.f;

    // 判定终点：向前偏移
    FVector EndLocation = StartLocation + GetActorForwardVector() * FinalOffset;

    // 构造查询参数
    FCollisionQueryParams Params;
    Params.AddIgnoredActor(this);  // 忽略自身

    // 执行球体扫描
    FHitResult HitResult;
    bool bHit = GetWorld()->SweepSingleByChannel(
        HitResult,
        StartLocation,
        EndLocation,
        FQuat::Identity,
        ECC_Pawn,                            // 只检测 Pawn 通道（敌人通常是 Pawn）
        FCollisionShape::MakeSphere(FinalRadius),
        Params
    );

    if (bHit && HitResult.GetActor())
    {
        AActor* HitActor = HitResult.GetActor();

        // 找目标的 AttributeComponent
        UAttributeComponent* TargetAttr =
            HitActor->FindComponentByClass<UAttributeComponent>();

        if (TargetAttr)
        {
            // 造成伤害
            TargetAttr->ApplyDamage(FinalDamage, this);

            UE_LOG(LogTemp, Log,
                TEXT("[Melee] Hit '%s' for %.1f damage (combo hit %d, sub %d)"),
                *HitActor->GetName(), FinalDamage,
                CurrentComboIndex, DisplaySubIndex);

            // 击退效果
            if (ACharacter* HitChar = Cast<ACharacter>(HitActor))
            {
                FVector KnockbackDir =
                    (HitActor->GetActorLocation() - GetActorLocation()).GetSafeNormal();
                KnockbackDir.Z = 0.3f;  // 稍微向上弹起
                HitChar->LaunchCharacter(KnockbackDir * FinalKnockback, true, true);
            }
        }

        // ★ 蓝图扩展点：命中特效/音效/震动/帧冻结等
        BP_OnMeleeAttackHit(HitResult, CurrentComboIndex, DisplaySubIndex, FinalDamage);
    }
}
```

#### 7.5 OnMeleeHitNotify() — AnimNotify 回调

```cpp
void AMyPlayerCharacter::OnMeleeHitNotify()
{
    MeleeHitCheck();
}
```

#### 7.6 AdvanceToNextHit()

```cpp
void AMyPlayerCharacter::AdvanceToNextHit()
{
    // 安全检查
    if (!ActiveComboDataCache.IsValid())
    {
        ResetCombo();
        return;
    }

    // 清除消费掉的状态
    bHasBufferedInput = false;

    // 段数递增
    CurrentComboIndex++;

    // 总段数
    int32 TotalHits = ActiveComboDataCache->Hits.Num();

    // 检查是否超出最大段数
    if (CurrentComboIndex >= TotalHits)
    {
        if (ActiveComboDataCache->bLoopFromLastHit)
        {
            // 循环模式：回到第一段
            CurrentComboIndex = 0;
            UE_LOG(LogTemp, Log, TEXT("[Combo] Loop back to hit 0"));
        }
        else
        {
            // 非循环：连击结束
            UE_LOG(LogTemp, Log, TEXT("[Combo] Combo complete (%d hits), ending"), TotalHits);
            ResetCombo();
            bIsAttacking = false;
            return;
        }
    }

    UE_LOG(LogTemp, Log, TEXT("[Combo] ➜ Advancing to hit %d/%d"),
        CurrentComboIndex, TotalHits - 1);

    // ★ 蓝图扩展点：段切换反馈
    BP_OnComboAdvanced(CurrentComboIndex);

    // ★ 播放下一段（内部会重启所有 Timer）
    StartComboHit();
}
```

#### 7.7 ResetCombo()

```cpp
void AMyPlayerCharacter::ResetCombo(bool bInterrupted /* = false */)
{
    UE_LOG(LogTemp, Log,
        TEXT("[Combo] ↺ Reset to idle (was at hit %d, interrupted=%s)"),
        CurrentComboIndex,
        bInterrupted ? TEXT("yes") : TEXT("no"));

    // 归零所有状态索引
    CurrentComboIndex = 0;
    bIsInComboWindow = false;
    bHasBufferedInput = false;
    CurrentSubHitIndex = 0;

    // 清除所有 Timer
    GetWorldTimerManager().ClearTimer(ComboResetTimer);
    GetWorldTimerManager().ClearTimer(WindowOpenTimer);

    // 安全停止可能还在播的 Montage（防止残留动画）
    if (ActiveComboDataCache.IsValid() && ActiveComboDataCache->ComboMontage)
    {
        StopAnimMontage(ActiveComboDataCache->ComboMontage);
    }

    // ★ 蓝图扩展点：连击结束清理
    BP_OnComboReset(bInterrupted);
}
```

#### 7.8 Timer 回调和 MontageEnded

```cpp
// ========== 窗口开启 ==========
void AMyPlayerCharacter::OnComboWindowOpen()
{
    bIsInComboWindow = true;
    UE_LOG(LogTemp, Log,
        TEXT("[Combo] 📂 Window OPEN for hit %d - input accepted now"),
        CurrentComboIndex);
}

// ========== 全局超时 ==========
void AMyPlayerCharacter::OnComboResetTimeout()
{
    UE_LOG(LogTemp, Log,
        TEXT("[Combo] ⏱ TIMEOUT after %.2fs - forcing reset"),
        ActiveComboDataCache.IsValid() ? ActiveComboDataCache->ComboResetTime : 0.f);
    ResetCombo(false);  // 非中断性超时
    bIsAttacking = false;
}

// ========== Montage 播放结束 ==========
void AMyPlayerCharacter::OnAttackMontageEnded_Combo(
    UAnimMontage* Montage, bool bInterrupted)
{
    // 先清除窗口 Timer（防止残留触发）
    GetWorldTimerManager().ClearTimer(WindowOpenTimer);
    bIsInComboWindow = false;

    if (bInterrupted)
    {
        // 被外部打断（受伤硬直、闪避取消、切换武器等）
        UE_LOG(LogTemp, Log, TEXT("[Combo] Montage interrupted!"));
        ResetCombo(true);
        bIsAttacking = false;
        return;
    }

    // 检查是否有缓冲的输入
    if (bHasBufferedInput)
    {
        // ✅ 有缓冲 → 衔接到下一段
        UE_LOG(LogTemp, Log, TEXT("[Combo] Buffered input found → advancing"));
        AdvanceToNextHit();
    }
    else
    {
        // ❌ 无缓冲 → 连击自然结束
        UE_LOG(LogTemp, Log, TEXT("[Combo] No buffered input → combo ended naturally"));
        ResetCombo(false);
        bIsAttacking = false;
    }
}
```

---

## 8. EquipWeapon / UnequipWeapon / 快捷栏切换 — 连击清理

### 8.1 EquipWeapon() — 预加载连击数据

在现有的 `EquipWeapon()` 方法末尾追加：

```cpp
void AMyPlayerCharacter::EquipWeapon(UWeaponData* InWeaponData)
{
    // ... [原有代码不变] ...

    // ★ 新增：预加载连击数据（避免首次攻击时卡帧）
    ActiveComboDataCache.Reset();  // 先清空旧缓存
    
    if (!InWeaponData->bIsRangedWeapon && InWeaponData->MeleeComboData.IsValid())
    {
        UComboAttackData* Loaded = InWeaponData->MeleeComboData.LoadSynchronous();
        if (Loaded && Loaded->ComboMontage && Loaded->Hits.Num() > 0)
        {
            ActiveComboDataCache = Loaded;
            UE_LOG(LogTemp, Log,
                TEXT("[Combo] Pre-loaded combo data: '%s', %d hits"),
                *Loaded->ComboName.ToString(), Loaded->Hits.Num());
        }
        else
        {
            UE_LOG(LogTemp, Log,
                TEXT("[Weapon] '%s' has no valid combo config (ranged or unconfigured)"),
                *InWeaponData->ItemName.ToString());
        }
    }
}
```

### 8.2 UnequipWeapon() — 清理连击状态

```cpp
void AMyPlayerCharacter::UnequipWeapon()
{
    // ... [原有代码不变] ...

    // ★ 新增：重置连击系统
    ResetCombo(true);  // interrupt = true（属于主动切换导致的中断）
    ActiveComboDataCache.Reset();
    
    // 注意: bIsAttacking 的重置由 ResetCombo 的调用方控制
    // （ResetCombo 本身只管连击状态机，不强制改 bIsAttacking）
}
```

### 8.3 HandleQuickSlotSelectionChanged() — 切槽时清理

在快捷栏切换回调中，确保切换到非近战武器时也清理：

```cpp
void AMyPlayerCharacter::HandleQuickSlotSelectionChanged(int32 SlotIndex)
{
    // ... [原有 ClearHeldItem / UnequipWeapon 等代码不变] ...
    
    // UnequipWeapon 内部已经会调 ResetCombo()，此处无需额外处理
    // 但如果新选中的物品不是武器（比如药水），要确保连击状态确实清除了
    
    // （实际上 UnequipWeapon 已经覆盖了这个 case）
}
```

---

## 9. AnimNotify_MeleeHit 实现

### 9.1 头文件

```cpp
#pragma once
#include "Animation/AnimNotifies/AnimNotify.h"
#include "AnimNotify_MeleeHit.generated.h"

/**
 * 近战命中帧通知 (AnimNotify_MeleeHit)
 *
 * 【用途】
 * 放在连击 Montage 每段攻击 Section 的"武器接触敌人瞬间"帧。
 * 当动画播放到此 Notify 帧时，引擎自动调用 Notify() → 回调玩家角色的
 * OnMeleeHitNotify() → MeleeHitCheck() → SphereTrace + ApplyDamage。
 *
 * 【设计模式】
 * 与项目中已有的 AnimNotify_UseItemComplete 和 AnimNotify_EnemyAttack
 * 采用完全相同的 Notify→Cast Owner→Callback 模式。
 *
 * 【使用方式】
 * 1. 在 Montage 编辑器的 Notify Track 中找到对应 Section
 * 2. 在武器即将接触敌人的那一帧（手臂伸直/武器过身体中心的时刻）
 * 3. 拖入一个 AnimNotify_MeleeHit
 * 4. 同一 Section 可放置多个（配合 SubHits 实现多段判定）
 *
 * 【调用链路】
 * Montage 播放到 Notify 帧
 *   → 引擎自动调用 AnimNotify_MeleeHit::Notify()
 *     → MeshComp.GetOwner() 获取拥有者 Actor
 *       → Cast<AMyPlayerCharacter>(Owner)
 *         → PlayerChar->OnMeleeHitNotify()
 *           → PlayerChar->MeleeHitCheck()
 *             → SphereTrace → ApplyDamage → 击退 → BP_OnMeleeAttackHit
 */
UCLASS()
class INTROCPP_API UAnimNotify_MeleeHit : public UAnimNotify
{
    GENERATED_BODY()

public:

    /**
     * 动画播放到此 Notify 帧时由引擎自动调用
     *
     * @param MeshComp      播放此动画的骨骼网格组件（角色的 Mesh）
     * @param Animation     正在播放的动画序列
     * @param EventReference Notify 事件引用（含时间等信息）
     */
    virtual void Notify(USkeletalMeshComponent* MeshComp,
        UAnimSequenceBase* Animation,
        const FAnimNotifyEventReference& EventReference) override;
};
```

### 9.2 实现文件

```cpp
#include "AnimNotify_MeleeHit.h"
#include "MyPlayerCharacter.h"

void UAnimNotify_MeleeHit::Notify(
    USkeletalMeshComponent* MeshComp,
    UAnimSequenceBase* Animation,
    const FAnimNotifyEventReference& EventReference)
{
    Super::Notify(MeshComp, Animation, EventReference);

    // 安全获取 Owner Actor
    AActor* OwnerActor = MeshComp ? MeshComp->GetOwner() : nullptr;
    if (!OwnerActor) return;

    // 尝试转换为玩家角色
    if (AMyPlayerCharacter* PlayerChar = Cast<AMyPlayerCharacter>(OwnerActor))
    {
        PlayerChar->OnMeleeHitNotify();
    }
    // 如果 Cast 失败（例如敌人也用了这个 Notify），静默忽略
}
```

---

## 10. WeaponData 扩展

### 10.1 在 WeaponData.h 类定义末尾新增

```cpp
// ====== 连击系统（仅近战武器使用）======

/**
 * 近战连击配置数据的软引用
 * 
 * - bIsRangedWeapon = false 时生效
 * - 指向一个 UComboAttackData DataAsset（包含 Montage + 各段参数）
 * - 软引用避免不用的连击数据占用内存
 * - 在 EquipWeapon() 时 LoadSynchronous 预加载
 * 
 * 留空(null)的近战武器：无法进行连击，
 * Attack() 会因 EnsureComboDataReady() 返回 false 而拒绝执行。
 */
UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat|Melee Combo")
TSoftObjectPtr<UComboAttackData> MeleeComboData;
```

**注意：不添加 `bIsMeleeWeapon` 字段**，直接用已有的 `bIsRangedWeapon` 取反来判断：
```cpp
bool bIsMelee = !CurrentWeaponData->bIsRangedWeapon;
```

---

## 11. UE 编辑器操作步骤

### Step 1: 编译 C++

- 编译项目，确认无错误
- 新类型会自动出现在编辑器中

### Step 2: 制作/导入连击 Montage

准备一个包含多个 Section 的 Montage 资产：

1. 导入或制作各段攻击动画（Hit1 / Hit2 / Hit3）
2. 创建/打开 Montage 编辑器
3. 将动画按顺序排列在同一时间线上
4. 为每段创建 **Section**：
   - 在时间线上右键 → Add Section → 命名为 `"Hit1"` / `"Hit2"` / `"Hit3"`
   - 确保 Section 的时间范围正确覆盖对应的动画片段
5. **在每个 Section 的"武器命中瞬间"帧添加 Notify**：
   - 找到 Notify Track 区域
   - 添加名为 `"MeleeHit"` 的轨道（或使用 Default Track）
   - 将 `AnimNotify_MeleeHit` 拖入对应的时间点
   - 如某段有多判定（SubHits），拖入多个 MeleeHit Notify

**推荐 Notify 位置参考**（以总时长为例）：

| Section | 总时长 | Notify 位置 | 说明 |
|---------|--------|------------|------|
| Hit1 | ~0.50s | @ 0.20s (40%) | 横扫中段，手伸直 |
| Hit2 | ~0.50s | @ 0.22s (44%) | 上挑顶点前一刻 |
| Hit3 | ~0.60s | @ 0.28s (47%) | 下劈即将触地 |

### Step 3: 创建连击数据资产实例

1. **Content Browser → 右键 → Miscellaneous → Data Asset**
2. 选择 `ComboAttackData` 类
3. 命名为 `DA_Combo_SwordBasic`
4. 编辑 Details 面板：

```
基本信息:
  ComboName: "基础剑技三连"
  WeaponAnimType: Slash_1H
  ComboMontage: [拖入 M_Combo_Slash_1H]

行为:
  bLoopFromLastHit: ☑ true (循环) 或 ☐ false (不循环)
  ComboResetTime: 1.0

Hits 数组 (点击 + 号添加元素):

  [0]:
    SectionName: "Hit1"
    BaseDamage: 15
    DamageMultiplier: 1.0
    AttackSphereRadius: 50
    AttackForwardOffset: 60
    KnockbackForce: 500
    HitWindowStart: 0.30
    HitWindowEnd: 0.80
    SubHits: [空]

  [1]:
    SectionName: "Hit2"
    BaseDamage: 18
    DamageMultiplier: 1.2
    AttackSphereRadius: 55
    AttackForwardOffset: 65
    KnockbackForce: 600
    HitWindowStart: 0.25
    HitWindowEnd: 0.75
    SubHits: [空]

  [2]:
    SectionName: "Hit3"
    BaseDamage: 25
    DamageMultiplier: 1.5
    AttackSphereRadius: 70
    AttackForwardOffset: 80
    KnockbackForce: 800
    HitWindowStart: 0.35
    HitWindowEnd: 0.90
    SubHits: [空]
```

### Step 4: 绑定到武器

打开铁剑的 `UWeaponData` 资产（如 `DA_WP_Sword_Iron`），设置：

```
Combat:
  bIsRangedWeapon: ☐ false
  WeaponAnimType: Slash_1H
  Combat | Melee Combo:
    MeleeComboData: [拖入 DA_Combo_SwordBasic]

(可选) 兼容性绑定:
角色蓝图的 AttackMontageMap:
  [Slash_1H] = M_Combo_Slash_1H   ← 同一个 Montage！
  (非连击场景 fallback 使用)
```

---

## 12. 示例配置速查表

### 12.1 三段剑连击（DA_Combo_SwordBasic）

| 参数 | Hit1 | Hit2 | Hit3 |
|------|------|------|------|
| Section | "Hit1" | "Hit2" | "Hit3" |
| Montage 时间 | 0.0~0.50s | 0.50~1.00s | 1.00~1.60s |
| 基础伤害 | 15 | 18 | 25 |
| 伤害倍率 | 1.0x | 1.2x | 1.5x |
| 最终伤害 | **15** | **21.6** | **37.5** |
| 判定半径 | 50 | 55 | 70 |
| 向前偏移 | 60 | 65 | 80 |
| 击退力度 | 500 | 600 | 800 |
| 窗口开启 | 0.30s | 0.25s | 0.35s |
| 窗口关闭(参考) | 0.80s | 0.75s | 0.90s |
| SubHits | 空 | 空 | 空 |

**手感特点**：快起手 → 渐强 → 重收尾，经典 ARPG 三段节奏

### 12.2 双刀五连击（DA_Combo_DualBlade）— 带 SubHits 示例

| 参数 | Hit1 | Hit2 | Hit3 | Hit4 | Hit5 |
|------|------|------|------|------|------|
| Section | "Hit1" | "Hit2" | "Hit3" | "Hit4" | "Hit5" |
| 基础伤害 | 10 | 10 | 12 | 14 | 20 |
| 伤害倍率 | 1.0 | 1.0 | 1.2 | 1.3 | 2.0 |
| 判定半径 | 45 | 45 | 50 | 55 | 65 |
| **SubHits** | **空** | **2 个** | **空** | **3 个** | **空** |
| SubHits[0] | — | Mult=0.8 半径=40 | — | Mult=0.7 半径=40 | — |
| SubHits[1] | — | Mult=1.3 半径=55 | — | Mult=1.0 半径=50 | — |
| SubHits[2] | — | — | — | Mult=1.5 半径=70 | — |

**说明**：
- Hit2 是"双刀左右斩"，2 次判定（左轻右重）
- Hit4 是"乱舞三连刺"，3 次判定（轻→中→重）
- 其他段落为普通单次判定

### 12.3 两段斧连击（DA_Combo_AxeHeavy）

| 参数 | Hit1 | Hit2 |
|------|------|------|
| Section | "Hit1" | "Hit2" |
| 基础伤害 | 25 | 40 |
| 伤害倍率 | 1.0x | 1.6x |
| 最终伤害 | **25** | **64** |
| 判定半径 | 65 | 75 |
| 击退力度 | 800 | 1200 |
| 窗口开启 | 0.35s | 0.38s |
| 窗口关闭(参考) | 0.85s | 0.90s |
| bLoopFromLastHit | false | — |

**手感特点**：慢速重型武器，两段即止不循环，强调每一击的分量感

---

## 13. 未来扩展方向（不在本次范围）

- [ ] **连击中断/取消**: 受伤/闪避时打断当前连击并进入受击硬直（调用 `ResetCombo(true)` 即可）
- [ ] **空中连击**: 跳跃中的专用连击序列（ComboAttackData 加 `bIsAirCombo` 字段区分）
- [ ] **冲刺攻击**: 冲刺+攻击的特殊起始段（额外字段 `ChargeEntryMontage` / `ChargeEntryConfig`）
- [ ] **蓄力攻击**: 按住蓄力释放强力单段（`HoldToCharge` 参数）
- [ ] **派生攻击**: 特定段 + 方向键 = 特殊招式（如 Hit2 + ↓ = 下劈变体）
- [ ] **连击计数 UI**: 屏幕显示当前段数 + 累计伤害数字（读 `GetCurrentComboIndex()`）
- [ ] **武器切换连击**: 不同武器独立的 ComboData，切换时自动 Reset
- [ ] **属性加成**: 力量/敏捷属性影响各段 DamageMultiplier
- [ ] **音效/震动**: 每段独立的打击音效 + 手柄震动反馈
- [ ] **帧冻结 (Hit Stop)**: 命中瞬间短暂停顿增强打击感（可在 BP_OnMeleeHit 中实现）
- [ ] **连击评级**: 根据连击完成度和速度给予 S/A/B/C 评价

---

## 14. 参考文件索引

| 文件 | 参考价值 |
|------|---------|
| `EnemyBase::ExecuteMeleeDamage()` | SphereTrace + ApplyDamage 完整实现模板 |
| `AnimNotify_EnemyAttack.h/.cpp` | AnimNotify 模式模板（本项目统一风格）|
| `AnimNotify_UseItemComplete.h/.cpp` | AnimNotify 模式模板（本项目统一风格）|
| `AAFireballProjectile::ProcessHit()` | ApplyDamage 调用方式 |
| `UAttributeComponent::ApplyDamage()` | 统一伤害接口签名 |
| `MyPlayerCharacter::Attack()` | 入口点，已被连击系统改造 |
| `MyPlayerCharacter::FireFromHand()` | 远程投射物发射逻辑（保持不变）|
| `MyPlayerCharacter::EquipWeapon()` | 装备流程，需追加预加载逻辑 |
| `MyPlayerCharacter::HandleQuickSlotSelectionChanged()` | 快捷栏切换，需确认连击清理 |
| `UItemAction.h` | 策略模式参考（未来攻击也可考虑 Action 化）|

---

## 附录 A：设计决策记录

| 决策 | 选择 | 原因 |
|------|------|------|
| 动画存储方式 | 单 Montage + Section | 比 per-Montage 更省文件、与 AttackMontageMap 兼容 |
| 是否加 bIsMeleeWeapon | **不加** | 与已有 bIsRangedWeapon 冗余，取反即可 |
| 数据加载时机 | EquipWeapon() 预加载 | 避免 Attack() 首次卡帧 |
| 连击状态存放位置 | MyPlayerCharacter 成员变量 | 当前规模够用；未来可抽取为 UComboManagerComponent |
| SubHits 方案 | FSubHitEntry 覆盖数组 | 高级面板可选，不影响普通配置体验 |
| 窗口管理方式 | WindowOpenTimer + ComboResetTimer + MontageEnded | 三层协作，清晰可靠 |
| 切换武器时 | ResetCombo(true) + 清缓存 | 避免旧连击数据污染新武器 |
