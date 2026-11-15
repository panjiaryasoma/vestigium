"""Build a transparent, unharmonized daily baseline from user-provided NASA FIRMS CSVs.

Run: python build_vestigium_daily_baseline.py data.zip output.csv
Produces daily counts independently for each source, for type=0 presumed vegetation fire.
acq_date is UTC; missing days in the output mean no records found, not confirmed zero fires.
DO NOT sum satellite counts into unique real-world fire events.
"""
import csv, sys, zipfile, collections, pathlib, io
INPUT = pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '/mnt/data/data.zip')
OUTPUT = pathlib.Path(sys.argv[2] if len(sys.argv)>2 else '/mnt/data/vestigium_daily_sensor_baseline.csv')
metrics=collections.defaultdict(lambda:[0,0.,0,0])
with zipfile.ZipFile(INPUT) as z:
 for name in z.namelist():
  if not name.endswith('_Indonesia.csv'):continue
  sensor = name.split('/')[0]
  with z.open(name) as f:
   rd=csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig',newline=''))
   for row in rd:
    if row.get('type')!='0':continue # presumed vegetation fire, NOT certified forest fire
    key=(row['acq_date'],sensor)
    m=metrics[key]
    m[0]+=1;m[1]+=float(row['frp'])
    if row.get('daynight')=='D':m[2]+=1
    elif row.get('daynight')=='N':m[3]+=1
with OUTPUT.open('w',newline='',encoding='utf8') as f:
 w=csv.writer(f)
 w.writerow(['acq_date_utc','source','type0_detection_count','frp_sum_mw','frp_mean_mw','daytime_detections','nighttime_detections'])
 for (dt,sensor),m in sorted(metrics.items()):
  w.writerow([dt,sensor,m[0],f'{m[1]:.2f}',f'{m[1]/m[0]:.4f}',m[2],m[3]])
print('OUTPUT:',OUTPUT,'rows:',len(metrics),'detections:',sum(x[0] for x in metrics.values()))