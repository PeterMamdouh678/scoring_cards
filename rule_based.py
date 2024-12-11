import mysql.connector
from mysql.connector import Error
import pymysql
from sqlalchemy import create_engine
import numpy as np
import pandas as pd
pd.set_option('display.max_columns', None)
from datetime import datetime
import json
from db_connect import merged_data
import streamlit as st

# test_df = data.copy()
# Connection parameters
def get_rules():
    rule_based = st.secrets['rule_based']
    DB_USERNAME = rule_based['DB_USERNAME']
    DB_PASSWORD = rule_based['DB_PASSWORD']
    DB_HOST = rule_based['DB_HOST']
    DB_PORT = rule_based['DB_PORT']
    DB_NAME = rule_based['DB_NAME']

    # Create the connection engine
    engine = create_engine(f'mysql+mysqlconnector://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
    # Connect to the database
    conn = engine.connect()

    sql = """
    select *
    FROM business_rules
    """
    # conn = mysql.connector.connect(database='zoho', password='Youssef123$', 
    #                         host='adva-warehouse.c45dykr9xlqi.eu-west-3.rds.amazonaws.com', port='3306',user='admin')


    df = pd.read_sql(sql, conn)
    return df


def apply_actions(group, actions):
    """Apply actions to a DataFrame group."""
    for action_data in actions:
        action = action_data['action']
        field = action_data['field']
        value = action_data['value']

        if action in ["change_data_record", "add_data_record"]:
            group[field] = value

        elif action == "proceed_to_next_step":
            continue

        else:
            group['status'] = action

    return group

def process_group_conditions(conditions,test_df):
    """Process and combine conditions within a group."""
    int_Operator = {'EQUALS': "==",
        'NOT_EQUALS' : "!=", 
        "GREATER_THAN" : ">",
        "LESS_THAN" : "<",
        "GREATER_EQUAL" : ">=",
        "LESS_EQUAL" : "<=",
        "CONTAINS" : "IN",
        "NOT_CONTAINS": "NOT IN"
        }
    group_condition = None

    for cond in conditions:
        column = cond['field']
        operator = int_Operator.get(cond['operator'])
        value = cond['value']
        relation = cond.get('relation_next_condition')  # AND/OR within the group

        # Create filter condition
        if operator == "IN":
            filter_condition = test_df[column].isin([value])
        elif operator == "NOT IN":
            filter_condition = ~test_df[column].isin([value])
        else:
            value = float(value)
            filter_condition = eval(f"test_df[column] {operator} {value!r}")

        # Combine conditions within the group
        if group_condition is None:
            group_condition = filter_condition
        elif relation == "AND":
            group_condition &= filter_condition
        elif relation == "OR":
            group_condition |= filter_condition


    return group_condition

# def rule_check(df)
def rule_check(test_df):
    df = get_rules()
    for rule_idx, rule_data in df.iterrows():
        one_rule = rule_data.to_frame().T.reset_index()

        # Parse JSON fields
        grouped_conditions = json.loads(one_rule['condition_groups'].iloc[0])
        true_actions = json.loads(one_rule['true_actions'].iloc[0])
        false_actions = json.loads(one_rule['false_actions'].iloc[0])

        final_condition = None  # To hold the cumulative condition across groups

        for group_idx, group in enumerate(grouped_conditions):
            # Process conditions within the group
            group_conditions = process_group_conditions(group['grouped_conditions'],test_df)

            # Combine group conditions using operator_next_group
            operator_prev_group = group.get('operator_prev_group')  # AND/OR between groups
            if final_condition is None:
                final_condition = group_conditions
            elif operator_prev_group == "AND":
                final_condition &= group_conditions
            elif operator_prev_group == "OR":
                final_condition |= group_conditions

        # Apply the final condition to the DataFrame
        if final_condition is not None:
            true_group = test_df[final_condition].copy()
            false_group = test_df[~final_condition].copy()

            # Apply actions to true and false groups
            true_group = apply_actions(true_group, true_actions)
            # print()
            false_group = apply_actions(false_group, false_actions)

            st.write(f"actions applied for rule {one_rule['name'][0]}.")
            # st.write(f"False group actions applied for rule {one_rule['name'][0]}.")

    return true_group, false_group
