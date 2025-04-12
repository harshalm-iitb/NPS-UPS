import numpy as np
import numpy_financial as npf
import locale
from datetime import datetime, date

try:
    from tabulate import tabulate  # Import tabulate for better table formatting
except ImportError:
    tabulate = None  # Fallback if tabulate is not installed

# -------------------------------
# Global Constants and Pay Scales
# -------------------------------
PAY_SCALES = [
    {"level": 10, "basic_pay": 56100, "years_in_scale": 4},  # Junior Time Scale
    {"level": 11, "basic_pay": 67700, "years_in_scale": 5},  # Senior Time Scale
    {"level": 12, "basic_pay": 78800, "years_in_scale": 4},  # Junior Administrative Grade
    {"level": 13, "basic_pay": 123100, "years_in_scale": 1}, # Selection Grade
    {"level": 14, "basic_pay": 144200, "years_in_scale": 4}, # Super Time Scale
    {"level": 15, "basic_pay": 182200, "years_in_scale": 7}, # Senior Administrative Grade
    {"level": 16, "basic_pay": 205400, "years_in_scale": 5}, # HAG Scale
    {"level": 17, "basic_pay": 225000, "years_in_scale": 6}, # Apex Scale
    {"level": 18, "basic_pay": 250000, "years_in_scale": 2}, # Cabinet Secretary
]

# Define overall_table globally to track salary and NPS corpus progression
overall_table = []

# Global table for UPS values to avoid recalculation
ups_values_table = []

# Month constants (1-based)
JANUARY = 1
APRIL = 4
JULY = 7
DECEMBER = 12

def calculate_monthly_salary(pay_scale_level, months_at_level, increment_months):
    """
    Calculate the monthly salary for a given pay scale level and months at that level.
    Includes Dearness Allowance (DA) as 53% of the basic pay.
    
    Parameters:
    - pay_scale_level: The level in PAY_SCALES
    - months_at_level: How many months the officer has been at this level
    - increment_months: How many times the July increment has been applied
    """
    increment_rate = 0.03  # Fixed 3% annual increment
    pay_scale = next((scale for scale in PAY_SCALES if scale["level"] == pay_scale_level), None)
    if not pay_scale:
        raise ValueError(f"Invalid pay scale level: {pay_scale_level}")

    basic_pay = pay_scale["basic_pay"] * (1 + increment_rate) ** increment_months
    salary = basic_pay + (0.53 * basic_pay)  # Add Dearness Allowance (DA)
    return salary, basic_pay

def update_pay_scales_for_pay_commission(fitment_factor):
    """
    Update all pay scale levels globally by applying the fitment factor.
    """
    for i, scale in enumerate(PAY_SCALES):
        # Use the previous level's basic pay if it exists, otherwise use the current level's basic pay
        previous_level_basic_pay = PAY_SCALES[i - 1]["basic_pay"] if i > 0 else scale["basic_pay"]
        # Calculate the updated basic pay
        updated_basic_pay = max(
            scale["basic_pay"] * fitment_factor,
            previous_level_basic_pay * (1.03 ** (scale["years_in_scale"] + 2))
        )
        scale["basic_pay"] = updated_basic_pay

def get_pay_scale_for_service_months(service_months):
    """
    Determine the pay scale based on total service months.
    Returns the pay scale and months spent in current scale.
    Pay scale updates apply from January.
    """
    cumulative_months = 0
    for i, scale in enumerate(PAY_SCALES):
        scale_months = scale["years_in_scale"] * 12
        cumulative_months += scale_months
        if service_months < cumulative_months:
            months_in_current_scale = service_months - (cumulative_months - scale_months)
            return scale, months_in_current_scale
    
    # If all levels are completed, return the last scale
    last_scale = PAY_SCALES[-1]
    last_scale_months = last_scale["years_in_scale"] * 12
    return last_scale, service_months - (cumulative_months - last_scale_months)

def calculate_fitment_factor(inflation_rate, cost_of_living_adjustment=0.2):
    """
    Calculate the fitment factor using Ackroyd's formula and cost of living adjustments (COLA).
    """
    years_elapsed = 10  # Fixed to 10 years
    inflation_adjustment = (1 + inflation_rate) ** years_elapsed
    fitment_factor = inflation_adjustment + cost_of_living_adjustment
    return fitment_factor

