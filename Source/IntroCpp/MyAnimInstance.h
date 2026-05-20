#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "EWeaponTypes.h"
#include "MyAnimInstance.generated.h"

/**
 * 项目统一的 AnimInstance 基类。
 *
 * 暴露 CurrentWeaponAnimType 供 Animation Blueprint 读取，
 * ABP 侧用 Switch on EWeaponAnimType 根据武器类型切换 locomotion BlendSpace。
 *
 * ABP_Move 需要重新设置父类为 MyAnimInstance 才能使用此属性。
 */
UCLASS(Blueprintable, BlueprintType)
class INTROCPP_API UMyAnimInstance : public UAnimInstance
{
	GENERATED_BODY()

public:
	/** 当前装备武器对应的动画类型。由角色在 EquipWeapon/UnequipWeapon 时设置。None = 空手。 */
	UPROPERTY(BlueprintReadOnly, Category = "Locomotion")
	EWeaponAnimType CurrentWeaponAnimType = EWeaponAnimType::None;
};
