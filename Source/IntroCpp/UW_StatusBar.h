// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/ProgressBar.h"
#include "Components/TextBlock.h"
#include "AttributeComponent.h"
#include "ItemDataBase.h"
#include "UW_StatusBar.generated.h"

class UInventoryComponent;
class UUW_QuickSlot;

/**
 * 状态栏UI - 显示角色HP、MP 和 5格快捷栏
 */
UCLASS()
class INTROCPP_API UUW_StatusBar : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;

	// ==========================================
	// 初始化：绑定属性组件（HP/MP）
	// ==========================================
	UFUNCTION(BlueprintCallable, Category = "Status Bar")
	void InitWithAttributes(UAttributeComponent* InAttrComp);

	// ==========================================
	// 初始化：绑定背包组件（快捷栏数据源）
	// ==========================================
	UFUNCTION(BlueprintCallable, Category = "QuickSlot")
	void InitWithInventory(UInventoryComponent* InInvComp);

	// ==========================================
	// UI控件 — HP/MP（在蓝图中BindWidget）
	// ==========================================

	UPROPERTY(meta = (BindWidget))
	UProgressBar* ProgressBar_HP;

	UPROPERTY(meta = (BindWidget))
	UProgressBar* ProgressBar_MP;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* Text_HP;

	UPROPERTY(meta = (BindWidgetOptional))
	UTextBlock* Text_MP;

	// ==========================================
	// UI控件 — 快捷栏容器（在蓝图中 BindWidgetOptional）
	// ==========================================

	/** 快捷栏格子容器（HorizontalBox 或 Overlay），用于程序化创建子 Widget */
	UPROPERTY(meta = (BindWidgetOptional))
	class UPanelWidget* QuickSlotContainer;

	// ==========================================
	// 快捷栏刷新（供外部调用，如装备变更后）
	// ==========================================

	/** 刷新所有5个格子的显示 + 高亮 */
	UFUNCTION(BlueprintCallable, Category = "QuickSlot")
	void RefreshQuickSlots();

private:
	// 引用的属性组件
	UPROPERTY()
	UAttributeComponent* AttributeComp;

	// 引用的背包组件（快捷栏数据源）
	UPROPERTY()
	UInventoryComponent* InvComp;

	// 5 个快捷栏子 Widget 实例
	UPROPERTY()
	TArray<UUW_QuickSlot*> SlotWidgets;

	// 单格 Widget 类（蓝图子类）
	UPROPERTY(EditDefaultsOnly, Category = "QuickSlot")
	TSubclassOf<UUW_QuickSlot> QuickSlotWidgetClass;

	// ==========================================
	// HP/MP 事件回调
	// ==========================================
	UFUNCTION()
	void OnHealthChanged(float CurrentHP, float MaxHP);

	UFUNCTION()
	void OnManaChanged(float CurrentMP, float MaxMP);

	void UpdateHealthDisplay(float Current, float Max);
	void UpdateManaDisplay(float Current, float Max);

	// ==========================================
	// 快捷栏事件回调
	// ==========================================
	UFUNCTION()
	void OnQuickSlotSelected(int32 SlotIndex);

	UFUNCTION()
	void OnQuickSlotChanged(int32 SlotIndex);

	UFUNCTION()
	void OnEquipmentChanged(FName ItemID, bool bEquipped);

	/** 创建5个 QuickSlot 子 Widget 并放入 Container */
	void CreateSlotWidgets();

	/** 根据当前 InvComp 数据刷新单个格子 */
	void RefreshSingleSlot(int32 Index);
};
