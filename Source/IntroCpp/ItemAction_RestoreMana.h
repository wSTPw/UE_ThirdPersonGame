// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "ItemAction.h"
#include "ItemAction_RestoreMana.generated.h"

UCLASS(Blueprintable)
class INTROCPP_API UItemAction_RestoreMana : public UItemAction
{
	GENERATED_BODY()

public:
	// 恢复魔法值数量（可在蓝图或数据表中覆盖）
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mana")
	int32 ManaAmount = 20;

	virtual void InitializeFromItemData(const UItemDataBase* ItemData) override;
	// 执行动作（默认实现示例：对 Character 打日志并返回已消费）
	virtual bool Execute_Implementation(UInventoryComponent* Inventory, int32 SlotIndex, AActor* Instigator) override;
};
