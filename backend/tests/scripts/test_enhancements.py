"""
Test script for the three new enhancements:
1. Overall score calculation
2. File upload support
3. Transcript segments/tokens

Run with: python test_enhancements.py
"""

import requests
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"


def test_overall_score():
    """Test that overall score is properly calculated from metrics."""
    print("\n=== Testing Overall Score Calculation ===")

    # Use existing audio file for testing
    audio_path = Path(__file__).parent / "harvard.wav"
    if not audio_path.exists():
        print(f"❌ Test audio file not found: {audio_path}")
        print("   Please place a test audio file at backend/harvard.wav")
        return False

    # Submit job with all metrics (same as manual test)
    response = requests.post(
        f"{BASE_URL}/api/v1/presentations",
        json={
            "audio_url": f"file://{audio_path.absolute().as_posix()}",
            "language": "en",
            "talk_type": "test",
            "audience_type": "general",
            "requested_metrics": ["pace", "pause_quality", "fillers", "intonation", "content_structure", "confidence_cv"],
        },
    )

    if response.status_code != 201:
        print(f"❌ Failed to create job: {response.text}")
        return False

    job_id = response.json()["job_id"]
    print(f"✓ Job created: {job_id}")

    # Poll until done
    for _ in range(60):
        response = requests.get(f"{BASE_URL}/api/v1/presentations/{job_id}")
        data = response.json()

        if data["status"] == "done":
            overall_score = data.get("overall_score", {})
            score = overall_score.get("score_0_100", 0)
            label = overall_score.get("label", "unknown")
            confidence = overall_score.get("confidence", 0.0)

            print(f"✓ Overall score: {score}/100 ({label}, confidence: {confidence})")

            if score == 0 and label == "unknown":
                print("❌ Overall score is still hardcoded (0, unknown)")
                return False
            else:
                print("✓ Overall score is properly calculated!")
                return True

        elif data["status"] == "failed":
            print(f"❌ Job failed: {data.get('failure', {}).get('message')}")
            return False

        time.sleep(1)

    print("❌ Job timed out")
    return False


def test_file_upload():
    """Test file upload endpoint."""
    print("\n=== Testing File Upload ===")

    # Use existing audio file for testing
    audio_path = Path(__file__).parent / "harvard.wav"
    if not audio_path.exists():
        print(f"❌ Test audio file not found: {audio_path}")
        print("   Please place a test audio file at backend/harvard.wav")
        return False

    # Upload file
    with open(audio_path, "rb") as f:
        files = {"file": (audio_path.name, f, "audio/wav")}
        data = {
            "language": "en",
            "talk_type": "presentation",
            "audience_type": "general",
        }

        response = requests.post(
            f"{BASE_URL}/api/v1/presentations/upload",
            files=files,
            data=data,
        )

    if response.status_code != 201:
        print(f"❌ Failed to upload file: {response.text}")
        return False

    job_data = response.json()
    job_id = job_data["job_id"]
    audio_url = job_data["input"]["audio_url"]

    print(f"✓ File uploaded: {job_id}")
    print(f"✓ Saved to: {audio_url}")

    # Verify file exists in uploads directory
    if "file://" in audio_url:
        file_path = Path(audio_url.replace("file://", ""))
        if file_path.exists():
            print(f"✓ File exists at: {file_path}")
            return True
        else:
            print(f"❌ File not found at: {file_path}")
            return False

    return True


def test_transcript_segments_tokens():
    """Test that transcript includes segments and tokens."""
    print("\n=== Testing Transcript Segments/Tokens ===")

    # Use existing audio file for testing
    audio_path = Path(__file__).parent / "harvard.wav"
    if not audio_path.exists():
        print(f"❌ Test audio file not found: {audio_path}")
        print("   Please place a test audio file at backend/harvard.wav")
        return False

    # Submit job
    response = requests.post(
        f"{BASE_URL}/api/v1/presentations",
        json={
            "audio_url": f"file://{audio_path.absolute().as_posix()}",
            "language": "en",
            "talk_type": "presentation",
            "audience_type": "general",
        },
    )

    if response.status_code != 201:
        print(f"❌ Failed to create job: {response.text}")
        return False

    job_id = response.json()["job_id"]
    print(f"✓ Job created: {job_id}")

    # Poll until done
    for _ in range(60):
        response = requests.get(f"{BASE_URL}/api/v1/presentations/{job_id}")
        data = response.json()

        if data["status"] == "done":
            # Get transcript
            response = requests.get(f"{BASE_URL}/api/v1/presentations/{job_id}/transcript")
            transcript_data = response.json()

            transcript = transcript_data.get("transcript", {})
            segments = transcript.get("segments", [])
            tokens = transcript.get("tokens", [])

            print(f"✓ Transcript has {len(segments)} segments")
            print(f"✓ Transcript has {len(tokens)} tokens")

            if len(segments) == 0 and len(tokens) == 0:
                print("❌ Segments and tokens are empty!")
                return False

            # Check if tokens have is_filler field
            if tokens:
                has_filler_field = all("is_filler" in token for token in tokens)
                if has_filler_field:
                    print("✓ Tokens have is_filler field")
                else:
                    print("❌ Tokens missing is_filler field")
                    return False

                # Show sample token
                sample_token = tokens[0]
                print(f"✓ Sample token: {sample_token}")

            # Show sample segment
            if segments:
                sample_segment = segments[0]
                print(f"✓ Sample segment: start={sample_segment['start_sec']:.1f}s, "
                      f"end={sample_segment['end_sec']:.1f}s, "
                      f"text='{sample_segment['text'][:50]}...'")

            print("✓ Transcript enhancement working!")
            return True

        elif data["status"] == "failed":
            print(f"❌ Job failed: {data.get('failure', {}).get('message')}")
            return False

        time.sleep(1)

    print("❌ Job timed out")
    return False


def main():
    """Run all tests."""
    print("Starting enhancement tests...")
    print("Make sure the API server is running: uvicorn main:app --reload")

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ API server is not running!")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server!")
        print("   Please start the server with: uvicorn main:app --reload")
        return

    print("✓ API server is running")

    results = {
        "Overall Score": test_overall_score(),
        "File Upload": test_file_upload(),
        "Transcript Segments/Tokens": test_transcript_segments_tokens(),
    }

    print("\n" + "="*50)
    print("TEST RESULTS:")
    print("="*50)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")

    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed")


if __name__ == "__main__":
    main()
