// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "EWeaponTypes.h"
#include "ComboAttackData.generated.h"

// 前向声明（避免拉入沉重的 Animation 模块头文件，此处只需指针)
class UAnimMontage;

/**
 * 子判定参数（FSubHitEntry）
 *
 * 当一段攻击内有多次独立伤害判定时使用。
 * 例如：双刀乱舞（左斩+右斩）、长枪三连刺、大剑横扫（近+远）等。
 *
 * 所有 Override 字段遵循统一约定：
 *   = 0（或等效默认值）→ 继承父级 FComboHitEntry 的对应值
 *   != 0                  → 使用此处的覆盖值，忽略父级
 */
USTRUCT(BlueprintType)
struct INTROCPP_API FSubHitEntry
{
	GENERATED_BODY()

	/** 伤害倍率覆盖。0 = 继承父级 HitEntry.DamageMultiplier */
	UPROPERTY(EditAnywhere, Category = "Sub-Hit Override")
	float DamageMultiplierOverride = 0.f;

	/** 判定半径覆盖（cm）。0 = 继承父级 HitEntry.AttackSphereRadius */
	UPROPERTY(EditAnywhere, Category = "Sub-Hit Override")
	float SphereRadiusOverride = 0.f;

	/** 向前偏移覆盖（cm）。0 = 继承父级 HitEntry.AttackForwardOffset */
	UPROPERTY(EditAnywhere, Category = "Sub-Hit Override")
	float ForwardOffsetOverride = 0.f;

	/** 击退力度覆盖。0 = 继承父级 HitEntry.KnockbackForce */
	UPROPERTY(EditAnywhere, Category = "Sub-Hit Override")
	float KnockbackOverride = 0.f;
};

/**
 * 单段攻击的完整参数包（FComboHitEntry）
 *
 * 每个 FComboHitEntry 代表连击序列中的一次独立攻击动作，
 * 包含动画定位、伤害数值、判定范围、击退效果、输入窗口等全部信息。
 *
 * 【普通模式】SubHits 为空（默认）：
 *   这段攻击只有 1 次 SphereTrace 判定，使用本结构体的主属性。
 *   适用场景：标准单次斩击、突刺、下劈等。
 *
 * 【多判定模式】SubHits 非空：
 *   这段攻击有 N 次独立判定，每次可单独覆盖伤害/范围/击退等参数。
 *   Montage 对应 Section 中需放 N 个 AnimNotify_MeleeHit，
 *   按 Notify 触发顺序依次读取 SubHits[0]、SubHits[1]...
 *   适用场景：双刀乱舞、长枪连刺、大剑多段横扫等。
 *
 * 【编辑器体验】
 *   SubHits 放在 AdvancedDisplay 面板中，普通配置时完全不可见，
 *   不影响日常数据填写流程。
 */
USTRUCT(BlueprintType)
struct INTROCPP_API FComboHitEntry
{
	GENERATED_BODY()

	// ====== 动画定位 ======

	/**
	 * 在 ComboAttackData.ComboMontage 中对应的 Section 名称
	 * 
	 * 例如："Hit1"、"Hit2"、"Hit3"
	 * 必须与 Montage 编辑器中的 Section 名完全一致（区分大小写）
	 */
	UPROPERTY(EditAnywhere, Category = "Animation")
	FName SectionName = TEXT("Hit1");

	// ====== 伤害数值 ======

	/** 基础伤害值。最终伤害 = BaseDamage × DamageMultiplier × 属性加成(未来) */
	UPROPERTY(EditAnywhere, Category = "Damage")
	float BaseDamage = 20.f;

	/** 伤害倍率。用于后段递增：Hit1=1.0x, Hit2=1.3x, Hit3=1.8x 等 */
	UPROPERTY(EditAnywhere, Category = "Damage")
	float DamageMultiplier = 1.0f;

	// ====== 判定参数 ======

	/** SphereTrace 检测半径（cm）。值越大判定范围越宽 */
	UPROPERTY(EditAnywhere, Category = "Detection")
	float AttackSphereRadius = 50.f;

