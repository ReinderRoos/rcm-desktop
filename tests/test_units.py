"""Tests voor units.py — tijdseenheden en conversies."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rcm_core.units import TimeDuration, TimeUnit, HOURS_PER_YEAR


class TestTimeDuration:
    def test_hours_to_hours(self):
        assert TimeDuration(4.0, TimeUnit.HOURS).to_hours() == 4.0

    def test_days_to_hours(self):
        assert TimeDuration(1.0, TimeUnit.DAYS).to_hours() == 24.0

    def test_weeks_to_hours(self):
        assert TimeDuration(1.0, TimeUnit.WEEKS).to_hours() == 168.0

    def test_months_to_hours(self):
        assert TimeDuration(1.0, TimeUnit.MONTHS).to_hours() == 730.0

    def test_years_to_hours(self):
        assert TimeDuration(1.0, TimeUnit.YEARS).to_hours() == 8760.0

    def test_fractional_days(self):
        assert TimeDuration(0.5, TimeUnit.DAYS).to_hours() == 12.0

    def test_to_years_from_hours(self):
        result = TimeDuration(8760.0, TimeUnit.HOURS).to_years()
        assert abs(result - 1.0) < 1e-10

    def test_to_years_from_days(self):
        result = TimeDuration(365.0, TimeUnit.DAYS).to_years()
        assert abs(result - 1.0) < 1e-10

    def test_roundtrip_dict(self):
        d = TimeDuration(8.0, TimeUnit.DAYS)
        assert TimeDuration.from_dict(d.to_dict()) == d

    def test_zero_duration(self):
        assert TimeDuration(0.0, TimeUnit.HOURS).to_hours() == 0.0
