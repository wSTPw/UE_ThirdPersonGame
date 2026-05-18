// Fill out your copyright notice in the Description page of Project Settings.

#include "UDragItemOperation.h"
#include "Engine/Texture2D.h"

// ============================================================================
//  工厂方法实现
// ============================================================================

/** 从背包槽位创建拖拽操作 — 设置 SourceType=Inventory */
UDragItemOperation* UDragItemOperation::CreateFromInventory(int32 SlotIndex, const FItemInstance& Item, const TSoftObjectPtr<UTexture2D>& Icon)
{
	UDragItemOperation* Operation = NewObject<UDragItemOperation>();
	Operation->SourceType = EDragSource::Inventory;
	Operation->SourceIndex = SlotIndex;
	Operation->DraggedItem = Item;
	Operation->ItemIconTexture = Icon;
	Operation->DragVisual = nullptr;  // 由调用方决定是否设置 DragVisual
	return Operation;
}

/** 从快捷栏槽位创建拖拽操作 — 设置 SourceType=QuickSlot */
UDragItemOperation* UDragItemOperation::CreateFromQuickSlot(int32 SlotIndex, const FItemInstance& Item, const TSoftObjectPtr<UTexture2D>& Icon)
{
	UDragItemOperation* Operation = NewObject<UDragItemOperation>();
	Operation->SourceType = EDragSource::QuickSlot;
	Operation->SourceIndex = SlotIndex;
	Operation->DraggedItem = Item;
	Operation->ItemIconTexture = Icon;
	Operation->DragVisual = nullptr;
	return Operation;
}
