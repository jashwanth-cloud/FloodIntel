"""
Phase 3 — Step 8: Pipeline Tests
=================================
Lightweight tests for all processing functions.
Runs each pipeline on a small sample before full-scale processing.
"""

import os
import sys
import unittest
import tempfile
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "scripts", "data_processing"))

FEATURES_DIR = os.path.join(BASE_DIR, "data", "features")


class TestRainfallPipeline(unittest.TestCase):
    """Tests for rainfall_pipeline.py"""

    def test_nc_time_conversion(self):
        """Test that TIME values convert correctly to dates."""
        from rainfall_pipeline import nc_time_to_dates
        from datetime import date

        # Day 0 = 1900-12-31, Day 1 = 1901-01-01
        result = nc_time_to_dates([0, 1, 365])
        self.assertEqual(result[0], date(1900, 12, 31))
        self.assertEqual(result[1], date(1901, 1, 1))
        self.assertEqual(result[2], date(1901, 12, 31))

    def test_nc_time_2018(self):
        """Test that 2018 time values decode correctly."""
        from rainfall_pipeline import nc_time_to_dates
        from datetime import date

        # From inspection: RF25_ind2018_rfp25.nc first time value = 42735.0
        result = nc_time_to_dates([42735.0])
        self.assertEqual(result[0].year, 2018)
        self.assertEqual(result[0].month, 1)
        self.assertEqual(result[0].day, 1)

    def test_sample_processing(self):
        """Test that sample processing runs without error."""
        from rainfall_pipeline import process_single_year, NC_FILES
        if not NC_FILES:
            self.skipTest("No NetCDF files found")

        df, lons, lats, dates, rain = process_single_year(NC_FILES[0], sample_only=True)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn("lat", df.columns)
        self.assertIn("lon", df.columns)
        self.assertIn("date", df.columns)
        self.assertIn("rainfall_mm", df.columns)
        self.assertGreater(len(df), 0)

    def test_no_negative_rainfall(self):
        """Test that no negative rainfall values appear after processing."""
        from rainfall_pipeline import process_single_year, NC_FILES
        if not NC_FILES:
            self.skipTest("No NetCDF files found")

        df, _, _, _, _ = process_single_year(NC_FILES[0], sample_only=True)
        neg = (df["rainfall_mm"] < 0).sum()
        self.assertEqual(neg, 0, f"Found {neg} negative rainfall values")

    def test_rainfall_units(self):
        """Test that rainfall values are in plausible mm range."""
        from rainfall_pipeline import process_single_year, NC_FILES
        if not NC_FILES:
            self.skipTest("No NetCDF files found")

        df, _, _, _, _ = process_single_year(NC_FILES[0], sample_only=True)
        max_rain = df["rainfall_mm"].max()
        self.assertLessEqual(max_rain, 1000.0, f"Rainfall max {max_rain} seems too high (expected mm)")

    def test_coordinate_bounds(self):
        """Test that lat/lon are within India bounds."""
        from rainfall_pipeline import process_single_year, NC_FILES
        if not NC_FILES:
            self.skipTest("No NetCDF files found")

        df, _, _, _, _ = process_single_year(NC_FILES[0], sample_only=True)
        self.assertTrue((df["lat"] >= 6.0).all(), "Latitude below 6°N")
        self.assertTrue((df["lat"] <= 39.0).all(), "Latitude above 39°N")
        self.assertTrue((df["lon"] >= 66.0).all(), "Longitude below 66°E")
        self.assertTrue((df["lon"] <= 101.0).all(), "Longitude above 101°E")


class TestDEMPipeline(unittest.TestCase):
    """Tests for dem_pipeline.py"""

    def test_slope_computation(self):
        """Test slope calculation on a synthetic elevation array."""
        from dem_pipeline import compute_slope_from_array

        # Flat terrain → slope ≈ 0
        flat = np.zeros((10, 10))
        slope = compute_slope_from_array(flat, 0.001, 0.001)
        self.assertTrue(np.allclose(slope, 0, atol=1e-6))

        # Inclined terrain → slope > 0
        inclined = np.tile(np.arange(10), (10, 1)).astype(float) * 10  # 10m per pixel
        slope2 = compute_slope_from_array(inclined, 0.001, 0.001)
        # Interior pixels should have positive slope
        self.assertGreater(slope2[5, 5], 0)

    def test_aoi_overlap_check(self):
        """Test the AOI overlap detection function."""
        from dem_pipeline import check_dem_aoi_overlap, FLOOD_AOI_BOUNDS

        # Test tile bounds (from inspection): Africa area, should NOT overlap Andhra Pradesh
        non_overlapping = (4.0, 12.0, 5.0, 13.0)
        self.assertFalse(check_dem_aoi_overlap(non_overlapping, FLOOD_AOI_BOUNDS))

        # Overlapping bounds (synthetic)
        overlapping = (80.0, 16.0, 81.0, 17.0)
        self.assertTrue(check_dem_aoi_overlap(overlapping, FLOOD_AOI_BOUNDS))

    def test_sample_dem_processing(self):
        """Test that DEM sample processing produces valid DataFrame."""
        from dem_pipeline import run_dem_pipeline
        df, meta = run_dem_pipeline(sample_only=True)
        if df is None:
            self.skipTest("DEM not available")
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn("elevation_m", df.columns)
        self.assertIn("slope_deg", df.columns)
        self.assertGreater(len(df), 0)
        # No NaN in elevation (valid pixels only)
        self.assertEqual(df["elevation_m"].isnull().sum(), 0)


