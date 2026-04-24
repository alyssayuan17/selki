import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
    Cell, ReferenceLine, ResponsiveContainer
} from "recharts";
import Navbar from "../components/Navbar/Navbar";
import QualityWarningsPanel from "../components/QualityWarnings/QualityWarningsPanel";
import ScoreBadge from "../components/ScoreBadge/ScoreBadge";
import MetricsGrid from "../components/MetricsGrid/MetricsGrid";
import Timeline from "../components/Timeline";
import Transcript from "../components/Transcript";
import Button from "../components/Button/Button";
import "./ResultsPage.css";

// ── Shared helpers ──────────────────────────────────────────────────────────

function StatRow({ label, value }) {
    return (
        <div style={{ display: "flex", justifyContent: "space-between", padding: "0.3rem 0", borderBottom: "1px solid #f3f4f6" }}>
            <span style={{ color: "#6b7280", fontSize: "0.875rem" }}>{label}</span>
            <span style={{ fontWeight: 500, fontSize: "0.875rem" }}>{value}</span>
        </div>
    );
}

function wpmColor(wpm) {
    if (wpm < 110) return "#f59e0b";
    if (wpm <= 170) return "#22c55e";
    return "#ef4444";
}

// ── Per-metric detail components ────────────────────────────────────────────

