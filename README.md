# CHase Sleep Tracker

The sleep tracker is a Streamlit app in [`sleep-tracker-app/`](sleep-tracker-app/).

## Deploy with Streamlit Community Cloud

1. Push this repository to GitHub.
2. In Streamlit Community Cloud, select the `main` branch.
3. Set **Main file path** to `sleep-tracker-app/app.py`.
4. Add the app password and Supabase URL/key in **Settings → Secrets**. See
   [`sleep-tracker-app/README.md`](sleep-tracker-app/README.md) for setup details.

The Supabase `service_role` key is sensitive. Add it only to Streamlit Secrets;
do not commit it to GitHub.
