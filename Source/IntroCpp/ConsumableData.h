// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "ItemDataBase.h"       // UItemDataBase 基类（继承目标）
#include "EWeaponTypes.h"        // EBuffType 枚举（BuffType 字段需要）
#include "Animation/AnimMontage.h" // UAnimMontage（UseMontage 需要）
#include "ConsumableData.generated.h"

/**
 * UConsumableData — 消耗品类物品数据子类
 *
 * 继承自 UItemDataBase，扩展消耗品特有的效果属性。
 *
 * 【典型用途】
 *   - 生命药水 (DA_HP_Potion)：HealthRestore=50
 *   - 魔法药水 (DA_MP_Potion)：ManaRestore=30
 *   - 回复药剂 (DA_RegenPotion)：BuffType=Regeneration, BuffDuration=10s
 *
 * 【使用流程】
 *   1. 玩家右键/快捷栏 → InventoryComponent::UseItem()
 *   2. 加载 ItemActionClasses 列表中的 Action
 *   3. Action->InitializeFromItemData(this) 读取 HealthRestore/ManaRestore 到 Action 成员变量
 *   4. Action->Execute() 调用 AttributeComponent.ApplyHeal() / RestoreMana()
 *   5. 返回 true → UseItem 执行 RemoveItemAt(SlotIndex, 1) 扣减数量
 *
 * 【在编辑器中创建】
 *   右键 → Miscellaneous → Data Asset → 选择 ConsumableData 类
 */
UCLASS(Blueprintable)
class INTROCPP_API UConsumableData : public UItemDataBase
{
	GENERATED_BODY()

public:
	/* 使用内联构造函数（实现直接写在头文件），无需额外 .cpp 文件 */
	UConsumableData();

	// ==========================================
	// 消耗品效果属性
	// ==========================================

	/** 使用后恢复的生命值。由 ItemAction_Heal::InitializeFromItemData() 读取 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Effect")
	int32 HealthRestore = 0;

	/** 使用后恢复的魔法值。由 ItemAction_RestoreMana::InitializeFromItemData() 读取 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Effect")
	int32 ManaRestore = 0;

	/**
	 * Buff 类型。
	 * None = 无额外效果（仅回血/回蓝）
	 * 其他值 = 使用后附加对应 Buff（需未来扩展 BuffSystem 支持）
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Effect")
	EBuffType BuffType = EBuffType::None;

	/**
	 * Buff 持续时间（秒）。
	 * 仅当 BuffType != EBuffType::None 时有效（EditCondition 条件显示控制）
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Effect", meta = (EditCondition = "BuffType != EBuffType::None"))
	float BuffDuration = 0.0f;

	/**
	 * Buff 数值强度。
	 * 具体含义取决于 BuffType：
	 *   Regeneration → 每秒回复量
	 *   Speed        → 移速加成百分比
	 *   Defense      → 防御加成数值
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Effect", meta = (EditCondition = "BuffType != EBuffType::None"))
	float BuffValue = 0.0f;

	// ==========================================
	// 动作表现
	// ==========================================

	/**
	 * 使用动画 Montage。
	 * 右键长按使用消耗品时播放的角色动画（如"喝药水"、"吃食物"动作）。
	 * 动画播完后通过 AnimNotify_UseItemComplete 通知角色执行实际效果。
	 * 留空 = 不播放动画，立即执行效果（适合瞬发物品）
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animation")
	UAnimMontage* UseMontage = nullptr;
};

// ---- 内联构造函数：自动设置 ItemType 为消耗品 ----
inline UConsumableData::UConsumableData()
{
	ItemType = EItemType::Consumable;
}
