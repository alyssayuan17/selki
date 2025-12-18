"""
test_pause_overlap.py

Unit tests for pause overlap detection and merging logic.
"""

from analyzer.metrics.pause_quality import (
    pauses_overlap,
    merge_overlapping_pauses,
    combine_pauses
)


def test_pauses_overlap():
    """Test overlap detection between two pauses."""
    print("\n" + "="*60)
    print("TEST 1: Pause Overlap Detection")
    print("="*60)

    # Test case 1: Complete overlap
    p1 = {"start": 1.0, "end": 2.0}
    p2 = {"start": 1.5, "end": 2.5}
    result = pauses_overlap(p1, p2)
    print(f"1. Complete overlap [1.0-2.0] vs [1.5-2.5]: {result} (expected: True)")
    assert result == True

    # Test case 2: No overlap
    p1 = {"start": 1.0, "end": 2.0}
    p2 = {"start": 3.0, "end": 4.0}
    result = pauses_overlap(p1, p2)
    print(f"2. No overlap [1.0-2.0] vs [3.0-4.0]: {result} (expected: False)")
    assert result == False

    # Test case 3: Tiny overlap (below threshold)
    p1 = {"start": 1.0, "end": 2.0}
    p2 = {"start": 1.95, "end": 3.0}
    result = pauses_overlap(p1, p2, threshold=0.1)
    print(f"3. Tiny overlap [1.0-2.0] vs [1.95-3.0]: {result} (expected: False, overlap=0.05s < 0.1s)")
    assert result == False

    # Test case 4: Exact boundary touch
    p1 = {"start": 1.0, "end": 2.0}
    p2 = {"start": 2.0, "end": 3.0}
    result = pauses_overlap(p1, p2, threshold=0.1)
    print(f"4. Exact touch [1.0-2.0] vs [2.0-3.0]: {result} (expected: False)")
    assert result == False

    # Test case 5: One completely inside another
    p1 = {"start": 1.0, "end": 5.0}
    p2 = {"start": 2.0, "end": 3.0}
    result = pauses_overlap(p1, p2)
    print(f"5. Complete containment [1.0-5.0] vs [2.0-3.0]: {result} (expected: True)")
    assert result == True

    print("\n[PASS] All overlap detection tests passed!")


def test_merge_vad_priority():
    """Test that VAD takes priority over ASR when overlapping."""
    print("\n" + "="*60)
    print("TEST 2: VAD Priority over ASR")
    print("="*60)

    pauses = [
        {"start": 1.0, "end": 2.0, "duration": 1.0, "source": "asr"},
        {"start": 1.5, "end": 2.5, "duration": 1.0, "source": "vad"},  # Overlaps with ASR
    ]

    merged = merge_overlapping_pauses(pauses)

    print(f"Input: 2 pauses (1 ASR, 1 VAD overlapping)")
    print(f"  - ASR: [1.0-2.0]")
    print(f"  - VAD: [1.5-2.5]")
    print(f"\nOutput: {len(merged)} pause(s)")
    for i, p in enumerate(merged, 1):
        print(f"  {i}. [{p['start']}-{p['end']}] source={p['source']}")

    assert len(merged) == 1, f"Expected 1 merged pause, got {len(merged)}"
    assert merged[0]["source"] == "vad", "Expected VAD source to win"
    assert merged[0]["start"] == 1.5, "Expected VAD pause start"
    assert merged[0]["end"] == 2.5, "Expected VAD pause end"

    print("\n[PASS] VAD correctly replaced overlapping ASR pause!")


def test_merge_same_type():
    """Test merging two pauses of the same type."""
    print("\n" + "="*60)
    print("TEST 3: Merge Same Type (ASR + ASR)")
    print("="*60)

    pauses = [
        {"start": 1.0, "end": 2.0, "duration": 1.0, "source": "asr"},
        {"start": 1.8, "end": 3.0, "duration": 1.2, "source": "asr"},  # Overlaps
    ]

    merged = merge_overlapping_pauses(pauses)

    print(f"Input: 2 ASR pauses overlapping")
    print(f"  - ASR: [1.0-2.0]")
    print(f"  - ASR: [1.8-3.0]")
    print(f"\nOutput: {len(merged)} pause(s)")
    for i, p in enumerate(merged, 1):
        print(f"  {i}. [{p['start']}-{p['end']}] duration={p['duration']}s source={p['source']}")

    assert len(merged) == 1, f"Expected 1 merged pause, got {len(merged)}"
    assert merged[0]["start"] == 1.0, "Expected merged start to be min of both"
    assert merged[0]["end"] == 3.0, "Expected merged end to be max of both"
    assert merged[0]["duration"] == 2.0, "Expected merged duration to be 2.0s"

    print("\n[PASS] Same-type pauses correctly merged!")


