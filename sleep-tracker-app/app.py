import datetime
import hmac
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from postgrest.exceptions import APIError
from streamlit.errors import StreamlitSecretNotFoundError
from supabase import create_client

from energy_scale import ENERGY_BANDS, describe_energy_level
from sleep_scoring import calculate_sleep_score, get_sleep_coaching_tip


ENERGY_DISPLAY_TIMEZONE = ZoneInfo("America/Los_Angeles")

st.set_page_config(page_title="Sleep Coach", page_icon="🌙", layout="centered")
st.title("🌙 Personal Sleep Coach")

column_names = {
    "log_date": "Date",
    "bedtime": "Bedtime",
    "wake_time": "Wake Time",
    "latency_mins": "Latency (mins)",
    "night_awakenings": "Night Awakenings",
    "wake_after_sleep_mins": "Awake After Falling Asleep (mins)",
    "sleep_quality": "Restfulness (1-10)",
    "caffeine_consumed": "Had Caffeine",
    "caffeine_cutoff": "Last Caffeine Time",
    "screen_time_mins": "Screen Time (mins)",
    "stress": "Stress",
    "morning_mood": "Morning Mood",
    "sleep_score": "Sleep Score",
    "score_version": "Score Version",
}
columns = list(column_names.values())


@st.cache_resource
def get_supabase_client():
    settings = st.secrets["supabase"]
    return create_client(settings["url"], settings["key"])


try:
    app_settings = st.secrets.get("app", {})
    supabase_settings = st.secrets.get("supabase", {})
except StreamlitSecretNotFoundError:
    st.error(
        "Set up Streamlit secrets with your app password and Supabase "
        "credentials before using this app."
    )
    st.stop()

if not app_settings.get("password"):
    st.error(
        "Set an app password in Streamlit secrets before using this private "
        "sleep tracker."
    )
    st.stop()

if not supabase_settings.get("url") or not supabase_settings.get("key"):
    st.error(
        "Online storage is not configured yet. Add your Supabase URL and "
        "secret key to Streamlit secrets."
    )
    st.stop()

if not st.session_state.get("authenticated", False):
    with st.form("login_form"):
        entered_password = st.text_input("App password", type="password")
        login_submitted = st.form_submit_button("Log in")

    if login_submitted:
        if hmac.compare_digest(entered_password, app_settings["password"]):
            st.session_state["authenticated"] = True
            st.rerun()
        st.error("Incorrect password.")
    st.stop()

supabase = get_supabase_client()

tab_log, tab_energy, tab_dashboard = st.tabs(
    ["Log Sleep", "Energy Check-ins", "Dashboard & Trends"]
)

