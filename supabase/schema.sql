-- Banedagbok: databaseskjema for Supabase.
-- Kjør hele fila én gang i Supabase: SQL Editor → New query → lim inn → Run.
-- Fila kan kjøres på nytt uten å ødelegge data.
--
-- Datamodell: hver rad har en id og et JSON-dokument (data) med samme form som
-- nettsiden bruker. Noen felt er hentet ut som egne kolonner for filtrering.
--   config      én rad (id = 'oppsett'): klubbnavn, anlegg, delbaner, kampvarighet
--   kamper      kamper fra fotball.no (kilde = 'fotball.no') og manuelle bookinger (kilde = 'manuell')
--   treninger   faste treningstider
--   redaktorer  e-postadresser som får endre (alle andre kan bare lese)

create table if not exists public.config (
  id         text primary key,
  data       jsonb not null,
  updated_at timestamptz not null default now()
);

create table if not exists public.kamper (
  id         text primary key,
  data       jsonb not null,
  anlegg_id  text generated always as (data->>'anleggId') stored,
  dato       text generated always as (data->>'dato') stored,      -- ISO-dato, YYYY-MM-DD
  kilde      text generated always as (coalesce(data->>'kilde', 'fotball.no')) stored,
  updated_at timestamptz not null default now()
);
create index if not exists kamper_anlegg_dato on public.kamper (anlegg_id, dato);

create table if not exists public.treninger (
  id         text primary key,
  data       jsonb not null,
  updated_at timestamptz not null default now()
);

create table if not exists public.redaktorer (
  epost      text primary key,
  navn       text,
  lagt_til   timestamptz not null default now()
);

-- updated_at holdes oppdatert automatisk
create or replace function public.sett_updated_at() returns trigger
language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end $$;

do $$
declare t text;
begin
  foreach t in array array['config', 'kamper', 'treninger'] loop
    execute format('drop trigger if exists %I_updated_at on public.%I', t, t);
    execute format('create trigger %I_updated_at before update on public.%I for each row execute function public.sett_updated_at()', t, t);
  end loop;
end $$;

-- Er innlogget bruker redaktør? Sjekker e-posten i innloggingen mot tabellen redaktorer.
create or replace function public.er_redaktor() returns boolean
language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.redaktorer r
    where lower(r.epost) = lower(coalesce(auth.jwt() ->> 'email', ''))
  );
$$;
revoke all on function public.er_redaktor() from public;
grant execute on function public.er_redaktor() to anon, authenticated;

-- Tilgangsregler (Row Level Security)
alter table public.config     enable row level security;
alter table public.kamper     enable row level security;
alter table public.treninger  enable row level security;
alter table public.redaktorer enable row level security;

do $$
declare t text;
begin
  foreach t in array array['config', 'kamper', 'treninger'] loop
    execute format('drop policy if exists "alle kan lese" on public.%I', t);
    execute format('drop policy if exists "redaktorer kan legge til" on public.%I', t);
    execute format('drop policy if exists "redaktorer kan endre" on public.%I', t);
    execute format('drop policy if exists "redaktorer kan slette" on public.%I', t);
    execute format('create policy "alle kan lese" on public.%I for select to anon, authenticated using (true)', t);
    execute format('create policy "redaktorer kan legge til" on public.%I for insert to authenticated with check (public.er_redaktor())', t);
    execute format('create policy "redaktorer kan endre" on public.%I for update to authenticated using (public.er_redaktor()) with check (public.er_redaktor())', t);
    execute format('create policy "redaktorer kan slette" on public.%I for delete to authenticated using (public.er_redaktor())', t);
  end loop;
end $$;

-- Redaktørlista er bare synlig for redaktører. Den vedlikeholdes i Supabase (Table Editor eller SQL).
drop policy if exists "redaktorer ser lista" on public.redaktorer;
create policy "redaktorer ser lista" on public.redaktorer for select to authenticated using (public.er_redaktor());

grant select on public.config, public.kamper, public.treninger to anon, authenticated;
grant insert, update, delete on public.config, public.kamper, public.treninger to authenticated;
grant select on public.redaktorer to authenticated;

-- Sanntid: åpne sider oppdateres når noen andre endrer noe
do $$
declare t text;
begin
  if exists (select 1 from pg_publication where pubname = 'supabase_realtime') then
    foreach t in array array['config', 'kamper', 'treninger'] loop
      if not exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = t) then
        execute format('alter publication supabase_realtime add table public.%I', t);
      end if;
    end loop;
  end if;
end $$;
