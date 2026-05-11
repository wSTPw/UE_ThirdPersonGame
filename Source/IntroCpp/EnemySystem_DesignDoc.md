# 近战敌人系统 — 完整设计方案

> **文档版本**: v1.0 | **日期**: 2026-05-11
> **目标**: 构建一套数据驱动、可复用、易扩展的近战敌人系统
> **对齐**: 完全遵循项目现有架构模式（AttributeComponent / AnimNotify / DataAsset）

---

## 一、系统全景图

### 1.1 核心设计原则

```
                    ACharacter (UE 内置)
                         │
              ┌──────────┴──────────┐
              │                       │
     AMyPlayerCharacter          AEnemyBase (新建)
     (你现有的玩家)                │
                          ┌───────┴────────┐
                          │                │
                     ASlimeEnemy      AGoblinEnemy
                     (史莱姆)          (哥布林)
                        ...             ...
```

**核心原则：最大化复用现有组件体系**

```
AMyPlayerCharacter          AEnemyBase (新建)
├── UAttributeComponent  ←──┤   同一个组件！同样的 ApplyDamage 接口
│                            │   玩家扣血 = 敌人扣血，同一套代码
│                            │
├── AnimNotify 触发攻击 ─────│   AnimNotify_EnemyAttack
│   FireFromHand()           ├── SphereTrace 近战检测 → ApplyDamage(Damage, this)
│                            │
├── AttackMontage + 播放 ────│   PerformAttack() → PlayAnimMontage(AttackMontage)
│                            │
└── WeaponData(DataAsset)    ├── EnemyData(DataAsset) — 数据驱动配置
                             │   HP/伤害/速度/动画 全在蓝图中配
                             │
                             └── EnemyAIController — 状态机: Patrol→Chase→Attack→Death
```

### 1.2 与现有系统的对接关系

| 现有系统 | 对接方式 | 说明 |
|---------|---------|------|
| `UAttributeComponent` | 直接挂载到 Enemy | 复用 ApplyDamage / OnHealthChanged / OnCharacterDeath |
| `AnimNotify_Fireball` | 新建 `AnimNotify_EnemyAttack` | 同样的 Notify → 回调模式 |
| `AFireballProjectile::ProcessHit` | 敌人攻击检测复用同模式 | FindComponentByClass<UAttributeComponent>() → ApplyDamage() |
| `ConsumableData/WeaponData` | 新建 `EnemyData` (UPrimaryDataAsset) | 同样的 DataAsset 驱动思路 |
| `MyPlayerCharacter::MeleeHitCheck()` | `ExecuteMeleeDamage()` 完善此模式 | 预留接口终于实现 |

---

## 二、文件清单与开发顺序

### 2.1 文件总览

| 阶段 | 文件 | 说明 | 行数估算 |
|------|------|------|---------|
| **Phase 1** | `EnemyData.h` | 敌人数据资产（DataAsset） | ~70行 |
| **Phase 2** | `EnemyBase.h` | 敌人基类头文件 | ~100行 |
| | `EnemyBase.cpp` | 敌人基类实现 | ~200行 |
| **Phase 3** | `AnimNotify_EnemyAttack.h` | 攻击帧通知头文件 | ~15行 |
| | `AnimNotify_EnemyAttack.cpp` | 攻击帧通知实现 | ~20行 |
| **Phase 4** | `EnemyAIController.h` | AI控制器头文件 | ~60行 |
| | `EnemyAIController.cpp` | AI控制器实现 | ~200行 |
| **Phase 5** | 具体子类（可选） | 如 `ASlimeEnemy` | ~30行 |

### 2.2 开发优先级（建议实施顺序）

```
Week 1: 最小可用原型（能追能打能死）
  ├─ Phase 1: EnemyData — 所有数值走配置
  ├─ Phase 3: AnimNotify_EnemyAttack — 攻击帧触发
  ├─ Phase 2: EnemyBase — 基类 + 攻击检测 + 死亡
  └─ Phase 4: EnemyAIController — Chase + Attack 两态即可

Week 2: 完善 AI
  └─ Patrol 巡逻状态 + WaitAtPoint

Week 3: 打磨 + 扩展
  ├─ HitReact 受击反馈动画
  ├─ 掉落物系统（死亡时生成 PickupItem）
  └─ 第一种具体敌人子类（如 ASlimeEnemy）
```

---

## 三、Phase 1: EnemyData（数据资产）

### 3.1 设计思路

**完全对齐 ConsumableData / WeaponData 的模式**: 使用 UPrimaryDataAsset，所有数值在蓝图中配置，不同敌人只需换 DataAsset 不改 C++。

