import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { actionsApi } from '../lib/api'
import ActionCard from '../components/ActionCard'
import toast from 'react-hot-toast'
import { FunnelIcon } from '@heroicons/react/24/outline'

export default function ApprovalQueue() {
    const [filters, setFilters] = useState({
        risk_level: '',
        account: '',
        status: 'pending',
    })
    const [selectedActions, setSelectedActions] = useState([])
    const queryClient = useQueryClient()

    // Fetch pending actions
    const { data: actions, isLoading } = useQuery({
        queryKey: ['actions', filters],
        queryFn: () => actionsApi.list(filters),
    })

    // Approve mutation
    const approveMutation = useMutation({
        mutationFn: (id) => actionsApi.approve(id),
        onSuccess: () => {
            queryClient.invalidateQueries(['actions'])
            toast.success('Action approved successfully')
        },
        onError: () => {
            toast.error('Failed to approve action')
        },
    })

    // Reject mutation
    const rejectMutation = useMutation({
        mutationFn: ({ id, reason }) => actionsApi.reject(id, reason),
        onSuccess: () => {
            queryClient.invalidateQueries(['actions'])
            toast.success('Action rejected')
        },
        onError: () => {
            toast.error('Failed to reject action')
        },
    })

    // Update mutation
    const updateMutation = useMutation({
        mutationFn: ({ id, data }) => actionsApi.update(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries(['actions'])
            toast.success('Action updated successfully')
        },
        onError: () => {
            toast.error('Failed to update action')
        },
    })

    // Bulk approve mutation
    const bulkApproveMutation = useMutation({
        mutationFn: (ids) => actionsApi.bulkApprove(ids),
        onSuccess: () => {
            queryClient.invalidateQueries(['actions'])
            setSelectedActions([])
            toast.success('Actions approved successfully')
        },
        onError: () => {
            toast.error('Failed to approve actions')
        },
    })

    const handleApprove = (id) => {
        approveMutation.mutate(id)
    }

    const handleReject = (id) => {
        const reason = prompt('Reason for rejection (optional):')
        rejectMutation.mutate({ id, reason: reason || 'No reason provided' })
    }

    const handleUpdate = (id, data) => {
        updateMutation.mutate({ id, data })
    }

    const handleBulkApprove = () => {
        if (selectedActions.length === 0) {
            toast.error('No actions selected')
            return
        }
        bulkApproveMutation.mutate(selectedActions)
    }

    const toggleSelection = (id) => {
        setSelectedActions((prev) =>
            prev.includes(id) ? prev.filter((actionId) => actionId !== id) : [...prev, id]
        )
    }

    const toggleSelectAll = () => {
        if (selectedActions.length === actions?.data?.length) {
            setSelectedActions([])
        } else {
            setSelectedActions(actions?.data?.map((a) => a.id) || [])
        }
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Approval Queue</h1>
                    <p className="mt-2 text-gray-600 dark:text-gray-400">
                        Review and approve AI-generated actions
                    </p>
                </div>

                {selectedActions.length > 0 && (
                    <button onClick={handleBulkApprove} className="btn-primary">
                        Approve {selectedActions.length} Selected
                    </button>
                )}
            </div>

            {/* Filters */}
            <div className="card">
                <div className="flex items-center space-x-4">
                    <FunnelIcon className="h-5 w-5 text-gray-400" />
                    <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Risk Level
                            </label>
                            <select
                                value={filters.risk_level}
                                onChange={(e) => setFilters({ ...filters, risk_level: e.target.value })}
                                className="input"
                            >
                                <option value="">All Levels</option>
                                <option value="low">Low Risk</option>
                                <option value="medium">Medium Risk</option>
                                <option value="high">High Risk</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Status
                            </label>
                            <select
                                value={filters.status}
                                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                                className="input"
                            >
                                <option value="pending">Pending</option>
                                <option value="approved">Approved</option>
                                <option value="rejected">Rejected</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Account
                            </label>
                            <input
                                type="text"
                                placeholder="Search by account name..."
                                value={filters.account}
                                onChange={(e) => setFilters({ ...filters, account: e.target.value })}
                                className="input"
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* Actions List */}
            <div className="space-y-4">
                {isLoading ? (
                    <div className="space-y-4">
                        {[...Array(3)].map((_, i) => (
                            <div key={i} className="card animate-pulse">
                                <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
                            </div>
                        ))}
                    </div>
                ) : actions?.data?.length > 0 ? (
                    <>
                        {/* Select all checkbox */}
                        <div className="card">
                            <label className="flex items-center space-x-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={selectedActions.length === actions.data.length}
                                    onChange={toggleSelectAll}
                                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                                />
                                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                    Select all ({actions.data.length} actions)
                                </span>
                            </label>
                        </div>

                        {/* Action cards */}
                        {actions.data.map((action) => (
                            <div key={action.id} className="flex items-start space-x-4">
                                <div className="flex-shrink-0 pt-6">
                                    <input
                                        type="checkbox"
                                        checked={selectedActions.includes(action.id)}
                                        onChange={() => toggleSelection(action.id)}
                                        className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                                    />
                                </div>
                                <div className="flex-1">
                                    <ActionCard
                                        action={action}
                                        onApprove={handleApprove}
                                        onReject={handleReject}
                                        onUpdate={handleUpdate}
                                    />
                                </div>
                            </div>
                        ))}
                    </>
                ) : (
                    <div className="card text-center py-12">
                        <p className="text-gray-500 dark:text-gray-400">
                            {filters.status === 'pending'
                                ? 'No pending actions. All caught up!'
                                : 'No actions found with the selected filters.'}
                        </p>
                    </div>
                )}
            </div>
        </div>
    )
}
