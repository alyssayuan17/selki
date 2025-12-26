import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import QualityWarningsPanel from "../components/QualityWarningsPanel";
import ScoreBadge from "../components/ScoreBadge";

export default function ResultPage() {
    const { jobId } = useParams();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetch(`/api/v1/presentations/${jobId}/full`)
        .then((response) => {
            if (!response.ok) {
            throw new Error("Failed to fetch results");
            }
            return response.json();
        })
        .then((result) => {
            setData(result);
            setLoading(false);
        })
        .catch((err) => {
            setError(err.message);
            setLoading(false);
        });
    }, [jobId]);

    // build warnings array from quality_flags
    const buildWarnings = (qualityFlags) => {
        if (!qualityFlags) return [];

        const warnings = [];
        const { abstain_reason, mic_quality, background_noise_level } = qualityFlags;

        // abstain_reason warnings
        if (abstain_reason === "low_asr_confidence") {
        warnings.push("Audio quality is too poor for reliable analysis");
        } else if (abstain_reason === "low_speech_ratio") {
        warnings.push("Not enough speech detected in the recording");
        } else if (abstain_reason === "low_asr_and_speech_ratio") {
        warnings.push("Poor audio quality and insufficient speech detected");
        }

        // mic_quality warnings
        if (mic_quality === "very_quiet") {
        warnings.push("Microphone volume is too low");
        } else if (mic_quality === "noisy") {
        warnings.push("Excessive background noise detected");
        }

        // background_noise_level warnings
        if (background_noise_level === "high") {
        warnings.push("High background noise may affect analysis");
        } else if (background_noise_level === "medium") {
        warnings.push("Moderate background noise detected");
        }

        return warnings;
    };

    if (loading) return <div className="page">Loading...</div>;
    if (error) return <div className="page">Error: {error}</div>;
    if (!data) return <div className="page">No data</div>;

    const warnings = buildWarnings(data.quality_flags);
    const score = data.overall_score?.score_0_100 || 0;
    const initial = data.input?.talk_type?.[0]?.toUpperCase() || "R";

    return (
        <div className="page">
        <ScoreBadge score={score} initial={initial} />
        {warnings.length > 0 && <QualityWarningsPanel warnings={warnings} />}
        </div>
    );
}