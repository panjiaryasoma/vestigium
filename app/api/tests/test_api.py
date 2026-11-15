import sys
from pathlib import Path

from fastapi.testclient import TestClient

# Allow both `pytest` at repository root and tests from app/api.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main
from main import app

client = TestClient(app)


def test_health_and_metadata():
    assert client.get('/api/health').status_code == 200
    r = client.get('/api/v1/meta').json()
    assert r['time_zone'] == 'UTC'
    assert r['observation_unit'] == 'satellite_thermal_pixel_detection_not_unique_fire_event'


def test_demo_points_and_filters():
    response = client.get('/api/v1/hotspots', params={'year': 2015, 'month': 9, 'sensor': 'MODIS'})
    assert response.status_code == 200
    data = response.json()
    assert data['type'] == 'FeatureCollection'
    assert all(f['properties']['sensor'] == 'MODIS' for f in data['features'])
    assert all(len(f['geometry']['coordinates']) == 2 for f in data['features'])


def test_invalid_bbox_rejected():
    assert client.get('/api/v1/hotspots', params={'bbox': 'hello'}).status_code == 422
    assert client.get('/api/v1/hotspots', params={'bbox': '130,10,100,-5'}).status_code == 422
    assert client.get('/api/v1/hotspots', params={'region': 'Atlantis'}).status_code == 422


def test_temporal_and_analysis():
    r = client.get('/api/v1/temporal', params={'year': 2015, 'grain': 'monthly'})
    assert r.status_code == 200
    assert len(r.json()['data']) <= 12
    findings = client.get('/api/v1/analysis', params={'year': 2015}).json()['findings']
    assert len(findings) == 12


def test_evaluation_is_provenance_labelled():
    r = client.get('/api/v1/evaluation').json()
    assert 'archived' in r['kind']
    assert len(r['metrics']) == 4


def test_calendar_never_fakes_calibration():
    r = client.get('/api/v1/calendar', params={'year': 2015}).json()
    if not r['available']:
        assert r['data'] == []


def test_repo_pipeline_default_paths():
    from pathlib import Path
    root = Path(main.__file__).resolve().parents[2]
    assert main.REPO_ROOT == root
    # Only verify location mapping when no explicit environment overrides are set.
    assert main.source_path("VESTIGIUM_TEST_UNSET_VAR", "data/processed/data-engineering/vestigium_hotspots.sqlite") == root / "data/processed/data-engineering/vestigium_hotspots.sqlite"


def test_live_sqlite_and_harmonization_integration(monkeypatch, tmp_path):
    import sqlite3
    db = tmp_path / "hotspots.sqlite"
    with sqlite3.connect(db) as conn:
        conn.execute("""CREATE TABLE hotspots (
            id INTEGER PRIMARY KEY, longitude REAL, latitude REAL, date_utc TEXT,
            timestamp_utc TEXT, sensor TEXT, satellite TEXT, frp_mw REAL,
            confidence_modis_pct REAL, confidence_viirs_label TEXT,
            year INTEGER, month INTEGER)""")
        conn.execute("""INSERT INTO hotspots VALUES
            (1, 113.9218, -2.2145, '2015-09-12', '2015-09-12T07:32:00Z',
             'MODIS', 'Terra', 42.8, 85, NULL, 2015, 9)""")
    calendar = tmp_path / "harmonized_calendar_monthly.csv"
    calendar.write_text("year,month,MODIS,VIIRS_SNPP,VIIRS_NOAA20,modis_reference_equivalent_proxy,calendar_display_estimate,calendar_method\n2015,9,1,2,,3.2,2,observed_viirs_snpp\n", encoding="utf-8")
    monkeypatch.setattr(main, 'DB', db)
    monkeypatch.setattr(main, 'CALENDAR', calendar)
    monkeypatch.setattr(main, 'MONTHLY', tmp_path / 'missing_monthly.csv')
    monkeypatch.setattr(main, 'MODE', 'live')
    main.monthly_rows.cache_clear()
    main.calendar_rows.cache_clear()
    try:
        payload = client.get('/api/v1/hotspots', params={'year': 2015, 'month': 9}).json()
        assert len(payload['features']) == 1
        record = payload['features'][0]['properties']
        assert record['sensor'] == 'MODIS'
        assert record['confidence_modis_pct'] == 85
        assert record['synthetic'] is False
        assert client.get('/api/v1/meta').json()['synthetic'] is False
        assert client.get('/api/v1/temporal', params={'year': 2015}).json()['data'][0]['count'] == 1
        cal = client.get('/api/v1/calendar', params={'year': 2015}).json()
        assert cal['available'] is True
        assert cal['data'][0]['calendar_method'] == 'observed_viirs_snpp'
    finally:
        main.monthly_rows.cache_clear()
        main.calendar_rows.cache_clear()


def test_demo_does_not_mix_real_calendar(monkeypatch, tmp_path):
    calendar = tmp_path / 'stale_calendar.csv'
    calendar.write_text('year,month,MODIS\n2015,9,123\n', encoding='utf-8')
    monkeypatch.setattr(main, 'MODE', 'demo')
    monkeypatch.setattr(main, 'CALENDAR', calendar)
    main.calendar_rows.cache_clear()
    try:
        assert client.get('/api/v1/calendar', params={'year': 2015}).json()['available'] is False
        assert client.get('/api/v1/meta').json()['has_harmonization_calendar'] is False
    finally:
        main.calendar_rows.cache_clear()
