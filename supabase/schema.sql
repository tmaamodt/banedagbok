-- Banedagbok: databaseskjema for Supabase.
-- Kjør hele fila én gang i Supabase: SQL Editor → New query → lim inn → Run.
-- Fila kan kjøres på nytt uten å ødelegge data.
--
-- Datamodell: hver rad har en id og et JSON-dokument (data) med samme form som
-- nettsiden bruker. Noen felt er hentet ut som egne kolonner for filtrering.
--   config      én rad (id = 'oppsett'): klubbnavn, anlegg, delbaner, kampvarighet
--   kamper      kamper fra fotball.no (kilde = 'fotball.no'), treningskamper (kilde = 'treningskamp')
--               og manuelle bookinger (kilde = 'manuell')
--   treninger   treningstider: faste hver uke i en periode (type = 'fast') eller enkelttreninger (type = 'enkelt')
--   foresporsler forespørsler om banetid fra trenere (status: ny / godkjent / avslatt)
--   brukere     hvem som kan logge inn og hva de får gjøre. Eldre rader har e-posten som id, godkjente fra
--               godkjenningslisten har id «u-<Supabase-bruker-id>». En bruker kjennes igjen på Supabase-bruker-id
--               (data.uids) og på e-postadressene sine (data.epost og data.eposter).
--   ventende    godkjenningslisten: innlogginger som ikke er koblet til en bruker ennå (id = Supabase-bruker-id)
--   varsellogg  e-postvarsler som er sendt (skrives av scripts/send_varsler.py), så ingen får samme varsel to ganger
--   grupper     treningsgrupper: et treningsnavn (f.eks. «G16») koblet til lag på fotball.no
--   lagkamper   alle kamper for klubbene som bruker banene (også bortekamper), én rad per klubb per måned
--   gjest       treninger og bookinger på gjesteanlegg, hentet fra Hoopit, én rad per bane per måned
--   dommere     lokale dommere med navn, kontaktinfo, fødselsår og kamptyper. Bare admin og dommeransvarlig ser dem.
--   dommeroppdrag  lokal dommer satt opp på en kamp (id = kampens id). Alle ser bare kortnavnet («Ola N.»).
--
-- Roller (data->>'rolle' i brukere):
--   admin         alt, inkludert brukere, anlegg, kamper og godkjenning av forespørsler
--   trener_pluss  som trener, og i tillegg legge inn og endre enkelttreninger og treningskamper for egne lag
--   trener        avlyse og slette treninger, enkelttreninger og treningskamper for egne lag, og sende forespørsler
-- Faste treningstider (hver uke) legges bare inn av admin, eller ved at admin godkjenner en forespørsel.
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

create table if not exists public.grupper (
  id         text primary key,
  data       jsonb not null,                            -- {lag: "G16", fotballLag: ["G16 Bjørkelangen", ...]}
  updated_at timestamptz not null default now()
);

create table if not exists public.lagkamper (
  id         text primary key,                          -- "<klubb-ID>-<ÅÅÅÅ-MM>"
  data       jsonb not null,                            -- {klubbId, maned, kamper: [...]}; skrives av hent_kamper.py
  updated_at timestamptz not null default now()
);

create table if not exists public.gjest (
  id         text primary key,                          -- "h<Hoopit bane-ID>-<ÅÅÅÅ-MM>"
  data       jsonb not null,                            -- {venueId, anleggId, baneId, maned, hentet, hendelser: [...]}; skrives av hent_kamper.py
  updated_at timestamptz not null default now()
);

create table if not exists public.brukere (
  id         text primary key check (id = lower(id)),   -- e-post (eldre rader) eller «u-<Supabase-bruker-id>»
  data       jsonb not null,                            -- {epost, eposter: [...], uids: [...], navn, rolle, lag: [...], dommerId,
                                                        --  varsler: {godkjenning, kampITrening}, varselEpost}
  rolle      text generated always as (data->>'rolle') stored check (rolle in ('admin', 'trener_pluss', 'trener', 'dommeransvarlig', 'dommer')),
  updated_at timestamptz not null default now()
);
-- databaser laget før rollen dommeransvarlig fantes: oppdater sjekken
alter table public.brukere drop constraint if exists brukere_rolle_check;
alter table public.brukere add constraint brukere_rolle_check check (rolle in ('admin', 'trener_pluss', 'trener', 'dommeransvarlig', 'dommer'));

