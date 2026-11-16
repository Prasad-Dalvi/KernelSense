import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import Dashboard   from './pages/Dashboard';
import Assistant   from './pages/Assistant';
import SystemHealth from './pages/SystemHealth';
import Processes   from './pages/Processes';
import Storage     from './pages/Storage';
import History     from './pages/History';

export default function App() {
  return (
    <BrowserRouter>
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
