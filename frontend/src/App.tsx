import { Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import { Dashboard } from "./pages/Dashboard";
import { Students } from "./pages/Students";
import { Schedule } from "./pages/Schedule";
import { Billing } from "./pages/Billing";
import { Notifications } from "./pages/Notifications";

export default function App() {
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
