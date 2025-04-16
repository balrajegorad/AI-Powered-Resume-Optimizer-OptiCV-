// ResumePreview.js
import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import "./ResumePreview.css";

const ResumePreview = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { rewrittenResume, jobDesc } = location.state || {};

  const goToHome = () => {
    navigate("/", {
      state: {
        jobDesc: jobDesc,
        rewrittenResume: rewrittenResume,
      },
    });
  };

  return (
    <div className="container">
      <h2>Optimized Resume Preview</h2>
      <pre>{rewrittenResume || "No resume data available."}</pre>
      <button className="home-btn" onClick={goToHome}>Go to Home</button>
    </div>
  );
};

export default ResumePreview;
