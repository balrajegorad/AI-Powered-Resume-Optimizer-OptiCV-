import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { setToken } from "../auth";
import './SignupLoginForm.css';
import { toast } from "react-toastify";

import BASE_URL from "../config";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loggingIn, setLoggingIn] = useState(false);

  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoggingIn(true);
    try {
      const res = await axios.post(`${BASE_URL}/login`, {
        email,
        password,
      });
      setToken(res.data.token);
      toast.success("Login successful!");
      navigate("/");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Login failed");
    } finally {
      setLoggingIn(false);
    }
  };

  return (
    <div className="container">
      <h1 className="title">OptiCV</h1>
      <form className="form" onSubmit={handleLogin}>
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
          <button className="login-btn" type="submit" disabled={loggingIn}>
            {loggingIn ? "Logging in..." : "Log in"}
          </button>
        </div>

        <div className="divider">
          <hr />
          <span>Or</span>
          <hr />
        </div>

        <div className="form-actions">
          <button
            className="signup-btn"
            type="button"
            onClick={() => navigate("/signup")}
          >
            Sign Up
          </button>
        </div>
      </form>
    </div>
  );
};

export default Login;
