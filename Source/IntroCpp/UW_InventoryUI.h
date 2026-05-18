// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/Button.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Components/Border.h"                // 格子背景边框（替代 Button）
#include "Components/UniformGridPanel.h"
#include "InventoryComponent.h"           // FItemInstance + UInventoryComponent
#include "UDragItemOperation.h"          // 拖拽操作数据载体
#include "UW_InventoryUI.generated.h"

// 前向声明（避免循环包含）
class UButton;
class UTextBlock;
class UImage;
class UUniformGridPanel;
class UW_InventorySlot;   // 单个背包槽位 Widget（本文件下方定义）
class UUW_QuickSlot;      // 快捷栏 Widget（外部文件定义）

// ============================================================
//  UW_InventoryUI — 背包主界面 Widget
// ============================================================

/**
 * 背包主界面：显示所有背包槽位的网格 + 选中物品详情面板 + 操作按钮
 *
 * 【Widget 层次结构】(对应 UMG 蓝图)
 * ┌─────────────────────────────────────────────┐
 * │  [Sort]                    [Close]          │  ← 按钮
 * ├─────────────────────────────────────────────┤
 * │  Weight: x / Max   Items: N                │  ← 统计文本
 * ├─────────────────────────────────────────────┤
 * │  Grid_Inventory (UniformGridPanel)         │  ← 槽位网格容器
 * │  ┌──┐┌──┐┌──┐┌──┐┌──┐                     │
 * │  │S0││S1││S2││...│    │  (5列x4行=20格)    │  ← InventorySlot[]
 * │  └──┘└──┘└──┘└──┘└──┘                     │
 * ├─────────────────────────────────────────────┤
 * │  📷 Icon   Name                          │  ← 详情面板 (Optional)
 * │       Description                         │
 * │  [Use]  [Drop]                            │
 * └─────────────────────────────────────────────┘
 *
 * 【数据绑定方式】
 * SetInventoryComponent() → 绑定委托监听背包变更事件 → 自动 RefreshUI()
 *
 * 【拖拽系统角色】
 * 作为拖拽操作的中枢协调者：
 * - CreateDragOperation(): 为 Slot 创建拖拽数据+视觉图标
 * - HandleInventorySlotDrop(): 处理放到背包槽位的操作逻辑
 * - HandleQuickSlotDrop(): 处理放到快捷栏槽位的操作逻辑
 */
UCLASS()
class INTROCPP_API UUW_InventoryUI : public UUserWidget
{
	GENERATED_BODY()

protected:
	/** 构建时初始化按钮绑定、创建槽位、首次刷新*/
	virtual void NativeConstruct() override;

	/** 销毁时解绑所有按钮事件防止悬空引用*/
	virtual void NativeDestruct() override;

public:

	// ==========================================
	// 公开接口
	// ==========================================

	/**
	 * 设置要显示的背包组件引用，并自动绑定事件监听。
	 * 必须在 NativeConstruct 之后或显示前调用！
	 *
	 * @param InInventoryComponent 通常传入角色的 InventoryComp 指针
	 */
	UFUNCTION(BlueprintCallable, Category = "Inventory UI")
	void SetInventoryComponent(UInventoryComponent* InInventoryComponent);

	/** 全量刷新 UI：重新读取 Inventory 数据并更新每个 Slot 的显示 */
	UFUNCTION(BlueprintCallable, Category = "Inventory UI")
	void RefreshUI();

	// ==========================================
	// 图标异步加载（两个重载）
	// ==========================================

	/**
	 * 异步加载物品图标并设置到指定的 InventorySlot Widget
	 * 使用 StreamableManager 避免同步加载卡顿
	 *
	 * @param IconPath   图标的软引用路径
	 * @param SlotWidget 目标槽位 Widget（用于加载完成后设置 Image）
	 */
	void LoadItemIconAsync(const TSoftObjectPtr<UTexture2D>& IconPath, UW_InventorySlot* SlotWidget);

	/** 重载版本：目标为 QuickSlot Widget */
	void LoadItemIconAsync(const TSoftObjectPtr<UTexture2D>& IconPath, UUW_QuickSlot* SlotWidget);

	// ==========================================
	// UI 元素（BindWidget — 在蓝图中绑定对应 Named Widget）
	// ==========================================

	/** 背包槽位网格容器（UniformGridPanel，5列自动排列）*/
	UPROPERTY(meta = (BindWidget))
	UUniformGridPanel* Grid_Inventory;

	/** 当前重量显示文本 */
	UPROPERTY(meta = (BindWidget))
	UTextBlock* Text_CurrentWeight;

	/** 最大承重显示文本 */
	UPROPERTY(meta = (BindWidget))
	UTextBlock* Text_MaxWeight;

	/** 当前物品种类数显示文本 */
	UPROPERTY(meta = (BindWidget))
	UTextBlock* Text_ItemCount;

	/** 整理排序按钮 */
	UPROPERTY(meta = (BindWidget))
	UButton* Button_Sort;