create index if not exists brukere_uids on public.brukere using gin ((data->'uids'));
create index if not exists brukere_eposter on public.brukere using gin ((data->'eposter'));

-- Godkjenningslisten: den som logger inn uten å være kjent, havner her til admin godkjenner
create table if not exists public.ventende (
  id         text primary key,                          -- Supabase-bruker-id (auth.users.id)
  data       jsonb not null,                            -- {uid, epost, navn, leverandor, forst, sist}
  updated_at timestamptz not null default now()
);

-- Sendte e-postvarsler. Bare send_varsler.py (service_role) leser og skriver.
create table if not exists public.varsellogg (
  id         text primary key,                          -- f.eks. «godkjenning|<id>» eller «kamp|<kamp>|<trening>|<dato>»
  data       jsonb not null,                            -- {sendt}
  updated_at timestamptz not null default now()
);

create table if not exists public.dommere (
  id         text primary key,
  data       jsonb not null,                            -- {navn, telefon, epost, fodselsar, kamptyper: ["5","7","9","11"], aktiv}
  updated_at timestamptz not null default now()
);

create table if not exists public.dommeroppdrag (
  id         text primary key,                          -- kampens id
  data       jsonb not null,                            -- {kampId, dommerId, navn: "Ola N.", tildelt}
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
  foreach t in array array['config', 'kamper', 'treninger', 'foresporsler', 'brukere', 'grupper', 'lagkamper', 'gjest', 'dommere', 'dommeroppdrag', 'ventende', 'varsellogg'] loop
    execute format('drop trigger if exists %I_updated_at on public.%I', t, t);
    execute format('create trigger %I_updated_at before update on public.%I for each row execute function public.sett_updated_at()', t, t);
  end loop;
end $$;

-- Hjelpefunksjoner. security definer: de leser brukere uten å være stoppet av tilgangsreglene.
create or replace function public.min_epost() returns text
language sql stable as $$ select lower(coalesce(auth.jwt() ->> 'email', '')) $$;

-- Brukeren (id i brukere) som innlogget person er: først på Supabase-bruker-id, ellers på e-postadressen
create or replace function public.min_brukerid() returns text
language sql stable security definer set search_path = public as $$
  select coalesce(
    (select id from public.brukere where data->'uids' ? coalesce(auth.uid()::text, '') limit 1),
    (select id from public.brukere where public.min_epost() <> ''
       and (lower(data->>'epost') = public.min_epost() or data->'eposter' ? public.min_epost()) limit 1),
    '');
$$;

-- Kalles av nettsiden etter innlogging. Kjent bruker: Supabase-bruker-id kobles til brukeren (første gang),
-- og brukeren returneres med id. Ukjent: personen legges i godkjenningslisten, og svaret er null.
drop function if exists public.min_bruker();
create function public.min_bruker() returns jsonb
language plpgsql volatile security definer set search_path = public as $$
declare
  u    text := coalesce(auth.uid()::text, '');
  bid  text;
  d    jsonb;
  meta jsonb := coalesce(auth.jwt() -> 'user_metadata', '{}'::jsonb);
begin
  if u = '' then return null; end if;
  bid := public.min_brukerid();
  if bid <> '' then
    -- vilkåret i where gjør at to samtidige innlogginger ikke legger inn samme id to ganger
    update public.brukere set data = jsonb_set(data, '{uids}', coalesce(data->'uids', '[]'::jsonb) || to_jsonb(u))
      where id = bid and not coalesce(data->'uids', '[]'::jsonb) ? u;
    select data into d from public.brukere where id = bid;
    delete from public.ventende where id = u;
    return d || jsonb_build_object('id', bid);
  end if;
  insert into public.ventende (id, data) values (u, jsonb_build_object(
      'uid', u, 'epost', public.min_epost(), 'navn', coalesce(meta->>'full_name', meta->>'name', ''),
      'leverandor', coalesce(auth.jwt() -> 'app_metadata' ->> 'provider', 'email'), 'forst', now(), 'sist', now()))
  on conflict (id) do update set data = public.ventende.data
      || jsonb_build_object('epost', excluded.data->'epost', 'leverandor', excluded.data->'leverandor', 'sist', now());
  return null;
end $$;

create or replace function public.min_rolle() returns text
language sql stable security definer set search_path = public as $$
  select coalesce((select rolle from public.brukere where id = public.min_brukerid()), '');
$$;

create or replace function public.er_admin() returns boolean
language sql stable as $$ select public.min_rolle() = 'admin' $$;

create or replace function public.er_dommeransvarlig() returns boolean
language sql stable as $$ select public.min_rolle() in ('admin', 'dommeransvarlig') $$;

-- Dommeren som innlogget bruker er koblet til (brukere.data.dommerId), eller ''
create or replace function public.min_dommer() returns text
language sql stable security definer set search_path = public as $$
  select coalesce((select data->>'dommerId' from public.brukere where id = public.min_brukerid()), '');
$$;

-- En dommer kan bare endre egen kontaktinfo (telefon og e-post), ikke navn, kamptyper, kompetanse eller aktiv
create or replace function public.sjekk_dommer_endring() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if not public.er_dommeransvarlig()
     and (new.data - 'telefon' - 'epost') is distinct from (old.data - 'telefon' - 'epost') then
    raise exception 'Du kan bare endre telefon og e-post.' using errcode = '42501';
  end if;
  return new;
end $$;

-- Er innlogget bruker trener (eller trener+) for dette laget?
create or replace function public.har_lag(lag text) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.brukere
    where id = public.min_brukerid() and rolle in ('trener', 'trener_pluss')
      and coalesce(data->'lag', '[]'::jsonb) ? coalesce(lag, '')
  );
