// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Widgets/DeclarativeSyntaxSupport.h"
#include "Input/Reply.h"
#include "Widgets/SWidget.h"
#include "Blueprint/DragDropOperation.h"  // UDragDropOperation 基类
#include "ItemDataBase.h"                // FItemInstance（DraggedItem 字段类型）
#include "UDragItemOperation.generated.h"

// ============================================================
//  EDragSource — 拖拽来源类型枚举
// ============================================================

/**
 * 标识拖拽操作是从哪里发起的
 * 用于 OnDrop 处理时区分不同的数据交换逻辑
 */
UENUM(BlueprintType)
enum class EDragSource : uint8
{
	Inventory,      // 来自背包槽位 (UW_InventorySlot)
	QuickSlot       // 来自快捷栏槽位 (UUW_QuickSlot)
};

// ============================================================
//  UDragItemOperation — 物品拖拽操作数据载体
// ============================================================

/**
 * 在背包和快捷栏之间拖动物品时携带的数据对象。
 *
 * 继承自 UDragDropOperation（Slate 原生拖拽系统基类），
 * 由 NativeOnDragDetected 创建，通过 Slate 事件系统传递到目标 Widget 的 NativeOnDrop。
 *
 * 【包含的数据】
 * - 来源标识（从哪来的：背包 or 快捷栏）
 * - 源位置索引（哪个格子发起的拖拽）
 * - 物品实例数据（拖的是什么东西：ID + 数量）
 * - 图标纹理（用于生成跟随鼠标的视觉 DragVisual）
 *
 * 【生命周期】
 * 创建于 TransientPackage（临时包），拖拽结束后由 GC 自动回收。
 * 无需手动 Delete。
 */
UCLASS()
class INTROCPP_API UDragItemOperation : public UDragDropOperation
{
	GENERATED_BODY()

public:

	// ==========================================
	// 拖拽数据字段
	// ==========================================

	/** 拖拽来源类型（背包槽位 or 快捷栏槽位）*/
	UPROPERTY(VisibleAnywhere, Category = "Drag")
	EDragSource SourceType = EDragSource::Inventory;

	/** 源槽位索引（在 Inventory[] 或 QuickSlots[] 中的位置）*/
	UPROPERTY(VisibleAnywhere, Category = "Drag")
	int32 SourceIndex = -1;

	/** 被拖拽的物品实例数据（ID + 数量），目标 OnDrop 用此执行数据交换 */
	UPROPERTY(VisibleAnywhere, Category = "Drag")
	FItemInstance DraggedItem;

	/** 物品图标纹理软引用（用于生成拖拽时的视觉图标 Widget）*/
	UPROPERTY(VisibleAnywhere, Category = "Drag")
	TSoftObjectPtr<UTexture2D> ItemIconTexture;

	/** 拖拽时的视觉 Widget（可选，通常是一个 Image 显示物品图标跟鼠标移动）*/
	UPROPERTY()
	class UUserWidget* DragVisual;

	// ==========================================
	// 工厂方法 — 快速构建拖拽操作
	// ==========================================

	/** 从背包槽位创建拖拽操作 */
	static UDragItemOperation* CreateFromInventory(int32 SlotIndex, const FItemInstance& Item, const TSoftObjectPtr<UTexture2D>& Icon);

	/** 从快捷栏槽位创建拖拽操作 */
	static UDragItemOperation* CreateFromQuickSlot(int32 SlotIndex, const FItemInstance& Item, const TSoftObjectPtr<UTexture2D>& Icon);

	// ==========================================
	// 便捷判断方法
	// ==========================================

	/** 是否来自背包槽位 */
	bool IsFromInventory() const { return SourceType == EDragSource::Inventory; }

	/** 是否来自快捷栏槽位 */
	bool IsFromQuickSlot() const { return SourceType == EDragSource::QuickSlot; }
};
