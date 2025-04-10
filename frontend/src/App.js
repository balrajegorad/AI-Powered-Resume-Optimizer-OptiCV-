// frontend/src/App.js

import React, { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [resumeFile, setResumeFile] = useState(null);
  const [jobDesc, setJobDesc] = useState("");
  const [atsScore, setAtsScore] = useState(null);
  const [rewrittenResume, setRewrittenResume] = useState("");
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!resumeFile || !jobDesc) return alert("Upload resume and enter JD");

    const formData = new FormData();
    formData.append("resume", resumeFile);
    formData.append("jd", jobDesc);

    setLoading(true);
    await axios.post("http://127.0.0.1:9999/upload", formData);
    setLoading(false);
    alert("Resume uploaded!");
  };

  const checkAtsScore = async () => {
    const formData = new FormData();
    formData.append("jd", jobDesc);

    const res = await axios.post("http://127.0.0.1:9999/ats-score", formData);
    setAtsScore(res.data.ats_score);
  };

  const rewriteResume = async () => {
    const formData = new FormData();
    formData.append("jd", jobDesc);

    const res = await axios.post("http://127.0.0.1:9999/rewrite", formData);
    setRewrittenResume(res.data.rewritten_resume);
  };

  const downloadPDF = () => {
    axios
      .get("http://127.0.0.1:9999/generate-pdf", { responseType: "blob" })
      .then((res) => {
        const url = window.URL.createObjectURL(new Blob([res.data]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", "optimized_resume.pdf");
        document.body.appendChild(link);
        link.click();
      });
  };

  return (
    <div className="container">
      <h1>OptiCV - ATS Resume Optimizer</h1>

      <div className="section">
        <label>Upload Resume (PDF)</label>
        <input type="file" accept=".pdf" onChange={(e) => setResumeFile(e.target.files[0])} />
      </div>

      <div className="section">
        <label>Job Description</label>
        <textarea value={jobDesc} onChange={(e) => setJobDesc(e.target.value)} rows="5" />
      </div>

      <div className="buttons">
        <button onClick={handleUpload} disabled={loading}>
          {loading ? "Uploading..." : "Upload"}
        </button>
        <button onClick={checkAtsScore}>Check ATS Score</button>
        <button onClick={rewriteResume}>Rewrite Resume</button>
        <button onClick={downloadPDF}>Download Optimized Resume</button>
      </div>

      {atsScore !== null && (
        <div className="result">
          <h2>ATS Score: {atsScore}%</h2>
        </div>
      )}

      {rewrittenResume && (
        <div className="result">
          <h2>Optimized Resume Preview:</h2>
          <pre>{rewrittenResume}</pre>
        </div>
      )}
    </div>
  );
}

export default App;