$$;

-- Er forespørselen sendt av innlogget bruker? Nye har brukerId, eldre bare e-post.
-- Eldre forespørsler uten brukerId er mine når e-posten er en av e-postadressene mine.
create or replace function public.er_min(d jsonb) returns boolean
language sql stable security definer set search_path = public as $$
  select case when coalesce(d->>'brukerId', '') <> '' then d->>'brukerId' = public.min_brukerid()
              else coalesce(d->>'epost', '') <> '' and (lower(d->>'epost') = public.min_epost()
                   or exists (select 1 from public.brukere b where b.id = public.min_brukerid()
                              and (lower(b.data->>'epost') = lower(d->>'epost') or b.data->'eposter' ? lower(d->>'epost')))) end;
$$;

-- En e-postadresse eller innlogging kan bare høre til én bruker
create or replace function public.sjekk_unik_bruker() returns trigger
language plpgsql security definer set search_path = public as $$
declare e text; u text;
begin
  for e in select distinct lower(x) from (
      select new.data->>'epost' as x
      union all select jsonb_array_elements_text(coalesce(new.data->'eposter', '[]'::jsonb))) s
    where coalesce(x, '') <> '' loop
    if exists (select 1 from public.brukere b where b.id <> new.id
               and (lower(b.data->>'epost') = e or b.data->'eposter' ? e)) then
      raise exception 'E-postadressen % hører allerede til en annen bruker.', e using errcode = '23505';
    end if;
  end loop;
  for u in select jsonb_array_elements_text(coalesce(new.data->'uids', '[]'::jsonb)) loop
    if exists (select 1 from public.brukere b where b.id <> new.id and b.data->'uids' ? u) then
      raise exception 'Innloggingen er allerede koblet til en annen bruker.' using errcode = '23505';
    end if;
  end loop;
  return new;
end $$;
drop trigger if exists brukere_unik on public.brukere;
create trigger brukere_unik before insert or update on public.brukere
  for each row execute function public.sjekk_unik_bruker();

