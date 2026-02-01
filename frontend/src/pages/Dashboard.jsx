import { useQuery } from '@tanstack/react-query'
import { accountsApi, metricsApi, signalsApi } from '../lib/api'
import MetricCard from '../components/MetricCard'
import AccountCard from '../components/AccountCard'
import SignalTimeline from '../components/SignalTimeline'
import {
    ChartBarIcon,
    CheckCircleIcon,
    BoltIcon,
    TrophyIcon,
} from '@heroicons/react/24/outline'

export default function Dashboard() {
    // Fetch high-intent accounts
    const { data: accounts, isLoading: accountsLoading } = useQuery({
        queryKey: ['accounts', 'high-intent'],
        queryFn: () => accountsApi.list({ sort: 'intent_score', order: 'desc', limit: 20 }),
    })

    // Fetch metrics summary
    const { data: metrics, isLoading: metricsLoading } = useQuery({
        queryKey: ['metrics'],
        queryFn: () => metricsApi.summary(),
    })

    // Fetch recent signals
    const { data: recentSignals, isLoading: signalsLoading } = useQuery({
        queryKey: ['signals', 'recent'],
        queryFn: () => signalsApi.recent(24),
    })

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
                <p className="mt-2 text-gray-600 dark:text-gray-400">
                    Real-time revenue intelligence and account insights
                </p>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <MetricCard
                    title="Signals Today"
                    value={metrics?.data?.signals_today || 0}
                    change={metrics?.data?.signals_change}
                    icon={BoltIcon}
                    loading={metricsLoading}
                />
                <MetricCard
                    title="Actions Approved"
                    value={metrics?.data?.actions_approved || 0}
                    change={metrics?.data?.actions_change}
                    icon={CheckCircleIcon}
                    loading={metricsLoading}
                />
                <MetricCard
                    title="Avg Intent Score"
                    value={metrics?.data?.avg_intent_score?.toFixed(1) || '0.0'}
                    change={metrics?.data?.intent_change}
                    icon={ChartBarIcon}
                    loading={metricsLoading}
                />
                <MetricCard
                    title="High-Intent Accounts"
                    value={metrics?.data?.high_intent_count || 0}
                    change={metrics?.data?.high_intent_change}
                    icon={TrophyIcon}
                    loading={metricsLoading}
                />
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* High-Intent Accounts Leaderboard */}
                <div className="lg:col-span-2">
                    <div className="card">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                                High-Intent Accounts
                            </h2>
                            <span className="text-sm text-gray-500 dark:text-gray-400">
                                Top 20 by intent score
                            </span>
                        </div>

                        {accountsLoading ? (
                            <div className="space-y-4">
                                {[...Array(5)].map((_, i) => (
                                    <div key={i} className="animate-pulse">
                                        <div className="h-24 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
                                    </div>
                                ))}
                            </div>
                        ) : accounts?.data?.length > 0 ? (
                            <div className="space-y-4 max-h-[600px] overflow-y-auto">
                                {accounts.data.map((account, index) => (
                                    <div key={account.id} className="flex items-center space-x-4">
                                        <div className="flex-shrink-0 w-8 text-center">
                                            <span className="text-lg font-bold text-gray-400 dark:text-gray-600">
                                                #{index + 1}
                                            </span>
                                        </div>
                                        <div className="flex-1">
                                            <AccountCard account={account} />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-12">
                                <p className="text-gray-500 dark:text-gray-400">
                                    No high-intent accounts yet. Start ingesting signals to see accounts here.
                                </p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Signal Activity Feed */}
                <div className="lg:col-span-1">
                    <div className="card">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                                Recent Activity
                            </h2>
                            <span className="text-sm text-gray-500 dark:text-gray-400">Last 24 hours</span>
                        </div>

                        {signalsLoading ? (
                            <div className="space-y-4">
                                {[...Array(5)].map((_, i) => (
                                    <div key={i} className="animate-pulse">
                                        <div className="h-16 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
                                    </div>
                                ))}
                            </div>
                        ) : recentSignals?.data?.length > 0 ? (
                            <div className="max-h-[600px] overflow-y-auto">
                                <SignalTimeline signals={recentSignals.data} />
                            </div>
                        ) : (
                            <div className="text-center py-12">
                                <BoltIcon className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-600" />
                                <p className="mt-4 text-gray-500 dark:text-gray-400">
                                    No recent signals. Connect your integrations to start receiving signals.
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Quick Actions */}
            <div className="card">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Quick Actions</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <a
                        href="/approvals"
                        className="p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:border-primary-500 dark:hover:border-primary-400 transition-colors group"
                    >
                        <CheckCircleIcon className="h-8 w-8 text-gray-400 group-hover:text-primary-600 dark:group-hover:text-primary-400 mb-2" />
                        <h3 className="font-semibold text-gray-900 dark:text-white">Review Approvals</h3>
                        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                            {metrics?.data?.pending_approvals || 0} actions waiting
                        </p>
                    </a>

                    <a
                        href="/admin/integrations"
                        className="p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:border-primary-500 dark:hover:border-primary-400 transition-colors group"
                    >
                        <BoltIcon className="h-8 w-8 text-gray-400 group-hover:text-primary-600 dark:group-hover:text-primary-400 mb-2" />
                        <h3 className="font-semibold text-gray-900 dark:text-white">Connect Integrations</h3>
                        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                            Set up Salesforce, Outreach, and more
                        </p>
                    </a>

                    <a
                        href="/analytics"
                        className="p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:border-primary-500 dark:hover:border-primary-400 transition-colors group"
                    >
                        <ChartBarIcon className="h-8 w-8 text-gray-400 group-hover:text-primary-600 dark:group-hover:text-primary-400 mb-2" />
                        <h3 className="font-semibold text-gray-900 dark:text-white">View Analytics</h3>
                        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                            Deep dive into signal and action metrics
                        </p>
                    </a>
                </div>
            </div>
        </div>
    )
}
