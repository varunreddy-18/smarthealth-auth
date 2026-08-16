import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { decodeToken } from "../utils/decodeToken";

function Dashboard() {
  const navigate = useNavigate();

  const [user, setUser] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("token");

    // No token → go back to login
    if (!token) {
      navigate("/");
      return;
    }

    try {
      const decodedUser = decodeToken(token);

        if (!decodedUser) {
        localStorage.removeItem("token");
        navigate("/");
        return;
        }

      // Check whether JWT is expired
      const currentTime = Date.now() / 1000;

      if (decodedUser.exp < currentTime) {
        localStorage.removeItem("token");
        navigate("/");
        return;
      }

      setUser(decodedUser);
    } catch (error) {
      // Invalid token
      localStorage.removeItem("token");
      navigate("/");
    }
  }, [navigate]);

  const logout = async () => {
    try {
      // attempt to notify backend so refresh token/session are revoked
      await fetch(`${import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'}/auth/logout`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
    } catch (err) {
      // ignore network errors
    }

    localStorage.removeItem("token");
    localStorage.removeItem("refresh_token");
    navigate("/");
  };

  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100">
        <p className="text-lg text-slate-600">
          Loading dashboard...
        </p>
      </div>
    );
  }

  const roleTitle =
    user.role.charAt(0).toUpperCase() + user.role.slice(1);

  return (
    <div className="min-h-screen bg-slate-100">

      {/* Navbar */}
      <nav className="bg-blue-700 px-6 py-4 text-white shadow">

        <div className="mx-auto flex max-w-6xl items-center justify-between">

          <h1 className="text-xl font-bold">
            SmartHealth
          </h1>

          <button
            onClick={logout}
            className="rounded-lg bg-white px-4 py-2 text-sm font-semibold text-blue-700 hover:bg-slate-100"
          >
            Logout
          </button>

        </div>

      </nav>

      {/* Main Content */}
      <main className="mx-auto max-w-6xl p-6">

        <div className="rounded-2xl bg-white p-8 shadow">

          <h2 className="text-3xl font-bold text-slate-800">
            Welcome to SmartHealth
          </h2>

          <p className="mt-2 text-slate-500">
            You are successfully authenticated.
          </p>

          {/* User information */}
          <div className="mt-8 grid gap-4 md:grid-cols-3">

            <div className="rounded-xl bg-blue-50 p-5">

              <p className="text-sm text-slate-500">
                Email
              </p>

              <p className="mt-2 break-all font-semibold text-slate-800">
                {user.email}
              </p>

            </div>

            <div className="rounded-xl bg-green-50 p-5">

              <p className="text-sm text-slate-500">
                Role
              </p>

              <p className="mt-2 text-lg font-semibold text-green-700">
                {roleTitle}
              </p>

            </div>

            <div className="rounded-xl bg-purple-50 p-5">

              <p className="text-sm text-slate-500">
                User ID
              </p>

              <p className="mt-2 text-lg font-semibold text-purple-700">
                {user.sub}
              </p>

            </div>

          </div>

          {/* Role-specific content */}
          <div className="mt-8 rounded-xl border border-slate-200 p-6">

            {user.role === "patient" && (
              <>
                <h3 className="text-xl font-bold text-slate-800">
                  Patient Dashboard
                </h3>

                <p className="mt-2 text-slate-600">
                  View appointments, prescriptions, and health records.
                </p>
              </>
            )}

            {user.role === "doctor" && (
              <>
                <h3 className="text-xl font-bold text-slate-800">
                  Doctor Dashboard
                </h3>

                <p className="mt-2 text-slate-600">
                  View assigned patients and manage prescriptions.
                </p>
              </>
            )}

            {user.role === "pharmacist" && (
              <>
                <h3 className="text-xl font-bold text-slate-800">
                  Pharmacist Dashboard
                </h3>

                <p className="mt-2 text-slate-600">
                  Manage medicine orders and pharmacy operations.
                </p>
              </>
            )}

            {user.role === "admin" && (
              <>
                <h3 className="text-xl font-bold text-slate-800">
                  Admin Dashboard
                </h3>

                <p className="mt-2 text-slate-600">
                  Manage users, roles, permissions, and system activity.
                </p>
              </>
            )}

          </div>

        </div>

      </main>

    </div>
  );
}

export default Dashboard;