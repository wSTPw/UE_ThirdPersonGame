#include "MHWICharacter.h"
#include "MHWIAnimInstance.h"
#include "AttributeComponent.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "EnhancedPlayerInput.h"
#include "Engine/LocalPlayer.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "InputCoreTypes.h"
#include "Misc/ScopeExit.h"
#include "UObject/ConstructorHelpers.h"
#include <initializer_list>

namespace MHWI
{
    static bool InHalfOpenWindow(float Position, float Start, float End)
    {
        return FMath::IsFinite(Position) && FMath::IsFinite(Start) && FMath::IsFinite(End)
            && End > Start && Position >= Start && Position < End;
    }
    static constexpr float SpiritMultipliers[] = {1.f, 1.05f, 1.1f, 1.2f};
    /** Reference gravity for HelmAirGravity (cm/s^2); the data value is project tuning. */
    static constexpr float ReferenceWorldGravity = 980.f;
    /** Extra time after a Roll ends in which its drawn Light recovery route stays valid. */
    static constexpr float RollRecoveryGraceSeconds = 0.15f;
    static const FName SpecialSheathe(TEXT("SpecialSheathe"));
    static const FName ForesightSlash(TEXT("ForesightSlash"));
    static const FName SpiritRoundslash(TEXT("SpiritRoundslash"));
    static const FName IaiSpiritSlash(TEXT("IaiSpiritSlash"));
    static const FName Roll(TEXT("Roll"));
    static bool IsRollMove(FName Move)
    { return Move == Roll || Move == FName(TEXT("RollLeft")) || Move == FName(TEXT("RollRight")) || Move == FName(TEXT("RollBack")); }
    static const FName FadeSlash(TEXT("FadeSlash"));
    static const FName FadeSlashLeft(TEXT("FadeSlashLeft"));
    static const FName FadeSlashRight(TEXT("FadeSlashRight"));
    static const FName SpiritThrust(TEXT("SpiritThrust"));
    static const FName HelmRise(TEXT("HelmRise"));
    static const FName HelmAir(TEXT("HelmAir"));
    static const FName HelmStrike(TEXT("SpiritHelmBreaker"));
    static const FName HelmLand(TEXT("HelmLand"));

    static bool IsFadeSlashMove(FName Move)
    {
        return Move == FadeSlash || Move == FadeSlashLeft || Move == FadeSlashRight;
    }

    static bool IsHelmStageMove(FName Move)
    {
        return Move == HelmRise || Move == HelmAir || Move == HelmStrike || Move == HelmLand;
    }

    /** Air and Strike are landing-driven; they must never advance from montage length alone. */
    static bool IsHelmAerialStageMove(FName Move)
    {
        return Move == HelmAir || Move == HelmStrike;
    }

    /** PC attack buttons/chords and gamepad equivalents normalize to one air slam. */
    static bool IsHelmSlamInput(EMHWIInput Input)
    {
        return Input == EMHWIInput::Light || Input == EMHWIInput::Thrust
            || Input == EMHWIInput::Spirit || Input == EMHWIInput::HelmBreaker;
    }

    static bool IsHelmContinuation(FName From, FName To)
    {
        return (From == SpiritThrust && To == HelmRise)
            || (From == HelmRise && To == HelmAir)
            || (From == HelmAir && To == HelmStrike)
            || (From == HelmAir && To == HelmLand)
            || (From == HelmStrike && To == HelmLand);
    }
}

AMHWICharacter::AMHWICharacter()
{
    PrimaryActorTick.bCanEverTick = true;
    // Read montage position after mesh animation has advanced this frame.
    PrimaryActorTick.TickGroup = TG_PostUpdateWork;
    GetCapsuleComponent()->InitCapsuleSize(38.f, 92.f);
    bUseControllerRotationYaw = false;
    GetCharacterMovement()->bOrientRotationToMovement = true;
    GetCharacterMovement()->RotationRate = FRotator(0.f, 540.f, 0.f);
    GetCharacterMovement()->MaxWalkSpeed = 180.f;
    GetCharacterMovement()->BrakingDecelerationWalking = 1200.f;
    GetMesh()->SetRelativeLocation(FVector(0.f, 0.f, -92.f));
    GetMesh()->SetRelativeRotation(FRotator(0.f, -90.f, 0.f));
    GetMesh()->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    Attributes = CreateDefaultSubobject<UAttributeComponent>(TEXT("Attributes"));
    SpringArm = CreateDefaultSubobject<USpringArmComponent>(TEXT("SpringArm"));
    SpringArm->SetupAttachment(RootComponent);
    SpringArm->TargetArmLength = 420.f;
    SpringArm->SocketOffset = FVector(0.f, 35.f, 70.f);
    SpringArm->bUsePawnControlRotation = true;
    Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
    Camera->SetupAttachment(SpringArm);
    WeaponMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("WeaponMesh"));
    WeaponMesh->SetupAttachment(GetMesh());
    WeaponMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    WeaponMesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
    ScabbardMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("ScabbardMesh"));
    ScabbardMesh->SetupAttachment(GetMesh());
    ScabbardMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    for (int32 Motion : MHWI::Native::GetConnectorMotions())
    {
        const FString Path = FString::Printf(TEXT("/Game/MHWI/Animations/R06Staging/A_w03_00_%03d"), Motion);
        ConstructorHelpers::FObjectFinder<UAnimSequence> Sequence(*Path);
        if (Sequence.Succeeded()) NativeConnectorSequences.Add(Motion, Sequence.Object);
    }
    const int32 Additional[] = {10,11,12,13,61,62,63,113,115,116,126,130,151,221,
        332,333,334,338,339,340,341,342,343,344,345,346,347,348,349};
    for (int32 Motion : Additional)
    {
        const FString Name = FString::Printf(TEXT("w03_00_%03d"), Motion);
        ConstructorHelpers::FObjectFinder<UAnimSequence> Sequence(*FString::Printf(
            TEXT("/Game/MHWI/Animations/R06Remaining/A_%s"), *Name));
        if (Sequence.Succeeded())
        {
            NativeSourceSequences.Add(FName(*Name), Sequence.Object);
            NativeConnectorSequences.Add(Motion, Sequence.Object);
        }
    }
    for (int32 Motion : {70, 71, 72})
    {
        const FString Name = FString::Printf(TEXT("co00_00_%03d"), Motion);
        ConstructorHelpers::FObjectFinder<UAnimSequence> Sequence(*FString::Printf(
            TEXT("/Game/MHWI/Animations/R06Remaining/A_%s"), *Name));
        if (Sequence.Succeeded()) NativeSourceSequences.Add(FName(*Name), Sequence.Object);
    }
}

void AMHWICharacter::BeginPlay()
{
    Super::BeginPlay();
    AddTickPrerequisiteComponent(GetMesh());
    AddTickPrerequisiteComponent(WeaponMesh);
    InitializeNativeRuntimeMoves();
    ResetSpiritGaugeDecayClock();
    Attributes->OnCharacterDeath.AddDynamic(this, &AMHWICharacter::HandleDeath);
    Attributes->OnDamaged.AddDynamic(this, &AMHWICharacter::HandleDamaged);
    if (GetMesh()->GetAnimInstance())
        GetMesh()->GetAnimInstance()->SetRootMotionMode(ERootMotionMode::RootMotionFromMontagesOnly);
    // Weapons have independent, remapped source rigs; do not use leader pose.
    SetSourceWeaponMotion(bSheathed ? 0 : 1);
    RefreshWeaponAttachment();
    PreviousActorLocation = GetActorLocation();
    BuildInputMapping();
    InstallInputMapping();
    RefreshMovement();
}

void AMHWICharacter::BuildInputMapping()
{
    if (RuntimeMapping) return;
    RuntimeMapping = NewObject<UInputMappingContext>(this, TEXT("MHWI_RuntimeMapping"));
    MoveAction = NewObject<UInputAction>(this, TEXT("MHWI_Move"));
    MoveAction->ValueType = EInputActionValueType::Axis2D;
    MoveAction->AccumulationBehavior = EInputActionAccumulationBehavior::Cumulative;
    LookAction = NewObject<UInputAction>(this, TEXT("MHWI_Look"));
    LookAction->ValueType = EInputActionValueType::Axis2D;
    LookAction->AccumulationBehavior = EInputActionAccumulationBehavior::Cumulative;
    SprintAction = NewObject<UInputAction>(this, TEXT("MHWI_Sprint"));
    KeyboardSprintAction = NewObject<UInputAction>(this, TEXT("MHWI_KeyboardSprint"));
    auto MapDirection = [this](FKey Key, bool bY, bool bNegative)
    {
        FEnhancedActionKeyMapping& Mapping = RuntimeMapping->MapKey(MoveAction, Key);
        if (bNegative) Mapping.Modifiers.Add(NewObject<UInputModifierNegate>(RuntimeMapping));
        if (bY)
        {
            UInputModifierSwizzleAxis* Swizzle = NewObject<UInputModifierSwizzleAxis>(RuntimeMapping);
            Swizzle->Order = EInputAxisSwizzle::YXZ;
            Mapping.Modifiers.Add(Swizzle);
        }
    };
    MapDirection(EKeys::W, true, false);
    MapDirection(EKeys::S, true, true);
    MapDirection(EKeys::D, false, false);
    MapDirection(EKeys::A, false, true);
    RuntimeMapping->MapKey(MoveAction, EKeys::Gamepad_Left2D);
    RuntimeMapping->MapKey(LookAction, EKeys::Mouse2D);
    FEnhancedActionKeyMapping& PadLook = RuntimeMapping->MapKey(LookAction, EKeys::Gamepad_Right2D);
    UInputModifierScalar* PadScale = NewObject<UInputModifierScalar>(RuntimeMapping);
    PadScale->Scalar = FVector(2.2f, 1.8f, 1.f);
    PadLook.Modifiers.Add(PadScale);
    RuntimeMapping->MapKey(KeyboardSprintAction, EKeys::LeftShift);
    RuntimeMapping->MapKey(SprintAction, EKeys::Gamepad_LeftThumbstick);
    // MHWI PC: Ctrl is the Spirit modifier. Direct Foresight/Helm/Fade/Special
    // Sheathe shortcuts are intentionally absent; their official chords are
    // resolved from device-specific keyboard edges below.
    const FKey Keyboard[] = { EKeys::LeftMouseButton, EKeys::RightMouseButton, EKeys::LeftControl,
        EKeys::Invalid, EKeys::Invalid, EKeys::Invalid, EKeys::SpaceBar, EKeys::E, EKeys::Invalid, EKeys::V };
    FKey Gamepad[] = { EKeys::Gamepad_FaceButton_Top, EKeys::Gamepad_FaceButton_Right,
        EKeys::Gamepad_RightShoulder, EKeys::Gamepad_LeftShoulder, EKeys::Gamepad_RightTrigger,
        EKeys::Gamepad_LeftTrigger, EKeys::Gamepad_FaceButton_Bottom, EKeys::Gamepad_FaceButton_Left, EKeys::Gamepad_DPad_Up, EKeys::Gamepad_DPad_Left };
    if (bOriginalInputPreset)
    {
        // Original device semantics: RT is the Spirit modifier. Foresight,
        // HelmBreaker and FadeSlash are derived from RT+Y / RT+B / Y+B by the
        // gesture resolver, so their direct gamepad keys are intentionally absent.
        Gamepad[2] = EKeys::Gamepad_RightTrigger;
        Gamepad[3] = EKeys::Invalid;
        Gamepad[4] = EKeys::Invalid;
        Gamepad[8] = EKeys::Invalid;
    }
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(Keyboard); ++Index)
    {
        // Keep the legacy action names on the gamepad path: existing PIE and
        // debugging tools inject them directly and must not silently become PC input.
        UInputAction* Action = NewObject<UInputAction>(this, FName(*FString::Printf(TEXT("MHWI_Command_%d"), Index)));
        CommandActions.Add(Action);
        if (Gamepad[Index].IsValid()) RuntimeMapping->MapKey(Action, Gamepad[Index]);

        UInputAction* KeyboardAction = NewObject<UInputAction>(this,
            FName(*FString::Printf(TEXT("MHWI_KeyboardCommand_%d"), Index)));
        KeyboardCommandActions.Add(KeyboardAction);
        if (Keyboard[Index].IsValid()) RuntimeMapping->MapKey(KeyboardAction, Keyboard[Index]);
    }
}

