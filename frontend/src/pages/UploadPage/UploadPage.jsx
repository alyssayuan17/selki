import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import Navbar from "../../components/Navbar/Navbar";
import Button from "../../components/Button/Button";
import CustomSelect from "../../components/CustomSelect/CustomSelect";
import { useAuth } from "../../context/AuthContext";
import "./UploadPage.css";

export default function UploadPage() {
    const navigate = useNavigate();
    const location = useLocation();
    const { isLoggedIn } = useAuth();
    const [uploadMode, setUploadMode] = useState("file");
    const [file, setFile] = useState(null);
    const [audioUrl, setAudioUrl] = useState("");
    const [formData, setFormData] = useState({
        language: "en",
        talk_type: "",
        audience_type: "",
    });
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState(null);
    const [isDragging, setIsDragging] = useState(false);

    const handleDragOver = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const droppedFile = files[0];
            const allowedTypes = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.webm'];
            const fileExt = '.' + droppedFile.name.split('.').pop().toLowerCase();
            if (allowedTypes.includes(fileExt)) {
                setFile(droppedFile);
                setError(null);
            } else {
                setError(`Invalid file type. Allowed types: ${allowedTypes.join(', ')}`);
            }
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!isLoggedIn) { navigate(`/auth?returnTo=${encodeURIComponent(location.pathname)}`); return; }
        if (uploadMode === "file" && !file) { setError("Please select an audio file"); return; }
        if (uploadMode === "url" && !audioUrl) { setError("Please enter an audio URL"); return; }
        if (!formData.talk_type || !formData.audience_type) { setError("Please fill in all required fields"); return; }

        setUploading(true);
        setError(null);

        try {
            let response;
            if (uploadMode === "file") {
                const uploadFormData = new FormData();
                uploadFormData.append("file", file);
                uploadFormData.append("language", formData.language);
                uploadFormData.append("talk_type", formData.talk_type);
                uploadFormData.append("audience_type", formData.audience_type);
                uploadFormData.append("requested_metrics", JSON.stringify([
                    "pace", "pause_quality", "fillers", "intonation", "content_structure", "confidence_cv"
                ]));
                uploadFormData.append("user_metadata", JSON.stringify({}));
                response = await fetch("/api/v1/presentations/upload", { method: "POST", body: uploadFormData });
            } else {
                const payload = {
                    audio_url: audioUrl,
                    video_url: null,
                    language: formData.language,
                    talk_type: formData.talk_type,
                    audience_type: formData.audience_type,
                    requested_metrics: ["pace", "pause_quality", "fillers", "intonation", "content_structure", "confidence_cv"],
                    user_metadata: {}
                };
                response = await fetch("/api/v1/presentations", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });
            }

            if (!response.ok) {
                let errorMessage = "Submission failed";
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorData.message || errorMessage;
                } catch {
                    errorMessage = `Server error: ${response.status} ${response.statusText}`;
                }
                throw new Error(errorMessage);
            }

            const result = await response.json();
            navigate(`/processing/${result.job_id}`);
        } catch (err) {
            setError(err.message);
            setUploading(false);
        }
    };

    return (
        <>
            <Navbar />
            <div className="page upload-page">
                <h1 className="gradient-title upload-page__title">Present to Us!</h1>
                <p className="subtitle-text">Upload your audio file or provide a URL to get AI-powered feedback on your presentation</p>

                <div className="upload-mode-toggle">
                    <Button type="button" variant={uploadMode === "file" ? "primary" : "secondary"} onClick={() => setUploadMode("file")}>Upload File</Button>
                    <Button type="button" variant={uploadMode === "url" ? "primary" : "secondary"} onClick={() => setUploadMode("url")}>Enter URL</Button>
                </div>

                <form onSubmit={handleSubmit} className="upload-form">
                    {uploadMode === "file" ? (
                        <div
                            className={`upload-card ${isDragging ? 'upload-card--dragging' : ''}`}
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            onDrop={handleDrop}
                        >
                            <img src="/upload.svg" alt="Upload" className="upload-icon" />
                            <input
                                type="file"
                                id="file-input"
                                accept=".wav,.mp3,.m4a,.flac,.ogg,.webm"
                                onChange={(e) => { if (e.target.files.length > 0) setFile(e.target.files[0]); }}
                                style={{ display: 'none' }}
                            />
                            {file && <p className="file-name">{file.name}</p>}
                            <Button type="button" variant="primary" onClick={() => document.getElementById('file-input').click()}>
                                {file ? "Change File" : "Upload File"}
                            </Button>
                            <p className="upload-subtitle">or drop a file</p>
                            <p className="file-types-hint">Accepted: WAV, MP3, M4A, FLAC, OGG, WEBM</p>
                        </div>
                    ) : (
                        <div className="form-group url-form-group">
                            <label htmlFor="audio_url">Audio URL *</label>
                            <input
                                type="url"
                                id="audio_url"
                                className="form-control"
                                placeholder="https://example.com/audio.mp3"
                                value={audioUrl}
                                onChange={(e) => setAudioUrl(e.target.value)}
                                required
                            />
                            <small className="form-hint">Enter a direct URL to an audio file (mp3, wav, m4a, etc.)</small>
                        </div>
                    )}

                    <div className="form-fields-row">
                        <div className="form-group">
                            <label htmlFor="talk_type">Presentation Type *</label>
                            <CustomSelect
                                id="talk_type"
                                value={formData.talk_type}
                                onChange={(e) => setFormData({ ...formData, talk_type: e.target.value })}
                                required
                                options={[
                                    { value: "", label: "Select type..." },
                                    { value: "pitch", label: "Pitch" },
                                    { value: "lecture", label: "Lecture" },
                                    { value: "meeting", label: "Meeting" },
                                    { value: "interview", label: "Interview" },
                                    { value: "speech", label: "Speech" },
                                    { value: "other", label: "Other" },
                                ]}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="audience_type">Audience Type *</label>
                            <CustomSelect
                                id="audience_type"
                                value={formData.audience_type}
                                onChange={(e) => setFormData({ ...formData, audience_type: e.target.value })}
                                required
                                options={[
                                    { value: "", label: "Select audience..." },
                                    { value: "general", label: "General" },
                                    { value: "technical", label: "Technical" },
                                    { value: "executive", label: "Executive" },
                                    { value: "academic", label: "Academic" },
                                    { value: "students", label: "Students" },
                                ]}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="language">Language</label>
                            <CustomSelect
                                id="language"
                                value={formData.language}
                                onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                                options={[
                                    { value: "en", label: "English" },
                                    { value: "es", label: "Spanish" },
                                    { value: "fr", label: "French" },
                                    { value: "de", label: "German" },
                                ]}
                            />
                        </div>
                        <div className="form-group button-group">
                            <label>&nbsp;</label>
                            <Button
                                type="submit"
                                variant="primary"
                                disabled={uploading || (uploadMode === "file" ? !file : !audioUrl) || !formData.talk_type || !formData.audience_type}
                            >
                                {uploading ? "Submitting..." : "Analyze Presentation"}
                            </Button>
                        </div>
                    </div>

                    {error && <div className="error-message">{error}</div>}
                </form>
            </div>
        </>
    );
}
