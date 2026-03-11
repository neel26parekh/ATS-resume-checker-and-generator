/**
 * App Shell — Root Component
 * ==========================
 * Sets up React Router with routes for all three pages:
 *   /           → HomePage (landing page)
 *   /checker    → CheckerPage (ATS score checker)
 *   /generator  → GeneratorPage (resume builder)
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header from './components/Header.jsx';
import HomePage from './pages/HomePage.jsx';
import CheckerPage from './pages/CheckerPage.jsx';
import GeneratorPage from './pages/GeneratorPage.jsx';

export default function App() {
    return (
        <BrowserRouter>
            <div className="app">
                <Header />
                <main>
                    <Routes>
                        <Route path="/" element={<HomePage />} />
                        <Route path="/checker" element={<CheckerPage />} />
                        <Route path="/generator" element={<GeneratorPage />} />
                    </Routes>
                </main>
            </div>
        </BrowserRouter>
    );
}
