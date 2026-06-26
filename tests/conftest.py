import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture
def sample_crop():
    """Shared fixture providing a sample crop array for testing."""
    import numpy as np
    return np.zeros((100, 100, 3), dtype=np.uint8)
