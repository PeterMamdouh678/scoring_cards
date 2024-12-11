import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz
from datetime import datetime, timedelta
from db_connect import merged_data
from rule_based import rule_check

def main():

    @st.cache_data
    def get_data():
        return merged_data()

    df = pd.DataFrame(get_data())
    # df = merged_data()
    # default = transactions()
    df.rename(columns={"totalamount_sum_x":"max_installment_amount"},inplace=True)
    df = df[100:]
    red_flags = pd.read_excel("red_flags.xlsx")

    negative_zones = red_flags[red_flags['NegativeZone'].notna()]['NegativeZone']
    negative_jobs = red_flags[red_flags['NegativeJob'].notna()]['NegativeJob']

    threshold = 85

    cars = pd.read_excel("cars.xlsx")
    cars['LastFiveYears'] = cars['LastFiveYears'].apply(lambda x:int(str(x).split('K')[0]) * 1000 )
    cars['PlusFiveYears'] = cars['PlusFiveYears'].apply(lambda x:int(str(x).split('K')[0]) * 1000 )

    clubs = pd.read_excel("clubs.xlsx")
    # clubs['PostAmanLimit2'] = clubs['PostAmanLimit2'].apply(lambda x:int(str(x).split('K')[0]) * 1000 )
    clubs['PostAmanLimit2'] = clubs['PostAmanLimit2'].apply(
        lambda x: int(str(x).split('K')[0]) * 1000 if pd.notna(x) and str(x) != '0' else 0
    )

    # Define weights and score mappings for the credit assessment
    weights = {
        "Age": 1.0,
        "Marital Status": 0.5,
        "Family Dependents": 0.5,
        "Education": 1.0,
        "Employment Age": 1.0,
        "Job Position": 1.5,
        "Income Level": 2.0,
        "I-Score": 3.0,
        "Credit History Length": 1.5,
        "Debt Levels": 2.0,
        "Payment History": 3.0,
        "Residence Stability": 0.5,
        "Asset Ownership": 1.0,
        "Type of Employment": 1.0,
        "Industry Type": 1.0,
        "Spending Patterns": 1.5,
        "collateral":1,
        "type_collateral":1
    }

    score_mapping = {
        "Income Level": {"<2k": 0, "2-6k": 1, "6-10k": 2, "10-20k": 3, "20-50k": 4, "50k+": 5},
        "Debt Levels": {"High (>70%)": 1, "Medium (30-70%)": 3, "Low (<30%)": 5},
        "Age": {"<20 or >65": 1, "21-29": 3, "30-39": 4, "40-49": 5, "50-59": 4, "60+": 2},
        "Marital Status": {"Single": 5, "Married": 3, "Divorced": 2, "Widowed": 2},
        "Residence Stability": {"<1yr": 1, "1-3yrs": 2, "3-5yrs": 3, "5+yrs": 4},
        "Family Dependents": {"2+": 1, "2": 3, "1": 4, "0": 5},
        "Education": {"None": 0, "High School": 2, "University": 3, "Postgrad": 5},
        "Type of Employment": {"Permanent": 5, "Contract": 3, "Self-employed": 1, "Other": 0},
        "Employment Age": {"<6m": 0, "6m-1yr": 1, "1-2yr": 2, "2-5yr": 3, "5-10yr": 4, "10+yr": 5},
        "Job Position": {"Entry": 1, "Junior": 2, "Senior": 3, "Manager": 4, "Executive": 5},
        "I-Score": {"Poor": 1, "Fair": 2, "Good": 3, "Very Good": 4, "Excellent": 5},
        "Credit History Length": {"<1yr": 1, "1-3yrs": 2, "3-5yrs": 3, "5-10yrs": 4, "10+yrs": 5},
        "Payment History": {"0-50% on-time": 1, "51-80% on-time": 3, "81-100% on-time": 5},
        "type_collateral":{"Personal items":1,"Vehicles":3,"Club":3,"Real estate":5},
        "collateral":{">EGP 1,000,000":5, "EGP 500,000-1,000,000":4, "EGP 200,000-500,000":3, "EGP 100,000-200,000":2, "<EGP 100,000":1},
        "Industry Type": {"Stable (e.g., healthcare)": 5, "Moderate (e.g., retail)": 3, "Unstable (e.g., gig work)": 1},
        "Spending Patterns": {"High": 1, "Average": 3, "Conservative": 5},
        "Asset Ownership": {"No": 1, "Yes": 5}
    }
    #------------------------------------------------------------------------------------------
    # Fuzzy match club names 
    def is_fuzzy_match_club(name, input_clubs):
        threshold = 85
        return any(fuzz.ratio(name, club) >= threshold for club in input_clubs)

    # Fuzzy Match carbrand and model names
    def fuzzy_match_car(row,input_car):
        threshold = 85

        brand_match = fuzz.ratio(row['BrandNameEN'], input_car['CarBrand']) >= threshold
        model_match = fuzz.ratio(row['ModelNameEN'], input_car['CarModel']) >= threshold
        return brand_match and model_match
    #------------------------------------------------------------------------------------------
    # Function to map benchmarks to scores
    def get_score_from_benchmark(benchmark, optionss, inverse=False):
        score = optionss[benchmark]
        print("benchmark: ", benchmark, ' score: ', score)    
        # print("score: ", score)
        return 6 - score if inverse else score

    # Function to calculate weighted score
    def calculate_weighted_score(score, weight):
        return score * weight
    #------------------------------------------------------------------------------------------

    # print(df)
    # Streamlit application
    st.title("Maseera Credit Assessment Scorecard")

    # Financial Perspective
    st.write("### Search for a user")

    phone_numbers = df['api_phone_number'].unique()
    number = st.selectbox("Select a phone number:", phone_numbers)

    # number = st.text_input("Write the number of the user")

    # nid = st.text_input("Write the NID of the user")


    # print("Number : ", number)
    # Conditional Filtering
    if number:  # Trigger filtering only when `number` is not empty
        filtered_data = df[df['number'] == number].reset_index()
        if not filtered_data.empty:
            st.write("User Data:")
            st.dataframe(filtered_data)
    #     else:
    #         st.write("No matching data found.")
    # elif nid:
    #     filtered_data = df[df['ID Number'] == nid].reset_index()
    #     if not filtered_data.empty:
    #         st.write("Filtered Data:")
    #         st.dataframe(filtered_data)
    #     else:
    #         st.write("No matching data found.")
    else:
        st.write("Please enter a number or a NID to search.")
        filtered_data = df.reset_index()

    rules = st.button("check rules")
    if rules:
        true_group, false_group = rule_check(filtered_data)
        st.write("true_group")
        st.dataframe(true_group)
        st.write("false_group")
        st.dataframe(false_group) 

    st.divider()

    # Financial Perspective
    st.write("### Financial")
    # ======================================================
    income_weight = st.slider("Income Weight", 0, 10, 3)
    # income_options = list(score_mapping["Income Level"].keys())
    income_options = filtered_data['Total Income'][0]
    st.write("User income = ", income_options)
    # "Income Level": {"<2k": 0, "2-6k": 1, "6-10k": 2, "10-20k": 3, "20-50k": 4, "50k+": 5},
    if income_options < 2000:
        income_benchmark = "<2k"
    elif 2000 > income_options >= 6000:
        income_benchmark = "2-6k"
    elif 6000 > income_options >= 10000:
        income_benchmark = "6-10k"
    elif 10000 > income_options >= 20000:
        income_benchmark = "10-20k"
    elif 20000 > income_options >= 50000:
        income_benchmark = "20-50k"
    else:
        income_benchmark = "50k+"

    # income_benchmark = st.selectbox("Monthly Income Benchmark", income_options)
    # income_score = get_score_from_benchmark(income_benchmark, income_options)
    income_score = get_score_from_benchmark(income_benchmark, score_mapping["Income Level"])

    # stability_weight = st.slider("Stability of Income Weight", 0, 10, 5)
    # stability_options = list(score_mapping["Debt Levels"].keys())
    # stability_benchmark = st.selectbox("Stability of Income Source Benchmark", stability_options)
    # stability_score = get_score_from_benchmark(stability_benchmark, stability_options)
    st.divider()
    # ======================================================

    # Customer - Personal Information
    st.write("### Customer - Personal Information")

    job_weight = st.slider("job Weight", 0, 10, 3)
    # job = st.text_input("What is your job as in NID in arabic")
    if filtered_data['NID Occupation'][0] in []:
        job = filtered_data['NID Occupation'][0]
    else:
        job = 'Other'
    st.write("User job as in NID = ", job)
    # job_flag = process.extract(job, negative_zones)

    job_flag = negative_jobs.apply(lambda text: fuzz.partial_ratio(job, text) >= threshold).any()

    st.divider()
    # ======================================================

    location_weight = st.slider("location Weight", 0, 10, 3)
    # location = st.text_input("What is your location as in NID in arabic")
    location = filtered_data['NID Area'][0] 
    st.write("User Location as in NID = ", location)
    # location_flag = process.extract(location, negative_zones)
    location_flag = negative_zones.apply(lambda text: fuzz.partial_ratio(location, text) >= threshold).any()

    st.divider()
    # ======================================================

    age_weight = st.slider("Age Weight", 0, 10, 3)
    # age_options = list(score_mapping["Age"].keys())
    age_options = int(filtered_data['Age'][0])
    if age_options < 20 or age_options > 65:
        age_benchmark = "<20 or >65"
    elif 20 <= age_options <= 29: 
        age_benchmark = "21-29"
    elif 30 <= age_options <= 39: 
        age_benchmark = "30-39"
    elif 40 <= age_options <= 49: 
        age_benchmark = "40-49"
    elif 40 < age_options <= 59: 
        age_benchmark = "50-59"
    else:
        age_benchmark = "<20 or >65"

    st.write("User Age as in NID = ", age_options)
    # else:
    #     age_benchmark = "30-39"
    # age_benchmark = st.selectbox("Age Benchmark", age_options)
    # age_score = get_score_from_benchmark(age_benchmark, age_options)
    age_score = get_score_from_benchmark(age_benchmark, score_mapping["Age"])

    st.divider()
    # ======================================================

    marital_status_weight = st.slider("Marital Status Weight", 0, 10, 3)
    # marital_status_options = list(score_mapping["Marital Status"].keys())
    marital_status_options = filtered_data['Marital Status'][0] 
    # "Marital Status": {"Single": 1, "Married": 3, "Divorced": 2, "Widowed": 2},
    if marital_status_options == 'Single':
        marital_status_benchmark = 'Single'
    elif marital_status_options == "Married":
        marital_status_benchmark = "Married"
    elif marital_status_options == "Divorced":
        marital_status_benchmark = "Divorced"
    else:
        marital_status_benchmark = "Widowed"

    st.write("User Marital Status = ", marital_status_benchmark )
    # marital_status_benchmark = st.selectbox("Marital Status Benchmark", marital_status_options)
    # marital_status_score = get_score_from_benchmark(marital_status_benchmark, marital_status_options)
    marital_status_score = get_score_from_benchmark(marital_status_benchmark, score_mapping["Marital Status"])

    st.divider()
    # ======================================================

    residence_stability_weight = st.slider("Residence Stability Weight", 0, 10, 3)
    residence_stability_options = list(score_mapping["Residence Stability"].keys())
    residence_stability_benchmark = st.selectbox("Residence Stability Benchmark", residence_stability_options)
    # residence_stability_score = get_score_from_benchmark(residence_stability_benchmark, residence_stability_options)
    residence_stability_score = get_score_from_benchmark(residence_stability_benchmark, score_mapping["Residence Stability"])

    st.divider()
    # ======================================================

    family_dependents_weight = st.slider("Family Dependents Weight", 0, 10, 3)
    # family_dependents_options = list(score_mapping["Family Dependents"].keys())
    family_dependents_options = filtered_data['Number Of Dependents'][0] 
    #     "Family Dependents": {"2+": 1, "2": 3, "1": 4, "0": 5},
    family_dependents_benchmark = str(family_dependents_options)
    st.write(" Number of family dependents = ", family_dependents_benchmark)
    # family_dependents_benchmark = st.selectbox("Family Dependents Benchmark", family_dependents_options)
    # family_dependents_score = get_score_from_benchmark(family_dependents_benchmark, family_dependents_options)
    family_dependents_score = get_score_from_benchmark(family_dependents_benchmark, score_mapping["Family Dependents"])

    st.divider()
    # ======================================================

    education_weight = st.slider("Education Weight", 0, 10, 3)
    education_options = list(score_mapping["Education"].keys())
    education_benchmark = st.selectbox("Education Benchmark", education_options)
    # education_score = get_score_from_benchmark(education_benchmark, education_options)
    education_score = get_score_from_benchmark(education_benchmark, score_mapping["Education"])

    st.divider()
    # ======================================================

    employment_type_weight = st.slider("Type of Employment Weight", 0, 10, 3)
    # employment_type_options = list(score_mapping["Type of Employment"].keys())
    employment_type_options = filtered_data['employment_type'][0] 
    # "Type of Employment": {"Permanent": 5, "Contract": 3, "Self-employed": 1, "Other": 0},
    employment_type_benchmark = employment_type_options
    st.write("User Employment type = ", employment_type_benchmark)
    # employment_type_benchmark = st.selectbox("Type of Employment Benchmark", employment_type_options)
    # employment_type_score = get_score_from_benchmark(employment_type_benchmark, employment_type_options)
    employment_type_score = get_score_from_benchmark(employment_type_benchmark, score_mapping["Type of Employment"])

    st.divider()
    # ======================================================

    employment_age_weight = st.slider("Employment Age Weight", 0, 10, 3)
    employment_age_options = list(score_mapping["Employment Age"].keys())
    employment_age_benchmark = st.selectbox("Employment Age Benchmark", employment_age_options)
    # employment_age_score = get_score_from_benchmark(employment_age_benchmark, employment_age_options)
    employment_age_score = get_score_from_benchmark(employment_age_benchmark, score_mapping["Employment Age"])

    st.divider()
    # ======================================================

    job_position_weight = st.slider("Job Position Weight", 0, 10, 3)
    job_position_options = list(score_mapping["Job Position"].keys())
    job_position_benchmark = st.selectbox("Job Position Benchmark", job_position_options)
    # job_position_score = get_score_from_benchmark(job_position_benchmark, job_position_options)
    job_position_score = get_score_from_benchmark(job_position_benchmark, score_mapping["Job Position"])

    st.divider()
    # ======================================================

    st.write("### Internal Processes - Credit History")
    i_score_weight = st.slider("I-Score Weight", 0, 10, 3)
    i_score_options = list(score_mapping["I-Score"].keys())
    i_score_benchmark = st.selectbox("I-Score (Credit Score) Benchmark", i_score_options)
    # i_score_score = get_score_from_benchmark(i_score_benchmark, i_score_options)
    i_score_score = get_score_from_benchmark(i_score_benchmark, score_mapping["I-Score"])

    st.divider()
    # ======================================================

    credit_history_length_weight = st.slider("Credit History Length Weight", 0, 10, 3)
    credit_history_length_options = list(score_mapping["Credit History Length"].keys())
    credit_history_length_benchmark = st.selectbox("Credit History Length Benchmark", credit_history_length_options)
    # credit_history_length_score = get_score_from_benchmark(credit_history_length_benchmark, credit_history_length_options)
    credit_history_length_score = get_score_from_benchmark(credit_history_length_benchmark, score_mapping["Credit History Length"])

    st.divider()
    # ======================================================

    debt_levels_weight = st.slider("Debt Levels Weight", 0, 10, 3)
    # debt_levels_options = list(score_mapping["Debt Levels"].keys())
    debt_levels_options = filtered_data['debt_level'][0] 
    # "Debt Levels": {"High (>70%)": 1, "Medium (30-70%)": 3, "Low (<30%)": 5},
    if debt_levels_options < 30:
        debt_levels_benchmark = "Low (<30%)"
    elif  30 <= debt_levels_options < 70:
        debt_levels_benchmark = "Medium (30-70%)"
    elif debt_levels_options > 70:
        debt_levels_benchmark = "High (>70%)"
    else: debt_levels_benchmark = "Low (<30%)"

    st.write("User debt level = ", debt_levels_options)
    # debt_levels_benchmark = st.selectbox("Debt Levels Benchmark", debt_levels_options)
    # debt_levels_score = get_score_from_benchmark(debt_levels_benchmark, debt_levels_options)
    debt_levels_score = get_score_from_benchmark(debt_levels_benchmark, score_mapping["Debt Levels"])

    st.divider()
    # ======================================================

    payment_history_weight = st.slider("Payment History Weight", 0, 20, 10)
    # "Payment History": {"0-50% on-time": 1, "51-80% on-time": 3, "81-100% on-time": 5}
    # payment_history_options = list(score_mapping["Payment History"].keys())
    # "Payment History": {"0-50% on-time": 1, "51-80% on-time": 3, "81-100% on-time": 5},

    payment_history_options = filtered_data['perc_months_default'][0] 
    if payment_history_options <= 50:
        payment_history_benchmark = "0-50% on-time"
    elif 50 < payment_history_options <= 80 :
        payment_history_benchmark = "51-80% on-time"
    else:
        payment_history_benchmark = "81-100% on-time"

    st.write("User payment history perc. = ", payment_history_benchmark)
    # payment_history_benchmark = st.selectbox("Payment History Benchmark", payment_history_options)
    # payment_history_score = get_score_from_benchmark(payment_history_benchmark, payment_history_options)
    payment_history_score = get_score_from_benchmark(payment_history_benchmark, score_mapping["Payment History"])

    st.write("### Learning & Growth - Collateral")
    # ======================================================

    type_collateral_weight = st.slider("Type of Collateral Weight", 0, 10, 4)

    st.dataframe(filtered_data[['number','car_brand', 'car_model', 'car_manfucture_year','Club Name',]])
    type_collateral_options = list(score_mapping["type_collateral"].keys()) 
    # type_collateral_options
    # "type_collateral":{"Personal items":1,"Vehicles":3,"Club":3,"Real estate":5}
    type_collateral_benchmark = st.selectbox("Type of Collateral Benchmark", type_collateral_options)
    # type_collateral_benchmark = filtered_data['debt_level'][0]
    # type_collateral_score = get_score_from_benchmark(type_collateral_benchmark, type_collateral_options)
    type_collateral_score = get_score_from_benchmark(type_collateral_benchmark, score_mapping["type_collateral"])

    st.divider()

    collateral_weight = st.slider("Collateral Value Weight", 0, 10, 6)
    if type_collateral_benchmark == "Vehicles":
        # BrandNameEN = st.text_input("What is your car brand name in Eng.")
        # ModelNameEN = st.text_input("What is your car Model name in Eng.")

        # BrandNameEN = st.selectbox("Select car brand name",cars['BrandNameEN'])
        BrandNameEN = filtered_data['car_brand'][0]
        st.write("Car brand : ", BrandNameEN)
        filtered_cars_brand = cars[cars['BrandNameEN']==BrandNameEN]

        # ModelNameEN = st.selectbox("Select the car Model",filtered_cars_brand['ModelNameAR'])
        ModelNameEN = filtered_data['car_model'][0]
        st.write("Car Model : ", ModelNameEN)
        filtered_cars = filtered_cars_brand[filtered_cars_brand['ModelNameAR']==ModelNameEN]

        # ManifcatureYear = int(st.number_input("What is the manifacture year?"))
        ManifcatureYear = filtered_data['car_manfucture_year'][0]
        st.write("Car Manf. Year : ", ManifcatureYear)

        current_year = int(datetime.now().year)

        First_5_years = current_year - 5
        Last_5_Years = First_5_years - 5

        First_5_Years_cond  = current_year >= ManifcatureYear >= First_5_years
        print('First_5_Years_cond : ',First_5_Years_cond) 

        Last_5_Years_cond = First_5_years >= ManifcatureYear >= Last_5_Years
        print('Last_5_Years_cond : ',Last_5_Years_cond)

        if First_5_Years_cond:
            car_value = filtered_cars['LastFiveYears'].reset_index(drop=True)
            car_value = int(car_value[0])
            print('car_value : ',car_value)
            st.write("aman offers : ", car_value)
            # if car_value < 100000:
            #     collateral_benchmark = "<EGP 100,000"
            # elif 200000 > car_value >= 100000:
            #     collateral_benchmark = "EGP 100,000-200,000"
            # elif 500000 > car_value >= 200000:
            #     collateral_benchmark = "EGP 200,000-500,000"
            # elif 1000000 > car_value >= 500000: 
            #     collateral_benchmark = "EGP 500,000-1,000,000"
            # else:
            #     collateral_benchmark = ">EGP 1,000,000"

        elif Last_5_Years_cond:
            car_value = filtered_cars['PlusFiveYears'].reset_index(drop=True)
            car_value = int(car_value[0])
            print('car_value : ',car_value)
            st.write("aman offers : ", car_value)
            # if car_value < 100000:
            #     collateral_benchmark = "<EGP 100,000"
            # elif 200000 > car_value >= 100000:
            #     collateral_benchmark = "EGP 100,000-200,000"
            # elif 500000 > car_value >= 200000:
            #     collateral_benchmark = "EGP 200,000-500,000"
            # elif 1000000 > car_value >= 500000: 
            #     collateral_benchmark = "EGP 500,000-1,000,000"
            # else:
            #     collateral_benchmark = ">EGP 1,000,000"
        # else:
            
            # collateral_score = get_score_from_benchmark(collateral_benchmark, collateral_options)
        # collateral_options = list(score_mapping["collateral"].keys())
        # collateral_benchmark = st.selectbox("Collateral Value Benchmark", collateral_options)
        # st.write('collateral_value :', collateral_benchmark)    


    elif type_collateral_benchmark == "Club":
        # club = st.selectbox("Select a club",clubs['NameEn'])
        club = filtered_data['Club Name'][0]
        st.write("Club Name : ", club)
        club_value =  clubs[clubs['NameEn']==club]['PostAmanLimit2'].reset_index(drop=True)
        club_value =int(club_value[0])
        print('club_value : ', club_value)
        st.write("aman offers : ", club_value)

        # if club_value < 100000:
        #     collateral_benchmark = "<EGP 100,000"
        # elif 200000 > club_value >= 100000:
        #     collateral_benchmark = "EGP 100,000-200,000"
        # elif 500000 > club_value >= 200000:
        #     collateral_benchmark = "EGP 200,000-500,000"
        # elif 1000000 > club_value >= 500000: 
        #     collateral_benchmark = "EGP 500,000-1,000,000"
        # else:
        #     collateral_benchmark = ">EGP 1,000,000"
        # st.write('collateral_value :', collateral_benchmark)    

    # else:
    collateral_options = list(score_mapping["collateral"].keys())
    collateral_benchmark = st.selectbox("Collateral Value Benchmark", collateral_options)
        # collateral_score = get_score_from_benchmark(collateral_benchmark, collateral_options)
    collateral_score = get_score_from_benchmark(collateral_benchmark, score_mapping["collateral"])

    st.divider()

    industry_type_weight = st.slider("insurance Type Weight", 0, 10, 3)
    industry_type_options = list(score_mapping["Industry Type"].keys())
    industry_type_benchmark = st.selectbox("Industry Type Benchmark", industry_type_options)
    # industry_type_score = get_score_from_benchmark(industry_type_benchmark, industry_type_options)
    industry_type_score = get_score_from_benchmark(industry_type_benchmark, score_mapping["Industry Type"])

    st.divider()

    spending_patterns_weight = st.slider("Spending Patterns Weight", 0, 10, 3)
    spending_patterns_options = list(score_mapping["Spending Patterns"].keys())
    spending_patterns_benchmark = st.selectbox("Spending Patterns Benchmark", spending_patterns_options)
    # spending_patterns_score = get_score_from_benchmark(spending_patterns_benchmark, spending_patterns_options)
    spending_patterns_score = get_score_from_benchmark(spending_patterns_benchmark, score_mapping["Spending Patterns"])

    st.divider()
    # Calculate each weighted score and add to the total
    total_score = (
        calculate_weighted_score(income_score, income_weight) +
        # calculate_weighted_score(stability_score, stability_weight) +
        calculate_weighted_score(age_score, age_weight) +
        calculate_weighted_score(marital_status_score, marital_status_weight) +
        calculate_weighted_score(family_dependents_score, family_dependents_weight) +
        calculate_weighted_score(education_score, education_weight) +
        calculate_weighted_score(employment_age_score, employment_age_weight) +
        calculate_weighted_score(job_position_score, job_position_weight) +
        calculate_weighted_score(i_score_score, i_score_weight) +
        calculate_weighted_score(collateral_score, collateral_weight) +
        calculate_weighted_score(credit_history_length_score, credit_history_length_weight) +
        calculate_weighted_score(debt_levels_score, debt_levels_weight) +
        calculate_weighted_score(payment_history_score, payment_history_weight) +
        calculate_weighted_score(residence_stability_score, residence_stability_weight) +
        calculate_weighted_score(employment_type_score, employment_type_weight) +
        calculate_weighted_score(industry_type_score, industry_type_weight) +
        calculate_weighted_score(spending_patterns_score, spending_patterns_weight) +
        calculate_weighted_score(type_collateral_score, type_collateral_weight)
    )
    # Sum of all weights, should ideally be close to 100 for full distribution
    # total_weight = sum(weights.values())
    total_weight = income_weight+age_weight+marital_status_weight+family_dependents_weight+education_weight+employment_age_weight+job_position_weight+i_score_weight+collateral_weight+credit_history_length_weight+debt_levels_weight+payment_history_weight+residence_stability_weight+employment_type_weight+industry_type_weight+spending_patterns_weight+type_collateral_weight
    # Calculate final score as a percentage, normalized based on maximum achievable score (5 per factor)
    max_possible_score = total_weight * 5  # 5 is the highest eligibility score per factor
    final_score = (total_score / max_possible_score) * 100 if max_possible_score != 0 else 0
    # final_score = (total_score / max_possible_score) * 100 if max_possible_score != 0 else 0


    # Display final score in percentage
    st.subheader("Final Credit Score")
    st.metric(label="Score", value=f"{final_score:.2f}%")

    # Determine eligibility and loan amount
    if location_flag:
        loan_eligibility = "Rejected"
        rejection_reason = 'red_flags : location'
        eligible_amount = 0
    elif job_flag:
        loan_eligibility = "Rejected"
        rejection_reason = 'red_flags : job'
        eligible_amount = 0
    elif final_score < 50:
        loan_eligibility = "Rejected"
        rejection_reason = f'Low Score: {final_score}'
        eligible_amount = 0
    else:
        # Scale the eligible amount from 0 EGP to 50,000 EGP based on the final score
        eligible_amount = (final_score - 50) / 50 * 50000  # Linear scaling from 50-100 score to 0-50k EGP
        loan_eligibility = f"Eligible for up to {eligible_amount:,.2f} EGP"

    # Display eligibility and eligible amount
    st.markdown(f"""
        <div style="
            padding: 20px;
            background-color: #e6f2ff;
            border-radius: 10px;
            text-align: center;
            font-size: 20px;
            color: #333333;
        ">
            <strong>Loan Eligibility:</strong> {loan_eligibility}
        </div>
        """, unsafe_allow_html=True)
    if loan_eligibility == 'Rejected':
        st.write(f'rejection reason : {rejection_reason}')

    st.write("")

    if st.button('show user default info'):
        st.write("User default info")
        st.dataframe(filtered_data[['max_installment_amount','transaction_count_x','repayment_status']])

if __name__ == "__main__":
    main()