// Fill out your copyright notice in the Description page of Project Settings.

#include "UW_InventoryUI.h"
#include "UW_QuickSlot.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "Components/Image.h"
#include "Components/UniformGridPanel.h"
#include "Components/UniformGridSlot.h"
#include "Engine/Texture2D.h"
#include "Engine/StreamableManager.h"
#include "Engine/AssetManager.h"
#include "Widgets/SWidget.h"
#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Components/Image.h"

// ==========================================
// UUW_InventoryUI 实现
// ==========================================

void UUW_InventoryUI::NativeConstruct()
{
	Super::NativeConstruct();

	// 绑定按钮事件
	if (Button_Sort) { Button_Sort->OnClicked.AddDynamic(this, &UUW_InventoryUI::OnButton_SortClicked); }
	if (Button_Close) { Button_Close->OnClicked.AddDynamic(this, &UUW_InventoryUI::OnButton_CloseClicked); }
	if (Button_UseItem) { Button_UseItem->OnClicked.AddDynamic(this, &UUW_InventoryUI::OnButton_UseItemClicked); }
	if (Button_DropItem) { Button_DropItem->OnClicked.AddDynamic(this, &UUW_InventoryUI::OnButton_DropItemClicked); }

	if (Grid_Inventory)
	{
		Grid_Inventory->SetVisibility(ESlateVisibility::Visible);
		Grid_Inventory->SetIsEnabled(true);
	}

	InitializeSlots();
	RefreshUI();
}

void UUW_InventoryUI::NativeDestruct()
{
	if (Button_Sort) { Button_Sort->OnClicked.RemoveDynamic(this, &UUW_InventoryUI::OnButton_SortClicked); }
	if (Button_Close) { Button_Close->OnClicked.RemoveDynamic(this, &UUW_InventoryUI::OnButton_CloseClicked); }
	if (Button_UseItem) { Button_UseItem->OnClicked.RemoveDynamic(this, &UUW_InventoryUI::OnButton_UseItemClicked); }
	if (Button_DropItem) { Button_DropItem->OnClicked.RemoveDynamic(this, &UUW_InventoryUI::OnButton_DropItemClicked); }

	Super::NativeDestruct();
}

void UUW_InventoryUI::SetInventoryComponent(UInventoryComponent* InInventoryComponent)
{
	InventoryComponent = InInventoryComponent;

	if (InventoryComponent)
	{
		InventoryComponent->OnInventoryUpdated.AddUObject(this, &UUW_InventoryUI::OnInventoryUpdated);
		InventoryComponent->OnItemAdded.AddUObject(this, &UUW_InventoryUI::OnItemAdded);
		InventoryComponent->OnItemRemoved.AddUObject(this, &UUW_InventoryUI::OnItemRemoved);
	}

	RefreshUI();
}

void UUW_InventoryUI::RefreshUI()
{
	if (!InventoryComponent || !Grid_Inventory) return;

	UpdateInventoryInfo();

	const TArray<FItemInstance>& Items = InventoryComponent->GetAllItems();
	for (int32 i = 0; i < InventorySlots.Num() && i < Items.Num(); i++)
	{
		InventorySlots[i]->UpdateSlot(Items[i], InventoryComponent);
	}

	UpdateSelectedItemInfo();
}

void UUW_InventoryUI::InitializeSlots()
{
	if (!Grid_Inventory) return;

	if (!SlotWidgetClass)
	{
		SlotWidgetClass = UW_InventorySlot::StaticClass();
	}

	Grid_Inventory->ClearChildren();
	InventorySlots.Empty();

	const int32 MaxSlots = 20;
	const int32 SlotsPerRow = 5;

	for (int32 i = 0; i < MaxSlots; i++)
	{
		UW_InventorySlot* SlotWidget = CreateWidget<UW_InventorySlot>(this, SlotWidgetClass);
		if (SlotWidget)
		{
			SlotWidget->SetupSlot(i, this);
			InventorySlots.Add(SlotWidget);

			UUniformGridSlot* GridSlot = Grid_Inventory->AddChildToUniformGrid(SlotWidget);
			if (GridSlot)
			{
				GridSlot->SetColumn(i % SlotsPerRow);
				GridSlot->SetRow(i / SlotsPerRow);
				GridSlot->SetHorizontalAlignment(HAlign_Fill);
				GridSlot->SetVerticalAlignment(VAlign_Fill);
			}
		}
	}
}

