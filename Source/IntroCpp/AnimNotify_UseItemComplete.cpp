// Fill out your copyright notice in the Description page of Project Settings.

#include "AnimNotify_UseItemComplete.h"
#include "MyPlayerCharacter.h"
#include "Components/SkeletalMeshComponent.h"

void UAnimNotify_UseItemComplete::Notify(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation,
	const FAnimNotifyEventReference& EventReference)
{
	Super::Notify(MeshComp, Animation, EventReference);

	if (!MeshComp) return;

	// 从骨骼网格组件获取拥有者 Actor
	AActor* Owner = MeshComp->GetOwner();
	if (!Owner) return;

	// 转换为玩家角色，调用使用物品完成方法
	if (AMyPlayerCharacter* PlayerChar = Cast<AMyPlayerCharacter>(Owner))
	{
		PlayerChar->OnUseItemAnimFinished();
	}
}