void AMHWICharacter::InstallInputMapping()
{
    BuildInputMapping();
    if (InstalledInputSubsystem.IsValid()) InstalledInputSubsystem->RemoveMappingContext(RuntimeMapping);
    InstalledInputSubsystem.Reset();
    if (const APlayerController* PC = Cast<APlayerController>(Controller))
        if (ULocalPlayer* Player = PC->GetLocalPlayer())
            if (UEnhancedInputLocalPlayerSubsystem* Subsystem = Player->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
            {
                Subsystem->RemoveMappingContext(RuntimeMapping);
                Subsystem->AddMappingContext(RuntimeMapping, 50);
                InstalledInputSubsystem = Subsystem;
            }
}

void AMHWICharacter::PawnClientRestart()
{
    Super::PawnClientRestart();
    InstallInputMapping();
}

void AMHWICharacter::UnPossessed()
{
    if (InstalledInputSubsystem.IsValid() && RuntimeMapping) InstalledInputSubsystem->RemoveMappingContext(RuntimeMapping);
    InstalledInputSubsystem.Reset();
    bSprintHeld = false;
    bKeyboardSpiritHeld = bKeyboardLightHeld = bKeyboardThrustHeld = bKeyboardEvadeHeld = false;
    KeyboardFrameInputEdges.Reset();
    MoveInput = FVector2D::ZeroVector;
    InterruptMove();
    Super::UnPossessed();
}

void AMHWICharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);
    BuildInputMapping();
    if (UEnhancedInputComponent* Input = Cast<UEnhancedInputComponent>(PlayerInputComponent))
    {
        Input->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AMHWICharacter::Move);
        Input->BindAction(MoveAction, ETriggerEvent::Completed, this, &AMHWICharacter::Move);
        Input->BindAction(LookAction, ETriggerEvent::Triggered, this, &AMHWICharacter::Look);
        Input->BindAction(SprintAction, ETriggerEvent::Started, this, &AMHWICharacter::SprintStarted);
        Input->BindAction(SprintAction, ETriggerEvent::Completed, this, &AMHWICharacter::SprintStopped);
        Input->BindAction(SprintAction, ETriggerEvent::Canceled, this, &AMHWICharacter::SprintStopped);
        Input->BindAction(KeyboardSprintAction, ETriggerEvent::Started, this, &AMHWICharacter::KeyboardSprintStarted);
        Input->BindAction(KeyboardSprintAction, ETriggerEvent::Completed, this, &AMHWICharacter::SprintStopped);
        Input->BindAction(KeyboardSprintAction, ETriggerEvent::Canceled, this, &AMHWICharacter::SprintStopped);
        for (int32 Index = 0; Index < CommandActions.Num(); ++Index)
        {
            Input->BindAction(CommandActions[Index], ETriggerEvent::Started, this, &AMHWICharacter::CommandStarted, static_cast<EMHWIInput>(Index));
            Input->BindAction(CommandActions[Index], ETriggerEvent::Completed, this, &AMHWICharacter::CommandReleased, static_cast<EMHWIInput>(Index));
            Input->BindAction(CommandActions[Index], ETriggerEvent::Canceled, this, &AMHWICharacter::CommandReleased, static_cast<EMHWIInput>(Index));
        }
        for (int32 Index = 0; Index < KeyboardCommandActions.Num(); ++Index)
        {
            Input->BindAction(KeyboardCommandActions[Index], ETriggerEvent::Started, this, &AMHWICharacter::KeyboardCommandStarted, static_cast<EMHWIInput>(Index));
            Input->BindAction(KeyboardCommandActions[Index], ETriggerEvent::Completed, this, &AMHWICharacter::KeyboardCommandReleased, static_cast<EMHWIInput>(Index));
            Input->BindAction(KeyboardCommandActions[Index], ETriggerEvent::Canceled, this, &AMHWICharacter::KeyboardCommandReleased, static_cast<EMHWIInput>(Index));
        }
    }
    else
        UE_LOG(LogTemp, Error, TEXT("MHWICharacter requires EnhancedInputComponent; configure the training GameMode's PlayerController."));
}

void AMHWICharacter::Move(const FInputActionValue& Value)
{
    MoveInput = Value.Get<FVector2D>().GetClampedToMaxSize(1.f);
    if (bEnding || !Attributes->IsAlive() || !CurrentMove.IsNone() || NativeSourceMontage || !Controller) return;
    const FVector WorldIntent = GetMoveIntentWorldDirection();
    if (!WorldIntent.IsNearlyZero())
        AddMovementInput(WorldIntent, static_cast<float>(MoveInput.Size()));
}

FVector AMHWICharacter::GetMoveIntentWorldDirection() const
{
    if (!Controller || MoveInput.IsNearlyZero()) return FVector::ZeroVector;
    // UE world axes: X is forward, Y is right. MoveInput is (X = right, Y = forward),
    // so (MoveInput.Y, MoveInput.X, 0) projected through camera yaw is the shared intent.
    const FRotator CameraYaw(0.f, Controller->GetControlRotation().Yaw, 0.f);
    return CameraYaw.RotateVector(FVector(MoveInput.Y, MoveInput.X, 0.f)).GetSafeNormal();
}

FName AMHWICharacter::SelectFadeSlashMove() const
{
    const FVector WorldIntent = GetMoveIntentWorldDirection();
    if (WorldIntent.IsNearlyZero()) return MHWI::FadeSlash;
    // Sample against the right axis before any fragment selection so the chosen
    // sideways clip is not rotated a second time. 0.2 dead zone is project tuning.
    const float Side = FVector::DotProduct(WorldIntent, GetActorRightVector());
    if (Side < -0.2f) return MHWI::FadeSlashLeft;
    if (Side > 0.2f) return MHWI::FadeSlashRight;
    return MHWI::FadeSlash;
}

void AMHWICharacter::TurnTowardYaw(float DesiredYaw, float MaxAngle, float DurationSeconds, float& AccumulatedDegrees)
{
    if (MaxAngle <= 0.f || ActiveDefinition.TurnSpeed <= 0.f || DurationSeconds <= 0.f) return;
    const float Remaining = MaxAngle - AccumulatedDegrees;
    if (Remaining <= KINDA_SMALL_NUMBER) return;
    const float CurrentYaw = GetActorRotation().Yaw;
    const float DeltaYaw = FMath::FindDeltaAngleDegrees(CurrentYaw, DesiredYaw);
    if (FMath::IsNearlyZero(DeltaYaw, 0.01f)) return;
    // Shortest arc, capped by both the angular speed and the window's total budget.
    const float Step = FMath::Min3(FMath::Abs(DeltaYaw), ActiveDefinition.TurnSpeed * DurationSeconds, Remaining);
    if (Step <= 0.f) return;
    FRotator NewRotation = GetActorRotation();
    NewRotation.Yaw = FRotator::NormalizeAxis(CurrentYaw + FMath::Sign(DeltaYaw) * Step);
    SetActorRotation(NewRotation);
    AccumulatedDegrees += Step;
}

void AMHWICharacter::ApplyTurnWindows(float FromPosition, float ToPosition)
{
    if (CurrentMove.IsNone() || !Moveset || ToPosition <= FromPosition) return;
    // Roll has its own free-form start direction. The three Fade Slash clips carry
    // authored lateral displacement and must not be rotated after selection.
    if (MHWI::IsRollMove(CurrentMove) || MHWI::IsFadeSlashMove(CurrentMove)) return;
    // Small analog drift counts as no directional intent for turning.
    if (MoveInput.SizeSquared() < 0.01f) return;
    const FVector WorldIntent = GetMoveIntentWorldDirection();
    if (WorldIntent.IsNearlyZero()) return; // Looking around alone never turns an attack.
    const float DesiredYaw = WorldIntent.Rotation().Yaw;

    // Like the cancel window, use the montage interval [FromPosition, ToPosition]
    // intersected with the authored window. A low frame that jumps across the whole
    // early window still consumes the real overlap instead of skipping it.
    auto ApplyWindow = [&](float Start, float End, float MaxAngle, float& Accumulated)
    {
        if (MaxAngle <= 0.f || End < Start) return;
        const float OverlapStart = FMath::Max(Start, FromPosition);
        const float OverlapEnd = FMath::Min(End, ToPosition);
        if (OverlapEnd <= OverlapStart) return;
        // Montage seconds -> real seconds at the effective play rate sampled in the
        // overlap, so TurnSpeed is never applied for a whole render frame.
        const float SamplePosition = 0.5f * (OverlapStart + OverlapEnd);
        const float EffectiveRate = FMath::Max(0.01f,
            ActiveDefinition.PlayRate * EvaluateSourcePlayRate(SamplePosition));
        const float OverlapSeconds = (OverlapEnd - OverlapStart) / EffectiveRate;
        TurnTowardYaw(DesiredYaw, MaxAngle, OverlapSeconds, Accumulated);
    };

    ApplyWindow(ActiveDefinition.TurnStartTime, ActiveDefinition.TurnEndTime,
        ActiveDefinition.TurnMaxAngle, MainTurnAccumulated);
    if (ActiveDefinition.ReturnTurnStartTime >= 0.f
        && ActiveDefinition.ReturnTurnEndTime >= ActiveDefinition.ReturnTurnStartTime)
    {
        ApplyWindow(ActiveDefinition.ReturnTurnStartTime, ActiveDefinition.ReturnTurnEndTime,
            ActiveDefinition.ReturnTurnMaxAngle, ReturnTurnAccumulated);
    }
}

void AMHWICharacter::Look(const FInputActionValue& Value)
{
    const FVector2D LookInput = Value.Get<FVector2D>();
    AddControllerYawInput(LookInput.X);
    AddControllerPitchInput(-LookInput.Y);
}

void AMHWICharacter::SprintStarted() { bSprintHeld = true; RefreshMovement(); }
void AMHWICharacter::SprintStopped() { bSprintHeld = false; RefreshMovement(); }
void AMHWICharacter::KeyboardSprintStarted()
{
    SprintStarted();
    // PC Shift is Sprint while sheathed and Sheathe while drawn. The ordinary
    // input route still decides whether the current action may sheath.
    if (!bSheathed) RequestInput(EMHWIInput::ToggleSheathe);
}

void AMHWICharacter::SampleMoveInputForCommand()
{
    // Enhanced Input fires Started delegates before Triggered/Completed. A
    // simultaneous move + command must use this frame's evaluated action value,
    // even when Move() has not received its callback yet (or is about to release).
    if (const APlayerController* PC = Cast<APlayerController>(Controller))
        if (const UEnhancedPlayerInput* PlayerInput = Cast<UEnhancedPlayerInput>(PC->PlayerInput))
            if (MoveAction)
                MoveInput = PlayerInput->GetActionValue(MoveAction).Get<FVector2D>().GetClampedToMaxSize(1.f);
}

void AMHWICharacter::CommandStarted(EMHWIInput Input)
{
    SampleMoveInputForCommand();
    if (Input == EMHWIInput::Light) bLightHeld = true;
    else if (Input == EMHWIInput::Thrust) bThrustHeld = true;
    else if (Input == EMHWIInput::Spirit) bSpiritHeld = true;
    if (bOriginalInputPreset)
    {
        // Resolve after every Started callback for this frame; this is what makes
        // RT+Y / RT+B / Y+B atomic instead of two independent requests.
        FrameInputEdges.Add(Input);
        return;
    }
    RequestInput(Input);
}

void AMHWICharacter::CommandReleased(EMHWIInput Input)
{
    if (Input == EMHWIInput::Light) bLightHeld = false;
    else if (Input == EMHWIInput::Thrust) bThrustHeld = false;
    else if (Input == EMHWIInput::Spirit) bSpiritHeld = false;
}

void AMHWICharacter::KeyboardCommandStarted(EMHWIInput Input)
{
    // PC RMB is a drawn-only thrust. E is Sheathe/Use Item in the original;
    // this training sandbox has no item action, so sheathed E must not draw.
    // These device-local filters leave gamepad and direct RequestInput unchanged.
    if (bSheathed && (Input == EMHWIInput::Thrust || Input == EMHWIInput::ToggleSheathe)) return;
    SampleMoveInputForCommand();
    if (Input == EMHWIInput::Light) bKeyboardLightHeld = true;
    else if (Input == EMHWIInput::Thrust) bKeyboardThrustHeld = true;
    else if (Input == EMHWIInput::Spirit) bKeyboardSpiritHeld = true;
    else if (Input == EMHWIInput::Evade) bKeyboardEvadeHeld = true;
    KeyboardFrameInputEdges.AddUnique(Input);
}

void AMHWICharacter::KeyboardCommandReleased(EMHWIInput Input)
{
    if (Input == EMHWIInput::Light) bKeyboardLightHeld = false;
    else if (Input == EMHWIInput::Thrust) bKeyboardThrustHeld = false;
    else if (Input == EMHWIInput::Spirit) bKeyboardSpiritHeld = false;
    else if (Input == EMHWIInput::Evade) bKeyboardEvadeHeld = false;
}

void AMHWICharacter::ResolveFrameInputEdges()
{
    if (FrameInputEdges.IsEmpty()) return;
    TArray<EMHWIInput> Edges = MoveTemp(FrameInputEdges);
    FrameInputEdges.Reset();
    const bool bSpirit = bSpiritHeld || Edges.Contains(EMHWIInput::Spirit);
    const bool bLight = bLightHeld || Edges.Contains(EMHWIInput::Light);
    const bool bThrust = bThrustHeld || Edges.Contains(EMHWIInput::Thrust);
    // Chord priority is a project adapter: the pinned FSM stores composed input
    // states but does not expose a global arbitration order. One chord consumes
    // all of its member edges so a single press never starts two actions.
    if (bSpirit && bLight)
    {
        Edges.RemoveAll([](EMHWIInput Edge) {
            return Edge == EMHWIInput::Spirit || Edge == EMHWIInput::Light || Edge == EMHWIInput::Thrust; });
        RequestInput(EMHWIInput::HelmBreaker);
    }
    else if (bSpirit && bThrust)
    {
        Edges.RemoveAll([](EMHWIInput Edge) {
            return Edge == EMHWIInput::Spirit || Edge == EMHWIInput::Thrust || Edge == EMHWIInput::Light; });
        RequestInput(EMHWIInput::Foresight);
    }
    else if (bLight && bThrust)
    {
        Edges.RemoveAll([](EMHWIInput Edge) {
            return Edge == EMHWIInput::Light || Edge == EMHWIInput::Thrust; });
        RequestInput(EMHWIInput::FadeSlash);
    }
    for (const EMHWIInput Edge : Edges) RequestInput(Edge);
}