void UUW_InventoryUI::UpdateInventoryInfo()
{
	if (!InventoryComponent) return;

	if (Text_CurrentWeight) { Text_CurrentWeight->SetText(FText::FromString(FString::Printf(TEXT("%.1f"), InventoryComponent->CurrentWeight))); }
	if (Text_MaxWeight)     { Text_MaxWeight->SetText(FText::FromString(FString::Printf(TEXT("%.1f"), InventoryComponent->MaxWeight))); }
	if (Text_ItemCount)      { Text_ItemCount->SetText(FText::FromString(FString::Printf(TEXT("%d"), InventoryComponent->CurrentItemCount))); }
}

void UUW_InventoryUI::UpdateSelectedItemInfo()
{
	if (!InventoryComponent || SelectedSlotIndex == -1)
	{
		if (Image_SelectedItemIcon)    { Image_SelectedItemIcon->SetBrushFromTexture(nullptr); Image_SelectedItemIcon->SetVisibility(ESlateVisibility::Collapsed); }
		if (Text_SelectedItemName)      Text_SelectedItemName->SetText(FText::GetEmpty());
		if (Text_SelectedItemDescription) Text_SelectedItemDescription->SetText(FText::GetEmpty());
		if (Button_UseItem)             Button_UseItem->SetIsEnabled(false);
		if (Button_DropItem)            Button_DropItem->SetIsEnabled(false);
		return;
	}

	FItemInstance SelectedItem = InventoryComponent->GetItemAt(SelectedSlotIndex);
	if (SelectedItem.IsEmpty())
	{
		if (Image_SelectedItemIcon)    { Image_SelectedItemIcon->SetBrushFromTexture(nullptr); Image_SelectedItemIcon->SetVisibility(ESlateVisibility::Collapsed); }
		if (Text_SelectedItemName)      Text_SelectedItemName->SetText(FText::GetEmpty());
		if (Text_SelectedItemDescription) Text_SelectedItemDescription->SetText(FText::GetEmpty());
		if (Button_UseItem)             Button_UseItem->SetIsEnabled(false);
		if (Button_DropItem)            Button_DropItem->SetIsEnabled(false);
		SelectedSlotIndex = -1;
		return;
	}

	UItemDataBase* ItemData = InventoryComponent->GetItemData(SelectedItem.ItemID);
	if (!ItemData)
	{
		if (Image_SelectedItemIcon)    { Image_SelectedItemIcon->SetBrushFromTexture(nullptr); Image_SelectedItemIcon->SetVisibility(ESlateVisibility::Collapsed); }
		if (Text_SelectedItemName)      Text_SelectedItemName->SetText(FText::GetEmpty());
		if (Text_SelectedItemDescription) Text_SelectedItemDescription->SetText(FText::GetEmpty());
		if (Button_UseItem)             Button_UseItem->SetIsEnabled(false);
		if (Button_DropItem)            Button_DropItem->SetIsEnabled(false);
		return;
	}

	if (Text_SelectedItemName)       Text_SelectedItemName->SetText(ItemData->ItemName);
	if (Text_SelectedItemDescription) Text_SelectedItemDescription->SetText(ItemData->ItemDescription);
	if (Button_UseItem)              Button_UseItem->SetIsEnabled(ItemData->bCanUse);
	if (Button_DropItem)             Button_DropItem->SetIsEnabled(ItemData->bCanDrop);

	if (Image_SelectedItemIcon)
	{
		if (!ItemData->ItemIcon.IsNull())
		{
			Image_SelectedItemIcon->SetVisibility(ESlateVisibility::Visible);
			LoadItemIconAsync(ItemData->ItemIcon, static_cast<UUW_QuickSlot*>(nullptr));
		}
		else
		{
			Image_SelectedItemIcon->SetBrushFromTexture(nullptr);
			Image_SelectedItemIcon->SetVisibility(ESlateVisibility::Collapsed);
		}
	}
}

