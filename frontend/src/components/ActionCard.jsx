import { useState } from 'react'
import { format } from 'date-fns'
import clsx from 'clsx'
import {
    CheckCircleIcon,
    XCircleIcon,
    PencilIcon,
    ChevronDownIcon,
    ChevronUpIcon,
} from '@heroicons/react/24/outline'

export default function ActionCard({ action, onApprove, onReject, onUpdate }) {
    const [isExpanded, setIsExpanded] = useState(false)
    const [isEditing, setIsEditing] = useState(false)
    const [editedContent, setEditedContent] = useState(action.content)

    const getRiskColor = (risk) => {
        switch (risk) {
            case 'high':
                return 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-300'
            case 'medium':
                return 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-300'
            case 'low':
                return 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-300'
            default:
                return 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300'
        }
    }

    const handleSaveEdit = () => {
        onUpdate(action.id, { content: editedContent })
        setIsEditing(false)
    }

    return (
        <div className="card hover:shadow-md transition-shadow">
            {/* Header */}
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <div className="flex items-center space-x-2">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                            {action.type === 'email' ? 'Email' : 'Task'}: {action.subject || action.title}
                        </h3>
                        <span
                            className={clsx(
                                'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                                getRiskColor(action.risk_level)
                            )}
                        >
                            {action.risk_level} risk
                        </span>
                    </div>
                    <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                        For: {action.account_name} • {format(new Date(action.created_at), 'MMM d, h:mm a')}
                    </p>
                </div>

                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                    {isExpanded ? (
                        <ChevronUpIcon className="h-5 w-5 text-gray-500" />
                    ) : (
                        <ChevronDownIcon className="h-5 w-5 text-gray-500" />
                    )}
                </button>
            </div>

            {/* Preview */}
            {!isExpanded && (
                <p className="mt-3 text-sm text-gray-600 dark:text-gray-300 line-clamp-2">
                    {action.content}
                </p>
            )}

            {/* Expanded content */}
            {isExpanded && (
                <div className="mt-4 space-y-4">
                    {/* Content */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Content
                        </label>
                        {isEditing ? (
                            <textarea
                                value={editedContent}
                                onChange={(e) => setEditedContent(e.target.value)}
                                rows={6}
                                className="input"
                            />
                        ) : (
                            <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                                {action.content}
                            </div>
                        )}
                    </div>

                    {/* Agent reasoning */}
                    {action.reasoning && (
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Agent Reasoning
                            </label>
                            <div className="p-3 bg-blue-50 dark:bg-blue-900/10 rounded-lg text-sm text-gray-700 dark:text-gray-300">
                                {action.reasoning}
                            </div>
                        </div>
                    )}

                    {/* Account context */}
                    {action.account_context && (
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Account Context
                            </label>
                            <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg text-sm">
                                <p className="text-gray-700 dark:text-gray-300">
                                    Intent Score: <span className="font-semibold">{action.account_context.intent_score}</span>
                                </p>
                                <p className="text-gray-700 dark:text-gray-300 mt-1">
                                    Recent Signals: {action.account_context.recent_signals?.join(', ')}
                                </p>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Actions */}
            <div className="mt-4 flex items-center justify-between">
                <div className="flex space-x-2">
                    {isEditing ? (
                        <>
                            <button onClick={handleSaveEdit} className="btn-primary text-sm">
                                Save Changes
                            </button>
                            <button
                                onClick={() => {
                                    setIsEditing(false)
                                    setEditedContent(action.content)
                                }}
                                className="btn-secondary text-sm"
                            >
                                Cancel
                            </button>
                        </>
                    ) : (
                        <>
                            <button
                                onClick={() => onApprove(action.id)}
                                className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
                            >
                                <CheckCircleIcon className="h-4 w-4 mr-1" />
                                Approve
                            </button>
                            <button
                                onClick={() => onReject(action.id)}
                                className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
                            >
                                <XCircleIcon className="h-4 w-4 mr-1" />
                                Reject
                            </button>
                            {isExpanded && (
                                <button
                                    onClick={() => setIsEditing(true)}
                                    className="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-lg text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700"
                                >
                                    <PencilIcon className="h-4 w-4 mr-1" />
                                    Edit
                                </button>
                            )}
                        </>
                    )}
                </div>

                {action.confidence_score && (
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                        Confidence: {Math.round(action.confidence_score * 100)}%
                    </span>
                )}
            </div>
        </div>
    )
}