void AMHWICharacter::ResolveKeyboardFrameInputEdges()
{
    if (KeyboardFrameInputEdges.IsEmpty()) return;
    TArray<EMHWIInput> Edges = MoveTemp(KeyboardFrameInputEdges);
    KeyboardFrameInputEdges.Reset();
    // Include a key pressed and released inside one frame, without allowing an
    // unrelated edge to retrigger an older held chord (the keyboard A02 guard).
    const bool bSpirit = bKeyboardSpiritHeld || Edges.Contains(EMHWIInput::Spirit);
    const bool bLight = bKeyboardLightHeld || Edges.Contains(EMHWIInput::Light);
    const bool bThrust = bKeyboardThrustHeld || Edges.Contains(EMHWIInput::Thrust);
    const bool bEvade = bKeyboardEvadeHeld || Edges.Contains(EMHWIInput::Evade);
    auto HasNewMember = [&Edges](std::initializer_list<EMHWIInput> Members)
    {
        for (const EMHWIInput Member : Members)
            if (Edges.Contains(Member)) return true;
        return false;
    };
    auto ConsumeAttackEdges = [&Edges](bool bIncludeEvade)
    {
        Edges.Remove(EMHWIInput::Spirit);
        Edges.Remove(EMHWIInput::Light);
        Edges.Remove(EMHWIInput::Thrust);
        if (bIncludeEvade) Edges.Remove(EMHWIInput::Evade);
    };

    // One keyboard attack gesture per frame. The priority for three or more
    // simultaneous attack keys is a project adapter, not claimed native order.
    if (bSpirit && bEvade && HasNewMember({EMHWIInput::Spirit, EMHWIInput::Evade}))
    {
        ConsumeAttackEdges(true);
        RequestInput(EMHWIInput::SpecialSheathe);
    }
    else if (bSpirit && bLight && HasNewMember({EMHWIInput::Spirit, EMHWIInput::Light}))
    {
        ConsumeAttackEdges(false);
        RequestInput(EMHWIInput::HelmBreaker);
    }
    else if (bSpirit && bThrust && HasNewMember({EMHWIInput::Spirit, EMHWIInput::Thrust}))
    {
        ConsumeAttackEdges(false);
        RequestInput(EMHWIInput::Foresight);
    }
    else if (bLight && bThrust && HasNewMember({EMHWIInput::Light, EMHWIInput::Thrust}))
    {
        ConsumeAttackEdges(false);
        RequestInput(EMHWIInput::FadeSlash);
    }
    for (const EMHWIInput Edge : Edges) RequestInput(Edge);
}

void AMHWICharacter::SetInputBlocked(bool bBlocked)
{
    bInputBlocked = bBlocked;
    if (!bBlocked) return;
    PendingInput.Reset();
    bBufferedInsideWindow = false;
    bHelmSlamRequested = false;
    FrameInputEdges.Reset();
    KeyboardFrameInputEdges.Reset();
}

void AMHWICharacter::RefreshMovement()
{
    GetCharacterMovement()->MaxWalkSpeed = Moveset ? (IsSprinting() ? Moveset->RunSpeed : Moveset->WalkSpeed) : 180.f;
    GetCharacterMovement()->bOrientRotationToMovement = CurrentMove.IsNone() && !NativeSourceMontage;
}

void AMHWICharacter::RefreshWeaponAttachment(float DeltaSeconds)
{
    FMHWIWeaponAttachmentSettings Settings;
    Settings.WeaponBone = WeaponBone;
    Settings.ScabbardBone = ScabbardBone;
    Settings.SheathedWeaponBone = SheathedWeaponBone;
    Settings.SpecialScabbardBone = SpecialScabbardBone;
    Settings.WeaponRelativeTransform = WeaponRelativeTransform;
    Settings.ScabbardRelativeTransform = ScabbardRelativeTransform;
    Settings.SheathedWeaponRelativeTransform = SheathedWeaponRelativeTransform;
    Settings.SpecialScabbardRelativeTransform = SpecialScabbardRelativeTransform;
    Settings.SpecialWeaponRelativeTransform = SpecialWeaponRelativeTransform;
    FMHWIWeaponAttachmentContext Context;
    Context.CurrentMove = bNativeConnector ? NAME_None : CurrentMove;
    Context.MontagePosition = CurrentPosition;
    Context.bSheathed = bSheathed;
    Context.bSpecialSheathHeld = bSpecialSheathHeld;
    Context.bMoveStartedSheathed = bMoveStartedSheathed;
    Context.bUnsheathAtStart = ActiveDefinition.bUnsheathAtStart;
    if (ActiveDefinition.bSheathAtEnd && CurrentMove == MHWI::SpiritRoundslash)
    {
        // An explicit internal sheathed state anchors PROJECT equipment fitting.
        // It is not decoded as a native whole-equipment socket command.
        for (const FMHWIWeaponMotionEvent& Event : ActiveDefinition.WeaponMotionEvents)
            if (Event.MotionNo == 0 && FMath::IsFinite(Event.Time) && Event.Time > 0.f)
            {
                Context.ReturnToSheathTime = Event.Time;
                break;
            }
    }
    Context.ExecutionSerial = ExecutionSerial;
    WeaponAttachmentRuntime.Update(GetMesh(), WeaponMesh, ScabbardMesh, Settings, Context, DeltaSeconds);
}

void AMHWICharacter::SetSourceWeaponMotion(int32 MotionNo, float Position)
{
    if (MotionNo < 0 || !Moveset || !WeaponMesh) return;
    const TObjectPtr<UAnimSequence>* Entry = Moveset->WeaponMotions.Find(MotionNo);
    UAnimSequence* Sequence = Entry ? Entry->Get() : nullptr;
    // Optional for old DataAssets. Never assign a hunter pose to the independent rig.
    if (!Sequence || !WeaponMesh->GetSkeletalMeshAsset()
        || Sequence->GetSkeleton() != WeaponMesh->GetSkeletalMeshAsset()->GetSkeleton()) return;
    WeaponMesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);
    WeaponMesh->SetAnimation(Sequence);
    if (UAnimSingleNodeInstance* SingleNode = WeaponMesh->GetSingleNodeInstance())
        SingleNode->SetPlaying(false); // The character owns the pose clock, including seeks.
    WeaponMotionNo = MotionNo;
    WeaponMotionPosition = FMath::Clamp(Position, 0.f, Sequence->GetPlayLength());
    UpdateSourceWeaponPose(0.f);
}

void AMHWICharacter::UpdateSourceWeaponPose(float DeltaSeconds)
{
    if (WeaponMotionNo < 0 || !WeaponMesh || !Moveset) return;
    const TObjectPtr<UAnimSequence>* Entry = Moveset->WeaponMotions.Find(WeaponMotionNo);
    UAnimSequence* Sequence = Entry ? Entry->Get() : nullptr;
    UAnimSingleNodeInstance* Instance = WeaponMesh->GetSingleNodeInstance();
    if (!Sequence || !Instance || Instance->GetCurrentAsset() != Sequence) return;
    WeaponMotionPosition = FMath::Clamp(WeaponMotionPosition + FMath::Max(0.f, DeltaSeconds),
        0.f, Sequence->GetPlayLength());
    Instance->SetPosition(WeaponMotionPosition, false);
    // The character ticks after the hunter mesh. Refresh the dependent weapon now
    // rather than presenting the preceding frame after a source event or seek.
    WeaponMesh->TickAnimation(0.f, false);
    WeaponMesh->RefreshBoneTransforms();
}

void AMHWICharacter::AdvanceSourceWeaponEvents(float FromPosition, float NewPosition)
{
    // Keep weapon playback in real actor seconds even when the hunter montage
    // runs faster. Source coordinates identify events; they are not elapsed time.
    const float FrameDelta = GetWorld() ? GetWorld()->GetDeltaSeconds() * CustomTimeDilation : 0.f;
    const float SourceDelta = NewPosition - FromPosition;
    float EventLimit = NewPosition;
    if (ActiveDefinition.bHoldsSpecialSheath && ActiveMontage)
        EventLimit = FMath::Min(EventLimit, ActiveDefinition.SpecialSheathHoldTime >= 0.f
            ? ActiveDefinition.SpecialSheathHoldTime : ActiveMontage->GetPlayLength() - 0.05f);
    while (ActiveDefinition.WeaponMotionEvents.IsValidIndex(NextWeaponMotionEvent))
    {
        const FMHWIWeaponMotionEvent Event = ActiveDefinition.WeaponMotionEvents[NextWeaponMotionEvent];
        if (!FMath::IsFinite(Event.Time) || Event.Time < 0.f)
        {
            ++NextWeaponMotionEvent;
            continue;
        }
        if (Event.Time > EventLimit + KINDA_SMALL_NUMBER) break;
        ++NextWeaponMotionEvent;
        // Catch up an event crossed in a long frame; -1 means keep the last motion.
        const float CatchUp = SourceDelta > SMALL_NUMBER ? FrameDelta
            * FMath::Clamp((NewPosition - Event.Time) / SourceDelta, 0.f, 1.f) : 0.f;
        if (Event.MotionNo >= 0) SetSourceWeaponMotion(Event.MotionNo, CatchUp);
    }
}

float AMHWICharacter::EvaluateSourcePlayRate(float Position) const
{
    const TMap<float, float>& Keys = CapturedSpiritLevel > 0 && !ActiveDefinition.EmpoweredSourcePlayRates.IsEmpty()
        ? ActiveDefinition.EmpoweredSourcePlayRates : ActiveDefinition.SourcePlayRates;
    float LowerTime = -FLT_MAX, UpperTime = FLT_MAX, LowerRate = 1.f, UpperRate = 1.f;
    for (const TPair<float, float>& Key : Keys)
    {
        if (!FMath::IsFinite(Key.Key) || !FMath::IsFinite(Key.Value) || Key.Value <= 0.f) continue;
        if (Key.Key <= Position && Key.Key > LowerTime) { LowerTime = Key.Key; LowerRate = Key.Value; }
        if (Key.Key > Position && Key.Key < UpperTime) { UpperTime = Key.Key; UpperRate = Key.Value; }
    }
    if (LowerTime == -FLT_MAX) return UpperTime == FLT_MAX ? 1.f : UpperRate;
    if (UpperTime == FLT_MAX) return LowerRate;
    return FMath::Lerp(LowerRate, UpperRate, FMath::Clamp((Position - LowerTime) / (UpperTime - LowerTime), 0.f, 1.f));
}

bool AMHWICharacter::ResolveInput(EMHWIInput Input, FName& OutMove, float* OutCancelStart, float* OutCancelEnd) const
{
    if (!Moveset) return false;
    if (OutCancelStart) *OutCancelStart = ActiveDefinition.CancelStart;
    if (OutCancelEnd) *OutCancelEnd = ActiveDefinition.CancelEnd;
    if (!CurrentMove.IsNone())
    {
        if (Input == EMHWIInput::SlingerBurst)
        {
            if (bSheathed || bNativeConnector || SlingerAmmo <= 0) return false;
            const FVector Intent = GetMoveIntentWorldDirection();
            const float Side = FVector::DotProduct(Intent, GetActorRightVector());
            const int32 Direction = Side < -0.2f ? 1 : (Side > 0.2f ? 2 : 0);
            OutMove = MHWI::Native::GetSlingerMove(MHWI::Native::GetSlingerAction(NativeActionNode, Direction));
            return !OutMove.IsNone();
        }
        // A Roll decides its drawn state at its start so a sheathed dodge never
        // consumes the drawn-only recovery route even if the clip unsheathes.
        const bool bDrawnForRoute = MHWI::IsRollMove(CurrentMove) ? bRollStartedDrawn : !bSheathed;
        bool bHasExplicitInput = false;
        for (const FMHWIRoute& Route : ActiveDefinition.Routes)
        {
            if (Route.Input != Input) continue;
            bHasExplicitInput = true;
            // R05: routes with no source FSM edge stay available as explicit
            // project adaptations in the shortcut preset, but are not promoted
            // into the original-input preset.
            if (Route.bProjectAdaptation && bOriginalInputPreset) continue;
            if (Route.RequireFullSpiritCost)
            {
                const FMHWIMoveDefinition* TargetDefinition = Moveset->Moves.Find(Route.NextMove);
                if (!TargetDefinition || !FMath::IsFinite(TargetDefinition->SpiritCost)
                    || TargetDefinition->SpiritCost < 0.f || SpiritGauge < TargetDefinition->SpiritCost)
                    continue; // Keep native priority: a later route may handle low gauge.
            }
            if (Route.Input == Input && (!Route.RequireHit || bHitConfirmed)
                && (!Route.RequireCounter || bCounterConfirmed)
                && (!Route.RequireDrawn || bDrawnForRoute))
            {
                OutMove = Route.NextMove == MHWI::FadeSlash && Input == EMHWIInput::FadeSlash
                    ? SelectFadeSlashMove() : Route.NextMove;
                if (OutCancelStart && Route.CancelStart >= 0.f) *OutCancelStart = Route.CancelStart;
                if (OutCancelEnd && Route.CancelEnd >= 0.f) *OutCancelEnd = Route.CancelEnd;
                return !OutMove.IsNone();
            }
        }
        // An explicit input owns its prerequisites and window. Never let a generic
        // fallback bypass a disabled/conditional route for that same input.
        if (bHasExplicitInput) return false;
        // A sheathed Roll has no drawn-only Light route. Resolve the normal draw
        // entry so an LMB pressed while the dodge is still active is not silently
        // swallowed; a drawn Roll keeps its data-driven recovery route above.
        if (MHWI::IsRollMove(CurrentMove) && !bDrawnForRoute && Input == EMHWIInput::Light)
        {
            OutMove = TEXT("DrawSlash");
            if (!Moveset->Moves.Contains(OutMove)) OutMove = TEXT("Draw");
            return Moveset->Moves.Contains(OutMove);
        }
        // Air/Strike input is handled by RequestInput as a slam request, not a
        // generic cancel; never let an old generic path start a ground move midair.
        if (MHWI::IsHelmStageMove(CurrentMove)) return false;
        // Explicitly permitted generic cancels. Other chain links must exist in Routes.
        if (Input == EMHWIInput::Evade) { OutMove = SelectRollMove(); return true; }
        if (Input == EMHWIInput::SpecialSheathe && !bSheathed) { OutMove = MHWI::SpecialSheathe; return true; }
        if (Input == EMHWIInput::Foresight && !bSheathed) { OutMove = MHWI::ForesightSlash; return true; }
        if (Input == EMHWIInput::FadeSlash && !bSheathed)
        {
            OutMove = SelectFadeSlashMove();
            return true;
        }
        return false;
    }
    // Drawn Roll keeps its data-driven Light route for a short, bounded recovery
    // boundary. A sheathed Roll never creates this context and falls back to DrawSlash.
    if (Input == EMHWIInput::Light && CanUseRollRecovery())
    {
        OutMove = RollRecoveryMove;
        return true;
    }
    switch (Input)
    {
    case EMHWIInput::Light: OutMove = bSheathed ? TEXT("DrawSlash") : (MoveInput.Y > 0.3f ? TEXT("WalkOnSlash") : TEXT("OverheadSlash")); break;
    case EMHWIInput::Thrust: OutMove = bSheathed ? TEXT("DrawSlash") : TEXT("Thrust"); break;
    case EMHWIInput::Spirit: OutMove = bSheathed ? TEXT("DrawSlash") : TEXT("SpiritI"); break;
    case EMHWIInput::HelmBreaker: if (!bSheathed) OutMove = MHWI::SpiritThrust; break;
    case EMHWIInput::SpecialSheathe: break; // Requires an active move's cancel window.
    case EMHWIInput::Foresight: break; // Requires an active move's cancel window.
    case EMHWIInput::SlingerBurst: break; // Requires a permitted active spirit-combo source.
    case EMHWIInput::Evade: OutMove = SelectRollMove(); break;
    case EMHWIInput::ToggleSheathe: OutMove = bSheathed ? TEXT("Draw") : TEXT("Sheathe"); break;
    case EMHWIInput::FadeSlash:
        if (!bSheathed) OutMove = SelectFadeSlashMove();
        break;
    }
    if (!Moveset->Moves.Contains(OutMove) && OutMove == TEXT("DrawSlash")) OutMove = TEXT("Draw");
    return !OutMove.IsNone() && Moveset->Moves.Contains(OutMove);
}

