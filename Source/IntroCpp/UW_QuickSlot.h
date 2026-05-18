// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Components/Border.h"            // 选中高亮边框
#include "ItemDataBase.h"                // UItemDataBase (SetItemData 参数)
#include "InventoryComponent.h"          // FItemInstance
#include "UDragItemOperation.h"         // 拖拽操作类型

// 前向声明（避免循环包含）
class UUW_InventoryUI;
class UInventoryComponent;

#include "UW_QuickSlot.generated.h"

/**
 * UW_QuickSlot — 快捷栏单格子 Widget（支持拖拽交互）
 *
 * 【职责】
 * 显示快捷栏中一个格子的物品图标和数量，支持选中高亮和完整的拖拽操作。
 *
 * 【Widget 结构】
 * ┌────────────────────┐
 * │ Border_Highlight    │  (选中高亮边框，默认 Hidden)
 * │ ┌────────────────┐ │
 * │ │ Image_ItemIcon   │ │  物品图标
 * │ │ Text_Count       │ │  数量文字 (>1时显示)
 * │ └────────────────┘ │
 * └────────────────────┘
 *
 * 【与 InventorySlot 的差异】
 * - QuickSlot 使用**同步加载**图标（只有5格，不需要异步优化）
 * - NativeOnDrop 中**直接操作数据**不经过父 UI（因为快捷栏可能独立于背包 UI 存在）
 * - SetItemData() 接收 UItemDataBase* 而非 FItemInstance（接口更直观）
 */
UCLASS()
class INTROCPP_API UUW_QuickSlot : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Widget 构建完成初始化 */
	virtual void NativeConstruct() override;

	// ==========================================
	// 数据绑定接口
	// ==========================================

	/**
	 * 用物品数据和数量填充此格的显示内容
	 * 同时缓存数据以供后续拖拽使用
	 *
	 * @param ItemData 物品配置数据指针（读取 Icon、ID 等）
	 * @param Quantity 数量
	 */
	UFUNCTION(BlueprintCallable, Category = "QuickSlot")
	void SetItemData(UItemDataBase* ItemData, int32 Quantity);

	/** 清空此格（重置为无物品状态）*/
	UFUNCTION(BlueprintCallable, Category = "QuickSlot")
	void ClearSlot();

	/**
	 * 设置选中高亮状态
	 * 通过 Border_Highlight 的 Visible/Hidden 控制视觉反馈
	 */
	void SetSelected(bool bSelected);

	/** 获取/设置槽位索引（用于拖拽时标识来源位置）*/
	int32 GetSlotIndex() const { return SlotIndex; }
	void SetSlotIndex(int32 InIndex) { SlotIndex = InIndex; }

	// ==========================================
	// 拖拽相关接口
	// ==========================================

	/** 设置背包组件引用（拖拽交换操作需要读写背包和快捷栏数据）*/
	void SetInventoryComponent(UInventoryComponent* InInvComp) { InvComp = InInvComp; }

	// ==========================================
	// UI 控件（BindWidgetOptional — 可选绑定）
	// ==========================================

	/** 物品图标图片 */
	UPROPERTY(meta = (BindWidgetOptional))
	UImage* Image_ItemIcon;

	/** 数量显示文字 */
	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* Text_Count;

	/** 选中高亮边框（未选中=Hidden, 选中=Visible）*/
	UPROPERTY(meta = (BindWidgetOptional))
	UBorder* Border_Highlight;

protected:
	// ====== Slate 拖拽事件覆写 ======

	/** 鼠标按下：有物品 → 检测拖拽；空 → 忽略 */
	virtual FReply NativeOnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;

	/** 拖拽检测通过：创建 DragDropOperation + 隐藏自身图标 */
	virtual void NativeOnDragDetected(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent, UDragDropOperation*& OutOperation) override;

	/** 拖拽取消：恢复图标可见性 */
	virtual void NativeOnDragCancelled(const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation) override;

	/** 有拖动物品放到此格子上 */
	virtual bool NativeOnDrop(const FGeometry& MyGeometry, const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation) override;

	/** 拖拽经过：是否允许放置 */
	virtual bool NativeOnDragOver(const FGeometry& MyGeometry, const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation) override;

	/** 拖拽离开 */
	virtual void NativeOnDragLeave(const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation) override;

private:

	/** 此格在快捷栏中的索引 [0, 4] */
	int32 SlotIndex = 0;

	/** 背包组件引用（拖拽交换时需要读写数据）*/
	UPROPERTY()
	UInventoryComponent* InvComp = nullptr;

	/** 缓存的当前物品实例（拖拽发起时携带的数据）*/
	FItemInstance CachedItem;

	/** 缓存的当前图标纹理（拖拽时生成 DragVisual 用）*/
	TSoftObjectPtr<UTexture2D> CachedIconTexture;
};