```cpp
// 文件: EnemyData.h
#pragma once
#include "CoreMinimal.h"
#include "Engine/PrimaryDataAsset.h"
#include "EnemyData.generated.h"

/**
 * 敌人数据资产 (PrimaryDataAsset)
 * 
 * 每种敌人的数值配置都在这里。
 * 在 Content Browser 中右键 → Miscellaneous → Data Asset → 选择此类 即可创建实例。
 * 
 * 示例: DA_Enemy_Slime, DA_Enemy_Goblin, DA_Enemy_Boss
 */
UCLASS(Blueprintable, Abstract)
class INTROCPP_API UEnemyData : public UPrimaryDataAsset
{
    GENERATED_BODY()

public:
    
    // ================================================================
    // 基础属性 (Stats)
    // ================================================================
    
    /** 最大生命值 */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Stats")
    float MaxHealth = 100.f;

    /** 每次攻击造成的伤害 */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Stats")
    float AttackDamage = 15.f;
    
    /** 击退力度（0=不击退）*/
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Stats")
    float KnockbackForce = 500.f;


    // ================================================================
    // 移动行为 (Movement)
    // ================================================================

    /** 巡逻/闲置时的移动速度 */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Movement")
    float WalkSpeed = 200.f;

    /** 追击玩家时的移动速度 */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Movement")
    float ChaseSpeed = 400.f;

    /** 是否可以转向（面向目标） */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Movement")
    bool bCanRotate = true;

    /** 转向插值速度（越大越快） */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Movement", meta = (EditCondition = "bCanRotate"))
    float RotationInterpSpeed = 5.f;


    // ================================================================
    // 巡逻设置 (Patrol)
    // ================================================================

    /** 巡逻半径（以初始位置为圆心） */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Patrol")
    float PatrolRadius = 800.f;

    /** 到达巡逻点后的等待时间（秒） */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Patrol")
    float WaitTimeAtPatrolPoint = 2.f;

    /** 巡逻行为类型 */
    UENUM(BlueprintType)
    enum class EPatrolType : uint8 { Random, Circular, BackAndForth };

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Patrol")
    EPatrolType PatrolBehavior = EPatrolType::Random;


    // ================================================================
    // 战斗感知 (Combat Detection)
    // ================================================================

    /** 视觉感知半径（能看到玩家的最大距离） */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
    float SightRadius = 1200.f;

    /** 进入此距离后开始攻击 */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
    float AttackRange = 150.f;

    /** 攻击间隔冷却（秒） */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
    float AttackCooldown = 1.5f;

    /** 丢失目标后继续追击的额外时间（秒），防止频繁切换状态 */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
    float ChaseLeewayTime = 1.0f;

    /** 脱离攻击范围后多久回到追击（秒） */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
    float ExitAttackRangeGraceTime = 0.5f;


    // ================================================================
    // 攻击参数 (Attack Config)
    // ================================================================

    /** 攻击检测形状半径（SphereTrace 的球体大小） */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Attack")
    float AttackSphereRadius = 50.f;

    /** 攻击检测前方延伸距离（从角色位置向前量多少） */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Attack")
    float AttackForwardOffset = 80.f;

    /** 攻击检测的高度偏移（Z轴） */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Attack")
    float AttackZOffset = 0.f;


    // ================================================================
    // 动画 Montage（和玩家武器数据的 Montage 配置方式一致）
    // ================================================================

    /** 攻击动画蒙太奇 */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Animation")
    UAnimMontage* AttackMontage;

    /** 死亡动画蒙太奇 */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Animation")
    UAnimMontage* DeathMontage;

    /** 受击反馈动画（被玩家打中时播放） */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Animation")
    UAnimMontage* HitReactMontage;

    /** 闲置待机动画蒙太奇 */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Animation")
    UAnimMontage* IdleMontage;


    // ================================================================
    // 外观资源 (Appearance) — 可选，用于简单敌人直接换皮
    // ================================================================

    /** 身体网格体（静态网格体敌人适用） */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Appearance")
    UStaticMesh* BodyMesh;

    /** 身体材质 */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Appearance")
    UMaterialInterface* BodyMaterial;

    /** 缩放比例 */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Appearance")
    FVector MeshScale = FVector(1.f);

    /** 骨骼网格体（ skeletal mesh 敌人适用，优先级高于 StaticMesh） */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Appearance")
    USkeletalMesh* SkeletalBodyMesh;


    // ================================================================
    // 音效/VFX (Audio & VFX) — 编辑器可扩展
    // ================================================================

    /** 攻击音效 */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Audio")
    USoundBase* AttackSound;

    /** 死亡音效 */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Audio")
    USoundBase* DeathSound;

    /** 受击音效 */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Audio")
    USoundBase* HitSound;
};
```

### 3.2 编辑器中的使用流程

```
步骤1: Content Browser 右键 → Miscellaneous → Data Asset

步骤2: 选择父类:
      └─ EnemyData (UEnemyData)

步骤3: 命名资产（格式: DA_Enemy_<名称>）
      例: DA_Enemy_Slime, DA_Enemy_Goblin

步骤4: Details 面板配置:
+-- Details -----------------------------------------------------------+
| Stats                                                               |
|   Max Health        [ 100       ]                                   |
|   Attack Damage     [ 15        ]                                   |
|   Knockback Force   [ 500       ]                                   |
|                                                                      |
| Movement                                                            |
|   Walk Speed         [ 200      ]                                   |
|   Chase Speed        [ 400      ]                                   |
|                                                                      |
| Combat                                                              |
|   Sight Radius       [ 1200     ]                                   |
|   Attack Range       [ 150      ]                                   |
|   Attack Cooldown    [ 1.5      ]                                   |
|                                                                      |
| Animation                                                           |
|   Attack Montage     [ M_Slash   ]  ← 从内容浏览器拖入               |
|   Death Montage      [ M_Death   ]                                   |
|   Hit React Montage  [ M_HitReact]                                   |
|                                                                      |
| Appearance                                                          |
|   Body Mesh          [ SM_Slime  ]                                   |
|   Body Material      [ M_Goo     ]                                   |
|                                                                      |
| Audio                                                               |
|   Attack Sound       [ S_Attack  ]                                   |
|   Death Sound        [ S_Death   ]                                   |
+----------------------------------------------------------------------+

步骤5: Ctrl+S 保存
完成! 这个 .uasset 将挂载到 BP_Enemy 的 EnemyData 属性上
```

