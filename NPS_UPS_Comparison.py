import numpy as np
import numpy_financial as npf
import locale
from datetime import datetime, date

import csv  # Import csv for generating CSV files

try:
    from tabulate import tabulate  # Import tabulate for better table formatting
except ImportError:
    tabulate = None  # Fallback if tabulate is not installed

# -------------------------------
# Global Constants and Pay Scales
# -------------------------------
# Define pay scales with levels, basic pay, and years in each scale
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

# Define global variables to track salary progression and UPS values
overall_table = []  # Tracks salary and NPS corpus progression
ups_values_table = []  # Tracks UPS values to avoid recalculation
inflation_rate = 0.05  # Default inflation rate (5%)
birth_year = 1996 # Year of birth
birth_month = 6 # Month of birth
normal_retirement_age = 60  # Normal retirement age
pension_fund_nav_rate = 0.08 # NAV rate for pension fund (8%)
withdrawal_percentage = 0
pay_commission_interval = 10 # Pay commission interval in years
retirement_age = 60  # Default retirement age
# Month constants for readability
JANUARY = 1
APRIL = 4
JULY = 7
DECEMBER = 12

# Minimum assured payout for UPS
MIN_UPS_PAYOUT = 10000

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

def calculate_fitment_factor(cost_of_living_adjustment=0.2):
    """
    Calculate the fitment factor using Ackroyd's formula and cost of living adjustments (COLA).
    """
    years_elapsed = 10  # Fixed to 10 years
    inflation_adjustment = (1 + inflation_rate) ** years_elapsed
    fitment_factor = inflation_adjustment + cost_of_living_adjustment
    return fitment_factor