bool AMHWICharacter::RequestInput(EMHWIInput Input)
{
    LastRequestedInput = Input;
    ++InputRequestSerial;
    if (bEnding || bFinishing || bDispatchingHits || bInputBlocked || IsGestureLocked()
        || !Attributes->IsAlive() || !Moveset) return false;
    // Aerial Helm stages own their input: PC LMB/RMB/Ctrl, their chords, and
    // the corresponding gamepad commands all become one slam request.
    if (HelmPhase == EHelmPhase::Rise || HelmPhase == EHelmPhase::Air || HelmPhase == EHelmPhase::Strike)
    {
        if (!MHWI::IsHelmSlamInput(Input)) return false;
        if (HelmPhase == EHelmPhase::Strike) return false;
        bHelmSlamRequested = true;
        if (HelmPhase == EHelmPhase::Rise)
        {
            // Reuse the normal 0.3 s buffer: an early Rise press can expire before Air.
            const UWorld* World = GetWorld();
            HelmSlamExpiresAt = (World ? World->GetTimeSeconds() : 0.f) + FMath::Max(0.f, Moveset->InputBufferSeconds);
            return true;
        }
        // Air: enter Strike immediately; the tick path retries if state was not ready.
        // Authorization is NOT granted here: only the Strike clip reaching its own
        // descent point may authorize HelmLand damage/colour loss.
        HelmSlamExpiresAt = -1.f;
        if (StartResolvedMove(MHWI::HelmStrike))
        {
            bHelmSlamRequested = false;
            return true;
        }
        return true;
    }
    if (NativeSourceMontage) return RequestNativeSourceInput(Input);
    if (CurrentMove.IsNone() || bSpecialSheathHeld)
    {
        FName NextMove;
        float Start = 0.f, End = 0.f;
        if (!ResolveInput(Input, NextMove, &Start, &End)) return false;
        if (bSpecialSheathHeld && (CurrentPosition < Start || CurrentPosition > End)) return false;
        return StartResolvedMove(NextMove);
    }
    PendingInput = Input;
    PendingExpiresAt = GetWorld()->GetTimeSeconds() + FMath::Max(0.f, Moveset->InputBufferSeconds);
    if (bNativeConnector)
    {
        PendingMontagePosition = 0.f;
        bBufferedInsideWindow = false;
        return true;
    }
    UAnimInstance* Anim = GetMesh()->GetAnimInstance();
    FAnimMontageInstance* Instance = Anim ? Anim->GetMontageInstanceForID(ActiveMontageInstanceId) : nullptr;
    const float Position = Instance ? Instance->GetPosition() : CurrentPosition;
    PendingMontagePosition = Position;
    FName BufferedMove;
    float Start = 0.f, End = 0.f;
    bBufferedInsideWindow = ResolveInput(Input, BufferedMove, &Start, &End)
        && Position >= Start && Position <= End;
    // Character tick resolves requests after processing hit windows at the same animation position.
    return true;
}

bool AMHWICharacter::StartResolvedMove(FName MoveId)
{
    if (bEnding || bFinishing || bDispatchingHits || !Moveset || !Attributes->IsAlive()) return false;
    const int32 SourceAction = MHWI::Native::SlingerActionFromMove(MoveId);
    if (SourceAction != INDEX_NONE) return StartNativeSource({3, SourceAction}, ENativeSourceKind::Slinger);
    if (bSheathed && MHWI::IsRollMove(MoveId) && MoveId != MHWI::Roll) return false;
    // Stage entry is an identity/lifecycle rule: a hit-confirmed white+ Spirit
    // Thrust is the only way into Rise, and landing/input own the later stages.
    if (!CanStartHelmStage(MoveId)) return false;
    // R26: no ground action may start from a falling state; airborne behaviour
    // must come from an explicit aerial/environment branch, not a neutral input.
    if (GetCharacterMovement()->IsFalling() && !MHWI::IsHelmStageMove(MoveId) && !MHWI::IsRollMove(MoveId)) return false;
    const FMHWIMoveDefinition* Definition = Moveset->Moves.Find(MoveId);
    UAnimInstance* Anim = GetMesh()->GetAnimInstance();
    if (!Definition || !Anim || !FMath::IsFinite(Definition->PlayRate) || Definition->PlayRate <= 0.f
        || !FMath::IsFinite(Definition->SpiritCost) || Definition->SpiritCost < 0.f) return false;
    UAnimMontage* SelectedMontage = Definition->Montage;
    if (bSheathed && Definition->SheathedMontage) SelectedMontage = Definition->SheathedMontage;
    if (const TObjectPtr<UAnimMontage>* Variant = Definition->SpiritLevelMontages.Find(SpiritLevel)) SelectedMontage = *Variant;
    if (!SelectedMontage || !GetMesh()->GetSkeletalMeshAsset()
        || SelectedMontage->GetSkeleton() != GetMesh()->GetSkeletalMeshAsset()->GetSkeleton()) return false;
    // Capture the old action and actual source clock before FinishMove clears it.
    FNativeLinkStart NativeStart;
    if (!PrepareNativeLink(MoveId, SelectedMontage, NativeStart)) return false;
    int32 SelectedBodyMotion = INDEX_NONE;
    const int32 SelectedTimelineMotion = MHWI::Native::ReadMainMotion(SelectedMontage, SelectedBodyMotion)
        ? MHWI::Native::GetTimelineMotion(MoveId, SpiritLevel, SelectedBodyMotion) : INDEX_NONE;
    const bool bWeakSpiritAttack = Definition->bAllowWeakSpiritAttack && SpiritGauge < Definition->SpiritCost;
    if ((!bWeakSpiritAttack && SpiritGauge < Definition->SpiritCost) || (Definition->bRequireSpiritLevel && SpiritLevel <= 0)
        || (Definition->bRequireNonzeroGauge && SpiritGauge <= 0.f)) return false;
    FMHWIMoveDefinition NewDefinition = *Definition;
    const float StartingGauge = SpiritGauge;
    if (bWeakSpiritAttack)
    {
        NewDefinition.SpiritCost = 0.f;
        for (FMHWIHitWindow& Window : NewDefinition.DamageWindows)
            Window.SpiritGain = FMath::Max(0.f, NewDefinition.WeakSpiritGain);
    }
    const bool bContinueHelm = MHWI::IsHelmContinuation(CurrentMove, MoveId);
    const bool bWasDrawn = !bSheathed;
    const bool bWasBackMounted = bSheathed || WeaponAttachmentRuntime.IsBackMounted();
    UAnimMontage* PreviousCarrier = ActiveMontage ? ActiveMontage.Get() : NativeSourceMontage.Get();
    // A direct chain has no displayed neutral frame. Preserve the old internal
    // weapon pose until the successor selects its own event/default animation.
    // Let Montage_Play perform the physical handoff with the successor's MBD
    // blend. Logical cleanup still invalidates all callbacks before playback.
    FinishMove(true, false, bContinueHelm, true);
    NativeRetiringMontage = PreviousCarrier;
    if (bEnding || !Attributes->IsAlive())
    {
        FinishMove(true, true);
        return false;
    }
    ++ExecutionSerial;
    const uint32 Serial = ExecutionSerial;
    ActiveDefinition = NewDefinition;
    CurrentMove = MoveId;
    ActiveMontage = SelectedMontage;
    NativeActionNode = NativeStart.TargetNode;
    NativeTimelineMotion = SelectedTimelineMotion;
    if (!BeginNativeLink(NativeStart))
    {
        FinishMove(true, true);
        return false;
    }
    PreviousPosition = CurrentPosition = bNativeConnector ? 0.f : NativeInitialPosition;
    NextWeaponMotionEvent = 0;
    PreviousActorLocation = GetActorLocation();
    ActionStartWorldTime = GetWorld()->GetTimeSeconds();
    CapturedDamageMultiplier = MHWI::SpiritMultipliers[FMath::Clamp(SpiritLevel, 0, 3)] * FMath::Max(0.f, Moveset->BaseDamageMultiplier);
    CapturedSpiritLevel = SpiritLevel;
    CapturedSpiritGauge = StartingGauge;
    CapturedWeakMultiplier = bWeakSpiritAttack ? FMath::Clamp(NewDefinition.WeakDamageMultiplier, 0.f, 1.f) : 1.f;
    if (bWeakSpiritAttack)
        CapturedDamageMultiplier *= CapturedWeakMultiplier;
    bHitConfirmed = bCounterConfirmed = bRaisedLevelThisAction = false;
    bRoundslashHitLatched = false;
    bSpecialSheathHeld = false;
    bMoveStartedSheathed = bWasBackMounted;
    SpecialSheathElapsed = 0.f;
    HitActors.Reset();
    WindowsThatGrantedGauge.Reset();
    MainTurnAccumulated = ReturnTurnAccumulated = 0.f;

    if (MHWI::IsRollMove(MoveId))
    {
        RollProtectionFramesRemaining = SelectEvasionProtectionFrames();
        bRollStartedDrawn = bWasDrawn;
        // Roll keeps the original free-form start direction; Fade Slash does not.
        if (MoveId == MHWI::Roll && !MoveInput.IsNearlyZero() && Controller)
        {
            const FVector DodgeDirection = GetMoveIntentWorldDirection();
            if (!DodgeDirection.IsNearlyZero()) SetActorRotation(DodgeDirection.Rotation());
        }
        if (bWasDrawn) CaptureRollRecovery(NewDefinition, SelectedMontage);
        else ClearRollRecovery();
    }
    else
    {
        RollProtectionFramesRemaining = 0.f;
        bRollStartedDrawn = false;
        ClearRollRecovery();
    }

    // A helm chain owns its velocity across stages; a per-step stop would erase
    // the Rise/Air/Strike motion that the previous stage handed over.
    if (!bContinueHelm) GetCharacterMovement()->StopMovementImmediately();
    const float StartPosition = bNativeConnector ? NativeConnectorPosition : NativeInitialPosition;
    const float StartRate = bNativeConnector ? 1.f : NewDefinition.PlayRate * EvaluateSourcePlayRate(StartPosition);
    if (!NativeStart.bContinuePrevious)
        if (UMHWIAnimInstance* NativeAnim = Cast<UMHWIAnimInstance>(Anim))
            NativeAnim->BeginNativeBlend(FMath::RoundToInt(FMath::Max(0.f, NativeBlendFrames)));
    if (!NativeStart.bContinuePrevious
        && Anim->Montage_Play(ActiveMontage, StartRate, EMontagePlayReturnType::MontageLength, StartPosition) <= 0.f)
    {
        FinishMove(true, true);
        return false;
    }
    NativeRetiringMontage = nullptr;
    if (FAnimMontageInstance* Instance = Anim->GetActiveInstanceForMontage(ActiveMontage))
        ActiveMontageInstanceId = Instance->GetInstanceID();
    FOnMontageEnded EndDelegate;
    EndDelegate.BindUObject(this, &AMHWICharacter::MontageEnded, Serial);
    Anim->Montage_SetEndDelegate(EndDelegate, ActiveMontage);
    if (Serial != ExecutionSerial || bEnding) return false;
    ApplyStageMovement(MoveId, NewDefinition);
    float NewGauge = SpiritGauge - NewDefinition.SpiritCost + NewDefinition.SpiritGainOnStart;
    if (NewDefinition.bConsumeAllGauge) NewGauge = 0.f;
    SetSpiritGauge(NewGauge);
    if (NewDefinition.bUnsheathAtStart) bSheathed = false;
    // A roll never changes the sheathe state by itself: a sheathed dodge must
    // still resolve its next neutral Light to DrawSlash, not a drawn entry.
    if (MHWI::IsRollMove(MoveId)) bSheathed = !bWasDrawn;
    if (bNativeConnector)
    {
        if (!NativeStart.bContinuePrevious) AdvanceConnectorWeaponEvents(-1.f, NativeConnectorSourceFrame);
    }
    else InitializeMainEventClock(StartPosition);
    if (!bNativeConnector && !NewDefinition.WeaponMotionEvents.ContainsByPredicate([](const FMHWIWeaponMotionEvent& Event)
        { return FMath::IsFinite(Event.Time) && Event.Time >= 0.f && Event.MotionNo >= 0; }))
        SetSourceWeaponMotion(bSheathed ? 0 : (bMoveStartedSheathed ? 2 : 1));
    RefreshWeaponAttachment();
    RefreshMovement();
    OnMoveChanged.Broadcast(CurrentMove, GetMoveDisplayName());
    if (Serial == ExecutionSerial && !bEnding) OnStateChanged.Broadcast();
    return Serial == ExecutionSerial && !bEnding;
}

bool AMHWICharacter::StartMove(FName MoveId)
{
    // Blueprint entry is neutral only. Active chains must pass RequestInput's routes.
    return !bInputBlocked && CurrentMove.IsNone() && !NativeSourceMontage && StartResolvedMove(MoveId);
}

