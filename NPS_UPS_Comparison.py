import numpy as np
import numpy_financial as npf  # Use numpy_financial for IRR calculation

# -------------------------------
# Global Constants and Pay Scales
# -------------------------------
PAY_SCALES = [
    {"level": 10, "basic_pay": 56100, "total_years": 4},  # Junior Time Scale
    {"level": 11, "basic_pay": 67700, "total_years": 5},  # Senior Time Scale
    {"level": 12, "basic_pay": 78800, "total_years": 4},  # Junior Administrative Grade
    {"level": 13, "basic_pay": 123100, "total_years": 1}, # Selection Grade
    {"level": 14, "basic_pay": 144200, "total_years": 4}, # Super Time Scale
    {"level": 15, "basic_pay": 182200, "total_years": 7}, # Senior Administrative Grade
    {"level": 16, "basic_pay": 205400, "total_years": 5}, # HAG Scale
    {"level": 17, "basic_pay": 225000, "total_years": 6}, # Apex Scale
    {"level": 18, "basic_pay": 250000, "total_years": 2}, # Cabinet Secretary
]

def calculate_nps_contribution_progression(joining_age, retirement_age, fitment_factor, joining_year, pay_commission_years, eol_years=0, death_age=None, employee_contribution_rate=0.1, government_contribution_rate_pre_2019=0.12, government_contribution_rate_post_2019=0.14):
    """
    Calculate yearly NPS contributions based on IAS pay scales.
    Handles Extraordinary Leave (EOL) with no pay for a specified number of years and stops progression if death occurs before retirement.
    Includes contributions from both the employee and the government.
    """
    nps_contributions = []
    current_age = joining_age + eol_years  # Adjust starting age to account for EOL years
    skipped_years = 0

    for scale in PAY_SCALES:
        for year in range(scale["total_years"]):
            if current_age >= retirement_age or (death_age and current_age >= death_age):
                break
            if skipped_years < eol_years:
                # Skip the year for EOL
                skipped_years += 1
                current_age += 1
                continue
            # Calculate monthly salary
            current_year = joining_year + (current_age - joining_age)
            if current_year in pay_commission_years:
                update_pay_scales_for_pay_commission(fitment_factor)
            monthly_salary = calculate_monthly_salary(scale["level"], year)
            # Determine government contribution rate based on the year
            government_contribution_rate = government_contribution_rate_post_2019 if current_year >= 2019 else government_contribution_rate_pre_2019
            # Calculate NPS contribution
            yearly_contribution = monthly_salary * 12 * (employee_contribution_rate + government_contribution_rate)
            nps_contributions.append({"age": current_age, "nps_contribution": yearly_contribution})
            current_age += 1

    return nps_contributions


def calculate_ups_corpus(salary_progression, inflation_rate, death_age, fitment_factor, spouse_benefit=True, pay_commission_interval=10, dearness_relief_rate=0.05):
    """
    Calculate the inflation-adjusted UPS corpus.
    If death occurs before retirement, the spouse receives 50% of the officer's pension as a benefit.
    Includes pay commissions applied at regular intervals post-retirement.
    Accounts for proportionate payout for lesser service.
    Adds Dearness Relief (DR) to the pension amount.
    """
    if not salary_progression or salary_progression[-1]["age"] >= death_age:
        return 0  # No UPS corpus if death occurs before retirement

    pension_percentage = 0.5  # 50% of last drawn salary
    last_drawn_salary = salary_progression[-1]["basic_pay"]
    corpus = 0

    # Calculate proportionate service years
    total_service_years = salary_progression[-1]["age"] - salary_progression[0]["age"]
    eligible_service_years = min(total_service_years, 25)  # Full pension for 25 years of service
    proportionate_factor = eligible_service_years / 25

    for age in range(salary_progression[-1]["age"] + 1, death_age + 1):
        # Apply fitment factor for pay commission years
        if (age - salary_progression[-1]["age"]) % pay_commission_interval == 0:
            last_drawn_salary *= fitment_factor
        # Add Dearness Relief (DR) to the pension
        pension = last_drawn_salary * pension_percentage * proportionate_factor * (1 + dearness_relief_rate)
        corpus += pension / ((1 + inflation_rate) ** (age - salary_progression[-1]["age"]))

    # If death occurs before retirement, calculate spouse benefits
    if spouse_benefit and salary_progression[-1]["age"] < death_age:
        spouse_pension_percentage = 0.5 * pension_percentage  # 50% of the officer's pension
        for age in range(death_age, death_age + 20):  # Assume spouse receives benefits for 20 years
            if (age - salary_progression[-1]["age"]) % pay_commission_interval == 0:
                last_drawn_salary *= fitment_factor
            # Add Dearness Relief (DR) to the spouse's pension
            pension = last_drawn_salary * spouse_pension_percentage * proportionate_factor * (1 + dearness_relief_rate)
            corpus += pension / ((1 + inflation_rate) ** (age - salary_progression[-1]["age"]))

    return corpus


