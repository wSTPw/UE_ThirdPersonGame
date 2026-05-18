// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "EEnemyTypes.h"
#include "Animation/AnimMontage.h"
#include "EnemyData.generated.h"

/**
 * 敌人数据资产 (PrimaryDataAsset)
 *
 * 每种敌人的数值配置都在这里。
 * 在 Content Browser 中右键 → Miscellaneous → Data Asset → 选择此类 即可创建实例。
 *
 * 示例: DA_Enemy_Slime, DA_Enemy_Goblin, DA_Enemy_Boss
 */
UCLASS(Blueprintable)
class INTROCPP_API UEnemyData : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:

	// ==========================================
	// 基础属性 (Stats)
	// ==========================================

	/** 最大生命值 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Stats")
	float MaxHealth = 100.f;

	/** 每次攻击造成的伤害 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Stats")
	float AttackDamage = 15.f;

	/** 击退力度（0=不击退）*/
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Stats")
	float KnockbackForce = 500.f;


	// ==========================================
	// 移动行为 (Movement)
	// ==========================================

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


	// ==========================================
	// 巡逻设置 (Patrol)
	// ==========================================

	/** 巡逻半径（以初始位置为圆心） */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Patrol")
	float PatrolRadius = 800.f;

	/** 到达巡逻点后的等待时间（秒） */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Patrol")
	float WaitTimeAtPatrolPoint = 2.f;

	/** 巡逻行为类型 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Patrol")
	EPatrolType PatrolBehavior = EPatrolType::Random;


	// ==========================================
	// 战斗感知 (Combat Detection)
	// ==========================================

	/** 视觉感知半径（能看到玩家的最大距离） */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combat")
	float SightRadius = 1200.f;

	// 注意: 视觉记忆时间已统一使用 ChaseLeewayTime（由 AIPerception 的 SetMaxAge 驱动）

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


	// ==========================================
	// 攻击参数 (Attack Config)
	// ==========================================

	/** 攻击检测形状半径（SphereTrace 的球体大小） */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Attack")
	float AttackSphereRadius = 50.f;

	/** 攻击检测前方延伸距离（从角色位置向前量多少） */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Attack")
	float AttackForwardOffset = 80.f;

	/** 攻击检测的高度偏移（Z轴） */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Attack")
	float AttackZOffset = 0.f;


	// ==========================================
	// 动画 Montage（和玩家武器数据的 Montage 配置方式一致）
	// ==========================================

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


	// ==========================================
	// 外观资源 (Appearance)
	// ==========================================

	/**
	 * 骨骼网格体（SkeletalMesh 敌人适用）
	 * ACharacter 默认使用 SkeletalMeshComponent，这是主要的外观配置方式
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Appearance")
	USkeletalMesh* BodyMesh;

	/** 身体材质（覆盖默认材质） */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Appearance")
	UMaterialInterface* BodyMaterial;

	/** 缩放比例 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Appearance")
	FVector MeshScale = FVector(1.f);


	// ==========================================
	// 音效/VFX (Audio & VFX) — 编辑器可扩展
	// ==========================================

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
