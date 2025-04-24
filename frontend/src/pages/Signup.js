import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import './SignupLoginForm.css';
import { setToken } from "../auth";
import { toast } from "react-toastify";

const Signup = () => {
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [password, setPassword] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [sendingOtp, setSendingOtp] = useState(false);
  const [signingUp, setSigningUp] = useState(false);

  const navigate = useNavigate();

  const sendOtp = async () => {
    setSendingOtp(true);
    try {
      const res = await axios.post("https://ai-powered-resume-optimizer-opticv.onrender.com/request-otp", { email });
      toast.success(res.data.message);
      setOtpSent(true);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to send OTP");
    } finally {
      setSendingOtp(false);
    }
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    setSigningUp(true);
    try {
      const res = await axios.post("https://ai-powered-resume-optimizer-opticv.onrender.com/signup", {
        email,
        password,
        otp,
      });
      setToken(res.data.token);
      toast.success("Signup successful!");
      navigate("/");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Signup failed");
    } finally {
      setSigningUp(false);
    }
  };

  return (
    <div className="container">
      <h1 className="title">OptiCV</h1>
      <form className="form" onSubmit={handleSignup}>
        <div className="form-group">
          <input
            className="input"
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        {!otpSent ? (
          <div className="form-actions">
            <button
              className="signup-btn"
              type="button"
              onClick={sendOtp}
              disabled={sendingOtp}
            >
              {sendingOtp ? "Sending..." : "Send OTP"}
            </button>
          </div>
        ) : (
          <>
            <div className="form-group">
              <input
                className="input"
                type="text"
                placeholder="OTP"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <input
                className="input"
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <div className="form-actions">
              <button
                className="signup-btn"
                type="submit"
                disabled={signingUp}
              >
                {signingUp ? "Signing up..." : "Sign Up"}
              </button>
            </div>
          </>
        )}

        <div className="divider">
          <hr />
          <span>Or</span>
          <hr />
        </div>
        <div className="form-actions">
          <button
            className="login-btn"
            type="button"
            onClick={() => navigate("/login")}
          >
            Log in
          </button>
        </div>
      </form>
    </div>
  );
};

export default Signup;
