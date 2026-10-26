// Fill out your copyright notice in the Description page of Project Settings.
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "InputActionValue.h" // 增强输入必需
#include "UW_MainHUD.h"
#include "InventoryComponent.h"
#include "AttributeComponent.h"
#include "UW_StatusBar.h"
#include "WeaponData.h"       // UWeaponData（当前武器数据指针）
#include "EWeaponTypes.h"     // EWeaponAnimType（AttackMontageMap 的 Key）
#include "ComboAttackData.h"  // UComboAttackData（连击系统配置缓存）
#include "MyAnimInstance.h"   // UMyAnimInstance（locomotion 动画类型通信）
#include "Components/StaticMeshComponent.h"
#include "Actions/CharacterActionComponent.h"
#include "MyPlayerCharacter.generated.h"

UCLASS()
class INTROCPP_API AMyPlayerCharacter : public ACharacter
{
    GENERATED_BODY()

public:
    // 构造函数
    AMyPlayerCharacter();

protected:
    // 游戏开始时调用
    virtual void BeginPlay() override;

public:
    // 每帧调用
    virtual void Tick(float DeltaTime) override;

public:
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

    // 如果需要在编辑器/构造时处理
    virtual void OnConstruction(const FTransform& Transform) override;

    // 输入绑定调用
    virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;

    // ==============================================
    // 组件声明（摄像机相关）
    // ==============================================
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
    class USpringArmComponent* SpringArm;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
    class UCameraComponent* Camera;

    // ==============================================
    // 增强输入配置（在蓝图里指定）
    // ==============================================
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Input")
    class UInputMappingContext* InputMapping;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Input")
    class UInputAction* IA_Move;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Input")
    class UInputAction* IA_Look;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Input")
    class UInputAction* IA_Jump;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Input")
    class UInputAction* IA_Inventory;  // 背包开关

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Input")
    class UInputAction* IA_Attack;  // 攻击（鼠标左键）

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Input")
    class UInputAction* IA_UseItem;  // 使用物品（鼠标右键/长按）

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Input")
    class UInputAction* IA_QuickSlot1;  // 快捷栏1
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Input")
    class UInputAction* IA_QuickSlot2;  // 快捷栏2
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Input")
    class UInputAction* IA_QuickSlot3;  // 快捷栏3
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Input")
    class UInputAction* IA_QuickSlot4;  // 快捷栏4
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Input")
    class UInputAction* IA_QuickSlot5;  // 快捷栏5

public:
    // ==============================================
	// 背包组件（在蓝图里指定）
    // ==============================================
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Inventory")
    UInventoryComponent* InventoryComponent;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Actions")
    TObjectPtr<UCharacterActionComponent> Actions;

    // ==============================================
	// 属性组件（HP/MP管理）
    // ==============================================
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Attributes")
    UAttributeComponent* AttributeComp;

    // ==============================================
    // 背包UI
    // ==============================================
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    void ToggleInventory();

    UPROPERTY(EditDefaultsOnly, Category = "UI")
    TSubclassOf<class UUW_InventoryUI> InventoryUIClass;

    UPROPERTY()
    UUW_InventoryUI* InventoryUIInstance;

    // ==============================================
	// 状态栏UI（HP/MP显示）
    // ==============================================
    UFUNCTION(BlueprintCallable, Category = "Status")
    void ShowStatusBar();

	UFUNCTION(BlueprintCallable, Category = "Status")
	void HideStatusBar();

	UFUNCTION(BlueprintCallable, Category = "Status")
	void ToggleStatusBar();  // 开关切换

	UPROPERTY(EditDefaultsOnly, Category = "UI")
	TSubclassOf<class UUW_StatusBar> StatusBarUIClass;

	UPROPERTY()
	UUW_StatusBar* StatusBarInstance;

	// ==============================================
	// 攻击系统（武器数据驱动）
	// ==============================================

	/** 当前缓存的武器数据（由 InventoryComponent.Equip 时传入，指针引用不拷贝） */
	UPROPERTY(Transient)
	TObjectPtr<UWeaponData> CurrentWeaponData;

	/** 当前装备的 ItemID（用于日志/调试等需要重新查 Subsystem 时） */
	FName CurrentWeaponID = NAME_None;