### 3.3 预设示例配置

| 资产名 | MaxHP | Dmg | Speed(Sight/Chase) | Range | Cooldown | 特征 |
|--------|-------|-----|-------------------|-------|----------|------|
| `DA_Enemy_Slime` | 50 | 8 | 150/250 | 80 | 2.0 | 弱怪慢攻大群 |
| `DA_Enemy_Goblin` | 80 | 12 | 200/400 | 120 | 1.2 | 中等标准怪 |
| `DA_Enemy_Orc` | 200 | 25 | 180/350 | 150 | 1.8 | 高血高伤慢 |
| `DA_Enemy_Boss` | 500 | 40 | 220/300 | 180 | 2.5 | Boss 级别 |

---

## 四、Phase 2: EnemyBase（敌人基类）

### 4.1 设计思路

**完全对齐 MyPlayerCharacter 的结构风格**：

- 继承 `ACharacter`（和玩家一致，自带 Capsule+Mesh+CharacterMovement）
- 用 `AttributeComp`（而非自造 HP 字段）— 和玩家共享同一套伤害/死亡系统
- `PerformAttack()` 播放 Montage — 和你的 `UseHeldItem()/Attack()` 同一模式
- `OnAttackAnimNotify()` 被 AnimNotify 调 — 和 `OnUseItemAnimFinished()` 同一模式
- 数据走 `EnemyData` DataAsset — 和 WeaponData/ConsumableData 一致

### 4.2 头文件

```cpp
// 文件: EnemyBase.h
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "EnemyData.h"
#include "EnemyBase.generated.h"

/**
 * 近战敌人基类
 * 
 * 继承自 ACharacter，挂载 UAttributeComponent 实现生命值管理。
 * 通过 EnemyData (PrimaryDataAsset) 数据驱动所有行为参数。
 * 攻击采用 AnimNotify 精确帧触发模式（与火球攻击/物品使用同一套方案）。
 * 
 * 子类化方式:
 *   - C++ 继承: class ASlimeEnemy : public AEnemyBase { ... };
 *   - 蓝图继承: 创建 BP_Enemy_Slime 基于 AEnemyBase
 */
UCLASS(Abstract, Blueprintable)
class INTROCPP_API AEnemyBase : public ACharacter
{
    GENERATED_BODY()

public:

    // ====== 构造函数 / 生命周期 ======
    AEnemyBase();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaTime) override;

protected:

    // ====== 组件声明（对齐 MyPlayerCharacter 的组织方式）======

    /** 属性组件（HP/MP/死亡系统）— 与玩家共享同一个组件类！ */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
    UAttributeComponent* AttributeComp;

    /** 攻击检测起始点组件（类似玩家的 Socket） */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
    USceneComponent* AttackOrigin;

public:

    // ====== 数据驱动配置（蓝图中指定具体的 EnemyData 资产）======

    /**
     * 此敌人的数值配置数据资产。
     * 在蓝图子类的 Defaults 中拖入对应的 DA_Enemy_xxx 资产。
     * BeginPlay 时自动读取并初始化所有参数。
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    UEnemyData* EnemyData;


    // ====== AI 状态查询接口（BlueprintCallable，给 AIController 调用）======

    /** 设置当前追踪的目标 Actor（通常是玩家） */
    UFUNCTION(BlueprintCallable, Category = "AI")
    void SetTargetActor(AActor* Target);

    /** 清除当前目标 */
    UFUNCTION(BlueprintCallable, Category = "AI")
    void ClearTargetActor();

    /** 获取当前目标 */
    UFUNCTION(BlueprintCallable, Category = "AI", Pure)
    AActor* GetTargetActor() const { return TargetActor; }

    /** 目标是否在指定距离内 */
    UFUNCTION(BlueprintCallable, Category = "AI", Pure)
    bool IsTargetInRange(float Range) const;

    /** 是否存活 */
    UFUNCTION(BlueprintCallable, Category = "AI", Pure)
    bool IsAlive() const;

    /** 是否正在执行攻击动作 */
    UFUNCTION(BlueprintCallable, Category = "AI", Pure)
    bool IsAttacking() const { return bIsAttacking; }

    /** 是否正在执行死亡流程 */
    UFUNCTION(BlueprintCallable, Category = "AI", Pure)
    bool IsDead() const { return bIsDead; }


    // ====== 行为接口 ======

    /**
     * 执行攻击动作
     * 
     * 流程（与 UseHeldItem/Attack 同一模式）：
     * 1. 检查冷却/条件
     * 2. 设置 bIsAttacking = true
     * 3. PlayAnimMontage(AttackMontage)
     * 4. 等待 AnimNotify_EnemyAttack 触发 → OnAttackAnimNotify()
     * 5. 动画结束回调重置 bIsAttacking
     */
    UFUNCTION(BlueprintCallable, Category = "Combat")
    void PerformAttack();

    /**
     * AnimNotify 攻击帧回调入口
     * 由 AnimNotify_EnemyAttack::Notify() 在动画精确帧调用。
     * 在此处执行实际的伤害检测（SphereTrace）。
     */
    void OnAttackAnimNotify();

    /** 死亡处理 */
    UFUNCTION(BlueprintCallable, Category = "Combat")
    void Die();

    /** 受击处理（被玩家攻击时由外部调用） */
    UFUNCTION(BlueprintCallable, Category = "Combat")
    void OnReceiveDamage();


protected:

    // ====== 核心攻击检测逻辑 ======

    /**
     * 执行近战伤害检测
     * 
     * 方式: SphereTrace（球体扫描）
     * 流程:
     *   1. 从 AttackOrigin 或 GetActorLocation 发出 SphereTrace
     *   2. 方向 = GetActorForwardVector()
     *   3. 忽略自己
     *   4. 如果命中 Actor 且有 UAttributeComponent → ApplyDamage
     * 
     * ★★★ 与火球 ProcessHit 完全相同的伤害调用方式 ★★★
     */
    void ExecuteMeleeDamage();

    /** 应用 EnemyData 中的属性初始化角色（速度、碰撞等） */
    void ApplyEnemyDataSettings();

    /** 应用外观设置（Mesh/Material/Scale） */
    void ApplyAppearanceFromData();

private:

    // ====== 内部状态（不加 UPROPERTY，纯 C++ 管理）======
    
    /** 当前追踪的目标（通常由 AIController 设置） */
    AActor* TargetActor = nullptr;

    /** 是否正在攻击动画中 */
    bool bIsAttacking = false;

    /** 是否已死亡 */
    bool bIsDead = false;

    /** 上次攻击时间戳（用于冷却判断） */
    float LastAttackTime = 0.f;

    /** 攻击冷却计时器 */
    float AttackCooldownTimer = 0.f;

    /** 死亡后销毁倒计时 */
    float DeathDestroyTimer = 0.f;

    /** 死亡后多久销毁（秒） */
    static constexpr float DEATH_DESTROY_DELAY = 3.f;

protected:

    // ====== 委托绑定方法 ======
    
    UFUNCTION()
    void OnHealthChanged(float CurrentHP, float MaxHP);

    UFUNCTION()
    void OnDeathDelegate();
};
```

