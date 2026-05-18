#pragma once

#include "CoreMinimal.h"
#include "ItemAction.h"                    // 基类
#include "ItemAction_RestoreMana.generated.h"

/**
 * UItemAction_RestoreMana — 回复魔法值效果 Action
 *
 * 与 UItemAction_Heal 结构完全对称，区别是调用 RestoreMana() 而非 ApplyHeal()。
 * 同样从 UConsumableData.ManaRestore 读取配置值初始化 ManaAmount。
 */
UCLASS(Blueprintable)
class INTROCPP_API UItemAction_RestoreMana : public UItemAction
{
	GENERATED_BODY()

public:

	/** 回复的魔法值点数。可在蓝图或 DataAsset 中覆盖 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mana")
	int32 ManaAmount = 20;

	/** 从 UConsumableData 读取 ManaRestore 初始化回复量 */
	virtual void InitializeFromItemData(const UItemDataBase* ItemData) override;

	/** 执行回蓝效果：调用 AttributeComponent.RestoreMana() */
	virtual bool Execute_Implementation(UInventoryComponent* Inventory, int32 SlotIndex, AActor* Instigator) override;
};