void AMHWICharacter::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    ON_SCOPE_EXIT { if (!bEnding) RefreshWeaponAttachment(DeltaSeconds); };
    if (bEnding || !Attributes->IsAlive()) return;
    ResolveKeyboardFrameInputEdges();
    if (bOriginalInputPreset) ResolveFrameInputEdges();
    // Hit stop freezes the action/weapon presentation clock only. Resource and
    // colour timers below still run, so a hit lag can never extend the gauge.
    const bool bHitLagThisFrame = PendingHitLag > 0.f;
    if (bHitLagThisFrame) PendingHitLag = FMath::Max(0.f, PendingHitLag - DeltaSeconds);
    else UpdateSourceWeaponPose(DeltaSeconds);
    CounterArmorRemaining = FMath::Max(0.f, CounterArmorRemaining - DeltaSeconds);
    RollProtectionFramesRemaining = FMath::Max(0.f, RollProtectionFramesRemaining - DeltaSeconds * 60.f);
    bool bResourceChanged = false;
    if (SpiritLevel > 0)
    {
        // Native order: subtract the pause first; only an expired pause permits
        // colour-T to advance. A long frame is not split into invented substeps.
        SpiritDecayPauseRemaining = FMath::Max(0.f, SpiritDecayPauseRemaining - DeltaSeconds);
        if (SpiritDecayPauseRemaining <= 0.f)
        {
            SpiritTimeRemaining = FMath::Max(0.f, SpiritTimeRemaining - DeltaSeconds);
            if (SpiritTimeRemaining <= 0.f) { SetSpiritLevel(SpiritLevel - 1); bResourceChanged = true; }
        }
    }
    if (GaugeRegenSeconds > 0.f)
    {
        const float EffectiveSeconds = FMath::Min(DeltaSeconds, GaugeRegenSeconds);
        GaugeRegenSeconds = FMath::Max(0.f, GaugeRegenSeconds - DeltaSeconds);
        SetSpiritGauge(SpiritGauge + EffectiveSeconds
            * (Moveset ? FMath::Max(0.f, Moveset->GaugeRegenPerSecond) : 0.f));
        bResourceChanged = true;
    }
    else if (Moveset && Moveset->SpiritGaugeDecayTimeScale > 0.f && Moveset->SpiritGaugeDecayFraction > 0.f)
    {
        SpiritGaugeDecayCountdown -= DeltaSeconds / Moveset->SpiritGaugeDecayTimeScale;
        if (SpiritGaugeDecayCountdown < 0.f)
        {
            ResetSpiritGaugeDecayClock();
            SetSpiritGauge(SpiritGauge - 100.f * Moveset->SpiritGaugeDecayFraction);
            bResourceChanged = true;
        }
    }
    TickDelayedShells(DeltaSeconds);
    if (bResourceChanged) OnStateChanged.Broadcast();
    if (bEnding || !Attributes->IsAlive()) return;

    // A Roll recovery route is short-lived and never survives sheathing.
    if (!RollRecoveryMove.IsNone()
        && (bSheathed || GetWorld()->GetTimeSeconds() > RollRecoveryExpiresAt))
    {
        ClearRollRecovery();
    }

    if (bSpecialSheathHeld)
    {
        SpecialSheathElapsed += DeltaSeconds;
        if (!Moveset || SpecialSheathElapsed >= Moveset->SpecialSheathHoldSeconds) FinishMove(false, true);
        return;
    }

    // Landed() only records the fact and execution serial. Switching stages at
    // this safe point prevents movement-callback reentry and duplicate commits.
    HandleHelmLanding();
    if (bEnding || !Attributes->IsAlive()) return;

    // Air attack input enters Strike immediately; the Strike clip itself commits
    // the fast descent once at HelmStrikeStartTime, never at 0 s.
    if (HelmPhase == EHelmPhase::Air) MaybeCommitHelmStrike();
    if (HelmPhase == EHelmPhase::Strike) MaybeStartHelmDescent();

    if (TickNativeSource()) return;
    if (!ActiveMontage) return;
    UAnimInstance* Anim = GetMesh()->GetAnimInstance();
    if (bHitLagThisFrame)
    {
        if (Anim) Anim->Montage_SetPlayRate(ActiveMontage, 0.f);
        return;
    }
    FAnimMontageInstance* Instance = Anim ? Anim->GetMontageInstanceForID(ActiveMontageInstanceId) : nullptr;
    if (!Instance || Instance->GetInstanceID() != ActiveMontageInstanceId)
    {
        if (HelmPhase == EHelmPhase::Air || HelmPhase == EHelmPhase::Strike)
        {
            // The pose carrier ended while still airborne: hold the stage and let
            // real landing (or a queued slam) drive the next transition.
            bHelmPoseHeld = true;
            if (HelmPhase == EHelmPhase::Air) MaybeCommitHelmStrike();
            if (HelmPhase == EHelmPhase::Strike) MaybeStartHelmDescent();
            return;
        }
        FinishMove(true, false);
        return;
    }
    const float NewPosition = Instance->GetPosition();
    if (bNativeConnector)
    {
        if (!Instance->IsActive() || (!Instance->IsPlaying()
            && NewPosition < ActiveMontage->GetPlayLength() - KINDA_SMALL_NUMBER))
        { FinishMove(true, true); return; }
        // Connection time is not action time: no main hits, routes or turn windows.
        AdvanceNativeLink(NewPosition);
        return;
    }
    // Cache the id before AdvanceAction: it may start another stage and stop this
    // montage, invalidating the FAnimMontageInstance pointer.
    const int32 PlayingInstanceId = Instance->GetInstanceID();
    // The previous position is needed for cross-frame window overlap; it is read
    // before a loop rewind can reassign CurrentPosition.
    const float PositionBeforeUpdate = CurrentPosition;
    if (!bHelmPoseHeld)
    {
        Anim->Montage_SetPlayRate(ActiveMontage, ActiveDefinition.PlayRate * EvaluateSourcePlayRate(NewPosition));
        if (NewPosition + KINDA_SMALL_NUMBER < CurrentPosition)
        {
            if (MHWI::IsHelmAerialStageMove(CurrentMove))
            {
                // 172/173 may loop while airborne; a loop-point rewind is pose
                // progression, not a broken montage and never an automatic landing.
                CurrentPosition = NewPosition;
                PreviousPosition = NewPosition;
            }
            else
            {
                FinishMove(true, true);
                return;
            }
        }
        ApplyTurnWindows(PositionBeforeUpdate, NewPosition);
        AdvanceAction(NewPosition, true);
        if (bEnding || !Attributes->IsAlive()) return;
    }
    if (HelmPhase == EHelmPhase::Air) MaybeCommitHelmStrike();
    if (HelmPhase == EHelmPhase::Strike) MaybeStartHelmDescent();
    if (bEnding || !Attributes->IsAlive()) return;

    // Air/Strike may reach the animation tail while still airborne. Pause the pose
    // instead of treating that as landing or as an automatic next stage.
    if (ActiveMontage && !bHelmPoseHeld && MHWI::IsHelmAerialStageMove(CurrentMove)
        && ActiveMontageInstanceId == PlayingInstanceId)
    {
        const float Length = ActiveMontage->GetPlayLength();
        if (NewPosition >= Length - 0.02f)
        {
            Anim->Montage_Pause(ActiveMontage);
            bHelmPoseHeld = true;
        }
    }

    // A stopped/paused external montage must not permanently lock the character.
    // Aerial stages are excluded: gravity/landing, not montage length, ends them.
    if (ActiveMontage && !bSpecialSheathHeld && !MHWI::IsHelmAerialStageMove(CurrentMove)
        && GetWorld()->GetTimeSeconds() - ActionStartWorldTime > ActiveMontage->GetPlayLength() / FMath::Max(ActiveDefinition.PlayRate, 0.01f) + 1.f)
        FinishMove(true, true);
}

void AMHWICharacter::AdvanceAction(float NewPosition, bool bAllowTransition)
{
    if (bEnding || !ActiveMontage || bDispatchingHits) return;
    const uint32 Serial = ExecutionSerial;
    const float From = CurrentPosition;
    CurrentPosition = NewPosition;
    AdvanceSourceWeaponEvents(From, NewPosition);
    bDispatchingHits = true;
    const TArray<FMHWIHitWindow> Windows = ActiveDefinition.DamageWindows;
    for (int32 Index = 0; Index < Windows.Num(); ++Index)
    {
        const FMHWIHitWindow& Window = Windows[Index];
        if (Window.StartTime <= NewPosition && Window.EndTime >= From && Window.EndTime >= Window.StartTime)
            SweepWindow(Index, Window);
        if (Serial != ExecutionSerial || bEnding || bPendingDeath || bPendingInterruption || bPendingNativeRecoil) break;
    }
    bDispatchingHits = false;
    if (bPendingDeath) { bPendingDeath = false; HandleDeath(); return; }
    if (PendingNativeImpact.IsSet())
    {
        const EMHWIImpactSize Size = PendingNativeImpact.GetValue();
        PendingNativeImpact.Reset();
        bPendingInterruption = false;
        StartNativeImpact(Size);
        return;
    }
    if (bPendingNativeRecoil)
    {
        bPendingNativeRecoil = false;
        if (!StartNativeSource({3, 34}, ENativeSourceKind::Recoil)) InterruptMove();
        return;
    }
    if (bPendingInterruption) { bPendingInterruption = false; InterruptMove(); return; }
    if (Serial != ExecutionSerial || bEnding) return;
    PreviousPosition = CurrentPosition;
    PreviousActorLocation = GetActorLocation();
    if (!bAllowTransition) return;
    FName FollowUp = !ActiveDefinition.AutoFollowUp.IsNone() ? ActiveDefinition.AutoFollowUp
        : (bHitConfirmed ? ActiveDefinition.AutoFollowUpOnHit : NAME_None);
    // Air and Strike are driven by input/landing, never by montage length.
    if (MHWI::IsHelmAerialStageMove(CurrentMove)) FollowUp = NAME_None;
    if (!FollowUp.IsNone() && NewPosition >= ActiveDefinition.AutoFollowUpTime)
    {
        if (StartResolvedMove(FollowUp)) return;
        // The stage gate denied the link (no real hit / no white+ colour) or the
        // new montage failed; never pretend the transition happened.
        if (Serial != ExecutionSerial || bEnding) return;
    }
    if (ActiveDefinition.bHoldsSpecialSheath)
    {
        const float HoldPosition = ActiveDefinition.SpecialSheathHoldTime >= 0.f ? ActiveDefinition.SpecialSheathHoldTime : ActiveMontage->GetPlayLength() - 0.05f;
        if (NewPosition >= HoldPosition) { EnterSpecialSheathHold(); return; }
    }
    TryConsumeBuffered(From, NewPosition);
}

