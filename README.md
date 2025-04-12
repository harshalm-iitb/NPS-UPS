# NPS vs UPS Corpus Comparison for IAS Officers

## Overview
This Python script calculates and compares the corpus of an IAS officer under the **Unfunded Pension Scheme (UPS)** and the **National Pension Scheme (NPS)**. It considers various factors such as career progression, pay commission rises, fitment factors, inflation, voluntary retirement (VRS), extraordinary leave (EOL) with no pay, **Dearness Relief (DR)**, and scenarios where the officer's **age of death occurs before retirement**. Additionally, it includes **spouse benefits**, where the legally wedded spouse receives **60% of the officer's pension** until their death.

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

| Parameter                     | Default Value       |
|-------------------------------|---------------------|
| **Joining Age**               | 26 years           |
| **Retirement Age**            | 60 years           |
| **Death Age**                 | 75 years           |
| **Spouse Age Difference**     | 0 years            |
| **Fitment Factor**            | 1.82               |
| **Annual Increment Rate**     | 3% (0.03)          |
| **Market Return Rate**        | 8% (0.08)          |
| **Inflation Rate**            | 5% (0.05)          |
| **Cost of Living Adjustment** | 20% (0.2)          |
| **Voluntary Retirement Age**  | Same as retirement |
| **Extraordinary Leave (EOL)** | 1 year             |
| **Pay Commission Interval**   | 10 years           |
| **Pay Commission Increase**   | 20% (0.2)          |
| **Superannuation Age**        | 60 years           |

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

#### UPS Lump Sum:
```
lump_sum = (1 / 10) * avg_last_12_months_salary * (qualifying_service_months / 6)
if IC > BC:
    lump_sum += (IC - BC)
```
- **`qualifying_service_months`**: The total number of service months.
- **Condition**: Lump sum is only provided if the officer has completed at least 25 years of service.
- **Adjustment**: If the individual corpus (`IC`) exceeds the benchmark corpus (`BC`), the positive difference `(IC - BC)` is added to the lump sum.

#### UPS Corpus:
The UPS corpus is calculated as the present value of all future pension payments, adjusted for inflation and Dearness Relief (DR).

1. **Annual Pension with DR**:
   ```
   adjusted_pension = monthly_pension * (1 + dr_rate)
   ```
   - **`dr_rate`**: Dearness Relief rate (default: 3% or 0.03).

2. **Present Value of Pension**:
   ```
   present_value = annual_pension / ((1 + inflation_rate) ** years_since_retirement)
   ```
   - **`annual_pension`**: The officer's annual pension.
   - **`inflation_rate`**: The expected inflation rate (default: 5% or 0.05).
   - **`years_since_retirement`**: The number of years since the officer retired.

3. **Total UPS Corpus**:
   ```
   ups_corpus = sum(present_value for each year) + lump_sum
   ```
   - The total UPS corpus includes the present value of all pension payments and the lump sum (if applicable).

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
- **Annuity Percentage**: 40% of the NPS corpus is used for annuity.
- **Annuity Rate**: 6% annual return on the annuity corpus.
- **Lump Sum**: 60% of the NPS corpus is available as a lump sum at retirement.
- **RoP**: The full annuity corpus is returned to the nominee upon death.

---

## Assumptions
1. **Benchmark Corpus**:
   - The benchmark corpus (BC) is assumed to be the same as the individual corpus (IC), given that no extra investment is made in the pension corpus and no premature withdrawals are made.
2. **Switch to UPS**:
   - The default switch date is **April 2025**, but the user can specify a different date.
   - Contributions to the individual corpus after the switch are based on the salary progression.

---

## Corner Cases Handled

1. **Death Before Retirement**:
   - If the officer's death occurs before retirement, the salary progression and contributions stop, and the UPS corpus is set to `0`.
   - NPS contributions also stop, and the corpus is calculated based on the contributions made until the death year.

2. **Spouse Benefits**:
   - If the officer passes away, the spouse receives **60% of the officer's pension** until their death. The user can specify the age difference between the officer's death and the spouse's death.

3. **Extraordinary Leave (EOL)**:
   - If the officer takes a year of leave without pay, the salary progression and contributions are skipped for that year.

4. **Pay Commission Adjustments**:
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
11. **Extraordinary Leave (EOL)**: The number of years the officer takes leave without pay (default: 1).

---

## Demo Run

```plaintext
Corpus Comparison (UPS vs NPS)
Enter birth year of the officer (default: 1996): 
Enter year of joining the service (default: 2022): 
Enter retirement age (default: 60): 
Enter death age (default: 75):
Enter the age difference between spouse's death and employee's death (negative values allowed, default: 0): 
Choose a Life Cycle Fund for NPS:
1. Aggressive Life Cycle Fund (LC75) - 75% equity up to 35 years, reduces to 15% by 55 years.
2. Moderate Life Cycle Fund (LC50) - 50% equity up to 35 years, reduces to 10% by 55 years.
3. Conservative Life Cycle Fund (LC25) - 25% equity up to 35 years, reduces to 5% by 55 years.
Enter your choice (1/2/3, default: 2): 
Enter the inflation rate (default: 0.05 for 5%): 
Enter the cost of living adjustment (default: 0.2 for 20%): 
Enter market return rate (default: 0.08 for 8%):
Enter pay commission interval in years (default: 10): 

--- Salary Progression ---
Year: 2022, Age: 26, Monthly Salary: ₹85,833.00
Year: 2023, Age: 27, Monthly Salary: ₹88,407.99
...

Final UPS Corpus (Including Dearness Relief and Spouse Benefits): ₹353,325,195.97

Final NPS Corpus (Including Returns): ₹238,907,641.76
