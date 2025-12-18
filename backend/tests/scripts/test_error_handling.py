"""
test_error_handling.py

Simple test script to demonstrate error handling in the analyzer pipeline.

Run with:
    python test_error_handling.py
"""

from pathlib import Path
from analyzer.logging_config import setup_logging
from analyzer.run_pipeline import run_full_analysis


def test_valid_audio():
    """Test with a valid audio file."""
    print("\n" + "="*60)
    print("TEST 1: Valid audio file")
    print("="*60)

    audio_path = Path("test.wav")
    if not audio_path.exists():
        print(f"SKIPPED: {audio_path} not found")
        return

    payload = {
        "audio_url": str(audio_path),
        "language": "en",
        "talk_type": "presentation",
        "audience_type": "general",
        "requested_metrics": ["pace", "pause_quality"],
        "user_metadata": {},
    }

    try:
        result = run_full_analysis(
            job_id="test-001",
            audio_path=audio_path,
            raw_input_payload=payload,
        )
        print(f"[PASS] SUCCESS: Analysis completed")
        print(f"  - Status: {result['status']}")
        print(f"  - Duration: {result['input']['duration_sec']:.2f}s")
        print(f"  - Words: {len(result.get('transcript', {}).get('full_text', '').split())}")
        print(f"  - Metrics: {list(result.get('metrics', {}).keys())}")
    except Exception as e:
        print(f"[FAIL] FAILED: {e}")


def test_nonexistent_file():
    """Test with non-existent audio file."""
    print("\n" + "="*60)
    print("TEST 2: Non-existent file")
    print("="*60)

    audio_path = Path("does_not_exist.wav")

    payload = {
        "audio_url": str(audio_path),
        "language": "en",
        "talk_type": "presentation",
        "audience_type": "general",
        "requested_metrics": ["pace"],
        "user_metadata": {},
    }

    try:
        result = run_full_analysis(
            job_id="test-002",
            audio_path=audio_path,
            raw_input_payload=payload,
        )
        print(f"[FAIL] UNEXPECTED: Should have raised ValueError")
    except ValueError as e:
        print(f"[PASS] EXPECTED ERROR CAUGHT: {e}")
    except Exception as e:
        print(f"[FAIL] WRONG ERROR TYPE: {type(e).__name__}: {e}")


def test_invalid_payload():
    """Test with invalid input payload."""
    print("\n" + "="*60)
    print("TEST 3: Invalid payload (missing required field)")
    print("="*60)

    audio_path = Path("test.wav")
    if not audio_path.exists():
        print(f"SKIPPED: {audio_path} not found")
        return

    # Missing required 'audio_url' field
    payload = {
        "language": "en",
        "talk_type": "presentation",
    }

    try:
        result = run_full_analysis(
            job_id="test-003",
            audio_path=audio_path,
            raw_input_payload=payload,
        )
        print(f"[FAIL] UNEXPECTED: Should have raised ValueError")
    except ValueError as e:
        print(f"[PASS] EXPECTED ERROR CAUGHT: {e}")
    except Exception as e:
        print(f"[FAIL] WRONG ERROR TYPE: {type(e).__name__}: {e}")


def test_empty_payload():
    """Test with empty payload."""
    print("\n" + "="*60)
    print("TEST 4: Empty payload")
    print("="*60)

    audio_path = Path("test.wav")
    if not audio_path.exists():
        print(f"SKIPPED: {audio_path} not found")
        return

    payload = {}

    try:
        result = run_full_analysis(
            job_id="test-004",
            audio_path=audio_path,
            raw_input_payload=payload,
        )
        print(f"[FAIL] UNEXPECTED: Should have raised ValueError")
    except ValueError as e:
        print(f"[PASS] EXPECTED ERROR CAUGHT: {e}")
    except Exception as e:
        print(f"[FAIL] WRONG ERROR TYPE: {type(e).__name__}: {e}")


def test_directory_instead_of_file():
    """Test with directory path instead of file."""
    print("\n" + "="*60)
    print("TEST 5: Directory instead of file")
    print("="*60)

    audio_path = Path("analyzer")  # Directory, not file

    payload = {
        "audio_url": "test",
        "language": "en",
        "talk_type": "presentation",
        "audience_type": "general",
        "requested_metrics": ["pace"],
        "user_metadata": {},
    }

    try:
        result = run_full_analysis(
            job_id="test-005",
            audio_path=audio_path,
            raw_input_payload=payload,
        )
        print(f"[FAIL] UNEXPECTED: Should have raised ValueError")
    except ValueError as e:
        print(f"[PASS] EXPECTED ERROR CAUGHT: {e}")
    except Exception as e:
        print(f"[FAIL] WRONG ERROR TYPE: {type(e).__name__}: {e}")


def main():
    """Run all error handling tests."""
    print("\n" + "#"*60)
    print("# ERROR HANDLING TESTS")
    print("#"*60)

    # Setup logging with INFO level to see what's happening
    setup_logging(level="INFO")

    # Run tests
    test_valid_audio()
    test_nonexistent_file()
    test_invalid_payload()
    test_empty_payload()
    test_directory_instead_of_file()

    print("\n" + "#"*60)
    print("# TESTS COMPLETED")
    print("#"*60 + "\n")


if __name__ == "__main__":
    main()
