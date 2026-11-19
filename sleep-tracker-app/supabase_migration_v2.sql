alter table public.sleep_logs
    add column if not exists wake_after_sleep_mins integer,
    add column if not exists caffeine_consumed boolean not null default true,
    add column if not exists score_version smallint not null default 1,
    alter column caffeine_cutoff drop not null,
    alter column estimated_deep_sleep_hrs drop not null,
    alter column estimated_rem_sleep_hrs drop not null;

grant select, insert on public.sleep_logs to service_role;
