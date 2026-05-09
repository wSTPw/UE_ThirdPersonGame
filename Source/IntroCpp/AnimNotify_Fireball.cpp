// Fill out your copyright notice in the Description page of Project Settings.

#include "AnimNotify_Fireball.h"
#include "MyPlayerCharacter.h"
#include "Components/SkeletalMeshComponent.h"

void UAnimNotify_Fireball::Notify(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation,
	const FAnimNotifyEventReference& EventReference)
{
	Super::Notify(MeshComp, Animation, EventReference);

	if (!MeshComp) return;

	// 从骨骼网格组件获取拥有者 Actor
	AActor* Owner = MeshComp->GetOwner();
	if (!Owner) return;

	// 转换为玩家角色，调用火球发射方法
	if (AMyPlayerCharacter* PlayerChar = Cast<AMyPlayerCharacter>(Owner))
	{
		PlayerChar->FireFromHand();
	}
}