with tab_log:
    st.subheader("Log Last Night's Sleep")
    with st.form("sleep_log_form", clear_on_submit=True):
        log_date = st.date_input(
            "Date you got out of bed", datetime.date.today()
        )
        had_caffeine = st.checkbox(
            "Did you have caffeine before this sleep?"
        )
        caffeine_cutoff = st.time_input(
            "Time of your last caffeinated drink (if any)",
            datetime.time(14, 0),
            format="12h",
            help="This time is saved only if you check that you had caffeine.",
        )

        bedtime = st.time_input(
            "Time you got into bed and tried to sleep",
            datetime.time(22, 30),
            format="12h",
        )
        waketime = st.time_input(
            "Time you got out of bed",
            datetime.time(6, 30),
            format="12h",
        )

        latency = st.number_input(
            "Time to fall asleep (mins)", min_value=0, max_value=180, value=15
        )
        awakenings = st.number_input(
            "Night awakenings (count)", min_value=0, max_value=20, value=0
        )
        awake_after_sleep = st.number_input(
            "Total minutes awake after first falling asleep, including before "
            "getting out of bed",
            min_value=0,
            max_value=600,
            value=0,
        )
        restfulness = st.slider(
            "How rested do you feel? [1-10]", 1, 10, 7
        )
        screen_time = st.number_input(
            "Screen time before bed (mins)", min_value=0, max_value=300, value=30
        )
        stress = st.slider("Evening stress level [1-10]", 1, 10, 3)
        mood = st.slider("Morning mood [1-10]", 1, 10, 7)

        submitted = st.form_submit_button(
            "Save & Calculate Score", use_container_width=True
        )

    st.caption(
        "This is a transparent tracking estimate, not a medical assessment. "
        "Caffeine, screen time, stress, and mood are recorded as context, "
        "not automatic score penalties. The awakening count is logged, while "
        "total awake minutes are used in the score."
    )
    with st.expander("How the score works"):
        st.markdown(
            "- **Sleep duration (35 points):** full points at 7 hours or more.\n"
            "- **Sleep efficiency (30):** time asleep divided by time in bed; "
            "full points at 85%, none below 60%.\n"
            "- **Time to fall asleep (15):** full points at 20 minutes or less; "
            "gradually decreases to zero at 60 minutes.\n"
            "- **Restfulness (20):** your 1-10 rating.\n\n"
            "This is a simple tracking rubric, not a clinically validated "
            "score. It cannot measure sleep stages."
        )

    if submitted:
        b_dt = datetime.datetime.combine(log_date, bedtime)
        w_dt = datetime.datetime.combine(log_date, waketime)
        if w_dt < b_dt:
            w_dt += datetime.timedelta(days=1)

        time_in_bed_mins = int((w_dt - b_dt).total_seconds() // 60)
        if time_in_bed_mins <= 0:
            st.error("Time in bed must be greater than zero.")
        elif latency + awake_after_sleep > time_in_bed_mins:
            st.error(
                "Time to fall asleep plus awake time cannot exceed time in bed."
            )
        else:
            actual_sleep_hrs = (
                time_in_bed_mins - latency - awake_after_sleep
            ) / 60.0
            sleep_score, score_breakdown = calculate_sleep_score(
                time_in_bed_mins=time_in_bed_mins,
                sleep_latency_mins=int(latency),
                awake_after_sleep_mins=int(awake_after_sleep),
                restfulness=int(restfulness),
            )

            new_row = {
                "log_date": str(log_date),
                "bedtime": bedtime.strftime("%H:%M"),
                "wake_time": waketime.strftime("%H:%M"),
                "latency_mins": int(latency),
                "night_awakenings": int(awakenings),
                "wake_after_sleep_mins": int(awake_after_sleep),
                "sleep_quality": int(restfulness),
                "caffeine_consumed": had_caffeine,
                "caffeine_cutoff": (
                    caffeine_cutoff.strftime("%H:%M")
                    if caffeine_cutoff is not None
                    else None
                ),
                "screen_time_mins": int(screen_time),
                "stress": int(stress),
                "morning_mood": int(mood),
                "sleep_score": sleep_score,
                "score_version": 2,
            }
            supabase.table("sleep_logs").insert(new_row).execute()
            st.success(
                f"Logged! Estimated sleep: **{actual_sleep_hrs:.1f} hrs** "
                f"| Sleep Score: **{sleep_score}/100**"
            )
            st.caption(
                "Score breakdown: "
                + " · ".join(
                    f"{name}: {points}"
                    for name, points in score_breakdown.items()
                )
            )
            st.info(
                "Coach's next step: "
                + get_sleep_coaching_tip(sleep_score, score_breakdown)
            )
            st.balloons()

with tab_energy:
    st.subheader("How energized do you feel right now?")
    st.caption(
        "Check in whenever you want. Each entry is a snapshot; there is no "
        "required schedule."
    )

    try:
        energy_records = (
            supabase.table("energy_checkins")
            .select("recorded_at, energy_level")
            .order("recorded_at")
            .execute()
            .data
        )
    except APIError as exc:
        if exc.code not in {"42P01", "PGRST205"}:
            raise
        energy_records = None
        st.error(
            "Energy check-ins need a database update first. Run "
            "supabase_migration_v3.sql in your Supabase SQL Editor, then "
            "refresh this app."
        )

    if energy_records is not None:
        with st.form("energy_checkin_form", clear_on_submit=True):
            energy_level = st.number_input(
                "Mental energy right now (1-100)",
                min_value=1,
                max_value=100,
                value=50,
                step=1,
                help=(
                    "Use your own sense of focus, mental bandwidth, and "
                    "overall energy. There are no right or wrong ratings."
                ),
            )
            energy_submitted = st.form_submit_button(
                "Save energy snapshot", use_container_width=True
            )

        band_label, band_description = describe_energy_level(
            int(energy_level)
        )
        st.info(f"**{band_label}:** {band_description}")

        with st.expander("How to use the 1-100 scale"):
            for lower, upper, label, description in ENERGY_BANDS:
                st.markdown(
                    f"- **{lower}-{upper} — {label}:** {description}"
                )
            st.caption(
                "This is a subjective self-rating, not an objective measure "
                "of cognition or a medical assessment. Look for your own "
                "patterns rather than trying to maximize every score."
            )

        if energy_submitted:
            supabase.table("energy_checkins").insert(
                {"energy_level": int(energy_level)}
            ).execute()
            st.success("Energy snapshot saved.")
            energy_records = (
                supabase.table("energy_checkins")
                .select("recorded_at, energy_level")
                .order("recorded_at")
                .execute()
                .data
            )

        st.subheader("Your energy curve")
        st.caption(
            "Times are shown in Riverside, California time (Pacific), with "
            "daylight-saving changes applied. Hover over a point to see its "
            "exact timestamp and rating."
        )

        if not energy_records:
            st.info("Your curve will appear after your first energy check-in.")
        else:
            energy_df = pd.DataFrame(energy_records)
            energy_df["Recorded at"] = pd.to_datetime(
                energy_df["recorded_at"], utc=True
            )
            energy_df["Local time"] = energy_df["Recorded at"].dt.tz_convert(
                ENERGY_DISPLAY_TIMEZONE
            )
            energy_df = energy_df.sort_values("Recorded at")

            view_range = st.selectbox(
                "Show check-ins from",
                ["Last 24 hours", "Last 7 days", "Last 30 days", "All time"],
                index=1,
            )
            now_utc = pd.Timestamp.now(tz="UTC")
            range_lengths = {
                "Last 24 hours": pd.Timedelta(hours=24),
                "Last 7 days": pd.Timedelta(days=7),
                "Last 30 days": pd.Timedelta(days=30),
            }
            if view_range == "All time":
                filtered_energy = energy_df
            else:
                range_start = now_utc - range_lengths[view_range]
                filtered_energy = energy_df[
                    energy_df["Recorded at"] >= range_start
                ]

            if filtered_energy.empty:
                st.info(f"No energy check-ins in the {view_range.lower()}.")
            else:
                energy_fig = go.Figure()
                day_groups = filtered_energy.groupby(
                    filtered_energy["Local time"].dt.strftime("%Y-%m-%d"),
                    sort=True,
                )
                for day, day_records in day_groups:
                    exact_times = day_records["Local time"].dt.strftime(
                        "%Y-%m-%d %I:%M:%S %p %Z"
                    )
                    energy_fig.add_trace(
                        go.Scatter(
                            x=day_records["Local time"].dt.tz_localize(None),
                            y=day_records["energy_level"],
                            customdata=exact_times,
                            mode="lines+markers",
                            name=day,
                            hovertemplate=(
                                "Time: %{customdata}<br>"
                                "Energy: %{y}/100<extra></extra>"
                            ),
                        )
                    )
                energy_fig.add_hline(
                    y=50,
                    line_dash="dash",
                    line_color="gray",
                    annotation_text="Midpoint",
                )
                energy_fig.update_layout(
                    height=380,
                    margin=dict(l=10, r=10, t=25, b=20),
                    xaxis_title="Local time (Pacific)",
                    yaxis_title="Self-rated energy",
                    yaxis=dict(range=[1, 100], dtick=10),
                    legend_title_text="Date (local)",
                )
                st.plotly_chart(energy_fig, use_container_width=True)

                st.subheader("Compare energy at similar times")
                st.caption(
                    "Each date uses the same 24-hour clock, so check-ins near "
                    "the same time line up across days. Lines connect only "
                    "ratings you entered; unlogged times are not estimated."
                )
                time_of_day_fig = go.Figure()
                time_of_day_groups = filtered_energy.groupby(
                    filtered_energy["Local time"].dt.strftime("%Y-%m-%d"),
                    sort=True,
                )
                for day, day_records in time_of_day_groups:
                    local_times = day_records["Local time"]
                    hour_of_day = (
                        local_times.dt.hour
                        + local_times.dt.minute / 60
                        + local_times.dt.second / 3600
                    )
                    exact_times = local_times.dt.strftime(
                        "%Y-%m-%d %I:%M:%S %p %Z"
                    )
                    time_of_day_fig.add_trace(
                        go.Scatter(
                            x=hour_of_day,
                            y=day_records["energy_level"],
                            customdata=exact_times,
                            mode="lines+markers",
                            name=day,
                            hovertemplate=(
                                "Time: %{customdata}<br>"
                                "Energy: %{y}/100<extra></extra>"
                            ),
                        )
                    )
                time_of_day_fig.add_hline(
                    y=50,
                    line_dash="dash",
                    line_color="gray",
                    annotation_text="Midpoint",
                )
                time_of_day_fig.update_layout(
                    height=380,
                    margin=dict(l=10, r=10, t=25, b=20),
                    xaxis=dict(
                        title="Time of day (Pacific)",
                        range=[0, 24],
                        tickvals=[0, 4, 8, 12, 16, 20, 24],
                        ticktext=[
                            "12 AM",
                            "4 AM",
                            "8 AM",
                            "12 PM",
                            "4 PM",
                            "8 PM",
                            "12 AM",
                        ],
                    ),
                    yaxis=dict(
                        title="Self-rated energy",
                        range=[1, 100],
                        dtick=10,
                    ),
                    legend_title_text="Date (local)",
                )
                st.plotly_chart(time_of_day_fig, use_container_width=True)

            download_df = pd.DataFrame(
                {
                    "Recorded at (local)": energy_df["Local time"].dt.strftime(
                        "%Y-%m-%d %I:%M:%S %p %Z"
                    ),
                    "Recorded at (UTC)": energy_df["Recorded at"].dt.strftime(
                        "%Y-%m-%d %H:%M:%S UTC"
                    ),
                    "Energy (1-100)": energy_df["energy_level"],
                }
            )
            st.download_button(
                "Download all energy check-ins",
                data=download_df.to_csv(index=False),
                file_name="energy_checkins.csv",
                mime="text/csv",
            )

            st.subheader("Recent snapshots")
            recent_energy = energy_df.sort_values(
                "Recorded at", ascending=False
            ).head(50)
            st.dataframe(
                pd.DataFrame(
                    {
                        "Recorded at (local)": recent_energy[
                            "Local time"
                        ].dt.strftime("%Y-%m-%d %I:%M:%S %p %Z"),
                        "Energy (1-100)": recent_energy["energy_level"],
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

with tab_dashboard:
    response = (
        supabase.table("sleep_logs")
        .select(", ".join(column_names))
        .order("log_date")
        .execute()
    )
    records = response.data

    if not records:
        st.info(
            "No sleep logs found yet! Switch to the "
            "**Log Sleep** tab to add your first night."
        )
    else:
        df = pd.DataFrame(records).rename(columns=column_names)
        df = df[columns]
        target_sleep_hrs = 8.0

        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        df["Score Type"] = df["Score Version"].map(
            {1: "Earlier score", 2: "Diary score"}
        )
        st.download_button(
            "Download backup CSV",
            data=df[columns].to_csv(index=False),
            file_name="sleep_logs_backup.csv",
            mime="text/csv",
        )

        def calc_estimated_sleep(row):
            b = datetime.datetime.strptime(str(row["Bedtime"]), "%H:%M")
            w = datetime.datetime.strptime(str(row["Wake Time"]), "%H:%M")
            if w < b:
                w += datetime.timedelta(days=1)
            awake_after_sleep = row["Awake After Falling Asleep (mins)"]
            if pd.isna(awake_after_sleep):
                return float("nan")
            bed_hrs = (w - b).total_seconds() / 3600.0
            return max(
                0.0,
                bed_hrs
                - (
                    float(row["Latency (mins)"])
                    + float(awake_after_sleep)
                )
                / 60.0,
            )

        df["Estimated Sleep (hrs)"] = df.apply(calc_estimated_sleep, axis=1)
        known_sleep = df.dropna(subset=["Estimated Sleep (hrs)"]).copy()
        known_sleep["Gap vs 8h"] = (
            target_sleep_hrs - known_sleep["Estimated Sleep (hrs)"]
        )
        known_sleep["Rolling_7_Entry_Gap"] = (
            known_sleep["Gap vs 8h"].rolling(window=7, min_periods=1).sum()
        )
        thirty_days_ago = df["Date"].max() - pd.Timedelta(days=29)
        last_30_sleep = known_sleep[known_sleep["Date"] >= thirty_days_ago]
        diary_scores = df[
            (df["Score Version"] == 2) & (df["Date"] >= thirty_days_ago)
        ]

        st.subheader("Your Sleep Snapshot")
        m1, m2, m3 = st.columns(3)

        current_debt = (
            known_sleep["Rolling_7_Entry_Gap"].iloc[-1]
            if not known_sleep.empty
            else None
        )
        avg_30_hrs = (
            last_30_sleep["Estimated Sleep (hrs)"].mean()
            if not last_30_sleep.empty
            else None
        )
        avg_30_score = (
            diary_scores["Sleep Score"].mean()
            if not diary_scores.empty
            else None
        )

        m1.metric(
            label="7-Entry Sleep Gap vs 8h",
            value=f"{current_debt:.1f} hrs" if current_debt is not None else "—",
            delta=(
                f"{known_sleep['Gap vs 8h'].iloc[-1]:+.1f} hrs last night"
                if current_debt is not None
                else None
            ),
            delta_color="inverse",
        )
        m2.metric(
            label="30-Day Avg Sleep",
            value=f"{avg_30_hrs:.1f} hrs" if avg_30_hrs is not None else "—",
            delta=(
                f"{avg_30_hrs - target_sleep_hrs:+.1f} vs 8h reference"
                if avg_30_hrs is not None
                else None
            ),
        )
        m3.metric(
            label="30-Day Avg Score",
            value=f"{avg_30_score:.0f}/100" if avg_30_score is not None else "—",
        )

        st.divider()

        if not last_30_sleep.empty:
            st.subheader("Sleep Duration")
            fig_dur = go.Figure()
            fig_dur.add_trace(
                go.Bar(
                    x=last_30_sleep["Date"],
                    y=last_30_sleep["Estimated Sleep (hrs)"],
                    name="Estimated Sleep (hrs)",
                    marker_color="#636EFA",
                )
            )
            fig_dur.add_hline(
                y=target_sleep_hrs,
                line_dash="dash",
                line_color="#00CC96",
                annotation_text="8h reference",
            )
            fig_dur.update_layout(
                height=300,
                margin=dict(l=10, r=10, t=20, b=20),
                yaxis_title="Hours",
                xaxis_title="",
            )
            st.plotly_chart(fig_dur, use_container_width=True)
        else:
            st.info(
                "Sleep duration trends will appear after you save a log with "
                "the new awake-time question."
            )

        if not diary_scores.empty:
            st.subheader("Sleep Score Trend")
            fig_score = px.line(
                diary_scores,
                x="Date",
                y="Sleep Score",
                markers=True,
                range_y=[0, 105],
            )
            fig_score.update_traces(
                line_color="#AB63FA", line_width=3
            )
            fig_score.update_layout(
                height=280,
                margin=dict(l=10, r=10, t=20, b=20),
                xaxis_title="",
            )
            st.plotly_chart(fig_score, use_container_width=True)
        else:
            st.info(
                "The score trend will start after your first log with the "
                "updated scoring method."
            )

        if not known_sleep.empty:
            st.subheader("7-Entry Rolling Gap vs 8h Reference")
            fig_debt = px.area(
                known_sleep.tail(30),
                x="Date",
                y="Rolling_7_Entry_Gap",
            )
            fig_debt.update_traces(
                line_color="#EF553B",
                fillcolor="rgba(239, 85, 59, 0.2)",
            )
            fig_debt.update_layout(
                height=280,
                margin=dict(l=10, r=10, t=20, b=20),
                yaxis_title="Gap (Hours)",
                xaxis_title="",
            )
            st.plotly_chart(fig_debt, use_container_width=True)

        with st.expander("View Recent Sleep Logs"):
            display_cols = [
                "Date",
                "Bedtime",
                "Wake Time",
                "Estimated Sleep (hrs)",
                "Sleep Score",
                "Score Type",
            ]
            st.dataframe(
                df[display_cols]
                .sort_values("Date", ascending=False)
                .head(14),
                use_container_width=True,
                hide_index=True,
            )
