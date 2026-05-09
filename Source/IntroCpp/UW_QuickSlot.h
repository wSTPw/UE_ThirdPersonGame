// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Components/Border.h"
#include "ItemDataBase.h"
#include "InventoryComponent.h"  // FItemInstance
#include "UDragItemOperation.h"  // 拖拽操作

// 前向声明（避免循环包含）
class UUW_InventoryUI;
class UInventoryComponent;

#include "UW_QuickSlot.generated.h"

/**
 * UW_QuickSlot — 快捷栏单格子 Widget（支持拖拽）
 *
 * 功能：
 *   - 显示物品图标、数量、选中高亮
 *   - 支持拖出：将快捷栏物品拖回背包或其他快捷槽
 *   - 支持接收：从背包或其它快捷槽拖入
 */
UCLASS()
class INTROCPP_API UUW_QuickSlot : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual void NativeConstruct() override;

	// ==========================================
	// 数据绑定：从外部设置显示内容
	// ==========================================

	/** 用物品数据填充本格（图标 + 数量） */
	UFUNCTION(BlueprintCallable, Category = "QuickSlot")
	void SetItemData(UItemDataBase* ItemData, int32 Quantity);

	/** 清空本格（无物品状态） */
	UFUNCTION(BlueprintCallable, Category = "QuickSlot")
	void ClearSlot();

	/** 设置是否为选中状态（高亮边框） */
	void SetSelected(bool bSelected);

	int32 GetSlotIndex() const { return SlotIndex; }
	void SetSlotIndex(int32 InIndex) { SlotIndex = InIndex; }

	// ==========================================
	// 拖拽相关接口
	// ==========================================

	/** 设置背包组件引用（拖拽操作时需要） */
	void SetInventoryComponent(UInventoryComponent* InInvComp) { InvComp = InInvComp; }

	// ==========================================
	// UI 控件（BindWidgetOptional）
	// ==========================================

	UPROPERTY(meta = (BindWidgetOptional))
	UImage* Image_ItemIcon;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* Text_Count;

	UPROPERTY(meta = (BindWidgetOptional))
	UBorder* Border_Highlight;

protected:
	virtual FReply NativeOnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;
	virtual void NativeOnDragDetected(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent, UDragDropOperation*& OutOperation) override;
	virtual void NativeOnDragCancelled(const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation) override;
	virtual bool NativeOnDrop(const FGeometry& MyGeometry, const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation) override;
	virtual bool NativeOnDragOver(const FGeometry& MyGeometry, const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation) override;
	virtual void NativeOnDragLeave(const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation) override;

private:
	int32 SlotIndex = 0;

	// 背包组件引用（拖拽交换需要）
	UPROPERTY()
	UInventoryComponent* InvComp = nullptr;

	// 缓存的当前物品数据（用于发起拖拽）
	FItemInstance CachedItem;
	TSoftObjectPtr<UTexture2D> CachedIconTexture;
};
