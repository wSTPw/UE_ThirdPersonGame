// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "EWeaponTypes.generated.h"

/** 攻击动画类型 — 决定使用哪个共享 Montage
 *  按动作模式归类而非按武器种类，多把武器可共用同一动画 */
UENUM(BlueprintType)
enum class EWeaponAnimType : uint8
{
	Cast_1H		UMETA(DisplayName = "单手施法"),
	Cast_2H		UMETA(DisplayName = "双手施法"),
	Slash_1H	UMETA(DisplayName = "单手挥砍"),
	Slash_2H	UMETA(DisplayName = "双手挥砍"),
	Thrust		UMETA(DisplayName = "刺击"),
	Shoot		UMETA(DisplayName = "射箭/射击"),
	None		UMETA(DisplayName = "无攻击动作")
};

/** Buff 类型 — 供消耗品（UConsumableData）和未来技能系统使用 */
UENUM(BlueprintType)
enum class EBuffType : uint8
{
	None			UMETA(DisplayName = "无"),
	Regeneration	UMETA(DisplayName = "持续恢复"),
	Speed			UMETA(DisplayName = "加速"),
	Defense		UMETA(DisplayName = "防御增强")
};
