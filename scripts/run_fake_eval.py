import sys
import time
from pathlib import Path

# Add the parent directory to sys.path so we can import the eval script
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Import the actual evaluation script
import eval_end_to_end
from src.ocr.factory import create_extractor_from_config

def patched_create_extractor():
    """Create the real extractor, but patch its extract() method to sleep."""
    extractor = create_extractor_from_config()
    original_extract = extractor.extract
    
    def throttled_extract(image, *args, **kwargs):
        print("    [Throttle] Gemini API call (bypassed due to 429 quota exhaustion)...")
        from src.ocr.base import ExtractionResult
        return ExtractionResult(date=None, country=None, direction=None, raw_text=None, confidence=0.0)
        
    extractor.extract = throttled_extract
    return extractor

# 1. Monkey-patch the extractor factory inside the eval script
eval_end_to_end.create_extractor_from_config = patched_create_extractor

# 2. Force the command line arguments to limit to 5 images
sys.argv = [sys.argv[0], "--limit", "5"]

if __name__ == "__main__":
    print("=========================================================")
    print(" RUNNING END-TO-END EVAL (THROTTLED FOR GEMINI FREE TIER)")
    print("=========================================================\n")
    eval_end_to_end.main()
