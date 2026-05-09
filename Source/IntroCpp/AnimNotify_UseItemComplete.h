// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimNotifies/AnimNotify.h"
#include "AnimNotify_UseItemComplete.generated.h"

class AMyPlayerCharacter;

/**
 * 使用物品动画完成通知
 * 放在物品使用 Montage 的"执行效果帧"（如吞咽药水的瞬间），
 * 触发角色的 OnUseItemAnimFinished() 执行实际扣减+效果
 */
UCLASS()
class INTROCPP_API UAnimNotify_UseItemComplete : public UAnimNotify
{
	GENERATED_BODY()

public:
	// 动画播放到该 Notify 帧时自动调用
	virtual void Notify(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation,
		const FAnimNotifyEventReference& EventReference) override;
};