def calculate_nps_corpus(
    equity_return=0.12, 
    corporate_bond_return=0.08, 
    gsec_return=0.06,
    life_cycle_fund="LC50"  # Added parameter for life cycle fund selection
):
    """
    Calculate the NPS corpus based on monthly contributions and market returns.
    Updates the overall_table with cumulative NPS corpus for each month.
    
    Parameters:
    - equity_return: Annual return for equity (default: 12%)
    - corporate_bond_return: Annual return for corporate bonds (default: 8%)
    - gsec_return: Annual return for government securities (default: 6%)
    - life_cycle_fund: Selected life cycle fund (default: LC50)
    """
    corpus = 0
    employee_contribution_rate = 0.1  # Fixed employee contribution rate (10%)
    
    for i, entry in enumerate(overall_table):
        # Calculate the officer's age for the current year
        age = entry["year"] - overall_table[0]["year"] + (entry["month"] - overall_table[0]["month"]) / 12
        
        # Determine allocation percentages based on selected life cycle fund
        if life_cycle_fund == "LC75":
            if age <= 35:
                equity_allocation = 0.75
            else:
                equity_allocation = max(0.75 - 0.03 * (age - 35), 0.15)
        elif life_cycle_fund == "LC25":
            if age <= 35:
                equity_allocation = 0.25
            else:
                equity_allocation = max(0.25 - 0.01 * (age - 35), 0.05)
        else:  # Default to LC50
            if age <= 35:
                equity_allocation = 0.50
            else:
                equity_allocation = max(0.50 - 0.02 * (age - 35), 0.10)
        
        remaining_allocation = 1.0 - equity_allocation
        corporate_bond_allocation = remaining_allocation * 0.6  # 60% of remaining allocation
        gsec_allocation = remaining_allocation * 0.4  # 40% of remaining allocation
        
        # Calculate weighted monthly return
        weighted_monthly_return = (
            equity_allocation * (equity_return / 12) +
            corporate_bond_allocation * (corporate_bond_return / 12) +
            gsec_allocation * (gsec_return / 12)
        )
        
        # Calculate monthly contribution
        govt_rate = 0.14 if entry["year"] >= 2019 else 0.12
        monthly_contribution = entry["monthly_salary"] * (employee_contribution_rate + govt_rate)
        
        # Apply monthly return to the corpus
        corpus = (corpus + monthly_contribution) * (1 + weighted_monthly_return)
        
        # Update the entry with the current NPS corpus
        overall_table[i]["nps_corpus"] = corpus
    
    return corpus

def calculate_nps_pension_with_rop(nps_corpus, annuity_percentage=0.40, annuity_rate=0.06):
    """
    Calculate the NPS pension based on the final corpus and annuity plan with Return of Purchase Price.
    
    Parameters:
    - nps_corpus: The final NPS corpus at retirement
    - annuity_percentage: Percentage of corpus used for annuity (default: 40%)
    - annuity_rate: Annual annuity rate for Return of Purchase Price plan (default: 6%)
    
    Returns:
    - monthly_pension: Monthly pension amount
    - lump_sum: Lump sum amount available at retirement (60% of corpus)
    - rop_value: The purchase price that will be returned to nominees upon death
    """
    annuity_corpus = nps_corpus * annuity_percentage
    lump_sum = nps_corpus * (1 - annuity_percentage)
    
    # Annual pension amount (6% of annuity corpus)
    annual_pension = annuity_corpus * annuity_rate
    monthly_pension = annual_pension / 12
    
    # RoP value is the same as the annuity corpus
    rop_value = annuity_corpus
    
    return monthly_pension, lump_sum, rop_value