// ==========================================
// 按钮事件
// ==========================================

void UUW_InventoryUI::OnButton_SortClicked()        { if (InventoryComponent) InventoryComponent->SortItems(); }

void UUW_InventoryUI::OnButton_CloseClicked()
{
	OnInventoryClosed.Broadcast();
	RemoveFromParent();
}

void UUW_InventoryUI::OnButton_UseItemClicked()
{
	if (InventoryComponent && SelectedSlotIndex != -1)
	{
		InventoryComponent->UseItem(SelectedSlotIndex);
	}
}

void UUW_InventoryUI::OnButton_DropItemClicked()
{
	if (InventoryComponent && SelectedSlotIndex != -1)
	{
		InventoryComponent->DropItem(SelectedSlotIndex);
		SelectedSlotIndex = -1;
		if (Image_SelectedItemIcon)    { Image_SelectedItemIcon->SetBrushFromTexture(nullptr); Image_SelectedItemIcon->SetVisibility(ESlateVisibility::Collapsed); }
		if (Text_SelectedItemName)      Text_SelectedItemName->SetText(FText::GetEmpty());
		if (Text_SelectedItemDescription) Text_SelectedItemDescription->SetText(FText::GetEmpty());
		if (Button_UseItem)             Button_UseItem->SetIsEnabled(false);
		if (Button_DropItem)            Button_DropItem->SetIsEnabled(false);
		RefreshUI();
	}
}

// ==========================================
// 拖拽操作工厂（供 Slot 的 NativeOnDragDetected 调用）
// ==========================================

UDragItemOperation* UUW_InventoryUI::CreateDragOperation(EDragSource SourceType, int32 SlotIndex, const FItemInstance& Item, const TSoftObjectPtr<UTexture2D>& Icon)
{
	UDragItemOperation* Operation = NewObject<UDragItemOperation>(GetTransientPackage());
	Operation->SourceType = SourceType;
	Operation->SourceIndex = SlotIndex;
	Operation->DraggedItem = Item;
	Operation->ItemIconTexture = Icon;

	// 创建拖拽视觉：一个跟随鼠标的图标
	if (!Icon.IsNull())
	{
		UTexture2D* LoadedTex = Icon.LoadSynchronous();
		if (LoadedTex)
		{
			UImage* DragVisual = NewObject<UImage>(GetTransientPackage());
			DragVisual->SetBrushFromTexture(LoadedTex);
			Operation->DefaultDragVisual = DragVisual;
		}
	}

	Operation->Pivot = EDragPivot::CenterCenter;

	UE_LOG(LogTemp, Log, TEXT("[Drag] Created operation: type=%d index=%d item=%s"), (int32)SourceType, SlotIndex, *Item.ItemID.ToString());
	return Operation;
}

bool UUW_InventoryUI::HandleInventorySlotDrop(int32 TargetIndex, const UDragItemOperation& Operation)
{
	if (!InventoryComponent || Operation.DraggedItem.IsEmpty()) return false;

	if (Operation.IsFromInventory())
	{
		// 背包内部交换：直接用 SwapItems（原地交换指定索引）
		int32 SrcIdx = Operation.SourceIndex;
		if (SrcIdx == TargetIndex) return false;

		InventoryComponent->SwapItems(SrcIdx, TargetIndex);
		// SwapItems 内部已调用 BroadcastInventoryUpdate → 触发 OnInventoryUpdated → RefreshUI，无需重复调用

		UE_LOG(LogTemp, Log, TEXT("[Drag] Swapped inventory slots %d <-> %d"), SrcIdx, TargetIndex);
		return true;
	}
	else if (Operation.IsFromQuickSlot())
	{
		// 快捷栏 → 背包：把快捷栏物品放入目标背包槽位
		FItemInstance TargetItem = InventoryComponent->GetItemAt(TargetIndex);
		FItemInstance SrcQSItem = InventoryComponent->GetQuickSlot(Operation.SourceIndex);

		if (TargetItem.IsEmpty())
		{
			// 目标空：直接设置背包槽位 + 清空快捷栏
			InventoryComponent->SetItemAt(TargetIndex, SrcQSItem);
			InventoryComponent->ClearQuickSlot(Operation.SourceIndex);
		}
		else
		{
			// 目标非空：交换
			InventoryComponent->SetItemAt(TargetIndex, SrcQSItem);
			InventoryComponent->SetQuickSlot(Operation.SourceIndex, TargetItem);
		}

		// ★ 不在这里手动 RefreshUI：SetItemClick / SetQuickSlot / ClearQuickSlot 各自已通过委托触发 UI 刷新
		// 手动再调会导致重复渲染/状态闪烁（复制品的根因）
		UE_LOG(LogTemp, Log, TEXT("[Drag] QuickSlot %d -> Inventory slot %d"), Operation.SourceIndex, TargetIndex);
		return true;
	}

	return false;
}

