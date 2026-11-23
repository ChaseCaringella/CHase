# Sleep Tracker

The app stores sleep logs in Supabase, so they persist when the app restarts.
Use **Download backup CSV** on the dashboard to save a copy to your computer.

## Set up Supabase

1. Create a Supabase project.
2. In its SQL Editor, run the contents of `supabase_setup.sql`.
3. Copy the project URL and its `service_role` secret key from the API settings.
   Keep the secret key private; do not commit it to GitHub.

If you already created the `sleep_logs` table using an earlier version of this
app, run `supabase_migration_v2.sql` once in the SQL Editor before restarting
the app. It preserves prior logs, marks their scores as earlier scores, and
allows the new diary fields.

To add the optional energy check-ins to an existing project, run
`supabase_migration_v3.sql` once in the SQL Editor. Energy ratings are stored
as timestamped 1-100 snapshots in UTC and displayed in Riverside, California
time. The curve is a subjective self-report, not an objective measurement or
medical assessment.

To add the gym tracker to an existing project, run `supabase_migration_v4.sql`
once in the SQL Editor. The app then shows a **Gym Tracker** page in Streamlit's
navigation, with the six-day workout split, set logging, estimated 1RM trends,
personal records, recent history, and a CSV backup. Weights can be entered in
lb or kg; use one unit consistently because the app does not convert units.

## About the sleep score

The score is a transparent diary-based estimate for adults. It uses sleep
duration (35 points), sleep efficiency (30), time to fall asleep (15), and
your 1-10 restedness rating (20). The duration target is at least 7 hours;
efficiency earns full points at 85% and none below 60%; falling asleep within
20 minutes earns full latency points, which taper to zero at 60 minutes.
Caffeine, screen time, stress, and mood are saved as context rather than
automatic penalties. The score is not a diagnosis or a clinical sleep
measurement; diary entries cannot measure REM or deep sleep. The seven-hour
duration threshold is the adult minimum in CDC guidance for ages 18-60; CDC
guidance for ages 61-64 is 7-9 hours
([CDC sleep recommendations](https://www.cdc.gov/sleep/about/index.html)).

## Run locally

Install the requirements:

```bash
python -m pip install -r requirements.txt
```

Create `.streamlit/secrets.toml` with your own app password and Supabase
credentials:

```toml
[app]
password = "choose-a-long-private-password"

[supabase]
url = "https://your-project.supabase.co"
key = "your-service-role-secret-key"
```

Then start the app:

```bash
streamlit run app.py
```

## Deploy online

Push this repository to GitHub and deploy it with Streamlit Community Cloud.
In the app's **Settings → Secrets**, add the same TOML values shown above.
The app asks for the password in `[app]` before displaying sleep records.
Keep both the app password and Supabase key private.

## Use it on your phone

This is a mobile-friendly web app, not a native iOS or Android app. After
deploying it online, open its URL on your phone and use the browser's
**Add to Home Screen** option to create a home-screen shortcut. It requires an
internet connection and does not read data from phone sensors.
