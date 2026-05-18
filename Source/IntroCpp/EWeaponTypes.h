// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "EWeaponTypes.generated.h"

/**
 * 攻击动画类型枚举
 *
 * 按"动作模式"而非"武器种类"归类，多把不同武器可共用同一套动画。
 * 角色的 AttackMontageMap 存储了每种类型对应的 UAnimMontage*，
 * 武器装备时通过此枚举值从 Map 中取出对应 Montage。
 *
 * 示例：
 *   Cast_1H  → 单手法杖施法（火球术）
 *   Slash_1H → 单手剑挥砍（铁剑、钢剑通用）
 *   Shoot    → 弓箭/枪械射击动作
 */
UENUM(BlueprintType)
enum class EWeaponAnimType : uint8
{
	Cast_1H		UMETA(DisplayName = "单手施法"),     // 一只手施放法术（法杖、魔导书）
	Cast_2H		UMETA(DisplayName = "双手施法"),     // 双手大型法术（法球、大魔导书）
	Slash_1H	UMETA(DisplayName = "单手挥砍"),     // 单手近战挥砍（匕首、剑、斧）
	Slash_2H	UMETA(DisplayName = "双手挥砍"),     // 双手武器挥砍（巨剑、长枪、大锤）
	Thrust		UMETA(DisplayName = "刺击"),         // 直线突刺攻击（长矛、刺剑）
	Shoot		UMETA(DisplayName = "射箭/射击"),    // 远程投射物发射（弓弩、火器）
	None		UMETA(DisplayName = "无攻击动作")    // 无攻击能力（工具类物品）
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
