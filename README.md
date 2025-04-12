# NPS vs UPS Corpus Comparison for IAS Officers

## Overview
This Python script calculates and compares the corpus of an IAS officer under the **Unfunded Pension Scheme (UPS)** and the **National Pension Scheme (NPS)**. It considers various factors such as career progression, pay commission rises, fitment factors, inflation, voluntary retirement (VRS), extraordinary leave (EOL) with no pay, **Dearness Relief (DR)**, and scenarios where the officer's **age of death occurs before retirement**.

## Pay Scales

The following table shows the pay scales used in the calculations:

| Level | Description                     | Basic Pay (₹) | Total Years |
|-------|---------------------------------|---------------|-------------|
| 10    | Junior Time Scale               | 56,100        | 4           |
| 11    | Senior Time Scale               | 67,700        | 5           |
| 12    | Junior Administrative Grade     | 78,800        | 4           |
| 13    | Selection Grade                 | 1,23,100      | 1           |
| 14    | Super Time Scale                | 1,44,200      | 4           |
| 15    | Senior Administrative Grade     | 1,82,200      | 7           |
| 16    | HAG Scale                       | 2,05,400      | 5           |
| 17    | Apex Scale                      | 2,25,000      | 6           |
| 18    | Cabinet Secretary               | 2,50,000      | 2           |

## Features
- **Salary Progression**:
  - Calculates yearly salary progression based on IAS pay scales.
  - Accounts for fitment factors, annual increment rates, and pay commission adjustments.
  - Adjusts higher pay scales using `(1.03) ** total_years` for salary progression.
  - Stops salary progression if the officer's death occurs before retirement.
- **UPS Corpus**:
  - Calculates the inflation-adjusted corpus for the Unfunded Pension Scheme.
  - Based on 50% of the last drawn annual salary.
  - Includes **Dearness Relief (DR)** added to the pension amount.
  - Accounts for proportionate payout for lesser service (full pension for 25 years of service).
  - Returns `0` if the officer's death occurs before retirement.
  - Includes spouse benefits, where the spouse receives 50% of the officer's pension for 20 years after the officer's death.
- **NPS Corpus**:
  - Calculates the corpus for the National Pension Scheme.
  - Includes contributions from both the employee (10%) and the government (12% before 2019, 14% from 2019 onward).
  - Stops contributions if the officer's death occurs before retirement or VRS.
  - Adjusts the corpus for a 50-50 split between bonds and equity.
  - Accounts for 40% of the corpus being used for pension payouts.
- **Extraordinary Leave (EOL)**:
  - Handles scenarios where the officer takes a year of leave without pay.
- **Customizable Inputs with Default Values**:
  - Allows the user to input variables such as joining age, retirement age, death age, inflation rate, market return rate, pay commission interval, and pay commission increase. Default values are used if no input is provided.

