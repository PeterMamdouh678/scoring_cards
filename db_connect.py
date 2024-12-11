import mysql.connector
from mysql.connector import Error
import pymysql
from sqlalchemy import create_engine
import numpy as np
import pandas as pd
pd.set_option('display.max_columns', None)
from datetime import datetime
import streamlit as st

def connect_db():
    # Connection parameters
    zoho = st.secrets['zoho']

    username = zoho['username']
    password = zoho['password']
    host = zoho['host']
    port = zoho['port']
    database = zoho['database']

    # Create the connection engine
    engine = create_engine(f'mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}',
                              pool_recycle=3600,  # Recycle connections after 1 hour
                                pool_timeout=3600,    # Pool timeout
                                # pool_size=5,        # Maximum pool size
                                max_overflow=10,    # Maximum number of connections to create above pool_size
                                connect_args={
                                    'connect_timeout': 3600,  # Connection timeout
                                    }
                           )
    # Connect to the database
    conn = engine.connect()

    sql = """
    select *
    FROM financial_profiles
    """
    # conn = mysql.connector.connect(database='zoho', password='Youssef123$', 
    #                         host='adva-warehouse.c45dykr9xlqi.eu-west-3.rds.amazonaws.com', port='3306',user='admin')


    df = pd.read_sql(sql, conn)
    return df

# employment type 
def determine_employment_type(row):
    if row['Has Business'] == 'Yes':
        return 'Permanent'
    elif pd.notna(row['Employment Salary']) and row['Employment Salary'] != '':
        return 'Contract'
    elif pd.notna(row['Freelancer Sector']) and row['Freelancer Sector'] != '':
        return 'Self-employed'
    else:
        return 'Other'

# Adjust Car data
def process_car_data(row):
    # Initialize variables
    car_brand = None
    car_model = None
    car_manfucture_year = None

    # Step 2: Split 'Car Model' and assign values if it exists
    if row['Car Model'] and isinstance(row['Car Model'], str):
        parts = row['Car Model'].split(' ', 1)  # Split by space
        car_brand = parts[0]
        car_model = parts[1] if len(parts) > 1 else None

    # Step 3: Fill 'car_brand' if empty
    if not car_brand:
        car_brand = row['Car Brand'] or row['Car Type']

    # Step 4: Fill 'car_model' if empty
    if not car_model:
        car_model = row['Car Model OCR']

    # Step 5: Fill 'car_manfucture_year'
    car_manfucture_year = row['Manufacture Year'] or row['Car Manufacturing Year']

    return pd.Series([car_brand, car_model, car_manfucture_year])


# Calculate age
def calculate_age(birth_date):
    today = datetime.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age


# Define a function to clean the EGP format
def clean_currency(value):
    if pd.isna(value):  # Handle None or NaN
        return 0
    return float(value.replace('EGP', '').replace(',', '').strip())


def process_data():
    df = connect_db()

    df['number'] = df['Phone'].where(df['Phone'].notna() & (df['Phone'] != ''), df['Reference Contact Number'])
    df.drop(['Phone','Reference Contact Number'],axis=1,inplace=True)

    df['Number Of Dependents'] = df['Number Of Dependents'].replace({
        'No One': 0,
        None: 0,
        'One Person': 1,
        'Two Persons': 2,
        'Two Person':2,
        'Three Or More Persons': '2+'
    })


    # Apply the function to the DataFrame
    df['employment_type'] = df.apply(determine_employment_type, axis=1)

    # Apply the function to the DataFrame
    df[['car_brand', 'car_model', 'car_manfucture_year']] = df.apply(process_car_data, axis=1)


    # Convert 'Birth Of Date' to datetime and calculate age
    df['Birth Of Date'] = pd.to_datetime(df['Birth Of Date'], format='%d. %B %Y', errors='coerce')

    # Update 'Age' if it is empty or None
    df['Age'] = df.apply(
        lambda row: calculate_age(row['Birth Of Date']) if pd.isna(row['Age']) and pd.notna(row['Birth Of Date']) else row['Age'],
        axis=1
    )

    # Apply the cleaning function to relevant columns
    cols_to_clean = ['Remaining Limit', 'Credit Amount', 'Valu Limit']
    df[cols_to_clean] = df[cols_to_clean].map(clean_currency)

    # Calculate debt_level as Remaining Limit / (Credit Amount + Valu Limit)
    df['debt_level'] = (df['Remaining Limit'] / 
                        (df['Credit Amount'] + df['Valu Limit']).replace(0, float('inf'))) * 100

    # Replace infinity values (from division by zero) with 0
    df['debt_level'] = df['debt_level'].replace(float('inf'), 0)

    df= df [['number','ID Number','Remaining Limit','car_brand', 'car_model', 'car_manfucture_year','Club Name',
            'Age','Marital Status','NID Area','NID City', 'NID Occupation', 'Number Of Dependents',
            'employment_type','Total Income', 'debt_level'
            ]]
    
    return df

