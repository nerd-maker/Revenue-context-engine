import { Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import Sidebar from './components/Sidebar'
import TopBar from './components/TopBar'

// Pages
import Dashboard from './pages/Dashboard'
import ApprovalQueue from './pages/ApprovalQueue'
import AccountInsights from './pages/AccountInsights'
import Analytics from './pages/Analytics'
import Settings from './pages/admin/Settings'
import Integrations from './pages/admin/Integrations'
import PromptManagement from './pages/admin/PromptManagement'
import TeamManagement from './pages/admin/TeamManagement'
import Onboarding from './pages/Onboarding'

function App() {
    const [darkMode, setDarkMode] = useState(() => {
        return localStorage.getItem('darkMode') === 'true'
    })
    const [sidebarOpen, setSidebarOpen] = useState(true)

    // Get tenant ID from localStorage
    const tenantId = localStorage.getItem('tenant_id')

    // Connect to WebSocket for real-time updates
    const { isConnected } = useWebSocket(tenantId)

    // Apply dark mode class to document
    useEffect(() => {
        if (darkMode) {
            document.documentElement.classList.add('dark')
        } else {
            document.documentElement.classList.remove('dark')
        }
        localStorage.setItem('darkMode', darkMode)
    }, [darkMode])

    const toggleDarkMode = () => setDarkMode(!darkMode)
    const toggleSidebar = () => setSidebarOpen(!sidebarOpen)

    return (
        <div className="min-h-screen flex">
            {/* Sidebar */}
            <Sidebar isOpen={sidebarOpen} />

            {/* Main Content */}
            <div className="flex-1 flex flex-col">
                {/* Top Bar */}
                <TopBar
                    onToggleSidebar={toggleSidebar}
                    onToggleDarkMode={toggleDarkMode}
                    darkMode={darkMode}
                    isConnected={isConnected}
                />

                {/* Page Content */}
                <main className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900 p-6">
                    <Routes>
                        <Route path="/" element={<Navigate to="/dashboard" replace />} />
                        <Route path="/dashboard" element={<Dashboard />} />
                        <Route path="/approvals" element={<ApprovalQueue />} />
                        <Route path="/accounts/:id" element={<AccountInsights />} />
                        <Route path="/analytics" element={<Analytics />} />
                        <Route path="/admin/settings" element={<Settings />} />
                        <Route path="/admin/integrations" element={<Integrations />} />
                        <Route path="/admin/prompts" element={<PromptManagement />} />
                        <Route path="/admin/team" element={<TeamManagement />} />
                        <Route path="/onboarding" element={<Onboarding />} />
                    </Routes>
                </main>
            </div>
        </div>
    )
}

export default App
