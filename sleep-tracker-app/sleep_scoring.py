def calculate_sleep_score(
    time_in_bed_mins: int,
    sleep_latency_mins: int,
    awake_after_sleep_mins: int,
    restfulness: int,
) -> tuple[int, dict[str, int]]:
    if time_in_bed_mins <= 0:
        raise ValueError("Time in bed must be greater than zero.")
    if sleep_latency_mins < 0 or awake_after_sleep_mins < 0:
        raise ValueError("Sleep and awake minutes cannot be negative.")
    if sleep_latency_mins + awake_after_sleep_mins > time_in_bed_mins:
        raise ValueError("Awake time cannot exceed time in bed.")
    if not 1 <= restfulness <= 10:
        raise ValueError("Restfulness must be between 1 and 10.")

    sleep_mins = (
        time_in_bed_mins - sleep_latency_mins - awake_after_sleep_mins
    )
    efficiency = sleep_mins / time_in_bed_mins

    duration_points = 35 * min(sleep_mins / (7 * 60), 1)
    efficiency_points = 30 * min(
        max((efficiency - 0.60) / (0.85 - 0.60), 0), 1
    )
    latency_points = (
        15
        if sleep_latency_mins <= 20
        else 15 * max((60 - sleep_latency_mins) / 40, 0)
    )
    restfulness_points = 20 * (restfulness - 1) / 9

    breakdown = {
        "Duration": round(duration_points),
        "Sleep efficiency": round(efficiency_points),
        "Time to fall asleep": round(latency_points),
        "Restfulness": round(restfulness_points),
    }
    return sum(breakdown.values()), breakdown


def get_sleep_coaching_tip(
    score: int, breakdown: dict[str, int]
) -> str:
    if score == 100:
        return (
            "Great night by this diary's measures. Keep tracking; one night "
            "doesn't define your usual sleep."
        )

    lowest_component = min(breakdown, key=breakdown.get)
    tips = {
        "Duration": (
            "If your schedule allows, make a little more room for sleep. "
            "Adults generally need at least 7 hours."
        ),
        "Sleep efficiency": (
            "You spent a notable share of your time in bed awake. Keep "
            "tracking for a pattern; if it persists or affects your day, "
            "consider discussing it with a healthcare professional."
        ),
        "Time to fall asleep": (
            "Try a consistent wind-down routine and compare your time to "
            "fall asleep across several nights."
        ),
        "Restfulness": (
            "You felt less rested than hoped. Track this alongside your "
            "schedule and stress; seek professional advice if it persists."
        ),
    }
    return tips[lowest_component]
