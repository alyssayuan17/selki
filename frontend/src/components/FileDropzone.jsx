import { useState } from "react";

export default function FileDropzone({ onFileSelect, accept = ".wav,.mp3,.m4a,.flac,.ogg,.webm" }) {
    const [isDragging, setIsDragging] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null);

    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    };

    const handleFileInput = (e) => {
        const files = e.target.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    };

    const handleFile = (file) => {
        // validate file type
        const allowedTypes = accept.split(',').map(ext => ext.trim());
        const fileExt = '.' + file.name.split('.').pop().toLowerCase();

        if (!allowedTypes.includes(fileExt)) {
            alert(`Invalid file type. Allowed types: ${accept}`);
            return;
        }

        setSelectedFile(file);
        onFileSelect?.(file);
    };

    return (
        <div
            className={`file-dropzone ${isDragging ? "file-dropzone--dragging" : ""} ${selectedFile ? "file-dropzone--has-file" : ""}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
        >
            <input
                type="file"
                id="file-input"
                className="file-dropzone__input"
                accept={accept}
                onChange={handleFileInput}
            />

            <label htmlFor="file-input" className="file-dropzone__label">
                {selectedFile ? (
                    <>
                        <div className="file-dropzone__icon">✓</div>
                        <div className="file-dropzone__text">
                            <strong>{selectedFile.name}</strong>
                            <span>{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</span>
                        </div>
                        <button
                            type="button"
                            className="file-dropzone__remove"
                            onClick={(e) => {
                                e.preventDefault();
                                setSelectedFile(null);
                                onFileSelect?.(null);
                            }}
                        >
                            Remove
                        </button>
                    </>
                ) : (
                    <>
                        <div className="file-dropzone__icon">📁</div>
                        <div className="file-dropzone__text">
                            <strong>Drop your audio file here</strong>
                            <span>or click to browse</span>
                        </div>
                        <div className="file-dropzone__formats">
                            Supported: {accept}
                        </div>
                    </>
                )}
            </label>
        </div>
    );
}
