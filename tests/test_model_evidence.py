"""Integrity checks for the archived research evaluation and its SVG figures.

These checks verify report transcription and chart asset integrity. They do NOT
retrain on the NASA FIRMS archive or independently reproduce its historical
test metrics.
"""
from __future__ import annotations

import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EV=ROOT/"docs/harmonization/evidence/archived_metrics_2026-11-15.json"
FIG=ROOT/"docs/harmonization/figures"

class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e=json.loads(EV.read_text(encoding="utf8"))

    def test_archived_provenance_is_explicit(self):
        self.assertIn("archived",self.e["provenance"]["kind"])
        self.assertIn("not_new_model_rerun",self.e["provenance"]["kind"])

    def test_evaluation_years_do_not_overlap(self):
        split=self.e["split"]
        self.assertEqual(split["train"],"2013–2021")
        self.assertEqual(split["validation"],"2022")
        self.assertEqual(split["test"],"2023–2025")
        self.assertEqual(split["test_n"],17291)

    def test_candidate_selection_uses_validation_rmse(self):
        rows=self.e["metrics"]["validation_2022"]
        calibrations=[r for r in rows if r["method"]!="raw_modis"]
        best=min(calibrations,key=lambda r:r["rmse"])
        self.assertEqual(best["method"],self.e["split"]["preferred_candidate"])
        self.assertEqual(best["method"],"ml_poisson_hgbr")

    def test_test_mae_and_rmse_are_distinct_findings(self):
        rows={x["method"]:x for x in self.e["metrics"]["temporal_holdout_2023_2025"]}
        self.assertLess(rows["ml_poisson_hgbr"]["mae"],rows["seasonal_ratio"]["mae"])
        self.assertGreater(rows["ml_poisson_hgbr"]["rmse"],rows["global_ratio"]["rmse"])
        self.assertEqual(rows["ml_poisson_hgbr"]["mae"],10.24)
        self.assertEqual(rows["global_ratio"]["rmse"],21.87)

    def test_reference_count_and_regional_counts(self):
        e=self.e["metrics"]
        segments=e["regional_holdout"]
        self.assertEqual(sum(x["observed"] for x in segments),
                         e["observed_test_reference_count_modis_positive_grid_months"])
        self.assertEqual(sum(x["predicted"] for x in segments),
                         e["selected_model_estimated_count_same_scope"])
        ref=e["observed_test_reference_count_modis_positive_grid_months"]
        predicted=e["selected_model_estimated_count_same_scope"]
        self.assertAlmostEqual((predicted-ref)/ref*100,11.25,places=1)

    def test_coverage_shares_reconcile(self):
        v=self.e["metrics"]["overlap_coverage"]
        self.assertAlmostEqual(
            v["snpp_pixels_with_modis_positive_grid_month_share_2013_2025_pct"]+
            v["snpp_pixels_without_modis_positive_grid_month_share_2013_2025_pct"],
            100,places=5)

    def test_svg_figures_are_valid(self):
        expected=["holdout_mae.svg","holdout_rmse.svg","validation_rmse.svg","regional_bias.svg",
                  "viirs_detection_gap.svg","test_volume.svg"]
        for name in expected:
            with self.subTest(name=name):
                root=ET.parse(FIG/name).getroot()
                self.assertEqual(root.tag,"{http://www.w3.org/2000/svg}svg")
                self.assertIsNotNone(root.find("{http://www.w3.org/2000/svg}title"))
                self.assertIsNotNone(root.find("{http://www.w3.org/2000/svg}desc"))

if __name__=="__main__":
    unittest.main()
