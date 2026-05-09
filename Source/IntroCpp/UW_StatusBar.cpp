// Fill out your copyright notice in the Description page of Project Settings.

#include "UW_StatusBar.h"
#include "Components/ProgressBar.h"
#include "Components/TextBlock.h"
#include "Components/PanelWidget.h"
#include "AttributeComponent.h"
#include "InventoryComponent.h"
#include "UW_QuickSlot.h"
#include "ItemDataSubsystem.h"

void UUW_StatusBar::NativeConstruct()
{
	Super::NativeConstruct();
}

void UUW_StatusBar::NativeDestruct()
{
	// 解绑 HP/MP 事件
	if (AttributeComp)
	{
		AttributeComp->OnHealthChanged.RemoveAll(this);
		AttributeComp->OnManaChanged.RemoveAll(this);
	}

	// 解绑快捷栏事件
	if (InvComp)
	{
		InvComp->OnQuickSlotSelected.RemoveAll(this);
		InvComp->OnQuickSlotChanged.RemoveAll(this);
		InvComp->OnEquipmentChanged.RemoveAll(this);
	}

	Super::NativeDestruct();
}

// ==========================================
// HP/MP 初始化
// ==========================================

void UUW_StatusBar::InitWithAttributes(UAttributeComponent* InAttrComp)
{
	if (AttributeComp && AttributeComp != InAttrComp)
	{
		AttributeComp->OnHealthChanged.RemoveAll(this);
		AttributeComp->OnManaChanged.RemoveAll(this);
	}

	AttributeComp = InAttrComp;

	if (!AttributeComp) return;

	AttributeComp->OnHealthChanged.AddDynamic(this, &UUW_StatusBar::OnHealthChanged);
	AttributeComp->OnManaChanged.AddDynamic(this, &UUW_StatusBar::OnManaChanged);

	UpdateHealthDisplay(AttributeComp->GetCurrentHealth(), AttributeComp->GetMaxHealth());
	UpdateManaDisplay(AttributeComp->GetCurrentMana(), AttributeComp->GetMaxMana());

	UE_LOG(LogTemp, Log, TEXT("[StatusBar] Bound AttrComp, HP: %.0f/%.0f MP: %.0f/%.0f"),
		AttributeComp->GetCurrentHealth(), AttributeComp->GetMaxHealth(),
		AttributeComp->GetCurrentMana(), AttributeComp->GetMaxMana());
}

// ==========================================
// 快捷栏初始化
// ==========================================

void UUW_StatusBar::InitWithInventory(UInventoryComponent* InInvComp)
{
	InvComp = InInvComp;

	if (!InvComp) return;

	// 绑定快捷栏事件
	InvComp->OnQuickSlotSelected.AddDynamic(this, &UUW_StatusBar::OnQuickSlotSelected);
	InvComp->OnQuickSlotChanged.AddDynamic(this, &UUW_StatusBar::OnQuickSlotChanged);
	InvComp->OnEquipmentChanged.AddDynamic(this, &UUW_StatusBar::OnEquipmentChanged);

	// 创建子 Widget 并放入容器
	CreateSlotWidgets();

	// 立即刷新
	RefreshQuickSlots();

	UE_LOG(LogTemp, Log, TEXT("[StatusBar] Bound InvComp for QuickSlots"));
}

// ==========================================
// HP/MP 回调
// ==========================================

void UUW_StatusBar::OnHealthChanged(float CurrentHP, float MaxHP)
{
	UpdateHealthDisplay(CurrentHP, MaxHP);
}

void UUW_StatusBar::OnManaChanged(float CurrentMP, float MaxMP)
{
	UpdateManaDisplay(CurrentMP, MaxMP);
}

void UUW_StatusBar::UpdateHealthDisplay(float Current, float Max)
{
	if (ProgressBar_HP)
	{
		float Percent = (Max > 0.0f) ? (Current / Max) : 0.0f;
		ProgressBar_HP->SetPercent(Percent);

		if (Percent < 0.3f)
		{
			ProgressBar_HP->SetFillColorAndOpacity(FLinearColor(1.0f, 0.2f, 0.2f, 1.0f));
		}
		else
		{
			ProgressBar_HP->SetFillColorAndOpacity(FLinearColor(0.9f, 0.15f, 0.15f, 1.0f));
		}
	}

	if (Text_HP)
	{
		Text_HP->SetText(FText::FromString(FString::Printf(TEXT("%.0f / %.0f"), Current, Max)));
	}
}