bool UUW_InventoryUI::HandleQuickSlotDrop(int32 TargetIndex, const UDragItemOperation& Operation, UInventoryComponent* InvComp)
{
	if (!InvComp || Operation.DraggedItem.IsEmpty()) return false;

	if (Operation.IsFromInventory())
	{
		// 背包 → 快捷栏
		FItemInstance ExistingQSItem = InvComp->GetQuickSlot(TargetIndex);
		FItemInstance SrcInvItem = InventoryComponent->GetItemAt(Operation.SourceIndex);

		if (ExistingQSItem.IsEmpty())
		{
			// 目标空：快捷栏设为源物品 + 清空背包源槽位
			InvComp->SetQuickSlot(TargetIndex, SrcInvItem);
			InventoryComponent->SetItemAt(Operation.SourceIndex, FItemInstance());
		}
		else
		{
			// 目标非空：交换
			InvComp->SetQuickSlot(TargetIndex, SrcInvItem);
			InventoryComponent->SetItemAt(Operation.SourceIndex, ExistingQSItem);
		}
		// SetQuickSlot / SetItemClick 各自通过委托触发 UI 刷新（OnQuickSlotChanged / OnInventoryUpdated），无需手动 RefreshUI

		UE_LOG(LogTemp, Log, TEXT("[Drag] Inventory slot %d -> QuickSlot %d"), Operation.SourceIndex, TargetIndex);
		return true;
	}
	else if (Operation.IsFromQuickSlot())
	{
		// 快捷栏内部交换（SetQuickSlot 直接操作指定索引，没问题）
		if (Operation.SourceIndex == TargetIndex) return true;

		FItemInstance SrcItem = InvComp->GetQuickSlot(Operation.SourceIndex);
		FItemInstance DstItem = InvComp->GetQuickSlot(TargetIndex);

		InvComp->SetQuickSlot(Operation.SourceIndex, DstItem);
		InvComp->SetQuickSlot(TargetIndex, SrcItem);

		UE_LOG(LogTemp, Log, TEXT("[Drag] QuickSlot %d <-> %d swap"), Operation.SourceIndex, TargetIndex);
		return true;
	}

	return false;
}

// ==========================================
// 槽位选择事件
// ==========================================

void UUW_InventoryUI::OnSlotSelected(int32 SlotIndex)
{
	if (SelectedSlotIndex != -1 && SelectedSlotIndex < InventorySlots.Num())
	{
		InventorySlots[SelectedSlotIndex]->SetSelected(false);
	}

	SelectedSlotIndex = SlotIndex;

	if (SelectedSlotIndex != -1 && SelectedSlotIndex < InventorySlots.Num())
	{
		InventorySlots[SelectedSlotIndex]->SetSelected(true);
	}

	UpdateSelectedItemInfo();
}

// ==========================================
// 背包更新事件
// ==========================================

void UUW_InventoryUI::OnInventoryUpdated()          { RefreshUI(); }

void UUW_InventoryUI::OnItemAdded(const FItemInstance& Item) { UpdateInventoryInfo(); }

