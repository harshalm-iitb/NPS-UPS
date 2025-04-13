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
  - Starts from 0 and grows based on monthly contributions (`monthly_salary * 0.2`) and the Pension Fund NAV rate (default: 8% annually, user-configurable).
  - Before the switch: Contributions are added to the benchmark corpus, and it grows at the NAV rate.
  - After the switch: Any addition to the individual corpus is matched in the benchmark corpus.
- **`service_months`**: The total number of service months, capped at 300 months (25 years).

#### Switch to UPS:
- The switch from NPS to UPS is assumed to occur in **April 2025** by default. The user can specify a different switch date.
- At the moment of the switch:
  - The **individual corpus (IC)** is set to the NPS corpus accumulated until the switch date.
  - The **benchmark corpus (BC)** starts from 0 and grows based on contributions and the Pension Fund NAV rate.
  - After the switch, both the employee and the government contribute **10% of the monthly salary** to the individual corpus, and the same amount is added to the benchmark corpus.
  - Both the individual corpus and benchmark corpus grow at the Pension Fund NAV rate (default: 8% annually, user-configurable).

#### Assumptions
1. **Benchmark Corpus**:
   - The benchmark corpus (BC) is assumed to grow based on monthly contributions (`monthly_salary * 0.2`) and the Pension Fund NAV rate. It is not directly linked to the individual corpus (IC) but grows in parallel after the switch.
   - No premature withdrawals or additional investments are assumed for the individual corpus.
2. **Switch to UPS**:
   - The default switch date is **April 2025**, but the user can specify a different date.
   - Contributions to the individual corpus and benchmark corpus after the switch are based on the salary progression and grow at the Pension Fund NAV rate.

#### UPS Lump Sum:
```
lump_sum = (1 / 10) * avg_last_12_months_salary * (qualifying_service_months / 6)
if IC > BC:
    lump_sum += (IC - BC)
```

#### UPS Corpus:
The UPS corpus is calculated as the present value of all future pension payments, adjusted for inflation and Dearness Relief (DR).

1. **Annual Pension with DR**:
   `````
   adjusted_pension = monthly_pension * (1 + dr_rate) ** (2 * years_since_retirement)
   `````
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
   - The nominal UPS corpus is the sum of all annual pension payments without adjusting for inflation.

4. **Total UPS Corpus**:
   ```
   ups_corpus = sum(present_value for each year) + lump_sum
   ```
   - The total UPS corpus includes the inflation-adjusted present value of all pension payments and the lump sum (if applicable).

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
#### Function: `calculate_nps_pension_with_rop`
This function calculates the monthly pension, lump sum, and Return of Purchase Price (RoP) based on the final NPS corpus at retirement.

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
   - The remaining corpus (default: 60%) is available as a lump sum at retirement.

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
   - The annuity corpus is returned to the nominee upon the death of the pensioner.

#### Assumptions and Default Values:
- **Annuity Rate**: 6% annual return on the annuity corpus.
- **Lump Sum**: 60% of the NPS corpus is available as a lump sum at retirement.
- **RoP**: The full annuity corpus is returned to the nominee upon death.

#### Total NPS Value:
The total NPS value includes both nominal and inflation-adjusted values:

1. **Nominal NPS Value**:
   ```
   nominal_nps_value = lump_sum + (monthly_pension * 12 * years_receiving_pension) + rop_value
   ```
   - **`lump_sum`**: The lump sum available at retirement.
   - **`monthly_pension`**: The monthly pension amount.
   - **`years_receiving_pension`**: The number of years the pension is received.
   - **`rop_value`**: The Return of Purchase Price.

2. **Inflation-Adjusted NPS Value**:
   ```
   inflation_adjusted_nps_value = lump_sum + (monthly_pension * 12 * years_receiving_pension) * ((1 + inflation_rate) * (1 - (1 / (1 + inflation_rate) ** years_receiving_pension)) / inflation_rate) + rop_value / ((1 + inflation_rate) ** years_receiving_pension)
   ```
   - Adjusts the pension payments and RoP for inflation over the years.
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
...existing content...