-- Innlogget bruker slår egne e-postvarsler av og på. Endrer bare varsler og varselEpost, ikke rolle, lag eller annet.
create or replace function public.sett_mine_varsler(varsler jsonb, varsel_epost text) returns jsonb
language plpgsql volatile security definer set search_path = public as $$
declare bid text := public.min_brukerid(); v jsonb := '{}'::jsonb; k text; d jsonb;
begin
  if bid = '' then raise exception 'Du er ikke registrert som bruker.' using errcode = '42501'; end if;
  foreach k in array array['godkjenning', 'kampITrening'] loop
    if jsonb_typeof(varsler->k) = 'boolean' then v := v || jsonb_build_object(k, varsler->k); end if;
  end loop;
  if coalesce(varsel_epost, '') <> '' and varsel_epost !~ '^[^@\s]+@[^@\s]+\.[^@\s]+$' then
    raise exception 'Ugyldig e-postadresse for varsler.' using errcode = 'P0001';
  end if;
  update public.brukere set data = data || jsonb_build_object('varsler', v, 'varselEpost', lower(coalesce(varsel_epost, '')))
    where id = bid returning data into d;
  return d || jsonb_build_object('id', bid);
end $$;
revoke all on function public.sett_mine_varsler(jsonb, text) from public;
grant execute on function public.sett_mine_varsler(jsonb, text) to authenticated;

revoke all on function public.min_bruker(), public.min_rolle(), public.er_admin(), public.har_lag(text), public.min_epost(), public.min_brukerid(), public.er_min(jsonb) from public;
grant execute on function public.min_bruker(), public.min_rolle(), public.er_admin(), public.har_lag(text), public.min_epost(), public.min_brukerid(), public.er_min(jsonb) to anon, authenticated;

-- Trenere kan bare avlyse enkeltdager på faste treningstider. Trener+ kan i tillegg endre enkelttreninger.
create or replace function public.sjekk_trener_endring() returns trigger
language plpgsql security definer set search_path = public as $$
declare r text := public.min_rolle();
begin
  if (r = 'trener' or (r = 'trener_pluss' and (coalesce(old.data->>'type', 'fast') <> 'enkelt' or coalesce(new.data->>'type', 'fast') <> 'enkelt')))
     and (new.data - 'avlyst') is distinct from (old.data - 'avlyst') then
    raise exception 'Du kan bare avlyse enkeltdager. Endring av en fast treningstid må søkes om hos admin.'
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
  -- new.rolle (beregnet kolonne) er ikke satt ennå i en before-trigger, så rollen leses fra data
  if old.rolle = 'admin' and (tg_op = 'DELETE' or new.data->>'rolle' is distinct from 'admin')
     and not exists (select 1 from public.brukere where rolle = 'admin' and id <> old.id) then
    raise exception 'Det må finnes minst én admin. Legg til en ny admin først.' using errcode = '42501';
  end if;
  return case when tg_op = 'DELETE' then old else new end;
end $$;
drop trigger if exists brukere_behold_admin on public.brukere;
create trigger brukere_behold_admin before update or delete on public.brukere
  for each row execute function public.behold_en_admin();

-- Gjesteanlegg er bare til visning: ingen treninger, forespørsler, bookinger eller treningskamper kan
-- legges der. Kamper fra fotball.no (hent_kamper.py) er lov.
create or replace function public.er_gjesteanlegg(anlegg text) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.config c, jsonb_array_elements(coalesce(c.data->'anlegg', '[]'::jsonb)) a
                 where c.id = 'oppsett' and a->>'id' = anlegg and coalesce((a->>'gjest')::boolean, false));
$$;
create or replace function public.sjekk_gjesteanlegg() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if public.er_gjesteanlegg(new.data->>'anleggId')
     and not (tg_table_name = 'kamper' and coalesce(new.data->>'kilde', 'fotball.no') = 'fotball.no') then
    raise exception 'Anlegget er et gjesteanlegg og kan bare vises, ikke endres.' using errcode = '42501';
  end if;
  return new;
end $$;
do $$
declare t text;
begin
  foreach t in array array['kamper', 'treninger', 'foresporsler'] loop
    execute format('drop trigger if exists %I_gjesteanlegg on public.%I', t, t);
    execute format('create trigger %I_gjesteanlegg before insert or update on public.%I for each row execute function public.sjekk_gjesteanlegg()', t, t);
  end loop;
end $$;