def calculate_nps_contribution(basic_pay, employee_contribution_rate, government_contribution_rate):
    """
    Calculate the total NPS contribution for a given year.
    Includes contributions from both the employee and the government.
    """
    return basic_pay * (employee_contribution_rate + government_contribution_rate)


def calculate_nps_corpus(
    salary_progression, 
    employee_contribution_rate, 
    market_return_rate, 
    vrs_age, 
    death_age, 
    spouse_benefit=True, 
    inflation_rate=0.05, 
    bond_rate=0.07, 
    equity_rate=0.12, 
    pension_payout_rate=0.4
):
    """
    Calculate the NPS corpus based on contributions from the employee and the government, and market returns.
    If death occurs before retirement, the spouse receives the accumulated corpus as a lump sum.
    Adjusts the investment plan to a 50-50 split between bonds and equity.
    Accounts for 40% of the total corpus being used for pension payouts starting at the age of retirement.
    """
    corpus = 0
    government_contribution_rate_pre_2019 = 0.12  # 12% before 2019
    government_contribution_rate_post_2019 = 0.14  # 14% from 2019 onward

    for year in salary_progression:
        if year["age"] >= vrs_age or (death_age and year["age"] >= death_age):
            break
        # Determine government contribution rate based on the year
        if year["age"] < 2019 - (2023 - year["age"]):  # Before 2019
            government_contribution_rate = government_contribution_rate_pre_2019
        else:  # 2019 and after
            government_contribution_rate = government_contribution_rate_post_2019

        # Use the calculate_nps_contribution function
        yearly_contribution = calculate_nps_contribution(
            year["basic_pay"], employee_contribution_rate, government_contribution_rate
        )
        corpus = (corpus + yearly_contribution) * (1 + market_return_rate)

    # If death occurs before retirement, spouse receives the accumulated corpus
    if spouse_benefit and death_age and salary_progression[-1]["age"] < death_age:
        return corpus  # Spouse receives the full accumulated corpus as a lump sum

    # Adjust corpus for a 50-50 split between bonds and equity
    bond_corpus = corpus * 0.5 * (1 + bond_rate)
    equity_corpus = corpus * 0.5 * (1 + equity_rate)
    total_corpus = bond_corpus + equity_corpus

    # Calculate pension payout (40% of the total corpus)
    pension_corpus = total_corpus * pension_payout_rate
    lump_sum_corpus = total_corpus * (1 - pension_payout_rate)

    # Adjust pension payouts for inflation
    pension_payout = 0
    for age in range(vrs_age, death_age + 1):
        yearly_pension = pension_corpus * market_return_rate
        pension_payout += yearly_pension / ((1 + inflation_rate) ** (age - vrs_age))

    # Return the total corpus including lump sum and inflation-adjusted pension payouts
    return lump_sum_corpus + pension_payout


