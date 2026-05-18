// Fill out your copyright notice in the Description page of Project Settings.

#include "ItemAction_Heal.h"
#include "GameFramework/Character.h"      // Cast<ACharacter> 检查
#include "AttributeComponent.h"           // ApplyHeal() 方法
#include "ConsumableData.h"               // UConsumableData (Cast 目标类型)

/**
 * 从物品 DataAsset 初始化治疗量
 *
 * 尝试将基类指针向下转型为消耗品子类，
 * 读取 HealthRestore 字段覆盖 HealAmount 默认值。
 * 这样每个药水 DataAsset 可以有不同的回复量而共享同一个 Action 类。
 */
void UItemAction_Heal::InitializeFromItemData(const UItemDataBase* ItemData)
{
	// 安全向下转型：UItemDataBase* → UConsumableData*
	if (const UConsumableData* ConsumableData = Cast<UConsumableData>(ItemData))
	{
		// 仅当 DataAsset 配置了有效的回复量时才覆盖（>0 表示有配置）
		if (ConsumableData->HealthRestore > 0)
		{
			HealAmount = ConsumableData->HealthRestore;
		}
	}
	// 如果 Cast 失败（不是消耗品类型），保持默认 HealAmount=20
}

/**
 * 执行治疗效果
 *
 * @return true = 治疗成功，物品应被消费
 *         false = 未找到 AttributeComponent 等失败情况
 */
bool UItemAction_Heal::Execute_Implementation(UInventoryComponent* Inventory, int32 SlotIndex, AActor* Instigator)
{
	if (!Instigator) return false;

	// 从触发者（角色）身上获取属性组件
	if (UAttributeComponent* AttrComp = Instigator->FindComponentByClass<UAttributeComponent>())
	{
		// 调用 AttributeComponent 的回血接口（内部处理上限检查、事件广播等）
		AttrComp->ApplyHeal(static_cast<float>(HealAmount));

		UE_LOG(LogTemp, Log, TEXT("UItemAction_Heal: 为 %s 回复 %d 点生命"),
			*Instigator->GetName(), HealAmount);
		return true;  // ★ 返回 true 告诉 UseItem() 此 Action 消费了物品
	}

	return false;  // 角色没有 AttributeComponent → 无法治疗
}
