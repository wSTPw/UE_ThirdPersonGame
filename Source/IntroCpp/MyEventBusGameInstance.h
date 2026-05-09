// Fill out your copyright notice in the Description page of Project Settings.

#pragma once
#include "CoreMinimal.h"
#include "Engine/GameInstance.h"
#include "MyEventBusGameInstance.generated.h"

// ====================== 全局委托声明（必须在 generated.h 之后）======================
DECLARE_MULTICAST_DELEGATE(FGlobalEvent_NoParam);
DECLARE_MULTICAST_DELEGATE_OneParam(FGlobalEvent_StringParam, FString);
DECLARE_MULTICAST_DELEGATE_OneParam(FGlobalEvent_IntParam, int32);
DECLARE_MULTICAST_DELEGATE_OneParam(FGlobalEvent_FloatParam, float);
DECLARE_MULTICAST_DELEGATE_OneParam(FGlobalEvent_ActorParam, AActor*);
DECLARE_MULTICAST_DELEGATE_TwoParams(FGlobalEvent_Damage, int32, AActor*);

UCLASS()
class INTROCPP_API UMyEventBusGameInstance : public UGameInstance
{
    GENERATED_BODY()

public:
    static UMyEventBusGameInstance* Get(const UObject* WorldContextObject);

    // ====================== 无参数事件 ======================
    template<typename UserClass>
    FDelegateHandle Subscribe_NoParam(FName EventName, UserClass* Listener, void (UserClass::* Callback)())
    {
        if (!IsValid(Listener)) return FDelegateHandle();
        FGlobalEvent_NoParam& Event = NoParamEventMap.FindOrAdd(EventName);
        return Event.AddUObject(Listener, Callback);
    }// Lambda 版本（只传事件名 + Lambda，不传 this）
    template<typename LambdaType>
    FDelegateHandle Subscribe_NoParam(FName EventName, LambdaType&& Callback)
    {
        FGlobalEvent_NoParam& Event = NoParamEventMap.FindOrAdd(EventName);
        return Event.AddLambda(Forward<LambdaType>(Callback));
    }
    void Publish_NoParam(FName EventName);
    void Unsubscribe_NoParam(FName EventName, FDelegateHandle Handle);

    // ====================== String参数事件 ======================
    template<typename UserClass>
    FDelegateHandle Subscribe_StringParam(FName EventName, UserClass* Listener, void (UserClass::* Callback)(FString))
    {
        if (!IsValid(Listener)) return FDelegateHandle();
        FGlobalEvent_StringParam& Event = StringParamEventMap.FindOrAdd(EventName);
        return Event.AddUObject(Listener, Callback);
    }
    void Publish_StringParam(FName EventName, FString Value);
    void Unsubscribe_StringParam(FName EventName, FDelegateHandle Handle);

    // ====================== Int参数事件 ======================
    template<typename UserClass>
    FDelegateHandle Subscribe_IntParam(FName EventName, UserClass* Listener, void (UserClass::* Callback)(int32))
    {
        if (!IsValid(Listener)) return FDelegateHandle();
        FGlobalEvent_IntParam& Event = IntParamEventMap.FindOrAdd(EventName);
        return Event.AddUObject(Listener, Callback);
    }
    void Publish_IntParam(FName EventName, int32 Value);
    void Unsubscribe_IntParam(FName EventName, FDelegateHandle Handle);

    // ====================== Float参数事件 ======================
    template<typename UserClass>
    FDelegateHandle Subscribe_FloatParam(FName EventName, UserClass* Listener, void (UserClass::* Callback)(float))
    {
        if (!IsValid(Listener)) return FDelegateHandle();
        FGlobalEvent_FloatParam& Event = FloatParamEventMap.FindOrAdd(EventName);
        return Event.AddUObject(Listener, Callback);
    }
    void Publish_FloatParam(FName EventName, float Value);
    void Unsubscribe_FloatParam(FName EventName, FDelegateHandle Handle);

    // ====================== Actor参数事件 ======================
    template<typename UserClass>
    FDelegateHandle Subscribe_ActorParam(FName EventName, UserClass* Listener, void (UserClass::* Callback)(AActor*))
    {
        if (!IsValid(Listener)) return FDelegateHandle();
        FGlobalEvent_ActorParam& Event = ActorParamEventMap.FindOrAdd(EventName);
        return Event.AddUObject(Listener, Callback);
    }
    void Publish_ActorParam(FName EventName, AActor* Actor);
    void Unsubscribe_ActorParam(FName EventName, FDelegateHandle Handle);

    // ====================== 伤害双参数事件 ======================
    template<typename UserClass>
    FDelegateHandle Subscribe_DamageEvent(FName EventName, UserClass* Listener, void (UserClass::* Callback)(int32, AActor*))
    {
        if (!IsValid(Listener)) return FDelegateHandle();
        FGlobalEvent_Damage& Event = DamageEventMap.FindOrAdd(EventName);
        return Event.AddUObject(Listener, Callback);
    }
    void Publish_DamageEvent(FName EventName, int32 Damage, AActor* Instigator);
    void Unsubscribe_DamageEvent(FName EventName, FDelegateHandle Handle);

private:
    TMap<FName, FGlobalEvent_NoParam> NoParamEventMap;
    TMap<FName, FGlobalEvent_StringParam> StringParamEventMap;
    TMap<FName, FGlobalEvent_IntParam> IntParamEventMap;
    TMap<FName, FGlobalEvent_FloatParam> FloatParamEventMap;
    TMap<FName, FGlobalEvent_ActorParam> ActorParamEventMap;
    TMap<FName, FGlobalEvent_Damage> DamageEventMap;
};