def initialize_ups_values(
    retirement_date,
    inflation_rate, 
    fitment_factor, 
    pay_commission_interval,
    retirement_age,  # Added retirement_age parameter
    switch_date=date(2025, 4, 1),  # Default switch date to April 2025
    pension_fund_nav_rate=0.08  # Default Pension Fund NAV growth rate (8%)
):
    """
    Initialize the UPS values table with basic information for each year after retirement.
    This creates a global table that can be incrementally updated.
    """
    global ups_values_table
    ups_values_table = []
    
    # Find the last 12 months' salary before retirement
    retirement_entries = [e for e in overall_table if 
                         (e["year"] < retirement_date.year) or 
                         (e["year"] == retirement_date.year and e["month"] <= retirement_date.month)]
    
    if not retirement_entries:
        return
    
    # Calculate the average of the last 12 months' salary
    last_12_months = retirement_entries[-12:] if len(retirement_entries) >= 12 else retirement_entries
    avg_last_12_months_salary = sum(e["monthly_salary"] for e in last_12_months) / len(last_12_months)
    
    # Calculate total service in months
    first_entry = overall_table[0]
    first_date = date(first_entry["year"], first_entry["month"], 1)
    service_months = (retirement_date.year - first_date.year) * 12 + retirement_date.month - first_date.month
    
    # Initialize benchmark corpus to start from 0
    benchmark_corpus = 0

    # Grow benchmark corpus before the switch date
    # Contributions to the benchmark corpus are calculated based on monthly salary progression
    for entry in overall_table:
        if entry["year"] < switch_date.year or (entry["year"] == switch_date.year and entry["month"] <= switch_date.month):
            monthly_contribution = entry["monthly_salary"] * 0.2  # 10% employee + 10% government
            benchmark_corpus += monthly_contribution  # Add monthly contributions to the benchmark corpus
            benchmark_corpus *= (1 + pension_fund_nav_rate / 12)  # Grow benchmark corpus at NAV rate
        else:
            break

    # Initialize individual corpus (IC) at the switch date
    # The individual corpus is set to the NPS corpus accumulated until the switch date
    individual_corpus = 0
    for entry in overall_table:
        if entry["year"] < switch_date.year or (entry["year"] == switch_date.year and entry["month"] <= switch_date.month):
            individual_corpus = entry["nps_corpus"]
            monthly_contribution = entry["monthly_salary"] * 0.2  # 10% employee + 10% government
            benchmark_corpus += monthly_contribution
            benchmark_corpus *= (1 + pension_fund_nav_rate / 12)
        else:
            break

    # After the switch, add contributions to both individual corpus and benchmark corpus
    for entry in overall_table:
        if entry["year"] > switch_date.year or (entry["year"] == switch_date.year and entry["month"] > switch_date.month):
            monthly_contribution = entry["monthly_salary"] * 0.2  # 10% employee + 10% government
            individual_corpus += monthly_contribution  # Add contributions to individual corpus
            benchmark_corpus += monthly_contribution  # Add contributions to benchmark corpus

        # Grow both individual corpus and benchmark corpus at the Pension Fund NAV rate
        individual_corpus *= (1 + pension_fund_nav_rate / 12)
        benchmark_corpus *= (1 + pension_fund_nav_rate / 12)

    # Calculate initial pension
    # The pension is based on the ratio of individual corpus to benchmark corpus, capped at 1
    pension_percentage = min(service_months / 300, 1)  # Cap service months at 25 years (300 months)
    corpus_ratio = min(individual_corpus / benchmark_corpus, 1)  # Upper cap at 1, no lower cap
    initial_pension = (avg_last_12_months_salary / 2) * corpus_ratio * pension_percentage
    
    # Lump sum calculation (gratuity, etc.)
    if service_months >= 25 * 12:  # Only if 25 years of service are completed
        qualifying_service_months = service_months
        lump_sum = (1 / 10) * avg_last_12_months_salary * (qualifying_service_months / 6)
        # Add the positive difference between individual_corpus and benchmark_corpus
        if individual_corpus > benchmark_corpus:
            lump_sum += (individual_corpus - benchmark_corpus)
    else:
                lump_sum = 0  # No lump sum if service is less than 25 years
    
    # Initialize the table with year-by-year values after retirement
    current_date = retirement_date
    current_pension = initial_pension
    
    # Assume we'll track 50 years after retirement to cover most possible death ages
    for year_offset in range(51):  # 0 to 50 years after retirement
        year = retirement_date.year + year_offset
        
        # Check for pay commission updates (April of pay commission years)
        is_pay_commission_year = False
        for pc_year in range(retirement_date.year, year + 1, pay_commission_interval):
            if year == pc_year:
                is_pay_commission_year = True
                break
        
        # Apply pay commission updates
        if is_pay_commission_year and year > retirement_date.year:  # Don't apply in retirement year
            current_pension = current_pension * fitment_factor
        
        # Apply DR (assume DR changes every year)
        dr_rate = 0.03  # 3% DR
        adjusted_pension = current_pension * (1 + dr_rate)
        
        # Add entry to the table
        ups_values_table.append({
            "year": year,
            "death_age": year - (retirement_date.year - retirement_date.month / 12 + retirement_age),  # Fixed usage
            "monthly_pension": adjusted_pension,
            "annual_pension": adjusted_pension * 12,
            "lump_sum": lump_sum if year == retirement_date.year else 0,  # Lump sum only in retirement year
            "present_value": 0,  # Will be calculated when we compute corpus for specific death ages
            "corpus": 0          # Will be computed when a specific death age is requested
        })
        
        # For next year
        current_pension = adjusted_pension