def calculate_irr(cash_flows):
    """
    Calculate the Internal Rate of Return (IRR) for a series of cash flows.
    """
    try:
        irr = npf.irr(cash_flows)
        return irr
    except Exception as e:
        print(f"Error calculating IRR: {e}")
        return None


def calculate_npv(cash_flows, discount_rate):
    """
    Calculate the Net Present Value (NPV) for a series of cash flows given a discount rate.
    """
    npv = sum(cf / ((1 + discount_rate) ** i) for i, cf in enumerate(cash_flows))
    return npv


def format_indian_currency(amount):
    """
    Format a number in the Indian numbering system (e.g., lakhs, crores).
    """
    if amount < 100000:
        return f"₹{amount:,.2f}"
    else:
        amount_str = f"{amount:,.2f}"
        parts = amount_str.split(",")
        if len(parts) > 2:
            return f"₹{parts[0]},{','.join(parts[1:])}"
        return f"₹{amount_str}"


def calculate_fitment_factor(base_year, current_year, inflation_rate, cost_of_living_adjustment=0.2):
    """
    Calculate the fitment factor using Ackroyd's formula and cost of living adjustments (COLA).
    The years elapsed is fixed to 10 years.
    """
    years_elapsed = 10  # Fixed to 10 years
    inflation_adjustment = (1 + inflation_rate) ** years_elapsed
    fitment_factor = inflation_adjustment + cost_of_living_adjustment
    return fitment_factor


def should_update_pay_scale(current_age, joining_age):
    """
    Determine if the pay scale should be updated based on the total years completed at previous levels.
    """
    total_years_completed = current_age - joining_age
    cumulative_years = 0
    for scale in PAY_SCALES:
        cumulative_years += scale["total_years"]
        if total_years_completed < cumulative_years:
            return scale
    # If all levels are completed, return the last scale
    print(f"All pay scales completed. Current age: {current_age}, Joining age: {joining_age}.")
    return PAY_SCALES[-1]  # Return the last scale if all levels are completed


# -------------------------------
# Salary and Contribution Functions
# -------------------------------
def calculate_monthly_salary(pay_scale_level, years_at_level):
    """
    Calculate the monthly salary for a given pay scale level and years at that level.
    Includes Dearness Allowance (DA) as 53% of the basic pay.
    """
    increment_rate = 0.03  # Fixed 3% annual increment
    pay_scale = next((scale for scale in PAY_SCALES if scale["level"] == pay_scale_level), None)
    if not pay_scale:
        raise ValueError(f"Invalid pay scale level: {pay_scale_level}")

    basic_pay = pay_scale["basic_pay"] * (1 + increment_rate) ** years_at_level
    salary = basic_pay + (0.53 * basic_pay)  # Add Dearness Allowance (DA)
    return salary


def update_pay_scales_for_pay_commission(fitment_factor):
    """
    Update all pay scale levels globally by applying the fitment factor.
    The new basic pay is the maximum of (basic pay * fitment factor) and (current salary * 1.5).
    Additionally, for higher pay scales, adjust the salary using (1.03) ** scale["total_years"].
    """
    for scale in PAY_SCALES:
        # Calculate the updated basic pay
        updated_basic_pay = max(
            scale["basic_pay"] * fitment_factor,
            scale["basic_pay"] * (1.03 ** scale["total_years"])
        )
        scale["basic_pay"] = updated_basic_pay


def calculate_nps_contribution(basic_pay, employee_contribution_rate, government_contribution_rate):
    """
    Calculate the total NPS contribution for a given year.
    Includes contributions from both the employee and the government.
    """
    return basic_pay * (employee_contribution_rate + government_contribution_rate)


