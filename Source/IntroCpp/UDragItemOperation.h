// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Widgets/DeclarativeSyntaxSupport.h"
#include "Input/Reply.h"
#include "Widgets/SWidget.h"
#include "Blueprint/DragDropOperation.h"
#include "ItemDataBase.h"    // FItemInstance
#include "UDragItemOperation.generated.h"

/**
 * 拖拽源类型枚举
 */
UENUM(BlueprintType)
enum class EDragSource : uint8
{
	Inventory,      // 来自背包槽位
	QuickSlot       // 来自快捷栏槽位
};

/**
 * UDragItemOperation — 物品拖拽操作
 *
 * 在背包和快捷栏之间拖动物品时携带的数据：
 *   - 源位置（类型 + 索引）
 *   - 物品实例（图标 + 数量等）
 *   - 拖拽时的视觉（跟随鼠标的图标 Widget）
 */
UCLASS()
class INTROCPP_API UDragItemOperation : public UDragDropOperation
{
	GENERATED_BODY()

public:
	// ==========================================
	// 拖拽数据
	// ==========================================

	/** 拖拽来源类型 */
	UPROPERTY(VisibleAnywhere, Category = "Drag")
	EDragSource SourceType = EDragSource::Inventory;

	/** 源槽位索引 */
	UPROPERTY(VisibleAnywhere, Category = "Drag")
	int32 SourceIndex = -1;

	/** 被拖拽的物品数据 */
	UPROPERTY(VisibleAnywhere, Category = "Drag")
	FItemInstance DraggedItem;

	/** 物品图标纹理（用于生成拖拽视觉） */
	UPROPERTY(VisibleAnywhere, Category = "Drag")
	TSoftObjectPtr<UTexture2D> ItemIconTexture;

	/** 拖拽时显示的视觉 Widget（可选，在 OnDrop 时由接收方决定是否使用） */
	UPROPERTY()
	class UUserWidget* DragVisual;

	// ==========================================
	// 工厂方法：快速构建拖拽操作
	// ==========================================

	static UDragItemOperation* CreateFromInventory(int32 SlotIndex, const FItemInstance& Item, const TSoftObjectPtr<UTexture2D>& Icon);
	static UDragItemOperation* CreateFromQuickSlot(int32 SlotIndex, const FItemInstance& Item, const TSoftObjectPtr<UTexture2D>& Icon);

	/** 是否来自背包 */
	bool IsFromInventory() const { return SourceType == EDragSource::Inventory; }

	/** 是否来自快捷栏 */
	bool IsFromQuickSlot() const { return SourceType == EDragSource::QuickSlot; }
};
