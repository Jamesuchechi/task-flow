import { Navigate, Route, Routes } from "react-router-dom";
import { GuestOnlyRoute, ProtectedRoute } from "./components/ProtectedRoute";
import { ToastContainer } from "./components/ToastContainer";
import { DashboardPage } from "./pages/DashboardPage";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";

export function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<LandingPage />} />

        <Route element={<GuestOnlyRoute />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>

        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<DashboardPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <ToastContainer />
    </>
  );
}

export default App;
