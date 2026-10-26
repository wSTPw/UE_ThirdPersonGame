#include "MHWIUI/MHWIHUD.h"

#include "AttributeComponent.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "GameFramework/PlayerController.h"
#include "MHWI/MHWICharacter.h"

void AMHWIHUD::DrawHUD()
{
	Super::DrawHUD();
	if (!bShowHUD || !Canvas || !GEngine || !PlayerOwner || Canvas->ClipX < 320.0f || Canvas->ClipY < 180.0f)
	{
		return;
	}

	const AMHWICharacter* Character = Cast<AMHWICharacter>(PlayerOwner->GetPawn());
	if (!IsValid(Character))
	{
		return;
	}

	const UAttributeComponent* Attributes = Character->Attributes;
	const bool bAlive = !IsValid(Attributes) || Attributes->IsAlive();
	const float Scale = FMath::Min(Canvas->ClipX / 1280.0f, Canvas->ClipY / 720.0f);
	const float Width = Canvas->ClipX / Scale;
	const float Height = Canvas->ClipY / Scale;
	UFont* Font = GEngine->GetSmallFont();
	if (!Font)
	{
		return;
	}

	const FLinearColor Panel(0.018f, 0.026f, 0.030f, 0.86f);
	const FLinearColor Text(0.92f, 0.92f, 0.85f, 1.0f);
	const FLinearColor Muted(0.57f, 0.64f, 0.63f, 1.0f);
	const FLinearColor Accent(0.82f, 0.68f, 0.38f, 1.0f);
	const FLinearColor Empty(0.075f, 0.095f, 0.10f, 1.0f);
	const FLinearColor LevelColors[] = {
		FLinearColor(0.48f, 0.57f, 0.59f, 1.0f),
		FLinearColor(0.95f, 0.95f, 0.90f, 1.0f),
		FLinearColor(1.0f, 0.76f, 0.18f, 1.0f),
		FLinearColor(0.95f, 0.24f, 0.20f, 1.0f)
	};
	const TCHAR* LevelNames[] = { TEXT("NONE"), TEXT("WHITE"), TEXT("YELLOW"), TEXT("RED") };
	const int32 Level = FMath::Clamp(Character->GetSpiritLevel(), 0, 3);
	const FLinearColor SpiritColor = LevelColors[Level];

	auto Rect = [&](float X, float Y, float W, float H, const FLinearColor& Color)
	{
		DrawRect(Color, X * Scale, Y * Scale, W * Scale, H * Scale);
	};
	auto Label = [&](const FString& Value, float X, float Y, const FLinearColor& Color,
		float FontScale = 1.0f, float MaxWidth = 0.0f)
	{
		FString Display = Value;
		if (MaxWidth > 0.0f)
		{
			float TextWidth = 0.0f;
			float TextHeight = 0.0f;
			GetTextSize(Display, TextWidth, TextHeight, Font, FontScale);
			if (TextWidth > MaxWidth)
			{
				while (Display.Len() > 1)
				{
					Display.LeftChopInline(1);
					GetTextSize(Display + TEXT("..."), TextWidth, TextHeight, Font, FontScale);
					if (TextWidth <= MaxWidth)
					{
						break;
					}
				}
				Display += TEXT("...");
			}
		}
		DrawText(Display, Color, X * Scale, Y * Scale, Font, Scale * FontScale);
	};
	auto Bar = [&](float X, float Y, float W, float H, float Fraction, const FLinearColor& Color)
	{
		Rect(X, Y, W, H, Empty);
		Rect(X + 2.0f, Y + 2.0f, (W - 4.0f) * FMath::Clamp(Fraction, 0.0f, 1.0f), H - 4.0f, Color);
	};

	Rect(24.0f, 24.0f, 370.0f, 188.0f, Panel);
	Rect(24.0f, 24.0f, 3.0f, 188.0f, Accent);
	Label(TEXT("MHWI  /  LONG SWORD"), 40.0f, 34.0f, Accent, 1.15f);
	Label(TEXT("HP"), 40.0f, 65.0f, Muted);
	const float HealthFraction = IsValid(Attributes) ? Attributes->GetHealthPercent() : 0.0f;
	Bar(72.0f, 67.0f, 300.0f, 12.0f, HealthFraction, FLinearColor(0.35f, 0.74f, 0.44f, 1.0f));
	Label(TEXT("SPIRIT"), 40.0f, 91.0f, Muted);
	Label(FString::Printf(TEXT("%3.0f / 100"), Character->GetSpiritGauge()), 270.0f, 91.0f, Text);
	Bar(40.0f, 114.0f, 332.0f, 16.0f, Character->GetSpiritGauge() / 100.0f, SpiritColor);
	Label(FString::Printf(TEXT("%s  /  LEVEL %d"), LevelNames[Level], Level), 40.0f, 145.0f, SpiritColor);
	Label(FString::Printf(TEXT("SLINGER  %d"), FMath::Max(0, Character->SlingerAmmo)), 40.0f, 176.0f, Muted);
	if (Level > 0)
	{
		Label(FString::Printf(TEXT("%.1f s"), FMath::Max(0.0f, Character->GetSpiritTimeRemaining())),
			292.0f, 145.0f, SpiritColor);
	}

	const float StatusY = Height - 94.0f;
	const float StatusWidth = FMath::Min(560.0f, Width - 48.0f);
	Rect(24.0f, StatusY, StatusWidth, 70.0f, Panel);
	Rect(24.0f, StatusY, 3.0f, 70.0f, bAlive ? SpiritColor : LevelColors[3]);
	const FString MoveName = Character->GetMoveDisplayName().ToString();
	Label(bAlive ? (Character->IsSheathed() ? TEXT("SHEATHED") : TEXT("DRAWN")) : TEXT("FAINTED"),
		40.0f, StatusY + 10.0f, bAlive ? Accent : LevelColors[3]);
	Label(MoveName.IsEmpty() ? TEXT("Idle") : MoveName, 156.0f, StatusY + 10.0f, Text,
		1.0f, StatusWidth - 146.0f);
	Label(Character->GetMoveStatus(), 40.0f, StatusY + 38.0f, Muted, 0.9f, StatusWidth - 32.0f);

	if (bShowControls && bAlive)
	{
		const float ControlsX = Width - 346.0f;
		const float ControlsY = Height - 331.0f;
		Rect(ControlsX, ControlsY, 322.0f, 307.0f, Panel);
		Label(TEXT("TRAINING CONTROLS"), ControlsX + 14.0f, ControlsY + 10.0f, Accent);
		const TCHAR* Controls[] = {
			TEXT("WASD Move    Mouse Look"),
			TEXT("LMB Slash    RMB Thrust"),
			TEXT("W + LMB Advancing Slash"),
			TEXT("C Fade (camera-rel); A/D sides"),
			TEXT("R Spirit     F Foresight"),
			TEXT("V / D-pad Left Slinger Burst"),
			TEXT("G Hit Helm; Air LMB/RMB/R/G Slam"),
			TEXT("Q Special Sheathe"),
			TEXT("  > LMB Iai / R Iai Spirit"),
			TEXT("F counter hit > R Roundslash"),
			TEXT("E Draw / Sheathe"),
			TEXT("Space Evade  Shift Sprint")
		};
		for (int32 Index = 0; Index < UE_ARRAY_COUNT(Controls); ++Index)
		{
			Label(Controls[Index], ControlsX + 14.0f, ControlsY + 39.0f + Index * 21.0f, Text, 0.95f);
		}
	}
}
