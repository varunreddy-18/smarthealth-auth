import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginUser, registerUser } from "../api/authApi";
import { decodeToken } from "../utils/decodeToken";

function AuthPage() {
  const [mode, setMode] = useState("login");

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("patient");

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  // If a valid token already exists, open dashboard
  useEffect(() => {
    const token = localStorage.getItem("token");

    if (!token) return;

    const user = decodeToken(token);

    if (!user) {
      localStorage.removeItem("token");
      return;
    }

    const currentTime = Date.now() / 1000;

    if (user.exp && user.exp < currentTime) {
      localStorage.removeItem("token");
      return;
    }

    navigate("/dashboard");
  }, [navigate]);

  const switchMode = (newMode) => {
    setMode(newMode);
    setError("");
    setMessage("");
    setPassword("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");
    setMessage("");
    setLoading(true);

    try {
      if (mode === "register") {
        await registerUser({
          full_name: fullName,
          email: email,
          password: password,
          role: role,
        });

        setMessage("Registration successful. Please login.");
        setMode("login");
        setPassword("");
      } else {
        const data = await loginUser({
          email: email,
          password: password,
        });

        localStorage.setItem("token", data.access_token);

        navigate("/dashboard");
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    window.location.href =
      "http://127.0.0.1:8000/auth/google/login";
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl">

        <div className="mb-7 text-center">
          <h1 className="text-3xl font-bold text-slate-800">
            SmartHealth
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Secure healthcare identity platform
          </p>
        </div>

        {/* Login/Register tabs */}
        <div className="mb-6 grid grid-cols-2 rounded-lg bg-slate-100 p-1">

          <button
            type="button"
            onClick={() => switchMode("login")}
            className={`rounded-md py-2 font-medium ${
              mode === "login"
                ? "bg-white text-blue-600 shadow"
                : "text-slate-500"
            }`}
          >
            Login
          </button>

          <button
            type="button"
            onClick={() => switchMode("register")}
            className={`rounded-md py-2 font-medium ${
              mode === "register"
                ? "bg-white text-blue-600 shadow"
                : "text-slate-500"
            }`}
          >
            Register
          </button>

        </div>

        {error && (
          <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">
            {error}
          </div>
        )}

        {message && (
          <div className="mb-4 rounded-lg bg-green-50 p-3 text-sm text-green-600">
            {message}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">

          {mode === "register" && (
            <div>
              <label className="mb-1 block text-sm font-medium">
                Full Name
              </label>

              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Enter your full name"
                required
                className="w-full rounded-lg border border-slate-300 px-4 py-3"
              />
            </div>
          )}

          <div>
            <label className="mb-1 block text-sm font-medium">
              Email
            </label>

            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
              className="w-full rounded-lg border border-slate-300 px-4 py-3"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">
              Password
            </label>

            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              className="w-full rounded-lg border border-slate-300 px-4 py-3"
            />
          </div>

          {mode === "register" && (
            <div>
              <label className="mb-1 block text-sm font-medium">
                Select Role
              </label>

              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-4 py-3"
              >
                <option value="patient">Patient</option>
                <option value="doctor">Doctor</option>
                <option value="pharmacist">Pharmacist</option>
              </select>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 py-3 font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
          >
            {loading
              ? "Please wait..."
              : mode === "login"
              ? "Login"
              : "Create Account"}
          </button>

        </form>

        <div className="my-6 flex items-center gap-3">
          <div className="h-px flex-1 bg-slate-200" />

          <span className="text-xs text-slate-400">
            OR
          </span>

          <div className="h-px flex-1 bg-slate-200" />
        </div>

        <button
          type="button"
          onClick={handleGoogleLogin}
          className="w-full rounded-lg border border-slate-300 py-3 font-medium text-slate-700 hover:bg-slate-50"
        >
          Continue with Google
        </button>

      </div>
    </div>
  );
}

export default AuthPage;