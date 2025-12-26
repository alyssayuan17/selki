import { useState } from "react";
import { useNavigate } from "react-router-dom";
import FileDropzone from "../components/FileDropzone";

export default function UploadPage() {
    const navigate = useNavigate();
    const [uploadMode, setUploadMode] = useState("file"); // "file" or "url"
    const [file, setFile] = useState(null);
    const [audioUrl, setAudioUrl] = useState("");
    const [formData, setFormData] = useState({
        language: "en",
        talk_type: "",
        audience_type: "",
    });
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();

        // Validate based on mode
        if (uploadMode === "file" && !file) {
            setError("Please select an audio file");
            return;
        }

        if (uploadMode === "url" && !audioUrl) {
            setError("Please enter an audio URL");
            return;
        }

        if (!formData.talk_type || !formData.audience_type) {
            setError("Please fill in all required fields");
            return;
        }

        setUploading(true);
        setError(null);

        try {
            let response;

            if (uploadMode === "file") {
                // File upload mode
                const uploadFormData = new FormData();
                uploadFormData.append("file", file);
                uploadFormData.append("language", formData.language);
                uploadFormData.append("talk_type", formData.talk_type);
                uploadFormData.append("audience_type", formData.audience_type);
                uploadFormData.append("requested_metrics", JSON.stringify([
                    "pace",
                    "pause_quality",
                    "fillers",
                    "intonation",
                    "content_structure"
                ]));
                uploadFormData.append("user_metadata", JSON.stringify({}));

                response = await fetch("/api/v1/presentations/upload", {
                    method: "POST",
                    body: uploadFormData,
                });
            } else {
                // URL mode
                const payload = {
                    audio_url: audioUrl,
                    video_url: null,
                    language: formData.language,
                    talk_type: formData.talk_type,
                    audience_type: formData.audience_type,
                    requested_metrics: [
                        "pace",
                        "pause_quality",
                        "fillers",
                        "intonation",
                        "content_structure"
                    ],
                    user_metadata: {}
                };

                response = await fetch("/api/v1/presentations", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(payload),
                });
            }

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Submission failed");
            }

            const result = await response.json();
            // navigate to processing page with job_id
            navigate(`/processing/${result.job_id}`);
        } catch (err) {
            setError(err.message);
            setUploading(false);
        }
    };

    return (
        <div className="page upload-page">
            <h1>Upload Presentation</h1>
            <p>Upload your audio file or provide a URL to get AI-powered feedback on your presentation</p>

            {/* Mode toggle */}
            <div className="upload-mode-toggle">
                <button
                    type="button"
                    className={`upload-mode-btn ${uploadMode === "file" ? "active" : ""}`}
                    onClick={() => setUploadMode("file")}
                >
                    Upload File
                </button>
                <button
                    type="button"
                    className={`upload-mode-btn ${uploadMode === "url" ? "active" : ""}`}
                    onClick={() => setUploadMode("url")}
                >
                    Enter URL
                </button>
            </div>

            <form onSubmit={handleSubmit} className="upload-form">
                {/* File dropzone or URL input based on mode */}
                {uploadMode === "file" ? (
                    <FileDropzone
                        onFileSelect={setFile}
                        accept=".wav,.mp3,.m4a,.flac,.ogg,.webm"
                    />
                ) : (
                    <div className="form-group">
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
                        <small className="form-hint">
                            Enter a direct URL to an audio file (mp3, wav, m4a, etc.)
                        </small>
                    </div>
                )}

                {/* Form fields */}
                <div className="form-group">
                    <label htmlFor="talk_type">Presentation Type *</label>
                    <select
                        id="talk_type"
                        className="form-control"
                        value={formData.talk_type}
                        onChange={(e) => setFormData({ ...formData, talk_type: e.target.value })}
                        required
                    >
                        <option value="">Select type...</option>
                        <option value="pitch">Pitch</option>
                        <option value="lecture">Lecture</option>
                        <option value="meeting">Meeting</option>
                        <option value="interview">Interview</option>
                        <option value="speech">Speech</option>
                        <option value="other">Other</option>
                    </select>
                </div>

                <div className="form-group">
                    <label htmlFor="audience_type">Audience Type *</label>
                    <select
                        id="audience_type"
                        className="form-control"
                        value={formData.audience_type}
                        onChange={(e) => setFormData({ ...formData, audience_type: e.target.value })}
                        required
                    >
                        <option value="">Select audience...</option>
                        <option value="general">General</option>
                        <option value="technical">Technical</option>
                        <option value="executive">Executive</option>
                        <option value="academic">Academic</option>
                        <option value="students">Students</option>
                    </select>
                </div>

                <div className="form-group">
                    <label htmlFor="language">Language</label>
                    <select
                        id="language"
                        className="form-control"
                        value={formData.language}
                        onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                    >
                        <option value="en">English</option>
                        <option value="es">Spanish</option>
                        <option value="fr">French</option>
                        <option value="de">German</option>
                    </select>
                </div>

                {error && (
                    <div className="error-message">{error}</div>
                )}

                <button
                    type="submit"
                    className="btn-primary"
                    disabled={uploading || (uploadMode === "file" ? !file : !audioUrl)}
                >
                    {uploading ? "Submitting..." : "Analyze Presentation"}
                </button>
            </form>
        </div>
    );
}