void UUW_InventoryUI::OnItemRemoved(const FItemInstance& Item)
{
	UpdateInventoryInfo();
	if (SelectedSlotIndex != -1)
	{
		FItemInstance SelectedItem = InventoryComponent->GetItemAt(SelectedSlotIndex);
		if (SelectedItem.IsEmpty())
		{
			SelectedSlotIndex = -1;
			UpdateSelectedItemInfo();
		}
	}
}

// ==========================================
// 图标异步加载（两个重载：给 InventorySlot 和 QuickSlot）
// ==========================================

void UUW_InventoryUI::LoadItemIconAsync(const TSoftObjectPtr<UTexture2D>& IconPath, UW_InventorySlot* SlotWidget)
{
	if (IconPath.IsNull())
	{
		if (SlotWidget && SlotWidget->Image_ItemIcon)
		{
			SlotWidget->Image_ItemIcon->SetBrushFromTexture(nullptr);
			SlotWidget->Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed);
		}
		else if (Image_SelectedItemIcon)
		{
			Image_SelectedItemIcon->SetBrushFromTexture(nullptr);
			Image_SelectedItemIcon->SetVisibility(ESlateVisibility::Collapsed);
		}
		return;
	}

	FStreamableManager& StreamableManager = UAssetManager::GetStreamableManager();
	FSoftObjectPath Path = IconPath.ToSoftObjectPath();

	if (SlotWidget && SlotWidget->Image_ItemIcon)
	{
		SlotWidget->Image_ItemIcon->SetVisibility(ESlateVisibility::HitTestInvisible);
	}
	else if (Image_SelectedItemIcon)
	{
		Image_SelectedItemIcon->SetVisibility(ESlateVisibility::HitTestInvisible);
	}

	StreamableManager.RequestAsyncLoad(Path,
		[this, SlotWidget](TSharedPtr<FStreamableHandle> Handle)
		{
			UTexture2D* LoadedTexture = Cast<UTexture2D>(Handle ? Handle->GetLoadedAsset() : nullptr);
			if (LoadedTexture)
			{
				if (SlotWidget && SlotWidget->Image_ItemIcon)
				{
					SlotWidget->Image_ItemIcon->SetBrushFromTexture(LoadedTexture);
					SlotWidget->Image_ItemIcon->SetVisibility(ESlateVisibility::HitTestInvisible);
				}
				else if (Image_SelectedItemIcon)
				{
					Image_SelectedItemIcon->SetBrushFromTexture(LoadedTexture);
					Image_SelectedItemIcon->SetVisibility(ESlateVisibility::HitTestInvisible);
				}
			}
			else
			{
				if (SlotWidget && SlotWidget->Image_ItemIcon)
				{
					SlotWidget->Image_ItemIcon->SetBrushFromTexture(nullptr);
					SlotWidget->Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed);
				}
				else if (Image_SelectedItemIcon)
				{
					Image_SelectedItemIcon->SetBrushFromTexture(nullptr);
					Image_SelectedItemIcon->SetVisibility(ESlateVisibility::Collapsed);
				}
			}
		});
}

