#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "MHWIHUD.generated.h"

/** Lightweight training overlay for the isolated MHWI character and map. */
UCLASS()
class INTROCPP_API AMHWIHUD : public AHUD
{
	GENERATED_BODY()

public:
	virtual void DrawHUD() override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MHWI|HUD")
	bool bShowControls = true;
};
