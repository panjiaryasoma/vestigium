"""Unit tests for the stable geospatial indexing/aggregation contracts."""
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from pyproj import Transformer
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_advanced import coord_grid,grid_centers,postaggregate_base_025,prepare,agg_per_file

class TestSpatialContract(unittest.TestCase):
    def test_global_grid_stable_with_negative_coordinates(self):
        x,y=coord_grid([113.9218,94.00001],[-2.2145,-11.999],.1)
        lon,lat=grid_centers(x,y,.1)
        self.assertTrue(abs(lon[0]-113.95)<.001)
        self.assertTrue(abs(lat[0]-(-2.25))<.001)
    def test_cannot_infer_burned_area_from_pixel_count(self):
        # the pipeline must preserve a non-causal detection_count name
        frame=pd.DataFrame({'sensor':['MODIS']*2,'year':[2015]*2,'month':[9]*2,'grid_x':[4,5],
                            'grid_y':[3,3],'detection_count':[2,3],
                            'sum_detected_pixel_frp_mw':[5.,8.]})
        out=postaggregate_base_025(frame,.5)
        self.assertEqual(int(out.detection_count.sum()),5)
        self.assertNotIn('burned_area_hectares',out.columns)
    def test_equal_area_grids_conserve_records(self):
        d=pd.DataFrame({'year':[2015]*3,'month':[9]*3,'longitude':[113.9,113.91,113.92],
                        'latitude':[-2.2,-2.21,-2.23],'frp':[2.,3.,5.], 'daynight':['D','D','N']})
        trans=Transformer.from_crs('EPSG:4326','EPSG:6933',always_xy=True)
        p=agg_per_file(d,'equal_area_25km','MODIS',trans)
        self.assertEqual(int(p.detection_count.sum()),3)
        self.assertEqual(int(p.daytime_detections.sum()),2)
        self.assertEqual(int(p.nighttime_detections.sum()),1)
        self.assertAlmostEqual(float(p.sum_detected_pixel_frp_mw.sum()),10.)
    def test_timestamp_validation(self):
        d=pd.DataFrame({'type':[0,0], 'latitude':[-2,-2], 'longitude':[113,113],
           'acq_date':['2015-09-02','2015-09-02'],'acq_time':[930,2460],
           'frp':[2,3], 'daynight':['D','N'], 'satellite':['T','T'],'confidence':[70,70]})
        result=prepare(d,2015)
        self.assertEqual(len(result),1)
        self.assertEqual(result.iloc[0].time_utc,'0930')
    def test_country_filter_excludes_angola_filename(self):
        from run_advanced import sensor_for
        self.assertIsNone(sensor_for('MODIS/modis_2003_Angola.csv'))
        self.assertEqual(sensor_for('MODIS/modis_2003_Indonesia.csv'),'MODIS')

if __name__=='__main__':unittest.main()
