// Fill out your copyright notice in the Description page of Project Settings.

#include "UW_InventoryUI.h"
#include "UW_QuickSlot.h"              // QuickSlot Widget（快捷栏拖拽需要）
#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "Components/Image.h"
#include "Components/UniformGridPanel.h"
#include "Components/UniformGridSlot.h"
#include "Engine/Texture2D.h"
#include "Engine/StreamableManager.h"   // 异步加载图标
#include "Engine/AssetManager.h"
#include "Widgets/SWidget.h"
#include "Blueprint/WidgetBlueprintLibrary.h"  // DetectDragIfPressed
#include "Components/Image.h"

// ============================================================================
//  UUW_InventoryUI — 背包主界面实现
// ============================================================================

/**
 * NativeConstruct: Widget 创建完成后的初始化入口
 * 绑定所有按钮事件 → 初始化槽位网格 → 首次刷新显示
 */
void UUW_InventoryUI::NativeConstruct()
{
	Super::NativeConstruct();

	// ====== 绑定按钮点击事件（安全检查 + AddDynamic）======
	if (Button_Sort) { Button_Sort->OnClicked.AddDynamic(this, &UUW_InventoryUI::OnButton_SortClicked); }
	if (Button_Close) { Button_Close->OnClicked.AddDynamic(this, &UUW_InventoryUI::OnButton_CloseClicked); }
	if (Button_UseItem) { Button_UseItem->OnClicked.AddDynamic(this, &UUW_InventoryUI::OnButton_UseItemClicked); }
	if (Button_DropItem) { Button_DropItem->OnClicked.AddDynamic(this, &UUW_InventoryUI::OnButton_DropItemClicked); }

	// 确保网格容器可用且可见
	if (Grid_Inventory)
	{
		Grid_Inventory->SetVisibility(ESlateVisibility::Visible);
		Grid_Inventory->SetIsEnabled(true);
	}

	// 创建 20 个 Slot Widget 并排列到 Grid 中，然后首次刷新
	InitializeSlots();
	RefreshUI();
}

/**
 * NativeDestruct: Widget 销毁前清理
 * 移除所有按钮绑定防止悬空回调导致 Crash
 */
void UUW_InventoryUI::NativeDestruct()
{
	if (Button_Sort) { Button_Sort->OnClicked.RemoveDynamic(this, &UUW_InventoryUI::OnButton_SortClicked); }
	if (Button_Close) { Button_Close->OnClicked.RemoveDynamic(this, &UUW_InventoryUI::OnButton_CloseClicked); }
	if (Button_UseItem) { Button_UseItem->OnClicked.RemoveDynamic(this, &UUW_InventoryUI::OnButton_UseItemClicked); }
	if (Button_DropItem) { Button_DropItem->OnClicked.RemoveDynamic(this, &UUW_InventoryUI::OnButton_DropItemClicked); }

	Super::NativeDestruct();
}

// ============================================================================
//  公开接口实现
// ============================================================================

/**
 * 设置背包组件引用并自动绑定事件监听
 * 此方法是 UI 与数据层连接的桥梁！
 */
void UUW_InventoryUI::SetInventoryComponent(UInventoryComponent* InInventoryComponent)
{
	InventoryComponent = InInventoryComponent;

	if (InventoryComponent)
	{
		// ★ 绑定三个核心事件委托 —— 数据变化时自动刷新 UI
		InventoryComponent->OnInventoryUpdated.AddUObject(this, &UUW_InventoryUI::OnInventoryUpdated);  // 全量刷新
		InventoryComponent->OnItemAdded.AddUObject(this, &UUW_InventoryUI::OnItemAdded);            // 增量更新统计
		InventoryComponent->OnItemRemoved.AddUObject(this, &UUW_InventoryUI::OnItemRemoved);         // 增量+清除选中
	}

	RefreshUI();  // 绑定后立即刷新一次以显示当前数据
}

/**
 * 全量刷新：遍历 Inventory 数据更新每个 Slot 的显示 + 更新详情面板
 * 由 OnInventoryUpdated 委托触发，也可手动调用
 */