function PaceDetails({ data }) {
    const d = data?.details;
    if (!d) return null;
    const segments = d.segment_stats || [];
    const chartData = segments.map((s, idx) => ({
        name: `Seg ${idx + 1}`,
        wpm: Math.round(s.wpm || 0),
    }));
    return (
        <div>
            <StatRow label="Average WPM" value={`${Math.round(d.average_wpm)} wpm`} />
            <StatRow label="Optimal range" value="110 – 170 wpm" />
            {chartData.length > 0 && (
                <div style={{ marginTop: "1rem" }}>
                    <p style={{ fontSize: "0.8rem", color: "#6b7280", marginBottom: "0.5rem" }}>WPM by segment</p>
                    <ResponsiveContainer width="100%" height={180}>
                        <BarChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                            <YAxis tick={{ fontSize: 11 }} domain={[0, "auto"]} />
                            <Tooltip formatter={(v) => [`${v} wpm`, "WPM"]} />
                            <ReferenceLine y={110} stroke="#f59e0b" strokeDasharray="4 4" />
                            <ReferenceLine y={170} stroke="#ef4444" strokeDasharray="4 4" />
                            <Bar dataKey="wpm" radius={[4, 4, 0, 0]}>
                                {chartData.map((entry, idx) => (
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

function FillersDetails({ data }) {
    const d = data?.details;
    if (!d) return null;
    const topFillers = d.top_fillers || [];
    const spikes = d.filler_spikes || [];
    return (
        <div>
            <StatRow label="Fillers per minute" value={(d.fillers_per_minute ?? "—").toString()} />
            <StatRow label="Total fillers" value={(d.total_fillers ?? "—").toString()} />
            {topFillers.length > 0 && (
                <div style={{ marginTop: "0.75rem" }}>
                    <p style={{ fontSize: "0.8rem", color: "#6b7280", marginBottom: "0.4rem" }}>Top fillers</p>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                        {topFillers.map(([word, count]) => (
                            <span key={word} style={{ background: "#fef3c7", color: "#92400e", padding: "0.2rem 0.6rem", borderRadius: 999, fontSize: "0.8rem" }}>
                                "{word}" ×{count}
                            </span>
                        ))}
                    </div>
                </div>
            )}
            {spikes.length > 0 && (
                <div style={{ marginTop: "0.75rem" }}>
                    <p style={{ fontSize: "0.8rem", color: "#6b7280", marginBottom: "0.4rem" }}>Filler spikes</p>
                    {spikes.map((sp, idx) => (
                        <div key={idx} style={{ fontSize: "0.8rem", color: "#374151", marginBottom: "0.2rem" }}>
                            {sp.start_sec?.toFixed(1)}s – {sp.end_sec?.toFixed(1)}s: {sp.count} fillers
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function PauseDetails({ data }) {
    const d = data?.details;
    if (!d) return null;
    const goodRatio = d.good_pause_ratio ?? 0;
    const badRatio = d.bad_pause_ratio ?? 0;
    return (
        <div>
            <StatRow label="Total pauses" value={(d.total_pauses ?? "—").toString()} />
            <StatRow label="Good pauses" value={(d.good_pauses ?? "—").toString()} />
            <StatRow label="Bad pauses" value={(d.bad_pauses ?? "—").toString()} />
            <div style={{ marginTop: "0.75rem" }}>
                <p style={{ fontSize: "0.8rem", color: "#6b7280", marginBottom: "0.4rem" }}>Pause quality ratio</p>
                <div style={{ display: "flex", height: 12, borderRadius: 6, overflow: "hidden", background: "#f3f4f6" }}>
                    <div style={{ width: `${goodRatio * 100}%`, background: "#22c55e" }} />
                    <div style={{ width: `${badRatio * 100}%`, background: "#ef4444" }} />
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "#6b7280", marginTop: "0.25rem" }}>
                    <span>Good {Math.round(goodRatio * 100)}%</span>
                    <span>Bad {Math.round(badRatio * 100)}%</span>
                </div>
            </div>
        </div>
    );
}

function IntonationDetails({ data }) {
    const d = data?.details;
    if (!d) return null;
    return (
        <div>
            <StatRow label="Mean pitch (Hz)" value={(d.mean_pitch ?? "—").toString()} />
            <StatRow label="Pitch std dev" value={(d.pitch_std ?? "—").toString()} />
            <StatRow label="Pitch range" value={d.pitch_range != null ? `${d.pitch_range} Hz` : "—"} />
            <StatRow label="Coeff of variation" value={d.pitch_cov != null ? `${(d.pitch_cov * 100).toFixed(1)}%` : "—"} />
            <StatRow label="Energy (RMS)" value={(d.mean_energy ?? "—").toString()} />
        </div>
    );
}

function ContentDetails({ data }) {
    const d = data?.details;
    if (!d) return null;
    const signposts = d.signpost_phrases || [];
    return (
        <div>
            <StatRow label="Sentences" value={(d.sentence_count ?? "—").toString()} />
            <StatRow label="Avg sentence length" value={d.avg_sentence_length != null ? `${d.avg_sentence_length.toFixed(1)} words` : "—"} />
            <StatRow label="Signpost phrases" value={(d.signpost_count ?? "—").toString()} />
            {signposts.length > 0 && (
                <div style={{ marginTop: "0.75rem" }}>
                    <p style={{ fontSize: "0.8rem", color: "#6b7280", marginBottom: "0.4rem" }}>Signpost examples</p>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                        {signposts.slice(0, 6).map((p, idx) => (
                            <span key={idx} style={{ background: "#dbeafe", color: "#1e40af", padding: "0.2rem 0.6rem", borderRadius: 999, fontSize: "0.8rem" }}>
                                {p}
                            </span>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

function MetricDetails({ metricId, data }) {
    if (!data) return null;
    if (metricId === "pace") return <PaceDetails data={data} />;
    if (metricId === "fillers") return <FillersDetails data={data} />;
    if (metricId === "pause_quality") return <PauseDetails data={data} />;
    if (metricId === "intonation") return <IntonationDetails data={data} />;
    if (metricId === "content_structure") return <ContentDetails data={data} />;
    return null;
}

function MetricDetailCard({ metricId, metricName, data }) {
    if (!data) return null;
    const feedback = data.feedback || [];
    return (
        <div className="metric-detail-card">
            <div className="metric-detail-card__header">
                <h3 className="metric-detail-card__name">{metricName}</h3>
                {!data.abstained && (
                    <>
                        <span className="metric-detail-card__score">{data.score_0_100}%</span>
                        <span className="metric-detail-card__badge">
                            {data.label} · {Math.round(data.confidence * 100)}% confidence
                        </span>
                    </>
                )}
            </div>

            <MetricDetails metricId={metricId} data={data} />

            {feedback.length > 0 && (
                <div className="metric-detail-card__feedback-section">
                    <p className="metric-detail-card__feedback-label">Feedback</p>
                    {feedback.map((fb, idx) => (
                        <div key={idx} className="metric-detail-card__feedback-item">
                            {fb.start_sec != null && (
                                <span className="metric-detail-card__feedback-time">
                                    {fb.start_sec.toFixed(1)}s
                                </span>
                            )}
                            {fb.message}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// ── Main page ───────────────────────────────────────────────────────────────

export default function ResultPage() {
    const { jobId } = useParams();
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedMetric, setSelectedMetric] = useState(null);
    const [selectedMetricName, setSelectedMetricName] = useState(null);
    const [viewIdx, setViewIdx] = useState(0);
    const [animDir, setAnimDir] = useState("forward");
    const [detailedTranscript, setDetailedTranscript] = useState(null);
    const [loadingDetailedTranscript, setLoadingDetailedTranscript] = useState(false);

    const VIEWS = [
        { id: "full",     title: "Full Text", description: "Plain transcript of everything said" },
        { id: "segments", title: "Segments",  description: "Transcript split by timed speech segments" },
        { id: "tokens",   title: "Words",     description: "Word-level view with filler words highlighted" },
    ];
    const transcriptView = VIEWS[viewIdx].id;
    const goNext = () => { setAnimDir("forward"); setViewIdx(i => i + 1); };
    const goBack = () => { setAnimDir("back");    setViewIdx(i => i - 1); };
    const goToIdx = (i) => { setAnimDir(i > viewIdx ? "forward" : "back"); setViewIdx(i); };

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

        return Object.entries(backendMetrics).map(([name, metricData]) => {
            // Extract overall performance message (first feedback item that spans full duration)
            let performanceMessage = null;
            if (metricData.feedback && metricData.feedback.length > 0) {
                const overallFeedback = metricData.feedback.find(
                    fb => fb.start_sec === 0 || fb.start_sec === 0.0
                );
                if (overallFeedback) {
                    performanceMessage = overallFeedback.message;
                }
            }

            return {
                id: name,
                label: name.replace(/_/g, ' ').toUpperCase(),
                value: metricData.abstained
                    ? "N/A"
                    : `${metricData.score_0_100}%`,
                subtext: metricData.abstained
                    ? "Not available"
                    : `${metricData.label} (${Math.round(metricData.confidence * 100)}% confidence)`,
                performanceMessage: performanceMessage,
                rawData: metricData
            };
        });
    };

    // handle delete job
    const handleDelete = async () => {
        if (!confirm("Are you sure you want to delete this analysis?")) return;

        try {
            const response = await fetch(`/api/v1/presentations/${jobId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                navigate('/history');
            } else {
                alert('Failed to delete job');
            }
        } catch (err) {
            alert('Error deleting job: ' + err.message);
        }
    };

    if (loading) return <><Navbar /><div className="page">Loading...</div></>;
    if (error) return <><Navbar /><div className="page">Error: {error}</div></>;
    if (!data) return <><Navbar /><div className="page">No data</div></>;

    const warnings = buildWarnings(data.quality_flags);
    const score = data.overall_score?.score_0_100 || 0;
    const initial = data.input?.talk_type?.[0]?.toUpperCase() || "R";
    const metricsArray = transformMetrics(data.metrics);

    return (
        <>
        <Navbar />
        <div className="page">
            {/* Header with delete button */}
            <div className="results-header">
                <Button
                    variant="secondary"
                    onClick={handleDelete}
                >
                    Delete
                </Button>
            </div>

            <ScoreBadge score={score} initial={initial} />
            {warnings.length > 0 && <QualityWarningsPanel warnings={warnings} />}

            <MetricsGrid
                metrics={metricsArray}
                selectedMetricId={selectedMetricName}
                onMetricClick={(metric) => {
                    if (metric.id === selectedMetricName) {
                        setSelectedMetric(null);
                        setSelectedMetricName(null);
                    } else {
                        setSelectedMetric(metric.rawData);
                        setSelectedMetricName(metric.id);
                    }
                }}
            />

            {selectedMetric && (
                <MetricDetailCard
                    metricId={selectedMetricName}
                    metricName={selectedMetricName?.replace(/_/g, ' ').toUpperCase()}
                    data={selectedMetric}
                />
            )}

            {/* Timeline */}
            <Timeline
                events={data.timeline || []}
                duration={data.input?.duration_sec || 0}
                selectedMetric={selectedMetricName}
                onSegmentClick={(segment) => console.log('Clicked segment:', segment)}
            />

            {/* Transcript Carousel */}
            <div className="transcript-carousel">
                <div className="transcript-carousel__macbar">
                    <span className="transcript-carousel__dot transcript-carousel__dot--red" />
                    <span className="transcript-carousel__dot transcript-carousel__dot--yellow" />
                    <span className="transcript-carousel__dot transcript-carousel__dot--green" />
                </div>
                <div className="transcript-carousel__header">
                    <span className="tc-title">Transcript Views</span>
                    <div className="transcript-carousel__dots">
                        {VIEWS.map((_, i) => (
                            <button
                                key={i}
                                className={`tc-dot${i === viewIdx ? " tc-dot--active" : ""}`}
                                onClick={() => goToIdx(i)}
                                aria-label={VIEWS[i].title}
                            />
                        ))}
                    </div>
                </div>

                <div className="transcript-carousel__info">
                    <span className="tc-view-title">{VIEWS[viewIdx].title}</span>
                    <span className="tc-view-desc">{VIEWS[viewIdx].description}</span>
                </div>

                <div className={`tc-content tc-content--${animDir}`} key={`${viewIdx}-${animDir}`}>
                    {loadingDetailedTranscript && (transcriptView === "segments" || transcriptView === "tokens") ? (
                        <div className="transcript-loading">Loading detailed transcript...</div>
                    ) : (
                        <Transcript
                            transcript={transcriptView === "full" ? data.transcript : (detailedTranscript || data.transcript)}
                            viewMode={transcriptView}
                        />
                    )}
                </div>

                <div className="tc-nav">
                    <button onClick={goBack} disabled={viewIdx === 0} className="btn btn-secondary tc-nav-btn">← Back</button>
                    <span className="tc-nav-counter">{viewIdx + 1} / {VIEWS.length}</span>
                    <button onClick={goNext} disabled={viewIdx === VIEWS.length - 1} className="btn btn-primary tc-nav-btn">Next →</button>
                </div>
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
        </>
    );
}