def test_multiple_overlaps():
    """Test complex scenario with multiple overlapping pauses."""
    print("\n" + "="*60)
    print("TEST 4: Multiple Overlapping Pauses")
    print("="*60)

    pauses = [
        {"start": 1.0, "end": 2.0, "duration": 1.0, "source": "asr"},
        {"start": 1.5, "end": 2.5, "duration": 1.0, "source": "vad"},  # Overlaps ASR
        {"start": 3.0, "end": 4.0, "duration": 1.0, "source": "asr"},  # Separate
        {"start": 3.2, "end": 3.8, "duration": 0.6, "source": "vad"},  # Overlaps ASR
        {"start": 5.0, "end": 6.0, "duration": 1.0, "source": "vad"},  # Separate
    ]

    merged = merge_overlapping_pauses(pauses)

    print(f"Input: 5 pauses (3 ASR, 2 VAD)")
    for p in pauses:
        print(f"  - {p['source'].upper()}: [{p['start']}-{p['end']}]")

    print(f"\nOutput: {len(merged)} pause(s)")
    for i, p in enumerate(merged, 1):
        print(f"  {i}. [{p['start']}-{p['end']}] source={p['source']}")

    assert len(merged) == 3, f"Expected 3 merged pauses, got {len(merged)}"

    # First pause should be VAD (replaced ASR)
    assert merged[0]["source"] == "vad"
    assert merged[0]["start"] == 1.5 and merged[0]["end"] == 2.5

    # Second pause should be VAD (replaced ASR)
    assert merged[1]["source"] == "vad"
    assert merged[1]["start"] == 3.2 and merged[1]["end"] == 3.8

    # Third pause should be VAD (standalone)
    assert merged[2]["source"] == "vad"
    assert merged[2]["start"] == 5.0 and merged[2]["end"] == 6.0

    print("\n[PASS] Multiple overlaps correctly resolved!")


def test_combine_pauses_integration():
    """Test the full combine_pauses function."""
    print("\n" + "="*60)
    print("TEST 5: Full combine_pauses Integration")
    print("="*60)

    word_pauses = [
        {"start": 1.0, "end": 2.0, "duration": 1.0},
        {"start": 3.0, "end": 4.0, "duration": 1.0},
    ]

    vad_silences = [
        {"start": 0.0, "end": 0.5},  # Boundary - should be filtered
        {"start": 1.5, "end": 2.5},  # Overlaps with first ASR pause
        {"start": 4.5, "end": 5.0},  # Separate
        {"start": 9.5, "end": 10.0},  # Boundary (end) - should be filtered
    ]

    duration_sec = 10.0

    combined = combine_pauses(word_pauses, vad_silences, duration_sec, boundary_margin=0.3)

    print(f"Input:")
    print(f"  - ASR word pauses: {len(word_pauses)}")
    for p in word_pauses:
        print(f"    [{p['start']}-{p['end']}]")
    print(f"  - VAD silences: {len(vad_silences)}")
    for p in vad_silences:
        print(f"    [{p['start']}-{p['end']}]")
    print(f"  - Duration: {duration_sec}s, boundary margin: 0.3s")

    print(f"\nOutput: {len(combined)} pauses")
    for i, p in enumerate(combined, 1):
        print(f"  {i}. [{p['start']}-{p['end']}] source={p['source']}")

    # Should have 3 pauses:
    # - VAD [1.5-2.5] (replaced ASR [1.0-2.0])
    # - ASR [3.0-4.0] (no overlap)
    # - VAD [4.5-5.0] (separate)
    # Boundary pauses should be filtered out

    assert len(combined) == 3, f"Expected 3 pauses, got {len(combined)}"

    # Check sources
    sources = [p["source"] for p in combined]
    assert sources.count("vad") == 2, "Expected 2 VAD pauses"
    assert sources.count("asr") == 1, "Expected 1 ASR pause"

    print("\n[PASS] Full integration test passed!")


def main():
    print("\n" + "#"*60)
    print("# PAUSE OVERLAP MERGING UNIT TESTS")
    print("#"*60)

    test_pauses_overlap()
    test_merge_vad_priority()
    test_merge_same_type()
    test_multiple_overlaps()
    test_combine_pauses_integration()

    print("\n" + "#"*60)
    print("# ALL TESTS PASSED!")
    print("#"*60 + "\n")


if __name__ == "__main__":
    main()
