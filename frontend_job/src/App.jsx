import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

import Navbar from './components/Navbar';
import AuthModal from './components/AuthModal';
import UploadPage from './pages/UploadPage';
import JobsPage from './pages/JobsPage';
import JobDetailPage from './pages/JobDetailPage';
import ApplicationsPage from './pages/ApplicationsPage';
import ProfilePage from './pages/ProfilePage'; // <-- UNCOMMENTED

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-brand-dark text-slate-200 font-sans">
        
        {/* The Navbar is now active across all pages! */}
        <Navbar />
        <AuthModal />
        
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/jobs" element={<JobsPage />} />
            <Route path="/jobs/:id" element={<JobDetailPage />} />
            <Route path="/applications" element={<ApplicationsPage />} />
            <Route path="/profile" element={<ProfilePage />} /> {/* <-- UNCOMMENTED */}
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;