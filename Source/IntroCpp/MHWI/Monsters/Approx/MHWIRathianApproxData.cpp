#include "MHWIRathianApproxData.h"

UMHWIRathianApproxMovesetData::UMHWIRathianApproxMovesetData()
{
    FMHWIRathianApproxMove Bite;
    Bite.RegistryName = TEXT("ACTION::BITE");
    Bite.Kind = EMHWIRathianApproxMoveKind::Attack;
    Bite.AnimQualification = EMHWIRathianApproxQualification::Evidenced;
    Bite.Animation = TSoftObjectPtr<UAnimSequence>(FSoftObjectPath(TEXT("/Game/MHWI/Rathalos/Animations/A_em001_02_001.A_em001_02_001")));
    Bite.AttackWindowStartSeconds = 0.f;
    Bite.AttackWindowEndSeconds = 0.3833f;
    Bite.AttackWindowQualification = EMHWIRathianApproxQualification::EngineeringFixture;
    Bite.DamageProxyMotionValue = 30.f;
    Bite.DamageQualification = EMHWIRathianApproxQualification::EvidencedConsumptionApprox;
    Bite.AttackRangeCm = 350.f;
    Bite.PreferredMinDistanceCm = 120.f;
    Bite.PreferredMaxDistanceCm = 360.f;
    Bite.MaxAngleDegrees = 65.f;
    Bite.CooldownSeconds = 1.2f;
    FMHWIRathianAttackPhase BitePhase;
    BitePhase.Kind = EMHWIRathianAttackPhaseKind::Active;
    BitePhase.Animation = Bite.Animation;
    BitePhase.bAttackWindowEnabled = true;
    BitePhase.bUseLegacySecondsWindow = true;
    BitePhase.WindowStartSeconds = Bite.AttackWindowStartSeconds;
    BitePhase.WindowEndSeconds = Bite.AttackWindowEndSeconds;
    BitePhase.WindowQualification = EMHWIRathianApproxQualification::EngineeringFixture;
    BitePhase.Damage = Bite.DamageProxyMotionValue;
    BitePhase.ImpactSize = EMHWIImpactSize::Small;
    FMHWIRathianAttackBox BiteBox;
    BiteBox.BoneName = TEXT("bone_head"); // Approximation fixture; confirm against imported skeleton before asset acceptance.
    BiteBox.LocalOffsetCm = FVector(35.f, 0.f, 0.f);
    BiteBox.HalfExtentCm = FVector(85.f, 55.f, 60.f);
    BitePhase.HitBoxes.Add(BiteBox);
    Bite.Phases.Add(BitePhase);
    Moves.Add(Bite);

    auto AddPhase = [](FMHWIRathianApproxMove& Move, EMHWIRathianAttackPhaseKind Kind, bool bAddBox)
    {
        FMHWIRathianAttackPhase Phase;
        Phase.Kind = Kind;
        Phase.WindowQualification = EMHWIRathianApproxQualification::EngineeringFixture;
        Phase.MovementQualification = EMHWIRathianApproxQualification::EngineeringFixture;
        Phase.FlightQualification = EMHWIRathianApproxQualification::EngineeringFixture;
        if (bAddBox)
        {
            FMHWIRathianAttackBox Box;
            Box.BoneName = NAME_None; // Asset-stage selection required.
            Box.Qualification = EMHWIRathianApproxQualification::EngineeringFixture;
            Phase.HitBoxes.Add(Box);
        }
        Move.Phases.Add(Phase);
    };
    auto AddUnavailable = [this, &AddPhase](const TCHAR* Name, float Min, float Max, float Angle, float Cooldown)
    {
        FMHWIRathianApproxMove Move;
        Move.RegistryName = Name;
        Move.Kind = EMHWIRathianApproxMoveKind::Attack;
        Move.AnimQualification = EMHWIRathianApproxQualification::Unavailable;
        Move.AttackWindowQualification = EMHWIRathianApproxQualification::Unavailable;
        Move.DamageQualification = EMHWIRathianApproxQualification::Unavailable;
        Move.PreferredMinDistanceCm = Min;
        Move.PreferredMaxDistanceCm = Max;
        Move.MaxAngleDegrees = Angle;
        Move.CooldownSeconds = Cooldown;
        if (Move.RegistryName == TEXT("ACTION::DASH_BITE2"))
        {
            AddPhase(Move, EMHWIRathianAttackPhaseKind::Windup, false);
            AddPhase(Move, EMHWIRathianAttackPhaseKind::Active, true);
            AddPhase(Move, EMHWIRathianAttackPhaseKind::Recovery, false);
        }
        else if (Move.RegistryName == TEXT("ACTION::FIRE_BREATH"))
        {
            AddPhase(Move, EMHWIRathianAttackPhaseKind::Windup, false);
            AddPhase(Move, EMHWIRathianAttackPhaseKind::Active, false);
            Move.Phases.Last().bSpawnFireballAtStart = true;
            Move.Phases.Last().FireballSocketName = NAME_None;
            AddPhase(Move, EMHWIRathianAttackPhaseKind::Recovery, false);
        }
        else
        {
            AddPhase(Move, EMHWIRathianAttackPhaseKind::TailTakeoff, true);
            AddPhase(Move, EMHWIRathianAttackPhaseKind::Active, true);
            AddPhase(Move, EMHWIRathianAttackPhaseKind::TailLanding, true);
        }
        Moves.Add(Move);
    };
    AddUnavailable(TEXT("ACTION::DASH_BITE2"), 320.f, 850.f, 55.f, 2.5f);
    AddUnavailable(TEXT("ACTION::FIRE_BREATH"), 650.f, 1500.f, 35.f, 4.f);
    AddUnavailable(TEXT("ACTION::ROLLING_TAIL_ATTACK2_L"), 250.f, 900.f, 180.f, 3.5f);
}
