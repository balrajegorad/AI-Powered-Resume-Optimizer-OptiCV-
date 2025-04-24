import React from "react";
import { BrowserRouter as Router, Route, Routes, Navigate } from "react-router-dom";
import Signup from "./pages/Signup";
import Login from "./pages/Login";
import Home from "./pages/Home";
import { isLoggedIn } from "./auth";
import ResumePreview from "./pages/ResumePreview";

import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";




const PrivateRoute = ({ children }) => {
  return isLoggedIn() ? children : <Navigate to="/login" />;
};

function App() {
  return (

    <>
      <Router>
        <Routes>
          <Route path="/" element={<PrivateRoute><Home /></PrivateRoute>} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/login" element={<Login />} />
          <Route path="/resume-preview" element={<ResumePreview />} />
          <Route path="*" element={<Login />} />
        </Routes>
      </Router>
      <ToastContainer position="top-center" autoClose={3000} />
    </>
      );
}

export default App;
