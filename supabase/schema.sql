-- Banedagbok: databaseskjema for Supabase.
-- Kjør hele fila én gang i Supabase: SQL Editor → New query → lim inn → Run.
-- Fila kan kjøres på nytt uten å ødelegge data.
--
-- Datamodell: hver rad har en id og et JSON-dokument (data) med samme form som
-- nettsiden bruker. Noen felt er hentet ut som egne kolonner for filtrering.
--   config      én rad (id = 'oppsett'): klubbnavn, anlegg, delbaner, kampvarighet
--   kamper      kamper fra fotball.no (kilde = 'fotball.no') og manuelle bookinger (kilde = 'manuell')
--   treninger   faste treningstider
--   foresporsler forespørsler om banetid fra trenere (status: ny / godkjent / avslatt)
--   brukere     hvem som kan logge inn og hva de får gjøre (id = e-post med små bokstaver)
--
-- Roller (data->>'rolle' i brukere):
--   admin         alt, inkludert brukere, anlegg, kamper og godkjenning av forespørsler
--   trener_pluss  legge inn, endre, avlyse og slette treninger for egne lag, og sende forespørsler
--   trener        avlyse og slette treninger for egne lag, og sende forespørsler
-- Alle, også de som ikke er logget inn, kan lese anlegg, kamper og treninger.

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

create table if not exists public.foresporsler (
  id         text primary key,
  data       jsonb not null,
  status     text generated always as (coalesce(data->>'status', 'ny')) stored,
  epost      text generated always as (lower(data->>'epost')) stored,
  updated_at timestamptz not null default now()
);

create table if not exists public.brukere (
  id         text primary key check (id = lower(id)),   -- e-postadressen med små bokstaver
  data       jsonb not null,                            -- {epost, navn, rolle, lag: [...]}
  rolle      text generated always as (data->>'rolle') stored check (rolle in ('admin', 'trener_pluss', 'trener')),
  updated_at timestamptz not null default now()
);

-- Tidligere versjon brukte en egen redaktørliste
drop function if exists public.er_redaktor();
drop table if exists public.redaktorer;

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
  foreach t in array array['config', 'kamper', 'treninger', 'foresporsler', 'brukere'] loop
    execute format('drop trigger if exists %I_updated_at on public.%I', t, t);
    execute format('create trigger %I_updated_at before update on public.%I for each row execute function public.sett_updated_at()', t, t);
  end loop;
end $$;

-- Hjelpefunksjoner. security definer: de leser brukere uten å være stoppet av tilgangsreglene.
create or replace function public.min_epost() returns text
language sql stable as $$ select lower(coalesce(auth.jwt() ->> 'email', '')) $$;

create or replace function public.min_bruker() returns jsonb
language sql stable security definer set search_path = public as $$
  select data from public.brukere where id = public.min_epost();
$$;

create or replace function public.min_rolle() returns text
language sql stable security definer set search_path = public as $$
  select coalesce((select rolle from public.brukere where id = public.min_epost()), '');
$$;

create or replace function public.er_admin() returns boolean
language sql stable as $$ select public.min_rolle() = 'admin' $$;

-- Er innlogget bruker trener (eller trener+) for dette laget?
create or replace function public.har_lag(lag text) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.brukere
    where id = public.min_epost() and rolle in ('trener', 'trener_pluss')
      and coalesce(data->'lag', '[]'::jsonb) ? coalesce(lag, '')
  );
$$;

revoke all on function public.min_bruker(), public.min_rolle(), public.er_admin(), public.har_lag(text), public.min_epost() from public;
grant execute on function public.min_bruker(), public.min_rolle(), public.er_admin(), public.har_lag(text), public.min_epost() to anon, authenticated;

-- En trener (ikke trener+) kan bare avlyse enkeltdager, ikke endre selve treningstiden
create or replace function public.sjekk_trener_endring() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if public.min_rolle() = 'trener' and (new.data - 'avlyst') is distinct from (old.data - 'avlyst') then
    raise exception 'Trenere kan bare avlyse enkeltdager. Be admin eller en trener+ endre treningstiden.'
      using errcode = '42501';
  end if;
  return new;
end $$;
drop trigger if exists treninger_trener_endring on public.treninger;
create trigger treninger_trener_endring before update on public.treninger
  for each row execute function public.sjekk_trener_endring();

