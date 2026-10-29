-- Database roles like Supabase's, for testing the REST backend against a
-- local PostgREST (docker-compose.test.yml).
create role anon nologin;
create role authenticated nologin;
create role service_role nologin bypassrls;
create role authenticator login noinherit password 'authenticator';
grant anon, authenticated, service_role to authenticator;

grant usage on schema public to anon, authenticated, service_role;
-- Like Supabase, the API roles get privileges on new tables by default, so
-- Row Level Security is what actually keeps anon out.
alter default privileges for role postgres in schema public
  grant all on tables to anon, authenticated, service_role;
alter default privileges for role postgres in schema public
  grant all on sequences to anon, authenticated, service_role;