void UUW_InventoryUI::RefreshUI()
{
	if (!InventoryComponent || !Grid_Inventory) return;

	// 更新顶部统计信息栏
	UpdateInventoryInfo();

	// 遍历背包数据并更新每个对应 Slot 的内容
	const TArray<FItemInstance>& Items = InventoryComponent->GetAllItems();
	for (int32 i = 0; i < InventorySlots.Num() && i < Items.Num(); i++)
	{
		InventorySlots[i]->UpdateSlot(Items[i], InventoryComponent);
	}

	// 更新选中物品的详情面板
	UpdateSelectedItemInfo();
}

// ============================================================================
//  槽位初始化
// ============================================================================

/**
 * 在 UniformGridPanel 中创建 20 个 InventorySlot Widget
 * 排列方式：5列 x 4行，共 20 格
 */
void UUW_InventoryUI::InitializeSlots()
{
	if (!Grid_Inventory) return;

	// 如果未指定自定义 Slot 类，使用默认的 UW_InventorySlot
	if (!SlotWidgetClass)
	{
		SlotWidgetClass = UW_InventorySlot::StaticClass();
	}

	// 清空旧槽位（防止重复初始化时堆积）
	Grid_Inventory->ClearChildren();
	InventorySlots.Empty();

	const int32 MaxSlots = 20;
	const int32 SlotsPerRow = 5;  // 每行5格

	for (int32 i = 0; i < MaxSlots; i++)
	{
		// 创建 Slot Widget 实例
		UW_InventorySlot* SlotWidget = CreateWidget<UW_InventorySlot>(this, SlotWidgetClass);
		if (SlotWidget)
		{
			// 初始化 Slot 的索引和父 UI 引用
			SlotWidget->SetupSlot(i, this);
			InventorySlots.Add(SlotWidget);

			// 添加到 Grid 并设置行列位置
			UUniformGridSlot* GridSlot = Grid_Inventory->AddChildToUniformGrid(SlotWidget);
			if (GridSlot)
			{
				GridSlot->SetColumn(i % SlotsPerRow);     // 列 = 索引 % 5 (0,1,2,3,4,0,1...)
				GridSlot->SetRow(i / SlotsPerRow);          // 行 = 索引 / 5 (0,0,0,0,0,1,1...)
				GridSlot->SetHorizontalAlignment(HAlign_Fill);   // 水平填满格子
				GridSlot->SetVerticalAlignment(VAlign_Fill);       // 垂直填满格子
			}
		}
	}
}

// ============================================================================
//  信息面板更新
// ============================================================================

/** 更新顶部的重量、承重、物品种类数文本 */
void UUW_InventoryUI::UpdateInventoryInfo()
{
	if (!InventoryComponent) return;

	if (Text_CurrentWeight) { Text_CurrentWeight->SetText(FText::FromString(FString::Printf(TEXT("%.1f"), InventoryComponent->CurrentWeight))); }
	if (Text_MaxWeight)     { Text_MaxWeight->SetText(FText::FromString(FString::Printf(TEXT("%.1f"), InventoryComponent->MaxWeight))); }
	if (Text_ItemCount)      { Text_ItemCount->SetText(FText::FromString(FString::Printf(TEXT("%d"), InventoryComponent->CurrentItemCount))); }
}

/**
 * 更新右侧选中物品详情面板
 * 根据 SelectedSlotIndex 显示对应的 Icon/Name/Description，
 * 控制 Use/Drop 按钮的 Enable 状态。
 *
 * 三种状态处理：
 * - 无选中 / 槽位空 / 找不到 ItemData → 清空详情面板
 * - 有选中且有有效数据 → 显示完整信息
 */
