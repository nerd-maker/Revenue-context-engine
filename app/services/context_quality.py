def compute_context_quality(context):
    has_tech_stack = bool(context.get('tech_stack'))
    has_employee_count = bool(context.get('employee_count'))
    has_recent_funding = bool(context.get('recent_funding'))
    signal_count = context.get('signal_count', 0)
    quality_score = (
        (0.3 if has_tech_stack else 0) +
        (0.2 if has_employee_count else 0) +
        (0.2 if has_recent_funding else 0) +
        (0.3 if signal_count > 5 else signal_count * 0.06)
    ) * 100
    return min(quality_score, 100.0)
