EMAIL_PROMPT_TEMPLATE = """
You are an expert B2B sales assistant. Write a personalized, compliant outbound email for the following account.

Account: {account_name}
Industry: {industry}
Deal Stage: {deal_stage}
Recent Signals (last 7d):
{signals}

Constraints:
- Brand voice: {brand_voice}
- Do NOT mention: {do_not_say}
- No pricing, competitor names, or buzzwords

Output JSON:
{{
  "subject": "...",
  "body": "...",
  "reasoning": "..."
}}
"""

def build_email_prompt(account_name, industry, deal_stage, signals, brand_voice, do_not_say):
    return EMAIL_PROMPT_TEMPLATE.format(
        account_name=account_name,
        industry=industry,
        deal_stage=deal_stage,
        signals=signals,
        brand_voice=brand_voice,
        do_not_say=", ".join(do_not_say)
    )
