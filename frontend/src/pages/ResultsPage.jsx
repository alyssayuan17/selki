import QualityWarnings from "./components/QualityWarnings";

export default function ResultPage() {
  return (
    <div className="page">
      <QualityWarnings
        warnings={[
          "Audio quality is too poor for reliable analysis", // low_asr_confidence
          "Not enough speech detected in the recording", // low_speech_ratio
          "Poor audio quality and insufficient speech detected", // low_asr_and_speech_ratio, when both above conditions are true
          "Microphone volume is too low", // mic_quality === "very_quiet"
          "Excessive background noise detected", // mic_quality === "noisy"
          "High background noise may affect analysis", // background_noise_level === "high"
          "Moderate background noise detected", // background_noise_level === "medium"
        ]}
      />
    </div>
  );
}