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

def calculate_nps_pension_with_rop(nps_corpus, withdrawal_percentage, annuity_rate=0.06):
    """
    Calculate the NPS pension based on the final corpus and annuity plan with Return of Purchase Price.
    
    Parameters:
    - nps_corpus: The final NPS corpus at retirement
    - withdrawal_percentage: Percentage of corpus withdrawn (default: 0%)
    - annuity_rate: Annual annuity rate for Return of Purchase Price plan (default: 6%)
    
    Returns:
    - monthly_pension: Monthly pension amount
    - lump_sum: Lump sum amount available at retirement (60% of corpus)
    - rop_value: The purchase price that will be returned to nominees upon death
    """
    annuity_corpus = nps_corpus * (1-withdrawal_percentage)
    # Calculate the lump sum amount by applying the withdrawal percentage to the total NPS corpus
    lump_sum = nps_corpus * withdrawal_percentage
    
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
    retirement_age,
    lumpsum_withdrawal_percentage,
    is_vrs=False,
    normal_retirement_age=60,
    switch_date=date(2025, 4, 1),
    pension_fund_nav_rate=0.08
):
    """
    Initialize the UPS values table with basic information for each year after retirement.
    Includes lumpsum withdrawal option and support for VRS (voluntary retirement scheme).
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
    
    # Check if service is at least 10 years (120 months)
    has_minimum_service = service_months >= 120  # At least 10 years of service
    
    # Check if eligible for VRS (Voluntary Retirement Scheme)
    # VRS can only occur after the officer has attained the age of 50 or completed 30 years of qualifying service
    vrs_eligible = (service_months >= 30 * 12) or (retirement_age >= 50)  # Updated VRS eligibility condition
    
    # Initialize benchmark corpus to start from 0
    benchmark_corpus = 0

    # Grow benchmark corpus before the switch date
    # Contributions to the benchmark corpus are calculated based on monthly salary progression
    for entry in overall_table:
        if entry["year"] < switch_date.year or (entry["year"] == switch_date.year and entry["month"] <= switch_date.month):
            monthly_contribution = entry["monthly_salary"] * 0.2  # 10% employee + 10% government
            benchmark_corpus += monthly_contribution  # Add monthly contributions to the benchmark corpus
            benchmark_corpus *= (1 + pension_fund_nav_rate / 12)  # Grow benchmark corpus at NAV rate
            entry["benchmark_corpus"] = benchmark_corpus  # Store the benchmark corpus in the entry

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
            entry["benchmark_corpus"] = benchmark_corpus  # Store the benchmark corpus in the entry
            entry["individual_corpus"] = individual_corpus
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
        entry["benchmark_corpus"] = benchmark_corpus  # Store the benchmark corpus in the entry
        entry["individual_corpus"] = individual_corpus

    # Calculate initial pension
    # The pension is based on the ratio of individual corpus to benchmark corpus, capped at 1
    pension_percentage = min(service_months / 300, 1)  # Cap service months at 25 years (300 months)
    corpus_ratio = min(individual_corpus / benchmark_corpus, 1)  # Upper cap at 1, no lower cap
    
    # Apply lumpsum withdrawal reduction to pension if requested
    # Determine withdrawal amount first (limited to 60% of individual corpus or benchmark corpus, whichever is lower)
    max_withdrawal_corpus = min(individual_corpus, benchmark_corpus)
    lumpsum_withdrawal_amount = max_withdrawal_corpus * min(lumpsum_withdrawal_percentage, 0.6)  # Cap at 60%
    
    # Calculate pension with reduction due to lumpsum withdrawal
    # Admissible Payout = Assured payout x (1-LW%)
    pension_reduction_factor = 1 - (lumpsum_withdrawal_amount / max_withdrawal_corpus)
    initial_pension = (avg_last_12_months_salary / 2) * corpus_ratio * pension_percentage * pension_reduction_factor
    
    # Apply minimum pension amount of ₹10,000 if applicable for 10+ years of service
    if has_minimum_service and initial_pension < MIN_UPS_PAYOUT:
        initial_pension = MIN_UPS_PAYOUT
    
    # Lump sum calculation (gratuity + potential excess corpus withdrawal)
    lump_sum = 0
    if service_months >= 60:  # Only if 5 years of service are completed (for gratuity)
        qualifying_service_months = service_months
        # Death gratuity calculation
        gratuity = (1 / 10) * avg_last_12_months_salary * (qualifying_service_months / 6)
        lump_sum += gratuity
        
        # Add the positive difference between individual_corpus and benchmark_corpus 
        if individual_corpus > benchmark_corpus:
            lump_sum += (individual_corpus - benchmark_corpus)
    
    # Add the requested lumpsum withdrawal amount
    lump_sum += lumpsum_withdrawal_amount
    
    # For VRS, we need to calculate the normal retirement date
    vrs_mode = is_vrs or (retirement_age < normal_retirement_age and vrs_eligible)
    
    # If VRS, store the normal retirement date
    if vrs_mode:
        normal_retirement_year = retirement_date.year + (normal_retirement_age - retirement_age)
        normal_retirement_date = date(normal_retirement_year, retirement_date.month, retirement_date.day)
    else:
        normal_retirement_date = None
    
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
        dr_rate = 0.02  # 2% DR
        adjusted_pension = current_pension * (1 + dr_rate)
        
        # For VRS case, pension starts only at normal retirement age
        monthly_pension_to_use = 0
        if not vrs_mode or (normal_retirement_date and year >= normal_retirement_date.year):
            monthly_pension_to_use = adjusted_pension
        else:
            monthly_pension_to_use = 0  # No pension before normal retirement age for VRS
        
        # Add entry to the table
        ups_values_table.append({
            "year": year,
            "death_age": year - (retirement_date.year - retirement_date.month / 12 + retirement_age),
            "monthly_pension": monthly_pension_to_use,  # Use 0 for years before normal retirement in VRS cases
            "annual_pension": monthly_pension_to_use * 12,
            "lump_sum": lump_sum if year == retirement_date.year else 0,  # Lump sum only in retirement year
            "present_value": 0,  # Will be calculated when we compute corpus for specific death ages
            "corpus": 0,         # Will be computed when a specific death age is requested
            "is_vrs": vrs_mode,
            "normal_retirement_year": normal_retirement_date.year if normal_retirement_date else None
        })
        
        # For next year, still increment the pension amount even if not paying it yet
        current_pension = adjusted_pension

def calculate_ups_corpus_and_pension(
    death_year,
    inflation_rate, 
    retirement_date,
    spouse_age_difference
):
    """
    Calculate the UPS corpus and monthly pension using the pre-computed UPS values table.
    Returns the inflation-adjusted corpus, nominal corpus, monthly pension, and lump sum.
    For pre-retirement death, calculates family pension based on last 12 months' salary.
    Includes family pension calculation for spouse directly in the corpus calculation.
    Accounts for delayed pension start in VRS cases.
    """
    global ups_values_table, overall_table
    
    if not ups_values_table or not overall_table:
        return 0, 0, 0, 0
        
    # Handle the case where retirement_date is an integer (retirement year)
    if isinstance(retirement_date, int):
        retirement_year = retirement_date
        # Default to January of retirement year if only year is provided
        retirement_month = 1
        retirement_date = date(retirement_year, retirement_month, 1)
    elif retirement_date is None:
        # If retirement_date is None, find the last entry in overall_table
        if overall_table:
            last_entry = overall_table[-1]
            retirement_year = last_entry["year"]
            retirement_month = last_entry["month"]
            retirement_date = date(retirement_year, retirement_month, 1)
        else:
            return 0, 0, 0, 0
    
    death_month = 12  # Assuming death in December for simplicity
    
    # Check if this is a pre-retirement death
    is_pre_retirement = death_year < retirement_date.year or (death_year == retirement_date.year and death_month < retirement_date.month)
    # print(f"Death Year: {death_year}, Retirement Date: {retirement_date}, Pre-retirement: {is_pre_retirement}")
    
    # For pre-retirement death, we need to simulate what entries would be post-death
    # rather than filtering for actual post-retirement entries
    if is_pre_retirement:
        # For pre-retirement death, recalculate the average salary based on the last 12 months before death
        # Find the last 12 months of entries before death
        pre_death_entries = [e for e in overall_table if 
                           (e["year"] < death_year) or 
                           (e["year"] == death_year and e["month"] <= death_month)]
        
        # print(f"Number of pre-death entries: {len(pre_death_entries)}")
        
        # Calculate average of last 12 months' salary before death
        last_12_months = pre_death_entries[-12:] if len(pre_death_entries) >= 12 else pre_death_entries
        if not last_12_months:
            # print("No last 12 month entries found")
            return 0, 0, 0, 0
            
        avg_last_12_months_salary = sum(e["monthly_salary"] for e in last_12_months) / len(last_12_months)
        # print(f"Average last 12 months salary: {avg_last_12_months_salary}")
        
        # Calculate service months until death
        first_entry = overall_table[0]
        first_date = date(first_entry["year"], first_entry["month"], 1)
        service_months = (death_year - first_date.year) * 12 + death_month - first_date.month
        # print(f"Service months until death: {service_months}")
        
        # Calculate what pension would have been if retired on death date
        # Then apply 60% family pension
        pension_percentage = min(service_months / 300, 1)  # Cap service months at 25 years (300 months)
        
        # Get benchmark and individual corpus values as of death date
        benchmark_corpus = 0
        individual_corpus = 0
        
        # Use the last entry in overall_table before or at death date
        for entry in overall_table:
            if (entry["year"] < death_year) or (entry["year"] == death_year and entry["month"] <= death_month):
                benchmark_corpus = entry.get("benchmark_corpus", 0)
                individual_corpus = entry.get("nps_corpus", 0)
        
        corpus_ratio = min(individual_corpus / benchmark_corpus if benchmark_corpus > 0 else 0, 1)
        
        # Calculate what the pension would have been
        potential_pension = (avg_last_12_months_salary / 2) * corpus_ratio * pension_percentage
        
        # Family pension is 60% of what would have been the pension
        family_pension_monthly = potential_pension * 0.6
        
        # Apply minimum pension if applicable (service > 10 years)
        MIN_UPS_PAYOUT = 10000  # Define the constant if it's not already defined
        if service_months >= 120 and family_pension_monthly < (MIN_UPS_PAYOUT * 0.6):
            family_pension_monthly = MIN_UPS_PAYOUT * 0.6
                
        # Now we need to get or create entries for years AFTER death
        # For pre-retirement death, we need to construct our own relevant entries
        # as there won't be any entries in ups_values_table for years before retirement
        relevant_entries = []
        
        # Create entries for each year from death year to death year + 50 (or a reasonable upper limit)
        max_year = death_year + spouse_age_difference  # Adjust as needed
        current_pension = family_pension_monthly
        
        for year in range(death_year, max_year + 1):
            # Apply yearly increases (DR adjustments, fitment factors, etc.)
            # This is simplified; in reality you'd want to apply the same rules as in initialize_ups_values
            if year > death_year:
                current_pension *= 1.02  # Apply 2% DR as in the original code
            
            relevant_entries.append({
                "year": year,
                "monthly_pension": current_pension,
                "annual_pension": current_pension * 12,
                "lump_sum": 0,  # Will calculate separately
                "present_value": 0,  # Will calculate below
                "corpus": 0,  # Will calculate below
                "is_vrs": False
            })
    else:
        # For normal retirement or post-retirement death, use the existing entries
        relevant_entries = [e for e in ups_values_table 
                        if e["year"] >= retirement_date.year and e["year"] <= death_year]
        
        if not relevant_entries:
            print("No relevant entries found for post-retirement calculation")
            return 0, 0, 0, 0
    
    # Calculate spouse's death year
    spouse_death_year = death_year + spouse_age_difference
    
    # Calculate present value for each year's pension
    corpus = 0
    nominal_corpus = 0
    
    for entry in relevant_entries:
        # Calculate months since retirement for NPV
        if is_pre_retirement:
            # For pre-retirement death, calculate from death date
            months_since_death = (entry["year"] - death_year) * 12
            if entry["year"] == death_year:
                months_since_death = 12 - death_month
            
            # Use death as reference point
            discount_months = months_since_death
        else:
            # For post-retirement death, calculate from retirement date
            months_since_retirement = (entry["year"] - retirement_date.year) * 12
            if entry["year"] == retirement_date.year:
                months_since_retirement = 12 - retirement_date.month
            
            # Use retirement as reference point
            discount_months = months_since_retirement
        
        # For pre-retirement death, we already calculated family pension
        if is_pre_retirement:
            annual_pension_amount = entry["annual_pension"]  # Already contains family pension
        else:
            annual_pension_amount = entry["annual_pension"]
        
        # Discount the annual pension to present value
        present_value = annual_pension_amount / ((1 + (inflation_rate / 12)) ** discount_months)
        entry["present_value"] = present_value
        corpus += present_value
        # Add nominal value of annual pension
        nominal_corpus += annual_pension_amount
    
    # Add spouse's family pension (60% of the assured pension) for years after employee's death
    if spouse_death_year > death_year:
        # Get the family pension amount
        if is_pre_retirement:
            # Already calculated family pension for pre-retirement death
            family_pension_monthly_for_spouse = 0 
        else:
            # For post-retirement death, family pension is 60% of last pension
            last_entry = relevant_entries[-1]
            family_pension_monthly_for_spouse = last_entry["monthly_pension"] * 0.6
            
        family_pension_annual = family_pension_monthly_for_spouse * 12
        
        
        # Add spouse's pension to nominal corpus
        spouse_nominal_pension = family_pension_annual * spouse_age_difference
        nominal_corpus += spouse_nominal_pension
        
        # Calculate present value of spouse's pension for each year
        for year_offset in range(1, spouse_age_difference + 1):
            current_year = death_year + year_offset
            
            if is_pre_retirement:
                # For pre-retirement death, calculate from death date
                months_since_death = year_offset * 12
                discount_months = months_since_death
            else:
                # For post-retirement, calculate from retirement date
                months_since_retirement = (current_year - retirement_date.year) * 12
                if retirement_date.year == current_year:
                    months_since_retirement = 12 - retirement_date.month
                discount_months = months_since_retirement
            
            # Discount the annual family pension to present value
            year_present_value = family_pension_annual / ((1 + (inflation_rate / 12)) ** discount_months)
            corpus += year_present_value
    
    # Calculate death gratuity for pre-retirement death
    lump_sum = 0
    if is_pre_retirement:
        # For pre-retirement death, calculate death gratuity based on service
        first_entry = overall_table[0]
        first_date = date(first_entry["year"], first_entry["month"], 1)
        service_months = (death_year - first_date.year) * 12 + death_month - first_date.month
        
        if service_months >= 60:  # 5 years minimum for gratuity
            qualifying_service_months = service_months
            # Use avg_last_12_months_salary calculated earlier for pre-retirement death
            gratuity = (1 / 10) * avg_last_12_months_salary * (qualifying_service_months / 6)
            lump_sum += gratuity
            # print(f"Death gratuity: {gratuity}")
    else:
        # For post-retirement, use retirement year lump sum
        lump_sum = next((e["lump_sum"] for e in relevant_entries if e["year"] == retirement_date.year), 0)
    
    corpus += lump_sum
    nominal_corpus += lump_sum
    
    # Get the monthly pension amount
    if is_pre_retirement:
        monthly_pension = family_pension_monthly
    else:
        last_entry = relevant_entries[-1]
        monthly_pension = last_entry["monthly_pension"]
    
    # Update the corpus value in the table entries we used
    for entry in relevant_entries:
        entry["corpus"] = corpus
        entry["nominal_corpus"] = nominal_corpus
    
    # print(f"Final results - Corpus: {corpus}, Nominal: {nominal_corpus}, Monthly: {monthly_pension}, Lump sum: {lump_sum}")
    return corpus, nominal_corpus, monthly_pension, lump_sum

def generate_mortality_comparison_table(
    birth_year, 
    birth_month,
    retirement_age,
    inflation_rate,
    fitment_factor,
    pay_commission_interval,
    nps_corpus,
    withdrawal_percentage,
    annuity_rate,
    spouse_age_difference,
    lumpsum_withdrawal_percentage=0,
    is_vrs=False,
    normal_retirement_age=60
):
    """
    Generate a comparison table for different death ages.
    Handles pre-retirement deaths, lumpsum withdrawal, and VRS scenarios.
    Spousal pension is now included in the corpus calculation.
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
            retirement_age,
            lumpsum_withdrawal_percentage,
            is_vrs,
            normal_retirement_age
        )
    
    table_data = []
    
    # For each potential death year from join year plus 10 years to 60 years after birth
    join_date = date(overall_table[0]["year"], overall_table[0]["month"], 1)
    death_year_start = join_date.year + 10
    
    for death_year in range(death_year_start, birth_year + 101):
        # Use the month from birth_month for consistency
        death_month = birth_month
        
            # Calculate NPS values (they will be adjusted based on death age)
        monthly_pension_nps, lump_sum_nps, rop_value = calculate_nps_pension_with_rop(
            nps_corpus, 
            withdrawal_percentage=withdrawal_percentage, 
            annuity_rate=annuity_rate
        )

        # Calculate UPS corpus and pension for this death year (including spousal pension)
        ups_corpus, nominal_ups_corpus, monthly_pension_ups, lump_sum_ups = calculate_ups_corpus_and_pension(
            death_year,
            inflation_rate,
            retirement_date,
            spouse_age_difference
        )

        death_age = round(death_year - birth_year + (birth_month - 1) / 12)  # Round off death age
        is_pre_retirement = death_year < retirement_year or (death_year == retirement_year and death_month < retirement_date.month)
        
        # Initialize NPS values
        total_nps_value = 0
        total_nps_value_nominal = 0

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
                total_nps_value_nominal = nps_at_death
                pre_retirement_monthly_pension_nps = 0  # No pension before retirement
                lump_sum_nps = nps_at_death  # Entire corpus as lump sum
            else:
                total_nps_value = 0
                total_nps_value_nominal = 0
                pre_retirement_monthly_pension_nps = 0
                lump_sum_nps = 0
        else:
            # Post-retirement calculations
            # Calculate years receiving pension
            years_receiving_pension = death_year - retirement_year
            
            # Calculate total NPS value including pension received and return of purchase price
            total_nps_value_nominal = lump_sum_nps + (monthly_pension_nps * 12 * years_receiving_pension) + rop_value

            # Calculate inflation-adjusted NPS value
            # Use a more accurate inflation adjustment formula
            if years_receiving_pension > 0:
                inflation_factor = (1 - (1 / (1 + inflation_rate) ** years_receiving_pension)) / inflation_rate * (1+inflation_rate)
                discounted_rop = rop_value / ((1 + inflation_rate) ** years_receiving_pension)
                total_nps_value = lump_sum_nps + (monthly_pension_nps * 12 * inflation_factor) + discounted_rop
            else:
                total_nps_value = lump_sum_nps + rop_value

        # Add row to table - include both nominal and inflation-adjusted values
        if is_pre_retirement:
            # For pre-retirement, ensure minimum pension is applied for 10+ years of service
            service_months = (death_year - join_date.year) * 12 + (death_month - join_date.month)
            if service_months >= 120 and monthly_pension_ups < MIN_UPS_PAYOUT * 0.6:  # 60% of minimum pension
                monthly_pension_ups = MIN_UPS_PAYOUT * 0.6  # Ensure minimum family pension
                
            table_data.append([
                death_age,
                monthly_pension_ups,  # Family pension
                pre_retirement_monthly_pension_nps,
                lump_sum_ups,  # Death gratuity
                lump_sum_nps,
                ups_corpus,  # Inflation-adjusted UPS corpus (now includes spousal pension)
                total_nps_value,  # Inflation-adjusted NPS value
                nominal_ups_corpus,  # Nominal UPS corpus (now includes spousal pension)
                total_nps_value_nominal  # Nominal NPS value
            ])
        else:
            table_data.append([
                death_age,
                monthly_pension_ups,
                monthly_pension_nps,
                lump_sum_ups,
                lump_sum_nps,
                ups_corpus,  # Inflation-adjusted UPS corpus (now includes spousal pension)
                total_nps_value,  # Inflation-adjusted NPS value
                nominal_ups_corpus,  # Nominal UPS corpus (now includes spousal pension)
                total_nps_value_nominal  # Nominal NPS value
            ])
    
    return table_data

