"""
test_fillers.py

Test script to verify fillers metric detection and integration.
"""

from pathlib import Path
from analyzer.logging_config import setup_logging
from analyzer.run_pipeline import run_full_analysis
from analyzer.metrics.fillers import compute_fillers_metric
import json


def test_fillers_unit():
    """Unit test the fillers metric with synthetic data."""
    print("\n" + "="*60)
    print("TEST 1: Fillers Metric Unit Test")
    print("="*60)

    # Test case 1: No fillers
    words = [
        {"text": "Hello", "start": 0.0, "end": 0.5},
        {"text": "world", "start": 0.6, "end": 1.0},
        {"text": "this", "start": 1.1, "end": 1.4},
        {"text": "is", "start": 1.5, "end": 1.7},
        {"text": "clean", "start": 1.8, "end": 2.2},
    ]
    duration_sec = 2.5

    result = compute_fillers_metric(words, duration_sec)
    print(f"\n1. Clean speech (no fillers):")
    print(f"   Score: {result['score_0_100']}/100")
    print(f"   Label: {result['label']}")
    print(f"   Total fillers: {result['details']['total_fillers']}")
    print(f"   Rate: {result['details']['filler_rate_per_min']:.2f}/min")
    assert result['label'] == 'low_filler_rate'
    assert result['details']['total_fillers'] == 0

    # Test case 2: Low filler rate
    words = [
        {"text": "um", "start": 0.0, "end": 0.3},
        {"text": "hello", "start": 0.4, "end": 0.8},
        {"text": "I", "start": 0.9, "end": 1.0},
        {"text": "think", "start": 1.1, "end": 1.4},
        {"text": "like", "start": 1.5, "end": 1.8},
        {"text": "this", "start": 1.9, "end": 2.2},
        {"text": "is", "start": 2.3, "end": 2.5},
        {"text": "good", "start": 2.6, "end": 3.0},
    ]
    duration_sec = 60.0  # 1 minute

    result = compute_fillers_metric(words, duration_sec)
    print(f"\n2. Low filler rate (2 fillers in 1 min):")
    print(f"   Score: {result['score_0_100']}/100")
    print(f"   Label: {result['label']}")
    print(f"   Total fillers: {result['details']['total_fillers']}")
    print(f"   Rate: {result['details']['filler_rate_per_min']:.2f}/min")
    print(f"   Top fillers: {result['details']['top_fillers']}")
    assert result['label'] == 'low_filler_rate'
    assert result['details']['total_fillers'] == 2

    # Test case 3: High filler rate
    words = [
        {"text": "um", "start": 0.0, "end": 0.3},
        {"text": "uh", "start": 0.4, "end": 0.6},
        {"text": "like", "start": 0.7, "end": 1.0},
        {"text": "hello", "start": 1.1, "end": 1.4},  # not a filler
        {"text": "um", "start": 1.5, "end": 1.7},
        {"text": "actually", "start": 1.8, "end": 2.2},
        {"text": "uh", "start": 2.3, "end": 2.5},
        {"text": "basically", "start": 2.6, "end": 3.0},
        {"text": "like", "start": 3.1, "end": 3.3},
        {"text": "um", "start": 3.4, "end": 3.6},
    ]
    duration_sec = 60.0  # 9 fillers in 1 minute = 9/min

    result = compute_fillers_metric(words, duration_sec)
    print(f"\n3. High filler rate (9 fillers in 1 min):")
    print(f"   Score: {result['score_0_100']}/100")
    print(f"   Label: {result['label']}")
    print(f"   Total fillers: {result['details']['total_fillers']}")
    print(f"   Rate: {result['details']['filler_rate_per_min']:.2f}/min")
    print(f"   Top fillers: {result['details']['top_fillers']}")
    assert result['label'] == 'high_filler_rate'
    assert result['details']['total_fillers'] == 9

    # Test case 4: Abstention
    result = compute_fillers_metric([], 0.0)
    print(f"\n4. Empty input (should abstain):")
    print(f"   Score: {result['score_0_100']}")
    print(f"   Label: {result['label']}")
    print(f"   Abstained: {result['abstained']}")
    print(f"   Reason: {result['details'].get('reason')}")
    assert result['abstained'] == True

    print("\n[PASS] All unit tests passed!")


def test_fillers_integration():
    """Test fillers metric with real audio file."""
    print("\n" + "="*60)
    print("TEST 2: Fillers Integration Test")
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
        "requested_metrics": ["fillers"],
        "user_metadata": {},
    }

    try:
        result = run_full_analysis(
            job_id="test-fillers",
            audio_path=audio_path,
            raw_input_payload=payload,
        )

        print(f"\n[SUCCESS] Analysis completed")
        print(f"Duration: {result['input']['duration_sec']:.2f}s")

        # Check fillers metric
        fillers = result['metrics'].get('fillers', {})
        print(f"\nFillers Metric:")
        print(f"  - Score: {fillers.get('score_0_100')}/100")
        print(f"  - Label: {fillers.get('label')}")
        print(f"  - Confidence: {fillers.get('confidence')}")

        if not fillers.get('abstained'):
            details = fillers.get('details', {})
            print(f"\nFiller Details:")
            print(f"  - Total fillers: {details.get('total_fillers')}")
            print(f"  - Rate: {details.get('filler_rate_per_min'):.2f}/min")

            top_fillers = details.get('top_fillers', [])
            if top_fillers:
                print(f"\nTop Fillers:")
                for i, filler in enumerate(top_fillers[:5], 1):
                    print(f"    {i}. '{filler['token']}': {filler['count']} times")

            feedback = fillers.get('feedback', [])
            if feedback:
                print(f"\nFeedback:")
                for fb in feedback:
                    print(f"  - {fb['message']}")
        else:
            print(f"  - Reason: {fillers.get('details', {}).get('reason', 'unknown')}")

        # Save result
        with open("fillers_test_result.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nFull result saved to: fillers_test_result.json")

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()


def test_all_metrics():
    """Test all implemented metrics together."""
    print("\n" + "="*60)
    print("TEST 3: All Metrics Integration")
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
        "requested_metrics": ["pace", "pause_quality", "fillers"],
        "user_metadata": {},
    }

    try:
        result = run_full_analysis(
            job_id="test-all-metrics",
            audio_path=audio_path,
            raw_input_payload=payload,
        )

        print(f"\n[SUCCESS] Analysis completed")
        print(f"Duration: {result['input']['duration_sec']:.2f}s")

        metrics = result['metrics']
        print(f"\nMetrics Computed: {list(metrics.keys())}")

        for metric_name, metric_data in metrics.items():
            score = metric_data.get('score_0_100')
            label = metric_data.get('label')
            abstained = metric_data.get('abstained', False)

            if abstained:
                print(f"\n{metric_name.upper()}: ABSTAINED")
                print(f"  Reason: {metric_data.get('details', {}).get('reason')}")
            else:
                print(f"\n{metric_name.upper()}: {score}/100 ({label})")

        print(f"\nTimeline events: {len(result.get('timeline', []))}")

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("\n" + "#"*60)
    print("# FILLERS METRIC TESTS")
    print("#"*60)

    # Setup logging
    setup_logging(level="INFO")

    test_fillers_unit()
    test_fillers_integration()
    test_all_metrics()

    print("\n" + "#"*60)
    print("# TESTS COMPLETED")
    print("#"*60 + "\n")


if __name__ == "__main__":
    main()