void AMHWICharacter::SweepWindow(int32 WindowIndex, const FMHWIHitWindow& Window)
{
    if (!GetWorld() || bEnding || !Attributes->IsAlive()) return;
    // A natural Air -> Land finish carries no damage authorization: no seven-hit
    // settlement and no colour loss without this chain's committed down-slam.
    if (CurrentMove == MHWI::HelmLand && !bHelmSlamAuthorized) return;
    const FVector Forward = GetActorForwardVector();
    const FVector Right = GetActorRightVector();
    const FVector Up(0.f, 0.f, 35.f);
    // Swept volume follows the character's root displacement, plus a blade-width fan.
    // This bounded fallback also works without authoring socket names on imported bones.
    FCollisionQueryParams Params(SCENE_QUERY_STAT(MHWIHit), false, this);
    FCollisionObjectQueryParams Objects;
    Objects.AddObjectTypesToQuery(ECC_Pawn);
    Objects.AddObjectTypesToQuery(ECC_WorldDynamic);
    TArray<FHitResult> Results;
    const float Reach = FMath::Clamp(Window.ForwardReach, 1.f, 1000.f);
    const float Radius = FMath::Clamp(Window.Radius, 1.f, 200.f);
    const FVector Start = PreviousActorLocation + Up;
    const FVector End = GetActorLocation() + Forward * Reach + Up;
    TSet<TWeakObjectPtr<AActor>> Candidates;
    TMap<TWeakObjectPtr<AActor>, FVector> ContactLocations;
    GetWorld()->SweepMultiByObjectType(Results, Start, End, FQuat::Identity, Objects, FCollisionShape::MakeSphere(Radius), Params);
    for (int32 Side = -1; Side <= 1; Side += 2)
    {
        TArray<FHitResult> SideHits;
        GetWorld()->SweepMultiByObjectType(SideHits, GetActorLocation() + Forward * Reach * 0.3f + Up,
            End + Right * Window.SideExtent * Side, FQuat::Identity, Objects, FCollisionShape::MakeSphere(Radius), Params);
        Results.Append(SideHits);
    }
    for (const FHitResult& Hit : Results)
    {
        Candidates.Add(Hit.GetActor());
        if (!ContactLocations.Contains(Hit.GetActor())) ContactLocations.Add(Hit.GetActor(), Hit.ImpactPoint);
    }
    const uint32 Serial = ExecutionSerial;
    TSet<TWeakObjectPtr<AActor>>& Actors = HitActors.FindOrAdd(WindowIndex);
    for (const TWeakObjectPtr<AActor>& Candidate : Candidates)
    {
        AActor* Target = Candidate.Get();
        if (!IsValid(Target) || Target == this || Actors.Contains(Target)) continue;
        UAttributeComponent* TargetAttributes = Target->FindComponentByClass<UAttributeComponent>();
        if (!TargetAttributes || !TargetAttributes->IsAlive()) continue;
        // Deflection is an explicit contact outcome, not an inference from zero HP loss.
        if (Target->GetClass()->ImplementsInterface(UMHWIContactResponse::StaticClass())
            && IMHWIContactResponse::Execute_DeflectsMHWIWeapon(Target, this))
        {
            if (Serial == ExecutionSerial && !bEnding && !bPendingDeath
                && !bPendingInterruption && Attributes->IsAlive()) bPendingNativeRecoil = true;
            return;
        }
        if (Serial != ExecutionSerial || bEnding || bPendingDeath || bPendingInterruption) return;
        if (!IsValid(Target) || !IsValid(TargetAttributes) || !TargetAttributes->IsAlive()) continue;
        // Record before publishing damage, because target delegates can reenter gameplay.
        Actors.Add(Target);
        const float HealthBefore = TargetAttributes->GetCurrentHealth();
        const float CounterMultiplier = bCounterConfirmed ? FMath::Max(0.f, ActiveDefinition.CounterDamageMultiplier) : 1.f;
        const float* LevelDamage = Window.SpiritLevelDamage.Find(CapturedSpiritLevel);
        const float BaseDamage = LevelDamage ? *LevelDamage : Window.Damage;
        const float FinalDamage = FMath::Max(0.f, BaseDamage) * CapturedDamageMultiplier * CounterMultiplier;
        const FVector* FoundContact = ContactLocations.Find(Candidate);
        const FVector ContactLocation = FoundContact ? *FoundContact : Target->GetActorLocation();
        // R22: publish a structured result before applying damage. FinalDamage is
        // deliberately identical to the previous expression; unresolved stages
        // stay Unavailable rather than receiving invented multipliers.
        LastResolvedHit = FMHWIResolvedHit();
        LastResolvedHit.MoveId = CurrentMove;
        LastResolvedHit.WindowIndex = WindowIndex;
        LastResolvedHit.ColRecordIndex = Window.ColRecordIndex;
        LastResolvedHit.MotionValueBase = BaseDamage;
        LastResolvedHit.ColorMultiplier = MHWI::SpiritMultipliers[FMath::Clamp(CapturedSpiritLevel, 0, 3)]
            * (Moveset ? FMath::Max(0.f, Moveset->BaseDamageMultiplier) : 1.f);
        LastResolvedHit.WeakMultiplier = CapturedWeakMultiplier;
        LastResolvedHit.CounterMultiplier = CounterMultiplier;
        LastResolvedHit.FinalDamage = FinalDamage;
        LastResolvedHit.ContactLocation = ContactLocation;
        TargetAttributes->ApplyDamage(FinalDamage, this);
        if (Serial != ExecutionSerial || bEnding || bPendingDeath || bPendingInterruption) return;
        if (!IsValid(TargetAttributes) || TargetAttributes->GetCurrentHealth() >= HealthBefore) continue;
        if (CurrentMove == MHWI::HelmStrike) ScheduleHelmShell(Target, ContactLocation);
        else if (CurrentMove == MHWI::IaiSpiritSlash) ScheduleIaiShell(Target, ContactLocation);
        bHitConfirmed = true;
        // R31: one hit event and one presentation-only stop per confirmed hit.
        PendingHitLag = FMath::Max(PendingHitLag, FMath::Max(0.f, Window.HitLagSeconds));
        OnHitResolved.Broadcast(CurrentPosition, WindowIndex, Window.ColRecordIndex);
        if (!WindowsThatGrantedGauge.Contains(WindowIndex))
        {
            WindowsThatGrantedGauge.Add(WindowIndex);
            SetSpiritGauge(SpiritGauge + Window.SpiritGain);
        }
        if (bCounterConfirmed && ActiveDefinition.bCounterRestoresGaugeOnHit) SetSpiritGauge(100.f);
        const float RegenDuration = bCounterConfirmed && ActiveDefinition.CounterGaugeRegenOnHitSeconds >= 0.f
            ? ActiveDefinition.CounterGaugeRegenOnHitSeconds : ActiveDefinition.GaugeRegenOnHitSeconds;
        GaugeRegenSeconds = FMath::Max(GaugeRegenSeconds, RegenDuration);
        if (CurrentMove == MHWI::SpiritRoundslash && ActiveDefinition.bRaiseSpiritOnHit)
        {
            // Action69 contact only latches eligibility. The exit/update commit,
            // not this damage callback, clears Q and raises/refreshes the colour.
            bRoundslashHitLatched = true;
        }
        else if (ActiveDefinition.bRaiseSpiritOnHit && !bRaisedLevelThisAction)
        {
            bRaisedLevelThisAction = true;
            SetSpiritLevel(SpiritLevel + 1);
        }
        OnStateChanged.Broadcast();
        if (Serial != ExecutionSerial || bEnding || bPendingDeath || bPendingInterruption) return;
    }
}

bool AMHWICharacter::TryConsumeBuffered(float From, float To)
{
    if (!PendingInput.IsSet() || !ActiveMontage || bEnding) return false;
    if (!bBufferedInsideWindow && GetWorld()->GetTimeSeconds() > PendingExpiresAt)
    {
        PendingInput.Reset();
        return false;
    }
    // A request cannot retroactively claim animation time before it was received.
    // This matters when the montage-end callback catches up a low-frame interval.
    From = FMath::Max(From, PendingMontagePosition);
    FName NextMove;
    float Start = 0.f, End = 0.f;
    if (!ResolveInput(PendingInput.GetValue(), NextMove, &Start, &End)
        || !FMath::IsFinite(Start) || !FMath::IsFinite(End) || End < Start
        || To < Start || From > End) return false;
    bBufferedInsideWindow = true;
    // Interval overlap authorizes the buffered route even if a long frame passed
    // the entire chain window. Never rewind a root-motion montage to do this.
    return StartResolvedMove(NextMove);
}

void AMHWICharacter::MontageEnded(UAnimMontage* Montage, bool bInterrupted, uint32 Serial)
{
    if (bEnding || bFinishing || Serial != ExecutionSerial || Montage != ActiveMontage) return;
    if (bNativeConnector)
    {
        if (bInterrupted) FinishMove(true, false);
        else AdvanceNativeLink(Montage->GetPlayLength(), true);
        return;
    }
    if (!bInterrupted)
    {
        const float TailFrom = CurrentPosition;
        AdvanceAction(Montage->GetPlayLength(), false);
        if (bEnding || Serial != ExecutionSerial || !Attributes->IsAlive()) return;
        // Reaching the tail of Air/Strike is neither landing nor an automatic next
        // stage. Hold the pose; Tick's landing/slam logic owns the transition.
        if (MHWI::IsHelmAerialStageMove(CurrentMove))
        {
            bHelmPoseHeld = true;
            return;
        }
        // End callbacks occur during animation update. Process a missed entire chain
        // window before disposing the execution, including low-frame-rate crossings.
        if (PendingInput.IsSet() && TryConsumeBuffered(TailFrom, CurrentPosition)) return;
        const FName FollowUp = !ActiveDefinition.AutoFollowUp.IsNone() ? ActiveDefinition.AutoFollowUp
            : (bHitConfirmed ? ActiveDefinition.AutoFollowUpOnHit : NAME_None);
        if (!FollowUp.IsNone())
        {
            const bool bContinueHelm = MHWI::IsHelmContinuation(CurrentMove, FollowUp);
            ActiveMontage = nullptr;
            // StartResolvedMove must see the previous stage to authorize mark transfer.
            if (bContinueHelm)
            {
                if (StartResolvedMove(FollowUp)) return;
                FinishMove(true, false);
                return;
            }
            FinishMove(false, false);
            StartResolvedMove(FollowUp);
            return;
        }
        if (ActiveDefinition.bHoldsSpecialSheath)
        {
            EnterSpecialSheathHold();
            return;
        }
    }
    FinishMove(bInterrupted, false);
}

void AMHWICharacter::FinishMove(bool bInterrupted, bool bStopMontage, bool bContinueHelm, bool bDeferEquipmentReset)
{
    if (bFinishing) return;
    bFinishing = true;
    UAnimMontage* OldMontage = ActiveMontage;
    const bool bHadMove = !CurrentMove.IsNone() || !NativeSourceMove.IsNone();
    const FName FinishedMove = CurrentMove;
    if (FinishedMove == MHWI::IaiSpiritSlash) IaiDelayedHit.Reset();
    CommitRoundslash();
    RollProtectionFramesRemaining = 0.f;
    // HelmLand's level spend (colour loss) requires this chain's real down-slam.
    const bool bAuthorizedHelmLand = FinishedMove != MHWI::HelmLand || bHelmSlamAuthorized;
    if (bHadMove)
    {
        if (ActiveDefinition.bSpendSpiritLevel && bAuthorizedHelmLand
            && (!ActiveDefinition.bPreserveLevelOnCounter || !bCounterConfirmed))
            SetSpiritLevel(SpiritLevel - 1);
        if (!bInterrupted && ActiveDefinition.bSheathAtEnd) bSheathed = true;
    }
    ++ExecutionSerial;
    if (MHWI::IsRollMove(FinishedMove) && !bInterrupted && bRollStartedDrawn)
    {
        MHWI::Native::ReadMotion(OldMontage, CurrentPosition, NativeRollRecoverySample);
        NativeRollRecoveryNode = NativeActionNode;
    }
    else if (!bDeferEquipmentReset) NativeRollRecoverySample = {};
    NativeLinkExecution.Cancel();
    NativeMainMontage = nullptr;
    NativeActionNode = INDEX_NONE;
    NativeTimelineMotion = INDEX_NONE;
    bNativeConnector = false;
    NativeConnectorPosition = 0.f;
    NativeConnectorSourceFrame = 0.f;
    NativeInitialPosition = 0.f;
    UAnimMontage* OldNativeSource = NativeSourceMontage;
    ReleaseNativeActionSource(NativeSourceGeneration);
    PendingNativeImpact.Reset();
    bPendingNativeRecoil = false;
    if (bStopMontage)
        if (UMHWIAnimInstance* NativeAnim = Cast<UMHWIAnimInstance>(GetMesh()->GetAnimInstance())) NativeAnim->CancelNativeBlend();
    ActiveMontage = nullptr;
    ActiveMontageInstanceId = INDEX_NONE;
    CurrentMove = NAME_None;
    bSpecialSheathHeld = false;
    PendingInput.Reset();
    bBufferedInsideWindow = false;
    PendingMontagePosition = 0.f;
    // Hit stop belongs to the execution that produced it; never freeze the next action.
    PendingHitLag = 0.f;
    HitActors.Reset();
    WindowsThatGrantedGauge.Reset();
    if (!bContinueHelm)
    {
        // Restores the one aerial snapshot (movement mode, gravity, root motion)
        // exactly once when the chain leaves its legal stages.
        ResetHelmChain();
    }
    if (bInterrupted || bEnding || bSheathed) ClearRollRecovery();
    if (bStopMontage && OldMontage && GetMesh()->GetAnimInstance())
        GetMesh()->GetAnimInstance()->Montage_Stop(FMath::Max(0.f, ActiveDefinition.BlendOut), OldMontage);
    if (bStopMontage && OldNativeSource && OldNativeSource != OldMontage && GetMesh()->GetAnimInstance())
        GetMesh()->GetAnimInstance()->Montage_Stop(0.f, OldNativeSource);
    if (bStopMontage && NativeRetiringMontage && GetMesh()->GetAnimInstance())
        GetMesh()->GetAnimInstance()->Montage_Stop(0.f, NativeRetiringMontage);
    NativeRetiringMontage = nullptr;
    ActiveDefinition = FMHWIMoveDefinition();
    NextWeaponMotionEvent = 0;
    if (!bDeferEquipmentReset)
    {
        SetSourceWeaponMotion(bSheathed ? 0 : 1);
        RefreshWeaponAttachment();
    }
    RefreshMovement();
    if (bHadMove && !bEnding)
    {
        OnMoveChanged.Broadcast(NAME_None, FText::GetEmpty());
        if (!bEnding) OnStateChanged.Broadcast();
    }
    if (ControlState != EMHWIControlState::Dead) ControlState = EMHWIControlState::Free;
    bFinishing = false;
}

void AMHWICharacter::EnterSpecialSheathHold()
{
    UAnimInstance* Anim = GetMesh()->GetAnimInstance();
    if (!Anim || !ActiveMontage) { FinishMove(true, true); return; }
    const float HoldPosition = FMath::Clamp(ActiveDefinition.SpecialSheathHoldTime >= 0.f
        ? ActiveDefinition.SpecialSheathHoldTime : ActiveMontage->GetPlayLength() - 0.05f,
        0.f, FMath::Max(0.f, ActiveMontage->GetPlayLength() - 0.001f));
    // A very long frame may already have ended the montage. Recreate only its pose
    // carrier; no action costs or hit effects are committed a second time.
    if (!Anim->GetActiveInstanceForMontage(ActiveMontage))
    {
        if (Anim->Montage_Play(ActiveMontage, ActiveDefinition.PlayRate) <= 0.f) { FinishMove(true, false); return; }
        if (FAnimMontageInstance* Instance = Anim->GetActiveInstanceForMontage(ActiveMontage)) ActiveMontageInstanceId = Instance->GetInstanceID();
    }
    Anim->Montage_SetPosition(ActiveMontage, HoldPosition);
    Anim->Montage_Pause(ActiveMontage);
    CurrentPosition = PreviousPosition = HoldPosition;
    bSpecialSheathHeld = true;
    bSheathed = true;
    SpecialSheathElapsed = 0.f;
    RefreshWeaponAttachment();
    const uint32 Serial = ExecutionSerial;
    OnStateChanged.Broadcast();
    if (bEnding || Serial != ExecutionSerial || !PendingInput.IsSet()) return;
    if (bBufferedInsideWindow || GetWorld()->GetTimeSeconds() <= PendingExpiresAt)
    {
        TryConsumeBuffered(HoldPosition, HoldPosition);
    }
}