def main():
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
    
    # Ask about normal retirement age (superannuation age)
    normal_retirement_age = int(input("Enter normal retirement age (superannuation age) (default: 60): ") or 60)
    
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
        inflation_rate = 0.05  # Default inflation rate
        cost_of_living_adjustment = 0.2  # Default COLA
        fitment_factor = calculate_fitment_factor(inflation_rate, cost_of_living_adjustment)

    print(f"Calculated Fitment Factor: {fitment_factor}")

    # NPS return rates
    equity_return = float(input("Enter annual equity return rate (default: 0.12 for 12%): ") or 0.12)
    corporate_bond_return = float(input("Enter annual corporate bond return rate (default: 0.08 for 8%): ") or 0.08)
    gsec_return = float(input("Enter annual G-Sec return rate (default: 0.06 for 6%): ") or 0.06)
    
    # Ask for desired annuity and lumpsum withdrawal percentages with default of 0
    withdrawal_percentage_input = input("Enter desired annuity and lumpsum withdrawal percentage (0-60%, default: 0%): ") or "0"
    withdrawal_percentage = min(float(withdrawal_percentage_input) / 100, 0.6)  # Convert percentage to decimal and cap at 60%
    lumpsum_withdrawal_percentage = withdrawal_percentage  # Set to the same value
    
    print(f"Annuity percentage set to: {withdrawal_percentage * 100}%")
    print(f"UPS lumpsum withdrawal percentage set to: {lumpsum_withdrawal_percentage * 100}%")
    
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
    nps_corpus = calculate_nps_corpus(
        equity_return, 
        corporate_bond_return, 
        gsec_return, 
        life_cycle_fund=life_cycle_fund  # Pass selected life cycle fund
    )
    
    # Calculate NPS pension with Return of Purchase Price
    monthly_pension, lump_sum, rop_value = calculate_nps_pension_with_rop(
        nps_corpus, 
        withdrawal_percentage, 
        annuity_rate=annuity_rate
    )
    
    # Initialize the UPS values table - now passing normal_retirement_age and is_vrs
    initialize_ups_values(
        retirement_date,
        inflation_rate,
        fitment_factor,
        pay_commission_interval,
        retirement_age,
        lumpsum_withdrawal_percentage,
        is_vrs=is_vrs,
        normal_retirement_age=normal_retirement_age
    )
    
    # Check if death is pre-retirement
    is_pre_retirement = death_year < retirement_year or (death_year == retirement_year and death_month < retirement_month)
    
    # Calculate UPS corpus for the input death year and month
    ups_corpus, nominal_ups_corpus, monthly_pension_ups, lump_sum_ups = calculate_ups_corpus_and_pension(
        death_year,
        inflation_rate, 
        retirement_date,
        spouse_age_difference
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
        print(f"Lump Sum at Retirement ({(withdrawal_percentage)*100:.0f}%): {locale.currency(lump_sum, grouping=True)}")
        print(f"Amount Used for Annuity ({(1-withdrawal_percentage)*100:.0f}%): {locale.currency(rop_value, grouping=True)}")
        print(f"Monthly NPS Pension (at {annuity_rate*100:.1f}% annuity rate): {locale.currency(monthly_pension, grouping=True)}")
        print(f"Return of Purchase Price on Death: {locale.currency(rop_value, grouping=True)}")
        
        # Display UPS details with VRS information if applicable
        print("\n--- UPS Details ---")
        if is_vrs:
            normal_retirement_year = retirement_year + (normal_retirement_age - retirement_age)
            print(f"VRS Case: Pension payments will start from year {normal_retirement_year} (normal retirement age)")
        
        print(f"Total UPS Corpus (Pension + Gratuity): {locale.currency(ups_corpus, grouping=True)}")
        print(f"UPS Monthly Pension: {locale.currency(monthly_pension_ups, grouping=True)}")
        print(f"UPS Lump Sum (Including withdrawal of {lumpsum_withdrawal_percentage*100:.1f}%): {locale.currency(lump_sum_ups, grouping=True)}")
        if lumpsum_withdrawal_percentage > 0:
            print(f"Note: UPS pension reduced by {lumpsum_withdrawal_percentage*100:.1f}% due to lumpsum withdrawal")
    
    # Generate mortality comparison table with updated parameters
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
        withdrawal_percentage,
        annuity_rate,
        spouse_age_difference,
        lumpsum_withdrawal_percentage,
        is_vrs=is_vrs,
        normal_retirement_age=normal_retirement_age
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
    
    # Display the table 
    try:
        if tabulate:
            print(tabulate(formatted_table, headers=headers, tablefmt="grid"))
        else:
            raise ImportError
    except ImportError:
        # Fallback if tabulate is not available
        print("|".join(headers))  # Print headers correctly
        print("-" * 120)
        for row in formatted_table:
            print("|".join(str(col) for col in row))
    
    # Create a summary of which system is better at different death ages
    print("\n--- Summary: Which System Is Better at Different Death Ages ---")
    
    # Add explanation of VRS pension start delay if applicable
    if is_vrs:
        normal_retirement_year = retirement_year + (normal_retirement_age - retirement_age)
        print(f"Note: For VRS cases, UPS pension starts only from year {normal_retirement_year} (normal retirement age)")
        print(f"      This delay is factored into all calculations\n")
    
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

if __name__ == "__main__":
    main()
