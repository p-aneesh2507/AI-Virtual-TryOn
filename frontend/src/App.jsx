import { useState } from "react";
import "./App.css";

const outfits = [
  {
    id: 1,
    name: "Classic Black",
    category: "T-Shirt",
    icon: "👕",
  },
  {
    id: 2,
    name: "Urban Blue",
    category: "Casual Shirt",
    icon: "👔",
  },
  {
    id: 3,
    name: "Minimal White",
    category: "T-Shirt",
    icon: "👕",
  },
  {
    id: 4,
    name: "Street Style",
    category: "Jacket",
    icon: "🧥",
  },
];

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [selectedOutfit, setSelectedOutfit] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");

  const handleFileChange = (event) => {
    const file = event.target.files[0];

    if (!file) return;

    setSelectedFile(file);
    setPreview(URL.createObjectURL(file));
    setMessage("");
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setMessage("Please upload your photo first.");
      return;
    }

    setUploading(true);
    setMessage("");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch("http://127.0.0.1:8000/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const data = await response.json();

      setMessage(`✓ ${data.message}`);
    } catch (error) {
      console.error(error);
      setMessage("Unable to connect to the backend.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="app">
      <header className="navbar">
        <div className="logo">
          <span className="logo-mark">✦</span>
          <span>TryOn AI</span>
        </div>

        <div className="nav-status">
          <span className="status-dot"></span>
          AI Fashion Studio
        </div>
      </header>

      <main className="main-content">
        <section className="hero">
          <div className="hero-badge">AI-POWERED VIRTUAL FITTING</div>

          <h1>
            See yourself in
            <span> any outfit.</span>
          </h1>

          <p>
            Upload your photo, choose an outfit, and experience AI-powered
            virtual try-on in seconds.
          </p>
        </section>

        <section className="workspace">
          {/* Photo Upload */}
          <div className="panel">
            <div className="panel-header">
              <div>
                <span className="step-number">01</span>
                <h2>Upload your photo</h2>
              </div>
              <span className="required">Required</span>
            </div>

            <div className={`upload-area ${preview ? "has-image" : ""}`}>
              {preview ? (
                <div className="preview-container">
                  <img src={preview} alt="Your uploaded photo" />

                  <label className="change-photo">
                    Change photo
                    <input
                      type="file"
                      accept="image/png,image/jpeg,image/webp"
                      onChange={handleFileChange}
                      hidden
                    />
                  </label>
                </div>
              ) : (
                <label className="upload-content">
                  <div className="upload-icon">↑</div>

                  <h3>Drop your photo here</h3>

                  <p>or click to browse</p>

                  <span>JPG, PNG or WEBP • Max 10MB</span>

                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/webp"
                    onChange={handleFileChange}
                    hidden
                  />
                </label>
              )}
            </div>
          </div>

          {/* Outfit Selection */}
          <div className="panel">
            <div className="panel-header">
              <div>
                <span className="step-number">02</span>
                <h2>Choose an outfit</h2>
              </div>
              <span className="optional">Select one</span>
            </div>

            <div className="outfit-grid">
              {outfits.map((outfit) => (
                <button
                  key={outfit.id}
                  className={`outfit-card ${
                    selectedOutfit === outfit.id ? "selected" : ""
                  }`}
                  onClick={() => setSelectedOutfit(outfit.id)}
                >
                  <div className="outfit-image">
                    <span>{outfit.icon}</span>
                  </div>

                  <div className="outfit-info">
                    <strong>{outfit.name}</strong>
                    <small>{outfit.category}</small>
                  </div>

                  {selectedOutfit === outfit.id && (
                    <span className="selected-check">✓</span>
                  )}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Action */}
        <section className="tryon-section">
          <button
            className="tryon-button"
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
          >
            {uploading ? "Uploading..." : "✨ Try On This Outfit"}
          </button>

          {!selectedFile && (
            <p className="hint">Upload a photo to continue</p>
          )}

          {selectedFile && !selectedOutfit && (
            <p className="hint">Choose an outfit to complete your selection</p>
          )}

          {message && (
            <div className="message">
              {message}
            </div>
          )}
        </section>
      </main>

      <footer>
        <span>AI Virtual Try-On</span>
        <span>Hackathon Prototype • Powered by AI</span>
      </footer>
    </div>
  );
}

export default App;