-- Det må alltid finnes minst én admin
create or replace function public.behold_en_admin() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if old.rolle = 'admin' and (tg_op = 'DELETE' or new.rolle is distinct from 'admin')
     and not exists (select 1 from public.brukere where rolle = 'admin' and id <> old.id) then
    raise exception 'Det må finnes minst én admin. Legg til en ny admin først.' using errcode = '42501';
  end if;
  return case when tg_op = 'DELETE' then old else new end;
end $$;
drop trigger if exists brukere_behold_admin on public.brukere;
create trigger brukere_behold_admin before update or delete on public.brukere
  for each row execute function public.behold_en_admin();

-- Tilgangsregler (Row Level Security)
alter table public.config       enable row level security;
alter table public.kamper       enable row level security;
alter table public.treninger    enable row level security;
alter table public.foresporsler enable row level security;
alter table public.brukere      enable row level security;

-- Fjern alle tidligere regler på tabellene, så fila kan kjøres på nytt
do $$
declare r record;
begin
  for r in select policyname, tablename from pg_policies
           where schemaname = 'public' and tablename in ('config', 'kamper', 'treninger', 'foresporsler', 'brukere') loop
    execute format('drop policy %I on public.%I', r.policyname, r.tablename);
  end loop;
end $$;

-- config og kamper: alle leser, admin endrer. Trenere kan slette bookinger for egne lag.
create policy "alle kan lese" on public.config for select to anon, authenticated using (true);
create policy "admin endrer" on public.config for all to authenticated using (public.er_admin()) with check (public.er_admin());

create policy "alle kan lese" on public.kamper for select to anon, authenticated using (true);
create policy "admin endrer" on public.kamper for all to authenticated using (public.er_admin()) with check (public.er_admin());
create policy "trenere sletter egne bookinger" on public.kamper for delete to authenticated
  using (kilde = 'manuell' and public.har_lag(data->>'lag'));

-- treninger
create policy "alle kan lese" on public.treninger for select to anon, authenticated using (true);
create policy "admin og trener+ legger til" on public.treninger for insert to authenticated
  with check (public.er_admin() or (public.min_rolle() = 'trener_pluss' and public.har_lag(data->>'lag')));
create policy "admin og trenere endrer egne" on public.treninger for update to authenticated
  using (public.er_admin() or public.har_lag(data->>'lag'))
  with check (public.er_admin() or public.har_lag(data->>'lag'));
create policy "admin og trenere sletter egne" on public.treninger for delete to authenticated
  using (public.er_admin() or public.har_lag(data->>'lag'));

-- foresporsler: trenere sender og ser sine egne, admin ser og behandler alle
create policy "admin og avsender leser" on public.foresporsler for select to authenticated
  using (public.er_admin() or epost = public.min_epost());
create policy "trenere sender" on public.foresporsler for insert to authenticated
  with check (public.er_admin() or (epost = public.min_epost() and status = 'ny' and public.har_lag(data->>'lag')));
create policy "admin behandler" on public.foresporsler for update to authenticated
  using (public.er_admin()) with check (public.er_admin());
create policy "admin og avsender sletter" on public.foresporsler for delete to authenticated
  using (public.er_admin() or (epost = public.min_epost() and status = 'ny'));

-- brukere: admin ser og endrer alle, andre ser bare seg selv
create policy "admin og en selv leser" on public.brukere for select to authenticated
  using (public.er_admin() or id = public.min_epost());
create policy "admin endrer" on public.brukere for all to authenticated
  using (public.er_admin()) with check (public.er_admin());

grant select on public.config, public.kamper, public.treninger to anon, authenticated;
grant insert, update, delete on public.config, public.kamper, public.treninger to authenticated;
grant select, insert, update, delete on public.foresporsler, public.brukere to authenticated;
-- anon får lese, men tilgangsreglene over gir dem ingen rader
grant select on public.foresporsler, public.brukere to anon;

-- Sanntid: åpne sider oppdateres når noen andre endrer noe
do $$
declare t text;
begin
  if exists (select 1 from pg_publication where pubname = 'supabase_realtime') then
    foreach t in array array['config', 'kamper', 'treninger', 'foresporsler', 'brukere'] loop
      if not exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = t) then
        execute format('alter publication supabase_realtime add table public.%I', t);
      end if;
    end loop;
  end if;
end $$;
