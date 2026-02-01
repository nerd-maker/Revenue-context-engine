import { format } from 'date-fns'
import {
    BriefcaseIcon,
    GlobeAltIcon,
    EnvelopeIcon,
    PhoneIcon,
    UserGroupIcon,
} from '@heroicons/react/24/outline'
import clsx from 'clsx'

const signalIcons = {
    job_posting: BriefcaseIcon,
    web_visit: GlobeAltIcon,
    email_open: EnvelopeIcon,
    crm_stage_change: UserGroupIcon,
    phone_call: PhoneIcon,
}

export default function SignalTimeline({ signals }) {
    // Group signals by date
    const groupedSignals = signals.reduce((groups, signal) => {
        const date = format(new Date(signal.timestamp), 'yyyy-MM-dd')
        if (!groups[date]) {
            groups[date] = []
        }
        groups[date].push(signal)
        return groups
    }, {})

    return (
        <div className="flow-root">
            <ul className="-mb-8">
                {Object.entries(groupedSignals).map(([date, dateSignals], dateIdx) => (
                    <li key={date}>
                        {/* Date header */}
                        <div className="relative pb-8">
                            <div className="relative flex items-center space-x-3">
                                <div className="flex-shrink-0">
                                    <div className="h-8 w-8 rounded-full bg-primary-100 dark:bg-primary-900/20 flex items-center justify-center">
                                        <span className="text-xs font-medium text-primary-600 dark:text-primary-400">
                                            {format(new Date(date), 'dd')}
                                        </span>
                                    </div>
                                </div>
                                <div className="min-w-0 flex-1">
                                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                                        {format(new Date(date), 'MMMM d, yyyy')}
                                    </p>
                                </div>
                            </div>

                            {/* Signals for this date */}
                            <div className="ml-11 mt-2 space-y-2">
                                {dateSignals.map((signal, signalIdx) => {
                                    const Icon = signalIcons[signal.type] || GlobeAltIcon
                                    const isLast = dateIdx === Object.keys(groupedSignals).length - 1 &&
                                        signalIdx === dateSignals.length - 1

                                    return (
                                        <div key={signal.id} className="relative">
                                            {!isLast && (
                                                <span
                                                    className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200 dark:bg-gray-700"
                                                    aria-hidden="true"
                                                />
                                            )}
                                            <div className="relative flex items-start space-x-3">
                                                <div className="relative">
                                                    <div className={clsx(
                                                        'h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white dark:ring-gray-900',
                                                        signal.confidence_score >= 0.7
                                                            ? 'bg-green-100 dark:bg-green-900/20'
                                                            : 'bg-gray-100 dark:bg-gray-800'
                                                    )}>
                                                        <Icon className={clsx(
                                                            'h-4 w-4',
                                                            signal.confidence_score >= 0.7
                                                                ? 'text-green-600 dark:text-green-400'
                                                                : 'text-gray-600 dark:text-gray-400'
                                                        )} />
                                                    </div>
                                                </div>
                                                <div className="min-w-0 flex-1">
                                                    <div>
                                                        <div className="text-sm">
                                                            <span className="font-medium text-gray-900 dark:text-white">
                                                                {signal.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                                            </span>
                                                        </div>
                                                        <p className="mt-0.5 text-sm text-gray-500 dark:text-gray-400">
                                                            {format(new Date(signal.timestamp), 'h:mm a')} • {signal.source}
                                                        </p>
                                                        {signal.metadata && (
                                                            <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
                                                                {signal.metadata.description || JSON.stringify(signal.metadata)}
                                                            </p>
                                                        )}
                                                    </div>
                                                    <div className="mt-1">
                                                        <span className={clsx(
                                                            'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                                                            signal.confidence_score >= 0.7
                                                                ? 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-300'
                                                                : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300'
                                                        )}>
                                                            {Math.round(signal.confidence_score * 100)}% confidence
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>
                    </li>
                ))}
            </ul>
        </div>
    )
}
