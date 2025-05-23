# NPS vs UPS Corpus Comparison for AIS Officers

## Overview
This program compares the benefits of the National Pension System (NPS) and the Unfunded Pension Scheme (UPS) for IAS officers. It calculates monthly salary progression, NPS corpus, and UPS corpus, and provides a detailed comparison across different death ages.

---

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

---

## Default Values Used

The script uses the following default values for calculations:

| Parameter                          | Default Value       | Inputable | Hardcoded |
|------------------------------------|---------------------|-----------|-----------|
| **Joining Age**                    | 26 years           | ☑         | ☐         |
| **Retirement Age (VRS included)**                 | 60 years           | ☑         | ☐         |
| **Death Age**                      | 75 years           | ☑         | ☐         |
| **Spouse Age Difference**          | 10 years           | ☑         | ☐         |
| **Fitment Factor**                 | Calculated (1.8289 for 5% inflation and 20% COLA) | ☑ | ☐         |
| **Market Return Rate**             | 8% (0.08)          | ☑         | ☐         |
| **Inflation Rate**                 | 5% (0.05)          | ☑         | ☐         |
| **Cost of Living Adjustment (COLA)**| 20% (0.2)          | ☑         | ☐         |
| **Pay Commission Interval**        | 10 years           | ☑         | ☐         |
| **Life Cycle Fund**                | LC50 (Moderate)    | ☑         | ☐         |
| **Annuity Rate (NPS)**             | 6% (0.06)          | ☑         | ☐         |
| **Lump Sum Withdrawal Percentage** | 0%                 | ☑         | ☐         |
| **Annual Increment Rate**          | 3% (0.03)          | ☐         | ☑         |
| **Voluntary Retirement Age**       | Same as retirement | ☐         | ☑         |
| **Default Superannuation Age**             | 60 years           | ☐         | ☑         |
| **Dearness Relief (DR)**           | 2% (0.02) semi-annually | ☐     | ☑         |
| **Minimum UPS Pension**            | ₹10,000 per month  | ☐         | ☑         |
| **Employee Contribution Rate (NPS)**| 10% (0.1)         | ☐         | ☑         |
| **Government Contribution Rate (NPS)**| 12% (0.12) pre 2019, 14% (0.14) onwards | ☐ | ☑         |
| **Switch Date to UPS**             | April 2025         | ☐         | ☑         |
| **Pension Fund NAV Growth Rate**   | 8% (0.08) annually | ☐         | ☑         |

---

## Formulae Used in the Script

### 1. **Salary Progression**
#### Formula:
```
basic_pay = initial_basic_pay * (1 + increment_rate) ** years_at_level
salary = basic_pay + (0.53 * basic_pay)
```
- **`initial_basic_pay`**: The starting basic pay for the pay scale level.
- **`increment_rate`**: Fixed annual increment rate (default: 3% or 0.03).
- **`years_at_level`**: Number of years the officer has spent at the current pay scale level.
- **`0.53`**: Dearness Allowance (DA) as a percentage of the basic pay.

---

