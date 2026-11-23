import datetime
import hmac

import pandas as pd
import plotly.express as px
import streamlit as st
from postgrest.exceptions import APIError
from streamlit.errors import StreamlitSecretNotFoundError
from supabase import create_client

from workout_tracker import SPLIT, calculate_set_metrics


ALL_EXERCISES = sorted(
    {exercise for exercises in SPLIT.values() for exercise in exercises}
)
EXERCISE_CHOICES = ["Use split exercise", "Custom exercise", *ALL_EXERCISES]

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
    st.error(
        "Set up the app password and Supabase credentials in Streamlit secrets first."
    )
    st.stop()

if not app_settings.get("password"):
    st.error(
        "Set an app password in Streamlit secrets before using this private tracker."
    )
    st.stop()
if not supabase_settings.get("url") or not supabase_settings.get("key"):
    st.error(
        "Add the Supabase URL and service-role key to Streamlit secrets first."
    )
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
    weight_unit = st.selectbox("Weight unit", ["lb", "kg"])
    st.caption(
        "Set count 0 skips an exercise. You can replace any split movement with "
        "another listed exercise or enter a custom name."
    )

    entries = []
    missing_custom_exercises = []
    for exercise_index, split_exercise in enumerate(SPLIT[workout_day]):
        with st.expander(split_exercise, expanded=exercise_index == 0):
            replacement = st.selectbox(
                "Exercise",
                EXERCISE_CHOICES,
                key=f"replacement_{workout_day}_{exercise_index}",
            )
            if replacement == "Use split exercise":
                exercise = split_exercise
            elif replacement == "Custom exercise":
                exercise = st.text_input(
                    "Custom exercise name",
                    key=f"custom_exercise_{workout_day}_{exercise_index}",
                ).strip()
            else:
                exercise = replacement

            set_count = st.number_input(
                "Sets completed",
                min_value=0,
                max_value=10,
                value=3,
                step=1,
                key=f"sets_{workout_day}_{exercise_index}",
            )
            if not exercise and set_count:
                missing_custom_exercises.append(split_exercise)
            for set_number in range(1, int(set_count) + 1):
                st.markdown(f"**Set {set_number}**")
                weight_col, reps_col, rpe_col = st.columns(3)
                weight = weight_col.number_input(
                    f"Weight ({weight_unit})",
                    min_value=0.1,
                    value=45.0,
                    step=2.5,
                    key=f"weight_{workout_day}_{exercise_index}_{set_number}",
                )
                reps = reps_col.number_input(
                    "Reps",
                    min_value=1,
                    max_value=100,
                    value=8,
                    step=1,
                    key=f"reps_{workout_day}_{exercise_index}_{set_number}",
                )
                rpe = rpe_col.number_input(
                    "RPE (1-10)",
                    min_value=1.0,
                    max_value=10.0,
                    value=8.0,
                    step=0.5,
                    key=f"rpe_{workout_day}_{exercise_index}_{set_number}",
                )
                volume, estimated_1rm = calculate_set_metrics(
                    float(weight), int(reps)
                )
                entries.append(
                    {
                        "workout_date": str(workout_date),
                        "day_type": workout_day,
                        "exercise": exercise,
                        "set_number": set_number,
                        "weight": round(float(weight), 2),
                        "weight_unit": weight_unit,
                        "reps": int(reps),
                        "rpe": float(rpe),
                        "volume": volume,
                        "est_1rm": estimated_1rm,
                    }
                )

    if st.button("Save workout", type="primary", use_container_width=True):
        if missing_custom_exercises:
            st.error(
                "Enter a name for each custom exercise with completed sets."
            )
        elif not entries:
            st.warning("Enter at least one set before saving.")
        else:
            try:
                supabase.table("gym_logs").insert(entries).execute()
                session_volume = sum(row["volume"] for row in entries)
                st.success(
                    f"Saved {len(entries)} sets for {workout_day}. "
                    f"Total volume: {session_volume:,.1f} "
                    f"{weight_unit} × reps."
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
            supabase.table("gym_logs")
            .select(
                "workout_date, day_type, exercise, set_number, weight, "
                "weight_unit, reps, rpe, volume, est_1rm"
            )
            .order("workout_date")
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
        df = pd.DataFrame(records).rename(
            columns={
                "workout_date": "Date",
                "day_type": "Workout",
                "exercise": "Exercise",
                "set_number": "Set",
                "weight": "Weight",
                "weight_unit": "Unit",
                "reps": "Reps",
                "rpe": "RPE",
                "volume": "Volume",
                "est_1rm": "Estimated 1RM",
            }
        )
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values(["Date", "Workout", "Exercise", "Set"])

        metric_columns = st.columns(4)
        metric_columns[0].metric("Logged sets", f"{len(df):,}")
        metric_columns[1].metric(
            "Exercises tracked", f"{df['Exercise'].nunique():,}"
        )
        for column, unit in zip(metric_columns[2:], ["lb", "kg"]):
            unit_volume = df.loc[df["Unit"] == unit, "Volume"].sum()
            column.metric(f"Volume ({unit} × reps)", f"{unit_volume:,.1f}")

        st.subheader("Estimated 1RM progress")
        exercise_options = sorted(df["Exercise"].unique())
        selected_exercise = st.selectbox(
            "Exercise to chart", exercise_options
        )
        exercise_logs = df[df["Exercise"] == selected_exercise]
        units_for_exercise = sorted(exercise_logs["Unit"].unique())
        selected_unit = st.selectbox("Weight unit", units_for_exercise)
        progress = (
            exercise_logs[exercise_logs["Unit"] == selected_unit]
            .groupby("Date", as_index=False)["Estimated 1RM"]
            .max()
        )
        if len(progress) == 1:
            st.metric(
                f"Best estimated 1RM — {selected_exercise}",
                f"{progress['Estimated 1RM'].max():g} {selected_unit}",
            )
        else:
            fig = px.line(progress, x="Date", y="Estimated 1RM", markers=True)
            fig.update_layout(
                height=320,
                margin=dict(l=10, r=10, t=20, b=20),
                yaxis_title=f"Estimated 1RM ({selected_unit})",
            )
            st.plotly_chart(fig, use_container_width=True)

        personal_records = (
            df.groupby(["Exercise", "Unit"], as_index=False)["Estimated 1RM"]
            .max()
            .rename(columns={"Estimated 1RM": "Best Estimated 1RM"})
            .sort_values("Best Estimated 1RM", ascending=False)
        )
        st.subheader("Personal records")
        st.dataframe(
            personal_records,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download workout backup CSV",
            data=df.to_csv(index=False),
            file_name="workout_logs_backup.csv",
            mime="text/csv",
        )
        st.subheader("Recent sets")
        st.dataframe(
            df.sort_values(
                ["Date", "Set"], ascending=[False, False]
            ).head(50),
            use_container_width=True,
            hide_index=True,
        )
    elif records is not None:
        st.info(
            "No workout sets logged yet. Use the Log Workout tab to record "
            "your first session."
        )
