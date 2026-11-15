#!/usr/bin/env python3
"""Reconcile VESTIGIUM EDA outputs without requiring the large raw ZIP."""
from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parent
S=json.loads((ROOT/'summary.json').read_text())
T=ROOT/'tables'
inv=pd.read_csv(T/'file_inventory.csv')
typ=pd.read_csv(T/'type_distribution.csv')
monthly=pd.read_csv(T/'monthly_type0.csv')
annual=pd.read_csv(T/'annual_type0.csv')
daily=pd.read_csv(T/'daily_type0.csv')
frp=pd.read_csv(T/'frp_type0_stats.csv')
assert len(inv)==48
assert inv.rows_all.sum()==S['all_indonesia_records']==6_355_534
assert inv.rows_type0.sum()==S['type0_total']==5_997_676
assert monthly.type0_count.sum()==S['type0_total']
assert annual.type0_count.sum()==S['type0_total']
assert daily.type0_count.sum()==S['type0_total']
assert frp.n_type0.sum()==S['type0_total']
assert typ.loc[typ.type==0,'count'].sum()==S['type0_total']
assert inv.duplicate_full_rows_within_file.sum()==S['duplicate_full_rows_within_each_file']
assert all((monthly.month.between(1,12)) & monthly.year.between(2000,2025))
assert all(annual.active_months.between(1,12))
assert not annual[['source','year']].duplicated().any()
assert not monthly[['source','year','month']].duplicated().any()
assert not daily[['source','date_utc']].duplicated().any()
assert len(list((ROOT/'figures').glob('*.png')))==17
assert len(list(T.glob('*.csv')))==20
print('PASS: inventory, type0, annual/monthly/daily, FRP, keys, graphics, and coverage.')