def initialize_nps_corpus(
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
    return

def calculate_nps_pension_with_rop(death_year, retirement_date, annuity_rate):
    """
    Calculate the NPS pension based on the final corpus and annuity plan with Return of Purchase Price.
    """
    global withdrawal_percentage, overall_table, normal_retirement_age, inflation_rate, pension_fund_nav_rate, retirement_age
    nps_corpus = 0
    if not overall_table:
        # Return default values if overall_table is empty
        return 0, 0, 0, 0

    is_vrs = retirement_age < normal_retirement_age

    if isinstance(retirement_date, int):
        retirement_year = retirement_date
        retirement_month = 1
        retirement_date = date(retirement_year, retirement_month, 1)
    else:
        retirement_year = retirement_date.year
        retirement_month = retirement_date.month

    is_pre_retirement = death_year < retirement_date.year or (death_year == retirement_date.year and death_month < retirement_date.month)

    if is_pre_retirement:
        # For pre-retirement, use the last entry in overall_table
        pre_death_entries = [e for e in overall_table if 
            (e["year"] < death_year) or 
            (e["year"] == death_year and e["month"] <= death_month)]
        if not pre_death_entries:
            return 0, 0, 0, 0  # Handle edge case where no entries exist
        nps_corpus = pre_death_entries[-1]["nps_corpus"]
        annuity_corpus = 0
        lump_sum = nps_corpus
        nominal_nps_corpus = nps_corpus
        return 0, lump_sum, nps_corpus, nominal_nps_corpus
    elif is_vrs:
        # For VRS, use the last entry in overall_table
        vrs_entries = [e for e in overall_table if 
            (e["year"] < retirement_date.year) or 
            (e["year"] == retirement_date.year and e["month"] <= retirement_date.month)]
        if not vrs_entries:
            return 0, 0, 0, 0  # Handle edge case where no entries exist
        nps_corpus = vrs_entries[-1]["nps_corpus"]
        annuity_corpus = nps_corpus * (1 - withdrawal_percentage)
        annual_pension = annuity_corpus * annuity_rate
        monthly_pension = annual_pension / 12
        lump_sum = nps_corpus * withdrawal_percentage
        nominal_nps_corpus = lump_sum + annuity_corpus
        return monthly_pension, lump_sum, nps_corpus, nominal_nps_corpus
    else:
        # For post-retirement, use the last entry in overall_table
        post_retirement_entries = [e for e in overall_table if 
            (e["year"] < retirement_date.year) or 
            (e["year"] == retirement_date.year and e["month"] <= retirement_date.month)]
        if not post_retirement_entries:
            return 0, 0, 0, 0  # Handle edge case where no entries exist
        nps_corpus = post_retirement_entries[-1]["nps_corpus"]
        annuity_corpus = nps_corpus * (1 - withdrawal_percentage)
        annual_pension = annuity_corpus * annuity_rate
        monthly_pension = annual_pension / 12
        lump_sum = nps_corpus * withdrawal_percentage
        nominal_nps_corpus = lump_sum + annuity_corpus
        return monthly_pension, lump_sum, nps_corpus, nominal_nps_corpus
# ------------------------------------------------------------------------------------------------------------------------------

def initialize_ups_values(retirement_date, switch_date=date(2025, 4, 1)):
    """
    Calculate UPS values for the retiree with optimized approach.
    
    Args:
        retirement_date (date): The date of retirement
        switch_date (date): The date when the UPS scheme was implemented
        
    Returns:
        dict: UPS values and parameters dictionary
    """
    global overall_table, pension_fund_nav_rate, withdrawal_percentage, MIN_UPS_PAYOUT, fitment_factor
    global pay_commission_interval, inflation_rate, retirement_age
    
    # Find the last 12 months' salary before retirement
    retirement_entries = [e for e in overall_table if 
                         (e["year"] < retirement_date.year) or 
                         (e["year"] == retirement_date.year and e["month"] <= retirement_date.month)]
    
    if not retirement_entries:
        return {}
    
    # Calculate the average of the last 12 months' salary
    last_12_months = retirement_entries[-12:] if len(retirement_entries) >= 12 else retirement_entries
    avg_last_12_months_salary = sum(e["monthly_salary"] for e in last_12_months) / len(last_12_months)
    
    # Calculate total service in months
    first_entry = overall_table[0]
    first_date = date(first_entry["year"], first_entry["month"], 1)
    service_months = (retirement_date.year - first_date.year) * 12 + retirement_date.month - first_date.month
    
    # Check if service is at least 10 years (120 months)
    has_minimum_service = service_months >= 120
    
    # Initialize corpus values
    benchmark_corpus, individual_corpus = calculate_corpus_values(switch_date)
    
    # Calculate initial pension parameters
    pension_percentage = min(service_months / 300, 1)  # Cap at 25 years (300 months)
    corpus_ratio = min(individual_corpus / benchmark_corpus if benchmark_corpus > 0 else 0, 1)
    
    # Calculate initial assured payout (before lumpsum withdrawal adjustment)
    assured_payout = (avg_last_12_months_salary / 2) * corpus_ratio * pension_percentage
    
    # Calculate lumpsum withdrawal and adjusted pension
    lumpsum_withdrawal, excess_corpus, adjusted_pension = calculate_lumpsum_and_pension(
        withdrawal_percentage, benchmark_corpus, individual_corpus, assured_payout, has_minimum_service
    )
    
    # Calculate gratuity
    gratuity = 0
    if service_months >= 60:  # 5+ years for gratuity
        gratuity = (1/10) * avg_last_12_months_salary * (service_months / 6)
    
    # Total lump sum is gratuity + excess corpus + lumpsum withdrawal
    lump_sum = gratuity + excess_corpus + lumpsum_withdrawal
    
    return {
        "retirement_date": retirement_date,
        "service_months": service_months,
        "avg_last_12_months_salary": avg_last_12_months_salary,
        "benchmark_corpus": benchmark_corpus,
        "individual_corpus": individual_corpus,
        "corpus_ratio": corpus_ratio,
        "assured_payout": assured_payout,
        "adjusted_pension": adjusted_pension,
        "lumpsum_withdrawal": lumpsum_withdrawal,
        "excess_corpus": excess_corpus,
        "gratuity": gratuity,
        "lump_sum": lump_sum,
        "has_minimum_service": has_minimum_service
    }

def calculate_corpus_values(switch_date):
    """
    Calculate benchmark and individual corpus values.
    
    Args:
        switch_date (date): The date when the UPS scheme was implemented
        
    Returns:
        tuple: (benchmark_corpus, individual_corpus)
    """
    global overall_table, pension_fund_nav_rate
    
    benchmark_corpus = 0
    individual_corpus = 0

    # Calculate corpus values up to switch date
    for entry in overall_table:
        entry_date = date(entry["year"], entry["month"], 1)
        if entry_date <= switch_date:
            monthly_contribution = entry["monthly_salary"] * 0.2  # 10% employee + 10% government
            benchmark_corpus += monthly_contribution
            benchmark_corpus *= (1 + pension_fund_nav_rate / 12)  # Grow at NAV rate
            individual_corpus = entry["nps_corpus"]  # Set individual corpus to NPS corpus value
            entry["benchmark_corpus"] = benchmark_corpus
            entry["individual_corpus"] = individual_corpus
        else:
            # After switch date, grow both corpus values
            monthly_contribution = entry["monthly_salary"] * 0.2
            individual_corpus += monthly_contribution
            benchmark_corpus += monthly_contribution
            
            individual_corpus *= (1 + pension_fund_nav_rate / 12)
            benchmark_corpus *= (1 + pension_fund_nav_rate / 12)
            
            entry["benchmark_corpus"] = benchmark_corpus
            entry["individual_corpus"] = individual_corpus
            
    return benchmark_corpus, individual_corpus

def calculate_lumpsum_and_pension(withdrawal_percentage, benchmark_corpus, individual_corpus, assured_payout, has_minimum_service):
    """
    Calculate lumpsum withdrawal amount and adjusted pension based on the UPS rules.
    
    Args:
        withdrawal_percentage (float): Percentage of corpus for lumpsum withdrawal (0 to 0.6)
        benchmark_corpus (float): Benchmark corpus value
        individual_corpus (float): Individual's corpus value
        assured_payout (float): Original assured payout before adjustment
        has_minimum_service (bool): Whether subscriber has minimum service required
        
    Returns:
        tuple: (lumpsum_withdrawal, excess_corpus, adjusted_pension)
    """
    global MIN_UPS_PAYOUT
    
    # Cap withdrawal percentage at 60%
    actual_withdrawal_percentage = min(withdrawal_percentage, 0.6)
    
    # Calculate excess amount in individual corpus
    excess_corpus = max(0, individual_corpus - benchmark_corpus)
    
    # Calculate lumpsum withdrawal amount based on benchmark corpus
    applicable_corpus = min(benchmark_corpus, individual_corpus)
    lumpsum_withdrawal = applicable_corpus * actual_withdrawal_percentage
    
    # Calculate adjusted pension with proportionate reduction
    adjusted_pension = assured_payout * (1 - actual_withdrawal_percentage)
    
    # Apply minimum pension if eligible
    if has_minimum_service and adjusted_pension < MIN_UPS_PAYOUT:
        adjusted_pension = MIN_UPS_PAYOUT
    
    return lumpsum_withdrawal, excess_corpus, adjusted_pension

def calculate_ups_corpus_and_pension(death_year, retirement_date, spouse_age_difference):
    """
    Master function to calculate UPS corpus and pension based on the scenario.
    
    Args:
        death_year (int): Year of death
        retirement_date (date or int): Date of retirement
        spouse_age_difference (int): Years spouse is expected to live after employee
        
    Returns:
        tuple: (inflation_adjusted_corpus, nominal_corpus, monthly_pension, lump_sum)
    """
    global overall_table, normal_retirement_age, retirement_age
    
    # Handle case where retirement_date is an integer
    if isinstance(retirement_date, int):
        retirement_year = retirement_date
        retirement_month = 1
        retirement_date = date(retirement_year, retirement_month, 1)
    elif retirement_date is None:
        if overall_table:
            last_entry = overall_table[-1]
            retirement_date = date(last_entry["year"], last_entry["month"], 1)
        else:
            return 0, 0, 0, 0
    
    # Initialize UPS values
    ups_values = initialize_ups_values(retirement_date, switch_date=date(2025, 4, 1))
    if not ups_values:
        return 0, 0, 0, 0
    
    # Determine scenario: pre-retirement death, VRS, or post-retirement death
    death_month = 12  # Assume death in December for simplicity
    is_pre_retirement = death_year < retirement_date.year or (death_year == retirement_date.year and death_month < retirement_date.month)
    
    if is_pre_retirement:
        return calculate_pre_retirement_benefits(death_year, retirement_date, spouse_age_difference, ups_values)
    
    is_vrs = retirement_age < normal_retirement_age
    if is_vrs:
        return calculate_vrs_benefits(death_year, retirement_date, spouse_age_difference, ups_values)
    
    return calculate_post_retirement_benefits(death_year, retirement_date, spouse_age_difference, ups_values)

def calculate_pre_retirement_benefits(death_year, retirement_date, spouse_age_difference, ups_values):
    """
    Calculate benefits for pre-retirement death scenario.
    
    Args:
        death_year (int): Year of death
        retirement_date (date): Date of retirement
        spouse_age_difference (int): Years spouse is expected to live after employee
        ups_values (dict): Pre-calculated UPS values
        
    Returns:
        tuple: (inflation_adjusted_corpus, nominal_corpus, monthly_pension, lump_sum)
    """
    global overall_table, inflation_rate, MIN_UPS_PAYOUT
    
    death_month = 12  # Assume death in December
    
    # Calculate average salary for last 12 months before death
    pre_death_entries = [e for e in overall_table if 
                       (e["year"] < death_year) or 
                       (e["year"] == death_year and e["month"] <= death_month)]
    
    if not pre_death_entries:
        return 0, 0, 0, 0
    
    last_12_months = pre_death_entries[-12:] if len(pre_death_entries) >= 12 else pre_death_entries
    avg_last_12_months_salary = sum(e["monthly_salary"] for e in last_12_months) / len(last_12_months)
    
    # Calculate service months until death
    first_entry = overall_table[0]
    first_date = date(first_entry["year"], first_entry["month"], 1)
    service_months = (death_year - first_date.year) * 12 + death_month - first_date.month
    
    # Calculate potential pension if retired on death date
    pension_percentage = min(service_months / 300, 1)
    
    # Get corpus values at death date
    death_entry = next((e for e in overall_table if 
                      e["year"] == death_year and e["month"] >= death_month), 
                     next((e for e in overall_table if e["year"] > death_year), None))
    
    benchmark_corpus = death_entry.get("benchmark_corpus", 0) if death_entry else 0
    individual_corpus = death_entry.get("individual_corpus", death_entry.get("nps_corpus", 0)) if death_entry else 0
    
    corpus_ratio = min(individual_corpus / benchmark_corpus if benchmark_corpus > 0 else 0, 1)
    
    # Calculate potential pension and family pension (60%)
    potential_pension = (avg_last_12_months_salary / 2) * corpus_ratio * pension_percentage
    family_pension_monthly = potential_pension * 0.6
    
    # Apply minimum pension if eligible (10+ years service)
    if service_months >= 120 and family_pension_monthly < (MIN_UPS_PAYOUT * 0.6):
        family_pension_monthly = MIN_UPS_PAYOUT * 0.6
    
    # Calculate present value for spouse's pension
    corpus, nominal_corpus = calculate_spouse_pension_value(
        death_year, death_month, family_pension_monthly, spouse_age_difference, inflation_rate
    )
    
    # Calculate death gratuity and excess corpus
    excess_corpus = max(0, individual_corpus - benchmark_corpus)
    
    lump_sum = 0
    if service_months >= 60:  # 5+ years for gratuity
        gratuity = (1/10) * avg_last_12_months_salary * (service_months / 6)
        lump_sum = gratuity + excess_corpus
    
    corpus += lump_sum
    nominal_corpus += lump_sum
    
    return corpus, nominal_corpus, family_pension_monthly, lump_sum

def calculate_spouse_pension_value(start_year, start_month, monthly_pension, years_duration, inflation_rate):
    """
    Calculate present and nominal value of pension over a period of years.
    
    Args:
        start_year (int): Year pension starts
        start_month (int): Month pension starts (1-12)
        monthly_pension (float): Initial monthly pension amount
        years_duration (int): Duration in years
        inflation_rate (float): Annual inflation rate
        
    Returns:
        tuple: (present_value, nominal_value)
    """
    corpus = 0
    nominal_corpus = 0
    
    current_pension = monthly_pension
    
    for year_offset in range(years_duration + 1):
        year = start_year + year_offset
        
        # Apply annual DR (2%) after first year
        if year > start_year:
            current_pension *= 1.02
        
        annual_pension = current_pension * 12
        nominal_corpus += annual_pension
        
        # Calculate present value
        months_since_start = (year - start_year) * 12
        if year == start_year:
            months_since_start = 12 - start_month
        
        present_value = annual_pension / ((1 + (inflation_rate / 12)) ** months_since_start)
        corpus += present_value
    
    return corpus, nominal_corpus

def calculate_pension_for_year(initial_pension, base_year, current_year, pay_commission_interval, fitment_factor):
    """
    Calculate pension amount for a specific year considering pay commission updates and DR.
    
    Args:
        initial_pension (float): Initial pension amount
        base_year (int): Year when pension started
        current_year (int): Year for which to calculate pension
        pay_commission_interval (int): Years between pay commissions
        fitment_factor (float): Increase factor during pay commission
        
    Returns:
        float: Adjusted monthly pension
    """
    pension = initial_pension
    dr_year = 0
    
    for year in range(base_year, current_year + 1):
        # Check for pay commission updates
        is_pay_commission_year = False
        for pc_year in range(base_year, year + 1, pay_commission_interval):
            if year == pc_year and year > base_year:
                is_pay_commission_year = True
                break
        
        # Apply pay commission fitment factor
        if is_pay_commission_year:
            pension *= fitment_factor
            dr_year = 0  # Reset DR counter after pay commission
        
        # Apply Dearness Relief (DR)
        dr_rate = 0.02  # 2% DR per year
        if dr_year > 0:
            pension *= (1 + dr_rate)
        
        dr_year += 1
    
    return pension

def calculate_vrs_benefits(death_year, retirement_date, spouse_age_difference, ups_values):
    """
    Calculate benefits for VRS (Voluntary Retirement Scheme) scenario.
    
    Args:
        death_year (int): Year of death
        retirement_date (date): Date of retirement
        spouse_age_difference (int): Years spouse is expected to live after employee
        ups_values (dict): Pre-calculated UPS values
        
    Returns:
        tuple: (inflation_adjusted_corpus, nominal_corpus, monthly_pension, lump_sum)
    """
    global overall_table, inflation_rate, normal_retirement_age, retirement_age, pay_commission_interval, fitment_factor
    
    # Calculate normal retirement year
    years_to_normal_retirement = normal_retirement_age - retirement_age
    normal_retirement_year = retirement_date.year + int(years_to_normal_retirement)
    
    initial_pension = ups_values["adjusted_pension"]  # Use adjusted pension (after withdrawal)
    lump_sum = ups_values["lump_sum"]
    
    corpus = 0
    nominal_corpus = 0
    
    # Add pension benefits from normal retirement to death
    for year in range(max(normal_retirement_year, retirement_date.year), death_year + 1):
        # Calculate pension for the year
        pension = calculate_pension_for_year(
            initial_pension, 
            normal_retirement_year, 
            year, 
            pay_commission_interval, 
            fitment_factor
        )
        
        annual_pension = pension * 12
        nominal_corpus += annual_pension
        
        # Calculate present value
        months_since_retirement = (year - retirement_date.year) * 12
        if year == retirement_date.year:
            months_since_retirement = 12 - retirement_date.month
            
        present_value = annual_pension / ((1 + (inflation_rate / 12)) ** months_since_retirement)
        corpus += present_value
    
    # Add spouse's family pension (60%) for years after employee's death
    if death_year < retirement_date.year + spouse_age_difference:
        # Calculate pension at death
        pension_at_death = calculate_pension_for_year(
            initial_pension, 
            normal_retirement_year, 
            death_year, 
            pay_commission_interval, 
            fitment_factor
        )
        
        family_pension = pension_at_death * 0.6
        
        # Calculate remaining spouse years
        remaining_spouse_years = retirement_date.year + spouse_age_difference - death_year
        
        # Calculate spouse pension values
        spouse_corpus, spouse_nominal = calculate_spouse_pension_value(
            death_year, 12, family_pension, remaining_spouse_years, inflation_rate
        )
        
        corpus += spouse_corpus
        nominal_corpus += spouse_nominal
    
    # Add lump sum
    corpus += lump_sum
    nominal_corpus += lump_sum
    
    # Get monthly pension amount from normal retirement year (or death year if later)
    monthly_pension = calculate_pension_for_year(
        initial_pension, 
        normal_retirement_year, 
        max(normal_retirement_year, death_year), 
        pay_commission_interval, 
        fitment_factor
    )
    
    return corpus, nominal_corpus, monthly_pension, lump_sum

def calculate_post_retirement_benefits(death_year, retirement_date, spouse_age_difference, ups_values):
    """
    Calculate benefits for post-retirement death scenario.
    
    Args:
        death_year (int): Year of death
        retirement_date (date): Date of retirement
        spouse_age_difference (int): Years spouse is expected to live after employee
        ups_values (dict): Pre-calculated UPS values
        
    Returns:
        tuple: (inflation_adjusted_corpus, nominal_corpus, monthly_pension, lump_sum)
    """
    global overall_table, inflation_rate, pay_commission_interval, fitment_factor
    
    initial_pension = ups_values["adjusted_pension"]  # Use adjusted pension (after withdrawal)
    lump_sum = ups_values["lump_sum"]
    
    corpus = 0
    nominal_corpus = 0
    
    # Add pension benefits from retirement to death
    for year in range(retirement_date.year, death_year + 1):
        # Calculate pension for the year
        pension = calculate_pension_for_year(
            initial_pension, 
            retirement_date.year, 
            year, 
            pay_commission_interval, 
            fitment_factor
        )
        
        annual_pension = pension * 12
        nominal_corpus += annual_pension
        
        # Calculate present value
        months_since_retirement = (year - retirement_date.year) * 12
        if year == retirement_date.year:
            months_since_retirement = 12 - retirement_date.month
            
        present_value = annual_pension / ((1 + (inflation_rate / 12)) ** months_since_retirement)
        corpus += present_value
    
    # Add spouse's family pension (60%) for years after employee's death
    if death_year < retirement_date.year + spouse_age_difference:
        # Calculate pension at death
        pension_at_death = calculate_pension_for_year(
            initial_pension, 
            retirement_date.year, 
            death_year, 
            pay_commission_interval, 
            fitment_factor
        )
        
        family_pension = pension_at_death * 0.6
        
        # Calculate remaining spouse years
        remaining_spouse_years = retirement_date.year + spouse_age_difference - death_year
        
        # Calculate spouse pension values
        spouse_corpus, spouse_nominal = calculate_spouse_pension_value(
            death_year, 12, family_pension, remaining_spouse_years, inflation_rate
        )
        
        corpus += spouse_corpus
        nominal_corpus += spouse_nominal
    
    # Add lump sum
    corpus += lump_sum
    nominal_corpus += lump_sum
    
    # Get monthly pension at death
    monthly_pension = calculate_pension_for_year(
        initial_pension, 
        retirement_date.year, 
        death_year, 
        pay_commission_interval, 
        fitment_factor
    )
    
    return corpus, nominal_corpus, monthly_pension, lump_sum# ----------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------
def generate_mortality_comparison_table(
    retirement_age,
    fitment_factor,
    pay_commission_interval,
    annuity_rate,
    spouse_age_difference
):
    """
    Generate a comparison table for different death ages.
    Handles pre-retirement deaths, lumpsum withdrawal, and VRS scenarios.
    Spousal pension is now included in the corpus calculation.
    """
    global birth_year, birth_month, overall_table

    retirement_year = birth_year + retirement_age
    retirement_date = date(retirement_year, birth_month, 1)
    
    # Initialize the UPS values table if it hasn't been done yet
    table_data = []
    
    # Traverse death_year in reverse order
    join_date = date(overall_table[0]["year"], overall_table[0]["month"], 1)
    death_year_start = join_date.year + 10
    death_year_end = birth_year + 100

    for death_year in range(death_year_start, death_year_end, 1):
        # Calculate NPS values (they will be adjusted based on death age)
        monthly_pension_nps, lump_sum_nps, nps_corpus, nominal_nps_corpus = calculate_nps_pension_with_rop( 
            death_year,
            retirement_date, 
            annuity_rate
        )
        # Calculate UPS corpus and pension for this death year (including spousal pension)
        ups_corpus, nominal_ups_corpus, monthly_pension_ups, lump_sum_ups = calculate_ups_corpus_and_pension(
            death_year,
            retirement_date,
            spouse_age_difference
        )
        death_age = round(death_year - birth_year + (birth_month - 1) / 12)  # Round off death age
        table_data.append([
            death_age,
            monthly_pension_ups,  # Family pension
            monthly_pension_nps,  # NPS pension
            lump_sum_ups,  # Death gratuity
            lump_sum_nps,
            ups_corpus,  # Inflation-adjusted UPS corpus (now includes spousal pension)
            nps_corpus,  # Inflation-adjusted NPS value
            nominal_ups_corpus,  # Nominal UPS corpus (now includes spousal pension)
            nominal_nps_corpus  # Nominal NPS value
        ])
    return table_data

def generate_csv_file(headers, table_data, output_file):
    """
    Generate a CSV file from the given headers and table data.
    
    Parameters:
    - headers: List of column headers.
    - table_data: List of rows, where each row is a list of column values.
    - output_file: Path to the output CSV file.
    """
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)  # Write headers
        writer.writerows(table_data)  # Write rows
    print(f"CSV file saved to {output_file}")

