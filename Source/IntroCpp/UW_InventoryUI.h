// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/Button.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Components/UniformGridPanel.h"
#include "InventoryComponent.h"
#include "UDragItemOperation.h"    // 拖拽操作
#include "UW_InventoryUI.generated.h"

// 前向声明
class UButton;
class UTextBlock;
class UImage;
class UUniformGridPanel;
class UW_InventorySlot;
class UUW_QuickSlot;

// ==========================================
// 背包主界面
// ==========================================
UCLASS()
class INTROCPP_API UUW_InventoryUI : public UUserWidget
{
	GENERATED_BODY()

protected:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;

public:
	// ==========================================
	// 设置背包组件
	// ==========================================
	UFUNCTION(BlueprintCallable, Category = "Inventory UI")
	void SetInventoryComponent(UInventoryComponent* InInventoryComponent);

	UFUNCTION(BlueprintCallable, Category = "Inventory UI")
	void RefreshUI();

	// ==========================================
	// 获取物品图标（异步加载）
	// ==========================================
	void LoadItemIconAsync(const TSoftObjectPtr<UTexture2D>& IconPath, UW_InventorySlot* SlotWidget);
	void LoadItemIconAsync(const TSoftObjectPtr<UTexture2D>& IconPath, UUW_QuickSlot* SlotWidget);

	// ==========================================
	// UI 元素（在蓝图中绑定）
	// ==========================================
	UPROPERTY(meta = (BindWidget))
	UUniformGridPanel* Grid_Inventory;

	UPROPERTY(meta = (BindWidget))
	UTextBlock* Text_CurrentWeight;

	UPROPERTY(meta = (BindWidget))
	UTextBlock* Text_MaxWeight;

	UPROPERTY(meta = (BindWidget))
	UTextBlock* Text_ItemCount;

	UPROPERTY(meta = (BindWidget))
	UButton* Button_Sort;

	UPROPERTY(meta = (BindWidget))
	UButton* Button_Close;

	UPROPERTY(meta = (BindWidgetOptional))
	UImage* Image_SelectedItemIcon;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* Text_SelectedItemName;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* Text_SelectedItemDescription;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* Button_UseItem;

	UPROPERTY(meta = (BindWidgetOptional))
	UButton* Button_DropItem;

	// ==========================================
	// 背包槽位数组
	// ==========================================
	UPROPERTY()
	TArray<UW_InventorySlot*> InventorySlots;

	// ==========================================
	// 当前选中的槽位
	// ==========================================
	UPROPERTY()
	int32 SelectedSlotIndex = -1;

	UPROPERTY()
	UInventoryComponent* InventoryComponent;

	// ==========================================
	// 槽位蓝图类（在蓝图中指定）
	// ==========================================
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "UI")
	TSubclassOf<UW_InventorySlot> SlotWidgetClass;

	// ==========================================
	// 槽位选择事件
	// ==========================================
	void OnSlotSelected(int32 SlotIndex);

	// ==========================================
	// 拖拽处理接口（供 InventorySlot / QuickSlot 的 OnDrop/OnDragCancelled 调用）
	// ==========================================

	/** 处理放置到背包槽位：来自背包内部交换 或 来自快捷栏 */
	bool HandleInventorySlotDrop(int32 TargetIndex, const UDragItemOperation& Operation);

	/** 处理放置到快捷栏槽位 */
	bool HandleQuickSlotDrop(int32 TargetIndex, const UDragItemOperation& Operation, UInventoryComponent* InvComp);

	/** 创建拖拽操作对象（含视觉图标），由 Slot 的 NativeOnDragDetected 调用 */
	UDragItemOperation* CreateDragOperation(EDragSource SourceType, int32 SlotIndex, const FItemInstance& Item, const TSoftObjectPtr<UTexture2D>& Icon);

protected:
	void InitializeSlots();
	void UpdateInventoryInfo();
	void UpdateSelectedItemInfo();

	// 按钮
	UFUNCTION()
	void OnButton_SortClicked();

	UFUNCTION()
	void OnButton_CloseClicked();

	UFUNCTION()
	void OnButton_UseItemClicked();

	UFUNCTION()
	void OnButton_DropItemClicked();

	// 背包更新事件
	UFUNCTION()
	void OnInventoryUpdated();

	UFUNCTION()
	void OnItemAdded(const FItemInstance& Item);

	UFUNCTION()
	void OnItemRemoved(const FItemInstance& Item);

public:
	DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnInventoryClosed);
	UPROPERTY(BlueprintAssignable, Category = "Inventory")
	FOnInventoryClosed OnInventoryClosed;
};

// ==========================================
// 单个背包槽位 UI（支持拖拽）
// ==========================================
UCLASS()
class INTROCPP_API UW_InventorySlot : public UUserWidget
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "Inventory Slot")
	void SetupSlot(int32 InSlotIndex, UUW_InventoryUI* InParentUI);

	UFUNCTION(BlueprintCallable, Category = "Inventory Slot")
	void UpdateSlot(const FItemInstance& ItemInstance, UInventoryComponent* InventoryComponent);

	UFUNCTION(BlueprintCallable, Category = "Inventory Slot")
	void SetSelected(bool bSelected);

public:
	UPROPERTY(meta = (BindWidget))
	UButton* Button_Slot;

	UPROPERTY(meta = (BindWidget))
	UImage* Image_ItemIcon;

	UPROPERTY(meta = (BindWidget))
	UTextBlock* Text_ItemQuantity;

protected:
	virtual void NativeConstruct() override;
	virtual FReply NativeOnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;
	virtual void NativeOnDragDetected(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent, UDragDropOperation*& OutOperation) override;
	virtual void NativeOnDragCancelled(const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation) override;
	virtual bool NativeOnDrop(const FGeometry& MyGeometry, const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation) override;
	virtual bool NativeOnDragOver(const FGeometry& MyGeometry, const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation) override;
	virtual void NativeOnDragLeave(const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation) override;

private:
	int32 SlotIndex = -1;
	bool bIsSelected = false;
	UUW_InventoryUI* ParentUI = nullptr;

	/** 当前缓存的物品实例（用于发起拖拽时携带数据） */
	FItemInstance CachedItem;
};