### 2. **Pay Scale Update for Pay Commission**
#### Formula:
```
updated_basic_pay = max(
    basic_pay * fitment_factor,
    previous_level_basic_pay * (1.03 ** (years_in_scale + 2))
)
```
- **`fitment_factor`**: A multiplier applied during pay commission updates (default: 1.82 based on Ackroyd's formula for 5% inflation rate and 20% cost of living adjustment).
- **`previous_level_basic_pay`**: The basic pay of the previous pay scale level.
- **`years_in_scale`**: The total number of years in the current pay scale level.
- **`1.03 ** (years_in_scale + 2)`**: Adjusts the salary for higher pay scales based on the total years in the pay scale plus an additional increments.

---

### 3. **UPS Corpus, Monthly Pension, and Lump Sum**
#### Initial UPS Pension:
```
initial_pension = (P / 2) * min(IC / BC, 1) * min(service_months / 300, 1)
```
- **`P`**: The average of the officer's last 12 months' salary before the switch.
- **`IC`**: The individual corpus, which is the NPS corpus accumulated until the switch date. After the switch, both the employee and the government contribute 10% of the monthly salary (from salary progression) to the individual corpus.
- **`BC`**: The benchmark corpus:
  - Starts from 0 and grows based on monthly contributions (`monthly_salary * 0.2`) and the Pension Fund NAV rate (default: 8% annually).
  - Before the switch: Contributions are added to the benchmark corpus, and it grows at the NAV rate.
  - After the switch: Any addition to the individual corpus is matched in the benchmark corpus.
- **`service_months`**: The total number of service months, capped at 300 months (25 years).

#### Lumpsum Withdrawal and Adjusted Pension:
```
lumpsum_withdrawal = min(BC, IC) * withdrawal_percentage
adjusted_pension = initial_pension * (1 - withdrawal_percentage)
```
- **`withdrawal_percentage`**: The percentage of the corpus withdrawn as a lump sum (capped at 60% or 0.6).
- **`BC`**: Benchmark corpus.
- **`IC`**: Individual corpus.
- **`initial_pension`**: The pension calculated before withdrawal adjustments.

#### Gratuity:
```
gratuity = (1 / 10) * avg_last_12_months_salary * (service_months / 6)
```
- **`avg_last_12_months_salary`**: The average of the officer's last 12 months' salary.
- **`service_months`**: Total service months (minimum 60 months required for gratuity).

#### UPS Lump Sum:
```
lump_sum = gratuity + excess_corpus + lumpsum_withdrawal
```
- **`excess_corpus`**: The positive difference between the individual corpus and the benchmark corpus:
  ```
  excess_corpus = max(0, IC - BC)
  ```

#### UPS Corpus:
The UPS corpus is calculated as the present value of all future pension payments, adjusted for inflation and Dearness Relief (DR).

1. **Annual Pension with DR**:
   ```
   adjusted_pension = monthly_pension * (1 + dr_rate) ** (2 * years_since_retirement)
   ```
   - **`dr_rate`**: Dearness Relief rate (default: 2% or 0.02, applied semi-annually).

2. **Present Value of Pension (Inflation-Adjusted)**:
   ```
   present_value = annual_pension / ((1 + inflation_rate) ** years_since_retirement)
   ```
   - **`annual_pension`**: The officer's annual pension.
   - **`inflation_rate`**: The expected inflation rate (default: 5% or 0.05).
   - **`years_since_retirement`**: The number of years since the officer retired.

3. **Nominal UPS Corpus**:
   ```
   nominal_corpus = sum(annual_pension for each year) + lump_sum
   ```

4. **Total UPS Corpus**:
   ```
   ups_corpus = sum(present_value for each year) + lump_sum
   ```

---

### 4. **NPS Corpus**
#### Formula:
```
corpus = (corpus + monthly_contribution) * (1 + weighted_monthly_return)
```
- **`monthly_contribution`**: The sum of employee and government contributions:
  ```
  monthly_contribution = monthly_salary * (employee_contribution_rate + government_contribution_rate)
  ```
  - **Employee Contribution Rate**: Fixed at 10% (0.1).
  - **Government Contribution Rate**:
    - 12% (0.12) before 2019.
    - 14% (0.14) from 2019 onward.

- **`weighted_monthly_return`**: Calculated based on the selected life cycle fund and asset allocation:
  ```
  weighted_monthly_return = (
      equity_allocation * (equity_return / 12) +
      corporate_bond_allocation * (corporate_bond_return / 12) +
      gsec_allocation * (gsec_return / 12)
  )
  ```

#### Life Cycle Fund Options:
The script allows the user to choose between three life cycle funds, which determine the equity allocation based on the officer's **age**:

1. **Aggressive Life Cycle Fund (LC75)**:
   - **Equity Allocation**: 75% up to age 35, reducing by 3% per year to a minimum of 15% by age 55.
   - **Formula**:
     ```
     equity_allocation = 0.75 if age <= 35 else max(0.75 - 0.03 * (age - 35), 0.15)
     ```

2. **Moderate Life Cycle Fund (LC50)** (Default):
   - **Equity Allocation**: 50% up to age 35, reducing by 2% per year to a minimum of 10% by age 55.
   - **Formula**:
     ```
     equity_allocation = 0.50 if age <= 35 else max(0.50 - 0.02 * (age - 35), 0.10)
     ```

3. **Conservative Life Cycle Fund (LC25)**:
   - **Equity Allocation**: 25% up to age 35, reducing by 1% per year to a minimum of 5% by age 55.
   - **Formula**:
     ```
     equity_allocation = 0.25 if age <= 35 else max(0.25 - 0.01 * (age - 35), 0.05)
     ```

- **Remaining Allocation**:
  ```
  corporate_bond_allocation = remaining_allocation * 0.6
  gsec_allocation = remaining_allocation * 0.4
  ```
  - **Remaining Allocation**: `1.0 - equity_allocation`.

---

### 5. **NPS Pension with Return of Purchase Price (RoP)**
#### Formulae:
1. **Annuity Corpus**:
   ```
   annuity_corpus = nps_corpus * annuity_percentage
   ```
   - **`nps_corpus`**: The total NPS corpus at retirement.
   - **`annuity_percentage`**: The percentage of the corpus used for annuity (default: 40%).

2. **Lump Sum**:
   ```
   lump_sum = nps_corpus * (1 - annuity_percentage)
   ```

3. **Annual Pension**:
   ```
   annual_pension = annuity_corpus * annuity_rate
   ```
- **`annuity_rate`**: The annual annuity rate for the Return of Purchase Price plan (default: 6%).

4. **Monthly Pension**:
   ```
   monthly_pension = annual_pension / 12
   ```

5. **Return of Purchase Price (RoP)**:
   ```
   rop_value = annuity_corpus
   ```

#### Total NPS Value:
1. **Nominal NPS Value**:
   ```
   nominal_nps_value = lump_sum + (monthly_pension * 12 * years_receiving_pension) + rop_value
   ```

2. **Inflation-Adjusted NPS Value**:
   ```
   inflation_adjusted_nps_value = lump_sum + (monthly_pension * 12 * years_receiving_pension) * ((1 + inflation_rate) * (1 - (1 / (1 + inflation_rate) ** years_receiving_pension)) / inflation_rate) + rop_value / ((1 + inflation_rate) ** years_receiving_pension)
   ```

---

## Assumptions
1. **Death Month Assumption**:
   - The month of death is assumed to be the same as the birth month:
     ```python
     death_month = birth_month
     ```

2. **Lump Sum Withdrawal Assumption**:
   - The lump sum withdrawal percentage in UPS is assumed to be the same as that in NPS.

3. **VRS Eligibility**:
   - Voluntary Retirement Scheme (VRS) can only occur if:
     - The officer has attained the age of 50, or
     - The officer has completed 30 years of qualifying service.

4. **Benchmark Corpus and Individual Corpus**:
   - The **benchmark corpus** represents the expected corpus based on contributions and growth at the Pension Fund NAV rate.
   - The **individual corpus** represents the actual NPS corpus accumulated by the officer.

5. **Dearness Relief (DR)**:
   - A 2% semi-annual Dearness Relief (DR) is applied to UPS pensions to adjust for inflation.

6. **Minimum Pension**:
   - The minimum assured payout for UPS is ₹10,000 per month for officers with at least 10 years of service.

---

## Corner Cases Handled

1. **Death Before Retirement**:
   - If the officer's death occurs before retirement, the salary progression and contributions stop, and the UPS corpus is set to `0`.
   - NPS contributions also stop, and the corpus is calculated based on the contributions made until the death year.

2. **Spouse Benefits**:
   - If the officer passes away, the spouse receives **60% of the officer's pension** until their death. The user can specify the age difference between the officer's death and the spouse's death.

3. **Pay Commission Adjustments**:
   - Pay commissions are applied at regular intervals (default: 10 years) and adjust the basic pay using the fitment factor.

---

## Handling Death Before Retirement
If the officer dies before reaching the retirement age:
- **NPS**: The entire accumulated NPS corpus is paid as a lump sum to the nominees. No monthly pension is provided since the officer did not retire.
- **UPS**: The family pension is provided to the spouse or dependents, along with a death gratuity. The family pension is calculated as a percentage of the officer's last drawn salary.

This ensures that the tool accounts for pre-retirement death scenarios and provides a fair comparison between NPS and UPS benefits.

---

## Installation Instructions

1. **Install Python**:
   - Ensure Python 3.x is installed on your system.
   - You can download it from [python.org](https://www.python.org/).

2. **Install Dependencies**:
   - Install the required Python libraries using the following command:
     ```bash
     pip install numpy numpy-financial tabulate
     ```

3. **Run the Script**:
   - Open a terminal or command prompt.
   - Navigate to the directory containing the script.
   - Run the script using the command:
     ```bash
     python NPS_UPS_Comparison.py
     ```

---

## Usage

### Input Variables and Default Values
The script will prompt you for the following inputs. If no input is provided, the default values will be used:
1. **Joining Age**: The age at which the officer joins the service (default: 26).
2. **Retirement Age**: The age at which the officer retires (default: 60).
3. **Death Age**: The age at which the officer is expected to pass away (default: 75).
4. **Spouse Age Difference**: The age difference between the officer's death and the spouse's death (default: 0). Negative values are allowed.
5. **Life Cycle Fund**: Choose between LC75, LC50 (default), and LC25 for equity allocation.
6. **Fitment Factor**: A multiplier for pay commission adjustments (default: 1.82).
7. **Inflation Rate**: The expected inflation rate (default: 5% or 0.05).
8. **Cost of Living Adjustment**: Default 20% (0.2).
9. **Market Return Rate**: The expected annual return rate for NPS investments (default: 8% or 0.08).
10. **Pay Commission Interval**: The interval (in years) at which pay commissions are applied (default: 10 years).

---

## Demo Run

### Input
```
Monthly-Based Corpus Comparison (UPS vs NPS with RoP Annuity)
-------------------------------------------------------------
Enter birth year of the officer (default: 1996): 
Enter birth month (1-12, default: 6): 
Enter year of joining the service (default: 2023): 
Enter month of joining (1-12, default: 12): 
Enter seniority year (default: 2022): 
Enter seniority month (1-12, default: 1): 
Enter normal retirement age (superannuation age) (default: 60): 
Enter actual retirement age (default: 60, less than 60 for VRS): 
Enter death age (default: 75): 
Enter fitment factor or press Enter to calculate using Ackroyd's formula (default inflation: 5%, COLA: 20%): 
Calculated Fitment Factor: 1.828894626777442
Enter annual equity return rate (default: 0.12 for 12%): 
Enter annual corporate bond return rate (default: 0.08 for 8%): 
Enter annual G-Sec return rate (default: 0.06 for 6%): 
Enter desired annuity and lumpsum withdrawal percentage (0-60%, default: 0%): 
Annuity percentage set to: 0.0%
UPS lumpsum withdrawal percentage set to: 0.0%
Enter annual annuity rate for Return of Purchase Price plan (default: 0.06 for 6%): 
Enter pay commission interval in years (default: 10): 
Choose a Life Cycle Fund for NPS:
1. Aggressive Life Cycle Fund (LC75) - 75% equity up to 35 years, reduces to 15% by 55 years.
2. Moderate Life Cycle Fund (LC50) - 50% equity up to 35 years, reduces to 10% by 55 years.
3. Conservative Life Cycle Fund (LC25) - 25% equity up to 35 years, reduces to 5% by 55 years.
Enter your choice (1/2/3, default: 2): 
Enter the age difference between spouse's death and employee's death (negative values allowed, default: 10): 
```

### Output
```
--- Salary and NPS Corpus Progression (Key Months) ---
Year | Month | Pay Level | Basic Pay | Monthly Salary | NPS Corpus
-----|-------|-----------|-----------|---------------|----------
2023 | Dec   | Level 10 | ₹ 56,100.00 | ₹ 85,833.00 | ₹ 20,764.72
2024 | Jan   | Level 10 | ₹ 56,100.00 | ₹ 85,833.00 | ₹ 41,695.56
2024 | Jul   | Level 10 | ₹ 57,783.00 | ₹ 88,407.99 | ₹ 1,71,467.16
2025 | Jan   | Level 10 | ₹ 57,783.00 | ₹ 88,407.99 | ₹ 3,10,783.99
2025 | Jul   | Level 10 | ₹ 59,516.49 | ₹ 91,060.23 | ₹ 4,57,564.83
2055 | Jul   | Level 17 | ₹ 47,06,868.19 | ₹ 72,01,508.33 | ₹ 48,62,66,831.49
2056 | Jan   | Level 17 | ₹ 47,06,868.19 | ₹ 72,01,508.33 | ₹ 52,07,43,904.36
2056 | Apr   | Level 17 | ₹ 86,08,365.94 | ₹ 1,31,70,799.89 | ₹ 54,00,54,589.25
2056 | Jun   | Level 17 | ₹ 86,08,365.94 | ₹ 1,31,70,799.89 | ₹ 55,51,28,076.23
2056 | Jul   | Level 17 | ₹ 87,80,533.26 | ₹ 1,34,07,823.54 | ₹ 57,15,00,000.00
2057 | Jan   | Level 17 | ₹ 89,56,143.92 | ₹ 1,36,46,679.07 | ₹ 59,00,00,000.00
2057 | Jul   | Level 17 | ₹ 91,35,266.80 | ₹ 1,38,87,379.66 | ₹ 61,00,00,000.00
2058 | Jan   | Level 17 | ₹ 93,17,971.14 | ₹ 1,41,29,950.21 | ₹ 63,15,00,000.00
2058 | Jul   | Level 17 | ₹ 95,04,327.56 | ₹ 1,43,74,416.96 | ₹ 65,45,00,000.00
```
The full output can be observed in demo_run.txt
