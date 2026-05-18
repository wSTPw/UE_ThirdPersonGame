// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimNotifies/AnimNotify.h"
#include "AnimNotify_EnemyAttack.generated.h"

/**
 * 敌人攻击帧通知
 *
 * 在攻击 Montage 的精确帧放置此 Notify，
 * 当动画播到此帧时自动触发敌人的实际伤害检测。
 *
 * 使用方式:
 *   1. 打开攻击 Montage（如 M_SlimeAttack）
 *   2. 在 Notify Track 上找到挥砍/爪击的那一帧
 *   3. 添加此 Notify
 *   4. 到达该帧时自动调用 AEnemyBase::OnAttackAnimNotify()
 */
UCLASS()
class INTROCPP_API UAnimNotify_EnemyAttack : public UAnimNotify
{
	GENERATED_BODY()

public:

	virtual void Notify(
		USkeletalMeshComponent* MeshComp,
		UAnimSequenceBase* Animation,
		const FAnimNotifyEventReference& EventReference
	) override;
};