def calculate_ups_corpus_and_pension(
    death_year,
    inflation_rate, 
    retirement_date,
    retirement_age
):
    """
    Calculate the UPS corpus and monthly pension using the pre-computed UPS values table.
    Only calculates the present value for the specified death year.
    """
    global ups_values_table
    
    if not ups_values_table:
        return 0, 0, 0
    
    # Find entries from retirement to death year
    relevant_entries = [e for e in ups_values_table 
                        if e["year"] >= retirement_date.year and e["year"] <= death_year]
    
    if not relevant_entries:
        return 0, 0, 0
    
    # Calculate present value for each year's pension
    corpus = 0
    for entry in relevant_entries:
        # Calculate months since retirement for NPV
        months_since_retirement = (entry["year"] - retirement_date.year) * 12
        if entry["year"] == retirement_date.year:
            # For first year, only count months after retirement
            months_since_retirement = (12 - retirement_date.month)
        
        # Discount the annual pension to present value
        present_value = entry["annual_pension"] / ((1 + (inflation_rate / 12)) ** months_since_retirement)
        entry["present_value"] = present_value
        corpus += present_value
    
    # Add lump sum (from retirement year)
    lump_sum = next((e["lump_sum"] for e in relevant_entries if e["year"] == retirement_date.year), 0)
    corpus += lump_sum
    
    # Get the most recent monthly pension amount
    last_entry = relevant_entries[-1]
    monthly_pension = last_entry["monthly_pension"]
    
    # Update the corpus value in the table entries we used
    for entry in relevant_entries:
        entry["corpus"] = corpus
    
    return corpus, monthly_pension, lump_sum

