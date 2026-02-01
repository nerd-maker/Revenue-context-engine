import clsx from 'clsx'
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/solid'

export default function MetricCard({ title, value, change, icon: Icon, loading = false }) {
    const isPositive = change >= 0

    if (loading) {
        return (
            <div className="card animate-pulse">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4"></div>
                <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
            </div>
        )
    }

    return (
        <div className="card">
            <div className="flex items-center justify-between">
                <div className="flex-1">
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
                    <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">{value}</p>
                    {change !== undefined && (
                        <div className="mt-2 flex items-center">
                            {isPositive ? (
                                <ArrowUpIcon className="h-4 w-4 text-green-600" />
                            ) : (
                                <ArrowDownIcon className="h-4 w-4 text-red-600" />
                            )}
                            <span
                                className={clsx(
                                    'ml-1 text-sm font-medium',
                                    isPositive ? 'text-green-600' : 'text-red-600'
                                )}
                            >
                                {Math.abs(change)}%
                            </span>
                            <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">vs last week</span>
                        </div>
                    )}
                </div>
                {Icon && (
                    <div className="flex-shrink-0">
                        <div className="p-3 bg-primary-100 dark:bg-primary-900/20 rounded-lg">
                            <Icon className="h-6 w-6 text-primary-600 dark:text-primary-400" />
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
