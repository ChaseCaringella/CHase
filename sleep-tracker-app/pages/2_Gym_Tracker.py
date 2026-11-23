import datetime
import hmac

import pandas as pd
import plotly.express as px
import streamlit as st
from postgrest.exceptions import APIError
from streamlit.errors import StreamlitSecretNotFoundError
from supabase import create_client


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


def estimate_1rm(weight, reps):
    """Estimate one-rep max with the Epley formula used by the original logger."""
    return weight * (1 + reps / 30.0) if reps > 1 else weight


st.set_page_config(page_title="Gym Tracker", page_icon="🏋️", layout="wide")
st.title("🏋️ Gym Tracker")
st.caption(
    "Log your workout split, track volume and estimated strength, and download "
    "a CSV backup. Estimates are training metrics, not medical advice."
)

try:
    app_settings = st.secrets.get("app", {})
    supabase_settings = st.secrets.get("supabase", {})
except StreamlitSecretNotFoundError:
    st.error("Set up the app password and Supabase credentials in Streamlit secrets first.")
    st.stop()

if not app_settings.get("password"):
    st.error("Set an app password in Streamlit secrets before using this private tracker.")
    st.stop()
if not supabase_settings.get("url") or not supabase_settings.get("key"):
    st.error("Add the Supabase URL and service-role key to Streamlit secrets first.")
    st.stop()

if not st.session_state.get("authenticated", False):
    with st.form("gym_login_form"):
        entered_password = st.text_input("App password", type="password")
        login_submitted = st.form_submit_button("Log in")
    if login_submitted:
        if hmac.compare_digest(entered_password, app_settings["password"]):
            st.session_state["authenticated"] = True
            st.rerun()
        st.error("Incorrect password.")
    st.stop()

@st.cache_resource
def get_supabase_client():
    return create_client(supabase_settings["url"], supabase_settings["key"])


supabase = get_supabase_client()
log_tab, dashboard_tab = st.tabs(["Log Workout", "Progress & History"])

with log_tab:
    st.subheader("Record a training session")
    workout_day = st.selectbox("Workout", list(SPLIT))
    workout_date = st.date_input("Workout date", datetime.date.today())
    st.caption("Set count 0 skips an exercise. Weight can be entered in lb or kg; stay consistent.")

    entries = []
    for exercise_index, exercise in enumerate(SPLIT[workout_day]):
        with st.expander(exercise, expanded=exercise_index == 0):
            set_count = st.number_input(
                f"Sets completed — {exercise}",
                min_value=0,
                max_value=10,
                value=3,
                step=1,
                key=f"sets_{workout_day}_{exercise}",
            )
            for set_number in range(1, int(set_count) + 1):
                st.markdown(f"**Set {set_number}**")
                weight_col, reps_col, rpe_col = st.columns(3)
                weight = weight_col.number_input(
                    "Weight (lb or kg)", min_value=0.0, value=0.0,
                    step=2.5, key=f"weight_{workout_day}_{exercise}_{set_number}",
                )
                reps = reps_col.number_input(
                    "Reps", min_value=1, max_value=100, value=8,
                    step=1, key=f"reps_{workout_day}_{exercise}_{set_number}",
                )
                rpe = rpe_col.number_input(
                    "RPE (1–10)", min_value=1.0, max_value=10.0, value=8.0,
                    step=0.5, key=f"rpe_{workout_day}_{exercise}_{set_number}",
                )
                entries.append({
                    "log_date": str(workout_date),
                    "day_type": workout_day,
                    "exercise": exercise,
                    "set_number": set_number,
                    "weight": float(weight),
                    "reps": int(reps),
                    "rpe": float(rpe),
                    "volume": round(float(weight) * int(reps), 2),
                    "est_1rm": round(estimate_1rm(float(weight), int(reps)), 2),
                })

    if st.button("Save workout", type="primary", use_container_width=True):
        if not entries:
            st.warning("Enter at least one set before saving.")
        else:
            try:
                supabase.table("workout_logs").insert(entries).execute()
                session_volume = sum(row["volume"] for row in entries)
                st.success(
                    f"Saved {len(entries)} sets for {workout_day}. "
                    f"Total volume: {session_volume:,.1f} (weight units × reps)."
                )
                st.rerun()
            except APIError as exc:
                if exc.code in {"42P01", "PGRST205"}:
                    st.error(
                        "The workout table is not set up yet. Run "
                        "supabase_migration_v4.sql in your Supabase SQL Editor, "
                        "then refresh this page."
                    )
                else:
                    raise

with dashboard_tab:
    try:
        records = (
            supabase.table("workout_logs")
            .select("log_date, day_type, exercise, set_number, weight, reps, rpe, volume, est_1rm")
            .order("log_date")
            .execute()
            .data
        )
    except APIError as exc:
        if exc.code not in {"42P01", "PGRST205"}:
            raise
        records = None
        st.error(
            "The workout table is not set up yet. Run "
            "supabase_migration_v4.sql in your Supabase SQL Editor, then refresh."
        )

    if records:
        df = pd.DataFrame(records).rename(columns={
            "log_date": "Date", "day_type": "Workout", "exercise": "Exercise",
            "set_number": "Set", "weight": "Weight", "reps": "Reps",
            "rpe": "RPE", "volume": "Volume", "est_1rm": "Estimated 1RM",
        })
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values(["Date", "Workout", "Exercise", "Set"])

        metric1, metric2, metric3 = st.columns(3)
        metric1.metric("Logged sets", f"{len(df):,}")
        metric2.metric("Total volume", f"{df['Volume'].sum():,.1f}")
        metric3.metric("Exercises tracked", f"{df['Exercise'].nunique():,}")

        st.subheader("Estimated 1RM progress")
        exercise_options = sorted(df["Exercise"].unique())
        selected_exercise = st.selectbox("Exercise to chart", exercise_options)
        progress = df[df["Exercise"] == selected_exercise].groupby("Date", as_index=False)["Estimated 1RM"].max()
        if len(progress) == 1:
            st.metric(f"Best estimated 1RM — {selected_exercise}", f"{progress['Estimated 1RM'].max():g}")
        else:
            fig = px.line(progress, x="Date", y="Estimated 1RM", markers=True)
            fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=20), yaxis_title="Estimated 1RM (weight units)")
            st.plotly_chart(fig, use_container_width=True)

        personal_records = df.groupby("Exercise", as_index=False)["Estimated 1RM"].max()
        personal_records = personal_records.rename(columns={"Estimated 1RM": "Best Estimated 1RM"})
        st.subheader("Personal records")
        st.dataframe(personal_records.sort_values("Best Estimated 1RM", ascending=False), use_container_width=True, hide_index=True)

        st.download_button(
            "Download workout backup CSV",
            data=df.to_csv(index=False),
            file_name="workout_logs_backup.csv",
            mime="text/csv",
        )
        st.subheader("Recent sets")
        st.dataframe(df.sort_values(["Date", "Set"], ascending=[False, False]).head(50), use_container_width=True, hide_index=True)
    elif records is not None:
        st.info("No workout sets logged yet. Use the Log Workout tab to record your first session.")
