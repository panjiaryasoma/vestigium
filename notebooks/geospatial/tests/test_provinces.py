import sys
import unittest
from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from assign_provinces_optional import match_province

class TestProvinceJoining(unittest.TestCase):
    def test_exact_point_in_polygon_join(self):
        polygons=gpd.GeoDataFrame({'shapeName':['A','B']},geometry=[box(112,-3,114,-1),box(115,-3,118,1)],crs='EPSG:4326')
        points=pd.DataFrame({'id':[1,2,3],'latitude':[-2,-2,4],'longitude':[113,117,118]})
        result=match_province(points,polygons,'shapeName').set_index('id')
        self.assertEqual(result.loc[1,'province_name'],'A')
        self.assertEqual(result.loc[2,'province_name'],'B')
        self.assertEqual(result.loc[3,'spatial_join_status'],'unmatched')

if __name__=='__main__':unittest.main()
