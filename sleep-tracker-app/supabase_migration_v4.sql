-- Add persistent gym workout logging to an existing Sleep Tracker Supabase project.
-- Run once in the Supabase SQL Editor. The app uses the service_role key
-- server-side, so no client-facing policies are needed.

create table if not exists public.workout_logs (
    id bigint generated always as identity primary key,
    log_date date not null,
    day_type text not null,
    exercise text not null,
    set_number integer not null check (set_number > 0),
    weight numeric(10, 2) not null check (weight >= 0),
    reps integer not null check (reps > 0),
    rpe numeric(3, 1) not null check (rpe between 1 and 10),
    volume numeric(12, 2) not null check (volume >= 0),
    est_1rm numeric(10, 2) not null check (est_1rm >= 0),
    created_at timestamptz not null default now()
);

create index if not exists workout_logs_date_idx
    on public.workout_logs (log_date desc);

create index if not exists workout_logs_exercise_date_idx
    on public.workout_logs (exercise, log_date);

alter table public.workout_logs enable row level security;
grant select, insert on public.workout_logs to service_role;
grant usage, select on sequence public.workout_logs_id_seq to service_role;
