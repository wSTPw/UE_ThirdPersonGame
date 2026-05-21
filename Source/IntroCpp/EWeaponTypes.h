// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "EWeaponTypes.generated.h"

/**
 * 攻击动画类型枚举
 *
 * 按"动作模式"归类，不同武器可共用同一套动画。
 * 角色的 AttackMontageMap 存储了每种类型对应的 UAnimMontage*，
 * 武器装备时通过此枚举值从 Map 中取出对应 Montage。
 *
 * 同时驱动 ABP_Move 的 locomotion 混合空间切换。
 */
UENUM(BlueprintType)
enum class EWeaponAnimType : uint8
{
	None		UMETA(DisplayName = "无攻击"),    // 空手或无攻击能力的物品
	Staff		UMETA(DisplayName = "法杖"),      // 法杖类武器（施法动作）
	LongSword	UMETA(DisplayName = "长剑")       // 长剑类武器（挥砍动作）	
};

/**
 * Buff 类型枚举 — 供消耗品（UConsumableData）和未来技能系统使用
 *
 * 当前为预留字段，BuffSystem 完整实现后生效。
 * ItemAction 子类可根据此值决定执行哪种 Buff 效果。
 */
UENUM(BlueprintType)
enum class EBuffType : uint8
{
	None			UMETA(DisplayName = "无"),           // 无额外效果，仅回血回蓝
	Regeneration	UMETA(DisplayName = "持续恢复"),     // HP/MP 持续回复效果
	Speed			UMETA(DisplayName = "加速"),         // 移动速度临时提升
	Defense		UMETA(DisplayName = "防御增强")       // 伤害减免/护甲增强
};
