import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import QualityWarningsPanel from "../components/QualityWarningsPanel";
import ScoreBadge from "../components/ScoreBadge";
import MetricsGrid from "../components/MetricsGrid";
import MetricDetailCard from "../components/MetricDetailCard";
import Timeline from "../components/Timeline";
import Transcript from "../components/Transcript";

export default function ResultPage() {
    const { jobId } = useParams();
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedMetric, setSelectedMetric] = useState(null);
    const [transcriptView, setTranscriptView] = useState("full");
    const [detailedTranscript, setDetailedTranscript] = useState(null);
    const [loadingDetailedTranscript, setLoadingDetailedTranscript] = useState(false);

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

    // fetch detailed transcript when user switches to segments or tokens view
    useEffect(() => {
        if ((transcriptView === "segments" || transcriptView === "tokens") && !detailedTranscript && !loadingDetailedTranscript) {
            setLoadingDetailedTranscript(true);

            fetch(`/api/v1/presentations/${jobId}/transcript`)
                .then((response) => {
                    if (!response.ok) {
                        throw new Error("Failed to fetch detailed transcript");
                    }
                    return response.json();
                })
                .then((result) => {
                    setDetailedTranscript(result.transcript);
                    setLoadingDetailedTranscript(false);
                })
                .catch((err) => {
                    console.error("Error fetching detailed transcript:", err);
                    setLoadingDetailedTranscript(false);
                });
        }
    }, [transcriptView, jobId, detailedTranscript, loadingDetailedTranscript]);

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

    // transform backend metrics to array for MetricsGrid
    const transformMetrics = (backendMetrics) => {
        if (!backendMetrics) return [];

        return Object.entries(backendMetrics).map(([name, metricData]) => ({
            id: name,
            label: name.replace(/_/g, ' ').toUpperCase(),
            value: metricData.abstained
                ? "N/A"
                : `${metricData.score_0_100}%`,
            subtext: metricData.abstained
                ? "Not available"
                : `${metricData.label} (${Math.round(metricData.confidence * 100)}% confidence)`,
            rawData: metricData
        }));
    };

    // handle delete job
    const handleDelete = async () => {
        if (!confirm("Are you sure you want to delete this analysis?")) return;

        try {
            const response = await fetch(`/api/v1/presentations/${jobId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                navigate('/');
            } else {
                alert('Failed to delete job');
            }
        } catch (err) {
            alert('Error deleting job: ' + err.message);
        }
    };

    if (loading) return <div className="page">Loading...</div>;
    if (error) return <div className="page">Error: {error}</div>;
    if (!data) return <div className="page">No data</div>;

    const warnings = buildWarnings(data.quality_flags);
    const score = data.overall_score?.score_0_100 || 0;
    const initial = data.input?.talk_type?.[0]?.toUpperCase() || "R";
    const metricsArray = transformMetrics(data.metrics);

    return (
        <div className="page">
            {/* Header with delete button */}
            <div className="results-header">
                <h2>Analysis Results</h2>
                <button
                    className="btn-delete"
                    onClick={handleDelete}
                    aria-label="Delete analysis"
                >
                    Delete
                </button>
            </div>

            <ScoreBadge score={score} initial={initial} />
            {warnings.length > 0 && <QualityWarningsPanel warnings={warnings} />}

            <MetricsGrid
                metrics={metricsArray}
                onMetricClick={(metric) => setSelectedMetric(metric.rawData)}
            />

            {selectedMetric && (
                <MetricDetailCard title={`${selectedMetric.label} Details`}>
                    <div>
                        <p><strong>Score:</strong> {selectedMetric.score_0_100 || "N/A"}/100</p>
                        <p><strong>Label:</strong> {selectedMetric.label}</p>
                        <p><strong>Confidence:</strong> {Math.round(selectedMetric.confidence * 100)}%</p>
                        <p><strong>Abstained:</strong> {selectedMetric.abstained ? "Yes" : "No"}</p>

                        {selectedMetric.details && Object.keys(selectedMetric.details).length > 0 && (
                            <>
                                <h4>Details:</h4>
                                <pre style={{ fontSize: '0.875rem', overflow: 'auto' }}>
                                    {JSON.stringify(selectedMetric.details, null, 2)}
                                </pre>
                            </>
                        )}

                        {selectedMetric.feedback && selectedMetric.feedback.length > 0 && (
                            <>
                                <h4>Feedback ({selectedMetric.feedback.length}):</h4>
                                {selectedMetric.feedback.map((fb, i) => (
                                    <div key={i} style={{
                                        padding: '0.75rem',
                                        marginBottom: '0.5rem',
                                        border: '1px solid #e5e7eb',
                                        borderRadius: '0.375rem'
                                    }}>
                                        <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                                            {fb.start_sec.toFixed(1)}s - {fb.end_sec.toFixed(1)}s
                                            {fb.tip_type && <span> • {fb.tip_type}</span>}
                                        </div>
                                        <p style={{ margin: '0.25rem 0 0 0' }}>{fb.message}</p>
                                    </div>
                                ))}
                            </>
                        )}
                    </div>
                </MetricDetailCard>
            )}

            {/* Timeline */}
            <Timeline
                events={data.timeline || []}
                duration={data.input?.duration_sec || 0}
                onSegmentClick={(segment) => console.log('Clicked segment:', segment)}
            />

            {/* Transcript with view mode toggle */}
            <div className="transcript-section">
                <div className="transcript-controls">
                    <button
                        className={transcriptView === "full" ? "active" : ""}
                        onClick={() => setTranscriptView("full")}
                    >
                        Full Text
                    </button>
                    <button
                        className={transcriptView === "segments" ? "active" : ""}
                        onClick={() => setTranscriptView("segments")}
                    >
                        Segments
                    </button>
                    <button
                        className={transcriptView === "tokens" ? "active" : ""}
                        onClick={() => setTranscriptView("tokens")}
                    >
                        Words
                    </button>
                </div>
                {loadingDetailedTranscript && (transcriptView === "segments" || transcriptView === "tokens") ? (
                    <div className="transcript-loading">Loading detailed transcript...</div>
                ) : (
                    <Transcript
                        transcript={transcriptView === "full" ? data.transcript : (detailedTranscript || data.transcript)}
                        viewMode={transcriptView}
                    />
                )}
            </div>

            {/* Model Metadata Footer */}
            {data.model_metadata && (
                <div className="model-metadata">
                    <h4>Model Information</h4>
                    <div className="model-metadata__grid">
                        <div><strong>ASR Model:</strong> {data.model_metadata.asr_model}</div>
                        <div><strong>VAD Model:</strong> {data.model_metadata.vad_model}</div>
                        <div><strong>Embedding Model:</strong> {data.model_metadata.embedding_model}</div>
                        <div><strong>Version:</strong> {data.model_metadata.version}</div>
                    </div>
                </div>
            )}
        </div>
    );
}