void UUW_InventoryUI::LoadItemIconAsync(const TSoftObjectPtr<UTexture2D>& IconPath, UUW_QuickSlot* SlotWidget)
{
	if (IconPath.IsNull())
	{
		if (SlotWidget && SlotWidget->Image_ItemIcon)
		{
			SlotWidget->Image_ItemIcon->SetBrushFromTexture(nullptr);
			SlotWidget->Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed);
		}
		else if (Image_SelectedItemIcon)
		{
			Image_SelectedItemIcon->SetBrushFromTexture(nullptr);
			Image_SelectedItemIcon->SetVisibility(ESlateVisibility::Collapsed);
		}
		return;
	}

	FStreamableManager& StreamableManager = UAssetManager::GetStreamableManager();
	FSoftObjectPath Path = IconPath.ToSoftObjectPath();

	if (SlotWidget && SlotWidget->Image_ItemIcon)
	{
		SlotWidget->Image_ItemIcon->SetVisibility(ESlateVisibility::HitTestInvisible);
	}
	else if (Image_SelectedItemIcon)
	{
		Image_SelectedItemIcon->SetVisibility(ESlateVisibility::HitTestInvisible);
	}

	StreamableManager.RequestAsyncLoad(Path,
		[this, SlotWidget](TSharedPtr<FStreamableHandle> Handle)
		{
			UTexture2D* LoadedTexture = Cast<UTexture2D>(Handle ? Handle->GetLoadedAsset() : nullptr);
			if (LoadedTexture)
			{
				if (SlotWidget && SlotWidget->Image_ItemIcon)
				{
					SlotWidget->Image_ItemIcon->SetBrushFromTexture(LoadedTexture);
					SlotWidget->Image_ItemIcon->SetVisibility(ESlateVisibility::HitTestInvisible);
				}
				else if (Image_SelectedItemIcon)
				{
					Image_SelectedItemIcon->SetBrushFromTexture(LoadedTexture);
					Image_SelectedItemIcon->SetVisibility(ESlateVisibility::HitTestInvisible);
				}
			}
			else
			{
				if (SlotWidget && SlotWidget->Image_ItemIcon)
				{
					SlotWidget->Image_ItemIcon->SetBrushFromTexture(nullptr);
					SlotWidget->Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed);
				}
				else if (Image_SelectedItemIcon)
				{
					Image_SelectedItemIcon->SetBrushFromTexture(nullptr);
					Image_SelectedItemIcon->SetVisibility(ESlateVisibility::Collapsed);
				}
			}
		});
}

// ==========================================
// UW_InventorySlot 实现（标准 Slate 拖拽流程）
// ==========================================

void UW_InventorySlot::SetupSlot(int32 InSlotIndex, UUW_InventoryUI* InParentUI)
{
	SlotIndex = InSlotIndex;
	ParentUI = InParentUI;
}

void UW_InventorySlot::UpdateSlot(const FItemInstance& ItemInstance, UInventoryComponent* InventoryComponent)
{
	CachedItem = ItemInstance;

	if (ItemInstance.IsEmpty())
	{
		if (Image_ItemIcon) { Image_ItemIcon->SetBrushFromTexture(nullptr); Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed); }
		if (Text_ItemQuantity) Text_ItemQuantity->SetText(FText::GetEmpty());
		return;
	}

	UItemDataBase* ItemData = InventoryComponent ? InventoryComponent->GetItemData(ItemInstance.ItemID) : nullptr;
	if (!ItemData)
	{
		if (Image_ItemIcon) { Image_ItemIcon->SetBrushFromTexture(nullptr); Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed); }
		return;
	}

	if (Image_ItemIcon)
	{
		if (!ItemData->ItemIcon.IsNull() && ParentUI)
		{
			ParentUI->LoadItemIconAsync(ItemData->ItemIcon, this);
		}
		else
		{
			Image_ItemIcon->SetBrushFromTexture(nullptr);
			Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed);
		}
	}

	if (Text_ItemQuantity)
	{
		Text_ItemQuantity->SetText(
			ItemInstance.Quantity > 1
				? FText::FromString(FString::Printf(TEXT("%d"), ItemInstance.Quantity))
				: FText::GetEmpty()
		);
	}
}

void UW_InventorySlot::SetSelected(bool bSelected)
{
	bIsSelected = bSelected;
	if (Button_Slot)
	{
		// 可在蓝图中根据 IsSelected 改变样式
	}
}

void UW_InventorySlot::NativeConstruct()
{
	Super::NativeConstruct();
	// Button_Slot 和 Image_ItemIcon 都设为 HitTestInvisible，让鼠标事件穿透到父级 UserWidget
	if (Button_Slot) Button_Slot->SetVisibility(ESlateVisibility::HitTestInvisible);
	if (Image_ItemIcon) Image_ItemIcon->SetVisibility(ESlateVisibility::HitTestInvisible);
}

FReply UW_InventorySlot::NativeOnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	if (MouseEvent.GetEffectingButton() != EKeys::LeftMouseButton) return FReply::Unhandled();

	// 空槽位 → 普通点击选中
	if (CachedItem.IsEmpty())
	{
		if (ParentUI) ParentUI->OnSlotSelected(SlotIndex);
		return FReply::Handled();
	}

	// 有物品 → 告诉Slate开始检测拖拽（Slate自动管理捕获、阈值、事件路由）
	return UWidgetBlueprintLibrary::DetectDragIfPressed(MouseEvent, this, EKeys::LeftMouseButton).NativeReply;
}

