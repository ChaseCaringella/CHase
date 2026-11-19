ENERGY_BANDS = (
    (90, 100, "Peak", "Very high energy; focus may feel especially clear."),
    (70, 89, "High", "Alert and productive; demanding tasks may feel manageable."),
    (50, 69, "Moderate", "Steady energy; routine tasks may feel manageable."),
    (30, 49, "Low", "Focus or decisions may take more effort."),
    (10, 29, "Very low", "You may feel depleted; consider a restorative break."),
    (1, 9, "Extremely low", "You may feel very depleted; consider rest or support."),
)


def describe_energy_level(level: int) -> tuple[str, str]:
    if not 1 <= level <= 100:
        raise ValueError("Energy level must be between 1 and 100.")

    for lower, upper, label, description in ENERGY_BANDS:
        if lower <= level <= upper:
            return f"{label} ({lower}-{upper})", description

    raise ValueError("Energy level must be between 1 and 100.")
