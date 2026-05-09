// Fill out your copyright notice in the Description page of Project Settings.

#include "UDragItemOperation.h"
#include "Engine/Texture2D.h"

UDragItemOperation* UDragItemOperation::CreateFromInventory(int32 SlotIndex, const FItemInstance& Item, const TSoftObjectPtr<UTexture2D>& Icon)
{
	UDragItemOperation* Operation = NewObject<UDragItemOperation>();
	Operation->SourceType = EDragSource::Inventory;
	Operation->SourceIndex = SlotIndex;
	Operation->DraggedItem = Item;
	Operation->ItemIconTexture = Icon;
	Operation->DragVisual = nullptr;
	return Operation;
}

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