def generate_markdown_table(headers, table_data, output_file):
    """
    Generate a Markdown table from the given headers and table data and save it to a file.
    
    Parameters:
    - headers: List of column headers.
    - table_data: List of rows, where each row is a list of column values.
    - output_file: Path to the output Markdown file.
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write headers
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("|" + " --- |" * len(headers) + "\n")
        
        # Write rows
        for row in table_data:
            f.write("| " + " | ".join(str(col) for col in row) + " |\n")
    print(f"Markdown table saved to {output_file}")

def generate_markdown_file(headers, table_data, salary_progression, inputs, summary, output_file):
    """
    Generate a Markdown file containing inputs, salary progression, a comparison table, and a summary.
    
    Parameters:
    - headers: List of column headers for the comparison table.
    - table_data: List of rows for the comparison table.
    - salary_progression: List of salary progression rows.
    - inputs: Dictionary of inputs and their values.
    - summary: List of tuples summarizing which system is better at different death ages.
    - output_file: Path to the output Markdown file.
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write inputs section
        f.write("# Monthly-Based Corpus Comparison (UPS vs NPS with RoP Annuity)\n\n")
        f.write("## Inputs\n\n")
        for key, value in inputs.items():
            f.write(f"- **{key}**: {value}\n")
        f.write("\n---\n\n")

        # Write salary progression section
        f.write("## Salary Progression\n\n")
        f.write("| Year | Month | Pay Level | Basic Pay (₹) | Monthly Salary (₹) | NPS Corpus (₹) |\n")
        f.write("|------|-------|-----------|----------------|---------------------|-----------------|\n")
        for row in salary_progression:
            f.write(f"| {row['year']} | {row['month']} | Level {row['pay_level']} | ₹ {row['basic_pay']:.2f} | ₹ {row['monthly_salary']:.2f} | ₹ {row['nps_corpus']:.2f} |\n")
        f.write("\n---\n\n")

        # Write comparison table section
        f.write("## NPS vs UPS Comparison Across Different Death Ages\n\n")
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("|" + " --- |" * len(headers) + "\n")
        for row in table_data:
            f.write("| " + " | ".join(str(col) for col in row) + " |\n")
        f.write("\n---\n\n")

        # Write summary section
        f.write("## Summary: Which System Is Better at Different Death Ages\n\n")
        if summary:
            for age, system, ups_value, nps_value in summary:
                f.write(f"- From age **{age}**: **{system}** is better\n")
                f.write(f"  - UPS Value: ₹ {ups_value:,.2f}\n")
                f.write(f"  - NPS Value: ₹ {nps_value:,.2f}\n")
                f.write(f"  - Difference: ₹ {abs(ups_value - nps_value):,.2f}\n\n")
        else:
            f.write("No data available for comparison.\n")
        f.write("\n---\n\n")
    print(f"Markdown file saved to {output_file}")

