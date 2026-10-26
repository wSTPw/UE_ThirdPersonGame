#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "CharacterActionTypes.h"
#include "CharacterActionComponent.generated.h"

class AMyPlayerCharacter;
class UWeaponData;
class UAnimMontage;
class UAnimSequenceBase;
class USkeletalMeshComponent;
class UCharacterActionExecution;
struct FAnimNotifyEventReference;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FCharacterActionChanged, FCharacterActionSnapshot, Snapshot);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FCharacterActionFinished, int64, RunId, ECharacterActionEndReason, Reason, ECharacterActionFailure, Failure);

UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class INTROCPP_API UCharacterActionComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UCharacterActionComponent();
    UFUNCTION(BlueprintCallable, Category="Actions") FCharacterActionRequestResult RequestAttack();
    UFUNCTION(BlueprintCallable, Category="Actions") FCharacterActionRequestResult RequestUseItem(bool bQuickSlot, int32 SlotIndex);
    UFUNCTION(BlueprintCallable, Category="Actions") void Interrupt(ECharacterActionEndReason Reason = ECharacterActionEndReason::Interrupted);
    // Voluntary cancellation requires the current run and an authored cancel window.
    UFUNCTION(BlueprintCallable, Category="Actions") bool TryCancelAction(int64 RunId);
    UFUNCTION(BlueprintPure, Category="Actions") FCharacterActionSnapshot GetSnapshot() const;
    UFUNCTION(BlueprintPure, Category="Actions") bool IsBusy() const;
    UFUNCTION(BlueprintPure, Category="Actions") bool CanChangeEquipment() const;
    UFUNCTION(BlueprintPure, Category="Actions") ECharacterActionFailure GetLastFailure() const { return LastFailure; }
    void SetUIBlocked(bool bBlocked);
    bool IsDispatching() const { return bDispatching; }
    bool AllowsInventoryMutation() const { return !IsBusy() && !bFinishing && !bDispatching && !bOwnerEnding; }
    bool HandleNotify(USkeletalMeshComponent* Mesh, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& Reference, ECharacterActionEvent Event);
    bool ApplyMelee(UCharacterActionExecution& Run);
    bool ApplyCast(UCharacterActionExecution& Run);
    bool ApplyItem(UCharacterActionExecution& Run);

    UPROPERTY(BlueprintAssignable, Category="Actions") FCharacterActionChanged OnActionChanged;
    UPROPERTY(BlueprintAssignable, Category="Actions") FCharacterActionFinished OnActionEnded;
    UPROPERTY(EditAnywhere, Category="Actions", meta=(ClampMin="0", ClampMax="0.5")) float InputBufferSeconds = 0.15f;
protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* TickFunction) override;
private:
#if WITH_DEV_AUTOMATION_TESTS
    friend struct FCharacterActionTestAccess;
#endif
    UPROPERTY(Transient) TObjectPtr<UCharacterActionExecution> Active;
    UPROPERTY(Transient) TObjectPtr<AMyPlayerCharacter> Character;
    TMap<FName, double> CooldownUntil;
    int64 NextRunId = 1;
    bool bUIBlocked = false;
    bool bFinishing = false;
    bool bDispatching = false;
    bool bOwnerEnding = false;
    bool bDeferredFinish = false;
    ECharacterActionEndReason DeferredReason = ECharacterActionEndReason::Interrupted;
    ECharacterActionFailure LastFailure = ECharacterActionFailure::None;
    ECharacterActionFailure CheckPermission() const;
    FCharacterActionRequestResult Reject(ECharacterActionFailure Failure);
    FCharacterActionRequestResult Start(UCharacterActionExecution* Run);
    bool PlaySegment();
    void Publish();
    void Finish(ECharacterActionEndReason Reason, ECharacterActionFailure Failure = ECharacterActionFailure::None);
    void OnMontageBlendOut(int64 RunId, int32 Generation, UAnimMontage* Montage, bool bInterrupted);
    void OnMontageEnded(int64 RunId, int32 Generation, UAnimMontage* Montage, bool bInterrupted);
    UFUNCTION() void OnOwnerDeath();
};