void UUW_InventoryUI::UpdateSelectedItemInfo()
{
	// 无效选中状态 → 清空面板
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

	// 选中格是空的 → 清除选中标记并清空面板
	if (SelectedItem.IsEmpty())
	{
		if (Image_SelectedItemIcon)    { Image_SelectedItemIcon->SetBrushFromTexture(nullptr); Image_SelectedItemIcon->SetVisibility(ESlateVisibility::Collapsed); }
		if (Text_SelectedItemName)      Text_SelectedItemName->SetText(FText::GetEmpty());
		if (Text_SelectedItemDescription) Text_SelectedItemDescription->SetText(FText::GetEmpty());
		if (Button_UseItem)             Button_UseItem->SetIsEnabled(false);
		if (Button_DropItem)            Button_DropItem->SetIsEnabled(false);
		SelectedSlotIndex = -1;  // 重置选中状态
		return;
	}

	// 通过 Subsystem 获取物品静态配置数据
	UItemDataBase* ItemData = InventoryComponent->GetItemData(SelectedItem.ItemID);
	if (!ItemData)
	{
		// 物品数据找不到（可能 DataAsset 未注册或已删除）→ 显示空白
		if (Image_SelectedItemIcon)    { Image_SelectedItemIcon->SetBrushFromTexture(nullptr); Image_SelectedItemIcon->SetVisibility(ESlateVisibility::Collapsed); }
		if (Text_SelectedItemName)      Text_SelectedItemName->SetText(FText::GetEmpty());
		if (Text_SelectedItemDescription) Text_SelectedItemDescription->SetText(FText::GetEmpty());
		if (Button_UseItem)             Button_UseItem->SetIsEnabled(false);
		if (Button_DropItem)            Button_DropItem->SetIsEnabled(false);
		return;
	}

	// ====== 正常情况：有选中 + 有数据 ======

	// 名称和描述（FText 支持本地化）
	if (Text_SelectedItemName)       Text_SelectedItemName->SetText(ItemData->ItemName);
	if (Text_SelectedItemDescription) Text_SelectedItemDescription->SetText(ItemData->ItemDescription);

	// 按钮 Enable 状态根据物品配置决定
	if (Button_UseItem)              Button_UseItem->SetIsEnabled(ItemData->bCanUse);
	if (Button_DropItem)             Button_DropItem->SetIsEnabled(ItemData->bCanDrop);

	// 图标（异步加载）
	if (Image_SelectedItemIcon)
	{
		if (!ItemData->ItemIcon.IsNull())
		{
			Image_SelectedItemIcon->SetVisibility(ESlateVisibility::Visible);
			LoadItemIconAsync(ItemData->ItemIcon, static_cast<UUW_QuickSlot*>(nullptr));  // nullptr 表示加载到详情面板
		}
		else
		{
			Image_SelectedItemIcon->SetBrushFromTexture(nullptr);
			Image_SelectedItemIcon->SetVisibility(ESlateVisibility::Collapsed);
		}
	}
}

// ============================================================================
//  按钮事件回调
// ============================================================================

void UUW_InventoryUI::OnButton_SortClicked()        { if (InventoryComponent) InventoryComponent->SortItems(); }

/** 关闭背包：广播关闭事件 + 从父级移除自身 Widget */
void UUW_InventoryUI::OnButton_CloseClicked()
{
	OnInventoryClosed.Broadcast();    // 通知外部（如 HUD/GameMode）
	RemoveFromParent();             // 从 UI 层级移除
}

/** 使用当前选中的物品 */
void UUW_InventoryUI::OnButton_UseItemClicked()
{
	if (InventoryComponent && SelectedSlotIndex != -1)
	{
		InventoryComponent->UseItem(SelectedSlotIndex);
	}
}

/** 丢弃当前选中的物品 */
void UUW_InventoryUI::OnButton_DropItemClicked()
{
	if (InventoryComponent && SelectedSlotIndex != -1)
	{
		InventoryComponent->DropItem(SelectedSlotIndex);
		SelectedSlotIndex = -1;  // 丢弃后清除选中
		// 清空详情面板显示
		if (Image_SelectedItemIcon)    { Image_SelectedItemIcon->SetBrushFromTexture(nullptr); Image_SelectedItemIcon->SetVisibility(ESlateVisibility::Collapsed); }
		if (Text_SelectedItemName)      Text_SelectedItemName->SetText(FText::GetEmpty());
		if (Text_SelectedItemDescription) Text_SelectedItemDescription->SetText(FText::GetEmpty());
		if (Button_UseItem)             Button_UseItem->SetIsEnabled(false);
		if (Button_DropItem)            Button_DropItem->SetIsEnabled(false);
		RefreshUI();
	}
}

// ============================================================================
//  拖拽操作工厂
// ============================================================================