def transactions():
    # Connection parameters
    aman_db = st.secrets['aman']
    username = aman_db['username']
    password = aman_db['password']
    host = aman_db['host']
    port = aman_db['port']
    database = aman_db['database']

    # Create the connection engine
    engine = create_engine(f'mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}',
                              pool_recycle=3600,  # Recycle connections after 1 hour
                                pool_timeout=3600,    # Pool timeout
                                # pool_size=5,        # Maximum pool size
                                max_overflow=10,    # Maximum number of connections to create above pool_size
                                connect_args={
                                    'connect_timeout': 3600,  # Connection timeout
                                    }
                                    )
    # Connect to the database
    conn = engine.connect()

    sql= """ 
    select * 
    from user_installment_behavior
    """

    # Execute the query within a connection context
    user_installment_behavior =  pd.read_sql_query(sql, con=conn)
    user_installment_behavior = user_installment_behavior[["totalamount","api_phone_number","date_of_installment","stage","n_months_default"]].drop_duplicates()

    user_installment_behavior["n_months_default"] = user_installment_behavior["n_months_default"].replace("",np.nan)
    user_installment_behavior["totalamount"] =user_installment_behavior["totalamount"].astype(float)
    user_installment_behavior['date_of_installment'] = pd.to_datetime(user_installment_behavior['date_of_installment'])
    user_installment_behavior["n_months_default"] =user_installment_behavior["n_months_default"].astype(float)

    # Define the columns to aggregate
    group_by_column = 'api_phone_number'  # or 'nationalid' if you prefer

    # Convert date column to datetime
    user_installment_behavior['date_of_installment'] = pd.to_datetime(user_installment_behavior['date_of_installment'])

    # Define custom aggregation for n_months_default
    def ratio_zero_none(series):
        # Count where n_months_default is 0 or None
        count_zero_none = series.isin([0, None,'None',np.nan]).sum()
        # count_zero_none = series.isna().sum() + series.isin[0,'None'].sum()

        # total_count = series.count()  # Exclude None values for the total count
        total_count = len(series)
        # print('count_zero_none : ',count_zero_none)
        # print('total_count : ',total_count)
        return (count_zero_none / total_count)*100 if total_count > 0 else 0

    # Define aggregation dictionary
    agg_columns = {
        'totalamount': ['sum', 'mean', 'max'],           # Multiple aggregations for total amount
        'n_months_default': ['median', 'max', ratio_zero_none],  # Add custom aggregation
        'date_of_installment': ['first', 'last']         # First and last installment dates
    }

    # Perform aggregation
    customer_level_data = user_installment_behavior.groupby(group_by_column).agg(agg_columns).reset_index()

    # Flatten MultiIndex columns and rename them
    customer_level_data.columns = [
        'api_phone_number', 
        'totalamount_sum', 
        'totalamount_mean', 
        'totalamount_max', 
        'n_months_default_median', 
        'n_months_default_max', 
        'perc_months_default', 
        'date_of_installment_first', 
        'date_of_installment_last'
    ]

    # Add transaction count as an additional calculation
    customer_level_data['transaction_count'] = user_installment_behavior.groupby(group_by_column)['date_of_installment'].count().values

    # Display the aggregated data
    customer_level_data

    sql= """ 
    select * 
    from customers_data
    """

    customers_data =  pd.read_sql_query(sql, con=conn)
    customers_data = customers_data.dropna(subset=['nationalid'])
    customers_data = customers_data[["nationalid","fullname_ar","mobilenumber1","salary","job","birthdate","city","district","maritalstatus"]].drop_duplicates()
    customers_data = customers_data.rename(columns={"mobilenumber1": "api_phone_number"})


    sql= """ 
    select * 
    from trxs
    """

    # Execute the query within a connection context
    trxs =  pd.read_sql_query(sql, con=conn)
    trxs = trxs[["totalamount","months","monthlyamount","trxdate","merchent","trx_details_status","branch","trxid","trxtype","trxenddate","api_phone_number","downpayment"]].drop_duplicates()
    trxs['totalamount'] = pd.to_numeric(trxs['totalamount'], errors='coerce').fillna(0).astype(int)
    trxs['months'] = pd.to_numeric(trxs['months'], errors='coerce').fillna(0).astype(int)
    trxs['monthlyamount'] = pd.to_numeric(trxs['monthlyamount'], errors='coerce').fillna(0).astype(int)
    trxs['trxid'] = pd.to_numeric(trxs['trxid'], errors='coerce').fillna(0).astype(int)
    trxs['downpayment'] = pd.to_numeric(trxs['downpayment'], errors='coerce').fillna(0).astype(int)
    trxs['trxdate'] = pd.to_datetime(trxs['trxdate'], dayfirst=True)
    trxs['trxenddate'] = pd.to_datetime(trxs['trxenddate'], dayfirst=True)

    trxs["intrest"] = ( ((trxs["months"]*trxs["monthlyamount"])  /(trxs["totalamount"] - trxs["downpayment"])  )-1)*100
    trxs["total_inc_intrest"] = trxs["months"]*trxs["monthlyamount"]

    # Define aggregation rules
    agg_columns = {
        'totalamount': ['sum', 'mean', 'max'],       # Total, average, and max amount
        'months': 'max',                             # Max months for each customer
        'monthlyamount': 'mean',                     # Average monthly amount
        'trxdate': 'min',                            # First transaction date
        'trxenddate': 'max',                         # Last transaction date
        'trx_details_status': lambda x: x.mode()[0], # Most common transaction status
        'trxtype': lambda x: ', '.join(x.unique()),  # Concatenate unique transaction types
        'trxid': 'count'  ,
        "downpayment":'max'                           # Number of transactions per customer
    }

    # Perform aggregation by 'merchent' (or replace with an appropriate customer identifier)
    trxs_agg = trxs.groupby('api_phone_number').agg(agg_columns).reset_index()

    # Flatten multi-level columns
    trxs_agg.columns = [
        'api_phone_number', 'totalamount_sum', 'totalamount_mean', 'totalamount_max', 
        'months_max', 'monthlyamount_mean', 'first_trxdate', 'last_trxenddate', 
        'trx_details_status_mode', 'unique_trxtypes', 'transaction_count','downpayment'
    ]

    # Display the aggregated data
    trxs_agg = trxs_agg.round(0)

    # Step 1: Merge table1 and table2 on 'api_phone_number'
    merged_data = pd.merge(customer_level_data, customers_data, on='api_phone_number', how='inner')

    # Step 2: Merge the result with table3 on 'api_phone_number'
    merged_data = pd.merge(merged_data, trxs_agg, on='api_phone_number', how='inner')

    # Convert birthdate to datetime format
    merged_data['birthdate'] = pd.to_datetime(merged_data['birthdate'], format='%m/%d/%Y %I:%M:%S %p')

    # Calculate age in years
    today = pd.to_datetime('today')
    merged_data['age'] = (today - merged_data['birthdate']).dt.days // 365  # Approximate age in years

    merged_data.loc[merged_data["n_months_default_max"] == 0, "repayment_status"] = "days_delay"
    merged_data.loc[merged_data["n_months_default_max"].isin([1]), "repayment_status"] = "late"
    merged_data.loc[merged_data["n_months_default_max"].isin([2,3,4,5,6]), "repayment_status"] = "default"
    merged_data.loc[merged_data["n_months_default_max"]>7 , "repayment_status"] = "default"
    merged_data.loc[merged_data["n_months_default_max"].isnull(), "repayment_status"] = "clean"

    needed  = merged_data[['api_phone_number','nationalid','totalamount_sum_x','totalamount_max_x','n_months_default_max','transaction_count_x','months_max',
                'transaction_count_y','perc_months_default','downpayment','repayment_status']]
    return needed

def merged_data():
    df = process_data()
    default = transactions()
    all_data = pd.merge(default, df, left_on='api_phone_number', right_on='number',how='inner')
    return all_data
# print(df)
