// Fill out your copyright notice in the Description page of Project Settings.

#include "MyEventBusGameInstance.h"
#include "Kismet/GameplayStatics.h"

UMyEventBusGameInstance* UMyEventBusGameInstance::Get(const UObject* WorldContextObject)
{
    if (!IsValid(WorldContextObject)) return nullptr;
    UGameInstance* GameInstance = UGameplayStatics::GetGameInstance(WorldContextObject);
    return Cast<UMyEventBusGameInstance>(GameInstance);
}

// ====================== 无参数事件实现 ======================
void UMyEventBusGameInstance::Publish_NoParam(FName EventName)
{
    if (FGlobalEvent_NoParam* Event = NoParamEventMap.Find(EventName))
        Event->Broadcast();
}
void UMyEventBusGameInstance::Unsubscribe_NoParam(FName EventName, FDelegateHandle Handle)
{
    if (FGlobalEvent_NoParam* Event = NoParamEventMap.Find(EventName))
        if (Handle.IsValid()) Event->Remove(Handle);
}

// ====================== FString参数事件实现 ======================
void UMyEventBusGameInstance::Publish_StringParam(FName EventName, FString Value)
{
    if (FGlobalEvent_StringParam* Event = StringParamEventMap.Find(EventName))
        Event->Broadcast(Value);
}
void UMyEventBusGameInstance::Unsubscribe_StringParam(FName EventName, FDelegateHandle Handle)
{
    if (FGlobalEvent_StringParam* Event = StringParamEventMap.Find(EventName))
        if (Handle.IsValid()) Event->Remove(Handle);
}

// ====================== Int参数事件实现 ======================
void UMyEventBusGameInstance::Publish_IntParam(FName EventName, int32 Value)
{
    if (FGlobalEvent_IntParam* Event = IntParamEventMap.Find(EventName))
        Event->Broadcast(Value);
}
void UMyEventBusGameInstance::Unsubscribe_IntParam(FName EventName, FDelegateHandle Handle)
{
    if (FGlobalEvent_IntParam* Event = IntParamEventMap.Find(EventName))
        if (Handle.IsValid()) Event->Remove(Handle);
}

// ====================== Float参数事件实现 ======================
void UMyEventBusGameInstance::Publish_FloatParam(FName EventName, float Value)
{
    if (FGlobalEvent_FloatParam* Event = FloatParamEventMap.Find(EventName))
        Event->Broadcast(Value);
}
void UMyEventBusGameInstance::Unsubscribe_FloatParam(FName EventName, FDelegateHandle Handle)
{
    if (FGlobalEvent_FloatParam* Event = FloatParamEventMap.Find(EventName))
        if (Handle.IsValid()) Event->Remove(Handle);
}

// ====================== Actor参数事件实现 ======================
void UMyEventBusGameInstance::Publish_ActorParam(FName EventName, AActor* Actor)
{
    if (FGlobalEvent_ActorParam* Event = ActorParamEventMap.Find(EventName))
        Event->Broadcast(Actor);
}
void UMyEventBusGameInstance::Unsubscribe_ActorParam(FName EventName, FDelegateHandle Handle)
{
    if (FGlobalEvent_ActorParam* Event = ActorParamEventMap.Find(EventName))
        if (Handle.IsValid()) Event->Remove(Handle);
}

// ====================== 伤害双参数事件实现 ======================
void UMyEventBusGameInstance::Publish_DamageEvent(FName EventName, int32 Damage, AActor* Instigator)
{
    if (FGlobalEvent_Damage* Event = DamageEventMap.Find(EventName))
        Event->Broadcast(Damage, Instigator);
}
void UMyEventBusGameInstance::Unsubscribe_DamageEvent(FName EventName, FDelegateHandle Handle)
{
    if (FGlobalEvent_Damage* Event = DamageEventMap.Find(EventName))
        if (Handle.IsValid()) Event->Remove(Handle);
}