	/** 关闭背包按钮 */
	UPROPERTY(meta = (BindWidget))
	UButton* Button_Close;

	// ---- 详情面板（BindWidgetOptional — 可选，没有也不报错）----

	/** 选中物品的图标预览 */
	UPROPERTY(meta = (BindWidgetOptional))
	UImage* Image_SelectedItemIcon;

	/** 选中物品的名称 */
	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* Text_SelectedItemName;

	/** 选中物品的描述 */
	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* Text_SelectedItemDescription;

	/** 使用物品按钮 */
	UPROPERTY(meta = (BindWidgetOptional))
	UButton* Button_UseItem;

	/** 丢弃物品按钮 */
	UPROPERTY(meta = (BindWidgetOptional))
	UButton* Button_DropItem;

	// ==========================================
	// 内部状态
	// ==========================================

	/** 所有背包槽位 Widget 的数组（与 Inventory[] 一一对应）*/
	UPROPERTY()
	TArray<UW_InventorySlot*> InventorySlots;

	/** 当前选中的槽位索引 (-1 = 未选中) */
	UPROPERTY()
	int32 SelectedSlotIndex = -1;

	/** 关联的背包组件指针（数据来源）*/
	UPROPERTY()
	UInventoryComponent* InventoryComponent;

	/**
	 * 槽位蓝图类（用于动态创建 InventorySlot）。
	 * 可在编辑器或蓝图中指定自定义子类来替换默认外观。
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "UI")
	TSubclassOf<UW_InventorySlot> SlotWidgetClass;

	// ==========================================
	// 槽位选择
	// ==========================================

	/** 处理某个槽位被点击/选中的事件 */
	void OnSlotSelected(int32 SlotIndex);

	// ==========================================
	// 拖拽处理接口（供 Slot Widget 的 OnDrop/OnDragCancelled 回调调用）
	// ==========================================

	/**
	 * 处理放置到背包槽位的拖拽操作
	 * 支持两种场景：
	 * - 来自背包其他槽位的内部交换 (SwapItems)
	 * - 来自快捷栏的放入 (SetItemAt + ClearQuickSlot)
	 *
	 * @return 操作是否成功执行
	 */
	bool HandleInventorySlotDrop(int32 TargetIndex, const UDragItemOperation& Operation);

	/**
	 * 处理放置到快捷栏槽位的拖拽操作
	 * @return 操作是否成功执行
	 */
	bool HandleQuickSlotDrop(int32 TargetIndex, const UDragItemOperation& Operation, UInventoryComponent* InvComp);

	/**
	 * 创建拖拽操作对象（含视觉跟随图标）
	 * 由 InventorySlot/QuickSlot 的 NativeOnDragDetected 调用
	 *
	 * @param SourceType 拖拽来源（背包 or 快捷栏）
	 * @param SlotIndex  源槽位索引
	 * @param Item       被拖拽的物品实例
	 * @param Icon       物品图标纹理（用于生成 DragVisual）
	 * @return           创建好的 DragDropOperation 对象
	 */
	UDragItemOperation* CreateDragOperation(EDragSource SourceType, int32 SlotIndex, const FItemInstance& Item, const TSoftObjectPtr<UTexture2D>& Icon);

protected:

	// ====== 内部辅助方法 ======

	/** 创建并排列所有 InventorySlot 到 Grid_Inventory 中（NativeConstruct 时调用）*/
	void InitializeSlots();

	/** 更新统计数字（重量/承重/数量）*/
	void UpdateInventoryInfo();

	/** 更新选中物品详情面板的显示内容 */
	void UpdateSelectedItemInfo();

	// ====== 按钮回调（UFUNCTION 绑定）======

	UFUNCTION()
	void OnButton_SortClicked();

	UFUNCTION()
	void OnButton_CloseClicked();

	UFUNCTION()
	void OnButton_UseItemClicked();

	UFUNCTION()
	void OnButton_DropItemClicked();

	// ====== 背包事件回调（从 InventoryComponent 委托绑定过来）======

	UFUNCTION()
	void OnInventoryUpdated();

	UFUNCTION()
	void OnItemAdded(const FItemInstance& Item);

	UFUNCTION()
	void OnItemRemoved(const FItemInstance& Item);

public:
	/** 背包关闭事件（点击关闭按钮时广播，让 GameMode/HUD 知道关闭了）*/
	DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnInventoryClosed);
	UPROPERTY(BlueprintAssignable, Category = "Inventory")
	FOnInventoryClosed OnInventoryClosed;
};

// ============================================================
//  UW_InventorySlot — 单个背包槽位 Widget
// ============================================================

