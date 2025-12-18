"""
test_intonation.py

Test script to verify intonation metric detection and integration.
"""

from pathlib import Path
from analyzer.logging_config import setup_logging
from analyzer.run_pipeline import run_full_analysis
from analyzer.metrics.intonation import compute_intonation_metric
import json


def test_intonation_unit():
    """Unit test the intonation metric with synthetic data."""
    print("\n" + "="*60)
    print("TEST 1: Intonation Metric Unit Test")
    print("="*60)

    # Test case 1: Monotone (low pitch_std, low energy_std)
    audio_features = {
        "mean_pitch_hz": 150.0,
        "pitch_std_hz": 8.0,  # Very low variance
        "energy_std": 0.003,
        "energy_mean": 0.05,
    }
    duration_sec = 30.0

    result = compute_intonation_metric(audio_features, duration_sec)
    print(f"\n1. Monotone speech (pitch_std=8.0 Hz):")
    print(f"   Score: {result['score_0_100']}/100")
    print(f"   Label: {result['label']}")
    print(f"   Confidence: {result['confidence']}")
    print(f"   Abstained: {result['abstained']}")
    if not result['abstained']:
        details = result['details']
        print(f"   Pitch std: {details.get('pitch_std_hz')} Hz")
        print(f"   Pitch range: {details.get('pitch_range_hz')} Hz (estimated)")
        print(f"   Pitch CoV: {details.get('pitch_cov'):.3f}" if details.get('pitch_cov') else "   Pitch CoV: None")
        print(f"   Prosody variance score: {details['prosody_variance_score']:.3f}")
    assert result['label'] == 'monotone'
    assert result['score_0_100'] is not None
    assert result['abstained'] == False
    assert result['details'].get('pitch_range_hz') is not None  # NEW
    assert result['details'].get('pitch_cov') is not None  # NEW

    # Test case 2: Somewhat monotone (moderate pitch_std)
    audio_features = {
        "mean_pitch_hz": 180.0,
        "pitch_std_hz": 22.0,  # Moderate variance
        "energy_std": 0.015,
        "energy_mean": 0.08,
    }
    duration_sec = 45.0

    result = compute_intonation_metric(audio_features, duration_sec)
    print(f"\n2. Somewhat monotone speech (pitch_std=22.0 Hz):")
    print(f"   Score: {result['score_0_100']}/100")
    print(f"   Label: {result['label']}")
    print(f"   Confidence: {result['confidence']}")
    print(f"   Prosody variance score: {result['details']['prosody_variance_score']:.3f}")
    assert result['label'] == 'somewhat_monotone'
    assert result['abstained'] == False

    # Test case 3: Dynamic (high pitch_std, high energy_std)
    audio_features = {
        "mean_pitch_hz": 200.0,
        "pitch_std_hz": 45.0,  # High variance
        "energy_std": 0.035,
        "energy_mean": 0.12,
    }
    duration_sec = 60.0

    result = compute_intonation_metric(audio_features, duration_sec)
    print(f"\n3. Dynamic speech (pitch_std=45.0 Hz):")
    print(f"   Score: {result['score_0_100']}/100")
    print(f"   Label: {result['label']}")
    print(f"   Confidence: {result['confidence']}")
    print(f"   Prosody variance score: {result['details']['prosody_variance_score']:.3f}")
    assert result['label'] == 'dynamic'
    assert result['score_0_100'] >= 80
    assert result['abstained'] == False

    # Test case 4: Very short audio (should abstain)
    audio_features = {
        "mean_pitch_hz": 150.0,
        "pitch_std_hz": 20.0,
        "energy_std": 0.01,
        "energy_mean": 0.05,
    }
    duration_sec = 2.0  # Too short

    result = compute_intonation_metric(audio_features, duration_sec)
    print(f"\n4. Very short audio (2.0s, should abstain):")
    print(f"   Score: {result['score_0_100']}")
    print(f"   Label: {result['label']}")
    print(f"   Abstained: {result['abstained']}")
    print(f"   Reason: {result['details'].get('reason', 'N/A')}")
    assert result['abstained'] == True

    # Test case 5: Missing pitch data (should abstain)
    audio_features = {
        "mean_pitch_hz": None,
        "pitch_std_hz": None,
        "energy_std": 0.01,
        "energy_mean": 0.05,
    }
    duration_sec = 30.0

    result = compute_intonation_metric(audio_features, duration_sec)
    print(f"\n5. Missing pitch data (should abstain):")
    print(f"   Score: {result['score_0_100']}")
    print(f"   Label: {result['label']}")
    print(f"   Abstained: {result['abstained']}")
    print(f"   Reason: {result['details'].get('reason', 'N/A')}")
    assert result['abstained'] == True

    # Test case 6: Very low variance (edge case - should still be monotone)
    audio_features = {
        "mean_pitch_hz": 120.0,
        "pitch_std_hz": 0.5,  # Almost zero variance
        "energy_std": 0.001,
        "energy_mean": 0.03,
    }
    duration_sec = 25.0

    result = compute_intonation_metric(audio_features, duration_sec)
    print(f"\n6. Very low variance (pitch_std=0.5 Hz):")
    print(f"   Score: {result['score_0_100']}/100")
    print(f"   Label: {result['label']}")
    print(f"   Confidence: {result['confidence']}")
    assert result['label'] == 'monotone'
    assert result['score_0_100'] < 50

    print("\n[PASS] All unit tests passed!")