### 4.3 实现文件关键方法

#### BeginPlay() — 初始化流程

```cpp
void AEnemyBase::BeginPlay()
{
    Super::BeginPlay();

    // 1. 确保 AttributeComp 存在
    if (AttributeComp)
    {
        // 绑定生命变化委托（和 UI 监听 AttributeComp 是同一套模式）
        AttributeComp->OnHealthChanged.AddDynamic(this, &AEnemyBase::OnHealthChanged);
        AttributeComp->OnCharacterDeath.AddDynamic(this, &AEnemyBase::OnDeathDelegate);
        
        // 从 EnemyData 初始设置 HP
        if (EnemyData)
        {
            AttributeComp->SetMaxHealth(EnemyData->MaxHealth);
            AttributeComp->SetHealth(EnemyData->MaxHealth);
        }
    }

    // 2. 应用 EnemyData 配置的速度、外观等
    ApplyEnemyDataSettings();
    ApplyAppearanceFromData();
}
```

#### PerformAttack() — 对齐 UseHeldItem() 模式

```cpp
void AEnemyBase::PerformAttack()
{
    // 条件守卫
    if (bIsDead || !IsAlive()) return;          // 已死
    if (!EnemyData || !EnemyData->AttackMontage) return;  // 无配置
    
    // 冷却检查
    float CurrentTime = GetWorld()->GetTimeSeconds();
    if (CurrentTime - LastAttackTime < EnemyData->AttackCooldown) return;
    
    // 标记状态
    bIsAttacking = true;
    LastAttackTime = CurrentTime;

    // 播放攻击 Montage（和 UseHeldItem() 完全一样的模式）
    float Duration = PlayAnimMontage(EnemyData->AttackMontage);

    if (Duration <= 0.f)
    {
        // 没有 Montage 或播放失败 → 直接执行伤害
        ExecuteMeleeDamage();
        bIsAttacking = false;
    }
    // 有 Montage → 等 AnimNotify 触发 OnAttackAnimNotify()
    // Montage 结束时会自然重置 bIsAttacking（或通过 OnMontageEnded 回调）
}

// ★★ AnimNotify 回调入口（和 OnUseItemAnimFinished() 同一模式）★★
void AEnemyBase::OnAttackAnimNotify()
{
    ExecuteMeleeDamage();
    // 注意：bIsAttacking 重放在 MontageEnded 回调或 Tick 中处理
    // 这样确保整个攻击动画期间不会被中断
}
```

#### ExecuteMeleeDamage() — 核心攻击检测（完善你的 MeleeHitCheck 预留）

