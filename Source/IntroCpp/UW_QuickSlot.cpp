// Fill out your copyright notice in the Description page of Project Settings.

#include "UW_QuickSlot.h"
#include "UW_InventoryUI.h"
#include "Engine/Texture2D.h"
#include "Components/Border.h"
#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Components/Image.h"

void UUW_QuickSlot::NativeConstruct()
{
	Super::NativeConstruct();
	// Image_ItemIcon 初始设为 Collapsed（不可见），避免空纹理显示白色
	if (Image_ItemIcon) Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed);
}

void UUW_QuickSlot::SetItemData(UItemDataBase* ItemData, int32 Quantity)
{
	if (!ItemData)
	{
		ClearSlot();
		return;
	}

	// 缓存数据（用于拖拽）
	CachedItem = FItemInstance(ItemData->ItemID, Quantity);
	CachedIconTexture = ItemData->ItemIcon;

	// 图标
	if (Image_ItemIcon)
	{
		if (!ItemData->ItemIcon.IsNull())
		{
			UTexture2D* IconTexture = ItemData->ItemIcon.LoadSynchronous();
			if (IconTexture)
			{
				Image_ItemIcon->SetBrushFromTexture(IconTexture);
				Image_ItemIcon->SetVisibility(ESlateVisibility::HitTestInvisible);
			}
			else
			{
				Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed);
			}
		}
		else
		{
			Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed);
		}
	}

	// 数量
	if (Text_Count)
	{
		if (Quantity > 1)
		{
			Text_Count->SetText(FText::FromString(FString::FromInt(Quantity)));
			Text_Count->SetVisibility(ESlateVisibility::Visible);
		}
		else
		{
			Text_Count->SetVisibility(ESlateVisibility::Collapsed);
		}
	}
}

void UUW_QuickSlot::ClearSlot()
{
	CachedItem = FItemInstance();
	CachedIconTexture.Reset();

	if (Image_ItemIcon) { Image_ItemIcon->SetBrushFromTexture(nullptr); Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed); }
	if (Text_Count)      { Text_Count->SetText(FText::GetEmpty()); Text_Count->SetVisibility(ESlateVisibility::Hidden); }
}

void UUW_QuickSlot::SetSelected(bool bSelected)
{
	if (Border_Highlight)
	{
		Border_Highlight->SetVisibility(bSelected ? ESlateVisibility::Visible : ESlateVisibility::Hidden);
	}
}

// ==========================================
// 拖拽：标准 Slate 流程
// ==========================================

FReply UUW_QuickSlot::NativeOnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	if (MouseEvent.GetEffectingButton() != EKeys::LeftMouseButton || CachedItem.IsEmpty())
		return FReply::Unhandled();

	// 有物品 → 让Slate检测拖拽
	return UWidgetBlueprintLibrary::DetectDragIfPressed(MouseEvent, this, EKeys::LeftMouseButton).NativeReply;
}

void UUW_QuickSlot::NativeOnDragDetected(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent, UDragDropOperation*& OutOperation)
{
	Super::NativeOnDragDetected(MyGeometry, MouseEvent, OutOperation);

	if (CachedItem.IsEmpty()) return;

	// 创建拖拽操作对象
	UDragItemOperation* Operation = NewObject<UDragItemOperation>(GetTransientPackage());
	Operation->SourceType = EDragSource::QuickSlot;
	Operation->SourceIndex = SlotIndex;
	Operation->DraggedItem = CachedItem;
	Operation->ItemIconTexture = CachedIconTexture;

	// 创建拖拽视觉图标
	if (!CachedIconTexture.IsNull())
	{
		UTexture2D* LoadedTex = CachedIconTexture.LoadSynchronous();
		if (LoadedTex)
		{
			UImage* DragVisual = NewObject<UImage>(GetTransientPackage());
			DragVisual->SetBrushFromTexture(LoadedTex);
			Operation->DefaultDragVisual = DragVisual;
		}
	}
	Operation->Pivot = EDragPivot::CenterCenter;

	OutOperation = Operation;

	// 隐藏自身图标（已被"拿起"，用Collapsed完全移除避免干扰拖拽事件路由）
	if (Image_ItemIcon) Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed);

	UE_LOG(LogTemp, Log, TEXT("[QuickSlot] DragDetected from slot=%d"), SlotIndex);
}

void UUW_QuickSlot::NativeOnDragCancelled(const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation)
{
	Super::NativeOnDragCancelled(InDragDropEvent, InOperation);

	// 恢复视觉（HitTestInvisible 保持事件穿透）
	if (Image_ItemIcon && !CachedItem.IsEmpty())
		Image_ItemIcon->SetVisibility(ESlateVisibility::HitTestInvisible);

	UE_LOG(LogTemp, Log, TEXT("[QuickSlot] DragCancelled at slot=%d (restored)"), SlotIndex);
}

// ==========================================
// 接收拖入
// ==========================================

bool UUW_QuickSlot::NativeOnDrop(const FGeometry& MyGeometry, const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation)
{
	Super::NativeOnDrop(MyGeometry, InDragDropEvent, InOperation);

	const UDragItemOperation* DragOp = Cast<UDragItemOperation>(InOperation);
	if (!DragOp || !InvComp) return false;

	// 放回自己 → 忽略
	if (DragOp->SourceType == EDragSource::QuickSlot && DragOp->SourceIndex == SlotIndex)
		return false;

	UE_LOG(LogTemp, Log, TEXT("[QuickSlot] OnDrop at target=%d, source type=%d idx=%d"), SlotIndex, (int32)DragOp->SourceType, DragOp->SourceIndex);

	FItemInstance ExistingItem = InvComp->GetQuickSlot(SlotIndex);

	if (DragOp->IsFromInventory())
	{
		// 背包 → 快捷栏
		if (ExistingItem.IsEmpty())
		{
			// 目标空：快捷栏设为源物品 + 清空背包源槽位
			InvComp->SetQuickSlot(SlotIndex, DragOp->DraggedItem);
			InvComp->SetItemAt(DragOp->SourceIndex, FItemInstance());
		}
		else
		{
			// 目标非空：快捷栏放新物品 + 原快捷栏物品回背包 + 清空源槽位
			InvComp->SetQuickSlot(SlotIndex, DragOp->DraggedItem);
			InvComp->AddItem(ExistingItem.ItemID, ExistingItem.Quantity);
			InvComp->SetItemAt(DragOp->SourceIndex, FItemInstance());
		}
	}
	else if (DragOp->IsFromQuickSlot())
	{
		// 快捷栏内部交换
		FItemInstance SrcItem = InvComp->GetQuickSlot(DragOp->SourceIndex);
		InvComp->SetQuickSlot(DragOp->SourceIndex, ExistingItem);
		InvComp->SetQuickSlot(SlotIndex, SrcItem);
	}

	// 通知背包 UI 刷新（如果存在的话通过 GameInstance 或其他方式获取引用）
	// 这里简化处理：直接返回 true，调用方负责刷新
	return true;
}

bool UUW_QuickSlot::NativeOnDragOver(const FGeometry& MyGeometry, const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation)
{
	return Cast<UDragItemOperation>(InOperation) != nullptr;
}

void UUW_QuickSlot::NativeOnDragLeave(const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation) {}
