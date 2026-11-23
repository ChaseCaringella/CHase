SPLIT = {
    "Push A": [
        "Incline Barbell or DB Press",
        "Machine Seated Press",
        "Dumbbell or Machine Lateral Raises",
        "30° Incline Dumbbell Fly",
        "Tricep Cable Pushdown",
        "Overhead Tricep Extension",
    ],
    "Pull A": [
        "Close-Grip Lat Pulldown / Pull-ups",
        "Chest-Supported Row",
        "Single-Arm Iliac Cable Pulldown",
        "Reverse Cable Flys",
        "EZ-Bar or Cable Curl",
        "Cable Reverse Curl",
    ],
    "Leg A": [
        "Seated Leg Curl",
        "Smith Machine or Hack Squat",
        "Barbell Romanian Deadlift (RDL)",
        "Leg Extension",
        "Standing or Leg Press Calf Raise",
        "Kneeling Cable Crunch",
    ],
    "Push B": [
        "Cable Lateral Raises",
        "Incline Barbell / DB Bench Press",
        "Seated Overhead DB Press",
        "Low-to-High Cable Fly",
        "EZ-Bar Skull Crushers",
        "Tricep Dips or Single-Arm Pushdown",
    ],
    "Pull B": [
        "Wide-Grip Lat Pulldown",
        "Single-Arm Neutral Cable Row",
        "Chest-Supported T-Bar / Incline Row",
        "Face Pulls (Rope)",
        "Incline DB Curl",
        "Hammer Curls",
    ],
    "Leg B": [
        "Seated Leg Curl",
        "Bulgarian Split Squat",
        "45° Weighted Back Extension",
        "Single-Leg Leg Extension",
        "Standing Calf Raise",
        "Hanging Leg Raises",
    ],
}


def calculate_set_metrics(weight: float, reps: int) -> tuple[float, float]:
    if weight <= 0 or reps < 1:
        raise ValueError("Weight and reps must be greater than zero.")

    volume = weight * reps
    estimated_1rm = weight * (1 + reps / 30.0) if reps > 1 else weight
    return round(volume, 2), round(estimated_1rm, 2)