```cpp
void AEnemyBase::ExecuteMeleeDamage()
{
    if (!TargetActor || !EnemyData) return;

    // === SphereTrace 攻击检测 ===
    FVector Start = AttackOrigin ? AttackOrigin->GetComponentLocation() : GetActorLocation();
    Start.Z += EnemyData->AttackZOffset;  // Z 轴偏移
    
    FVector ForwardDir = GetActorForwardVector();
    FVector End = Start + ForwardDir * EnemyData->AttackForwardOffset;

    FCollisionQueryParams Params;
    Params.AddIgnoredActor(this);          // 忽略自己

    FHitResult HitResult;
    bool bHit = GetWorld()->SweepSingleByChannel(
        HitResult,
        Start,
        End,
        FQuat::Identity,
        ECC_Pawn,                          // 或用项目自定义的碰撞通道
        FCollisionShape::MakeSphere(EnemyData->AttackSphereRadius),
        Params
    );

    // === 命中判定 ===
    if (bHit && HitResult.GetActor())
    {
        AActor* HitActor = HitResult.GetActor();
        
        // ★★★ 和火球 ProcessHit 完全相同的伤害调用方式 ★★★
        if (UAttributeComponent* TargetAttr = HitActor->FindComponentByClass<UAttributeComponent>())
        {
            TargetAttr->ApplyDamage(EnemyData->AttackDamage, this);
            
            // 可选: 击退效果
            if (EnemyData->KnockbackForce > 0.f)
            {
                FVector KnockbackDir = (HitActor->GetActorLocation() - GetActorLocation()).GetSafeNormal2D();
                KnockbackDir.Z = 0.3f;  // 轻微向上
                
                // 对 Character 类型施加冲量
                if (ACharacter* HitChar = Cast<ACharacter>(HitActor))
                {
                    HitChar->LaunchCharacter(KnockbackDir * EnemyData->KnockbackForce, true, true);
                }
            }
        }

        // 可选: 蓝图扩展点（给美术加 VFX/Sound）
        BP_OnEnemyAttackHit(HitResult);   // 蓝图中可实现
    }
}
```

#### Die() — 死亡处理

```cpp
void AEnemyBase::Die()
{
    if (bIsDead) return;
    bIsDead = true;
    bIsAttacking = false;

    // 停止移动和所有行为
    GetCharacterMovement()->StopMovementImmediately();

    // 播放死亡动画
    if (EnemyData && EnemyData->DeathMontage)
    {
        float Duration = PlayAnimMontage(EnemyData->DeathMontage);
        if (Duration <= 0.f)
        {
            Duration = 1.f;  // 最小等待
        }
        DeathDestroyTimer = Duration + DEATH_DESTROY_DELAY;
    }
    else
    {
        // 无死亡动画 → 快速消失
        DeathDestroyTimer = 0.5f;
    }

    // 碰撞禁用（防止死后还能被攻击/阻挡）
    GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);

    // 可选: 死亡音效
    if (EnemyData && EnemyData->DeathSound)
    {
        UGameplayStatics::PlaySoundAtLocation(this, EnemyData->DeathSound, GetActorLocation());
    }

    // 可选: 蓝图扩展点
    BP_OnEnemyDeath();  // 蓝图中可做掉落物/VFX 等

    // 通知 AIController 停止
    if (AEnemyAIController* EAICon = Cast<AEnemyAIController>(GetController()))
    {
        EAICon->OnOwnerDied();
    }

    // Tick 中处理延迟销毁
}

// Tick 中的死亡销毁逻辑
if (bIsDead)
{
    DeathDestroyTimer -= DeltaTime;
    if (DeathDestroyTimer <= 0.f)
    {
        Destroy();
    }
    return;  // 死亡后不再执行其他逻辑
}
```

---

## 五、Phase 3: AnimNotify_EnemyAttack（攻击通知）

### 5.1 设计思路

**完全对齐现有的 AnimNotify_Fireball 和 AnimNotify_UseItemComplete 模式**：

```
AnimNotify_Fireball::Notify()     → PlayerChar->FireFromHand()
AnimNotify_UseItemComplete::Notify() → PlayerChar->OnUseItemAnimFinished()
AnimNotify_EnemyAttack::Notify()  → EnemyBase->OnAttackAnimNotify()
                                      ↓
                                 ExecuteMeleeDamage()
```

### 5.2 实现

```cpp
// 文件: AnimNotify_EnemyAttack.h
#pragma once
#include "CoreMinimal.h"
#include "Animation/AnimNotifies/AnimNotify.h"
#include "AnimNotify_EnemyAttack.generated.h"

/**
 * 敌人攻击帧通知
 * 
 * 在攻击 Montage 的精确帧放置此 Notify，
 * 当动画播到此帧时自动触发敌人的实际伤害检测。
 * 
 * 使用方式:
 *   1. 打开攻击 Montage（如 M_SlimeAttack）
 *   2. 在 Notify Track 上找到挥砍/爪击的那一帧
 *   3. 添加此 Notify
 *   4. 到达该帧时自动调用 AEnemyBase::OnAttackAnimNotify()
 */
UCLASS()
class INTROCPP_API UAnimNotify_EnemyAttack : public UAnimNotify
{
    GENERATED_BODY()

public:
    virtual void Notify(
        USkeletalMeshComponent* MeshComp,
        UAnimSequenceBase* Animation,
        const FAnimNotifyEventReference& EventReference
    ) override;
};
```

```cpp
// 文件: AnimNotify_EnemyAttack.cpp
#include "AnimNotify_EnemyAttack.h"
#include "EnemyBase.h"

void UAnimNotify_EnemyAttack::Notify(
    USkeletalMeshComponent* MeshComp,
    UAnimSequenceBase* Animation,
    const FAnimNotifyEventReference& EventReference)
{
    Super::Notify(MeshComp, Animation, EventReference);

    // 安全检查
    if (!MeshComp) return;

    // 获取 owning Actor
    AActor* Owner = MeshComp->GetOwner();
    if (!Owner) return;

    // 尝试转换为 AEnemyBase 并调用攻击通知
    // （和 AnimNotify_UseItemComplete 完全相同的模式）
    if (AEnemyBase* Enemy = Cast<AEnemyBase>(Owner))
    {
        Enemy->OnAttackAnimNotify();
    }
}
```

