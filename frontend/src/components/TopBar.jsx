import {
    Bars3Icon,
    MoonIcon,
    SunIcon,
    BellIcon,
    UserCircleIcon,
} from '@heroicons/react/24/outline'
import { Menu } from '@headlessui/react'
import clsx from 'clsx'

export default function TopBar({ onToggleSidebar, onToggleDarkMode, darkMode, isConnected }) {
    return (
        <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-6">
            {/* Left side */}
            <div className="flex items-center space-x-4">
                <button
                    onClick={onToggleSidebar}
                    className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                    <Bars3Icon className="h-6 w-6 text-gray-600 dark:text-gray-300" />
                </button>

                {/* Connection status */}
                <div className="flex items-center space-x-2">
                    <div
                        className={clsx(
                            'h-2 w-2 rounded-full',
                            isConnected ? 'bg-green-500 animate-pulse-slow' : 'bg-red-500'
                        )}
                    />
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                        {isConnected ? 'Connected' : 'Disconnected'}
                    </span>
                </div>
            </div>

            {/* Right side */}
            <div className="flex items-center space-x-4">
                {/* Dark mode toggle */}
                <button
                    onClick={onToggleDarkMode}
                    className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                    {darkMode ? (
                        <SunIcon className="h-6 w-6 text-gray-600 dark:text-gray-300" />
                    ) : (
                        <MoonIcon className="h-6 w-6 text-gray-600 dark:text-gray-300" />
                    )}
                </button>

                {/* Notifications */}
                <button className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors relative">
                    <BellIcon className="h-6 w-6 text-gray-600 dark:text-gray-300" />
                    <span className="absolute top-1 right-1 h-2 w-2 bg-red-500 rounded-full" />
                </button>

                {/* User menu */}
                <Menu as="div" className="relative">
                    <Menu.Button className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                        <UserCircleIcon className="h-8 w-8 text-gray-600 dark:text-gray-300" />
                    </Menu.Button>

                    <Menu.Items className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 focus:outline-none">
                        <Menu.Item>
                            {({ active }) => (
                                <a
                                    href="#profile"
                                    className={clsx(
                                        'block px-4 py-2 text-sm',
                                        active
                                            ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                                            : 'text-gray-700 dark:text-gray-300'
                                    )}
                                >
                                    Your Profile
                                </a>
                            )}
                        </Menu.Item>
                        <Menu.Item>
                            {({ active }) => (
                                <a
                                    href="#settings"
                                    className={clsx(
                                        'block px-4 py-2 text-sm',
                                        active
                                            ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                                            : 'text-gray-700 dark:text-gray-300'
                                    )}
                                >
                                    Settings
                                </a>
                            )}
                        </Menu.Item>
                        <Menu.Item>
                            {({ active }) => (
                                <button
                                    onClick={() => {
                                        localStorage.removeItem('auth_token')
                                        localStorage.removeItem('tenant_id')
                                        window.location.href = '/login'
                                    }}
                                    className={clsx(
                                        'block w-full text-left px-4 py-2 text-sm',
                                        active
                                            ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                                            : 'text-gray-700 dark:text-gray-300'
                                    )}
                                >
                                    Sign out
                                </button>
                            )}
                        </Menu.Item>
                    </Menu.Items>
                </Menu>
            </div>
        </header>
    )
}
