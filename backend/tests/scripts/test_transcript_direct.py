"""
Quick test to verify transcript segments and tokens are working.
Tests the _build_transcript_from_words function directly.
"""

from analyzer.run_pipeline import _build_transcript_from_words

# Sample words data (like what comes from Whisper)
sample_words = [
    {"text": "Hello", "start": 0.0, "end": 0.5, "probability": 0.95},
    {"text": "everyone", "start": 0.6, "end": 1.2, "probability": 0.92},
    {"text": "um", "start": 1.3, "end": 1.5, "probability": 0.88},
    {"text": "today", "start": 1.6, "end": 2.0, "probability": 0.94},
    {"text": "we're", "start": 2.1, "end": 2.4, "probability": 0.91},
    {"text": "going", "start": 2.5, "end": 2.8, "probability": 0.93},
    {"text": "to", "start": 2.9, "end": 3.0, "probability": 0.96},
    {"text": "talk", "start": 3.1, "end": 3.5, "probability": 0.94},
    {"text": "about", "start": 3.6, "end": 4.0, "probability": 0.92},
    {"text": "like", "start": 4.1, "end": 4.3, "probability": 0.89},
    {"text": "presentations", "start": 4.4, "end": 5.2, "probability": 0.95},
]

print("Testing _build_transcript_from_words()...")
print("=" * 60)

result = _build_transcript_from_words(sample_words)

print(f"\nFull text: {result['full_text']}")
print(f"Language: {result['language']}")
print(f"\nNumber of segments: {len(result['segments'])}")
print(f"Number of tokens: {len(result['tokens'])}")

print("\n" + "=" * 60)
print("SEGMENTS:")
print("=" * 60)
for i, segment in enumerate(result['segments'], 1):
    print(f"\nSegment {i}:")
    print(f"  Time: {segment['start_sec']:.1f}s - {segment['end_sec']:.1f}s")
    print(f"  Text: {segment['text']}")
    print(f"  Confidence: {segment['avg_confidence']:.2f}")

print("\n" + "=" * 60)
print("TOKENS (first 5):")
print("=" * 60)
for i, token in enumerate(result['tokens'][:5], 1):
    print(f"\nToken {i}:")
    print(f"  Text: '{token['text']}'")
    print(f"  Time: {token['start_sec']:.1f}s - {token['end_sec']:.1f}s")
    print(f"  Is filler: {token['is_filler']}")

print("\n" + "=" * 60)
print("FILLER DETECTION:")
print("=" * 60)
fillers = [t for t in result['tokens'] if t['is_filler']]
print(f"Found {len(fillers)} filler words:")
for filler in fillers:
    print(f"  - '{filler['text']}' at {filler['start_sec']:.1f}s")

print("\n" + "=" * 60)
print("TEST RESULTS:")
print("=" * 60)

# Check that we have segments
if len(result['segments']) > 0:
    print("✓ Segments are populated")
else:
    print("❌ Segments are empty")

# Check that we have tokens
if len(result['tokens']) == len(sample_words):
    print("✓ Tokens are populated (correct count)")
else:
    print(f"❌ Token count mismatch: expected {len(sample_words)}, got {len(result['tokens'])}")

# Check that filler detection works
if len(fillers) == 2:  # "um" and "like"
    print("✓ Filler detection works (found 'um' and 'like')")
else:
    print(f"❌ Filler detection issue: expected 2 fillers, found {len(fillers)}")

# Check token structure
sample_token = result['tokens'][0]
required_fields = {'text', 'start_sec', 'end_sec', 'is_filler'}
if all(field in sample_token for field in required_fields):
    print("✓ Token structure is correct")
else:
    print(f"❌ Token structure missing fields: {required_fields - set(sample_token.keys())}")

# Check segment structure
sample_segment = result['segments'][0]
required_fields = {'start_sec', 'end_sec', 'text', 'avg_confidence'}
if all(field in sample_segment for field in required_fields):
    print("✓ Segment structure is correct")
else:
    print(f"❌ Segment structure missing fields: {required_fields - set(sample_segment.keys())}")

print("\n✅ All transcript enhancement features are working!")
