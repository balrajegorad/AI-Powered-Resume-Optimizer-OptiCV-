import React, { useState } from "react";
import axios from "axios";
import "./App.css";

import { AiOutlineGithub } from 'react-icons/ai'
import { AiOutlineTwitter } from 'react-icons/ai'
import { AiOutlineLinkedin } from 'react-icons/ai'

import ai_img from './Images/cartoon.png'; // with import
import logo from './Images/logo2.png'; 
function App() {
  const [resumeFile, setResumeFile] = useState(null);
  const [jobDesc, setJobDesc] = useState("");
  const [atsScore, setAtsScore] = useState(null);
  const [rewrittenResume, setRewrittenResume] = useState("");
  const [loading, setLoading] = useState(false);

  // Handle resume file upload
  const handleUpload = async () => {
    if (!resumeFile || !jobDesc) return alert("Upload resume and enter Job Description");

    const formData = new FormData();
    formData.append("resume", resumeFile);
    formData.append("jd", jobDesc);

    setLoading(true);
    try {
      await axios.post("http://127.0.0.1:9999/upload", formData);
      alert("Resume uploaded successfully!");
    } catch (error) {
      alert("Error uploading resume: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Check ATS score
  const checkAtsScore = async () => {
    if (!jobDesc) return alert("Enter Job Description");

    const formData = new FormData();
    formData.append("jd", jobDesc);

    setLoading(true);
    try {
      const res = await axios.post("http://127.0.0.1:9999/ats-score", formData);
      setAtsScore(res.data.ats_score);
    } catch (error) {
      alert("Error calculating ATS score: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Rewrite resume based on job description
  const rewriteResume = async () => {
    if (!jobDesc) return alert("Enter Job Description");

    const formData = new FormData();
    formData.append("jd", jobDesc);

    setLoading(true);
    try {
      const res = await axios.post("http://127.0.0.1:9999/rewrite", formData);
      setRewrittenResume(res.data.rewritten_resume);
    } catch (error) {
      alert("Error rewriting resume: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Download the optimized resume as PDF
  const downloadPDF = async () => {
    setLoading(true);
    try {
      const res = await axios.get("http://127.0.0.1:9999/generate-ats-pdf", { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "ats_optimized_resume.pdf");
      document.body.appendChild(link);
      link.click();
    } catch (error) {
      alert("Error downloading PDF: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="Header">
        <div className="Header-Sec">
          <img alt="Opticv-Logo" className="Logo" src={logo} />
          <button className="Logout-button">Logout</button>
        </div>
      </header>



      <div className="main-container">
        <div className="left-side">
          <h1 className="title">OptiCV – AI Resume Optimizer</h1>
          <p className="description">
            Revamp your resume to pass ATS checks. Upload your resume and job description, and let our AI optimize it for you!
          </p>
          <img alt="Cartoon robot giving a thumbs up" className="robot-img" src={ai_img} />
        </div>

        <div className="right-side">
          <div className="input-group">
            <label className="input-label">Upload Resume (PDF)</label>
            <input
              className="file-input"
              type="file"
              accept=".pdf"
              onChange={(e) => setResumeFile(e.target.files[0])}
            />
          </div>
          
          <div className="input-group">
            <label className="input-label">Job Description</label>
            <textarea
              className="textarea"
              value={jobDesc}
              onChange={(e) => setJobDesc(e.target.value)}
              rows="5"
            />
          </div>

          <div className="button-group">
            <button onClick={handleUpload} disabled={loading} className="primary-button">
              {loading ? "Uploading..." : "Upload Resume"}
            </button>
            <div className="sub-buttons">
              <button onClick={checkAtsScore} disabled={loading} className="secondary-button">
                {loading ? "Calculating..." : "Check ATS Score"}
              </button>
              <button button onClick={rewriteResume} disabled={loading} className="secondary-button">
                {loading ? "Rewriting..." : "Rewrite Resume"}
              </button>
            </div>
            <button onClick={downloadPDF} disabled={loading} className="secondary-button">
              {loading ? "Downloading..." : "Download Optimized Resume (PDF)"}
            </button>
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
      </div>

      <footer className="footer">
        <p className="footer-text">
          Built with <span className="heart">❤️</span> by OptiCV
        </p>
        <div className="footer-icons">
          <a href="https://www.linkedin.com/in/balugorad/" className="social-icon">
            <i className="linkedin"><AiOutlineLinkedin /></i>
          </a>
          <a href="https://github.com/balrajegorad" className="social-icon">
            <i className="github"><AiOutlineGithub /></i>
          </a>
          <a href="https://x.com/Balraje2169?t=d0862AsgNDBm1ntnVQsyLA&s=09" className="social-icon">
            <i className="twitter"><AiOutlineTwitter /></i>
          </a>
        </div>
        <p className="footer-text footer-last-text">support@opticv.ai</p>
      </footer>
    </div>
  );
}

export default App;