/**
 * 背包中的单个格子 Widget，支持完整的 Slate 拖拽交互。
 *
 * 【Widget 结构】（与 QuickSlot 一致，用 Border 替代 Button 避免事件拦截）
 * ┌──────────────────────┐
 * │ Border_SlotBackground│  (背景边框，默认不拦截鼠标)
 * │ ┌──────────────────┐ │
 * │ │  Image_ItemIcon  │ │  (HitTestInvisible — 显示图标，透传鼠标)
 * │ │  Text_ItemQuantity│ │  (数量>1时显示数字)
 * │ └──────────────────┘ │
 * └──────────────────────┘
 *
 * 【交互行为】
 * - 点击（无拖拽）→ 选中该格（高亮 + 显示详情）
 * - 拖动物品 → 隐藏自身图标，生成跟随鼠标的 DragVisual
 * - 放到其他格子 → 触发 OnDrop 数据交换
 * - 拖拽取消 → 恢复图标显示
 *
 * 【关键设计】
 * 与 QuickSlot 保持一致：Image 有图标时设为 HitTestInvisible 透传鼠标，
 * 让鼠标事件穿透到 UserWidget 级别的 NativeOnMouseButtonDown/DragDetected 等，
 * 这样可以精确控制 Slate 原生拖拽流程而非依赖 Button Click 事件。
 */
UCLASS()
class INTROCPP_API UW_InventorySlot : public UUserWidget
{
	GENERATED_BODY()

public:
	/**
	 * 初始化槽位：记录自己的索引和父 UI 引用
	 * 由 UW_InventoryUI::InitializeSlots() 在创建每个 Slot 后调用
	 *
	 * @param InSlotIndex 此槽位在网格中的位置索引 [0, 19]
	 * @param InParentUI   父级背包 UI（用于回调选择/拖拽等操作）
	 */
	UFUNCTION(BlueprintCallable, Category = "Inventory Slot")
	void SetupSlot(int32 InSlotIndex, UUW_InventoryUI* InParentUI);

	/**
	 * 更新此槽位的显示内容
	 * 由父 UI RefreshUI() 时对每个 Slot 调用
	 *
	 * @param ItemInstance        要显示的数据（ID + 数量）
	 * @param InventoryComponent 用于获取 ItemData（读取图标等资源）
	 */
	UFUNCTION(BlueprintCallable, Category = "Inventory Slot")
	void UpdateSlot(const FItemInstance& ItemInstance, UInventoryComponent* InventoryComponent);

	/**
	 * 设置选中状态（高亮边框等视觉反馈）
	 * 由父 UI OnSlotSelected() 切换调用
	 */
	UFUNCTION(BlueprintCallable, Category = "Inventory Slot")
	void SetSelected(bool bSelected);

public:
	// ====== BindWidget 控件（蓝图中必须绑定同名控件）======

	/** 格子背景边框（与 QuickSlot 结构一致，用 Border 替代 Button 避免事件拦截）*/
	UPROPERTY(meta = (BindWidgetOptional))
	UBorder* Border_SlotBackground;

	/** 物品图标图片 */
	UPROPERTY(meta = (BindWidgetOptional))
	UImage* Image_ItemIcon;

	/** 数量文本（仅当 Quantity > 1 时显示）*/
	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* Text_ItemQuantity;

protected:
	/** Widget 构建完成时的初始化（设置控件可见性模式）*/
	virtual void NativeConstruct() override;

	// ====== Slate 拖拽事件覆写（完整拖拽生命周期 + 点击检测）======

	/**
	 * 鼠标按下 — 统一启动拖拽检测（空格/有物品都一样）
	 * 区分"点击还是拖拽"的逻辑在 NativeOnMouseButtonUp 中通过 bDragInitiated 标志判断：
	 *   松开时 bDragInitiated==false  → 纯点击 → 选中该格
	 *   移动超阈值后 bDragInitiated==true → 走拖拽流程
	 */
	virtual FReply NativeOnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;

	/** 鼠标松开 — 如果期间没有触发拖拽，则判定为"点击"行为（选中槽位）*/
	virtual FReply NativeOnMouseButtonUp(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;

	/** 拖拽检测通过后触发：创建 DragDropOperation 并隐藏自身图标 */
	virtual void NativeOnDragDetected(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent, UDragDropOperation*& OutOperation) override;

	/** 拖拽取消（松开在无效区域）：恢复图标可见性 + 重置标志 */
	virtual void NativeOnDragCancelled(const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation) override;

	/** 有拖动物品放到此格子上时触发 */
	virtual bool NativeOnDrop(const FGeometry& MyGeometry, const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation) override;

	/** 拖拽经过此格子上方时触发（返回 true = 允许放置）*/
	virtual bool NativeOnDragOver(const FGeometry& MyGeometry, const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation) override;

	/** 拖拽离开此格子区域时触发 */
	virtual void NativeOnDragLeave(const FDragDropEvent& InDragDropEvent, UDragDropOperation* InOperation) override;

private:

	int32 SlotIndex = -1;              // 自己在第几个格子
	bool bIsSelected = false;          // 是否当前被选中高亮
	bool bDragInitiated = false;       // 本轮按下→松开期间是否已进入拖拽流程（用于区分点击 vs 拖拽）
	UUW_InventoryUI* ParentUI = nullptr; // 父级 UI 引用（回调用）

	/** 缓存的当前物品实例数据（用于发起拖拽时携带数据）*/
	FItemInstance CachedItem;
};