	/**
	 * 攻击动画共享池（蓝图中配置一次）
	 * Key = 动画类型枚举, Value = 对应的 Montage 资产
	 * 武器只存 EWeaponAnimType 枚举值 → 从此 Map 取出实际 Montage
	 *
	 * 示例配置（蓝图 Defaults）：
	 *   Staff     → M_Attack_Staff
	 *   LongBlade → M_Attack_LongBlade
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Attack")
	TMap<EWeaponAnimType, UAnimMontage*> AttackMontageMap;

	/** Compatibility mirror written by Actions; requests must query the component. */
	bool bIsAttacking = false;

	/** 设置攻击状态，同步推送到 AnimInstance */
	void SetAttacking(bool bInAttacking);

	/** Compatibility mirror written by Actions. */
	bool bIsUsingItem = false;

	/** 装备中的武器网格体组件（动态创建，挂到手部 Socket，复用为通用手持物品模型） */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Equipment")
	UStaticMeshComponent* WeaponMeshComp = nullptr;

	UFUNCTION(BlueprintCallable, Category = "Attack")
	void Attack();

	// ---- 装备/卸装武器 ----

	/**
	 * 装备武器（由 InventoryComponent.EquipItem 内部调用）
	 * 缓存 CurrentWeaponData 指针，预加载远程投射物软引用
	 */
	UFUNCTION(BlueprintCallable, Category = "Equipment")
	void EquipWeapon(UWeaponData* InWeaponData);

	/** 卸下武器（清空缓存） */
	UFUNCTION(BlueprintCallable, Category = "Equipment")
	void UnequipWeapon();

	/** 监听 InventoryComponent 的 OnEquipmentChanged 委托 */
	UFUNCTION()
	void HandleEquipmentChanged(FName ItemID, bool bEquipped);

	// ---- 手持物品系统（快捷栏选中时在手上显示模型） ----

	/**
	 * 在手上显示任意物品的模型（通用方法，武器/消耗品等均可）
	 * @param ItemData  物品数据（从中读取 StaticMesh / WeaponStaticMesh）
	 */
	UFUNCTION(BlueprintCallable, Category = "Equipment")
	void ShowHeldItem(UItemDataBase* ItemData);

	/** 清除手上的物品模型 */
	UFUNCTION(BlueprintCallable, Category = "Equipment")
	void ClearHeldItem();

	/** 快捷栏切换回调：根据新选中的格子自动装备武器或显示物品模型 */
	UFUNCTION()
	void HandleQuickSlotSelectionChanged(int32 SlotIndex);

	// ---- 发射 / 近战 ----

	/** Legacy unkeyed entry: warns and rejects. Use Actions + identified notify. */
	UFUNCTION(BlueprintCallable, Category = "Attack")
	void FireFromHand();

	/** 近战命中检测预留（当前仅 Log） */
	UFUNCTION(BlueprintCallable, Category = "Attack")
	void MeleeHitCheck();

	// ---- 使用物品系统（Minecraft 模式，右键） ----

	/** Minecraft 模式：使用当前手持物品（播放动画 → AnimNotify 回调 → 执行效果） */
	UFUNCTION(BlueprintCallable, Category = "Equipment")
	void UseHeldItem();

	/** Legacy unkeyed item notification: warns and rejects. */
	void OnUseItemAnimFinished();

	/** Legacy direct effect entry: rejects calls without execution identity. */
	void ExecuteItemUseEffect(UItemDataBase* ItemData, int32 SlotIndex);

	/** Legacy direct effect entry: rejects calls without execution identity. */
	void ExecuteItemActions(UItemDataBase* ItemData, int32 SlotIndex);

	/** 刷新手部模型显示（重新评估选中槽位应显示的物品/武器） */
	void RefreshHeldItemDisplay();

	/** 快捷栏内容变化回调（拖放/数量变化时触发，仅刷新当前选中槽位的手部模型） */
	UFUNCTION()
	void OnQuickSlotContentChanged(int32 SlotIndex);

	// ==============================================
	// 连击系统（近战武器专用，远程武器不使用）
	// ==============================================

private:
	void UpdateLocomotionAnimType();



	// ---- AnimNotify 回调（由 Notify 类调用，需 public）----

public:

	/** 近战命中 Notify 回调入口（由 AnimNotify_MeleeHit::Notify 触发）*/
	void OnMeleeHitNotify();

