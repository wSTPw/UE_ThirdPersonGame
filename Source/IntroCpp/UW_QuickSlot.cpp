// Fill out your copyright notice in the Description page of Project Settings.

#include "UW_QuickSlot.h"
#include "UW_InventoryUI.h"           // 父 UI 类型（OnDrop 时可能需要）
#include "Engine/Texture2D.h"
#include "Components/Border.h"
#include "Blueprint/WidgetBlueprintLibrary.h"  // DetectDragIfPressed
#include "Components/Image.h"

// ============================================================================
//  NativeConstruct — 初始化
// ============================================================================

void UUW_QuickSlot::NativeConstruct()
{
	Super::NativeConstruct();
	// 图标初始 Collapsed（避免空纹理显示为白色方块）
	if (Image_ItemIcon) Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed);
}

// ============================================================================
//  数据绑定方法
// ============================================================================

/**
 * 填充此格的显示内容并缓存数据供拖拽使用
 *
 * 与 InventorySlot 的差异：此处使用**同步加载**图标（快捷栏只有5格，
 * 同步 LoadSynchronous 的开销完全可接受，代码也更简洁）
 */
void UUW_QuickSlot::SetItemData(UItemDataBase* ItemData, int32 Quantity)
{
	if (!ItemData)
	{
		ClearSlot();
		return;
	}

	// ★ 缓存数据（拖拽发起时需要读取 ItemID 和 Icon）★
	CachedItem = FItemInstance(ItemData->ItemID, Quantity);
	CachedIconTexture = ItemData->ItemIcon;

	// === 设置图标 ===
	if (Image_ItemIcon)
	{
		if (!ItemData->ItemIcon.IsNull())
		{
			// 同步加载图标纹理（小文件，<1ms，5格总量可接受）
			UTexture2D* IconTexture = ItemData->ItemIcon.LoadSynchronous();
			if (IconTexture)
			{
				Image_ItemIcon->SetBrushFromTexture(IconTexture);
				Image_ItemIcon->SetVisibility(ESlateVisibility::HitTestInvisible);
			}
			else
			{
				Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed);  // 加载失败则隐藏
			}
		}
		else
		{
			Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed);  // 无配置图标则隐藏
		}
	}

	// === 设置数量文字 ===
	if (Text_Count)
	{
		if (Quantity > 1)
		{
			Text_Count->SetText(FText::FromString(FString::FromInt(Quantity)));
			Text_Count->SetVisibility(ESlateVisibility::Visible);
		}
		else
		{
			Text_Count->SetVisibility(ESlateVisibility::Collapsed);  // 数量为1时不显示
		}
	}
}

/** 清空此格：重置所有缓存和视觉状态 */
void UUW_QuickSlot::ClearSlot()
{
	CachedItem = FItemInstance();       // 清空物品数据
	CachedIconTexture.Reset();          // 清空图标引用

	if (Image_ItemIcon) { Image_ItemIcon->SetBrushFromTexture(nullptr); Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed); }
	if (Text_Count)      { Text_Count->SetText(FText::GetEmpty()); Text_Count->SetVisibility(ESlateVisibility::Hidden); }
}

/** 切换选中高亮边框的可见性 */
void UUW_QuickSlot::SetSelected(bool bSelected)
{
	if (Border_Highlight)
	{
		Border_Highlight->SetVisibility(bSelected ? ESlateVisibility::Visible : ESlateVisibility::Hidden);
	}
}

// ============================================================================
//  拖拽事件实现
// ============================================================================

/**
 * 鼠标按键按下 — 有物品时开始拖拽检测
 * 与 InventorySlot 类似但更简洁（不需要空格选中逻辑）
 */
FReply UUW_QuickSlot::NativeOnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	// 只响应左键 + 必须有物品才允许拖拽
	if (MouseEvent.GetEffectingButton() != EKeys::LeftMouseButton || CachedItem.IsEmpty())
		return FReply::Unhandled();

	// 让 Slate 检测拖拽阈值
	return UWidgetBlueprintLibrary::DetectDragIfPressed(MouseEvent, this, EKeys::LeftMouseButton).NativeReply;
}

/**
 * 拖拽检测通过 — 创建 DragDropOperation
 *
 * 注意：QuickSlot 自己创建 Operation（不经过父 UI 的 CreateDragOperation 工厂）,
 * 因为 QuickSlot 可能独立于背包 UI 使用。
 */
