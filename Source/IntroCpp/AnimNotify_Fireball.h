// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimNotifies/AnimNotify.h"
#include "AnimNotify_Fireball.generated.h"

class AMyPlayerCharacter;

/**
 * 火球发射动画通知
 * 放在攻击 Montage 的"施法释放帧"，触发角色的 FireFromHand()
 */
UCLASS()
class INTROCPP_API UAnimNotify_Fireball : public UAnimNotify
{
	GENERATED_BODY()

public:
	// 动画播放到该 Notify 帧时自动调用
	virtual void Notify(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation,
		const FAnimNotifyEventReference& EventReference) override;
};
