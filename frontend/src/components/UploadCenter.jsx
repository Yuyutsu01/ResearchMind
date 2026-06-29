import React, { useRef, useState } from 'react';

export default function UploadCenter({ onUploadSuccess, API_BASE }) {
  const fileInputRef = useRef(null);
  const [label, setLabel] = useState('No file selected');
  const [labelColor, setLabelColor] = useState('var(--text-muted)');
  const [isDragOver, setIsDragOver] = useState(false);

  const handleZoneClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const processUpload = async (file) => {
    setLabel(`Uploading: ${file.name}...`);
    setLabelColor('var(--warning)');
    
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData
      });
      const result = await res.json();
      if (result.success) {
        setLabel(`✓ Uploaded: ${file.name}`);
        setLabelColor('var(--success)');
        onUploadSuccess(result.file_path);
      } else {
        setLabel("Upload failed.");
        setLabelColor('var(--danger)');
      }
    } catch (err) {
      setLabel("Upload error.");
      setLabelColor('var(--danger)');
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      processUpload(e.target.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processUpload(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="card">
      <h3>Document Upload Center</h3>
      <div 
        id="upload-zone" 
        className="upload-zone"
        onClick={handleZoneClick}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        style={{ borderColor: isDragOver ? "#3B82F6" : "rgba(255, 255, 255, 0.08)" }}
      >
        <input 
          type="file" 
          ref={fileInputRef} 
          accept=".pdf,.txt,.md" 
          style={{ display: 'none' }} 
          onChange={handleFileChange}
        />
        <div className="upload-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
          </svg>
        </div>
        <p>Drag & drop papers or <strong>Browse files</strong></p>
        <div 
          id="selected-file-label" 
          className="selected-file-label" 
          style={{ color: labelColor }}
        >
          {label}
        </div>
      </div>
    </div>
  );
}