void UUW_QuickSlot::NativeOnDragDetected(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent, UDragDropOperation*& OutOperation)
{
	Super::NativeOnDragDetected(MyGeometry, MouseEvent, OutOperation);

	if (CachedItem.IsEmpty()) return;

	// 创建拖拽操作对象
	UDragItemOperation* Operation = NewObject<UDragItemOperation>(GetTransientPackage());
	Operation->SourceType = EDragSource::QuickSlot;     // 标记来源为快捷栏
	Operation->SourceIndex = SlotIndex;                 // 源槽位索引
	Operation->DraggedItem = CachedItem;                // 拖拽的数据
	Operation->ItemIconTexture = CachedIconTexture;      // 拖拽的图标

	// 生成跟随鼠标的视觉图标 Widget
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
	Operation->Pivot = EDragPivot::CenterCenter;        // 居中锚点

	OutOperation = Operation;

	// 隐藏自身图标（已被"拿起"）
	if (Image_ItemIcon) Image_ItemIcon->SetVisibility(ESlateVisibility::Collapsed);

	UE_LOG(LogTemp, Log, TEXT("[QuickSlot] DragDetected from slot=%d"), SlotIndex);
}

/** 拖拽取消 — 恢复图标 */
void UUW_QuickSlot::NativeOnDragCancelled(const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation)
{
	Super::NativeOnDragCancelled(InDragDropEvent, InOperation);

	if (Image_ItemIcon && !CachedItem.IsEmpty())
		Image_ItemIcon->SetVisibility(ESlateVisibility::HitTestInvisible);

	UE_LOG(LogTemp, Log, TEXT("[QuickSlot] DragCancelled at slot=%d (restored)"), SlotIndex);
}

// ============================================================================
//  接收拖放
// ============================================================================

/**
 * 有拖动物品放到此快捷格上时的处理逻辑
 *
 * QuickSlot 的 OnDrop 直接操作数据（不经过父 UI 中转），
 * 因为快捷栏可能独立于背包主 UI 存在和使用。
 *
 * 三种场景：
 * 1. 背包 → 快捷栏（IsFromInventory）
 *    - 目标空：移入 + 清源格
 *    - 目标非空：交换 + 多余的回背包（AddItem）
 * 2. 快捷栏 → 快捷栏（IsFromQuickSlot，不同索引）
 *    - 双向 SetQuickSlot 交换
 * 3. 放回自己 → 忽略
 */
bool UUW_QuickSlot::NativeOnDrop(const FGeometry& MyGeometry, const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation)
{
	Super::NativeOnDrop(MyGeometry, InDragDropEvent, InOperation);

	const UDragItemOperation* DragOp = Cast<UDragItemOperation>(InOperation);
	if (!DragOp || !InvComp) return false;

	// 放回自己 → 忽略（无操作）
	if (DragOp->SourceType == EDragSource::QuickSlot && DragOp->SourceIndex == SlotIndex)
		return false;

	UE_LOG(LogTemp, Log, TEXT("[QuickSlot] OnDrop at target=%d, source type=%d idx=%d"),
		SlotIndex, (int32)DragOp->SourceType, DragOp->SourceIndex);

	// 读取当前目标格的内容（用于交换判断）
	FItemInstance ExistingItem = InvComp->GetQuickSlot(SlotIndex);

	if (DragOp->IsFromInventory())
	{
		// ====== 场景1：来自背包 ======
		if (ExistingItem.IsEmpty())
		{
			// 目标空：快捷栏设为源物品 + 清空背包源槽位
			InvComp->SetQuickSlot(SlotIndex, DragOp->DraggedItem);
			InvComp->SetItemAt(DragOp->SourceIndex, FItemInstance());  // 清空背包源格
		}
		else
		{
			// 目标非空：快捷栏放新物品 + 旧快捷栏物品回背包 + 清空源格
			InvComp->SetQuickSlot(SlotIndex, DragOp->DraggedItem);
			InvComp->AddItem(ExistingItem.ItemID, ExistingItem.Quantity);   // 旧物品回背包
			InvComp->SetItemAt(DragOp->SourceIndex, FItemInstance());         // 清空源格
		}
	}
	else if (DragOp->IsFromQuickSlot())
	{
		// ====== 场景2：快捷栏内部交换 ======
		FItemInstance SrcItem = InvComp->GetQuickSlot(DragOp->SourceIndex);
		InvComp->SetQuickSlot(DragOp->SourceIndex, ExistingItem);  // 源 ← 当前目标
		InvComp->SetQuickSlot(SlotIndex, SrcItem);               // 目标 ← 源
	}

	// 操作成功
	return true;
}

/** 拖拽经过：有合法 DragOp 即允许放置 */
bool UUW_QuickSlot::NativeOnDragOver(const FGeometry& MyGeometry, const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation)
{
	return Cast<UDragItemOperation>(InOperation) != nullptr;
}

/** 拖拽离开（无特殊操作）*/
void UUW_QuickSlot::NativeOnDragLeave(const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation) {}
