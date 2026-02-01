import { Link, useLocation } from 'react-router-dom'
import {
    HomeIcon,
    ClipboardDocumentCheckIcon,
    ChartBarIcon,
    Cog6ToothIcon,
    BuildingOfficeIcon,
    UserGroupIcon,
    DocumentTextIcon,
    LinkIcon,
} from '@heroicons/react/24/outline'
import clsx from 'clsx'

const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
    { name: 'Approval Queue', href: '/approvals', icon: ClipboardDocumentCheckIcon },
    { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
]

const adminNavigation = [
    { name: 'Settings', href: '/admin/settings', icon: Cog6ToothIcon },
    { name: 'Integrations', href: '/admin/integrations', icon: LinkIcon },
    { name: 'Prompts', href: '/admin/prompts', icon: DocumentTextIcon },
    { name: 'Team', href: '/admin/team', icon: UserGroupIcon },
]

export default function Sidebar({ isOpen }) {
    const location = useLocation()

    return (
        <div
            className={clsx(
                'bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-300',
                isOpen ? 'w-64' : 'w-0 overflow-hidden'
            )}
        >
            <div className="flex flex-col h-full">
                {/* Logo */}
                <div className="flex items-center h-16 px-6 border-b border-gray-200 dark:border-gray-700">
                    <BuildingOfficeIcon className="h-8 w-8 text-primary-600" />
                    <span className="ml-3 text-xl font-bold text-gray-900 dark:text-white">
                        Revenue Context
                    </span>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
                    {navigation.map((item) => {
                        const isActive = location.pathname === item.href
                        return (
                            <Link
                                key={item.name}
                                to={item.href}
                                className={clsx(
                                    'flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors',
                                    isActive
                                        ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400'
                                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                                )}
                            >
                                <item.icon className="h-5 w-5 mr-3" />
                                {item.name}
                            </Link>
                        )
                    })}

                    {/* Admin Section */}
                    <div className="pt-6">
                        <p className="px-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            Admin
                        </p>
                        <div className="mt-2 space-y-1">
                            {adminNavigation.map((item) => {
                                const isActive = location.pathname === item.href
                                return (
                                    <Link
                                        key={item.name}
                                        to={item.href}
                                        className={clsx(
                                            'flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors',
                                            isActive
                                                ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400'
                                                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                                        )}
                                    >
                                        <item.icon className="h-5 w-5 mr-3" />
                                        {item.name}
                                    </Link>
                                )
                            })}
                        </div>
                    </div>
                </nav>

                {/* Footer */}
                <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                        © 2026 Revenue Context Engine
                    </p>
                </div>
            </div>
        </div>
    )
}