def test_intonation_integration():
    """Test intonation metric with real audio file."""
    print("\n" + "="*60)
    print("TEST 2: Intonation Integration Test")
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
        "requested_metrics": ["intonation"],
        "user_metadata": {},
    }

    try:
        result = run_full_analysis(
            job_id="test-intonation",
            audio_path=audio_path,
            raw_input_payload=payload,
        )

        print(f"\n[SUCCESS] Analysis completed")
        print(f"Duration: {result['input']['duration_sec']:.2f}s")

        # Check intonation metric
        intonation = result['metrics'].get('intonation', {})
        print(f"\nIntonation Metric:")
        print(f"  - Score: {intonation.get('score_0_100')}/100")
        print(f"  - Label: {intonation.get('label')}")
        print(f"  - Confidence: {intonation.get('confidence')}")

        if not intonation.get('abstained'):
            details = intonation.get('details', {})
            print(f"\nIntonation Details:")
            print(f"  - Mean pitch: {details.get('mean_pitch_hz', 'N/A')} Hz")
            print(f"  - Pitch std: {details.get('pitch_std_hz', 'N/A')} Hz")
            print(f"  - Energy std: {details.get('energy_std', 'N/A')}")
            print(f"  - Prosody variance score: {details.get('prosody_variance_score', 'N/A'):.3f}")

            feedback = intonation.get('feedback', [])
            if feedback:
                print(f"\nFeedback:")
                for fb in feedback:
                    print(f"  - {fb['message']}")
        else:
            print(f"  - Reason: {intonation.get('details', {}).get('reason', 'unknown')}")

        # Save result
        with open("intonation_test_result.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nFull result saved to: intonation_test_result.json")

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()


def test_all_metrics_with_intonation():
    """Test all implemented metrics together including intonation."""
    print("\n" + "="*60)
    print("TEST 3: All Metrics Integration (including Intonation)")
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
        "requested_metrics": ["pace", "pause_quality", "fillers", "intonation"],
        "user_metadata": {},
    }

    try:
        result = run_full_analysis(
            job_id="test-all-metrics-v2",
            audio_path=audio_path,
            raw_input_payload=payload,
        )

        print(f"\n[SUCCESS] Analysis completed")
        print(f"Duration: {result['input']['duration_sec']:.2f}s")

        metrics = result['metrics']
        print(f"\nMetrics Computed: {list(metrics.keys())}")
        print(f"Total metrics: {len(metrics)}/7 implemented")

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

        # Save comprehensive result
        with open("all_metrics_test_result.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nFull result saved to: all_metrics_test_result.json")

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("\n" + "#"*60)
    print("# INTONATION METRIC TESTS")
    print("#"*60)

    # Setup logging
    setup_logging(level="INFO")

    test_intonation_unit()
    test_intonation_integration()
    test_all_metrics_with_intonation()

    print("\n" + "#"*60)
    print("# TESTS COMPLETED")
    print("#"*60 + "\n")


if __name__ == "__main__":
    main()
