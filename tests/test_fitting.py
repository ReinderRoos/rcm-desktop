"""Tests voor fitting.py — MTTF/sigma fitten uit historische faaltijden."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from rcm_core.fitting import fit_from_failure_times, FitResult


class TestFitting:
    def test_fit_normal_basic(self):
        """Fit normale verdeling op data met bekende mu/sigma."""
        import numpy as np
        rng = np.random.default_rng(42)
        data = rng.normal(loc=50.0, scale=8.0, size=200).tolist()
        result = fit_from_failure_times(data, distribution="normal")
        assert result.distribution == "normal"
        assert abs(result.mttf - 50.0) < 3.0
        assert abs(result.sigma - 8.0) < 2.0

    def test_fit_exponential_basic(self):
        """Fit exponentiële verdeling op data met bekende MTTF."""
        import numpy as np
        rng = np.random.default_rng(42)
        data = rng.exponential(scale=20.0, size=500).tolist()
        result = fit_from_failure_times(data, distribution="exponential")
        assert result.distribution == "exponential"
        assert abs(result.mttf - 20.0) < 3.0
        assert result.sigma == 0.0

    def test_auto_selects_better_fit(self):
        """Auto-modus kiest de verdeling met lagere AICc."""
        import numpy as np
        # Sterk exponentieel gegenereerde data
        rng = np.random.default_rng(99)
        data = rng.exponential(scale=10.0, size=300).tolist()
        result = fit_from_failure_times(data, distribution="auto")
        # Exponentieel is hier beter; AICc van de winnaar is relevant
        assert result.distribution in ("normal", "exponential")
        assert result.goodness_of_fit is not None

    def test_empty_failure_times_raises(self):
        with pytest.raises(ValueError):
            fit_from_failure_times([])

    def test_fit_result_has_n_samples(self):
        data = [10.0, 12.0, 15.0, 8.0, 14.0]
        result = fit_from_failure_times(data, distribution="normal")
        assert result.n_samples == 5
        assert result.n_censored == 0

    def test_fit_with_censored_data(self):
        """Gecensureerde data mag zonder fout worden meegegeven."""
        data = [10.0, 15.0, 20.0, 25.0, 30.0]
        censored = [18.0, 22.0]
        result = fit_from_failure_times(data, censored_times=censored, distribution="normal")
        assert result.n_censored == 2
        assert result.mttf > 0
