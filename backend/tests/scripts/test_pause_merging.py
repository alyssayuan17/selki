"""
test_pause_merging.py

Test script to verify pause overlap merging logic.
"""

from pathlib import Path
from analyzer.logging_config import setup_logging
from analyzer.run_pipeline import run_full_analysis
import json


def test_pause_merging():
    """Test pause quality with real audio to see merging in action."""
    print("\n" + "="*60)
    print("TEST: Pause Quality Overlap Merging")
    print("="*60)

    # Use pausetest.mp3 which should have more pauses
    audio_path = Path("pausetest.mp3")
    if not audio_path.exists():
        audio_path = Path("test.wav")
        if not audio_path.exists():
            print(f"SKIPPED: No test audio files found")
            return
        print(f"Using {audio_path}")
    else:
        print(f"Using {audio_path}")

    payload = {
        "audio_url": str(audio_path),
        "language": "en",
        "talk_type": "presentation",
        "audience_type": "general",
        "requested_metrics": ["pause_quality"],
        "user_metadata": {},
    }

    try:
        result = run_full_analysis(
            job_id="test-pause-merge",
            audio_path=audio_path,
            raw_input_payload=payload,
        )

        print(f"\n[SUCCESS] Analysis completed")
        print(f"Duration: {result['input']['duration_sec']:.2f}s")

        # Check pause quality metric
        pause_quality = result['metrics'].get('pause_quality', {})
        print(f"\nPause Quality Metric:")
        print(f"  - Score: {pause_quality.get('score_0_100')}/100")
        print(f"  - Label: {pause_quality.get('label')}")
        print(f"  - Confidence: {pause_quality.get('confidence')}")

        details = pause_quality.get('details', {})
        print(f"\nPause Details:")

        if pause_quality.get('abstained'):
            print(f"  - Reason: {details.get('reason', 'unknown')}")
        else:
            print(f"  - Total pauses: {details.get('total_pauses')}")
            avg_dur = details.get('average_pause_duration')
            if avg_dur is not None:
                print(f"  - Average duration: {avg_dur:.3f}s")
            print(f"  - Long pauses (>1s): {details.get('long_pauses')}")
            print(f"  - Short pauses (<0.2s): {details.get('short_pauses')}")
            pause_rate = details.get('pause_rate')
            if pause_rate is not None:
                print(f"  - Pause rate: {pause_rate:.3f} pauses/sec")

        # Check timeline
        timeline = result.get('timeline', [])
        print(f"\nTimeline Events: {len(timeline)}")

        if timeline:
            print("\nPause Timeline:")
            for i, event in enumerate(timeline[:10], 1):  # Show first 10
                print(f"  {i}. [{event['start_sec']:.2f}s - {event['end_sec']:.2f}s] "
                      f"({event['end_sec'] - event['start_sec']:.2f}s) "
                      f"- {event['quality']} - source: {event['source']}")
            if len(timeline) > 10:
                print(f"  ... and {len(timeline) - 10} more")

        # Count sources
        asr_count = sum(1 for e in timeline if e.get('source') == 'asr')
        vad_count = sum(1 for e in timeline if e.get('source') == 'vad')
        print(f"\nSource breakdown: {asr_count} ASR, {vad_count} VAD")

        # Save full result
        with open("pause_merge_test_result.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nFull result saved to: pause_merge_test_result.json")

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("\n" + "#"*60)
    print("# PAUSE MERGING TEST")
    print("#"*60)

    # Setup logging with DEBUG to see merge details
    setup_logging(level="DEBUG")

    test_pause_merging()

    print("\n" + "#"*60)
    print("# TEST COMPLETED")
    print("#"*60 + "\n")


if __name__ == "__main__":
    main()
