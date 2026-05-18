create table public.gold_prices (
  id uuid primary key default gen_random_uuid(),
  source text not null,
  date date not null,
  purity text not null check (purity in ('24K', '22K', '18K', '9K')),
  price_per_gm integer not null,
  created_dt timestamptz not null,
  created_by text not null,
  modified_dt timestamptz,
  modified_by text,
  constraint gold_prices_source_date_purity_key unique (source, date, purity)
);

create index gold_prices_date_idx on public.gold_prices (date desc);

alter table public.gold_prices enable row level security;

create policy "gold_prices_public_read"
  on public.gold_prices for select
  to anon, authenticated
  using (true);