/**
 * 创建拖拽操作对象——包含数据和视觉图标
 *
 * 由 InventorySlot/QuickSlot 的 NativeOnDragDetected 调用
 * 返回的 Operation 会由 Slate 拖拽系统传递给目标 Widget 的 OnDrop
 *
 * @param SourceType 来源类型（Inventory 或 QuickSlot）
 * @param SlotIndex  源槽位索引
 * @param Item       被拖拽的物品实例数据
 * @param Icon       物品图标纹理（用于生成跟随鼠标的 DragVisual）
 * @return           配置完成的 DragDropOperation 对象
 */
UDragItemOperation* UUW_InventoryUI::CreateDragOperation(EDragSource SourceType, int32 SlotIndex, const FItemInstance& Item, const TSoftObjectPtr<UTexture2D>& Icon)
{
	// 在 TransientPackage 中创建（不归属任何持久对象，拖拽结束即被 GC 回收）
	UDragItemOperation* Operation = NewObject<UDragItemOperation>(GetTransientPackage());

	// 填充拖拽数据
	Operation->SourceType = SourceType;
	Operation->SourceIndex = SlotIndex;
	Operation->DraggedItem = Item;
	Operation->ItemIconTexture = Icon;

	// 创建拖拽视觉图标（一个跟随鼠标指针的 Image Widget）
	if (!Icon.IsNull())
	{
		UTexture2D* LoadedTex = Icon.LoadSynchronous();  // 小纹理同步加载可接受
		if (LoadedTex)
		{
			UImage* DragVisual = NewObject<UImage>(GetTransientPackage());
			DragVisual->SetBrushFromTexture(LoadedTex);
			Operation->DefaultDragVisual = DragVisual;
		}
	}

	// 设置拖拽锚点为中心居中
	Operation->Pivot = EDragPivot::CenterCenter;

	UE_LOG(LogTemp, Log, TEXT("[Drag] Created operation: type=%d index=%d item=%s"), (int32)SourceType, SlotIndex, *Item.ItemID.ToString());
	return Operation;
}

// ============================================================================
//  拖拽放置处理
// ============================================================================

/**
 * 处理放置到背包槽位的操作
 *
 * 场景A：来自背包其他槽位的内部交换
 *   → 直接调用 SwapItems()（原地交换两个索引的内容）
 *
 * 场景B：来自快捷栏的放入
 *   → 目标空：直接 SetItemAt + ClearQuickSlot（移动）
 *   → 目标非空：交换双方内容
 *
 * @note 不在此处手动 RefreshUI！SetItemAt/SetQuickSlot/ClearQuickSlot 各自通过委托触发 UI 刷新
 *       手动再调会导致重复渲染/状态闪烁（历史 Bug 的根因）
 */
bool UUW_InventoryUI::HandleInventorySlotDrop(int32 TargetIndex, const UDragItemOperation& Operation)
{
	if (!InventoryComponent || Operation.DraggedItem.IsEmpty()) return false;

	if (Operation.IsFromInventory())
	{
		// === 场景A：背包内部交换 ===
		int32 SrcIdx = Operation.SourceIndex;
		if (SrcIdx == TargetIndex) return false;  // 放回原位，忽略

		InventoryComponent->SwapItems(SrcIdx, TargetIndex);
		// SwapItems 内部已调用 BroadcastInventoryUpdate → 触发 OnInventoryUpdated → RefreshUI，无需重复

		UE_LOG(LogTemp, Log, TEXT("[Drag] Swapped inventory slots %d <-> %d"), SrcIdx, TargetIndex);
		return true;
	}
	else if (Operation.IsFromQuickSlot())
	{
		// === 场景B：快捷栏 → 背包 ===
		FItemInstance TargetItem = InventoryComponent->GetItemAt(TargetIndex);
		FItemInstance SrcQSItem = InventoryComponent->GetQuickSlot(Operation.SourceIndex);

		if (TargetItem.IsEmpty())
		{
			// 目标空：直接把快捷栏物品放入背包该格 + 清空快捷栏原格
			InventoryComponent->SetItemAt(TargetIndex, SrcQSItem);
			InventoryComponent->ClearQuickSlot(Operation.SourceIndex);
		}
		else
		{
			// 目标非空：交换（背包得到快捷栏物品，快捷栏得到背包物品）
			InventoryComponent->SetItemAt(TargetIndex, SrcQSItem);
			InventoryComponent->SetQuickSlot(Operation.SourceIndex, TargetItem);
		}

		// 各操作内部已通过委托触发 UI 刷新，不重复 RefreshUI
		UE_LOG(LogTemp, Log, TEXT("[Drag] QuickSlot %d -> Inventory slot %d"), Operation.SourceIndex, TargetIndex);
		return true;
	}

	return false;  // 未知来源类型，拒绝
}

