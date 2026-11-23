create table public.sleep_logs (
    id bigint generated always as identity primary key,
    log_date date not null,
    bedtime text not null,
    wake_time text not null,
    latency_mins integer not null,
    night_awakenings integer not null,
    wake_after_sleep_mins integer not null,
    sleep_quality integer not null,
    caffeine_consumed boolean not null default false,
    caffeine_cutoff text,
    screen_time_mins integer not null,
    stress integer not null,
    morning_mood integer not null,
    sleep_score integer not null,
    score_version smallint not null default 2,
    created_at timestamptz not null default now()
);

alter table public.sleep_logs enable row level security;

grant select, insert on public.sleep_logs to service_role;

create table public.energy_checkins (
    id bigint generated always as identity primary key,
    recorded_at timestamptz not null default now(),
    energy_level smallint not null
        check (energy_level between 1 and 100)
);

alter table public.energy_checkins enable row level security;

grant select, insert on public.energy_checkins to service_role;
grant usage, select on sequence public.energy_checkins_id_seq to service_role;

create table public.gym_logs (
    id bigint generated always as identity primary key,
    workout_date date not null,
    day_type text not null,
    exercise text not null,
    set_number integer not null check (set_number > 0),
    weight numeric(8, 2) not null check (weight > 0),
    weight_unit text not null check (weight_unit in ('lb', 'kg')),
    reps integer not null check (reps > 0),
    rpe numeric(3, 1) not null check (rpe between 1 and 10),
    volume numeric(10, 2) not null check (volume > 0),
    est_1rm numeric(10, 2) not null check (est_1rm > 0),
    created_at timestamptz not null default now()
);

alter table public.gym_logs enable row level security;

grant select, insert on public.gym_logs to service_role;
grant usage, select on sequence public.gym_logs_id_seq to service_role;
