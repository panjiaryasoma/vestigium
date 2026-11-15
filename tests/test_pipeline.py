"""Unit-level invariants; does not require the 498 MB NASA input archive."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "pipelines"))

from build_pipeline import normalize, sensor_from_name, source_members
from run_advanced import cell_indices, equal_area_cell

class IngestionTests(unittest.TestCase):
    def setUp(self):
        self.row = {
            "latitude": "-2.24", "longitude": "113.9",
            "type": "0", "frp": "12.4", "acq_date": "2015-09-12",
            "acq_time": "742", "satellite": "Terra", "confidence": "80",
            "daynight":"D"
        }
    def test_family_detection(self):
        self.assertEqual(sensor_from_name("MODIS/modis_2015_Indonesia.csv"),"MODIS")
        self.assertEqual(sensor_from_name("VIIRS_SNPP/viirs_snpp_2015_Indonesia.csv"),"VIIRS_SNPP")
        self.assertEqual(sensor_from_name("VIIRS_NOAA20/viirs_noaa20_2019_Indonesia.csv"),"VIIRS_NOAA20")
    def test_presumed_vegetation_filter(self):
        r=dict(self.row,type="2")
        self.assertIsNone(normalize(r,"MODIS"))
    def test_separate_confidence_and_utc(self):
        v=normalize(self.row,"MODIS")
        self.assertEqual(v[4],"2015-09-12T07:42:00Z")
        self.assertEqual(v[11],80.)
        self.assertIsNone(v[12])
        vv=normalize(dict(self.row,confidence="h"),"VIIRS_SNPP")
        self.assertIsNone(vv[11])
        self.assertEqual(vv[12],"h")
    def test_invalid_coordinates(self):
        with self.assertRaises(ValueError):
            normalize(dict(self.row,latitude="100"),"MODIS")
    def test_reject_negative_frp(self):
        with self.assertRaises(ValueError):
            normalize(dict(self.row,frp="-1"),"MODIS")
    def test_angola_excluded(self):
        import io,zipfile
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,"w") as z:
            z.writestr("MODIS/modis_2015_Indonesia.csv","test\n")
            z.writestr("MODIS/modis_2003_Angola.csv","test\n")
        with zipfile.ZipFile(buf) as z:
            self.assertEqual(source_members(z),["MODIS/modis_2015_Indonesia.csv"])

class SpatialTests(unittest.TestCase):
    def test_geographic_grid_stability(self):
        self.assertEqual(cell_indices(113.9,-2.24,0.25),cell_indices(113.9,-2.24,0.25))
    def test_projected_cell_keys(self):
        x,y=equal_area_cell(113.9,-2.24)
        self.assertIsInstance(x,int)
        self.assertIsInstance(y,int)

class HarmonizationTests(unittest.TestCase):
    def test_holdout_periods_are_disjoint(self):
        import pandas as pd
        from harmonize import fitting_splits
        d=pd.DataFrame({"year":[2012,2013,2021,2022,2023,2025],"v":[1]*6})
        x=fitting_splits(d)
        self.assertEqual(x["train"].year.tolist(),[2013,2021])
        self.assertEqual(x["validation"].year.tolist(),[2022])
        self.assertEqual(x["test"].year.tolist(),[2023,2025])
    def test_no_raw_sensor_sum_as_unique_incidents(self):
        import numpy as np,pandas as pd
        from harmonize import predict_baselines,metric
        d=pd.DataFrame({"modis_count":[2,3],"month":[7,8],"snpp_count":[4,8]})
        p=predict_baselines(d,2.0,{7:2.0,8:2.0})
        self.assertEqual(p["raw_modis"].tolist(),[2,3])
        self.assertTrue(np.all(p["global_ratio"]>=0))
        self.assertGreaterEqual(metric(d,p["global_ratio"])["rmse"],0)

if __name__ == "__main__":
    unittest.main()