-- Tilgangsregler (Row Level Security)
alter table public.config       enable row level security;
alter table public.kamper       enable row level security;
alter table public.treninger    enable row level security;
alter table public.foresporsler enable row level security;
alter table public.brukere      enable row level security;
alter table public.grupper      enable row level security;
alter table public.lagkamper    enable row level security;
alter table public.gjest        enable row level security;
alter table public.dommere      enable row level security;
alter table public.dommeroppdrag enable row level security;
alter table public.ventende     enable row level security;
alter table public.varsellogg   enable row level security;  -- ingen regler: bare service_role

-- Fjern alle tidligere regler på tabellene, så fila kan kjøres på nytt
do $$
declare r record;
begin
  for r in select policyname, tablename from pg_policies
           where schemaname = 'public' and tablename in ('config', 'kamper', 'treninger', 'foresporsler', 'brukere', 'grupper', 'lagkamper', 'gjest', 'dommere', 'dommeroppdrag', 'ventende') loop
    execute format('drop policy %I on public.%I', r.policyname, r.tablename);
  end loop;
end $$;

-- config og kamper: alle leser, admin endrer. Trenere kan slette bookinger for egne lag.
create policy "alle kan lese" on public.config for select to anon, authenticated using (true);
create policy "admin endrer" on public.config for all to authenticated using (public.er_admin()) with check (public.er_admin());

create policy "alle kan lese" on public.kamper for select to anon, authenticated using (true);
create policy "admin endrer" on public.kamper for all to authenticated using (public.er_admin()) with check (public.er_admin());
create policy "trenere sletter egne bookinger og treningskamper" on public.kamper for delete to authenticated
  using (kilde in ('manuell', 'treningskamp') and public.har_lag(data->>'lag'));
create policy "trener+ legger inn treningskamper" on public.kamper for insert to authenticated
  with check (kilde = 'treningskamp' and public.min_rolle() = 'trener_pluss' and public.har_lag(data->>'lag'));
create policy "trener+ endrer treningskamper" on public.kamper for update to authenticated
  using (kilde = 'treningskamp' and public.min_rolle() = 'trener_pluss' and public.har_lag(data->>'lag'))
  with check (kilde = 'treningskamp' and public.min_rolle() = 'trener_pluss' and public.har_lag(data->>'lag'));

-- treninger
create policy "alle kan lese" on public.treninger for select to anon, authenticated using (true);
create policy "admin legger til, trener+ bare enkelttreninger" on public.treninger for insert to authenticated
  with check (public.er_admin() or (public.min_rolle() = 'trener_pluss' and data->>'type' = 'enkelt' and public.har_lag(data->>'lag')));
create policy "admin og trenere endrer egne" on public.treninger for update to authenticated
  using (public.er_admin() or public.har_lag(data->>'lag'))
  with check (public.er_admin() or public.har_lag(data->>'lag'));
-- trenere sletter bare enkelttreninger; faste treninger avlyses en dag om gangen (avlyst), og endres fremover av admin
create policy "admin og trenere sletter egne enkelttreninger" on public.treninger for delete to authenticated
  using (public.er_admin() or (public.har_lag(data->>'lag') and data->>'type' = 'enkelt'));

-- grupper: alle leser, admin og trener+ (for egne lag) endrer
create policy "alle kan lese" on public.grupper for select to anon, authenticated using (true);
create policy "admin og trener+ endrer egne" on public.grupper for all to authenticated
  using (public.er_admin() or (public.min_rolle() = 'trener_pluss' and public.har_lag(data->>'lag')))
  with check (public.er_admin() or (public.min_rolle() = 'trener_pluss' and public.har_lag(data->>'lag')));

-- lagkamper: alle leser, admin kan importere for hånd (hent_kamper.py bruker service_role)
create policy "alle kan lese" on public.lagkamper for select to anon, authenticated using (true);
create policy "admin endrer" on public.lagkamper for all to authenticated using (public.er_admin()) with check (public.er_admin());

-- dommere: personopplysninger, bare admin og dommeransvarlig ser og endrer dem. Dommeren ser og endrer kontaktinfo for seg selv.
create policy "dommeransvarlig ser og endrer" on public.dommere for all to authenticated
  using (public.er_dommeransvarlig()) with check (public.er_dommeransvarlig());