void UW_InventorySlot::NativeOnDragDetected(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent, UDragDropOperation*& OutOperation)
{
	Super::NativeOnDragDetected(MyGeometry, MouseEvent, OutOperation);

	if (!ParentUI || CachedItem.IsEmpty()) return;

	// 获取图标纹理
	TSoftObjectPtr<UTexture2D> IconPtr;
	if (ParentUI->InventoryComponent)
	{
		UItemDataBase* Data = ParentUI->InventoryComponent->GetItemData(CachedItem.ItemID);
		if (Data) IconPtr = Data->ItemIcon;
	}

	// 委托父UI创建拖拽操作对象（包含数据 + 视觉图标）
	OutOperation = ParentUI->CreateDragOperation(EDragSource::Inventory, SlotIndex, CachedItem, IconPtr);

	// 隐藏自身图标（已被"拿起"，用Collapsed完全移除避免干扰拖拽事件路由）
	if (Image_ItemIcon) Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed);

	UE_LOG(LogTemp, Log, TEXT("[InvSlot] DragDetected from slot=%d"), SlotIndex);
}

void UW_InventorySlot::NativeOnDragCancelled(const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation)
{
	Super::NativeOnDragCancelled(InDragDropEvent, InOperation);

	// 拖拽取消（落在无效区域）→ 恢复视觉（HitTestInvisible 保持事件穿透）
	if (Image_ItemIcon && !CachedItem.IsEmpty())
		Image_ItemIcon->SetVisibility(ESlateVisibility::HitTestInvisible);

	UE_LOG(LogTemp, Log, TEXT("[InvSlot] DragCancelled at slot=%d (restored)"), SlotIndex);
}

bool UW_InventorySlot::NativeOnDrop(const FGeometry& MyGeometry, const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation)
{
	Super::NativeOnDrop(MyGeometry, InDragDropEvent, InOperation);

	UE_LOG(LogTemp, Log, TEXT("[InvSlot] *** OnDrop FIRED at slot=%d, InOperation=%s ***"), SlotIndex, *GetNameSafe(InOperation));

	const UDragItemOperation* DragOp = Cast<UDragItemOperation>(InOperation);
	if (!DragOp)
	{
		UE_LOG(LogTemp, Warning, TEXT("[InvSlot] OnDrop: Cast failed! InOperation type=%s"), InOperation ? *InOperation->GetClass()->GetName() : TEXT("null"));
		return false;
	}
	if (!ParentUI)
	{
		UE_LOG(LogTemp, Warning, TEXT("[InvSlot] OnDrop: ParentUI is null"));
		return false;
	}

	UE_LOG(LogTemp, Log, TEXT("[InvSlot] OnDrop at target=%d, source type=%d idx=%d"), SlotIndex, (int32)DragOp->SourceType, DragOp->SourceIndex);

	// 委托给父UI执行实际的数据操作
	bool bResult = ParentUI->HandleInventorySlotDrop(SlotIndex, *DragOp);

	// 放置成功后选中目标槽位，显示该位置的物品详情
	if (bResult && ParentUI)
	{
		ParentUI->OnSlotSelected(SlotIndex);
	}

	return bResult;
}

bool UW_InventorySlot::NativeOnDragOver(const FGeometry& MyGeometry, const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation)
{
	const UDragItemOperation* DragOp = Cast<UDragItemOperation>(InOperation);
	UE_LOG(LogTemp, Log, TEXT("[InvSlot] DragOver at slot=%d, operation=%s"), SlotIndex, DragOp ? TEXT("ValidDragOp") : (InOperation ? TEXT("OtherOp") : TEXT("NULL")));
	return DragOp != nullptr;
}

void UW_InventorySlot::NativeOnDragLeave(const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation)
{
	UE_LOG(LogTemp, Log, TEXT("[InvSlot] DragLeave slot=%d"), SlotIndex);
}