---

## 六、Phase 4: EnemyAIController（AI 控制器）

### 6.1 设计思路

采用**简单状态机**（C++ enum switch），适合初学者理解。预留升级为 BehaviorTree 的接口。

### 6.2 状态机定义

```
状态转换图:

  Patrol（巡逻）
    │  │
    │  └─ CanSeeTarget() == true ──→ Chase（追击）
    │
  Chase（追击）
    │  │
    ├─ IsTargetInRange(AttackRange) == true ──→ Attack（攻击）
    │
    └─ CanSeeTarget() == false ──────────────→ Patrol（巡逻）
       （带 ChaseLeewayTime 延迟防抖动）

  Attack（攻击）
    │  │
    ├─ 目标脱离 AttackRange + GraceTime ──→ Chase（追击）
    │
    └─ 目标死亡 ───────────────────────────→ Patrol（巡逻）

  Dead（死亡）← 任何状态收到 OnOwnerDied()
```

### 6.3 头文件

```cpp
// 文件: EnemyAIController.h
#pragma once
#include "AIController.h"
#include "EnemyAIController.generated.h"

class AEnemyBase;

/**
 * 敌人 AI 控制器
 * 
 * 使用简单的有限状态机（FSM）驱动敌人行为。
 * 状态: Patrol → Chase → Attack → Dead
 * 
 * 扩展方向:
 *   - 当前: 简单 FSM（适合初学者/小规模敌人）
 *   - 未来: 升级为 BehaviorTree（替换 UpdateState 为 BT 任务）
 */
UCLASS()
class INTROCPP_API AEnemyAIController : public AAIController
{
    GENERATED_BODY()

public:
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaTime) override;
    virtual void OnPossess(APawn* InPawn) override;

    /** 当控制的敌人死亡时调用（停止 AI 行为） */
    UFUNCTION(BlueprintCallable, Category = "AI")
    void OnOwnerDied();

protected:

    // ====== 状态枚举 ======
    
    UENUM(BlueprintType)
    enum class EAIState : uint8
    {
        Patrol,     // 巡逻/闲置
        Chase,      // 追击玩家
        Attack,      // 攻击
        Dead         // 死亡
    };

    /** 当前状态 */
    EAIState CurrentState = EAIState::Patrol;


    // ====== 状态更新入口 ======
    
    /** 每一帧根据条件决定是否转换状态 */
    void UpdateState(float DeltaTime);


    // ====== 各状态的行为逻辑 ======
    
    void State_Patrol(float DeltaTime);
    void State_Chase(float DeltaTime);
    void State_Attack(float DeltaTime);
    void State_Dead(float DeltaTime);


    // ====== 巡逻相关 ======
    
    FVector PatrolCenter;           // 巡逻中心点（出生位置）
    FVector CurrentPatrolTarget;    // 当前巡逻目标点
    float WaitTimer = 0.f;          // 到达目标点的等待计时
    bool bWaitingAtPatrolPoint = false; // 是否正在等待


    // ====== 感知辅助 ======
    
    /** 检测能否看到目标（视线检测 + 距离检测） */
    bool CanSeeTarget() const;

    /** 获取一个随机巡逻点（在 PatrolRadius 内） */
    FVector GetRandomPatrolPoint() const;


    // ====== 追击丢失防抖动 ======
    
    float LostTargetTimer = 0.f;    // 丢失目标的累计时间


    // ====== 辅助获取 ======
    
    /** 获取控制的敌人（安全转换） */
    AEnemyBase* GetEnemyPawn() const;
};
```

### 6.4 各状态行为详解

#### State_Patrol — 巡逻

```cpp
void AEnemyAIController::State_Patrol(float DeltaTime)
{
    AEnemyBase* Enemy = GetEnemyPawn();
    if (!Enemy || !Enemy->IsAlive()) return;
    
    UEnemyData* Data = Enemy->EnemyData;
    if (!Data) return;

    // 正在等待？
    if (bWaitingAtPatrolPoint)
    {
        WaitTimer -= DeltaTime;
        
        // 等待时原地旋转面向玩家方向（如果能看到的话）
        if (CanSeeTarget())
        {
            // 面向目标但不移动（警戒状态）
            FVector ToTarget = GetPawn()->GetActorLocation() - GetFocalPoint();
            SetFocalPoint(GetPawn()->GetActorLocation() - ToTarget);
        }
        
        if (WaitTimer <= 0.f)
        {
            bWaitingAtPatrolPoint = false;
            CurrentPatrolTarget = GetRandomPatrolPoint();  // 选下一个巡逻点
        }
        return;  // 等待期间不移动
    }

    // 向当前巡逻目标移动
    float DistToTarget = FVector::Dist2D(GetPawn()->GetActorLocation(), CurrentPatrolTarget);
    
    if (DistToTarget < 50.f)  // 到达巡逻点
    {
        bWaitingAtPatrolPoint = true;
        WaitTimer = Data->WaitTimeAtPatrolPoint;
        StopMovement();
    }
    else
    {
        // 使用 UE 的 AIMoveTo 移动
        MoveToLocation(CurrentPatrolTarget, -1.f, true, true);  // AcceptPartialPath
    }
}
```