/**
 * 处理放置到快捷栏的操作（由 UW_InventoryUI 协调调用）
 *
 * 场景A：来自背包 → 快捷栏
 *   目标空：快捷栏设为源物品 + 清空背包源格
 *   目标非空：交换
 *
 * 场景B：快捷栏内部交换
 */
bool UUW_InventoryUI::HandleQuickSlotDrop(int32 TargetIndex, const UDragItemOperation& Operation, UInventoryComponent* InvComp)
{
	if (!InvComp || Operation.DraggedItem.IsEmpty()) return false;

	if (Operation.IsFromInventory())
	{
		// === 背包 → 快捷栏 ===
		FItemInstance ExistingQSItem = InvComp->GetQuickSlot(TargetIndex);
		FItemInstance SrcInvItem = InventoryComponent->GetItemAt(Operation.SourceIndex);

		if (ExistingQSItem.IsEmpty())
		{
			// 目标快捷格为空：移入 + 清空源
			InvComp->SetQuickSlot(TargetIndex, SrcInvItem);
			InventoryComponent->SetItemAt(Operation.SourceIndex, FItemInstance());
		}
		else
		{
			// 目标非空：双向交换
			InvComp->SetQuickSlot(TargetIndex, SrcInvItem);
			InventoryComponent->SetItemAt(Operation.SourceIndex, ExistingQSItem);
		}

		UE_LOG(LogTemp, Log, TEXT("[Drag] Inventory slot %d -> QuickSlot %d"), Operation.SourceIndex, TargetIndex);
		return true;
	}
	else if (Operation.IsFromQuickSlot())
	{
		// === 快捷栏内部交换 ===
		if (Operation.SourceIndex == TargetIndex) return true;  // 放回自己，忽略

		FItemInstance SrcItem = InvComp->GetQuickSlot(Operation.SourceIndex);
		FItemInstance DstItem = InvComp->GetQuickSlot(TargetIndex);

		InvComp->SetQuickSlot(Operation.SourceIndex, DstItem);
		InvComp->SetQuickSlot(TargetIndex, SrcItem);

		UE_LOG(LogTemp, Log, TEXT("[Drag] QuickSlot %d <-> %d swap"), Operation.SourceIndex, TargetIndex);
		return true;
	}

	return false;
}

// ============================================================================
//  槽位选择逻辑
// ============================================================================

/**
 * 处理某个槽位被选中的事件
 * 取消旧高亮 → 设置新选中 → 更新详情面板
 */
void UUW_InventoryUI::OnSlotSelected(int32 SlotIndex)
{
	// 取消之前选中格的高亮
	if (SelectedSlotIndex != -1 && SelectedSlotIndex < InventorySlots.Num())
	{
		InventorySlots[SelectedSlotIndex]->SetSelected(false);
	}

	// 设置新的选中状态
	SelectedSlotIndex = SlotIndex;

	// 高亮新选中的格子
	if (SelectedSlotIndex != -1 && SelectedSlotIndex < InventorySlots.Num())
	{
		InventorySlots[SelectedSlotIndex]->SetSelected(true);
	}

	// 刷新详情面板显示新选中物品的信息
	UpdateSelectedItemInfo();
}

// ============================================================================
//  背包事件回调（从 InventoryComponent 委托驱动）
// ============================================================================

/** 背包任何变化 → 全量 RefreshUI */
void UUW_InventoryUI::OnInventoryUpdated()          { RefreshUI(); }

/** 新增物品 → 仅更新统计数字（不需要重建整个网格，性能优化）*/
void UUW_InventoryUI::OnItemAdded(const FItemInstance& Item) { UpdateInventoryInfo(); }

