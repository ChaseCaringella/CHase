create table if not exists public.energy_checkins (
    id bigint generated always as identity primary key,
    recorded_at timestamptz not null default now(),
    energy_level smallint not null
        check (energy_level between 1 and 100)
);

alter table public.energy_checkins enable row level security;

grant select, insert on public.energy_checkins to service_role;
grant usage, select on sequence public.energy_checkins_id_seq to service_role;
