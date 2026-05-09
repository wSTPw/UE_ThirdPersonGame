// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "ItemDataBase.h"       // UItemDataBase 基类
#include "EWeaponTypes.h"      // EWeaponAnimType 枚举
#include "Animation/AnimMontage.h"
#include "WeaponData.generated.h"

/**
 * UWeaponData — 武器数据子类（继承 UItemDataBase）
 *
 * 扩展武器专属的战斗属性：投射物类型、动画模式、伤害参数等。
 * 只有装备武器或执行攻击时才需要访问这些字段。
 *
 * 典型用途：DA_WP_FireStaff、DA_WP_Sword 等 DataAsset 资产。
 */
UCLASS(Blueprintable)
class INTROCPP_API UWeaponData : public UItemDataBase
{
	GENERATED_BODY()

public:
	// 使用 C++11 成员默认值 + 内联构造函数，无需 .cpp 文件
	UWeaponData();

	// ==========================================
	// 战斗属性
	// ==========================================

	/** 投射物 Actor 类（软引用），远程武器发射时 Spawn 的蓝图类 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
	TSoftClassPtr<AActor> WeaponProjectileClass;

	/** 攻击动画类型 — 决定从角色的 AttackMontageMap 中取哪个共享 Montage */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
	EWeaponAnimType WeaponAnimType = EWeaponAnimType::None;

	/** 是否为远程武器（true=投射物, false=近战） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
	bool bIsRangedWeapon = true;

	/** 单次攻击消耗的法力值 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
	float WeaponManaCost = 0.0f;

	/** 伤害覆盖值（0=使用投射物默认伤害，非0则覆盖） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
	int32 WeaponDamageOverride = 0;

	/** 发射位置的 Socket 名称 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
	FName WeaponFireSocketName = TEXT("hand_r");

	/** 攻击冷却时间（秒） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
	float WeaponAttackCooldown = 0.5f;

	/** 专属蒙太奇（空=走枚举→AttackMontageMap，非空=优先用此 Montage）
	 *  仅 1% 特殊武器需要，99% 的普通武器留空即可 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
	UAnimMontage* OverrideAttackMontage = nullptr;

	// ==========================================
	// 外观
	// ==========================================

	/** 武器 StaticMesh（软引用，装备时附加到角色手部 Socket） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Appearance")
	TSoftObjectPtr<UStaticMesh> WeaponStaticMesh;

	/** 手部 Socket 名称（默认 "RightHand"，与骨骼一致即可） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Appearance")
	FName HandSocketName = TEXT("RightHand");

	/** 武器模型缩放（默认 1,1,1，调小数值=缩小模型） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Appearance")
	FVector WeaponScale = FVector(1.0f, 1.0f, 1.0f);
};

// ---- 内联构造函数（无需 .cpp）----
inline UWeaponData::UWeaponData()
{
	ItemType = EItemType::Weapon;
}