/** 物品移除 → 更新统计 + 如果选中的被删了则清除选中 */
void UUW_InventoryUI::OnItemRemoved(const FItemInstance& Item)
{
	UpdateInventoryInfo();
	if (SelectedSlotIndex != -1)
	{
		FItemInstance SelectedItem = InventoryComponent->GetItemAt(SelectedSlotIndex);
		if (SelectedItem.IsEmpty())
		{
			SelectedSlotIndex = -1;
			UpdateSelectedItemInfo();  // 清空详情面板
		}
	}
}

// ============================================================================
//  图标异步加载
// ============================================================================

/**
 * 异步加载物品图标到 InventorySlot
 * 使用 StreamableManager.RequestAsyncLoad 实现异步加载，
 * 避免大量物品同时 LoadSynchronous 导致帧卡顿。
 *
 * 加载流程：
 * 1. 先将目标 Image 设为 HitTestInvisible（加载中状态，不可见但不阻挡事件）
 * 2. RequestAsyncLoad 发起异步请求
 * 3. 加载完成回调中设置 Texture 到 Image 并保持 HitTestInvisible
 * 4. 若加载失败则 Collapsed 隐藏
 */
void UUW_InventoryUI::LoadItemIconAsync(const TSoftObjectPtr<UTexture2D>& IconPath, UW_InventorySlot* SlotWidget)
{
	// 空路径 → 直接隐藏图标
	if (IconPath.IsNull())
	{
		if (SlotWidget && SlotWidget->Image_ItemIcon)
		{
			SlotWidget->Image_ItemIcon->SetBrushFromTexture(nullptr);
			SlotWidget->Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed);
		}
		else if (Image_SelectedItemIcon)  // 详情面板图标
		{
			Image_SelectedItemIcon->SetBrushFromTexture(nullptr);
			Image_SelectedItemIcon->SetVisibility(ESlateVisibility::Collapsed);
		}
		return;
	}

	// 通过 AssetManager 的 StreamableManager 发起异步加载
	FStreamableManager& StreamableManager = UAssetManager::GetStreamableManager();
	FSoftObjectPath Path = IconPath.ToSoftObjectPath();

	// 设置加载中的可见性状态
	if (SlotWidget && SlotWidget->Image_ItemIcon)
	{
		SlotWidget->Image_ItemIcon->SetVisibility(ESlateVisibility::HitTestInvisible);
	}
	else if (Image_SelectedItemIcon)
	{
		Image_SelectedItemIcon->SetVisibility(ESlateVisibility::HitTestInvisible);
	}

	// 发起异步加载请求（Lambda 回调在加载完成后在 GameThread 执行）
	StreamableManager.RequestAsyncLoad(Path,
		[this, SlotWidget](TSharedPtr<FStreamableHandle> Handle)
		{
			// 加载完成回调：获取加载好的 Texture2D 对象
			UTexture2D* LoadedTexture = Cast<UTexture2D>(Handle ? Handle->GetLoadedAsset() : nullptr);
			if (LoadedTexture)
			{
				// 成功：设置纹理并显示
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
				// 加载失败：隐藏图标
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

/**
 * 异步加载图标的重载版本 — 目标为 QuickSlot Widget
 * 逻辑与上方完全相同，仅最终设置的目标 Widget 类型不同
 */
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

// ============================================================================
//  UW_InventorySlot — 单个背包槽位 Widget 实现
// ============================================================================

void UW_InventorySlot::SetupSlot(int32 InSlotIndex, UUW_InventoryUI* InParentUI)
{
	SlotIndex = InSlotIndex;
	ParentUI = InParentUI;
}

/**
 * 更新此槽位的显示内容
 * 缓存 ItemInstance 以便后续拖拽时携带数据
 */
void UW_InventorySlot::UpdateSlot(const FItemInstance& ItemInstance, UInventoryComponent* InventoryComponent)
{
	CachedItem = ItemInstance;  // 缓存！（拖拽发起时需要读取）

	if (ItemInstance.IsEmpty())
	{
		// 空：隐藏图标和数量
		if (Image_ItemIcon) { Image_ItemIcon->SetBrushFromTexture(nullptr); Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed); }
		if (Text_ItemQuantity) Text_ItemQuantity->SetText(FText::GetEmpty());
		return;
	}

	// 获取物品配置数据以读取图标等信息
	UItemDataBase* ItemData = InventoryComponent ? InventoryComponent->GetItemData(ItemInstance.ItemID) : nullptr;
	if (!ItemData)
	{
		// 找不到物品数据 → 只能隐藏图标
		if (Image_ItemIcon) { Image_ItemIcon->SetBrushFromTexture(nullptr); Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed); }
		return;
	}

	// 异步加载图标（通过父 UI 的 StreamableManager）
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

	// 数量文字：只有 >1 时才显示数字（单数时不显示 "1" 占空间）
	if (Text_ItemQuantity)
	{
		Text_ItemQuantity->SetText(
			ItemInstance.Quantity > 1
				? FText::FromString(FString::Printf(TEXT("%d"), ItemInstance.Quantity))
				: FText::GetEmpty()
		);
	}
}

/** 设置选中状态（预留：蓝图中可根据 IsSelected 改变边框颜色等样式）*/
void UW_InventorySlot::SetSelected(bool bSelected)
{
	bIsSelected = bSelected;
	// 可扩展：根据 bSelected 切换边框颜色/图片高亮等
	// （已移除 Button_Slot，如需视觉反馈可在蓝图中绑定 IsSelected 到对应属性）
}

/** Widget 构建完成：设置控件初始可见性模式 */
void UW_InventorySlot::NativeConstruct()
{
	Super::NativeConstruct();
	// ★ 对齐 QuickSlot 的做法：Image 初始 Collapsed（避免空纹理显示白色方块）
	// 不需要设 HitTestInvisible — UpdateSlot / 异步加载回调中会在有图标时设置
	if (Image_ItemIcon) Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed);
}