# -------------------------------
# Corpus Calculation Functions
# -------------------------------
def calculate_nps_corpus(
    salary_progression, employee_contribution_rate, market_return_rate, vrs_age, death_age,
    spouse_benefit=True, inflation_rate=0.05, bond_rate=0.07, equity_rate=0.12, pension_payout_rate=0.4
):
    """
    Calculate the NPS corpus based on contributions from the employee and the government, and market returns.
    """
    corpus = 0
    government_contribution_rate_pre_2019 = 0.12
    government_contribution_rate_post_2019 = 0.14

    for year in salary_progression:
        if year["age"] >= vrs_age or (death_age and year["age"] >= death_age):
            break
        government_contribution_rate = (
            government_contribution_rate_post_2019 if year["age"] >= 2019 else government_contribution_rate_pre_2019
        )
        yearly_contribution = calculate_nps_contribution(
            year["basic_pay"], employee_contribution_rate, government_contribution_rate
        )
        corpus = (corpus + yearly_contribution) * (1 + market_return_rate)

    if spouse_benefit and death_age and salary_progression[-1]["age"] < death_age:
        return corpus  # Spouse receives the full accumulated corpus as a lump sum

    bond_corpus = corpus * 0.5 * (1 + bond_rate)
    equity_corpus = corpus * 0.5 * (1 + equity_rate)
    total_corpus = bond_corpus + equity_corpus

    pension_corpus = total_corpus * pension_payout_rate
    lump_sum_corpus = total_corpus * (1 - pension_payout_rate)

    pension_payout = 0
    for age in range(vrs_age, death_age + 1):
        yearly_pension = pension_corpus * market_return_rate
        pension_payout += yearly_pension / ((1 + inflation_rate) ** (age - vrs_age))

    return lump_sum_corpus + pension_payout


def calculate_ups_corpus(salary_progression, inflation_rate, death_age, fitment_factor, spouse_benefit=True, pay_commission_interval=10, dearness_relief_rate=0.05):
    """
    Calculate the inflation-adjusted UPS corpus.
    """
    if not salary_progression or salary_progression[-1]["age"] >= death_age:
        return 0

    pension_percentage = 0.5
    last_drawn_salary = salary_progression[-1]["basic_pay"]*12  # Monthly salary to annual salary
    corpus = 0

    total_service_years = salary_progression[-1]["age"] - salary_progression[0]["age"]
    eligible_service_years = min(total_service_years, 25)
    proportionate_factor = eligible_service_years / 25

    for age in range(salary_progression[-1]["age"] + 1, death_age + 1):
        if (age - salary_progression[-1]["age"]) % pay_commission_interval == 0:
            last_drawn_salary *= fitment_factor
        pension = last_drawn_salary * pension_percentage * proportionate_factor * (1 + dearness_relief_rate)
        corpus += pension / ((1 + inflation_rate) ** (age - salary_progression[-1]["age"]))

    if spouse_benefit and salary_progression[-1]["age"] < death_age:
        spouse_pension_percentage = 0.5 * pension_percentage
        for age in range(death_age, death_age + 20):
            if (age - salary_progression[-1]["age"]) % pay_commission_interval == 0:
                last_drawn_salary *= fitment_factor
            pension = last_drawn_salary * spouse_pension_percentage * proportionate_factor * (1 + dearness_relief_rate)
            corpus += pension / ((1 + inflation_rate) ** (age - salary_progression[-1]["age"]))

    return corpus


