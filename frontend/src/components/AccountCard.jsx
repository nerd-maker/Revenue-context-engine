import { Link } from 'react-router-dom'
import IntentScoreCard from './IntentScoreCard'
import clsx from 'clsx'

export default function AccountCard({ account, showScore = true }) {
    return (
        <Link
            to={`/accounts/${account.id}`}
            className="card hover:shadow-lg transition-all cursor-pointer group"
        >
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                        {account.name}
                    </h3>
                    {account.domain && (
                        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{account.domain}</p>
                    )}
                    {account.industry && (
                        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{account.industry}</p>
                    )}

                    {/* Recent signals count */}
                    {account.signal_count > 0 && (
                        <div className="mt-3 flex items-center space-x-4 text-sm">
                            <span className="text-gray-600 dark:text-gray-400">
                                {account.signal_count} signals
                            </span>
                            {account.last_signal_date && (
                                <span className="text-gray-500 dark:text-gray-500">
                                    Last: {new Date(account.last_signal_date).toLocaleDateString()}
                                </span>
                            )}
                        </div>
                    )}

                    {/* Risk flags */}
                    {account.risk_flags && Object.keys(account.risk_flags).length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-2">
                            {Object.entries(account.risk_flags).map(([key, value]) => (
                                <span
                                    key={key}
                                    className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-yellow-100 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-300"
                                >
                                    {key}: {value}
                                </span>
                            ))}
                        </div>
                    )}
                </div>

                {showScore && account.intent_score !== undefined && (
                    <div className="ml-4">
                        <IntentScoreCard score={account.intent_score} size="sm" />
                    </div>
                )}
            </div>
        </Link>
    )
}
