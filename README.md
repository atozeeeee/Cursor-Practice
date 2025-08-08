## Retirement Calculator (CLI)

Deterministic retirement projection with inflation adjustment and safe withdrawal analysis.

### Install

No install required. Uses Python 3 already available.

### Usage

```
python3 retirement_calculator.py \
  --current-age 35 \
  --retirement-age 65 \
  --current-savings 100000 \
  --monthly-contribution 1500 \
  --expected-annual-return 6.5 \
  --inflation 2.5 \
  --swr 4 \
  --desired-annual-income 80000 \
  --social-security-annual 20000
```

### Options
- `--current-age`: Current age in years
- `--retirement-age`: Target retirement age in years
- `--current-savings`: Current invested savings
- `--monthly-contribution`: Monthly contribution amount
- `--expected-annual-return`: Expected long-run nominal annual return (percent)
- `--inflation`: Expected long-run inflation (percent). Default 2.5
- `--swr`: Safe withdrawal rate (percent). Default 4.0
- `--desired-annual-income`: Desired annual income in today's dollars (optional)
- `--social-security-annual`: Social Security estimate in today's dollars (optional)
- `--contribution-increase`: Annual percent increase in contributions (default matches inflation)

### Notes
- Projections are nominal with conversion to today's dollars using inflation assumption.
- Contributions are added at the start of each month; both portfolio and contributions compound monthly.
- If `--contribution-increase` is omitted, contributions grow with inflation.