#### State_Chase — 追击

```cpp
void AEnemyAIController::State_Chase(float DeltaTime)
{
    AEnemyBase* Enemy = GetEnemyPawn();
    if (!Enemy || !Enemy->IsAlive()) return;

    APawn* TargetPawn = GetPawn<AActor>();
    if (!TargetPawn) return;

    // 移动到目标位置
    MoveToActor(TargetPawn, EnemyData ? EnemyData->AttackRange : 150.f);
    
    // 丢失目标检测（带防抖动）
    if (!CanSeeTarget())
    {
        LostTargetTimer += DeltaTime;
        float Leeway = (EnemyData) ? EnemyData->ChaseLeewayTime : 1.f;
        if (LostTargetTimer >= Leeway)
        {
            // 丢失太久 → 回到巡逻
            ChangeState(EAIState::Patrol);
            LostTargetTimer = 0.f;
            ClearFocus(EAIFocusBehavior::Move);
        }
    }
    else
    {
        LostTargetTimer = 0.f;  // 重置丢失计时
    }
}
```

#### State_Attack — 攻击

```cpp
void AEnemyAIController::State_Attack(float DeltaTime)
{
    AEnemyBase* Enemy = GetEnemyPawn();
    if (!Enemy || !Enemy->IsAlive()) return;

    APawn* TargetPawn = GetPawn<AActor>();
    if (!TargetPawn) return;

    // 面向目标
    SetFocus(TargetPawn);

    // 停止移动（站在原地攻击）
    StopMovement();

    // 检查目标是否还在攻击范围内
    float Distance = FVector::Dist(GetPawn()->GetActorLocation(), TargetPawn->GetActorLocation());
    float AttackRange = (EnemyData) ? EnemyData->AttackRange : 150.f;

    if (Distance > AttackRange * 1.2f)  // 给一点容差
    {
        // 目标脱离了攻击范围 → 回到追击
        ChangeState(EAIState::Chase);
        return;
    }

    // 目标还活着吗？
    if (UAttributeComponent* TargetAttr = TargetPawn->FindComponentByClass<UAttributeComponent>())
    {
        if (!TargetAttr->IsAlive())
        {
            // 目标已死 → 回到巡逻
            ChangeState(EAIState::Patrol);
            ClearFocus(EAIFocusBehavior::Move);
            return;
        }
    }

    // 执行攻击（冷却由 EnemyBase.PerformAttack() 内部控制）
    Enemy->PerformAttack();
}
```

---

## 七、完整战斗交互流程

### 7.1 敌人攻击玩家的完整链路

```
AIController.Tick()
  → State_Attack() 每帧检查
    → EnemyBase->PerformAttack()
      → 检查冷却 → bIsAttacking = true
      → PlayAnimMontage(AttackMontage)
      → ... 动画播放中 ...
      → [到达 Notify 所在帧]
        → AnimNotify_EnemyAttack::Notify()
          → EnemyBase->OnAttackAnimNotify()
            → ExecuteMeleeDamage()
              → SphereTrace (忽略自身)
              → 命中玩家 Actor
              → FindComponentByClass<UAttributeComponent>()  ← 和火球同一模式
              → Attr->ApplyDamage(EnemyData->AttackDamage, this)
              → 玩家 HP 减少 → 触发 OnHealthChanged → UI 血条刷新
              → 如果 HP ≤ 0 → 触发 OnCharacterDeath → 玩家死亡
      → [Montage 播放完毕]
        → bIsAttacking = false
```

### 7.2 玩家攻击敌人的完整链路

```
玩家按攻击键
  → MyPlayerCharacter::AttackStarted()
    → Attack()
      → PlayAnimMontage(...)
        → [到达 Notify 帧]
          → AnimNotify_Fireball::Notify()
            → FireFromHand() / MeleeHitCheck()
              → LineTrace/Sweep 检测命中
              → 命中敌人 Actor (AEnemyBase*)
              → EnemyBase->AttributeComp->ApplyDamage(PlayerDamage, PlayerChar)
                → Enemy HP 减少
                  → OnHealthChanged.Broadcast(Current, Max)
                    → AEnemyBase::OnHealthChanged() 接收
                      → 可选: 播放受击动画 HitReactMontage
                      → 可选: 播放受击音效 HitSound
                  → 如果 HP ≤ 0
                    → OnCharacterDeath.Broadcast()
                      → AEnemyBase::OnDeathDelegate() 接收
                        → Die()
                          → 播放死亡动画
                          → 禁用碰撞
                          → 死亡音效
                          → BP_OnEnemyDeath() → 可做掉落物
                          → 延迟 Destroy()
                          → AIController::OnOwnerDied() → 停止 AI
```

---

## 八、编辑器配置流程

### 8.1 创建敌人蓝图

