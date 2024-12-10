# import streamlit as st
import pandas as pd
import pymysql
import requests as req
from datetime import datetime, timedelta
from urllib import parse
import streamlit as st
import requests
from urllib import parse
import pandas as pd
import json
# from urllib import parse
from sqlalchemy import create_engine
from urllib import parse
import pandas as pd
import logging as logging
import os

import requests
import csv
import pandas as pd
import time
import urllib3
import json

# Auth Step
url = "https://www.amanshops.com/AmanAPI/Account/Auth"
# Define the payload with your username, password, and lang
data = {
    "AccountNumber": "31072632026",
    "Password": "ADVA@2023",
    "Lang": 1
}

response = requests.post(url, json=data)
if response.status_code == 200:
    data = response.json()
    if "Token" in data:
        token = data["Token"]
        print("Token:", token)
    else:
        print("Error: 'Token' not found in response")
else:
    print("Error: Request failed with status code", response.status_code)


    from datetime import datetime

########################## Card and Trx details ###############################


def get_card_info(mobile_number):
    payload = {
        "MobileNumber": mobile_number,
        "lang": 1
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
    url = 'https://www.amanshops.com/AmanAPI/Card/AmanCardInfo'
    response = requests.post(url, json=payload, headers=headers)
    card_info = response.json()

    # Check if there's data in the response
    if 'card_info' in card_info and 'trx_details' in card_info and card_info['trx_details']:
        # Initialize variables
        balance = float(card_info['card_info']['Balance'])
        num_of_trx = len(card_info['trx_details'])  # Number of transactions
        sum_of_trx_amount = 0  # Total transaction amount
        trx_amounts_per_year = {}  # Amount spent per year
        active_trx_count = 0  # Number of active transactions
        done_trx_count = 0  # Number of done transactions

        # Current date for comparison
        current_date = datetime.now()

        # Process each transaction
        for trx in card_info['trx_details']:
            trx_amount = trx['TotalAmount']
            trx_date = trx['TrxDate']
            trx_year = trx_date.split('/')[-1]  # Extract the year from the transaction date
            trx_end_date_str = trx['TrxEndDate']
            trx_end_date = datetime.strptime(trx_end_date_str, '%d/%m/%Y')  # Convert to datetime object

            # Summing up the transaction amounts
            sum_of_trx_amount += trx_amount

            # Calculate the amount spent per year
            if trx_year not in trx_amounts_per_year:
                trx_amounts_per_year[trx_year] = 0
            trx_amounts_per_year[trx_year] += trx_amount

            # Check if the transaction is done or active
            if trx_end_date < current_date:
                done_trx_count += 1  # Transaction is done
            else:
                active_trx_count += 1  # Transaction is active

        # Create a summary of the data
        summary = {
            'Current Card Balance': balance,
            'Trxs': num_of_trx,
            'Trxs Amount': sum_of_trx_amount,
            'Trxs Amount Per Year': trx_amounts_per_year,
            'Active Trxs': active_trx_count,
            'Done Trxs': done_trx_count
        }

        return summary
    else:
        return "This number has no CF cards or trxs"

########################## Paid Installments ###############################


def get_paid_installments(mobile_number):
    payload = {
        "MobileNumber": mobile_number,
        "lang": 1
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
    url = 'https://www.amanshops.com/AmanAPI/Card/GetPaidInstallments'
    response = requests.post(url, json=payload, headers=headers)
    paid_installments = response.json()

    # Check if there's data or not
    if paid_installments['ResultID'] == -46:
        return "No Paid Installments for this number"
    else:
        # Extract paid installments data
        installments = paid_installments['PaidInstallments']

        # Initialize variables to store results
        total_amount_per_year = {}  # Dictionary to store total amount per year
        monthly_count_per_year = {}  # Dictionary to count months per year

        # Iterate over the data for each year
        for year, payments in installments.items():
            total_amount_per_year[year] = 0
            monthly_count_per_year[year] = 0
            for payment in payments:
                total_amount_per_year[year] += payment['TotalAmount']  # Sum the total amount for the year
                # Count months per year (based on number of payments)
                monthly_count_per_year[year] += 1

        # Calculate average monthly payment per year
        avg_amount_per_month = {}
        for year, total_amount in total_amount_per_year.items():
            avg_amount_per_month[year] = total_amount / monthly_count_per_year[year]

        # Round the results and cast them to integers
        total_amount_per_year = {year: int(round(amount)) for year, amount in total_amount_per_year.items()}
        avg_amount_per_month = {year: int(round(avg)) for year, avg in avg_amount_per_month.items()}

        # Create summary of the data
        summary2 = {
            'total_amount_per_year': total_amount_per_year,
            'avg_amount_per_month': avg_amount_per_month
        }

        return summary2
    




########################## Defaults and next installments cards ###############################

def get_next_paid_installments(mobile_number):
    payload = {
        "MobileNumber": mobile_number,
        "lang": 1
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
    url = 'https://www.amanshops.com/AmanAPI/Card/NextPaidInstallments'
    response = requests.post(url, json=payload, headers=headers)
    next_installments = response.json()

    # Check if data exists
    if next_installments.get('ResultID') == -46:
        return "No next installments found for this number."
    
    installments = next_installments.get("NextInstallments", {})
    
    total_left_amount = 0
    total_amount_per_year = {}
    all_installments = []
    last_payment_date = None
    default_trxs = 0
    defaulted_amount = 0
    default_days = 0
    today = datetime.now().date()
    
    # Process installments for each year
    for year, payments in installments.items():
        total_amount_per_year[year] = sum(payment['TotalAmount'] for payment in payments)
        all_installments.extend(payments)  # Collect all installments
        for payment in payments:
            total_left_amount += payment['TotalAmount']  # Calculate total left to be paid
            # last_payment_date = payment['Date']  # Update the last payment date as the loop progresses
            
            # Check for defaulted transactions
            payment_date = datetime.strptime(payment['Date'], '%m/%d/%Y').date()
            if payment_date < today:
                default_trxs += 1
                defaulted_amount += payment['TotalAmount']
                days_defaulted = (today - payment_date).days
                default_days = max(default_days, days_defaulted)
    
    # Calculate the average amount to be paid per month
    num_months = len(all_installments)
    avg_amount_per_month = total_left_amount / num_months if num_months > 0 else 0
    
    # Prepare output
    summary3 = {
        "total_left_amount": int(total_left_amount),
        "avg_amount_per_month": int(round(avg_amount_per_month)),
        "total_amount_per_year": {year: int(amount) for year, amount in total_amount_per_year.items()},
        # "last_payment_date": last_payment_date,
        "default_trxs": default_trxs,
        "defaulted_amount": int(defaulted_amount),
        "default_days": default_days
    }

    return summary3


import requests
import json
from datetime import datetime


########################## Customer Data Function ###############################


import requests
import json
from datetime import datetime

def get_customer_data(mobile_number):
    payload = {
        "MobileNumber": mobile_number,
        "lang": 1
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
    url = 'https://www.amanshops.com/AmanAPI/Installment/GetCustomerData'
    response = requests.post(url, json=payload, headers=headers)
    adva_purchases = response.json()
    
    # Check if the response contains valid data
    if adva_purchases['ResultID'] == 0 and 'FullName_ar' in adva_purchases:
        data = adva_purchases
        customer_data = {
            "FullName_ar": data.get('FullName_ar', None),
            "NationalID": data.get('NationalID', None),
            "Address1": data.get('Address1', None),
            "Salary": data.get('Salary', None),
            "Job": data.get('Job', None),
            "JobAddress": data.get('JobAddress', None)
        }

        # Extract age and gender from NationalID
        national_id = data.get('NationalID', '')
        if national_id:
            year_of_birth = national_id[1:3]
            gender_code = int(national_id[-2]) if len(national_id) >= 2 else None
            
            # Determine the full year of birth
            current_year = datetime.now().year
            years_2000 = ["00", "01", "02", "03", "04"]
            year_prefix = "20" if year_of_birth in years_2000 else "19"
            year_of_birth = int(year_prefix + year_of_birth)
            
            # Calculate age
            age = current_year - year_of_birth
            
            # Determine gender
            gender = 'Female' if gender_code is not None and gender_code % 2 == 0 else 'Male'
            
            customer_data["Age"] = age
            customer_data["Gender"] = gender
        else:
            customer_data["Age"] = None
            customer_data["Gender"] = None

        return customer_data
    
    else:
        return "No Customer Profile for this number from CF"

############################################################## Credify Function ###############################################################


engine_adva = create_engine("mysql+pymysql://datateam:%s@172.16.20.6:3306/salamtakdb_new_schema" % parse.quote("datateam@Advaeg@048"))
engine2 = create_engine("mysql+pymysql://admin:%s@adva-warehouse.c45dykr9xlqi.eu-west-3.rds.amazonaws.com:3306/aman_v_2" % parse.quote("Youssef123$"))
engine_zoho = create_engine("mysql+pymysql://admin:%s@adva-warehouse.c45dykr9xlqi.eu-west-3.rds.amazonaws.com:3306/zoho" % parse.quote("Youssef123$"))

def get_user_transactions(mobile_number):
    # Credify API credentials
    creds = {
        "email": "credify-api@advaeg.com",
        "password": "JyZT@|!yo0%0pgD'|8mhnnkQhkINyUeB[99Z`xpCiY'Bc\r^F>o=Cj|d'SAPX}Y?U#`7%>SOGQ'OS+=`7;S,9@-+ey5Nw6MLRk'o<fbi*|ggE4|-a,~*+pYL]5|v'i"
    }

    try:
        # Get access token
        auth_url = 'https://api.credify.live/v1/auth/login'
        auth_response = requests.post(url=auth_url, json=creds)
        auth_response.raise_for_status()  # Raise an exception for bad status codes
        acc_token = auth_response.json()['access_token']

        # Database connection
        engine_adva = create_engine("mysql+pymysql://datateam:%s@172.16.20.6:3306/salamtakdb_new_schema" % parse.quote("datateam@Advaeg@048"))

        # SQL query
        query_credify = f"SELECT * FROM useraccounts WHERE Phone = '{mobile_number}'"

        # Execute query and fetch results
        with engine_adva.connect() as connection:
            result = pd.read_sql(query_credify, connection)

        # Check if we got any results
        if result.empty:
            return "No user found with this phone number"

        # Get the OwnerId (user_id)
        user_id = result['OwnerId'].iloc[0]

        # Make API call to get user transactions
        transactions_url = f'https://api.credify.live/api/v1/merchant/users/{user_id}/transactions'
        headers = {"authorization": f'Bearer {acc_token}'}
        resp = requests.get(url=transactions_url, headers=headers)
        # resp.raise_for_status()  # Raise an exception for bad status codes
        
        df = pd.DataFrame(resp.json()['items'])

        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Calculate date ranges
        today = datetime.now()
        last_30_days = today - timedelta(days=30)
        last_90_days = today - timedelta(days=90)

        # 1. Debit Banks
        debit_banks = df[df['account_type'] == 'Debit']['institution_name'].unique().tolist()

        # 2. Number of Sims
        number_of_sims = df[df['account_type'] == 'telecom']['institution_name'].nunique()

        # 3. Cash_in_last_30_days
        cash_in_last_30_days = df[(df['event'] == 'cash_in') & (df['timestamp'] > last_30_days)]['amount'].sum()

        # 4. Cash_out_last_30_days
        cash_out_last_30_days = df[(df['event'] == 'cash_out') & (df['timestamp'] > last_30_days)]['amount'].sum()

        # 5. Cash_in_last_90_days
        cash_in_last_90_days = df[(df['event'] == 'cash_in') & (df['timestamp'] > last_90_days)]['amount'].sum()

        # 6. Cash_out_last_90_days
        cash_out_last_90_days = df[(df['event'] == 'cash_out') & (df['timestamp'] > last_90_days)]['amount'].sum()

        # 7. sim_card_recharge_amount (refined)
        sim_card_recharge_amount = (
            df[(df['account_type'] == 'telecom') & (df['transaction_type'] == 'balance_recharge')]
            ['amount'].mean()
        )

        # 8. average_cash_in_per_month (refined)
        average_cash_in_per_month = (
            df[df['event'] == 'cash_in']
            .groupby(df['timestamp'].dt.to_period('M'))['amount']
            .mean()
            .mean()  # This calculates the average of the monthly averages
        )

        # 9. average_cash_out_per_month (refined)
        average_cash_out_per_month = (
            df[df['event'] == 'cash_out']
            .groupby(df['timestamp'].dt.to_period('M'))['amount']
            .mean()
            .mean()  # This calculates the average of the monthly averages
        )

        # 10. creditcards_or_limits
        creditcards_or_limits = df[df['account_type'] == 'credit_limit']['institution_name'].nunique()

        # 11. limits
        limit_providers = ["Fawry", "aman", "premium", "halan", "valu", "contact", "shahry", "sympl", "blnk", "mid_takseet"]
        limits = df[df['institution_name'].isin(limit_providers)]['institution_name'].unique().tolist()

        # 12. credit_cards
        credit_cards = df[(df['account_type'] == 'credit_limit') & (~df['institution_name'].isin(limit_providers))]['institution_name'].unique().tolist()

        # Prepare the result


        result = {
            "Debit_Banks": debit_banks,
            "Number_of_Sims": number_of_sims,
            "Cash_in_last_30_days": cash_in_last_30_days,
            "Cash_out_last_30_days": cash_out_last_30_days,
            "Cash_in_last_90_days": cash_in_last_90_days,
            "Cash_out_last_90_days": cash_out_last_90_days,
            "sim_card_recharge_amount": sim_card_recharge_amount,
            "average_cash_in_per_month": average_cash_in_per_month,
            "average_cash_out_per_month": average_cash_out_per_month,
            "creditcards_or_limits": creditcards_or_limits,
            "limits": limits,
            "credit_cards": credit_cards
        }

        return result
    
    except requests.exceptions.RequestException as e:
        return f"API call failed: {str(e)}"
    except Exception as e:
        return "No SMSs data for this number"


logging.basicConfig(level=logging.INFO)


def get_zoho_customer_data(phone_number):
    logging.info(f"Attempting to retrieve data for phone number: {phone_number}")
    
    # Create the database engine
    engine_zoho = create_engine("mysql+pymysql://admin:%s@adva-warehouse.c45dykr9xlqi.eu-west-3.rds.amazonaws.com:3306/zoho" % parse.quote("Youssef123$"))

    # Define the queries
    queries = {
        "salary": f"SELECT fp.`Total Income` FROM financial_profiles fp JOIN registered_users ru ON fp.Customer = ru.Customer WHERE ru.phone = '{phone_number}'",
        "age": f"SELECT fp.Age FROM financial_profiles fp JOIN registered_users ru ON fp.Customer = ru.Customer WHERE ru.phone = '{phone_number}'",
        "gender": f"SELECT fp.CalculatedGender FROM financial_profiles fp JOIN registered_users ru ON fp.Customer = ru.Customer WHERE ru.phone = '{phone_number}'",
        "name": f"SELECT fp.`Financial Profile Name` FROM financial_profiles fp JOIN registered_users ru ON fp.Customer = ru.Customer WHERE ru.phone = '{phone_number}'",
        "marital_status": f"SELECT fp.`Marital Status` FROM financial_profiles fp JOIN registered_users ru ON fp.Customer = ru.Customer WHERE ru.phone = '{phone_number}'",
        "job": f"SELECT fp.`Employment Sector` FROM financial_profiles fp JOIN registered_users ru ON fp.Customer = ru.Customer WHERE ru.phone = '{phone_number}'"
    }

    results = {}

    try:
        for key, query in queries.items():
            logging.info(f"Executing query: {query}")
            result = pd.read_sql(query, engine_zoho)
            
            if not result.empty:
                results[key] = result.iloc[0, 0]
                logging.info(f"Result for {key}: {results[key]}")
            else:
                results[key] = None
                logging.warning(f"No result found for {key}")

        if all(value is None for value in results.values()):
            logging.warning("No data found for any query")
            return "No data found for this phone number"

        return results

    except Exception as e:
        error_msg = f"An error occurred while retrieving Zoho data: {str(e)}"
        logging.error(error_msg)
        return error_msg
    
# zoho_data = get_zoho_customer_data("1234567890")
# print(zoho_data)
def calculate_iscore_metrics(customer_data, zoho_data, next_installments):
    # Check if both customer_data and zoho_data are None
    if customer_data is None and zoho_data is None:
        return "Unable to calculate I-Score: No customer data available"

    # Get salary from either customer_data or zoho_data
    salary = None
    if customer_data and isinstance(customer_data, dict):
        salary = customer_data.get('Salary')
    if salary is None and zoho_data and isinstance(zoho_data, dict):
        salary = zoho_data.get('salary')
    
    if not salary:
        return "Unable to calculate I-Score: Salary information not available"

    try:
        salary = float(salary)
    except ValueError:
        return f"Unable to calculate I-Score: Invalid salary value ({salary})"

    if salary <= 0:
        return "Unable to calculate I-Score: Salary must be greater than zero"

    # Check if next_installments is None or not a dictionary
    if next_installments is None or not isinstance(next_installments, dict):
        return "Unable to calculate I-Score: Installment information not available"

    # Get Avg_amount_per_month from next_installments
    avg_amount_per_month = next_installments.get('avg_amount_per_month')
    if avg_amount_per_month is None:
        return "Unable to calculate I-Score: Average monthly installment information not available"

    try:
        avg_amount_per_month = float(avg_amount_per_month)
    except ValueError:
        return f"Unable to calculate I-Score: Invalid average monthly installment value ({avg_amount_per_month})"

    # Get default_trxs from next_installments
    default_trxs = next_installments.get('default_trxs')
    if default_trxs is None:
        return "Unable to calculate I-Score: Default transactions information not available"

    try:
        default_trxs = int(default_trxs)
    except ValueError:
        return f"Unable to calculate I-Score: Invalid default transactions value ({default_trxs})"

    # Calculate max_eligible_amount and max_eligible_limit
    max_eligible_amount = salary
    max_eligible_limit = max(0, salary - (avg_amount_per_month * 12))

    # Calculate DBR
    dbr = (avg_amount_per_month / salary) * 100 if salary > 0 else 0

    # Calculate credit score
    def calculate_credit_score(dbr, dbr_min=0, dbr_max=40):
        if dbr_max == dbr_min:
            return 100 if dbr <= dbr_min else 0
        credit_score = (1 - (dbr - dbr_min) / (dbr_max - dbr_min)) * 100
        return max(0, min(credit_score, 100))

    credit_score = calculate_credit_score(dbr)

    # Calculate final credit score
    final_credit_score = max(0, credit_score - (10 * default_trxs))

    # Generate I-Score
    def generate_iscore(credit_score_decimal, iscore_min=0, iscore_max=1000):
        score_percentage = credit_score_decimal / 100
        iScore = int(iscore_min + (iscore_max - iscore_min) * score_percentage)
        if iScore < 400:
            risk_category = "Defaulting"
        elif iScore < 520:
            risk_category = "High Risk"
        elif iScore < 625:
            risk_category = "Poor"
        elif iScore < 700:
            risk_category = "Good"
        elif iScore < 750:
            risk_category = "Very Good"
        else:
            risk_category = "Excellent"
        return iScore, risk_category

    iscore, risk_category = generate_iscore(final_credit_score)

    return {
        "max_eligible_amount": max_eligible_amount,
        "max_eligible_limit": max_eligible_limit,
        "dbr": dbr,
        "credit_score": credit_score,
        "default_transactions": default_trxs,
        "final_credit_score": final_credit_score,
        "iscore": iscore,
        "risk_category": risk_category
    }

def get_consolidated_customer_data(mobile_number):
    # Ensure the token is available
    global token
    
    # Call each function and store the results
    card_info = get_card_info(mobile_number)
    paid_installments = get_paid_installments(mobile_number)
    next_installments = get_next_paid_installments(mobile_number)
    customer_data = get_customer_data(mobile_number)
    user_transactions = get_user_transactions(mobile_number)
    zoho_data = get_zoho_customer_data(mobile_number)
    
    # Initialize the consolidated data dictionary
    consolidated_data = {}
    
    # Helper function to safely update the consolidated data
    def safe_update(data, key):
        if isinstance(data, dict):
            consolidated_data[key] = data
        elif isinstance(data, str) and data not in ["No SMSs data for this number", "No Customer Profile for this number", "No data found for this phone number"]:
            consolidated_data[key] = data

    # Safely add each result to the consolidated data
    safe_update(card_info, 'Card Info')
    safe_update(paid_installments, 'Paid Installments')
    safe_update(next_installments, 'Next Installments')
    safe_update(customer_data, 'Customer Data')
    safe_update(user_transactions, 'User Transactions')
    safe_update(zoho_data, 'Zoho Data')
    
    # Calculate I-Score metrics
    iscore_metrics = calculate_iscore_metrics(
        consolidated_data.get('Customer Data'),
        consolidated_data.get('Zoho Data'),
        consolidated_data.get('Next Installments')
    )
    if isinstance(iscore_metrics, dict):
        safe_update(iscore_metrics, 'I-Score Metrics')
    else:
        consolidated_data['I-Score Metrics'] = {'Error': iscore_metrics}
    
    # Check if we have any data
    if not consolidated_data:
        return "No data found for this number"
    
    return consolidated_data

# Custom CSS to style the app
css = """
<style>
body {
    font-family: Arial, sans-serif;
    background-color: #f0f2f6;
    color: #1f1f1f;
}

.main-title {
    color: #0e1117;
    text-align: center;
    padding: 20px 0;
    font-size: 2.5em;
    font-weight: bold;
}

.tab-title {
    color: #0e1117;
    border-bottom: 2px solid #0e1117;
    padding-bottom: 10px;
    margin-bottom: 20px;
}

.section-title {
    color: #0e1117;
    margin-top: 30px;
    margin-bottom: 15px;
}

.card {
    background-color: white;
    border-radius: 5px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    padding: 20px;
    margin-bottom: 20px;
}

.card h3 {
    color: #0e1117;
    margin-bottom: 10px;
    font-size: 1.2em;
}

.card p {
    color: #4a4a4a;
    font-size: 1.1em;
}

.year-value {
    display: flex;
    justify-content: space-between;
    margin-bottom: 5px;
}

.year {
    font-weight: bold;
    color: #0e1117;
}

.amount {
    color: #4a4a4a;
}

.stButton > button {
    background-color: #0e1117;
    color: white;
    font-weight: bold;
    padding: 10px 20px;
    border-radius: 5px;
    border: none;
    cursor: pointer;
    transition: background-color 0.3s ease;
}

.stButton > button:hover {
    background-color: #2e7d32;
}

.stTextInput > div > div > input {
    background-color: white;
    color: #0e1117;
    border-radius: 5px;
    border: 1px solid #0e1117;
    padding: 10px;
    font-size: 1em;
}
</style>
"""

# Inject custom CSS
st.markdown(css, unsafe_allow_html=True)

def format_nested_dict(nested_dict):
    formatted_html = ""
    for key, value in nested_dict.items():
        formatted_html += f'<div class="year-value"><span class="year">{key}:</span><span class="amount">{value}</span></div>'
    return formatted_html


def display_card(title, value):
    with st.container():
        if isinstance(value, dict) and all(isinstance(v, (int, float)) for v in value.values()):
            st.markdown(f"""
            <div class="card">
                <h3>{title}</h3>
                {format_nested_dict(value)}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="card">
                <h3>{title}</h3>
                <p>{value}</p>
            </div>
            """, unsafe_allow_html=True)

def format_nested_dict(nested_dict):
    formatted_html = ""
    for key, value in nested_dict.items():
        formatted_html += f'<div class="year-value"><span class="year">{key}:</span><span class="amount">{value}</span></div>'
    return formatted_html

# import streamlit as st
import base64
import os

def display_data_section(data, section_title):
    if data:
        st.markdown(f"<h3 class='section-title'>{section_title}</h3>", unsafe_allow_html=True)
        if isinstance(data, dict):
            col1, col2 = st.columns(2)
            for i, (key, value) in enumerate(data.items()):
                with col1 if i % 2 == 0 else col2:
                    display_card(key.capitalize().replace('_', ' '), value)
        else:
            st.warning(data)
    else:
        st.warning(f"No {section_title} data available")

def get_binary_file_downloader_html(bin_file, file_label='File'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">Download {file_label}</a>'
    return href


def main():
    st.markdown("<h1 class='main-title'>Customer Credit Score Card</h1>", unsafe_allow_html=True)

    phone_number = st.text_input("Enter Customer Phone Number:")

    if st.button("Generate Credit Score Card"):
        if phone_number:
            with st.spinner('Retrieving customer data...'):
                consolidated_data = get_consolidated_customer_data(phone_number)

            if isinstance(consolidated_data, dict):
                tab1, tab2, tab3, tab4 = st.tabs(["Alternative Data", "CF Data", "Customer Profile", "I-Score"])

                with tab1:
                    st.markdown("<h2 class='tab-title'>Alternative Data</h2>", unsafe_allow_html=True)
                    display_data_section(consolidated_data.get('User Transactions'), 'Alternative Data')

                with tab2:
                    st.markdown("<h2 class='tab-title'>CF Data</h2>", unsafe_allow_html=True)
                    display_data_section(consolidated_data.get('Customer Data'), 'CF Customer Profile')
                    for section in ['Next Installments', 'Paid Installments', 'Card Info']:
                        display_data_section(consolidated_data.get(section), section)

                with tab3:
                    st.markdown("<h2 class='tab-title'>Customer Profile</h2>", unsafe_allow_html=True)
                    display_data_section(consolidated_data.get('Zoho Data'), 'Customer Profile')

                with tab4:
                    st.markdown("<h2 class='tab-title'>I-Score</h2>", unsafe_allow_html=True)
                    iscore_metrics = consolidated_data.get('I-Score Metrics')
                    if isinstance(iscore_metrics, dict):
                        if 'Error' in iscore_metrics:
                            st.warning(iscore_metrics['Error'])
                        else:
                            st.subheader("Final Credit Score")
                            st.info(f"{iscore_metrics['final_credit_score']:.2f}")
                            st.markdown("---")
                            display_data_section(iscore_metrics, 'I-Score Metrics')
                            
                            # Add download button
                            file_path = r"29307120103552.pdf"  # Replace with your actual file path
                            st.markdown(get_binary_file_downloader_html(file_path, 'I-Score Document'), unsafe_allow_html=True)
                    else:
                        st.warning("Unable to calculate I-Score")

            else:
                st.error(f"Error: {consolidated_data}")
        else:
            st.warning("Please enter a phone number.")

if __name__ == "__main__":
    main()