## Setup Instructions
1. **Install Python**:
   - Ensure Python 3.x is installed on your system.
   - You can download it from [python.org](https://www.python.org/).

2. **Run the Script**:
   - Open a terminal or command prompt.
   - Navigate to the directory containing the script.
   - Run the script using the command:
     ```bash
     python NPS_UPS_Comparison.py
     ```

## Usage
### Input Variables and Default Values
The script will prompt you for the following inputs. If no input is provided, the default values will be used:
1. **Joining Age**: The age at which the officer joins the service (default: 26).
2. **Retirement Age**: The age at which the officer retires (default: 60).
3. **Death Age**: The age at which the officer is expected to pass away (default: 75). If the death age is before retirement, the script adjusts calculations accordingly.
4. **Fitment Factor**: A multiplier for pay commission adjustments (default: 1.6). The new basic pay is calculated as the maximum of `(basic pay * fitment factor)` and `(current salary * 1.5)`. For higher pay scales, `(1.03) ** total_years` is also applied.
5. **Annual Increment Rate**: The yearly increment rate (default: 0.03 for 3%).
6. **Inflation Rate**: The expected inflation rate (default: 0.05 for 5%).
7. **Market Return Rate**: The expected annual return rate for NPS investments (default: 0.08 for 8%).
8. **Voluntary Retirement Age (VRS)**: The age at which the officer opts for voluntary retirement (default: retirement age).
9. **Extraordinary Leave (EOL)**: The year in which the officer takes a year of leave without pay (default: 1).
10. **Pay Commission Interval**: The interval (in years) at which pay commissions are applied (default: 10 years).
11. **Pay Commission Increase**: The percentage increase in pay due to pay commissions (default: 0.2 for 20%).
12. **Superannuation Age**: The maximum age of service (default: 60 years).

### Output
The script will calculate and display:
- **Salary Progression**: A detailed year-by-year breakdown of the officer's salary progression.
- **UPS Corpus (Inflation Adjusted)**: The total corpus under the Unfunded Pension Scheme, including Dearness Relief (DR). If the officer's death occurs before retirement, the UPS corpus will be `0`. Spouse benefits are included if applicable.
- **NPS Corpus (Including Government Contribution)**: The total corpus under the National Pension Scheme. Contributions stop if the officer's death occurs before retirement or VRS. The corpus includes adjustments for market returns and inflation.

### Example Run
```plaintext
Corpus Comparison (UPS vs NPS)
Enter birth year of the officer (default: 1996): 
Enter year of joining the service (default: 2022): 
Enter retirement age (default: 60): 
Enter death age (default: 75):
Do you want to calculate the fitment factor using Ackroyd's formula? (yes/no, default: yes):
Enter the inflation rate (default: 0.05 for 5%): 
Enter the cost of living adjustment (default: 0.2 for 20%): 
Enter inflation rate (default: 0.05 for 5%): 
Enter market return rate (default: 0.08 for 8%):
Enter pay commission interval in years (default: 10): 
Enter the number of years of Extraordinary Leave (EOL) with no pay (default: 1): 

--- Salary Progression ---
Year: 2022, Age: 26, Monthly Salary: ₹85,833.00
Year: 2023, Age: 27, Monthly Salary: ₹88,407.99
Year: 2024, Age: 28, Monthly Salary: ₹91,060.23
Year: 2025, Age: 29, Monthly Salary: ₹93,792.04
Year: 2026, Age: 30, Monthly Salary: ₹189,438.73
Year: 2027, Age: 31, Monthly Salary: ₹195,121.90
Year: 2028, Age: 32, Monthly Salary: ₹200,975.55
Year: 2029, Age: 33, Monthly Salary: ₹207,004.82
Year: 2030, Age: 34, Monthly Salary: ₹213,214.96
Year: 2031, Age: 35, Monthly Salary: ₹220,498.85
Year: 2032, Age: 36, Monthly Salary: ₹227,113.82
Year: 2033, Age: 37, Monthly Salary: ₹233,927.23
Year: 2034, Age: 38, Monthly Salary: ₹240,945.05
Year: 2035, Age: 39, Monthly Salary: ₹344,459.50
Year: 2036, Age: 40, Monthly Salary: ₹737,962.10
Year: 2037, Age: 41, Monthly Salary: ₹760,100.96
Year: 2038, Age: 42, Monthly Salary: ₹782,903.99
Year: 2039, Age: 43, Monthly Salary: ₹806,391.11
Year: 2040, Age: 44, Monthly Salary: ₹932,432.00
Year: 2041, Age: 45, Monthly Salary: ₹960,404.96
Year: 2042, Age: 46, Monthly Salary: ₹989,217.11
Year: 2043, Age: 47, Monthly Salary: ₹1,018,893.63
Year: 2044, Age: 48, Monthly Salary: ₹1,049,460.44
Year: 2045, Age: 49, Monthly Salary: ₹1,080,944.25
Year: 2046, Age: 50, Monthly Salary: ₹2,036,241.12
Year: 2047, Age: 51, Monthly Salary: ₹1,922,462.70
Year: 2048, Age: 52, Monthly Salary: ₹1,980,136.58
Year: 2049, Age: 53, Monthly Salary: ₹2,039,540.68
Year: 2050, Age: 54, Monthly Salary: ₹2,100,726.90
Year: 2051, Age: 55, Monthly Salary: ₹2,163,748.70
Year: 2052, Age: 56, Monthly Salary: ₹2,105,910.94
Year: 2053, Age: 57, Monthly Salary: ₹2,169,088.27
Year: 2054, Age: 58, Monthly Salary: ₹2,234,160.92
Year: 2055, Age: 59, Monthly Salary: ₹2,301,185.74

Final UPS Corpus (Including Dearness Relief): ₹353,325,195.97

Final NPS Corpus (Including Returns): ₹238,907,641.76
```

### Explanation of Inputs:
1. **Birth Year**: The year the officer was born (default: 1996).
2. **Year of Joining**: The year the officer joined the service (default: 2022).
3. **Retirement Age**: The age at which the officer retires (default: 60).
4. **Death Age**: The age at which the officer is expected to pass away (default: 75).
5. **Fitment Factor**: Calculated using Ackroyd's formula based on inflation and cost of living adjustment.
6. **Inflation Rate**: The expected inflation rate (default: 5% or 0.05).
7. **Market Return Rate**: The expected annual return rate for NPS investments (default: 8% or 0.08).
8. **Pay Commission Interval**: The interval (in years) at which pay commissions are applied (default: 10 years).
9. **Extraordinary Leave (EOL)**: The number of years the officer takes leave without pay (default: 1).

### Explanation of Outputs:
1. **Salary Progression**: Displays the officer's yearly salary progression, including basic pay and Dearness Allowance (DA).
2. **UPS Corpus**: The total corpus under the Unfunded Pension Scheme, adjusted for inflation and including Dearness Relief (DR).
3. **NPS Corpus**: The total corpus under the National Pension Scheme, including contributions from both the employee and the government, adjusted for market returns and inflation.

## Notes
- The script assumes the **7th Pay Commission** pay scales for IAS officers.
- The government contribution rate for NPS transitions from **12% (pre-2019)** to **14% (post-2019)**.
- The script accounts for **Extraordinary Leave (EOL)** by skipping salary progression and contributions for the specified year.
- If the officer's **death age occurs before retirement**, the script adjusts calculations for both UPS and NPS accordingly.
- **Dearness Relief (DR)** is added to the UPS pension amount to account for inflation.
- The fitment factor ensures that pay scales are updated to reflect either a fixed multiplier or a minimum increase of 50% over the current salary. For higher pay scales, `(1.03) ** total_years` is also applied.

## License
This script is provided as-is under the MIT License. Feel free to modify and use it as needed.

# Formulae Used in the Script

This section provides a detailed explanation of all the formulae used in the script for calculating salary progression, NPS corpus, UPS corpus, and related computations.

---

## 1. **Salary Progression**
### Formula:
```
basic_pay = initial_basic_pay * (1 + increment_rate) ** years_at_level
salary = basic_pay + (0.53 * basic_pay)
```
- **`initial_basic_pay`**: The starting basic pay for the pay scale level.
- **`increment_rate`**: Fixed annual increment rate (default: 3% or 0.03).
- **`years_at_level`**: Number of years the officer has spent at the current pay scale level.
- **`0.53`**: Dearness Allowance (DA) as a percentage of the basic pay.

---

## 2. **Pay Scale Update for Pay Commission**
### Formula:
```
updated_basic_pay = max(
    basic_pay * fitment_factor,
    basic_pay * (1.03 ** total_years)
)
```
- **`fitment_factor`**: A multiplier applied during pay commission updates (default: 1.6).
- **`1.03 ** total_years`**: Adjusts the salary for higher pay scales based on the total years in the pay scale.

---

## 3. **NPS Contribution**
### Formula:
```
nps_contribution = basic_pay * (employee_contribution_rate + government_contribution_rate)
```
- **`employee_contribution_rate`**: Fixed at 10% (0.1).
- **`government_contribution_rate`**:
  - 12% (0.12) before 2019.
  - 14% (0.14) from 2019 onward.

---

## 4. **NPS Corpus**
### Formula:
```
corpus = (corpus + yearly_contribution) * (1 + market_return_rate)
```
- **`yearly_contribution`**: The total NPS contribution for the year (employee + government).
- **`market_return_rate`**: Annual return rate on the NPS corpus (default: 8% or 0.08).

#### Post-Retirement Adjustments:
- **Bond and Equity Split**:
  ```
  bond_corpus = corpus * 0.5 * (1 + bond_rate)
  equity_corpus = corpus * 0.5 * (1 + equity_rate)
  total_corpus = bond_corpus + equity_corpus
  ```
  - **`bond_rate`**: Fixed at 7% (0.07).
  - **`equity_rate`**: Fixed at 12% (0.12).

- **Pension Payout**:
  ```
  pension_corpus = total_corpus * pension_payout_rate
  lump_sum_corpus = total_corpus * (1 - pension_payout_rate)
  ```
  - **`pension_payout_rate`**: Fixed at 40% (0.4).

- **Inflation-Adjusted Pension**:
  ```
  pension_payout += yearly_pension / ((1 + inflation_rate) ** years_since_retirement)
  ```
  - **`inflation_rate`**: Default 5% (0.05).

---

## 5. **UPS Corpus**
### Formula:
```
pension = last_drawn_salary * pension_percentage * proportionate_factor * (1 + dearness_relief_rate)
corpus += pension / ((1 + inflation_rate) ** years_since_retirement)
```
- **`last_drawn_salary`**: The officer's last drawn annual salary.
- **`pension_percentage`**: Fixed at 50% (0.5).
- **`proportionate_factor`**: Adjusts for years of service (full pension for 25 years of service).
- **`dearness_relief_rate`**: Default 5% (0.05).
- **`inflation_rate`**: Default 5% (0.05).

#### Spouse Benefits:
```
spouse_pension = last_drawn_salary * 0.5 * pension_percentage * proportionate_factor * (1 + dearness_relief_rate)
```
- Spouse receives 50% of the officer's pension for 20 years after the officer's death.

---

## 6. **Fitment Factor (Ackroyd's Formula)**
### Formula:
```
fitment_factor = (1 + inflation_rate) ** years_elapsed + cost_of_living_adjustment
```
- **`inflation_rate`**: Default 5% (0.05).
- **`years_elapsed`**: Fixed at 10 years.
- **`cost_of_living_adjustment`**: Default 20% (0.2).

---

## 7. **Internal Rate of Return (IRR)**
### Formula:
```
irr = npf.irr(cash_flows)
```
- **`cash_flows`**: A series of cash inflows and outflows.

---

## 8. **Net Present Value (NPV)**
### Formula:
```
npv = sum(cf / ((1 + discount_rate) ** i) for i, cf in enumerate(cash_flows))
```
- **`cf`**: Cash flow in year `i`.
- **`discount_rate`**: The rate used to discount future cash flows.

---

## 9. **Indian Currency Formatting**
### Formula:
```
formatted_amount = ₹{amount:,.2f}
```
- Formats the amount in the Indian numbering system (e.g., lakhs, crores).
