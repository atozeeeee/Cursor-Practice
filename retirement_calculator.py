#!/usr/bin/env python3

import argparse
from dataclasses import dataclass
from typing import Optional


@dataclass
class RetirementInputs:
    current_age_years: int
    retirement_age_years: int
    current_savings: float
    monthly_contribution: float
    expected_annual_return_pct: float
    inflation_annual_pct: float = 2.5
    safe_withdrawal_rate_pct: float = 4.0
    desired_annual_income_today: Optional[float] = None
    social_security_annual_today: float = 0.0
    contribution_increase_annual_pct: Optional[float] = None


@dataclass
class RetirementResults:
    years_until_retirement: float
    months_until_retirement: int
    nominal_balance_at_retirement: float
    real_balance_at_retirement_today_dollars: float
    nominal_sustainable_withdrawal_annual: float
    real_sustainable_withdrawal_annual_today_dollars: float
    desired_income_today: Optional[float]
    desired_income_after_ss_today: Optional[float]
    income_gap_today: Optional[float]


def calculate_monthly_rate(annual_rate_pct: float) -> float:
    annual_rate = annual_rate_pct / 100.0
    return (1.0 + annual_rate) ** (1.0 / 12.0) - 1.0


def project_balance(
    current_savings: float,
    monthly_contribution: float,
    months: int,
    monthly_return_rate: float,
    monthly_contribution_growth_rate: float,
) -> float:
    """Project account balance with monthly compounding and growing contributions.

    Uses an iterative month-by-month projection to support independent growth
    rates for returns and contributions. For typical horizons (< 70 years), this
    approach is performant and easy to reason about.
    """
    balance = current_savings
    contribution = monthly_contribution

    for _ in range(months):
        # Add contribution at the beginning of the month
        balance += contribution
        # Apply growth for the month
        balance *= (1.0 + monthly_return_rate)
        # Grow the contribution for next month
        contribution *= (1.0 + monthly_contribution_growth_rate)

    return balance


def compute_retirement(inputs: RetirementInputs) -> RetirementResults:
    if inputs.retirement_age_years <= inputs.current_age_years:
        raise ValueError("Retirement age must be greater than current age.")

    years = inputs.retirement_age_years - inputs.current_age_years
    months = years * 12

    monthly_return_rate = calculate_monthly_rate(inputs.expected_annual_return_pct)

    # If contribution growth not specified, assume it grows with inflation
    contribution_growth_annual_pct = (
        inputs.inflation_annual_pct
        if inputs.contribution_increase_annual_pct is None
        else inputs.contribution_increase_annual_pct
    )
    monthly_contrib_growth_rate = calculate_monthly_rate(contribution_growth_annual_pct)

    nominal_balance = project_balance(
        current_savings=inputs.current_savings,
        monthly_contribution=inputs.monthly_contribution,
        months=months,
        monthly_return_rate=monthly_return_rate,
        monthly_contribution_growth_rate=monthly_contrib_growth_rate,
    )

    # Convert nominal future value to today's dollars via inflation
    real_discount_factor = (1.0 + inputs.inflation_annual_pct / 100.0) ** years
    real_balance_today = nominal_balance / real_discount_factor

    swr = inputs.safe_withdrawal_rate_pct / 100.0
    nominal_sustainable_withdrawal = nominal_balance * swr
    real_sustainable_withdrawal_today = real_balance_today * swr

    desired_income_today: Optional[float] = None
    desired_income_after_ss_today: Optional[float] = None
    income_gap_today: Optional[float] = None

    if inputs.desired_annual_income_today is not None:
        desired_income_today = inputs.desired_annual_income_today
        desired_income_after_ss_today = max(
            0.0, desired_income_today - inputs.social_security_annual_today
        )
        income_gap_today = desired_income_after_ss_today - real_sustainable_withdrawal_today

    return RetirementResults(
        years_until_retirement=float(years),
        months_until_retirement=months,
        nominal_balance_at_retirement=nominal_balance,
        real_balance_at_retirement_today_dollars=real_balance_today,
        nominal_sustainable_withdrawal_annual=nominal_sustainable_withdrawal,
        real_sustainable_withdrawal_annual_today_dollars=real_sustainable_withdrawal_today,
        desired_income_today=desired_income_today,
        desired_income_after_ss_today=desired_income_after_ss_today,
        income_gap_today=income_gap_today,
    )


def format_currency(amount: float) -> str:
    return f"${amount:,.0f}"


def print_results(results: RetirementResults) -> None:
    print("Retirement Projection")
    print("-" * 80)
    print(f"Time until retirement: {results.years_until_retirement:.1f} years ({results.months_until_retirement} months)")
    print()
    print("Balances at retirement:")
    print(f"  Nominal: {format_currency(results.nominal_balance_at_retirement)}")
    print(
        f"  In today's dollars: {format_currency(results.real_balance_at_retirement_today_dollars)}"
    )
    print()
    print("Sustainable annual withdrawal (" "SWR" "):")
    print(f"  Nominal: {format_currency(results.nominal_sustainable_withdrawal_annual)}")
    print(
        f"  In today's dollars: {format_currency(results.real_sustainable_withdrawal_annual_today_dollars)}"
    )

    if results.desired_income_today is not None:
        print()
        print("Retirement income goal (today's dollars):")
        print(f"  Desired annual income: {format_currency(results.desired_income_today)}")
        print(
            f"  Less Social Security: {format_currency(results.desired_income_after_ss_today or 0.0)}"
        )
        gap = results.income_gap_today or 0.0
        status = "shortfall" if gap > 0 else "surplus"
        print(
            f"  Gap vs SWR from portfolio: {format_currency(abs(gap))} ({status})"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Deterministic retirement calculator with inflation adjustment and "
            "safe withdrawal analysis."
        )
    )

    parser.add_argument("--current-age", type=int, required=True, help="Current age in years")
    parser.add_argument("--retirement-age", type=int, required=True, help="Retirement age in years")
    parser.add_argument("--current-savings", type=float, required=True, help="Current invested retirement savings")
    parser.add_argument("--monthly-contribution", type=float, required=True, help="Monthly contribution amount")
    parser.add_argument(
        "--expected-annual-return",
        type=float,
        required=True,
        help="Expected average annual portfolio return (percent)",
    )
    parser.add_argument(
        "--inflation",
        type=float,
        default=2.5,
        help="Expected average annual inflation (percent). Default 2.5",
    )
    parser.add_argument(
        "--swr",
        type=float,
        default=4.0,
        help="Safe withdrawal rate (percent). Default 4.0",
    )
    parser.add_argument(
        "--desired-annual-income",
        type=float,
        default=None,
        help="Desired annual retirement income in today's dollars (optional)",
    )
    parser.add_argument(
        "--social-security-annual",
        type=float,
        default=0.0,
        help="Estimated annual Social Security in today's dollars (optional)",
    )
    parser.add_argument(
        "--contribution-increase",
        type=float,
        default=None,
        help=(
            "Annual percent increase in contributions. Default is to match inflation."
        ),
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    inputs = RetirementInputs(
        current_age_years=args.current_age,
        retirement_age_years=args.retirement_age,
        current_savings=args.current_savings,
        monthly_contribution=args.monthly_contribution,
        expected_annual_return_pct=args.expected_annual_return,
        inflation_annual_pct=args.inflation,
        safe_withdrawal_rate_pct=args.swr,
        desired_annual_income_today=args.desired_annual_income,
        social_security_annual_today=args.social_security_annual,
        contribution_increase_annual_pct=args.contribution_increase,
    )

    results = compute_retirement(inputs)
    print_results(results)


if __name__ == "__main__":
    main()