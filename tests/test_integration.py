"""Synthetic end-to-end smoke test: ZIP -> SQLite -> spatial grids -> ML.

Does not test full-data numeric parity. Uses fabricated pixel records solely for
pipeline-contract validation, never scientific conclusions.
"""
from __future__ import annotations

import csv
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "pipelines"))

from build_pipeline import build
from run_advanced import aggregate
from harmonize import run
from validate_outputs import validate

HEADERS = ["latitude","longitude","acq_date","acq_time","frp",
           "confidence","type","satellite","daynight"]

def csv_bytes(rows):
    dest=io.StringIO()
    w=csv.DictWriter(dest,fieldnames=HEADERS)
    w.writeheader()
    w.writerows(rows)
    return dest.getvalue()

class IntegrationTests(unittest.TestCase):
    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            source=root/"data.zip"
            with zipfile.ZipFile(source,"w",compression=zipfile.ZIP_DEFLATED) as z:
                for y in range(2013,2026):
                    for sensor in ("MODIS","VIIRS_SNPP"):
                        c="70" if sensor=="MODIS" else "n"
                        base={"latitude":"-2.2","longitude":"113.9",
                              "acq_date":f"{y}-09-17","acq_time":"0815",
                              "frp":str(8+(y-2013)),"confidence":c,
                              "type":"0","satellite":sensor,"daynight":"D"}
                        rows=[base]
                        if sensor=="MODIS":
                            rows.append(dict(base,type="2"))
                        z.writestr(f"{sensor}/{sensor.lower()}_{y}_Indonesia.csv",
                                   csv_bytes(rows))
            de=root/"data"/"processed"/"data-engineering"
            build(source,de)
            qa=json.loads((de/"quality_report.json").read_text())
            self.assertEqual(qa["source_files"],26)
            self.assertEqual(qa["accepted_presumed_vegetation_detections"],26)
            self.assertEqual(qa["excluded_non_vegetation_detections"],13)
            geo=root/"data"/"processed"/"geospatial"
            spatial=aggregate(de/"vestigium_hotspots.sqlite",geo)
            self.assertEqual(spatial["accepted_type0"],26)
            self.assertTrue(spatial["all_detectors_reconciled"])
            harm=root/"data"/"processed"/"harmonization"
            evaluation=run(geo/"monthly_equal_area_25km.csv",harm)
            self.assertIn(evaluation["preferred_method"],
                          ("global_ratio","seasonal_ratio","ml_poisson_hgbr"))
            self.assertTrue((harm/"harmonized_calendar_monthly.csv").exists())
            self.assertTrue((harm/"harmonized_calendar_annual.csv").exists())
            self.assertTrue((harm/"evaluation.json").exists())
            self.assertEqual(validate(root)["source_pixels"], 26)

if __name__=="__main__":
    unittest.main()