void UUW_StatusBar::UpdateManaDisplay(float Current, float Max)
{
	if (ProgressBar_MP)
	{
		float Percent = (Max > 0.0f) ? (Current / Max) : 0.0f;
		ProgressBar_MP->SetPercent(Percent);
		ProgressBar_MP->SetFillColorAndOpacity(FLinearColor(0.15f, 0.4f, 1.0f, 1.0f));
	}

	if (Text_MP)
	{
		Text_MP->SetText(FText::FromString(FString::Printf(TEXT("%.0f / %.0f"), Current, Max)));
	}
}

// ==========================================
// 快捷栏：创建子 Widget
// ==========================================

void UUW_StatusBar::CreateSlotWidgets()
{
	// 清理旧实例
	for (UUW_QuickSlot* SlotWidget : SlotWidgets)
	{
		if (SlotWidget)
		{
			SlotWidget->RemoveFromParent();
		}
	}
	SlotWidgets.Empty();

	if (!QuickSlotContainer)
	{
		UE_LOG(LogTemp, Warning, TEXT("[StatusBar] QuickSlotContainer is null, cannot create slot widgets"));
		return;
	}

	// 确保有有效的 Widget 类
	TSubclassOf<UUW_QuickSlot> ClassToUse = QuickSlotWidgetClass;
	if (!ClassToUse)
	{
		// 默认使用 C++ 基类（蓝图可覆盖）
		ClassToUse = UUW_QuickSlot::StaticClass();
	}

	// 创建5个格子
	for (int32 i = 0; i < UInventoryComponent::QUICK_SLOT_COUNT; ++i)
	{
		UUW_QuickSlot* SlotWidget = CreateWidget<UUW_QuickSlot>(this, ClassToUse);
		if (!SlotWidget) continue;

		SlotWidget->SetSlotIndex(i);

		// 设置背包组件引用（拖拽交换需要）
		SlotWidget->SetInventoryComponent(InvComp);

		// 放入容器
		QuickSlotContainer->AddChild(SlotWidget);

		SlotWidgets.Add(SlotWidget);
	}

	UE_LOG(LogTemp, Log, TEXT("[StatusBar] Created %d quick slot widgets"), SlotWidgets.Num());
}

// ==========================================
// 快捷栏：刷新显示
// ==========================================

void UUW_StatusBar::RefreshQuickSlots()
{
	if (!InvComp) return;

	// 刷新每个格子
	for (int32 i = 0; i < UInventoryComponent::QUICK_SLOT_COUNT; ++i)
	{
		RefreshSingleSlot(i);
	}

	// 更新选中高亮
	int32 SelectedIdx = InvComp->SelectedQuickSlotIndex;
	for (int32 i = 0; i < SlotWidgets.Num(); ++i)
	{
		if (SlotWidgets[i])
		{
			SlotWidgets[i]->SetSelected(i == SelectedIdx);
		}
	}
}

void UUW_StatusBar::RefreshSingleSlot(int32 Index)
{
	if (!InvComp || !SlotWidgets.IsValidIndex(Index)) return;

	UUW_QuickSlot* SlotWidget = SlotWidgets[Index];
	if (!SlotWidget) return;

	FItemInstance SlotItem = InvComp->GetQuickSlot(Index);

	if (SlotItem.IsEmpty())
	{
		SlotWidget->ClearSlot();
	}
	else
	{
		UItemDataBase* ItemData = InvComp->GetItemData(SlotItem.ItemID);
		SlotWidget->SetItemData(ItemData, SlotItem.Quantity);
	}
}

// ==========================================
// 快捷栏：事件回调
// ==========================================

void UUW_StatusBar::OnQuickSlotSelected(int32 SlotIndex)
{
	RefreshQuickSlots();
}

void UUW_StatusBar::OnQuickSlotChanged(int32 SlotIndex)
{
	RefreshSingleSlot(SlotIndex);
}

void UUW_StatusBar::OnEquipmentChanged(FName ItemID, bool bEquipped)
{
	// 装备变更时也刷新全部格子（可能影响武器高亮等状态）
	RefreshQuickSlots();
}
