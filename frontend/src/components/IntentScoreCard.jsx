import clsx from 'clsx'

export default function IntentScoreCard({ score, trend, size = 'md' }) {
    const getScoreColor = (score) => {
        if (score >= 70) return 'text-intent-high'
        if (score >= 40) return 'text-intent-medium'
        return 'text-intent-low'
    }

    const getScoreLabel = (score) => {
        if (score >= 70) return 'High Intent'
        if (score >= 40) return 'Medium Intent'
        return 'Low Intent'
    }

    const sizes = {
        sm: { container: 'w-16 h-16', text: 'text-lg', label: 'text-xs' },
        md: { container: 'w-24 h-24', text: 'text-2xl', label: 'text-sm' },
        lg: { container: 'w-32 h-32', text: 'text-3xl', label: 'text-base' },
    }

    const sizeClasses = sizes[size]
    const scoreColor = getScoreColor(score)
    const scoreLabel = getScoreLabel(score)

    // Calculate circle progress
    const circumference = 2 * Math.PI * 45
    const progress = circumference - (score / 100) * circumference

    return (
        <div className="flex flex-col items-center">
            <div className={clsx('relative', sizeClasses.container)}>
                {/* Background circle */}
                <svg className="transform -rotate-90 w-full h-full">
                    <circle
                        cx="50%"
                        cy="50%"
                        r="45%"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="none"
                        className="text-gray-200 dark:text-gray-700"
                    />
                    {/* Progress circle */}
                    <circle
                        cx="50%"
                        cy="50%"
                        r="45%"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="none"
                        strokeDasharray={circumference}
                        strokeDashoffset={progress}
                        strokeLinecap="round"
                        className={clsx(scoreColor, 'transition-all duration-500')}
                    />
                </svg>

                {/* Score text */}
                <div className="absolute inset-0 flex items-center justify-center">
                    <span className={clsx('font-bold', sizeClasses.text, scoreColor)}>
                        {Math.round(score)}
                    </span>
                </div>
            </div>

            {/* Label */}
            <div className="mt-2 text-center">
                <p className={clsx('font-medium', sizeClasses.label, 'text-gray-700 dark:text-gray-300')}>
                    {scoreLabel}
                </p>
                {trend && (
                    <p className={clsx('text-xs', trend > 0 ? 'text-green-600' : 'text-red-600')}>
                        {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}%
                    </p>
                )}
            </div>
        </div>
    )
}