def main():
    global withdrawal_percentage  # Declare global variable
    global ups_values_table, overall_table
    global normal_retirement_age, inflation_rate, fitment_factor, retirement_age
    global MIN_UPS_PAYOUT
    global pension_fund_nav_rate
    global spouse_age_difference
    global death_age
    global retirement_month
    global retirement_year
    global retirement_date
    global death_year
    global death_month
    """
    Main function to calculate and compare UPS and NPS benefits.
    Collects user inputs, calculates salary progression, and displays results.
    """
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
    
    # Ask about actual retirement age (could be less for VRS)
    retirement_age_input = input(f"Enter actual retirement age (default: {normal_retirement_age}, less than {normal_retirement_age} for VRS): ")
    retirement_age = int(retirement_age_input) if retirement_age_input else normal_retirement_age
    
    # Calculate if this is a VRS case
    is_vrs = retirement_age < normal_retirement_age
    
    retirement_month = birth_month  # Retirement occurs on the last day of the birth month
    retirement_year = birth_year + retirement_age
    retirement_date = date(retirement_year, retirement_month, 1)
    
    # Calculate and check service length at retirement
    service_months_at_retirement = (retirement_year - year_of_joining) * 12 + (retirement_month - month_of_joining)
    if is_vrs and service_months_at_retirement < 25 * 12:
        print(f"WARNING: Voluntary retirement requires a minimum of 25 years of qualifying service.")
        print(f"The officer will have only {service_months_at_retirement / 12:.1f} years of service at the retirement age of {retirement_age}.")
        proceed = input("Do you want to continue anyway? (y/n): ")
        if proceed.lower() != 'y':
            print("Exiting program.")
            return
    
    death_age = int(input("Enter death age (default: 75): ") or 75)
    death_year = birth_year + death_age  # Calculate death year
    death_month = birth_month  # Use birth month for consistency

    # Get fitment factor
    fitment_factor_input = input("Enter fitment factor or press Enter to calculate using Ackroyd's formula (default inflation: 5%, COLA: 20%): ").strip()
    if fitment_factor_input:
        fitment_factor = float(fitment_factor_input)
        inflation_rate = float(input("Enter inflation rate (default: 0.05 for 5%): ") or 0.05)
    else:
        cost_of_living_adjustment = 0.2  # Default COLA
        fitment_factor = calculate_fitment_factor(cost_of_living_adjustment)

    print(f"Calculated Fitment Factor: {fitment_factor}")

    # NPS return rates
    equity_return = float(input("Enter annual equity return rate (default: 0.12 for 12%): ") or 0.12)
    corporate_bond_return = float(input("Enter annual corporate bond return rate (default: 0.08 for 8%): ") or 0.08)
    gsec_return = float(input("Enter annual G-Sec return rate (default: 0.06 for 6%): ") or 0.06)
    
    # Ask for desired annuity and lumpsum withdrawal percentages with default of 0
    withdrawal_percentage_input = input("Enter desired annuity and lumpsum withdrawal percentage (0-60%, default: 0%): ") or "0"
    withdrawal_percentage = min(float(withdrawal_percentage_input) / 100, 0.6)  # Convert percentage to decimal and cap at 60%
    if withdrawal_percentage < 0:
        withdrawal_percentage = 0
    elif withdrawal_percentage > 0.6:
        withdrawal_percentage = 0.6
    print(f"Annuity percentage set to: {withdrawal_percentage * 100}%")
    print(f"UPS lumpsum withdrawal percentage set to: {withdrawal_percentage * 100}%")
    
    # NPS annuity parameters (rate)
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
    spouse_age_difference = int(input("Enter the age difference between spouse's death and employee's death (negative values allowed, default: 10): ") or 10)

    # Set locale for currency formatting
    try:
        locale.setlocale(locale.LC_ALL, 'en_IN.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'en_IN')
        except:
            locale.setlocale(locale.LC_ALL, '')  # Use system default if Indian locale not available

    # Ensure UTF-8 encoding for output
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

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
        if current_date.month == JULY and (last_increment_date is None or current_date.year > last_increment_date.year):
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
            "nps_corpus": 0,  # Initialize, will be updated by calculate_nps_corpus
            "individual_corpus": 0,  # Initialize, will be updated by calculate_nps_corpus
            "benchmark_corpus": 0  # Initialize, will be updated by calculate_nps_corpus
        })
        
        # Move to the next month
        if current_date.month == 12:
            current_date = date(current_date.year + 1, 1, 1)
        else:
            current_date = date(current_date.year, current_date.month + 1, 1)

    # Calculate NPS corpus and update the overall_table with monthly NPS corpus values
    initialize_nps_corpus(
        equity_return, 
        corporate_bond_return, 
        gsec_return, 
        life_cycle_fund=life_cycle_fund  # Pass selected life cycle fund
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
    print("\n--- End of Salary Progression ---")
    # Generate mortality comparison table with updated parameters
    print("\n--- NPS vs UPS Comparison Across Different Death Ages ---")
    print("(Including Pre-Retirement Death Benefits)")
    
    mortality_table = generate_mortality_comparison_table(
        retirement_age,
        fitment_factor,
        pay_commission_interval,
        annuity_rate,
        spouse_age_difference,
    )
    
    # Format table headers and data for display
    headers = [
        "Death Age",
        "UPS Monthly Pension",
        "NPS Monthly Pension",
        "UPS Lump Sum",
        "NPS Lump Sum",
        "UPS Total Corpus (Inflation-Adjusted)",
        "NPS Total Value (Inflation-Adjusted)",
        "UPS Total Corpus (Nominal)",
        "NPS Total Value (Nominal)"
    ]

    # Format currency values in the table
    formatted_table = []
    for row in mortality_table:
        formatted_row = [
            row[0],  # Death Age (no formatting)
            locale.currency(round(row[1]), grouping=True),  # UPS Monthly Pension
            locale.currency(round(row[2]), grouping=True),  # NPS Monthly Pension
            locale.currency(round(row[3]), grouping=True),  # UPS Lump Sum
            locale.currency(round(row[4]), grouping=True),  # NPS Lump Sum
            locale.currency(round(row[5]), grouping=True),  # UPS Total Corpus (Inflation-Adjusted)
            locale.currency(round(row[6]), grouping=True),  # NPS Total Value (Inflation-Adjusted)
            locale.currency(round(row[7]), grouping=True),   # UPS Total Corpus (Nominal)
            locale.currency(round(row[8]), grouping=True)  # NPS Total Value (Nominal)

        ]
        formatted_table.append(formatted_row)
    
    # Display the table in the terminal using tabulate
    print("\n--- NPS vs UPS Comparison Table ---")
    print(tabulate(formatted_table, headers=headers, tablefmt="grid"))

    # Save the table as a CSV file
    csv_output_file = "demo_run.csv"
    generate_csv_file(headers, mortality_table, csv_output_file)
    # Collect inputs for the Markdown file
    inputs = {
        "Birth Year": birth_year,
        "Birth Month": birth_month,
        "Year of Joining": year_of_joining,
        "Month of Joining": month_of_joining,
        "Seniority Year": seniority_year,
        "Seniority Month": seniority_month,
        "Normal Retirement Age": normal_retirement_age,
        "Actual Retirement Age": retirement_age,
        "Death Age": death_age,
        "Fitment Factor": fitment_factor,
        "Inflation Rate": inflation_rate,
        "Equity Return Rate": equity_return,
        "Corporate Bond Return Rate": corporate_bond_return,
        "G-Sec Return Rate": gsec_return,
        "Annuity Withdrawal Percentage": f"{withdrawal_percentage * 100}%",
        "UPS Lump Sum Withdrawal Percentage": f"{withdrawal_percentage * 100}%",
        "Annuity Rate": annuity_rate,
        "Pay Commission Interval": pay_commission_interval,
        "Life Cycle Fund": life_cycle_fund,
        "Spouse Age Difference": spouse_age_difference
    }

    # Prepare salary progression for the Markdown file
    salary_progression = []
    for entry in displayed_entries:
        salary_progression.append({
            "year": entry["year"],
            "month": date(2000, entry["month"], 1).strftime('%b'),
            "pay_level": entry["pay_level"],
            "basic_pay": entry["basic_pay"],
            "monthly_salary": entry["monthly_salary"],
            "nps_corpus": entry["nps_corpus"]
        })

    # Create a summary of which system is better at different death ages
    print("\n--- Summary: Which System Is Better at Different Death Ages ---")
    
    # Add explanation of VRS pension start delay if applicable
    if is_vrs:
        normal_retirement_year = retirement_year + (normal_retirement_age - retirement_age)
        print(f"Note: For VRS cases, UPS pension starts only from year {normal_retirement_year} (normal retirement age)")
        print(f"This delay is factored into all calculations\n")
    
    better_system_changes = []
    prev_better = None
    
    for row in mortality_table:
        death_age = row[0]
        ups_value = row[5]
        nps_value = row[6]
        
        # Ignore if both NPS and UPS values are 0
        if ups_value == 0 and nps_value == 0:
            continue
        
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
            print(f"  Difference: {locale.currency(diff, grouping=True)}")
            print("")
    else:
        print("No data available for comparison")

    # Save the table as a Markdown file
    output_file = "demo_run.md"
    generate_markdown_file(headers, formatted_table, salary_progression, inputs, better_system_changes, output_file)

if __name__ == "__main__":
    main()