--- NPS with Return of Purchase Price (RoP) Details ---
Final NPS Corpus: ₹ 55,51,28,076.23
Lump Sum at Retirement (0%): ₹ 0.00
Amount Used for Annuity (100%): ₹ 55,51,28,076.23
Monthly NPS Pension (at 6.0% annuity rate): ₹ 27,75,640.38
Return of Purchase Price on Death: ₹ 55,51,28,076.23

--- UPS Details ---
Total UPS Corpus (Pension + Gratuity): ₹ 1,19,70,01,509.90
UPS Monthly Pension: ₹ 1,08,05,740.59
UPS Lump Sum (Including withdrawal of 0.0%): ₹ 5,65,09,902.93

--- NPS vs UPS Comparison Across Different Death Ages ---
(Including Pre-Retirement Death Benefits)
+-------------+-----------------------+-----------------------+------------------+-------------------+-----------------------------------------+----------------------------------------+------------------------------+-----------------------------+
|   Death Age | UPS Monthly Pension   | NPS Monthly Pension   | UPS Lump Sum     | NPS Lump Sum      | UPS Total Corpus (Inflation-Adjusted)   | NPS Total Value (Inflation-Adjusted)   | UPS Total Corpus (Nominal)   | NPS Total Value (Nominal)   |
+=============+=======================+=======================+==================+===================+=========================================+========================================+==============================+=============================+
|          37 | ₹ 36,636.00           | ₹ 0.00                | ₹ 6,10,602.00    | ₹ 86,27,728.00    | ₹ 47,89,874.00                          | ₹ 86,27,728.00                         | ₹ 59,60,373.00               | ₹ 86,27,728.00              |
|          38 | ₹ 41,509.00           | ₹ 0.00                | ₹ 6,91,812.00    | ₹ 1,04,33,470.00  | ₹ 54,26,927.00                          | ₹ 1,04,33,470.00                       | ₹ 67,53,102.00               | ₹ 1,04,33,470.00            |
|          39 | ₹ 69,691.00           | ₹ 0.00                | ₹ 11,61,515.00   | ₹ 1,26,82,139.00  | ₹ 91,11,524.00                          | ₹ 1,26,82,139.00                       | ₹ 1,13,38,102.00             | ₹ 1,26,82,139.00            |
|          40 | ₹ 1,50,862.00         | ₹ 0.00                | ₹ 25,14,373.00   | ₹ 1,59,41,552.00  | ₹ 1,97,24,038.00                        | ₹ 1,59,41,552.00                       | ₹ 2,45,43,990.00             | ₹ 1,59,41,552.00            |
...existing content...

--- Summary: Which System Is Better at Different Death Ages ---
From age 37: NPS is better
  UPS value at age 37: ₹ 47,89,873.88
  NPS value at age 37: ₹ 86,27,728.31
  Difference: ₹ 38,37,854.43

From age 40: UPS is better
  UPS value at age 40: ₹ 1,97,24,037.94
  NPS value at age 40: ₹ 1,59,41,552.01
  Difference: ₹ 37,82,485.94

From age 43: NPS is better
  UPS value at age 43: ₹ 2,98,60,062.50
  NPS value at age 43: ₹ 3,26,50,834.79
  Difference: ₹ 27,90,772.30

From age 44: UPS is better
  UPS value at age 44: ₹ 4,26,37,516.27
  NPS value at age 44: ₹ 4,01,34,432.02
  Difference: ₹ 25,03,084.25

From age 45: NPS is better
  UPS value at age 45: ₹ 4,64,99,973.63
  NPS value at age 45: ₹ 4,90,83,770.69
  Difference: ₹ 25,83,797.06
```

---

## Analysis

1. **Pre-Retirement Death**:
   - The UPS payment exceeds the NPS benefits every time the pay scale changes. This is due to the death gratuity and family pension provided under UPS, which are based on the officer's last drawn salary.

2. **Post-Retirement Death**:
   - NPS is better immediately after retirement due to the large corpus and annuity-based pension.
   - However, UPS benefits start accumulating over time due to Dearness Relief (DR) and pay commission updates, eventually surpassing NPS benefits at later ages.

3. **Switch Points**:
   - The comparison table highlights specific ages where one system becomes better than the other. These switch points depend on factors like inflation, DR, and the officer's lifespan.
````