void AMHWICharacter::CaptureRollRecovery(const FMHWIMoveDefinition& Definition, const UAnimMontage* PlayedMontage)
{
    ClearRollRecovery();
    for (const FMHWIRoute& Route : Definition.Routes)
    {
        if (Route.Input == EMHWIInput::Light && Route.RequireDrawn && !Route.NextMove.IsNone())
        {
            RollRecoveryMove = Route.NextMove;
            break;
        }
    }
    if (RollRecoveryMove.IsNone() || !Moveset || !Moveset->Moves.Contains(RollRecoveryMove))
    {
        ClearRollRecovery();
        return;
    }
    // Use only the definition that owns this Roll (never the previous
    // ActiveDefinition), so a prior fast action cannot shorten the window.
    const TMap<float, float>& RateKeys = SpiritLevel > 0 && !Definition.EmpoweredSourcePlayRates.IsEmpty()
        ? Definition.EmpoweredSourcePlayRates : Definition.SourcePlayRates;
    float LowerTime = -FLT_MAX, UpperTime = FLT_MAX, LowerRate = 1.f, UpperRate = 1.f;
    for (const TPair<float, float>& Key : RateKeys)
    {
        if (!FMath::IsFinite(Key.Key) || !FMath::IsFinite(Key.Value) || Key.Value <= 0.f) continue;
        if (Key.Key <= 0.f && Key.Key > LowerTime) { LowerTime = Key.Key; LowerRate = Key.Value; }
        if (Key.Key > 0.f && Key.Key < UpperTime) { UpperTime = Key.Key; UpperRate = Key.Value; }
    }
    const float RateAtStart = LowerTime == -FLT_MAX ? (UpperTime == FLT_MAX ? 1.f : UpperRate) : LowerRate;
    const float SourceRate = FMath::Max(0.01f, Definition.PlayRate * RateAtStart);
    const float MontageSeconds = PlayedMontage ? PlayedMontage->GetPlayLength() / SourceRate : 0.f;
    RollRecoveryExpiresAt = GetWorld()->GetTimeSeconds() + MontageSeconds + MHWI::RollRecoveryGraceSeconds;
}

void AMHWICharacter::ClearRollRecovery()
{
    RollRecoveryMove = NAME_None;
    RollRecoveryExpiresAt = -1.f;
    NativeRollRecoverySample = {};
    NativeRollRecoveryNode = INDEX_NONE;
}

bool AMHWICharacter::CanUseRollRecovery() const
{
    return !RollRecoveryMove.IsNone() && !bSheathed && Moveset
        && Moveset->Moves.Contains(RollRecoveryMove) && GetWorld()
        && GetWorld()->GetTimeSeconds() <= RollRecoveryExpiresAt;
}

void AMHWICharacter::BeginAerialSnapshot()
{
    if (bHelmSnapshotValid) return;
    UCharacterMovementComponent* Movement = GetCharacterMovement();
    UAnimInstance* Anim = GetMesh()->GetAnimInstance();
    SavedMovementMode = Movement->MovementMode;
    SavedCustomMovementMode = Movement->CustomMovementMode;
    SavedGravityScale = Movement->GravityScale;
    SavedMaxFlySpeed = Movement->MaxFlySpeed;
    SavedRootMotionMode = ERootMotionMode::RootMotionFromMontagesOnly;
    if (Anim) SavedRootMotionMode = Anim->RootMotionMode;
    SavedOrientRotationToMovement = Movement->bOrientRotationToMovement;
    bHelmSnapshotValid = true;
}

void AMHWICharacter::RestoreAerialSnapshot()
{
    if (!bHelmSnapshotValid) return;
    bHelmSnapshotValid = false;
    UCharacterMovementComponent* Movement = GetCharacterMovement();
    if (!Movement) return;
    if (UAnimInstance* Anim = GetMesh()->GetAnimInstance())
        Anim->SetRootMotionMode(SavedRootMotionMode);
    Movement->GravityScale = SavedGravityScale;
    Movement->MaxFlySpeed = SavedMaxFlySpeed;
    Movement->bOrientRotationToMovement = SavedOrientRotationToMovement;
    if (bEnding) { Movement->SetMovementMode(MOVE_Falling); return; }
    if (SavedMovementMode != MOVE_Walking && SavedMovementMode != MOVE_Falling && SavedMovementMode != MOVE_Flying)
    {
        Movement->SetMovementMode(static_cast<EMovementMode>(SavedMovementMode), SavedCustomMovementMode);
        return;
    }
    FFindFloorResult Floor;
    Movement->FindFloor(GetActorLocation(), Floor, false);
    Movement->SetMovementMode(Floor.IsWalkableFloor() && Floor.FloorDist <= 3.f ? MOVE_Walking : MOVE_Falling);
}

void AMHWICharacter::ResetHelmChain()
{
    if (bHelmSnapshotValid) RestoreAerialSnapshot();
    HelmPhase = EHelmPhase::None;
    bHelmSlamRequested = false;
    HelmSlamExpiresAt = -1.f;
    bHelmSlamAuthorized = false;
    bHelmStrikeCommitted = false;
    bHelmPoseHeld = false;
    bPendingHelmLanded = false;
    PendingHelmLandSerial = 0;
    bHelmLandTransitioning = false;
}

void AMHWICharacter::ApplyHelmAirGravity()
{
    if (!Moveset) return;
    // Parameter is cm/s^2; the engine reference is the default 980 cm/s^2 world
    // gravity. Project tuning, not a verified original-game constant.
    GetCharacterMovement()->GravityScale = FMath::Clamp(
        Moveset->HelmAirGravity / MHWI::ReferenceWorldGravity, 0.05f, 10.f);
}

void AMHWICharacter::ApplyStageMovement(FName MoveId, const FMHWIMoveDefinition& Definition)
{
    UCharacterMovementComponent* Movement = GetCharacterMovement();
    UAnimInstance* Anim = GetMesh()->GetAnimInstance();
    if (MoveId == MHWI::HelmLand)
    {
        // Restore before any snapshot capture attempt: Land is the exit of the
        // chain and must return the saved root motion/gravity/movement exactly.
        HelmPhase = EHelmPhase::Land;
        bHelmPoseHeld = false;
        bHelmSlamRequested = false;
        HelmSlamExpiresAt = -1.f;
        // Authorization is intentionally kept for this Land action only.
        RestoreAerialSnapshot();
        return;
    }
    if (MHWI::IsHelmStageMove(MoveId) || Definition.bUseFullRootMotion) BeginAerialSnapshot();

    if (MoveId == MHWI::HelmRise)
    {
        HelmPhase = EHelmPhase::Rise;
        bHelmPoseHeld = false;
        bHelmStrikeCommitted = false;
        bHelmSlamRequested = false;
        HelmSlamExpiresAt = -1.f;
        if (Anim) Anim->SetRootMotionMode(ERootMotionMode::RootMotionFromMontagesOnly);
        // 171 keeps its authored vertical root motion; it is the only stage that does.
        Movement->SetMovementMode(MOVE_Flying);
        return;
    }
    if (MoveId == MHWI::HelmAir)
    {
        HelmPhase = EHelmPhase::Air;
        bHelmPoseHeld = false;
        bHelmStrikeCommitted = false;
        if (Anim) Anim->SetRootMotionMode(ERootMotionMode::IgnoreRootMotion);
        ApplyHelmAirGravity();
        Movement->SetMovementMode(MOVE_Falling);
        if (!Moveset) return;
        // A slam pressed in the Rise tail survives only within its 0.3 s buffer.
        if (bHelmSlamRequested && HelmSlamExpiresAt >= 0.f
            && GetWorld()->GetTimeSeconds() > HelmSlamExpiresAt)
        {
            bHelmSlamRequested = false;
        }
        if (bHelmSlamRequested) HelmSlamExpiresAt = -1.f;
        // 172 has zero root motion; physics owns displacement and the animation
        // is pose-only, so the handoff velocity is not overwritten by the clip.
        Movement->Velocity = GetActorForwardVector() * Moveset->HelmAirForwardSpeed
            + FVector(0.f, 0.f, Moveset->HelmAirVerticalSpeed);
        return;
    }
    if (MoveId == MHWI::HelmStrike)
    {
        HelmPhase = EHelmPhase::Strike;
        bHelmPoseHeld = false;
        bHelmStrikeCommitted = false;
        // Entering Strike is not authorization; the descent commit below grants it.
        bHelmSlamAuthorized = false;
        if (Anim) Anim->SetRootMotionMode(ERootMotionMode::IgnoreRootMotion);
        ApplyHelmAirGravity();
        if (!Movement->IsMovingOnGround()) Movement->SetMovementMode(MOVE_Falling);
        // Keep the handed-over air velocity during the strike wind-up. The fast
        // descent is applied once at HelmStrikeStartTime by MaybeStartHelmDescent.
        return;
    }
    if (Definition.bUseFullRootMotion)
    {
        if (Anim) Anim->SetRootMotionMode(ERootMotionMode::RootMotionFromMontagesOnly);
        Movement->SetMovementMode(MOVE_Flying);
    }
}

bool AMHWICharacter::CanStartHelmStage(FName MoveId) const
{
    if (MoveId == MHWI::HelmRise)
        return CurrentMove == MHWI::SpiritThrust && bHitConfirmed && SpiritLevel >= 1;
    if (MoveId == MHWI::HelmAir)
        return CurrentMove == MHWI::HelmRise;
    if (MoveId == MHWI::HelmStrike)
        return CurrentMove == MHWI::HelmAir && bHelmSlamRequested;
    if (MoveId == MHWI::HelmLand)
        return (CurrentMove == MHWI::HelmAir || CurrentMove == MHWI::HelmStrike)
            && (bPendingHelmLanded || bHelmLandTransitioning);
    return true;
}

void AMHWICharacter::MaybeCommitHelmStrike()
{
    if (!Moveset || HelmPhase != EHelmPhase::Air || !bHelmSlamRequested || bHelmLandTransitioning) return;
    if (HelmSlamExpiresAt >= 0.f && GetWorld()->GetTimeSeconds() > HelmSlamExpiresAt)
    {
        bHelmSlamRequested = false;
        return;
    }
    // A valid Air attack request enters the Strike animation immediately; the
    // descent commit inside the Strike clip is the only thing that authorizes
    // HelmLand damage or colour loss.
    if (StartResolvedMove(MHWI::HelmStrike))
    {
        bHelmSlamRequested = false;
        return;
    }
    bHelmSlamRequested = false;
    // If the strike cannot start, actual landing still resolves Air -> Land with
    // no damage authorization rather than trapping the character.
}

void AMHWICharacter::MaybeStartHelmDescent()
{
    if (!Moveset || HelmPhase != EHelmPhase::Strike || bHelmStrikeCommitted || bHelmLandTransitioning) return;
    if (CurrentPosition + KINDA_SMALL_NUMBER < FMath::Max(0.f, Moveset->HelmStrikeStartTime)) return;
    // One-shot commit at the Strike clip's descent point (never at 0 s, never
    // from montage length). The horizontal momentum is left untouched. This is
    // also the only point that authorizes the HelmLand seven-hit/colour loss.
    bHelmStrikeCommitted = true;
    bHelmSlamAuthorized = true;
    const float RegenDuration = CapturedSpiritLevel == 3 && ActiveDefinition.RedGaugeRegenOnCommitSeconds >= 0.f
        ? ActiveDefinition.RedGaugeRegenOnCommitSeconds : ActiveDefinition.GaugeRegenOnCommitSeconds;
    GaugeRegenSeconds = FMath::Max(GaugeRegenSeconds, RegenDuration);
    UCharacterMovementComponent* Movement = GetCharacterMovement();
    if (!Movement->IsMovingOnGround()) Movement->SetMovementMode(MOVE_Falling);
    Movement->Velocity.Z = -Moveset->HelmStrikeSpeed;
}

void AMHWICharacter::HandleHelmLanding()
{
    UCharacterMovementComponent* Movement = GetCharacterMovement();
    const bool bGrounded = Movement->IsMovingOnGround();
    if (!bPendingHelmLanded && !bGrounded) return;
    const uint32 LandedSerial = PendingHelmLandSerial;
    bPendingHelmLanded = false;
    // A pending callback from an older execution is stale unless the character
    // is physically grounded right now (e.g. a stage started while already down).
    if (!bGrounded && LandedSerial != ExecutionSerial) return;
    if (bHelmLandTransitioning) return;
    if (HelmPhase != EHelmPhase::Air && HelmPhase != EHelmPhase::Strike) return;
    bHelmLandTransitioning = true;
    const bool bStartedLand = StartResolvedMove(MHWI::HelmLand);
    bHelmLandTransitioning = false;
    if (!bStartedLand) FinishMove(true, true);
}

void AMHWICharacter::Landed(const FHitResult& Hit)
{
    Super::Landed(Hit);
    if (bEnding || !Attributes || !Attributes->IsAlive()) return;
    // Only record the physical fact here; Tick switches stages at a safe point
    // with the execution serial so reentrant callbacks cannot double-commit.
    if (HelmPhase == EHelmPhase::Air || HelmPhase == EHelmPhase::Strike)
    {
        bPendingHelmLanded = true;
        PendingHelmLandSerial = ExecutionSerial;
    }
}

void AMHWICharacter::InterruptMove()
{
    CounterArmorRemaining = 0.f;
    if (bDispatchingHits) { bPendingInterruption = true; return; }
    FinishMove(true, true);
}

bool AMHWICharacter::HandleIncomingDamage(float DamageAmount, AActor* DamageInstigator)
{
    if (bEnding || !Attributes->IsAlive() || DamageAmount <= 0.f || !ActiveMontage) return false;
    if (bNativeConnector) return false; // Main-action defense windows have not started.
    if (MHWI::IsRollMove(CurrentMove))
    {
        // PLP protection is a floating-point actor-frame countdown assigned at
        // action entry, not the legacy montage-second interval.
        return ActiveDefinition.bInvulnerable && RollProtectionFramesRemaining > 0.f;
    }
    UAnimInstance* Anim = GetMesh()->GetAnimInstance();
    FAnimMontageInstance* Instance = Anim ? Anim->GetMontageInstanceForID(ActiveMontageInstanceId) : nullptr;
    const float Position = Instance ? Instance->GetPosition() : CurrentPosition;
    const bool bIndependent = ActiveDefinition.bIndependentDefenseWindows;
    const bool bCounterWindow = bIndependent
        ? MHWI::InHalfOpenWindow(Position, ActiveDefinition.CounterStart, ActiveDefinition.CounterEnd)
        : Position >= ActiveDefinition.CounterStart && Position <= ActiveDefinition.CounterEnd;
    const bool bGaugeEligible = CapturedSpiritGauge >= ActiveDefinition.CounterMinimumGauge;
    if (ActiveDefinition.bCounter && bGaugeEligible && bCounterWindow)
    {
        if (!bCounterConfirmed)
            CounterArmorRemaining = FMath::Max(CounterArmorRemaining, ActiveDefinition.CounterHyperArmorSeconds);
        bCounterConfirmed = true;
        if (!ActiveDefinition.bCounterOnlyForIai && !ActiveDefinition.bCounterRestoresGaugeOnHit) SetSpiritGauge(100.f);
        OnStateChanged.Broadcast();
        return true;
    }
    if (!bIndependent) return ActiveDefinition.bInvulnerable && bCounterWindow;
    float End = CapturedSpiritLevel > 0 && ActiveDefinition.EmpoweredInvulnerabilityEnd >= 0.f
        ? ActiveDefinition.EmpoweredInvulnerabilityEnd : ActiveDefinition.InvulnerabilityEnd;
    if (!bGaugeEligible && ActiveDefinition.LowGaugeInvulnerabilityEnd >= 0.f)
        End = ActiveDefinition.LowGaugeInvulnerabilityEnd;
    return ActiveDefinition.bInvulnerable && MHWI::InHalfOpenWindow(Position, ActiveDefinition.InvulnerabilityStart, End);
}

