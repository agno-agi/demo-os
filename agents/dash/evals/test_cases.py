"""
Accuracy Cases
==============

Agent returns correct data and meaningful insights.
Eval type: AccuracyEval (1-10 score, pass threshold 7)
"""

CASES: list[dict] = [
    {
        "input": "What plans are available?",
        "expected_output": "Four plans: starter, professional, business, enterprise",
        "guidelines": "Response should mention all four plan tiers by name.",
    },
    {
        "input": "What's our current MRR?",
        "expected_output": "A numeric MRR value in dollars with context about what it means",
        "guidelines": "Must include a specific dollar amount. Bonus for trend context or plan breakdown.",
    },
    {
        "input": "Which acquisition source brings the most revenue?",
        "expected_output": "The source with highest total MRR from active subscriptions, with comparison to other sources",
        "guidelines": "Must name a specific source and provide revenue figures. Should compare across sources.",
    },
    {
        "input": "What's the average satisfaction score for support tickets?",
        "expected_output": "Average CSAT score between 1-5, noting that ~30% of tickets are unrated",
        "guidelines": "Must provide a numeric score. Should mention the NULL/unrated caveat.",
    },
    {
        "input": "How many customers signed up in 2024?",
        "expected_output": "A count of customers with signup_date in 2024",
        "guidelines": "Must provide a specific number. Monthly breakdown is a bonus.",
    },
    {
        "input": "What are the top reasons customers cancel?",
        "expected_output": "Ranked list of cancellation reasons with counts or MRR impact",
        "guidelines": "Must list specific reasons from the cancellation_reason column with quantitative data.",
    },
]
