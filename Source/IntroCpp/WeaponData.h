// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "ItemDataBase.h"       // UItemDataBase 基类
#include "EWeaponTypes.h"      // EWeaponAnimType 枚举（WeaponAnimType 字段需要）
#include "Animation/AnimMontage.h"  // OverrideAttackMontage 使用
#include "ComboAttackData.h"   // UComboAttackData（MeleeComboData 字段需要）
#include "WeaponData.generated.h"

/**
 * UWeaponData — 武器数据子类
 *
 * 继承自 UItemDataBase，扩展武器专属的战斗属性。
 * 只有装备武器或执行攻击时才需要访问这些字段。
 *
 * 【典型用途】
 *   - 火球法杖 (DA_WP_FireStaff)：投射物=BP_FireBall, 动画=Staff, 远程=true, MP消耗=10
 *   - 长刀 (DA_WP_LongSword)：动画=LongSword, 远程=false, 伤害=25
 *
 * 【装备流程】
 *   InventoryComponent::EquipItem(SlotIndex)
 *   → 角色监听 OnEquipmentChanged 委托
 *   → 读取 WeaponStaticMesh.LoadSynchronous()
 *   → AttachToComponent(HandSocketName)
 *   → 设置 Actor Scale = WeaponScale
 *
 * 【攻击流程】
 *   角色攻击输入 → 读取 GetEquippedWeaponData()
 *   → 根据 bIsRangedWeapon 分支：
 *     远程：SpawnActor(WeaponProjectileClass) 从 WeaponFireSocketName 发射
 *     近战：SphereTrace 检测 + ApplyDamage
 *
 * 【在编辑器中创建】
 *   右键 → Miscellaneous → Data Asset → 选择 WeaponData 类
 */
UCLASS(Blueprintable)
class INTROCPP_API UWeaponData : public UItemDataBase
{
	GENERATED_BODY()

public:
	/* 内联构造函数（实现写在头文件），无需额外 .cpp */
	UWeaponData();

	// ==========================================
	// 战斗属性
	// ==========================================

	/**
	 * 投射物 Actor 类（软引用）。
	 * 远程武器攻击时 Spawn 的蓝图类（如 BP_FireBall、BP_Arrow）。
	 * 近战武器留空即可。
	 * 软引用避免不使用的武器类型占用内存。
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
	TSoftClassPtr<AActor> WeaponProjectileClass;

	// ==========================================
	// 战斗属性 — 数值
	// ==========================================

	/** 是否为远程武器。true=发射投射物(Projectile), false=近战 SphereTrace 检测 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
	bool bIsRangedWeapon = true;

	/** 单次攻击消耗的法力值。0 = 不消耗 MP */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat|Stats")
	float WeaponManaCost = 0.0f;

	/**
	 * 伤害覆盖值。
	 * 0 = 使用投射物自身默认伤害（推荐，保持投射物自包含）
	 * 非0 = 强制覆盖投射物的 BaseDamage（特殊平衡调整用）
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat|Stats")
	int32 WeaponDamageOverride = 0;

	/** 攻击冷却时间（秒）。防止连点过快导致无限发射/挥砍 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat|Stats")
	float WeaponAttackCooldown = 0.5f;

	// ==========================================
	// 战斗属性 — 动画
	// ==========================================

	/**
	 * 攻击动画类型枚举。
	 * 决定角色使用 AttackMontageMap 中的哪个共享 Montage。
	 *
	 * 按"动作模式"而非"武器种类"分类，多把不同武器可共用同一套动画。
	 * 如需完全自定义，请使用 OverrideAttackMontage 字段。
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat|Animation")
	EWeaponAnimType WeaponAnimType = EWeaponAnimType::None;

	/**
	 * 专属攻击动画覆盖。
	 * 留空 = 走 WeaponAnimType → AttackMontageMap 的通用逻辑
	 * 非空 = 优先播放此 Montage（特殊武器需要独特动画时使用）
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat|Animation")
	UAnimMontage* OverrideAttackMontage = nullptr;

	// ==========================================
	// 战斗属性 — 发射
	// ==========================================

	/**
	 * 发射位置的 Socket 名称。
	 * 投射物生成时的起点（如 "hand_r"、"MuzzleFlash"）。
	 * 必须与角色骨骼中的 Socket 名称一致。
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat|Projectile")
	FName WeaponFireSocketName = TEXT("hand_r");

	// ==========================================
	// 外观属性
	// ==========================================

	/**
	 * 武器 StaticMesh（软引用）。
	 * 装备时附加到角色手部 Socket 显示的3D模型。
	 * 通过 LoadSynchronous() 同步加载（装备操作需要即时显示）。
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Appearance")
	TSoftObjectPtr<UStaticMesh> WeaponStaticMesh;

	/**
	 * 手部 Socket 名称（默认 "RightHand"）。
	 * 武器模型附着的骨骼 Socket，必须与角色 Mannequin/Skeleton 一致。
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Appearance")
	FName HandSocketName = TEXT("RightHand");

	/** 武器模型缩放比例。用于微调模型大小以匹配角色比例 (默认 1:1:1) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Appearance")
	FVector WeaponScale = FVector(1.0f, 1.0f, 1.0f);

	// ==========================================
	// 连击系统（仅近战武器使用）
	// ==========================================

	/**
	 * 近战连击配置数据的软引用
	 *
	 * - 当 bIsRangedWeapon = false 时生效
	 * - 指向一个 UComboAttackData DataAsset（包含 ComboMontage + 各段攻击参数）
	 * - 使用软引用避免不用的连击数据占用内存
	 * - 在 EquipWeapon() 中通过 LoadSynchronous() 预加载为强指针缓存
	 *
	 * 留空(null)的近战武器：无法进行连击，
	 * 攻击时 EnsureComboDataReady() 会返回 false 并拒绝执行。
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat|Melee Combo")
	TSoftObjectPtr<UComboAttackData> MeleeComboData;
};

// ---- 内联构造函数：自动设置 ItemType 为武器 ----
inline UWeaponData::UWeaponData()
{
	ItemType = EItemType::Weapon;
}