	// ---- 外部查询接口（给 UI、其他系统使用）----

	/** 获取当前正在执行的连击段数（0-based，Idle 时为 0）*/
	int32 GetCurrentComboIndex() const { return Actions ? Actions->GetSnapshot().ComboIndex : 0; }

	/** 是否正处于连击攻击过程中（任意段都在算）*/
	bool IsInComboAttack() const { return Actions && Actions->GetSnapshot().Kind == ECharacterActionKind::Melee; }

	// ---- 蓝图扩展点（BlueprintImplementableEvent）----

	/**
	 * 近战攻击命中时的蓝图扩展点
	 *
	 * 在 MeleeHitCheck() SphereTrace 命中目标后调用。
	 * 蓝图中可添加：命中特效、打击音效、屏幕震动、帧冻结(Hit Stop)、
	 * 连击计数UI 刷新等效果。
	 *
	 * @param HitResult     SphereTrace 的命中结果（含位置/法线/命中Actor 等）
	 * @param ComboHitIndex 当前是第几段攻击（0-based）
	 * @param SubHitIndex   当前是该段内第几次子判定（0-based，无 SubHits 时恒为 0）
	 * @param FinalDamage   本次造成的最终伤害值
	 */
	UFUNCTION(BlueprintImplementableEvent, Category = "Combat|Combo",
		meta = (DisplayName = "On Melee Attack Hit"))
	void BP_OnMeleeAttackHit(const FHitResult& HitResult, int32 ComboHitIndex, int32 SubHitIndex, float FinalDamage);

	/**
	 * 连击段推进时的蓝图扩展点
	 *
	 * 在 Actions 成功开始下一段后调用。
	 * 蓝图中可添加：段切换特效、音效变化、连击数字弹出等反馈。
	 *
	 * @param NewComboIndex 推进后的新段数索引（0-based）
	 */
	UFUNCTION(BlueprintImplementableEvent, Category = "Combat|Combo",
		meta = (DisplayName = "On Combo Advanced"))
	void BP_OnComboAdvanced(int32 NewComboIndex);

	/**
	 * 连击重置时的蓝图扩展点
	 *
	 * 在 Actions 统一结束近战执行时调用。
	 * 蓝图中可清理连击相关 UI、停止连击音效等。
	 *
	 * @param bWasInterrupted 是否被外部因素打断（受伤、切武器等）
	 */
	UFUNCTION(BlueprintImplementableEvent, Category = "Combat|Combo",
		meta = (DisplayName = "On Combo Reset"))
	void BP_OnComboReset(bool bWasInterrupted);

private:
    // ==============================================
    // 输入逻辑函数
    // ==============================================
    void Move(const FInputActionValue& Value);   // 移动
    void Look(const FInputActionValue& Value);   // 视角
    void JumpStart();                             // 跳跃开始
    void JumpEnd();                               // 跳跃结束
	void AttackStarted();                         // 攻击输入触发
	void UseItemStarted();                        // 使用物品输入按下（右键）
	void UseItemCompleted();                      // 使用物品输入松开（右键）
	void OnQuickSlot1Pressed();
	void OnQuickSlot2Pressed();
	void OnQuickSlot3Pressed();
	void OnQuickSlot4Pressed();
	void OnQuickSlot5Pressed();
	void OnQuickSlotPressed(int32 SlotIndex);     // 快捷栏按键（1~5）

    // ==============================================
    // 物品拾取相关（在 cpp 中实现）
    // ==============================================
public:
    // 将指定 Actor 的拾取重叠事件绑定到本角色
    void BindItemPickup(AActor* Actor);

    // 解绑
    void UnbindItemPickup(AActor* Actor);

protected:
    // 处理 Actor 的重叠拾取事件（绑定签名：AActor* OverlappedActor, AActor* OtherActor）
    UFUNCTION()
    void OnItemPickup(AActor* OverlappedActor, AActor* OtherActor);

private:
    // 跟踪已绑定的 Actor（避免重复绑定）
    TSet<AActor*> ItemOverlapEvents;

    // 背包是否打开中（用于拦截游戏输入）
    bool bIsInventoryOpen = false;

    // 背包关闭回调（UI按钮关闭时触发）
    UFUNCTION()
    void OnInventoryUIClosed();
};
