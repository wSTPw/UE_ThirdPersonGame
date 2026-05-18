// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimNotifies/AnimNotify.h"  // UAnimNotify 基类
#include "AnimNotify_UseItemComplete.generated.h"

// 前向声明（避免在头文件中包含沉重的 Character 头文件）
class AMyPlayerCharacter;

/**
 * UAnimNotify_UseItemComplete — 使用物品动画完成通知
 *
 * 【用途】
 * 放在使用物品 Montage 的"执行效果帧"（如角色吞咽药水、挥舞武器的瞬间）。
 * 当动画播放到该 Notify 帧时，自动触发角色的物品使用完成逻辑。
 *
 * 【设计目的】
 * 将"视觉效果"与"数值效果"解耦：
 *   - 播放喝药水动画 → 视觉反馈
 *   - 动画播到"吞咽帧"时才真正回血/扣蓝 → 数值生效
 *
 * 【使用方式】
 * 在 AnimMontage 编辑器的 Notify Track 中，
 * 找到"执行效果"对应的帧位置，添加此 Notify 即可。
 *
 * 【调用链】
 * AnimMontage 播放到 Notify 帧
 *   → Notify() 被引擎自动调用
 *     → 从 MeshComp 获取 Owner Actor
 *       → Cast 为 AMyPlayerCharacter
 *         → PlayerChar->OnUseItemAnimFinished()
 *           → 执行实际的 ItemAction / 扣减数量等逻辑
 */
UCLASS()
class INTROCPP_API UAnimNotify_UseItemComplete : public UAnimNotify
{
	GENERATED_BODY()

public:

	/**
	 * 动画播放到此 Notify 帧时由引擎自动调用
	 *
	 * @param MeshComp      播放此动画的骨骼网格组件（通常是角色的 Mesh）
	 * @param Animation     正在播放的动画序列
	 * @param EventReference Notify 事件引用（含时间等信息）
	 */
	virtual void Notify(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation,
		const FAnimNotifyEventReference& EventReference) override;
};
