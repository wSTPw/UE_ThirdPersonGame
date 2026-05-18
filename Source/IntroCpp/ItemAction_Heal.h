#pragma once

#include "ItemAction.h"
#include "ItemAction_Heal.generated.h"

/**
 * UItemAction_Heal — 治疗效果 Action
 *
 * 使用物品时恢复角色生命值。
 *
 * 【配置来源】
 * InitializeFromItemData() 从 UConsumableData.HealthRestore 读取回复量。
 * 如果 DataAsset 的 HealthRestore > 0，则覆盖编辑器中 HealAmount 的默认值。
 * 这样设计允许：同一个 BP_Action_Heal 类被多个不同药水复用，
 * 每个药水通过自己的 HealthRestore 字段控制具体回复多少。
 *
 * 【执行效果】
 * Execute() → Instigator.FindComponentByClass<UAttributeComponent>() → ApplyHeal(HealAmount)
 * 成功返回 true（标记为已消费）, 失败返回 false
 */
UCLASS(Blueprintable)
class INTROCPP_API UItemAction_Heal : public UItemAction
{
	GENERATED_BODY()

public:

	/** 回复的生命值点数。可在蓝图编辑器或 DataAsset 中覆盖 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Heal")
	int32 HealAmount = 20;

	/** 从 UConsumableData 读取 HealthRestore 来初始化 HealAmount */
	virtual void InitializeFromItemData(const UItemDataBase* ItemData) override;

	/** 执行治疗效果：调用 AttributeComponent.ApplyHeal() */
	virtual bool Execute_Implementation(UInventoryComponent* Inventory, int32 SlotIndex, AActor* Instigator) override;
};
