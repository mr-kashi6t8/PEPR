import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Layout } from './components/layout/Layout';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { ForgotPasswordPage } from './pages/ForgotPasswordPage';
import { DashboardPage } from './pages/DashboardPage';
import { TrendsPage } from './pages/TrendsPage';
import { GapsPage } from './pages/GapsPage';
import { ProblemsPage } from './pages/ProblemsPage';
import { ProblemDetailPage } from './pages/ProblemDetailPage';
import { ResearchPage } from './pages/ResearchPage';
import { ReportsPage } from './pages/ReportsPage';
import { IndicatorsPage } from './pages/IndicatorsPage';
import { AlertsPage } from './pages/AlertsPage';
import { AdminPage } from './pages/AdminPage';
import { UserManagementPage } from './pages/UserManagementPage';
import { SettingsPage } from './pages/SettingsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 mins
      retry: 1,
    },
  },
});

const ProtectedLayout: React.FC = () => {
  const { user } = useAuth();
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return <Layout />;
};

const RootRedirect: React.FC = () => {
  const { user } = useAuth();
  return <Navigate to={user ? "/dashboard" : "/login"} replace />;
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Dedicated Full-Screen Authentication Pages */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />

            {/* Protected Main Application Shell */}
            <Route path="/" element={<ProtectedLayout />}>
              <Route index element={<RootRedirect />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="trends" element={<TrendsPage />} />
              <Route path="gaps" element={<GapsPage />} />
              <Route path="problems" element={<ProblemsPage />} />
              <Route path="problems/:id" element={<ProblemDetailPage />} />
              <Route path="research" element={<ResearchPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route path="indicators" element={<IndicatorsPage />} />
              <Route path="alerts" element={<AlertsPage />} />
              <Route path="admin" element={<AdminPage />} />
              <Route path="users" element={<UserManagementPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>

            {/* Fallback route */}
            <Route path="*" element={<RootRedirect />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