# -------------------------------
# Main Function
# -------------------------------
def main():
    print("Corpus Comparison (UPS vs NPS)")

    # Input variables with default values
    birth_year = int(input("Enter birth year of the officer (default: 1996): ") or 1996)
    year_of_joining = int(input("Enter year of joining the service (default: 2022): ") or 2022)
    joining_age = year_of_joining - birth_year
    retirement_age = int(input("Enter retirement age (default: 60): ") or 60)
    death_age = int(input("Enter death age (default: 75): ") or 75)
    if death_age < joining_age:
        print("Error: Death age cannot be less than joining age.")
        return

    use_ackroyd_formula = input("Do you want to calculate the fitment factor using Ackroyd's formula? (yes/no, default: yes): ").strip().lower() in ["", "yes"]
    if use_ackroyd_formula:
        inflation_rate = float(input("Enter the inflation rate (default: 0.05 for 5%): ") or 0.05)
        cost_of_living_adjustment = float(input("Enter the cost of living adjustment (default: 0.2 for 20%): ") or 0.2)
        fitment_factor = calculate_fitment_factor(None, None, inflation_rate, cost_of_living_adjustment)
    else:
        fitment_factor = float(input("Enter fitment factor (default: 1.6): ") or 1.6)

    increment_rate = 0.03  # Fixed 3% annual increment
    inflation_rate = float(input("Enter inflation rate (default: 0.05 for 5%): ") or 0.05)
    market_return_rate = float(input("Enter market return rate (default: 0.08 for 8%): ") or 0.08)
    bond_rate = 0.07  # Fixed bond rate for NPS corpus
    equity_rate = 0.12  # Fixed equity rate for NPS corpus
    pension_payout_rate = 0.4  # 40% of NPS corpus used for pension payouts

    # Contribution rates based on year of joining and current year
    employee_contribution_rate = 0.1  # 10%
    government_contribution_rate_pre_2019 = 0.12  # 12% before 2019
    government_contribution_rate_post_2019 = 0.14  # 14% from 2019 onward

    # Pay commission details
    pay_commission_interval = int(input("Enter pay commission interval in years (default: 10): ") or 10)
    seventh_pay_commission_year = 2016  # 7th Pay Commission year
    pay_commission_years = list(range(seventh_pay_commission_year, 2100, pay_commission_interval))

    # Default EOL to 1 year
    eol_years = int(input("Enter the number of years of Extraordinary Leave (EOL) with no pay (default: 1): ") or 1)

    # Initialize variables
    current_year = year_of_joining
    current_age = joining_age
    nps_corpus = 0
    salary_progression = []

    # Loop through each year until death age
    while current_age < retirement_age and (death_age is None or current_age < death_age):
        # Check if it's a pay commission year
        if current_year in pay_commission_years:
            update_pay_scales_for_pay_commission(fitment_factor)

        # Determine pay scale level and years at level
        pay_scale = should_update_pay_scale(current_age, joining_age)
        previous_years = sum(scale["total_years"] for scale in PAY_SCALES if scale["level"] < pay_scale["level"])
        years_at_level = current_age - joining_age - previous_years  # Subtract years at previous levels

        # Calculate monthly salary
        monthly_salary = calculate_monthly_salary(pay_scale["level"], years_at_level)
        yearly_salary = monthly_salary * 12
        salary_progression.append({"year": current_year, "age": current_age, "basic_pay": monthly_salary})

        # Calculate NPS contribution
        government_contribution_rate = government_contribution_rate_post_2019 if current_year >= 2019 else government_contribution_rate_pre_2019
        yearly_contribution = yearly_salary * (employee_contribution_rate + government_contribution_rate)
        nps_corpus = (nps_corpus + yearly_contribution) * (1 + market_return_rate)

        # Increment year and age
        current_year += 1
        current_age += 1

    # Calculate UPS corpus
    ups_corpus = calculate_ups_corpus(
        salary_progression, inflation_rate, death_age, fitment_factor, 
        pay_commission_interval=pay_commission_interval
    )

    # Display salary progression
    print("\n--- Salary Progression ---")
    for entry in salary_progression:
        print(f"Year: {entry['year']}, Age: {entry['age']}, Monthly Salary: {format_indian_currency(entry['basic_pay'])}")

    print(f"\nFinal UPS Corpus (Including Dearness Relief): {format_indian_currency(ups_corpus)}")
    print(f"\nFinal NPS Corpus (Including Returns): {format_indian_currency(nps_corpus)}")


if __name__ == "__main__":
    main()