def generate_mortality_comparison_table(
    birth_year, 
    birth_month,
    retirement_age,
    inflation_rate,
    fitment_factor,
    pay_commission_interval,
    nps_corpus,
    annuity_percentage,
    annuity_rate,
    spouse_age_difference
):
    """
    Generate a comparison table for different death ages.
    Updated to handle pre-retirement deaths correctly.
    """
    retirement_year = birth_year + retirement_age
    retirement_date = date(retirement_year, birth_month, 1)
    
    # Initialize the UPS values table if it hasn't been done yet
    if not ups_values_table:
        initialize_ups_values(
            retirement_date,
            inflation_rate,
            fitment_factor,
            pay_commission_interval,
            retirement_age
        )
    
    table_data = []
    
    # Calculate NPS values (they will be adjusted based on death age)
    monthly_pension_nps, lump_sum_nps, rop_value = calculate_nps_pension_with_rop(
        nps_corpus, 
        annuity_percentage=annuity_percentage, 
        annuity_rate=annuity_rate
    )
    
    # For each potential death year from first year of service to 100 years after birth
    # Start from the join year, not retirement year
    join_date = date(overall_table[0]["year"], overall_table[0]["month"], 1)
    death_year_start = join_date.year
    
    for death_year in range(death_year_start, birth_year + 101):
        # Use the month from birth_month for consistency
        death_month = birth_month
        
        # Calculate UPS corpus and pension for this death year
        ups_corpus, monthly_pension_ups, lump_sum_ups = calculate_ups_corpus_and_pension(
            death_year,
            death_month,
            inflation_rate,
            retirement_date,
            retirement_age
        )
        
        death_age = death_year - birth_year + (birth_month - 1) / 12  # More precise death age calculation
        is_pre_retirement = death_year < retirement_year or (death_year == retirement_year and death_month < retirement_date.month)
        
        # For pre-retirement deaths, calculate NPS death benefit
        if is_pre_retirement:
            # Find NPS corpus at time of death
            death_entries = [e for e in overall_table 
                            if (e["year"] < death_year) or 
                               (e["year"] == death_year and e["month"] <= death_month)]
            
            if death_entries:
                # Get NPS corpus at time of death
                nps_at_death = death_entries[-1]["nps_corpus"]
                
                # For pre-retirement death, entire NPS corpus is paid to nominees
                total_nps_value = nps_at_death
                monthly_pension_nps = 0  # No pension before retirement
                lump_sum_nps = nps_at_death  # Entire corpus as lump sum
            else:
                total_nps_value = 0
                monthly_pension_nps = 0
                lump_sum_nps = 0
        else:
            # Post-retirement calculations remain the same
            # Calculate spouse's death year
            spouse_death_year = death_year + spouse_age_difference
            spouse_pension_years = max(0, spouse_death_year - death_year)
            spouse_pension = monthly_pension_ups * 0.6 * 12 * spouse_pension_years  # 60% of assured payout
            
            # Add spouse's pension to UPS corpus
            ups_corpus += spouse_pension
            
            # Calculate total NPS value including pension received and return of purchase price
            years_receiving_pension = death_year - retirement_year
            total_nps_value = lump_sum_nps + (monthly_pension_nps * 12 * years_receiving_pension) + rop_value
        
        # Add row to table - adjust the display for pre-retirement deaths
        if is_pre_retirement:
            table_data.append([
                death_age,
                0,  # No NPS monthly pension before retirement
                lump_sum_nps,  # Entire NPS corpus as lump sum
                lump_sum_ups,  # Death gratuity
                monthly_pension_ups,  # Family pension
                ups_corpus,
                total_nps_value
            ])
        else:
            table_data.append([
                death_age,
                monthly_pension_nps,
                lump_sum_nps,
                lump_sum_ups,
                monthly_pension_ups,
                ups_corpus,
                total_nps_value
            ])
    
    return table_data