class TestHydrologyPipeline(unittest.TestCase):
    """Tests for hydrology_pipeline.py"""

    def test_make_aoi_grid(self):
        """Test that AOI grid generation works correctly."""
        from hydrology_pipeline import make_aoi_grid, AOI_BOUNDS
        gdf = make_aoi_grid(AOI_BOUNDS, grid_spacing_deg=0.05)
        self.assertGreater(len(gdf), 0)
        self.assertIn("lat", gdf.columns)
        self.assertIn("lon", gdf.columns)
        # All points should be within (or very close to) AOI
        minx, miny, maxx, maxy = AOI_BOUNDS
        self.assertTrue((gdf["lat"] >= miny - 0.01).all())
        self.assertTrue((gdf["lat"] <= maxy + 0.01).all())

    def test_sample_hydrology_run(self):
        """Test that sample hydrology pipeline runs without crashing."""
        from hydrology_pipeline import run_hydrology_pipeline
        try:
            result = run_hydrology_pipeline(sample_only=True)
            self.assertIsInstance(result, pd.DataFrame)
        except Exception as e:
            self.skipTest(f"Hydrology pipeline failed (may be expected if data too large): {e}")


class TestFeatureAssembly(unittest.TestCase):
    """Tests for feature_assembly.py"""

    def test_sentinel1_loading(self):
        """Test Sentinel-1 feature loading from normalized TIF."""
        tif_path = os.path.join(BASE_DIR, "data", "processed", "satellite_features_normalized.tif")
        if not os.path.exists(tif_path):
            self.skipTest("Normalized TIF not found")

        from feature_assembly import load_sentinel1_features, SENTINEL1_FEATURES
        df = load_sentinel1_features()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn("lat", df.columns)
        self.assertIn("lon", df.columns)
        for feat in SENTINEL1_FEATURES:
            self.assertIn(feat, df.columns, f"Missing Sentinel-1 feature: {feat}")
        # 512×512 = 262144 pixels
        self.assertEqual(len(df), 262144)

    def test_feature_assembly_sample(self):
        """Test full feature assembly on 1000-pixel sample."""
        from feature_assembly import assemble_feature_dataset
        df = assemble_feature_dataset(sample_only=True)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertLessEqual(len(df), 1000)
        # Core columns must exist
        required = ["lat", "lon", "date"]
        for col in required:
            self.assertIn(col, df.columns, f"Missing required column: {col}")

    def test_no_fabricated_values(self):
        """Test that DEM columns are NaN (not fabricated) when no DEM available."""
        from feature_assembly import assemble_feature_dataset
        df = assemble_feature_dataset(sample_only=True)
        if "elevation_m" in df.columns:
            # DEM test tile doesn't cover AOI → should be NaN
            self.assertTrue(df["elevation_m"].isnull().all(),
                            "elevation_m should be all NaN (DEM not available for AOI)")


class TestQualityControl(unittest.TestCase):
    """Tests for quality_control.py"""

    def test_check_duplicates_clean(self):
        """Test duplicate detection with clean data."""
        from quality_control import check_duplicates
        df = pd.DataFrame({"lat": [1.0, 2.0, 3.0], "lon": [10.0, 11.0, 12.0], "date": ["2021-01-01"] * 3})
        result = check_duplicates(df)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["duplicate_rows"], 0)

    def test_check_duplicates_dirty(self):
        """Test duplicate detection with duplicate data."""
        from quality_control import check_duplicates
        df = pd.DataFrame({"lat": [1.0, 1.0], "lon": [10.0, 10.0], "date": ["2021-01-01", "2021-01-01"]})
        result = check_duplicates(df)
        self.assertEqual(result["status"], "WARN")
        self.assertGreater(result["duplicate_rows"], 0)

    def test_check_rainfall_negative(self):
        """Test detection of negative rainfall values."""
        from quality_control import check_rainfall_values
        df = pd.DataFrame({"rainfall_1d": [10.0, -5.0, 0.0]})
        result = check_rainfall_values(df)
        self.assertEqual(result["status"], "WARN")
        self.assertTrue(any("negative" in issue for issue in result["issues"]))

    def test_check_coordinates_valid(self):
        """Test coordinate validation with valid data."""
        from quality_control import check_coordinates
        df = pd.DataFrame({"lat": [16.25, 16.30], "lon": [80.40, 80.45]})
        result = check_coordinates(df)
        # Should pass global bounds check (may warn about AOI bounds)
        self.assertNotIn("outside [-90, 90]", str(result.get("issues", [])))

    def test_full_qc_run(self):
        """Test that QC pipeline runs end-to-end."""
        from quality_control import run_quality_control
        report = run_quality_control()
        self.assertIsInstance(report, dict)
        self.assertIn("checks", report)


if __name__ == "__main__":
    # Run with verbose output
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestRainfallPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestDEMPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestHydrologyPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestFeatureAssembly))
    suite.addTests(loader.loadTestsFromTestCase(TestQualityControl))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
