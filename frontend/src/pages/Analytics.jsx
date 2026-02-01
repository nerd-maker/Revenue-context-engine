import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../lib/api'
import {
    PieChart,
    Pie,
    Cell,
    LineChart,
    Line,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from 'recharts'
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline'

const COLORS = ['#0ea5e9', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444']

export default function Analytics() {
    const [dateRange, setDateRange] = useState('30d')

    // Fetch analytics data
    const { data: signalAnalytics, isLoading: signalsLoading } = useQuery({
        queryKey: ['analytics', 'signals', dateRange],
        queryFn: () => analyticsApi.signals({ range: dateRange }),
    })

    const { data: intentAnalytics, isLoading: intentLoading } = useQuery({
        queryKey: ['analytics', 'intent', dateRange],
        queryFn: () => analyticsApi.intentScores({ range: dateRange }),
    })

    const { data: actionAnalytics, isLoading: actionsLoading } = useQuery({
        queryKey: ['analytics', 'actions', dateRange],
        queryFn: () => analyticsApi.actions({ range: dateRange }),
    })

    const handleExportCSV = () => {
        // Mock CSV export - in real app, generate from actual data
        const csv = [
            ['Date', 'Signals', 'Actions', 'Avg Intent Score'],
            ['2026-01-01', '45', '12', '67.5'],
            ['2026-01-02', '52', '15', '69.2'],
            // ... more data
        ]
            .map((row) => row.join(','))
            .join('\n')

        const blob = new Blob([csv], { type: 'text/csv' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `analytics_${dateRange}.csv`
        a.click()
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Analytics</h1>
                    <p className="mt-2 text-gray-600 dark:text-gray-400">
                        Deep insights into signals, intent, and actions
                    </p>
                </div>

                <div className="flex items-center space-x-4">
                    {/* Date range selector */}
                    <select
                        value={dateRange}
                        onChange={(e) => setDateRange(e.target.value)}
                        className="input"
                    >
                        <option value="7d">Last 7 days</option>
                        <option value="30d">Last 30 days</option>
                        <option value="90d">Last 90 days</option>
                    </select>

                    {/* Export button */}
                    <button onClick={handleExportCSV} className="btn-primary">
                        <ArrowDownTrayIcon className="h-5 w-5 mr-2" />
                        Export CSV
                    </button>
                </div>
            </div>

            {/* Signals by Source */}
            <div className="card">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Signals by Source</h2>
                {signalsLoading ? (
                    <div className="h-80 flex items-center justify-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
                    </div>
                ) : (
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={signalAnalytics?.data?.by_source || [
                                    { name: 'Salesforce', value: 45 },
                                    { name: 'Clearbit', value: 30 },
                                    { name: 'Web Tracking', value: 15 },
                                    { name: 'Manual', value: 10 },
                                ]}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                outerRadius={100}
                                fill="#8884d8"
                                dataKey="value"
                            >
                                {(signalAnalytics?.data?.by_source || []).map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip />
                        </PieChart>
                    </ResponsiveContainer>
                )}
            </div>

            {/* Signals Over Time */}
            <div className="card">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Signals Over Time</h2>
                {signalsLoading ? (
                    <div className="h-80 flex items-center justify-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
                    </div>
                ) : (
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart
                            data={signalAnalytics?.data?.over_time || [
                                { date: 'Jan 1', count: 45 },
                                { date: 'Jan 2', count: 52 },
                                { date: 'Jan 3', count: 48 },
                                { date: 'Jan 4', count: 61 },
                                { date: 'Jan 5', count: 55 },
                            ]}
                        >
                            <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
                            <XAxis dataKey="date" className="text-gray-600 dark:text-gray-400" />
                            <YAxis className="text-gray-600 dark:text-gray-400" />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                    border: 'none',
                                    borderRadius: '8px',
                                    color: '#fff',
                                }}
                            />
                            <Legend />
                            <Line type="monotone" dataKey="count" stroke="#0ea5e9" strokeWidth={2} name="Signals" />
                        </LineChart>
                    </ResponsiveContainer>
                )}
            </div>

            {/* Intent Score Distribution */}
            <div className="card">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
                    Intent Score Distribution
                </h2>
                {intentLoading ? (
                    <div className="h-80 flex items-center justify-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
                    </div>
                ) : (
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart
                            data={intentAnalytics?.data?.distribution || [
                                { range: '0-20', count: 5 },
                                { range: '21-40', count: 12 },
                                { range: '41-60', count: 25 },
                                { range: '61-80', count: 18 },
                                { range: '81-100', count: 8 },
                            ]}
                        >
                            <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
                            <XAxis dataKey="range" className="text-gray-600 dark:text-gray-400" />
                            <YAxis className="text-gray-600 dark:text-gray-400" />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                    border: 'none',
                                    borderRadius: '8px',
                                    color: '#fff',
                                }}
                            />
                            <Bar dataKey="count" fill="#0ea5e9" name="Accounts" />
                        </BarChart>
                    </ResponsiveContainer>
                )}
            </div>

            {/* Action Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="card">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        Approval Rate
                    </h3>
                    <p className="text-4xl font-bold text-green-600 dark:text-green-400">
                        {actionAnalytics?.data?.approval_rate || '85'}%
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                        {actionAnalytics?.data?.total_actions || 127} total actions
                    </p>
                </div>

                <div className="card">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        Avg Response Time
                    </h3>
                    <p className="text-4xl font-bold text-blue-600 dark:text-blue-400">
                        {actionAnalytics?.data?.avg_response_time || '2.3'}h
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                        Time to approve/reject
                    </p>
                </div>

                <div className="card">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        High-Risk Actions
                    </h3>
                    <p className="text-4xl font-bold text-red-600 dark:text-red-400">
                        {actionAnalytics?.data?.high_risk_count || 12}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                        Requiring manual review
                    </p>
                </div>
            </div>

            {/* Approval Rate by Risk Level */}
            <div className="card">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
                    Approval Rate by Risk Level
                </h2>
                {actionsLoading ? (
                    <div className="h-80 flex items-center justify-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
                    </div>
                ) : (
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart
                            data={actionAnalytics?.data?.by_risk_level || [
                                { risk: 'Low', approved: 95, rejected: 5 },
                                { risk: 'Medium', approved: 82, rejected: 18 },
                                { risk: 'High', approved: 65, rejected: 35 },
                            ]}
                        >
                            <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
                            <XAxis dataKey="risk" className="text-gray-600 dark:text-gray-400" />
                            <YAxis className="text-gray-600 dark:text-gray-400" />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                    border: 'none',
                                    borderRadius: '8px',
                                    color: '#fff',
                                }}
                            />
                            <Legend />
                            <Bar dataKey="approved" stackId="a" fill="#10b981" name="Approved" />
                            <Bar dataKey="rejected" stackId="a" fill="#ef4444" name="Rejected" />
                        </BarChart>
                    </ResponsiveContainer>
                )}
            </div>
        </div>
    )
}
