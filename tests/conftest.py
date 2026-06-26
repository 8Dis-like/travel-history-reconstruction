import pytest

@pytest.fixture
def sample_crop():
    """Shared fixture providing a sample crop array for testing."""
    import numpy as np
    return np.zeros((100, 100, 3), dtype=np.uint8)