bool AMHWICharacter::InterceptIncomingDamage_Implementation(float DamageAmount, AActor* DamageInstigator)
{
    return HandleIncomingDamage(DamageAmount, DamageInstigator);
}

bool AMHWICharacter::AdjustIncomingDamage_Implementation(float DamageAmount, AActor* DamageInstigator, float& AdjustedDamage)
{
    AdjustedDamage = DamageAmount;
    if (bEnding || !Attributes || !Attributes->IsAlive() || CounterArmorRemaining <= 0.f || !Moveset) return false;
    AdjustedDamage = DamageAmount * FMath::Clamp(Moveset->CounterArmorDamageMultiplier, 0.f, 1.f);
    return true;
}

float AMHWICharacter::TakeDamage(float DamageAmount, const FDamageEvent& DamageEvent, AController* EventInstigator, AActor* DamageCauser)
{
    if (!Attributes || !Attributes->IsAlive() || DamageAmount <= 0.f) return 0.f;
    const float PreviousHealth = Attributes->GetCurrentHealth();
    Attributes->ApplyDamage(DamageAmount, DamageCauser);
    return FMath::Max(0.f, PreviousHealth - Attributes->GetCurrentHealth());
}

void AMHWICharacter::HandleDamaged(float DamageAmount, AActor* DamageInstigator)
{
    if (DamageAmount <= 0.f || bEnding) return;
    if (CounterArmorRemaining > 0.f) return; // Super armor reduces damage without suppressing HP loss.
    // Damage reaching this delegate was not intercepted. A sender can provide
    // explicit reaction size; an untyped legacy hit uses the small training adapter.
    const EMHWIImpactSize Size = IsValid(DamageInstigator) && DamageInstigator->GetClass()->ImplementsInterface(UMHWIContactResponse::StaticClass())
        ? IMHWIContactResponse::Execute_GetMHWIImpactSize(DamageInstigator) : EMHWIImpactSize::Small;
    StartNativeImpact(Size);
}

void AMHWICharacter::HandleDeath()
{
    CounterArmorRemaining = GaugeRegenSeconds = SpiritDecayPauseRemaining = 0.f;
    RollProtectionFramesRemaining = 0.f;
    ClearDelayedShells();
    PendingHitLag = 0.f;
    ControlState = EMHWIControlState::Dead;
    if (bDispatchingHits) { bPendingDeath = true; return; }
    FinishMove(true, true);
    GetCharacterMovement()->StopMovementImmediately();
    GetCharacterMovement()->DisableMovement();
    SetActorEnableCollision(false);
    if (!bEnding) OnStateChanged.Broadcast();
}

void AMHWICharacter::ResetSpiritGaugeDecayClock()
{
    SpiritGaugeDecayCountdown = Moveset ? FMath::Max(0.f, Moveset->SpiritGaugeDecayFraction) : 0.05f;
}

void AMHWICharacter::SetSpiritGauge(float NewValue)
{
    SpiritGauge = FMath::Clamp(FMath::IsFinite(NewValue) ? NewValue : 0.f, 0.f, 100.f);
    ResetSpiritGaugeDecayClock();
}

float AMHWICharacter::SelectEvasionProtectionFrames() const
{
    if (!Moveset) return 13.f;
    if (bEvasionMantleActive) return FMath::Max(0.f, Moveset->EvasionMantleProtectionFrames);
    const int32 Level = FMath::Clamp(EvadeWindowLevel, 0, 5);
    return Moveset->EvasionProtectionFrames.IsValidIndex(Level)
        ? FMath::Max(0.f, Moveset->EvasionProtectionFrames[Level]) : 13.f;
}

void AMHWICharacter::CommitRoundslash()
{
    if (CurrentMove != MHWI::SpiritRoundslash)
    {
        bRoundslashHitLatched = false;
        return;
    }
    if (!bRoundslashHitLatched) return;
    bRoundslashHitLatched = false;
    // Destruction/death cleanup is not asserted to be the native Action69 exit.
    if (bEnding || ControlState == EMHWIControlState::Dead || !Attributes->IsAlive()) return;
    bRaisedLevelThisAction = true;
    SetSpiritLevel(SpiritLevel + 1, true);
    // The native commit writes Q directly; it does not route through gauge_change.
    SpiritGauge = 0.f;
}

void AMHWICharacter::ScheduleHelmShell(AActor* Target, const FVector& ContactLocation)
{
    if (!IsValid(Target) || !Moveset || CapturedSpiritLevel <= 0) return;
    if (HelmDelayedHits.IsEmpty()) HelmShellScheduledCount = 0;
    const int32 Limit = FMath::Max(0, Moveset->HelmShellHitLimit);
    if (HelmShellScheduledCount >= Limit
        || !Moveset->HelmShellDamageByLevel.IsValidIndex(CapturedSpiritLevel)) return;
    const float MotionValue = Moveset->HelmShellDamageByLevel[CapturedSpiritLevel];
    if (MotionValue <= 0.f) return;
    const int32 FirstHitIndex = HelmShellScheduledCount;
    const FVector RelativeContact = Target->GetActorTransform().InverseTransformPosition(ContactLocation);
    const float FirstDelay = FMath::Max(0.f, Moveset->HelmShellFirstDelay);
    const float Interval = FMath::Max(0.f, Moveset->HelmShellInterval);

    // One confirmed aerial contact owns the full delayed sequence. Snapshot every
    // segment now so a low frame rate cannot lose later hits when the contact
    // window has already passed; TickDelayedShells drains every due entry.
    for (int32 HitIndex = FirstHitIndex; HitIndex < Limit; ++HitIndex)
    {
        FMHWIDelayedHitRuntime Hit;
        Hit.Target = Target;
        Hit.RelativeContact = RelativeContact;
        Hit.RemainingSeconds = FirstDelay + (HitIndex - FirstHitIndex) * Interval;
        Hit.MotionValue = MotionValue;
        Hit.DamageMultiplier = CapturedDamageMultiplier;
        Hit.HitIndex = HitIndex;
        HelmDelayedHits.Add(MoveTemp(Hit));
        ++HelmShellScheduledCount;
    }
}

void AMHWICharacter::ScheduleIaiShell(AActor* Target, const FVector& ContactLocation)
{
    if (!IsValid(Target) || !Moveset || IaiDelayedHit.IsSet() || CapturedSpiritLevel <= 0
        || !Moveset->IaiShellDamageByLevel.IsValidIndex(CapturedSpiritLevel)) return;
    const float MotionValue = Moveset->IaiShellDamageByLevel[CapturedSpiritLevel];
    if (MotionValue <= 0.f) return;
    FMHWIDelayedHitRuntime Hit;
    Hit.Target = Target;
    Hit.RelativeContact = Target->GetActorTransform().InverseTransformPosition(ContactLocation);
    Hit.RemainingSeconds = FMath::Max(0.f, Moveset->IaiShellDelay);
    Hit.MotionValue = MotionValue;
    Hit.DamageMultiplier = CapturedDamageMultiplier;
    Hit.HitIndex = 0;
    IaiDelayedHit = MoveTemp(Hit);
}

void AMHWICharacter::TickDelayedShells(float DeltaSeconds)
{
    const float Advance = FMath::Max(0.f, DeltaSeconds);
    for (FMHWIDelayedHitRuntime& Hit : HelmDelayedHits) Hit.RemainingSeconds -= Advance;
    while (!HelmDelayedHits.IsEmpty() && HelmDelayedHits[0].RemainingSeconds <= 0.f)
    {
        const FMHWIDelayedHitRuntime Hit = HelmDelayedHits[0];
        HelmDelayedHits.RemoveAt(0, 1, EAllowShrinking::No);
        EmitDelayedShell(Hit, MHWI::HelmStrike);
        if (bEnding || !Attributes->IsAlive()) return;
    }
    if (!IaiDelayedHit.IsSet()) return;
    IaiDelayedHit->RemainingSeconds -= Advance;
    if (IaiDelayedHit->RemainingSeconds > 0.f) return;
    const FMHWIDelayedHitRuntime Hit = IaiDelayedHit.GetValue();
    IaiDelayedHit.Reset();
    // Action102 alone owns this pending second hit; its exit clears it.
    if (CurrentMove == MHWI::IaiSpiritSlash) EmitDelayedShell(Hit, MHWI::IaiSpiritSlash);
}

void AMHWICharacter::EmitDelayedShell(const FMHWIDelayedHitRuntime& Hit, FName SourceMove)
{
    AActor* Target = Hit.Target.Get();
    if (!IsValid(Target) || bEnding || !Attributes->IsAlive()) return;
    UAttributeComponent* TargetAttributes = Target->FindComponentByClass<UAttributeComponent>();
    if (!TargetAttributes || !TargetAttributes->IsAlive()) return;
    const FVector ContactLocation = Target->GetActorTransform().TransformPosition(Hit.RelativeContact);
    const float FinalDamage = FMath::Max(0.f, Hit.MotionValue) * FMath::Max(0.f, Hit.DamageMultiplier);
    LastResolvedHit = FMHWIResolvedHit();
    LastResolvedHit.MoveId = SourceMove;
    LastResolvedHit.MotionValueBase = Hit.MotionValue;
    LastResolvedHit.ColorMultiplier = Hit.DamageMultiplier;
    LastResolvedHit.FinalDamage = FinalDamage;
    LastResolvedHit.bDelayedShell = true;
    LastResolvedHit.ShellHitIndex = Hit.HitIndex;
    LastResolvedHit.ContactLocation = ContactLocation;
    const float HealthBefore = TargetAttributes->GetCurrentHealth();
    TargetAttributes->ApplyDamage(FinalDamage, this);
    if (bEnding || !Attributes->IsAlive() || !IsValid(TargetAttributes)
        || TargetAttributes->GetCurrentHealth() >= HealthBefore) return;
    // No montage source time or melee COL record is invented for a delayed shell.
    OnHitResolved.Broadcast(-1.f, INDEX_NONE, INDEX_NONE);
    OnStateChanged.Broadcast();
}

void AMHWICharacter::ClearDelayedShells()
{
    HelmDelayedHits.Reset();
    HelmShellScheduledCount = 0;
    IaiDelayedHit.Reset();
}

void AMHWICharacter::SetSpiritLevel(int32 NewLevel, bool bPauseDecay)
{
    SpiritLevel = FMath::Clamp(NewLevel, 0, 3);
    SpiritTimeRemaining = Moveset && Moveset->SpiritLevelDurations.IsValidIndex(SpiritLevel)
        ? FMath::Max(0.f, Moveset->SpiritLevelDurations[SpiritLevel]) : (SpiritLevel > 0 ? 60.f : 0.f);
    SpiritDecayPauseRemaining = bPauseDecay && SpiritLevel > 0 && Moveset
        ? FMath::Max(0.f, Moveset->SpiritDecayPauseOnRaiseSeconds) : 0.f;
}

FText AMHWICharacter::GetMoveDisplayName() const
{
    if (CurrentMove.IsNone() && !NativeSourceMove.IsNone()) return FText::FromName(NativeSourceMove);
    return ActiveDefinition.DisplayName.IsEmpty() ? FText::FromName(CurrentMove) : ActiveDefinition.DisplayName;
}

FString AMHWICharacter::GetMoveStatus() const
{
    if (!Attributes || !Attributes->IsAlive()) return TEXT("Defeated");
    if (bSpecialSheathHeld) return TEXT("Special sheath: LMB / R");
    if (CurrentMove.IsNone() && !NativeSourceMove.IsNone()) return NativeSourceMove.ToString();
    if (CurrentMove.IsNone()) return bSheathed ? TEXT("Sheathed") : TEXT("Ready");
    if (bCounterConfirmed) return TEXT("Counter successful");
    for (uint8 Index = 0; Index <= static_cast<uint8>(EMHWIInput::SlingerBurst); ++Index)
    {
        FName Next;
        float Start = 0.f, End = 0.f;
        if (ResolveInput(static_cast<EMHWIInput>(Index), Next, &Start, &End)
            && CurrentPosition >= Start && CurrentPosition <= End) return TEXT("Chain / cancel window");
    }
    return bHitConfirmed ? TEXT("Hit confirmed") : TEXT("Executing");
}

void AMHWICharacter::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    bEnding = true;
    CounterArmorRemaining = GaugeRegenSeconds = SpiritDecayPauseRemaining = 0.f;
    RollProtectionFramesRemaining = 0.f;
    ClearDelayedShells();
    ++ExecutionSerial;
    if (Attributes)
    {
        Attributes->OnCharacterDeath.RemoveDynamic(this, &AMHWICharacter::HandleDeath);
        Attributes->OnDamaged.RemoveDynamic(this, &AMHWICharacter::HandleDamaged);
    }
    if (InstalledInputSubsystem.IsValid() && RuntimeMapping) InstalledInputSubsystem->RemoveMappingContext(RuntimeMapping);
    InstalledInputSubsystem.Reset();
    FinishMove(true, true);
    Super::EndPlay(EndPlayReason);
}