	/**
	 * 判定点向前偏移距离（cm）
	 * 从角色位置沿 ForwardVector 偏移此距离作为 SphereTrace 的终点
	 * 长武器应设较大值（如 80~100），短武器设较小值（如 40~60）
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
	 * 在此时间之前按下攻击键会被忽略（处于攻击预备/蓄力期）
	 * 通常设在"蓄力完毕、即将出刀"的时刻
	 */
	UPROPERTY(EditAnywhere, Category = "Input Window")
	float HitWindowStart = 0.3f;

	/**
	 * 窗口关闭参考时间（相对本段攻击开始，单位：秒）
	 * 注意：实际窗口关闭由 MontageEnded 回调决定，
	 * 此值仅作为编辑器中的参考标记，帮助策划把握手感节奏。
	 * 只要 Montage 结束前按下了就算有效输入
	 */
	UPROPERTY(EditAnywhere, Category = "Input Window")
	float HitWindowEnd = 0.8f;

	// ====== 子判定（高级可选）======

	/**
	 * 子判定列表
	 * 
	 * 空 = 单次判定模式（使用上面的一组主属性，绝大多数情况）
	 * 非空 = 多次独立判定模式（每项可覆盖部分属性）
	 * 
	 * @see FSubHitEntry 的文档了解详细用法
	 */
	UPROPERTY(EditAnywhere, AdvancedDisplay, Category = "Sub-Hits")
	TArray<FSubHitEntry> SubHits;
};

/**
 * 连击配置数据资产（UComboAttackData）
 *
 * 定义一套完整的近战连击序列参数。
 * 一把近战武器通过 WeaponData.MeleeComboData 引用一个此资产，
 * 多把同类武器可共享同一套连击配置。
 *
 * 【核心设计 — 动画挂载方式】
 * 使用"单 Montage + Section 跳转"模式：
 * - ComboMontage：一个 Montage 资产，内含多个 Section（Hit1/Hit2/...）
 * - Hits[].SectionName：指定每次攻击跳转到哪个 Section
 * - PlayAnimMontage(ComboMontage, 1.0f, SectionName) 播放对应段落
 * 
 * 好处：
 * 1. 整套连击只需 1 个 Montage 文件，编辑管理方便
 * 2. 可同时注册到角色 AttackMontageMap[WeaponAnimType] 作为非连击 fallback
 * 3. 同一 Montage 内 Section 间无缝切换（比跨 Montage Blend 更流畅）
 *
 * 【在编辑器中创建】
 * Content Browser → 右键 → Miscellaneous → Data Asset → 选择 ComboAttackData 类
 */
UCLASS()
class INTROCPP_API UComboAttackData : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:

	UComboAttackData();

	// ==========================================
	// 基本信息
	// ==========================================

	/** 连招名称（如"基础剑技三连"、"双刀乱舞五段"），用于日志和 UI 显示 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combo")
	FText ComboName;

	/** 对应的武器动画类型，用于识别和 fallback 匹配 AttackMontageMap */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combo")
	EWeaponAnimType WeaponAnimType = EWeaponAnimType::None;

	// ==========================================
	// 动画资源
	// ==========================================

	/**
	 * 整套连击序列的 Montage 资产（★ 核心字段，必填）
	 * 内含多个 Section（Hit1 / Hit2 / ...），每段对应一次攻击动作。
	 * 通过 Hits[].SectionName 指定播放哪一段。
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combo|Animation")
	UAnimMontage* ComboMontage = nullptr;

	// ==========================================
	// 连击序列配置
	// ==========================================

	/**
	 * 各段攻击配置列表
	 * 数组长度 = 连击段数（填 N 个元素就是 N 连击）
	 * 索引 0 = 第 1 段，索引 1 = 第 2 段，... 索引 N-1 = 最后一段
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combo|Hits")
	TArray<FComboHitEntry> Hits;

	// ==========================================
	// 全局行为设置
	// ==========================================

	/**
	 * 最后一段打完后是否循环回到第 1 段
	 * true  → 无限连击循环（适合快速轻武器如匕首、短剑）
	 * false → 打完最后一段后自然结束回到 Idle（默认，适合重武器）
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combo|Behavior")
	bool bLoopFromLastHit = false;

	/**
	 * 连击超时时间（秒）
	 * 从每次按下攻击键开始计时，超时未再按键 → 强制 ResetCombo 回到 Idle
	 * 推荐值：快速武器 1.0~1.2s，慢速重武器 1.3~1.8s
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combo|Behavior")
	float ComboResetTime = 1.0f;
};