create policy "dommer ser seg selv" on public.dommere for select to authenticated using (id = public.min_dommer());
create policy "dommer endrer egen kontaktinfo" on public.dommere for update to authenticated
  using (id = public.min_dommer()) with check (id = public.min_dommer());
drop trigger if exists dommere_egen_endring on public.dommere;
create trigger dommere_egen_endring before update on public.dommere for each row execute function public.sjekk_dommer_endring();
-- dommeroppdrag: alle ser kortnavnet på kampen; admin og dommeransvarlig setter opp
create policy "alle kan lese" on public.dommeroppdrag for select to anon, authenticated using (true);
create policy "dommeransvarlig setter opp" on public.dommeroppdrag for all to authenticated
  using (public.er_dommeransvarlig()) with check (public.er_dommeransvarlig());

-- gjest: alle leser. Bare hent_kamper.py (service_role) skriver.
create policy "alle kan lese" on public.gjest for select to anon, authenticated using (true);

-- foresporsler: trenere sender og ser sine egne, admin ser og behandler alle
create policy "admin og avsender leser" on public.foresporsler for select to authenticated
  using (public.er_admin() or public.er_min(data));
create policy "trenere sender" on public.foresporsler for insert to authenticated
  with check (public.er_admin() or (public.er_min(data) and status = 'ny' and public.har_lag(data->>'lag')));
create policy "admin behandler" on public.foresporsler for update to authenticated
  using (public.er_admin()) with check (public.er_admin());
create policy "admin og avsender sletter" on public.foresporsler for delete to authenticated
  using (public.er_admin() or (public.er_min(data) and status = 'ny'));

-- brukere: admin ser og endrer alle, andre ser bare seg selv
create policy "admin og en selv leser" on public.brukere for select to authenticated
  using (public.er_admin() or id = public.min_brukerid());
create policy "admin endrer" on public.brukere for all to authenticated
  using (public.er_admin()) with check (public.er_admin());
-- dommeransvarlig gir og tar bort innlogging for dommere (bare brukere med rollen dommer)
create policy "dommeransvarlig ser dommerbrukere" on public.brukere for select to authenticated
  using (public.er_dommeransvarlig() and rolle = 'dommer');
create policy "dommeransvarlig endrer dommerbrukere" on public.brukere for all to authenticated
  using (public.er_dommeransvarlig() and rolle = 'dommer') with check (public.er_dommeransvarlig() and rolle = 'dommer');

grant select on public.config, public.kamper, public.treninger to anon, authenticated;
grant insert, update, delete on public.config, public.kamper, public.treninger to authenticated;
-- ventende: admin ser og behandler godkjenningslisten. Nye rader legges inn av min_bruker().
create policy "admin behandler" on public.ventende for all to authenticated using (public.er_admin()) with check (public.er_admin());
create policy "en selv leser" on public.ventende for select to authenticated using (id = auth.uid()::text);

grant select, insert, update, delete on public.foresporsler, public.brukere, public.ventende to authenticated;
grant select on public.ventende to anon;
-- anon får lese, men tilgangsreglene over gir dem ingen rader
grant select on public.foresporsler, public.brukere to anon;
grant select on public.grupper, public.lagkamper, public.gjest to anon, authenticated;
-- anon får lese, men tilgangsreglene gir dem ingen rader fra dommere
grant select on public.dommere, public.dommeroppdrag to anon, authenticated;
grant insert, update, delete on public.dommere, public.dommeroppdrag to authenticated;
grant insert, update, delete on public.grupper, public.lagkamper to authenticated;

-- Sanntid: åpne sider oppdateres når noen andre endrer noe
do $$
declare t text;
begin
  if exists (select 1 from pg_publication where pubname = 'supabase_realtime') then
    foreach t in array array['config', 'kamper', 'treninger', 'foresporsler', 'brukere', 'grupper', 'lagkamper', 'gjest', 'dommere', 'dommeroppdrag', 'ventende'] loop
      if not exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = t) then
        execute format('alter publication supabase_realtime add table public.%I', t);
      end if;
    end loop;
  end if;
end $$;