def main():
    print("Monthly-Based Corpus Comparison (UPS vs NPS with RoP Annuity)")
    print("-------------------------------------------------------------")
    # Input variables with default values
    birth_year = int(input("Enter birth year of the officer (default: 1996): ") or 1996)
    birth_month = int(input("Enter birth month (1-12, default: 6): ") or 6)
    
    year_of_joining = int(input("Enter year of joining the service (default: 2023): ") or 2023)
    month_of_joining = int(input("Enter month of joining (1-12, default: 12): ") or 12)
    
    # Seniority year might be different from joining year
    seniority_year = int(input("Enter seniority year (default: 2022): ") or 2022)
    seniority_month = int(input("Enter seniority month (1-12, default: 1): ") or 1)
    
    retirement_age = int(input("Enter retirement age (default: 60): ") or 60)
    retirement_month = birth_month  # Retirement occurs on the last day of the birth month
    retirement_year = birth_year + retirement_age
    retirement_date = date(retirement_year, retirement_month, 1)
    
    death_age = int(input("Enter death age (default: 75): ") or 75)
    death_year = birth_year + death_age  # Calculate death year
    death_month = birth_month  # Use birth month for consistency

    # Get fitment factor
    fitment_factor_input = input("Enter fitment factor or press Enter to calculate using Ackroyd's formula (default inflation: 5%, COLA: 20%): ").strip()
    if fitment_factor_input:
        fitment_factor = float(fitment_factor_input)
        inflation_rate = float(input("Enter inflation rate (default: 0.05 for 5%): ") or 0.05)
    else:
        inflation_rate = 0.05  # Default inflation rate
        cost_of_living_adjustment = 0.2  # Default COLA
        fitment_factor = calculate_fitment_factor(inflation_rate, cost_of_living_adjustment)

    print(f"Calculated Fitment Factor: {fitment_factor}")

    # NPS return rates
    equity_return = float(input("Enter annual equity return rate (default: 0.12 for 12%): ") or 0.12)
    corporate_bond_return = float(input("Enter annual corporate bond return rate (default: 0.08 for 8%): ") or 0.08)
    gsec_return = float(input("Enter annual G-Sec return rate (default: 0.06 for 6%): ") or 0.06)
    
    # NPS annuity parameters
    annuity_percentage = float(input("Enter percentage of NPS corpus for annuity (default: 0.40 for 40%): ") or 0.40)
    annuity_rate = float(input("Enter annual annuity rate for Return of Purchase Price plan (default: 0.06 for 6%): ") or 0.06)
    
    # Pay commission details
    pay_commission_interval = int(input("Enter pay commission interval in years (default: 10): ") or 10)
    seventh_pay_commission_year = 2016  # 7th Pay Commission year
    pay_commission_years = [year for year in range(seventh_pay_commission_year, 2100, pay_commission_interval)]
    
    # Ask the user to choose a life cycle fund
    print("\nChoose a Life Cycle Fund for NPS:")
    print("1. Aggressive Life Cycle Fund (LC75) - 75% equity up to 35 years, reduces to 15% by 55 years.")
    print("2. Moderate Life Cycle Fund (LC50) - 50% equity up to 35 years, reduces to 10% by 55 years.")
    print("3. Conservative Life Cycle Fund (LC25) - 25% equity up to 35 years, reduces to 5% by 55 years.")
    life_cycle_choice = input("Enter your choice (1/2/3, default: 2): ") or "2"
    
    if life_cycle_choice == "1":
        life_cycle_fund = "LC75"
    elif life_cycle_choice == "3":
        life_cycle_fund = "LC25"
    else:
        life_cycle_fund = "LC50"
    
    # Ask for spouse's age difference
    global spouse_age_difference  # Make it global so it can be accessed in the calculate_ups_corpus_and_pension function
    spouse_age_difference = int(input("Enter the age difference between spouse's death and employee's death (negative values allowed, default: 0): ") or 0)

    # Set locale for currency formatting
    try:
        locale.setlocale(locale.LC_ALL, 'en_IN.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'en_IN')
        except:
            locale.setlocale(locale.LC_ALL, '')  # Use system default if Indian locale not available

    # Generate monthly salary progression
    global overall_table
    overall_table = []
    
    # Calculate seniority-based service months (for pay scale determination)
    seniority_start_date = date(seniority_year, seniority_month, 1)
    
    # Starting date
    current_date = date(year_of_joining, month_of_joining, 1)
    
    # Track July increments
    last_increment_date = None
    increment_count = 0
    
    # Process month by month until retirement
    while current_date <= retirement_date:  # Include the retirement month
        # Calculate seniority-based service months
        seniority_months = (current_date.year - seniority_start_date.year) * 12 + (current_date.month - seniority_start_date.month)
        
        # Update pay scales if it's April of a pay commission year (Pay Commission updates from April)
        if current_date.month == APRIL and current_date.year in pay_commission_years:
            update_pay_scales_for_pay_commission(fitment_factor)
            
        # Apply increment if it's July and we haven't had an increment this July
        if current_date.month == JULY and (last_increment_date is None or 
                                          current_date.year > last_increment_date.year):
            increment_count += 1
            last_increment_date = current_date
        
        # Get current pay scale and months in this scale based on seniority
        current_scale, months_in_scale = get_pay_scale_for_service_months(seniority_months)
        
        # Calculate monthly salary using increment count for the 3% annual raises
        monthly_salary, basic_pay = calculate_monthly_salary(current_scale["level"], months_in_scale, increment_count)
        
        overall_table.append({
            "year": current_date.year,
            "month": current_date.month,
            "monthly_salary": monthly_salary,
            "basic_pay": basic_pay,
            "pay_level": current_scale["level"],
            "months_in_scale": months_in_scale,
            "increments": increment_count,
            "nps_corpus": 0  # Initialize, will be updated by calculate_nps_corpus
        })
        
        # Move to the next month
        if current_date.month == 12:
            current_date = date(current_date.year + 1, 1, 1)
        else:
            current_date = date(current_date.year, current_date.month + 1, 1)

    # Calculate NPS corpus and update the overall_table with monthly NPS corpus values
    nps_corpus = calculate_nps_corpus(
        equity_return, 
        corporate_bond_return, 
        gsec_return, 
        life_cycle_fund=life_cycle_fund  # Pass selected life cycle fund
    )
    
    # Calculate NPS pension with Return of Purchase Price
    monthly_pension, lump_sum, rop_value = calculate_nps_pension_with_rop(
        nps_corpus, 
        annuity_percentage=annuity_percentage, 
        annuity_rate=annuity_rate
    )
    
    # Initialize the UPS values table
    initialize_ups_values(
        retirement_date,
        inflation_rate,
        fitment_factor,
        pay_commission_interval,
        retirement_age  # Pass retirement_age as an argument
    )
    
    # Check if death is pre-retirement
    is_pre_retirement = death_year < retirement_year or (death_year == retirement_year and death_month < retirement_month)
    
    # Calculate UPS corpus for the input death year and month
    ups_corpus, monthly_pension_ups, lump_sum_ups = calculate_ups_corpus_and_pension(
        death_year,
        death_month,
        inflation_rate, 
        retirement_date,
        retirement_age
    )

    # Display results - show key level changes and pay commission months
    print("\n--- Salary and NPS Corpus Progression (Key Months) ---")
    print("Year | Month | Pay Level | Basic Pay | Monthly Salary | NPS Corpus")
    print("-----|-------|-----------|-----------|---------------|----------")
    
    # Show only key months for readability
    displayed_entries = []
    prev_level = None
    
    for i, entry in enumerate(overall_table):
        is_key_month = False
        
        # Show first entry
        if i == 0:
            is_key_month = True
        
        # Show pay level changes (from January)
        elif entry["pay_level"] != prev_level and entry["month"] == JANUARY:
            is_key_month = True
            
        # Show pay commission months (April)
        elif entry["month"] == APRIL and entry["year"] in pay_commission_years:
            is_key_month = True
            
        # Show increment months (July)
        elif entry["month"] == JULY and (i == 0 or overall_table[i-1]["increments"] != entry["increments"]):
            is_key_month = True
            
        # Show January of each year
        elif entry["month"] == JANUARY:
            is_key_month = True
            
        # Show last entry
        elif i == len(overall_table) - 1:
            is_key_month = True
            
        if is_key_month:
            displayed_entries.append(entry)
            
        prev_level = entry["pay_level"]
    
    for entry in displayed_entries:
        month_name = date(2000, entry["month"], 1).strftime('%b')
        print(f"{entry['year']} | {month_name:5} | Level {entry['pay_level']} | {locale.currency(entry['basic_pay'], grouping=True)} | {locale.currency(entry['monthly_salary'], grouping=True)} | {locale.currency(entry['nps_corpus'], grouping=True)}")

    print(f"\nTotal months in service: {len(overall_table)}")
    
    # Display pre-retirement death notice if applicable
    if is_pre_retirement:
        print("\n--- PRE-RETIREMENT DEATH SCENARIO ---")
        print(f"Death occurs at age {death_age}, before retirement age {retirement_age}")
        print(f"NPS Benefit: Full corpus of {locale.currency(lump_sum_nps, grouping=True)} paid to nominees")
        print(f"UPS Family Pension: {locale.currency(monthly_pension_ups, grouping=True)} per month until spouse's death")
        print(f"UPS Death Gratuity: {locale.currency(lump_sum_ups, grouping=True)}")
    else:
        # Display NPS details with RoP
        print("\n--- NPS with Return of Purchase Price (RoP) Details ---")
        print(f"Final NPS Corpus: {locale.currency(nps_corpus, grouping=True)}")
        print(f"Lump Sum at Retirement ({(1-annuity_percentage)*100:.0f}%): {locale.currency(lump_sum, grouping=True)}")
        print(f"Amount Used for Annuity ({annuity_percentage*100:.0f}%): {locale.currency(rop_value, grouping=True)}")
        print(f"Monthly NPS Pension (at {annuity_rate*100:.1f}% annuity rate): {locale.currency(monthly_pension, grouping=True)}")
        print(f"Return of Purchase Price on Death: {locale.currency(rop_value, grouping=True)}")
        
        # Display UPS details
        print("\n--- UPS Details ---")
        print(f"Total UPS Corpus (Pension + Gratuity): {locale.currency(ups_corpus, grouping=True)}")
        print(f"UPS Monthly Pension: {locale.currency(monthly_pension_ups, grouping=True)}")
        print(f"UPS Lump Sum (Gratuity): {locale.currency(lump_sum_ups, grouping=True)}")
    
    # Generate mortality comparison table
    print("\n--- NPS vs UPS Comparison Across Different Death Ages ---")
    print("(Including Pre-Retirement Death Benefits)")
    
    mortality_table = generate_mortality_comparison_table(
        birth_year, 
        birth_month,
        retirement_age,
        inflation_rate,
        fitment_factor,
        pay_commission_interval,
        nps_corpus,
        annuity_percentage,
        annuity_rate,
        spouse_age_difference  # Pass spouse age difference
    )
    
    # Format table headers and data for display
    headers = [
        "Death Age",
        "NPS Monthly Pension",
        "NPS Lump Sum",
        "UPS Lump Sum",
        "UPS Monthly Pension",
        "UPS Total Corpus",
        "NPS Total Value"
    ]
    
    # Format currency values in the table
    formatted_table = []
    for row in mortality_table:
        formatted_row = [
            row[0],  # Death Age (no formatting)
            locale.currency(row[1], grouping=True),  # NPS Monthly Pension
            locale.currency(row[2], grouping=True),  # NPS Lump Sum
            locale.currency(row[3], grouping=True),  # UPS Lump Sum
            locale.currency(row[4], grouping=True),  # UPS Monthly Pension
            locale.currency(row[5], grouping=True),  # UPS Total Corpus
            locale.currency(row[6], grouping=True)   # NPS Total Value
        ]
        formatted_table.append(formatted_row)
    
    # Display the table 
    try:
        if tabulate:
            print(tabulate(formatted_table, headers=headers, tablefmt="grid"))
        else:
            raise ImportError
    except ImportError:
        # Fallback if tabulate is not available
        print("|".join(headers))
        print("-" * 120)
        for row in formatted_table:
            print("|".join(str(col) for col in row))
    
    # Create a summary of which system is better at different death ages
    print("\n--- Summary: Which System Is Better at Different Death Ages ---")
    better_system_changes = []
    prev_better = None
    
    for row in mortality_table:
        death_age = row[0]
        ups_value = row[5]
        nps_value = row[6]
        
        current_better = "UPS" if ups_value > nps_value else "NPS"
        
        if prev_better is None or current_better != prev_better:
            better_system_changes.append((death_age, current_better, ups_value, nps_value))
            prev_better = current_better
    
    if better_system_changes:
        for i, (age, system, ups_value, nps_value) in enumerate(better_system_changes):
            if i == 0:
                if age > retirement_age:
                    print(f"Before age {age}: Data not available (before retirement)")
                print(f"From age {age}: {system} is better")
            else:
                print(f"From age {age}: {system} is better")
                
            print(f"  UPS value at age {age}: {locale.currency(ups_value, grouping=True)}")
            print(f"  NPS value at age {age}: {locale.currency(nps_value, grouping=True)}")
            diff = abs(ups_value - nps_value)
            percent_diff = (diff / min(ups_value, nps_value)) * 100
            print(f"  Difference: {locale.currency(diff, grouping=True)} ({percent_diff:.2f}%)")
            print("")
    else:
        print("No data available for comparison")

if __name__ == "__main__":
    main()
