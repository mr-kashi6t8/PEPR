import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export const Layout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#F8F9FA] flex flex-col font-sans">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      
      <div className="lg:pl-64 flex-1 flex flex-col min-w-0">
        <Header onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />

        <main className="flex-1 p-4 lg:p-6 overflow-x-hidden max-w-7xl mx-auto w-full">
          <Outlet />
        </main>

        <footer className="bg-white border-t border-slate-200/90 py-3 px-6 text-center text-xs text-slate-500">
          Pakistan Institute of Development Economics (PIDE) © {new Date().getFullYear()} — Pakistan Economics Problem Radar (PEPR)
        </footer>
      </div>
    </div>
  );
};
