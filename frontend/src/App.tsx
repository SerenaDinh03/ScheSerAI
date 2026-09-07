import { Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import { Dashboard } from "./pages/Dashboard";
import { Students } from "./pages/Students";
import { Schedule } from "./pages/Schedule";
import { Billing } from "./pages/Billing";
import { Notifications } from "./pages/Notifications";
import { Login } from "./pages/Login";
import { useAuth } from "./context/AuthContext";

export default function App() {
  const { status } = useAuth();

  if (status === "loading") {
    return null;
  }

  if (status === "anonymous") {
    return <Login />;
  }

  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="students" element={<Students />} />
        <Route path="schedule" element={<Schedule />} />
        <Route path="billing" element={<Billing />} />
        <Route path="notifications" element={<Notifications />} />
      </Route>
    </Routes>
  );
}