```
步骤1: Content Browser 右键 → Blueprint Class

步骤2: 选择父类:
      └─ All Classes → 搜索 "Enemy Base" → 选择 AEnemyBase

步骤3: 命名: BP_Enemy_Slime

步骤4: 打开 BP_Enemy_Slime，在 Defaults 面板:

+-- BP_Enemy_Slime Defaults -------------------------------------------+
| Config                                                              |
|   Enemy Data     [ DA_Enemy_Slime        ]  ← 拖入对应的数据资产     |
|                                                                      |
| Components (已自动创建)                                              |
|   Attribute Comp   [ UAttributeComponent ]                           |
|   Attack Origin    [ USceneComponent      ]                           |
|                                                                      |
| Character (ACharacter 默认)                                          |
|   Capsule Component  → 调整高度/半径适配敌人模型                     |
|   Mesh               → 替换或留空（EnemyData 中也可配）             |
+---------------------------------------------------------------------+

步骤5: 编译 + 保存

步骤6: 关卡中拖入 BP_Enemy_Slime 实例
```

### 8.2 配置攻击 Montage 的 Notify

```
步骤1: 双击打开攻击 Montage（如 M_SlimeAttack）

步骤2: 在底部 Notify Track 上找到武器挥下的那一帧
      （通常是抬手之后、手落下的瞬间）

步骤3: 右键 Notify Track → Add Notify → 选择 'Enemy Attack'

步骤4: 保存 Montage

结果: 动画播到这一帧时自动触发 SphereTrace 伤害检测
```

### 8.3 GameMode 配置（让敌人自动获得 AI Controller）

```
方案A（推荐）: 在 EnemyBase 的构造函数中指定:
    AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;

方案B: 在关卡中选中 BP_Enemy_Slime 实例:
    Details → Pawn → Auto Possess AI → Placed in World or Spawned
```

---

## 九、未来可扩展路线图

### 9.1 短期扩展（不改架构即可实现）

| 功能 | 实现方式 | 说明 |
|------|---------|------|
| **多种敌人子类** | 继承 AEnemyBase | ASlimeEnemy / AGoblinEnemy / ABossEnemy，覆写特定方法 |
| **掉落物系统** | Die() 中 SpawnActor | 读取 EnemyData 或新增 DropTable 字段 |
| **受击硬直** | OnReceiveDamage() 加短暂眩晕 | 播放 HitReactMontage + 短暂禁用 AI |
| **音效/VFX** | BP_OnEnemyAttackHit / BP_OnEnemyDeath | 蓝图中实现，无需改 C++ |
| **巡逻路径点** | EnemyData 加 TArray<FVector> Waypoints | 替代随机巡逻 |

### 9.2 中期扩展（需新增模块）

| 功能 | 实现方式 | 说明 |
|------|---------|------|
| **远程敌人** | 子类化 ExecuteMeleeDamage | ARangedEnemy 覆写为生成投射物 |
| **BehaviorTree 升级** | 替换 AIController 的 Tick 状态机 | 更复杂的决策树 |
| **AIPerception 系统** | UAIPerceptionComponent | 视觉+听觉感知，替代简单距离检测 |
| **技能系统** | EnemyData 加 TArray<USkillData*> | 多段攻击/范围技能/Buff 技能 |
| **精英/Buff 变体** | 蓝图基于 DA_Enemy_Goblin 创建 DA_Elite_Goblin | 只覆写部分字段 |

### 9.3 远期扩展（架构级改动）

| 功能 | 说明 |
|------|------|
| **网络同步** | Replicate 属性 + Server-RPC 验证攻击 |
| **SaveSystem 集成** | 记录已击杀的敌人 |
| **对话/任务系统** | EnemyData 加 QuestID / DialogTree 引用 |
| **组队行为** | AI Controller 间通信，包围/协攻 |

---

## 十、文件改动汇总

| 文件 | 操作 | 内容 | 行数估算 |
|------|------|------|---------|
| `EnemyData.h` | **新建** | UPrimaryDataAsset 敌人数据基类 | ~170行 |
| `EnemyBase.h` | **新建** | 敌人基类声明 | ~130行 |
| `EnemyBase.cpp` | **新建** | 敌人基类实现 | ~300行 |
| `AnimNotify_EnemyAttack.h` | **新建** | 攻击帧通知声明 | ~18行 |
| `AnimNotify_EnemyAttack.cpp` | **新建** | 攻击帧通知实现 | ~22行 |
| `EnemyAIController.h` | **新建** | AI 控制器声明 | ~90行 |
| `EnemyAIController.cpp` | **新建** | AI 控制器实现 | ~280行 |
| **DA_Enemy_xxx** | **编辑器** | 敌人数据资产实例 | 每个 ~10项配置 |

---

## 十一、与现有代码的对接清单

### 需要修改的现有文件

| 文件 | 修改内容 | 原因 |
|------|---------|------|
| `IntroCpp.Build.cs` | 无需额外添加依赖 | AIModule 已存在；新文件在同一 Module 下 |
| `.uproject` | 无需添加插件 | 不需要新的 Plugin 依赖 |
| `MyPlayerCharacter.h/.cpp` | 可能需要在 `MeleeHitCheck()` 中加入敌人检测 | 完善 MeleeHitCheck 使其也能伤害敌人 |

### 完全不需要修改的现有文件

| 文件 | 为什么不动 |
|------|-----------|
| `AttributeComponent.h/.cpp` | 直接复用，无需任何改动 |
| `AFireballProjectile.h/.cpp` | 作为伤害参考模式，不需改 |
| `InventoryComponent.*` | 敌人不涉及背包 |
| `UI 相关文件` | 敌人血条是独立功能，后续再加 |
| `AnimNotify_Fireball/UseItemComplete` | 平行存在，互不影响 |
