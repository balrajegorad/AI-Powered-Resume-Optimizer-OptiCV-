import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import "../App.css";
import { logout } from "../auth";
import { toast } from "react-toastify";
import Modal from "react-modal";

import { AiOutlineGithub, AiOutlineTwitter, AiOutlineLinkedin } from 'react-icons/ai'

import ai_img from '../Images/cartoon.png';
import logo from '../Images/logo2.png';
import BASE_URL from "../config";

Modal.setAppElement('#root');

function App() {
  const [resumeFile, setResumeFile] = useState(null);
  const [jobDesc, setJobDesc] = useState("");
  const [atsScore, setAtsScore] = useState(null);
  const [optimizedAtsScore, setOptimizedAtsScore] = useState(null); // New state
  const [rewrittenResume, setRewrittenResume] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);

  const [uploading, setUploading] = useState(false);
  const [checkingScore, setCheckingScore] = useState(false);
  const [rewriting, setRewriting] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const navigate = useNavigate();

  const handleUpload = async () => {
    if (!resumeFile || !jobDesc) return toast.error("Upload resume and enter Job Description");

    const formData = new FormData();
    formData.append("resume", resumeFile);
    formData.append("jd", jobDesc);

    setUploading(true);
    try {
      await axios.post(`${BASE_URL}/upload`, formData);
      toast.success("Resume uploaded successfully!");
    } catch (error) {
      toast.error("Error uploading resume: " + error.message);
    } finally {
      setUploading(false);
    }
  };

  const checkAtsScore = async () => {
    if (!resumeFile || !jobDesc) return toast.error("Upload resume or enter Job Description");

    const formData = new FormData();
    formData.append("jd", jobDesc);

    setCheckingScore(true);
    try {
      const res = await axios.post(`${BASE_URL}/ats-score`, formData);
      setAtsScore(res.data.ats_score);
    } catch (error) {
      toast.error("Error calculating ATS score: " + error.message);
    } finally {
      setCheckingScore(false);
    }
  };

  const rewriteResume = async () => {
    if (!resumeFile || !jobDesc) return toast.error("Upload resume or enter Job Description");

    const formData = new FormData();
    formData.append("jd", jobDesc);

    setRewriting(true);
    try {
      const res = await axios.post(`${BASE_URL}/rewrite`, formData);
      setRewrittenResume(res.data.rewritten_resume);
      setOptimizedAtsScore(res.data.ats_score); // Store the optimized ATS score
      setIsModalOpen(true);
      toast.success("Resume optimized successfully!");
    } catch (error) {
      toast.error("Error rewriting resume: " + error.message);
    } finally {
      setRewriting(false);
    }
  };

  const downloadPDF = async () => {
    if (!rewrittenResume) return toast.error("Please rewrite the resume first before downloading.");
    setDownloading(true);
    try {
      const res = await axios.get(`${BASE_URL}/generate-ats-pdf`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "ats_optimized_resume.pdf");
      document.body.appendChild(link);
      link.click();
    } catch (error) {
      toast.error("Error downloading PDF: " + error.message);
    } finally {
      setDownloading(false);
    }
  };

  const handleLogout = () => {
    toast.success("Logout Successfully!");
    logout();
    navigate("/login");
  };

  return (
    <div className="app-container">
      <header className="Header">
        <div className="Header-Sec">
          <img alt="Opticv-Logo" className="Logo" src={logo} />
          <button className="Logout-button" onClick={handleLogout}>Logout</button>
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
            <button onClick={handleUpload} disabled={uploading} className="primary-button">
              {uploading ? "Uploading..." : "Upload Resume"}
            </button>

            <div className="ats-score-sec">
              <button onClick={checkAtsScore} disabled={checkingScore} className="secondary-button ats-score-btn">
                {checkingScore ? "Calculating..." : "Check ATS Score"}
              </button>

              {(atsScore !== null || optimizedAtsScore !== null) && (
                <div className="ats-result">
                  {atsScore !== null && <p>Original ATS Score: {atsScore}%</p>}
                  {optimizedAtsScore !== null && <p>Optimized ATS Score: {optimizedAtsScore}%</p>}
                </div>
              )}
            </div>

            <div className="sub-buttons">
              <button onClick={rewriteResume} disabled={rewriting} className="secondary-button">
                {rewriting ? "Rewriting..." : "Rewrite Resume"}
              </button>
              <button onClick={downloadPDF} disabled={downloading} className="secondary-button">
                {downloading ? "Downloading..." : "Download Optimized Resume"}
              </button>
            </div>
          </div>
        </div>
      </div>

      <Modal
        isOpen={isModalOpen}
        onRequestClose={() => setIsModalOpen(false)}
        contentLabel="Resume Preview"
        className="resume-modal"
        overlayClassName="resume-modal-overlay"
      >
        <h2>Optimized Resume Preview</h2>
        <pre className="resume-preview-text">{rewrittenResume}</pre>
        <button className="modal-close-btn" onClick={() => setIsModalOpen(false)}>
          Close
        </button>
      </Modal>

      <footer className="footer">
        <p className="footer-text">
          Built with <span className="heart">❤️</span> by OptiCV
        </p>
        <div className="footer-icons">
          <a href="https://www.linkedin.com/in/balugorad/" className="social-icon">
            <AiOutlineLinkedin />
          </a>
          <a href="https://github.com/balrajegorad" className="social-icon">
            <AiOutlineGithub />
          </a>
          <a href="https://x.com/Balraje2169?t=d0862AsgNDBm1ntnVQsyLA&s=09" className="social-icon">
            <AiOutlineTwitter />
          </a>
        </div>
        <p className="footer-text footer-last-text">support@opticv.ai</p>
      </footer>
    </div>
  );
}

export default App;
