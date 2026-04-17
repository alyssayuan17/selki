import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
    Cell, ReferenceLine, ResponsiveContainer,
} from "recharts";
import Navbar from "../components/Navbar/Navbar";
import QualityWarningsPanel from "../components/QualityWarnings/QualityWarningsPanel";
import ScoreBadge from "../components/ScoreBadge/ScoreBadge";
import MetricsGrid from "../components/MetricsGrid/MetricsGrid";
import MetricDetailCard from "../components/MetricDetailCard";
import Timeline from "../components/Timeline";
import Transcript from "../components/Transcript";

// ---------------------------------------------------------------------------
// Per-metric detail components
// ---------------------------------------------------------------------------

function StatRow({ label, value }) {
    return (
        <div style={{ display: "flex", justifyContent: "space-between", padding: "0.35rem 0", borderBottom: "1px solid #f3f4f6" }}>
            <span style={{ color: "#6b7280", fontSize: "0.875rem" }}>{label}</span>
            <span style={{ fontWeight: 600, fontSize: "0.875rem" }}>{value}</span>
        </div>
    );
}

function wpmColor(wpm) {
    if (wpm < 110) return "#f59e0b";
    if (wpm > 170) return "#ef4444";
    return "#22c55e";
}

function PaceDetails({ details }) {
    if (!details) return null;
    const segments = (details.segment_stats || []).map((s, i) => {
        const startMin = Math.floor(s.start_sec / 60);
        const startSec = Math.floor(s.start_sec % 60);
        return {
            name: `${startMin}:${String(startSec).padStart(2, "0")}`,
            wpm: Math.round(s.wpm),
        };
    });

    return (
        <div>
            <StatRow label="Average WPM" value={details.average_wpm?.toFixed(1) ?? "—"} />
            <StatRow label="Optimal range" value="110 – 170 WPM" />
            {segments.length > 0 && (
                <div style={{ marginTop: "1rem" }}>
                    <p style={{ fontSize: "0.8rem", color: "#9ca3af", marginBottom: "0.5rem" }}>
                        WPM by 30-second segment &nbsp;
                        <span style={{ color: "#f59e0b" }}>■</span> slow &nbsp;
                        <span style={{ color: "#22c55e" }}>■</span> optimal &nbsp;
                        <span style={{ color: "#ef4444" }}>■</span> fast
                    </p>
                    <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={segments} margin={{ top: 4, right: 8, bottom: 4, left: -16 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                            <YAxis domain={[0, 250]} tick={{ fontSize: 11 }} />
                            <Tooltip formatter={(v) => [`${v} WPM`, "Pace"]} />
                            <ReferenceLine y={110} stroke="#f59e0b" strokeDasharray="4 2" />
                            <ReferenceLine y={170} stroke="#ef4444" strokeDasharray="4 2" />
                            <Bar dataKey="wpm" radius={[4, 4, 0, 0]}>
                                {segments.map((entry, idx) => (
                                    <Cell key={idx} fill={wpmColor(entry.wpm)} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            )}
        </div>
    );
}

function FillersDetails({ details }) {
    if (!details) return null;
    const topFillers = details.top_fillers || [];
    const spikes = details.filler_spikes || [];

    return (
        <div>
            <StatRow label="Fillers per minute" value={details.filler_rate_per_min?.toFixed(1) ?? "—"} />
            <StatRow label="Fillers per 100 words" value={details.fillers_per_100_words?.toFixed(1) ?? "—"} />
            <StatRow label="Total fillers" value={details.total_fillers ?? "—"} />

            {topFillers.length > 0 && (
                <div style={{ marginTop: "0.75rem" }}>
                    <p style={{ fontSize: "0.8rem", color: "#6b7280", marginBottom: "0.4rem" }}>Most common fillers</p>
                    <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                        {topFillers.map((f, i) => (
                            <span key={i} style={{
                                background: "#fef3c7", color: "#92400e",
                                borderRadius: "999px", padding: "0.2rem 0.6rem",
                                fontSize: "0.8rem", fontWeight: 500,
                            }}>
                                "{f.token}" × {f.count}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {spikes.length > 0 && (
                <div style={{ marginTop: "0.75rem" }}>
                    <p style={{ fontSize: "0.8rem", color: "#6b7280", marginBottom: "0.4rem" }}>High-filler segments</p>
                    {spikes.map((s, i) => (
                        <div key={i} style={{
                            fontSize: "0.8rem", padding: "0.3rem 0",
                            borderBottom: "1px solid #f3f4f6", color: "#374151",
                        }}>
                            {s.start_sec.toFixed(0)}s – {s.end_sec.toFixed(0)}s &nbsp;·&nbsp;
                            <strong>{s.filler_rate?.toFixed(1)} / min</strong>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function PauseDetails({ details }) {
    if (!details) return null;
    const helpful = Math.round((details.helpful_ratio ?? 0) * 100);
    const awkward = Math.round((details.awkward_ratio ?? 0) * 100);

    return (
        <div>
            <StatRow label="Total pauses" value={details.total_pauses ?? "—"} />
            <StatRow label="Helpful pauses" value={`${details.helpful_count ?? "—"} (${helpful}%)`} />
            <StatRow label="Awkward pauses" value={`${details.awkward_count ?? "—"} (${awkward}%)`} />
            <StatRow label="Avg pause duration" value={details.average_pause_duration != null ? `${details.average_pause_duration.toFixed(2)}s` : "—"} />
            <StatRow label="Pause rate" value={details.pause_rate != null ? `${details.pause_rate.toFixed(2)} / min` : "—"} />

            {/* Simple ratio bar */}
            <div style={{ marginTop: "1rem" }}>
                <p style={{ fontSize: "0.8rem", color: "#6b7280", marginBottom: "0.4rem" }}>Helpful vs Awkward</p>
                <div style={{ display: "flex", height: "12px", borderRadius: "6px", overflow: "hidden", background: "#f3f4f6" }}>
                    <div style={{ width: `${helpful}%`, background: "#22c55e", transition: "width 0.4s" }} />
                    <div style={{ width: `${awkward}%`, background: "#ef4444", transition: "width 0.4s" }} />
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "#9ca3af", marginTop: "0.2rem" }}>
                    <span style={{ color: "#16a34a" }}>Helpful {helpful}%</span>
                    <span style={{ color: "#dc2626" }}>Awkward {awkward}%</span>
                </div>
            </div>
        </div>
    );
}

function IntonationDetails({ details }) {
    if (!details) return null;
    return (
        <div>
            <StatRow label="Mean pitch" value={details.mean_pitch_hz != null ? `${details.mean_pitch_hz.toFixed(1)} Hz` : "—"} />
            <StatRow label="Pitch variation (std)" value={details.pitch_std_hz != null ? `${details.pitch_std_hz.toFixed(1)} Hz` : "—"} />
            <StatRow label="Pitch range (5–95th %ile)" value={details.pitch_range_hz != null ? `${details.pitch_range_hz.toFixed(1)} Hz` : "—"} />
            <StatRow label="Pitch CoV" value={details.pitch_cov != null ? details.pitch_cov.toFixed(3) : "—"} />
            <StatRow label="Avg energy" value={details.energy_mean != null ? details.energy_mean.toFixed(4) : "—"} />
            <StatRow label="Energy variation (std)" value={details.energy_std != null ? details.energy_std.toFixed(4) : "—"} />
            <div style={{ marginTop: "0.75rem", fontSize: "0.8rem", color: "#6b7280" }}>
                A pitch range &gt; 100 Hz indicates expressive, engaging speech.
                Aim for CoV &gt; 0.15 for dynamic delivery.
            </div>
        </div>
    );
}

function ContentDetails({ details }) {
    if (!details) return null;
    const examples = details.signpost_examples || [];
    return (
        <div>
            <StatRow label="Sentences" value={details.num_sentences ?? "—"} />
            <StatRow label="Avg sentence length" value={details.avg_sentence_length_tokens != null ? `${details.avg_sentence_length_tokens.toFixed(1)} words` : "—"} />
            <StatRow label="Long sentences (> 30 words)" value={details.long_sentence_count ?? "—"} />
            <StatRow label="Signpost phrases" value={details.signpost_count ?? "—"} />
            <StatRow label="Low signposts flag" value={details.low_signposts ? "Yes ⚠️" : "No ✓"} />
            <StatRow label="Many long sentences" value={details.many_long_sentences ? "Yes ⚠️" : "No ✓"} />

            {examples.length > 0 && (
                <div style={{ marginTop: "0.75rem" }}>
                    <p style={{ fontSize: "0.8rem", color: "#6b7280", marginBottom: "0.4rem" }}>Signpost examples</p>
                    {examples.map((ex, i) => (
                        <div key={i} style={{
                            fontSize: "0.8rem", color: "#374151",
                            padding: "0.3rem 0.5rem",
                            background: "#f0fdf4",
                            borderRadius: "0.25rem",
                            marginBottom: "0.25rem",
                            borderLeft: "3px solid #22c55e",
                        }}>
                            "{ex}"
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function MetricDetails({ metricId, details }) {
    if (!details || details.reason) {
        return <p style={{ color: "#9ca3af", fontSize: "0.875rem" }}>No detail data available.</p>;
    }
    if (metricId === "pace") return <PaceDetails details={details} />;
    if (metricId === "fillers") return <FillersDetails details={details} />;
    if (metricId === "pause_quality") return <PauseDetails details={details} />;
    if (metricId === "intonation") return <IntonationDetails details={details} />;
    if (metricId === "content_structure") return <ContentDetails details={details} />;

    // Generic fallback: key–value table
    return (
        <div>
            {Object.entries(details).map(([k, v]) => (
                <StatRow
                    key={k}
                    label={k.replace(/_/g, " ")}
                    value={typeof v === "object" ? JSON.stringify(v) : String(v)}
                />
            ))}
        </div>
    );
}

// ---------------------------------------------------------------------------
// Main ResultPage
// ---------------------------------------------------------------------------

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
            .then((r) => {
                if (!r.ok) throw new Error("Failed to fetch results");
                return r.json();
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

    useEffect(() => {
        if (
            (transcriptView === "segments" || transcriptView === "tokens") &&
            !detailedTranscript && !loadingDetailedTranscript
        ) {
            setLoadingDetailedTranscript(true);
            fetch(`/api/v1/presentations/${jobId}/transcript`)
                .then((r) => {
                    if (!r.ok) throw new Error("Failed to fetch transcript");
                    return r.json();
                })
                .then((result) => {
                    setDetailedTranscript(result.transcript);
                    setLoadingDetailedTranscript(false);
                })
                .catch((err) => {
                    console.error("Error fetching transcript:", err);
                    setLoadingDetailedTranscript(false);
                });
        }
    }, [transcriptView, jobId, detailedTranscript, loadingDetailedTranscript]);

    const buildWarnings = (qualityFlags) => {
        if (!qualityFlags) return [];
        const warnings = [];
        const { abstain_reason, mic_quality, background_noise_level } = qualityFlags;
        if (abstain_reason === "low_asr_confidence")
            warnings.push("Audio quality is too poor for reliable analysis");
        else if (abstain_reason === "low_speech_ratio")
            warnings.push("Not enough speech detected in the recording");
        else if (abstain_reason === "low_asr_and_speech_ratio")
            warnings.push("Poor audio quality and insufficient speech detected");
        if (mic_quality === "very_quiet") warnings.push("Microphone volume is too low");
        else if (mic_quality === "noisy") warnings.push("Excessive background noise detected");
        if (background_noise_level === "high")
            warnings.push("High background noise may affect analysis");
        else if (background_noise_level === "medium")
            warnings.push("Moderate background noise detected");
        return warnings;
    };

    const transformMetrics = (backendMetrics) => {
        if (!backendMetrics) return [];
        return Object.entries(backendMetrics).map(([name, metricData]) => ({
            id: name,
            label: name.replace(/_/g, " ").toUpperCase(),
            value: metricData.abstained ? "N/A" : `${metricData.score_0_100}%`,
            subtext: metricData.abstained
                ? "Not available"
                : `${metricData.label.replace(/_/g, " ")} · ${Math.round(metricData.confidence * 100)}% confidence`,
            rawData: metricData,
        }));
    };

    const handleDelete = async () => {
        if (!confirm("Are you sure you want to delete this analysis?")) return;
        try {
            const response = await fetch(`/api/v1/presentations/${jobId}`, { method: "DELETE" });
            if (response.ok) {
                navigate("/history");
            } else {
                alert("Failed to delete job");
            }
        } catch (err) {
            alert("Error deleting job: " + err.message);
        }
    };

    if (loading) return <><Navbar /><div className="page">Loading...</div></>;
    if (error) return <><Navbar /><div className="page">Error: {error}</div></>;
    if (!data) return <><Navbar /><div className="page">No data</div></>;

    const warnings = buildWarnings(data.quality_flags);
    const score = data.overall_score?.score_0_100 ?? 0;
    const initial = data.input?.talk_type?.[0]?.toUpperCase() ?? "R";
    const metricsArray = transformMetrics(data.metrics);

    return (
        <>
            <Navbar />
            <div className="page">
                <div className="results-header">
                    <h2>Analysis Results</h2>
                    <button className="btn-delete" onClick={handleDelete} aria-label="Delete analysis">
                        Delete
                    </button>
                </div>

                <ScoreBadge score={score} initial={initial} />
                {warnings.length > 0 && <QualityWarningsPanel warnings={warnings} />}

                <MetricsGrid
                    metrics={metricsArray}
                    onMetricClick={(metric) => setSelectedMetric(
                        selectedMetric?.label === metric.rawData.label && selectedMetric?.id === metric.id
                            ? null
                            : { ...metric.rawData, id: metric.id }
                    )}
                />

                {selectedMetric && (
                    <MetricDetailCard title={selectedMetric.id.replace(/_/g, " ").toUpperCase()}>
                        <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap", marginBottom: "1rem" }}>
                            <div>
                                <span style={{ fontSize: "0.75rem", color: "#9ca3af" }}>Score</span>
                                <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#1f2937" }}>
                                    {selectedMetric.score_0_100 ?? "N/A"}<span style={{ fontSize: "0.9rem" }}>/100</span>
                                </div>
                            </div>
                            <div>
                                <span style={{ fontSize: "0.75rem", color: "#9ca3af" }}>Label</span>
                                <div style={{ fontWeight: 600, textTransform: "capitalize", color: "#374151" }}>
                                    {selectedMetric.label?.replace(/_/g, " ")}
                                </div>
                            </div>
                            <div>
                                <span style={{ fontSize: "0.75rem", color: "#9ca3af" }}>Confidence</span>
                                <div style={{ fontWeight: 600, color: "#374151" }}>
                                    {Math.round(selectedMetric.confidence * 100)}%
                                </div>
                            </div>
                        </div>

                        <MetricDetails
                            metricId={selectedMetric.id}
                            details={selectedMetric.details}
                        />

                        {selectedMetric.feedback?.length > 0 && (
                            <div style={{ marginTop: "1rem" }}>
                                <p style={{ fontSize: "0.8rem", color: "#6b7280", marginBottom: "0.5rem" }}>
                                    Feedback ({selectedMetric.feedback.length})
                                </p>
                                {selectedMetric.feedback.map((fb, i) => (
                                    <div key={i} style={{
                                        padding: "0.75rem",
                                        marginBottom: "0.5rem",
                                        border: "1px solid #e5e7eb",
                                        borderRadius: "0.375rem",
                                        borderLeft: "3px solid #88C7FD",
                                    }}>
                                        <div style={{ fontSize: "0.75rem", color: "#9ca3af", marginBottom: "0.25rem" }}>
                                            {fb.start_sec?.toFixed(1)}s – {fb.end_sec?.toFixed(1)}s
                                            {fb.tip_type && <span> · {fb.tip_type.replace(/_/g, " ")}</span>}
                                        </div>
                                        <p style={{ margin: 0, fontSize: "0.875rem" }}>{fb.message}</p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </MetricDetailCard>
                )}

                <Timeline
                    events={data.timeline || []}
                    duration={data.input?.duration_sec || 0}
                    onSegmentClick={(segment) => console.log("Clicked segment:", segment)}
                />

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

                {data.model_metadata && (
                    <div className="model-metadata">
                        <h4>Model Information</h4>
                        <div className="model-metadata__grid">
                            <div><strong>ASR Model:</strong> {data.model_metadata.asr_model}</div>
                            <div><strong>VAD Model:</strong> {data.model_metadata.vad_model}</div>
                            <div><strong>Version:</strong> {data.model_metadata.version}</div>
                        </div>
                    </div>
                )}
            </div>
        </>
    );
}
