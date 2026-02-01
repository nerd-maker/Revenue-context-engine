import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { accountsApi, signalsApi } from '../lib/api'
import { useState } from 'react'
import IntentScoreCard from '../components/IntentScoreCard'
import SignalTimeline from '../components/SignalTimeline'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { format, subDays } from 'date-fns'
import toast from 'react-hot-toast'

export default function AccountInsights() {
    const { id } = useParams()
    const [timeRange, setTimeRange] = useState('30d')
    const [showManualSignalForm, setShowManualSignalForm] = useState(false)
    const queryClient = useQueryClient()

    // Fetch account details
    const { data: account, isLoading: accountLoading } = useQuery({
        queryKey: ['account', id],
        queryFn: () => accountsApi.get(id),
    })

    // Fetch signals
    const { data: signals, isLoading: signalsLoading } = useQuery({
        queryKey: ['account-signals', id],
        queryFn: () => accountsApi.getSignals(id),
    })

    // Fetch actions
    const { data: actions, isLoading: actionsLoading } = useQuery({
        queryKey: ['account-actions', id],
        queryFn: () => accountsApi.getActions(id),
    })

    // Create manual signal mutation
    const createSignalMutation = useMutation({
        mutationFn: (data) => signalsApi.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries(['account-signals', id])
            queryClient.invalidateQueries(['account', id])
            setShowManualSignalForm(false)
            toast.success('Signal created successfully')
        },
        onError: () => {
            toast.error('Failed to create signal')
        },
    })

    const handleCreateSignal = (e) => {
        e.preventDefault()
        const formData = new FormData(e.target)
        createSignalMutation.mutate({
            account_id: id,
            type: formData.get('type'),
            source: 'manual',
            metadata: {
                description: formData.get('description'),
                created_by: 'user',
            },
            confidence_score: parseFloat(formData.get('confidence')),
        })
    }

    // Generate trend data
    const getTrendData = () => {
        const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 90
        const data = []
        for (let i = days; i >= 0; i--) {
            const date = subDays(new Date(), i)
            // Mock data - in real app, fetch from API
            data.push({
                date: format(date, 'MMM d'),
                score: Math.random() * 30 + (account?.data?.intent_score || 50),
            })
        }
        return data
    }

    if (accountLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            </div>
        )
    }

    const accountData = account?.data

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{accountData?.name}</h1>
                    <p className="mt-2 text-gray-600 dark:text-gray-400">
                        {accountData?.domain} • {accountData?.industry}
                    </p>
                </div>
                <IntentScoreCard score={accountData?.intent_score || 0} size="lg" />
            </div>

            {/* Intent Score Trend */}
            <div className="card">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white">Intent Score Trend</h2>
                    <div className="flex space-x-2">
                        {['7d', '30d', '90d'].map((range) => (
                            <button
                                key={range}
                                onClick={() => setTimeRange(range)}
                                className={`px-3 py-1 text-sm rounded-lg ${timeRange === range
                                        ? 'bg-primary-600 text-white'
                                        : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                                    }`}
                            >
                                {range}
                            </button>
                        ))}
                    </div>
                </div>

                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={getTrendData()}>
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
                        <Line
                            type="monotone"
                            dataKey="score"
                            stroke="#0ea5e9"
                            strokeWidth={2}
                            dot={{ fill: '#0ea5e9' }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            {/* Risk Flags */}
            {accountData?.risk_flags && Object.keys(accountData.risk_flags).length > 0 && (
                <div className="card bg-yellow-50 dark:bg-yellow-900/10 border-yellow-200 dark:border-yellow-800">
                    <h3 className="text-lg font-semibold text-yellow-900 dark:text-yellow-300 mb-3">
                        ⚠️ Risk Flags
                    </h3>
                    <div className="space-y-2">
                        {Object.entries(accountData.risk_flags).map(([key, value]) => (
                            <div key={key} className="flex items-center justify-between">
                                <span className="text-yellow-800 dark:text-yellow-200">{key}</span>
                                <span className="font-medium text-yellow-900 dark:text-yellow-100">{value}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Signals and Actions Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Signal Timeline */}
                <div className="card">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-xl font-bold text-gray-900 dark:text-white">Signal Timeline</h2>
                        <button
                            onClick={() => setShowManualSignalForm(!showManualSignalForm)}
                            className="btn-primary text-sm"
                        >
                            + Add Signal
                        </button>
                    </div>

                    {showManualSignalForm && (
                        <form onSubmit={handleCreateSignal} className="mb-6 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                            <div className="space-y-3">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        Signal Type
                                    </label>
                                    <select name="type" className="input" required>
                                        <option value="web_visit">Web Visit</option>
                                        <option value="email_open">Email Open</option>
                                        <option value="phone_call">Phone Call</option>
                                        <option value="job_posting">Job Posting</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        Description
                                    </label>
                                    <textarea name="description" rows={3} className="input" required />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        Confidence (0-1)
                                    </label>
                                    <input
                                        type="number"
                                        name="confidence"
                                        step="0.1"
                                        min="0"
                                        max="1"
                                        defaultValue="0.8"
                                        className="input"
                                        required
                                    />
                                </div>
                                <div className="flex space-x-2">
                                    <button type="submit" className="btn-primary text-sm">
                                        Create Signal
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setShowManualSignalForm(false)}
                                        className="btn-secondary text-sm"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        </form>
                    )}

                    {signalsLoading ? (
                        <div className="space-y-4">
                            {[...Array(3)].map((_, i) => (
                                <div key={i} className="animate-pulse h-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
                            ))}
                        </div>
                    ) : signals?.data?.length > 0 ? (
                        <div className="max-h-[600px] overflow-y-auto">
                            <SignalTimeline signals={signals.data} />
                        </div>
                    ) : (
                        <p className="text-center text-gray-500 dark:text-gray-400 py-8">
                            No signals yet. Add your first signal above.
                        </p>
                    )}
                </div>

                {/* Action History */}
                <div className="card">
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Action History</h2>

                    {actionsLoading ? (
                        <div className="space-y-4">
                            {[...Array(3)].map((_, i) => (
                                <div key={i} className="animate-pulse h-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
                            ))}
                        </div>
                    ) : actions?.data?.length > 0 ? (
                        <div className="space-y-4 max-h-[600px] overflow-y-auto">
                            {actions.data.map((action) => (
                                <div
                                    key={action.id}
                                    className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
                                >
                                    <div className="flex items-start justify-between">
                                        <div>
                                            <h4 className="font-medium text-gray-900 dark:text-white">
                                                {action.type}: {action.subject || action.title}
                                            </h4>
                                            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                                {format(new Date(action.created_at), 'MMM d, h:mm a')}
                                            </p>
                                        </div>
                                        <span
                                            className={`px-2 py-1 text-xs rounded-full ${action.status === 'approved'
                                                    ? 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-300'
                                                    : action.status === 'rejected'
                                                        ? 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-300'
                                                        : 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-300'
                                                }`}
                                        >
                                            {action.status}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-center text-gray-500 dark:text-gray-400 py-8">
                            No actions yet. Actions will appear here once the agent proposes them.
                        </p>
                    )}
                </div>
            </div>
        </div>
    )
}
