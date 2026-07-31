import { Navigate } from "react-router-dom";
import { decodeToken } from "../utils/decodeToken";

function ProtectedRoute({ children }) {
  const token = localStorage.getItem("token");

  if (!token) {
    return <Navigate to="/" replace />;
  }

  const user = decodeToken(token);

  if (!user) {
    localStorage.removeItem("token");
    return <Navigate to="/" replace />;
  }

  const currentTime = Date.now() / 1000;

  if (user.exp && user.exp < currentTime) {
    localStorage.removeItem("token");
    return <Navigate to="/" replace />;
  }

  return children;
}

export default ProtectedRoute;