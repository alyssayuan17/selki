"""
test_new_features.py

Test script to verify the new filler spike detection and pause classification features.
"""

import sys
sys.path.insert(0, '.')

from analyzer.metrics.fillers import compute_fillers_metric, _detect_filler_spikes
from analyzer.metrics.pause_quality import compute_pause_quality_metric, _classify_pause_context


def test_fillers_per_100_words():
    """Test fillers_per_100_words calculation."""
    print("\n" + "="*60)
    print("TEST 1: Fillers per 100 words calculation")
    print("="*60)

    # 10 words total, 2 fillers = 20 fillers per 100 words
    words = [
        {"text": "um", "start": 0.0, "end": 0.3},
        {"text": "hello", "start": 0.4, "end": 0.8},
        {"text": "I", "start": 0.9, "end": 1.0},
        {"text": "think", "start": 1.1, "end": 1.4},
        {"text": "like", "start": 1.5, "end": 1.8},  # filler
        {"text": "this", "start": 1.9, "end": 2.2},
        {"text": "is", "start": 2.3, "end": 2.5},
        {"text": "good", "start": 2.6, "end": 3.0},
        {"text": "stuff", "start": 3.1, "end": 3.5},
        {"text": "here", "start": 3.6, "end": 4.0},
    ]
    duration_sec = 60.0

    result = compute_fillers_metric(words, duration_sec)

    print(f"\nWords: {len(words)}")
    print(f"Fillers: {result['details']['total_fillers']}")
    print(f"Fillers per min: {result['details']['filler_rate_per_min']:.2f}")
    print(f"Fillers per 100 words: {result['details']['fillers_per_100_words']:.2f}")

    assert 'fillers_per_100_words' in result['details'], "Missing fillers_per_100_words!"
    expected = (2 / 10) * 100
    actual = result['details']['fillers_per_100_words']
    assert abs(actual - expected) < 0.1, f"Expected {expected}, got {actual}"

    print("✓ PASSED: fillers_per_100_words correctly calculated")


def test_filler_spike_detection():
    """Test filler spike detection."""
    print("\n" + "="*60)
    print("TEST 2: Filler spike detection")
    print("="*60)

    # Create a speech with a spike of fillers in the middle
    words = []

    # First 30 seconds: clean (0 fillers)
    for i in range(100):
        words.append({"text": f"word{i}", "start": i * 0.3, "end": (i + 1) * 0.3})

    # Next 30 seconds: high filler rate (many fillers)
    base_time = 30.0
    for i in range(50):
        # Every other word is a filler
        if i % 2 == 0:
            words.append({"text": "um", "start": base_time + i * 0.6, "end": base_time + (i + 1) * 0.6})
        else:
            words.append({"text": f"word{i}", "start": base_time + i * 0.6, "end": base_time + (i + 1) * 0.6})

    # Last 30 seconds: clean again
    base_time = 60.0
    for i in range(100):
        words.append({"text": f"word{i}", "start": base_time + i * 0.3, "end": base_time + (i + 1) * 0.3})

    spikes = _detect_filler_spikes(words)

    print(f"\nDetected {len(spikes)} filler spike(s)")
    for spike in spikes:
        print(f"  - [{spike['start_sec']:.1f}s - {spike['end_sec']:.1f}s]: {spike['filler_rate']:.1f}/min")

    assert len(spikes) > 0, "Should detect at least one spike"
    print("✓ PASSED: Filler spikes detected")


def test_filler_spikes_in_output():
    """Test that filler_spikes is included in metric output."""
    print("\n" + "="*60)
    print("TEST 3: Filler spikes in metric output")
    print("="*60)

    words = [
        {"text": "um", "start": 0.0, "end": 0.3},
        {"text": "uh", "start": 0.4, "end": 0.6},
        {"text": "like", "start": 0.7, "end": 1.0},
        {"text": "hello", "start": 1.1, "end": 1.4},
    ]
    duration_sec = 10.0

    result = compute_fillers_metric(words, duration_sec)

    assert 'filler_spikes' in result['details'], "Missing filler_spikes!"
    print(f"Filler spikes: {result['details']['filler_spikes']}")
    print("✓ PASSED: filler_spikes present in output")


def test_helpful_awkward_ratios():
    """Test helpful/awkward pause classification."""
    print("\n" + "="*60)
    print("TEST 4: Helpful/awkward pause ratios")
    print("="*60)

    # Create pauses
    word_pauses = [
        {"start": 5.0, "end": 5.5, "duration": 0.5},  # Should be helpful (medium duration)
        {"start": 10.0, "end": 10.1, "duration": 0.1},  # Should be awkward (too short)
        {"start": 15.0, "end": 18.0, "duration": 3.0},  # Should be awkward (too long)
    ]

    # Create word context
    words = [
        {"text": "Hello.", "start": 0.0, "end": 1.0},
        {"text": "This", "start": 5.6, "end": 6.0},
        {"text": "is", "start": 6.1, "end": 6.3},
        {"text": "good", "start": 10.2, "end": 10.5},
        {"text": "content", "start": 18.1, "end": 18.5},
    ]

    duration_sec = 20.0

    metric, timeline = compute_pause_quality_metric(word_pauses, None, duration_sec, words)

    print(f"\nTotal pauses: {metric['details']['total_pauses']}")
    print(f"Helpful count: {metric['details']['helpful_count']}")
    print(f"Awkward count: {metric['details']['awkward_count']}")
    print(f"Helpful ratio: {metric['details']['helpful_ratio']:.2f}")
    print(f"Awkward ratio: {metric['details']['awkward_ratio']:.2f}")

    assert 'helpful_ratio' in metric['details'], "Missing helpful_ratio!"
    assert 'awkward_ratio' in metric['details'], "Missing awkward_ratio!"
    assert 'helpful_count' in metric['details'], "Missing helpful_count!"
    assert 'awkward_count' in metric['details'], "Missing awkward_count!"

    print("✓ PASSED: Helpful/awkward ratios calculated")


def test_pause_context_in_timeline():
    """Test that pause context is included in timeline."""
    print("\n" + "="*60)
    print("TEST 5: Pause context in timeline")
    print("="*60)

    word_pauses = [
        {"start": 5.0, "end": 5.5, "duration": 0.5},
    ]

    words = [
        {"text": "Hello", "start": 0.0, "end": 1.0},
        {"text": "there", "start": 5.6, "end": 6.0},
    ]

    duration_sec = 10.0

    metric, timeline = compute_pause_quality_metric(word_pauses, None, duration_sec, words)

    print(f"\nTimeline events: {len(timeline)}")
    for event in timeline:
        print(f"  - [{event['start_sec']:.1f}s - {event['end_sec']:.1f}s]: "
              f"quality={event.get('quality')}, context={event.get('context')}")

    assert len(timeline) > 0, "Should have timeline events"
    assert 'context' in timeline[0], "Timeline event should have context field"
    assert timeline[0]['context'] in ['helpful', 'awkward'], "Context should be helpful or awkward"

    print("✓ PASSED: Pause context in timeline")


if __name__ == "__main__":
    try:
        test_fillers_per_100_words()
        test_filler_spike_detection()
        test_filler_spikes_in_output()
        test_helpful_awkward_ratios()
        test_pause_context_in_timeline()

        print("\n" + "="*60)
        print("ALL TESTS PASSED! ✓")
        print("="*60)

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
