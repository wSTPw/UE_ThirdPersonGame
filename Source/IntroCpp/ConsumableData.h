// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "ItemDataBase.h"
#include "EWeaponTypes.h"        // EBuffType 枚举
#include "ConsumableData.generated.h"

/**
 * UConsumableData — 消耗品类物品数据（继承 UItemDataBase）
 *
 * 扩展消耗品特有的属性：回复生命值 / 回复魔法值 / Buff 效果。
 * 典型用途：HP_Potion、MP_Potion、HP_Regen 等。
 */
UCLASS(Blueprintable)
class INTROCPP_API UConsumableData : public UItemDataBase
{
	GENERATED_BODY()

public:
	// 内联构造函数，无需 .cpp
	UConsumableData();

	/** 使用后恢复的生命值 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Effect")
	int32 HealthRestore = 0;

	/** 使用后恢复的魔法值 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Effect")
	int32 ManaRestore = 0;

	/** Buff 类型（None = 无额外效果） */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Effect")
	EBuffType BuffType = EBuffType::None;

	/** Buff 持续时间（秒），仅 BuffType != None 时有效 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Effect", meta = (EditCondition = "BuffType != EBuffType::None"))
	float BuffDuration = 0.0f;

	/** Buff 数值，仅 BuffType != None 时有效 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Effect", meta = (EditCondition = "BuffType != EBuffType::None"))
	float BuffValue = 0.0f;
	// ★ UseMontage 已在基类 UItemDataBase 中定义，无需重复声明（UHT 禁止 shadowing）
};

// ---- 内联构造函数 ----
inline UConsumableData::UConsumableData()
{
	ItemType = EItemType::Consumable;
}
