import React, { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import SplashScreen from './components/SplashScreen';
import Dashboard   from './pages/Dashboard';
import Assistant   from './pages/Assistant';
import SystemHealth from './pages/SystemHealth';
import Processes   from './pages/Processes';
import Storage     from './pages/Storage';
import History     from './pages/History';

export default function App() {
  const [showSplash, setShowSplash] = useState(() => {
    // Only show splash screen once per session
    const seen = sessionStorage.getItem('ks_splash_seen');
    return !seen;
  });

  const handleSplashDone = () => {
    sessionStorage.setItem('ks_splash_seen', 'true');
    setShowSplash(false);
  };

  return (
    <BrowserRouter>
      {showSplash && <SplashScreen onComplete={handleSplashDone} />}
      <MainLayout>
        <Routes>
          <Route path="/"          element={<Dashboard />}   />
          <Route path="/assistant" element={<Assistant />}   />
          <Route path="/health"    element={<SystemHealth />}/>
          <Route path="/processes" element={<Processes />}   />
          <Route path="/storage"   element={<Storage />}     />
          <Route path="/history"   element={<History />}     />
        </Routes>
      </MainLayout>
    </BrowserRouter>
  );
}