/**
 * 鼠标按下 — 统一启动拖拽检测（空格和有物品行为相同）
 *
 * 不再在此处区分"点击"还是"拖拽"，而是：
 * 1. 重置 bDragInitiated = false
 * 2. 统一调用 DetectDragIfPressed 让 Slate 监控移动阈值
 * 3. 松开时在 NativeOnMouseButtonUp 中检查标志：
 *    - bDragInitiated == false → 没有触发过拖拽 → 判定为"点击" → 选中槽位
 *    - bDragInitiated == true  → 已经进入拖拽流程 → 忽略（拖拽有自己的 OnDrop/Cancel 路径）
 */
FReply UW_InventorySlot::NativeOnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	// 只响应左键
	if (MouseEvent.GetEffectingButton() != EKeys::LeftMouseButton) return FReply::Unhandled();

	// 重置本轮拖拽标志
	bDragInitiated = false;

	// 无论空格还是有物品，都启动拖拽检测
	// 区分点击/拖拽的判断留给 NativeOnMouseButtonUp 处理
	return UWidgetBlueprintLibrary::DetectDragIfPressed(MouseEvent, this, EKeys::LeftMouseButton).NativeReply;
}

/**
 * 鼠标松开 — 点击/拖拽二选一判定点
 *
 * 如果从按下到松开期间没有触发过 NativeOnDragDetected（bDragInitiated==false），
 * 说明用户只是普通点击了一下 → 执行选中行为。
 */
FReply UW_InventorySlot::NativeOnMouseButtonUp(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	if (MouseEvent.GetEffectingButton() != EKeys::LeftMouseButton) return FReply::Unhandled();

	// 本轮未进入拖拽 → 判定为纯点击 → 选中此格
	if (!bDragInitiated && ParentUI)
	{
		ParentUI->OnSlotSelected(SlotIndex);
	}

	return FReply::Handled();
}

/**
 * 拖拽检测通过后触发 — 创建 DragDropOperation 并隐藏自身图标
 *
 * 此时用户已经按住 LMB 并移动超过了 Slate 拖拽阈值距离
 * 我们需要创建携带数据的 Operation 对象供后续 OnDrop 使用
 */
