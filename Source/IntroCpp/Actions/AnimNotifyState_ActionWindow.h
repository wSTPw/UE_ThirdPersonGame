#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimNotifies/AnimNotifyState.h"
#include "AnimNotifyState_ActionWindow.generated.h"

UENUM(BlueprintType)
enum class ECharacterActionWindow : uint8 { Chain, Cancel };

/** Authored montage time range. The action component samples its own playback
 * instance, so interruption never depends on a NotifyEnd callback being delivered. */
UCLASS(meta=(DisplayName="Character Action Window"))
class INTROCPP_API UAnimNotifyState_ActionWindow : public UAnimNotifyState
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Actions")
    ECharacterActionWindow Window = ECharacterActionWindow::Chain;
};