void UW_InventorySlot::NativeOnDragDetected(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent, UDragDropOperation*& OutOperation)
{
	Super::NativeOnDragDetected(MyGeometry, MouseEvent, OutOperation);

	// 标记本轮已进入拖拽流程（让 NativeOnMouseButtonUp 知道这不是点击）
	bDragInitiated = true;

	if (!ParentUI || CachedItem.IsEmpty()) return;

	// 从 Subsystem 获取物品图标用于生成拖拽视觉
	TSoftObjectPtr<UTexture2D> IconPtr;
	if (ParentUI->InventoryComponent)
	{
		UItemDataBase* Data = ParentUI->InventoryComponent->GetItemData(CachedItem.ItemID);
		if (Data) IconPtr = Data->ItemIcon;
	}

	// 委托父 UI 创建完整的拖拽操作（含数据 + 视觉图标 Widget）
	OutOperation = ParentUI->CreateDragOperation(EDragSource::Inventory, SlotIndex, CachedItem, IconPtr);

	// 隐藏自身图标（已被"拿起"，用 Collapsed 完全移除避免干扰拖拽事件路由）
	if (Image_ItemIcon) Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed);

	UE_LOG(LogTemp, Log, TEXT("[InvSlot] DragDetected from slot=%d"), SlotIndex);
}

/**
 * 拖拽取消 — 用户松开鼠标但不在有效的 Drop 目标上
 * 恢复自身图标的可见性（HitTestInvisible 保持事件穿透特性）
 */
void UW_InventorySlot::NativeOnDragCancelled(const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation)
{
	Super::NativeOnDragCancelled(InDragDropEvent, InOperation);

	// 拖拽已取消，重置标志（虽然本轮即将结束，但保持状态一致性）
	bDragInitiated = false;

	// 恢复视觉（如果缓存中有物品数据的话）
	if (Image_ItemIcon && !CachedItem.IsEmpty())
		Image_ItemIcon->SetVisibility(ESlateVisibility::HitTestInvisible);

	UE_LOG(LogTemp, Log, TEXT("[InvSlot] DragCancelled at slot=%d (restored)"), SlotIndex);
}

/**
 * 有拖动物品放到此格子上 — 核心放置处理
 *
 * 流程：
 * 1. 尝试 Cast 为我们的 UDragItemOperation（拒绝其他类型的拖放操作）
 * 2. 委托给父 UI HandleInventorySlotDrop 执行实际的数据交换
 * 3. 放置成功后自动选中此格（让用户看到交换结果）
 */
bool UW_InventorySlot::NativeOnDrop(const FGeometry& MyGeometry, const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation)
{
	Super::NativeOnDrop(MyGeometry, InDragDropEvent, InOperation);

	UE_LOG(LogTemp, Log, TEXT("[InvSlot] *** OnDrop FIRED at slot=%d, InOperation=%s ***"), SlotIndex, *GetNameSafe(InOperation));

	// 安全转换拖拽操作类型
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

	UE_LOG(LogTemp, Log, TEXT("[InvSlot] OnDrop at target=%d, source type=%d idx=%d"),
		SlotIndex, (int32)DragOp->SourceType, DragOp->SourceIndex);

	// ★ 委托给父 UI 执行实际数据操作（背包内交换 or 快捷栏放入等）
	bool bResult = ParentUI->HandleInventorySlotDrop(SlotIndex, *DragOp);

	// 放置成功 → 选中此目标格（显示交换后的结果）
	if (bResult && ParentUI)
	{
		ParentUI->OnSlotSelected(SlotIndex);
	}

	return bResult;
}

/** 拖拽经过此格子上方 — 返回是否允许放置（有合法 DragOp 即允许）*/
bool UW_InventorySlot::NativeOnDragOver(const FGeometry& MyGeometry, const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation)
{
	const UDragItemOperation* DragOp = Cast<UDragItemOperation>(InOperation);
	UE_LOG(LogTemp, Log, TEXT("[InvSlot] DragOver at slot=%d, operation=%s"), SlotIndex, DragOp ? TEXT("ValidDragOp") : (InOperation ? TEXT("OtherOp") : TEXT("NULL")));
	return DragOp != nullptr;
}

/** 拖拽离开此格子区域 */
void UW_InventorySlot::NativeOnDragLeave(const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation)
{
	UE_LOG(LogTemp, Log, TEXT("[InvSlot] DragLeave slot=%d"), SlotIndex);
}
