import streamlit as st
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Text, JSON, Boolean, DateTime, select
from sqlalchemy.orm import sessionmaker
# from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import SQLAlchemyError
import mysql.connector
from mysql.connector import Error
import pymysql
import numpy as np
import json
pd.set_option('display.max_columns', None)

# Set the page configuration with a centered layout
# st.set_page_config(
#     page_title="Rule Creator App",
#     layout="centered",  # You can use "centered" for a more constrained default
# )

# # Inject custom CSS for a custom width
# st.markdown(
#     """
#     <style>
#     .block-container {
#         max-width: 1000px;  /* Set the desired maximum width */
#         margin: 0 auto;     /* Center the content */
#         padding: 20px;      /* Optional: add padding for better appearance */
#     }
#     </style>
#     """,
#     unsafe_allow_html=True
# )
# Database connection details (consider using environment variables in production)
def main():
    rule_based = st.secrets['rule_based']
    DB_USERNAME = rule_based['DB_USERNAME']
    DB_PASSWORD = rule_based['DB_PASSWORD']
    DB_HOST = rule_based['DB_HOST']
    DB_PORT = rule_based['DB_PORT']
    DB_NAME = rule_based['DB_NAME']

    # Database connection string
    DATABASE_URL = f'mysql+mysqlconnector://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'


    # Initiate variables
    table_columns = {
        "customers": {
            "name": "Customers",
            "columns": [
                'n_months_default_max', 'perc_months_default',
                'downpayment', 'repayment_status',
                'Remaining Limit', 'car_brand', 'car_model', 'car_manfucture_year',
                'Club Name', 'Age', 'Marital Status', 'NID Area', 'NID City',
                'NID Occupation', 'Number Of Dependents', 'employment_type',
                'Total Income', 'debt_level',"category","status","skip","Jump to"
            ]
        }
    }

    logical_operators = ['AND','OR']

    int_Operator = {'EQUALS': "=",
            'NOT_EQUALS' : "!=", 
            "GREATER_THAN" : ">",
            "LESS_THAN" : "<",
            "GREATER_EQUAL" : ">=",
            "LESS_EQUAL" : "<=",
            "CONTAINS" : "IN",
            "NOT_CONTAINS": "NOT IN"
            }

    # st_operator = {
    #         "CONTAINS" : "IN",
    #         "NOT_CONTAINS": "NOT IN"
    #         }

    Actions = ["proceed_to_next_step", "change_data_record",
                "add_data_record", "Auto-Reject", "Auto_approve"]


    # def BusinessRule()
    def BusinessRule(
        rule_name: str,
        rule_description: str,
        rule_priority: int,
        condition_groups: List[Dict[str, Any]],
        true_actions: List[Dict[str, Any]],
        false_actions: List[Dict[str, Any]],
        rule_enabled: bool,
        dataframe: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Save a new business rule to the provided DataFrame.

        Args:
            rule_name (str): Name of the rule.
            rule_description (str): Description of the rule.
            rule_priority (int): Priority of the rule.
            condition_groups (List[Dict[str, Any]]): JSON representation of condition groups.
            true_actions (List[Dict[str, Any]]): JSON representation of true actions.
            false_actions (List[Dict[str, Any]]): JSON representation of false actions.
            rule_enabled (bool): Whether the rule is enabled.
            dataframe (pd.DataFrame): Existing DataFrame to which the rule will be added.

        Returns:
            pd.DataFrame: Updated DataFrame containing the new rule.
        """
        new_rule = {
            "id": str(uuid.uuid4()),
            "name": rule_name,
            "description": rule_description,
            "priority": rule_priority,
            "condition_groups": condition_groups,  # Store JSON directly
            "true_actions": true_actions,  # Store JSON directly
            "false_actions": false_actions,  # Store JSON directly
            "enabled": rule_enabled
        }

        # Append the new rule to the DataFrame
        updated_dataframe = pd.concat([dataframe, pd.DataFrame([new_rule])], ignore_index=True)
        return updated_dataframe

    def ConditionGroup( group_conditions, group_operator):
        groups ={
                "grouped_conditions":group_conditions,
                "operator_prev_group":group_operator}
        
        return groups


    def create_condition(group_index: int, condition_index: int):
        condition= {}
        index = condition_index
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            table = st.selectbox(
                "Select Table", 
                list(table_columns.keys()), 
                key=f"table_select_{group_index}_{condition_index}"
            )
        with col2:
            field = st.selectbox(
                "Select Field", 
                table_columns[table]['columns'], 
                key=f"field_select_{group_index}_{condition_index}"
            )
        with col3:
            operator = st.selectbox(
                "Select Operator", 
                # [op.keys() for op in int_Operator], 
                list(int_Operator.keys()),
                key=f"operator_select_{group_index}_{condition_index}"
            )
        with col4:
            value = st.text_input(
                "Enter Value *", 
                key=f"value_input_{group_index}_{condition_index}"
            )
        # if 
        # if index >0:
        #     relation_second_condition = st.selectbox(
        #         "Select Operator with next condition", 
        #     logical_operators, 
        #     key=f"second_relation_{group_index}_{condition_index}")
        # else:
        #     relation_second_condition = None
        
        condition = {
            "table":table,
            "field":field,
            "operator":operator,
            "value":value,
            # "relation_next_condition":relation_second_condition
            }

        return condition

    def create_action(action_index: int, action_group: str):
        table =  None
        field = None
        value = None
        status = None
        action_type = st.selectbox(
            "Select Action Type", 
            Actions, 
            key=f"{action_group}_action_type_select_{action_index}"
        )
        
        if action_type in ['change_data_record', 'add_data_record']:
            col1, col2, col3 = st.columns(3)
            with col1:
                table = st.selectbox(
                    "Select Table", 
                    list(table_columns.keys()), 
                    key=f"{action_group}_action_table_select_{action_index}"
                )
            with col2:
                field = st.selectbox(
                    "Select Field", 
                    table_columns[table]['columns'], 
                    key=f"{action_group}_action_field_select_{action_index}"
                )
            with col3:
                if field in ["skip","Jump to"]:
                    value = st.selectbox(
                    "Select value.", 
                    ["Field Investigation - Home", "Field Investigation - Work", "Field Investigation - Business", "CR Check 1","CR Check 1 & 2"], 
                    key=f"{action_group}_action_value_select_{action_index}"
                )
                else:
                    value = st.text_input(
                        "Enter Value *", 
                        key=f"{action_group}_action_value_input_{action_index}"
                    )
            # st.button("save data")
            # st.write("change the data accordingly")

        elif action_type in ['proceed_to_next_step']:
            # st.success("Proceeding to next step")
            status = "proceed_to_next_step"

        elif action_type in ['Auto-Reject']:
            # st.warning("Application Auto-Rejected")
            status = 'Auto-Reject'

        elif action_type in ['Auto_approve']:
            # st.success("Application Auto-Approved")
            status = 'Auto_approve'

        actions = {"action":action_type,
                "table":table,
                "field":field,
                "value":value,
                "status":status
                }

        return actions


    def validate_rule_data(rule_data):
        """
        Validate the rule data before saving.
        
        Args:
            rule_data (dict): Dictionary containing rule details
        
        Returns:
            tuple: (is_valid, error_messages)
        """
        error_messages = []

        # Validate rule name
        if not rule_data['name'] or rule_data['name'].strip() == '':
            error_messages.append("Rule name cannot be empty")

        # Validate condition groups
        if not rule_data['condition_groups']:
            error_messages.append("At least one condition group is required")
        else:
            for group_index, group in enumerate(rule_data['condition_groups'], 1):
                for condition_index, condition in enumerate(group['grouped_conditions'], 1):
                    # Check if table, field, and value are not empty
                    if not condition.get('table'):
                        error_messages.append(f"Group {group_index}, Condition {condition_index}: Table cannot be empty")
                    if not condition.get('field'):
                        error_messages.append(f"Group {group_index}, Condition {condition_index}: Field cannot be empty")
                    if not condition.get('value', '').strip():
                        error_messages.append(f"Group {group_index}, Condition {condition_index}: Value cannot be empty")

        # Validate actions (if any)
        for action_type in ['true_actions', 'false_actions']:
            for action_index, action in enumerate(rule_data[action_type], 1):
                # If action type requires table/field/value, validate them
                if action['action'] in ['change_data_record', 'add_data_record']:
                    if not action.get('table'):
                        error_messages.append(f"{action_type.replace('_', ' ').title()} Action {action_index}: Table cannot be empty")
                    if not action.get('field'):
                        error_messages.append(f"{action_type.replace('_', ' ').title()} Action {action_index}: Field cannot be empty")
                    if not action.get('value', '').strip():
                        error_messages.append(f"{action_type.replace('_', ' ').title()} Action {action_index}: Value cannot be empty")

        return len(error_messages) == 0, error_messages

    def check_priority_unique(engine, priority):
        """
        Check if the priority is unique in the database.
        
        Args:
            engine: SQLAlchemy database engine
            priority (int): Priority to check
        
        Returns:
            bool: True if priority is unique, False otherwise
        """
        try:
            # Create a session
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Create the metadata and table
            metadata = MetaData()
            rules_table = Table('business_rules', metadata,
                Column('priority', Integer)
            )
            
            # Create a select statement to check for existing priority
            query = select(rules_table.c.priority).where(rules_table.c.priority == priority)
            
            # Execute the query
            result = session.execute(query)
            existing_priorities = result.fetchall()
            
            # Check if priority exists
            return len(existing_priorities) == 0
        
        except SQLAlchemyError as e:
            st.error(f"Database error checking priority: {e}")
            return False
        except Exception as e:
            st.error(f"Unexpected error checking priority: {e}")
            return False

    def create_database_engine():
        """
        Create a SQLAlchemy database engine with error handling.
        
        Returns:
            engine: SQLAlchemy database engine
        """
        try:
            engine = create_engine(DATABASE_URL, echo=False)
            return engine
        except Exception as e:
            st.error(f"Database connection error: {e}")
            return None

    def save_rule_to_database(rule_data):
        """
        Save the business rule to the database with validation.
        
        Args:
            rule_data (dict): Dictionary containing rule details
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        # First, validate the rule data
        is_valid, validation_errors = validate_rule_data(rule_data)
        if not is_valid:
            # Display validation errors
            for error in validation_errors:
                st.error(error)
            return False

        # Get the database engine
        engine = create_database_engine()
        if not engine:
            st.error("Could not establish database connection.")
            return False

        # Check priority uniqueness
        if not check_priority_unique(engine, rule_data['priority']):
            st.error(f"Priority {rule_data['priority']} already exists. Please choose a unique priority.")
            return False

        try:
            # Create a session
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Create the table if it doesn't exist
            metadata = MetaData()
            rules_table = Table('business_rules', metadata,
                Column('id', String(36), primary_key=True),
                Column('name', String(255), nullable=False),
                Column('description', Text),
                Column('priority', Integer, unique=True),
                Column('condition_groups', Text),
                Column('true_actions', Text),
                Column('false_actions', Text),
                Column('enabled', Boolean),
                Column('created_at', DateTime, default=datetime.utcnow)
            )
            
            # Create the table if it doesn't exist
            metadata.create_all(engine)
            
            # Prepare the data for insertion
            insert_data = {
                'id': str(uuid.uuid4()),
                'name': rule_data['name'],
                'description': rule_data['description'],
                'priority': rule_data['priority'],
                'condition_groups': json.dumps(rule_data['condition_groups']),
                'true_actions': json.dumps(rule_data['true_actions']),
                'false_actions': json.dumps(rule_data['false_actions']),
                'enabled': rule_data['enabled']
            }
            
            # Execute the insert
            with engine.begin() as connection:
                connection.execute(rules_table.insert(), insert_data)
            
            return True
        
        except SQLAlchemyError as e:
            st.error(f"Database error: {e}")
            return False
        except Exception as e:
            st.error(f"Unexpected error saving rule: {e}")
            return False
        

    if "rules_df" not in st.session_state:
        st.session_state.rules_df = pd.DataFrame(columns=["id", "name", "description", "priority", "condition_groups", "true_actions", "false_actions", "enabled"])


    # Title
    st.title("Business Rules Creator")

    # Rule Main Info 
    rule_name = st.text_input("name *")
    rule_description = st.text_area("Rule Description")
    rule_priority = st.number_input("Rule Priority *", min_value=1, value=1)
    rule_enabled = st.checkbox("Rule Enabled", value=True)
    st.divider()
    # Condition Groups
    st.subheader("Condition Groups")
    condition_groups = []

    num_groups = st.number_input("Number of Condition Groups", min_value=1, value=1)
    # add_condition = st.button("add")
    for i in range(num_groups):
        st.markdown(f"### Condition Group {i+1}")
        group_conditions = []
        condition_operators = []
        if i == 0:
            group_operator_local = None
        else:
            group_operator_local = st.radio(f"Operator with previous Group", 
                                            logical_operators, 
                                            key=f"group_op_{i}")
        
        num_conditions = st.number_input(f"Number of Conditions in Group {i+1}", 
                                        min_value=1, value=1, key=f"num_cond_{i}")
        
        for j in range(num_conditions):
            # Add operator selection between conditions (except for the first condition)
            
            st.divider()
            
            condition = create_condition(group_index=i, condition_index=j)
            if j == num_conditions-1:
                relation_second_condition = None
                condition['relation_next_condition']=relation_second_condition

            else:
                relation_second_condition = st.selectbox(
                "Select Operator with next condition", 
                    logical_operators, 
                    key=f"second_relation_{i}_{j}")
                condition['relation_next_condition']=relation_second_condition

            group_conditions.append(condition)

        condition_groups.append(
            ConditionGroup(
                group_conditions=group_conditions,
                group_operator=group_operator_local,
            )
        )
            
    # True Actions
    st.divider()
    st.subheader("Actions When Rule is True")
    # num_true_actions = st.number_input("Number of True Actions", min_value=0, value=0)
    num_true_actions = st.number_input("Number of True Actions", min_value=0, value=0)
    true_actions = [create_action(action_index=i, action_group="true") for i in range(num_true_actions)]
    # st.json(true_actions)
    st.divider()

    # False Actions
    st.subheader("Actions When Rule is False")
    num_false_actions = st.number_input("Number of False Actions", min_value=0, value=0)
    false_actions = [create_action(action_index=i, action_group="false") for i in range(num_false_actions)]
    # st.json(false_actions)

    st.divider()    

    new_rule = []
    df = pd.DataFrame(columns=["id", "name", "description", "priority", "condition_groups", "true_actions", "false_actions", "enabled"])
    # Save Rule
    if st.button("Save Rule"):
        # Create the rule data dictionary from the last added rule
        st.session_state.rules_df =  BusinessRule(
            # str(uuid.uuid4()),
            rule_name,
            rule_description,
            rule_priority,
            condition_groups,
            # group_operator=LogicalOperator(group_operator),
            true_actions,
            false_actions,
            rule_enabled,
            st.session_state.rules_df
        )

        if not st.session_state.rules_df.empty:
            last_rule = st.session_state.rules_df.iloc[-1].to_dict()
            st.table(last_rule)
            
            # Prepare rule data for database saving
            rule_data = {
                'name': last_rule['name'],
                'description': last_rule['description'],
                'priority': last_rule['priority'],
                'condition_groups': last_rule['condition_groups'],
                'true_actions': last_rule['true_actions'],
                'false_actions': last_rule['false_actions'],
                'enabled': last_rule['enabled']
            }
            
            # st.table(st.session_state.rules_df)
            # Save to database
            if save_rule_to_database(rule_data):
                st.success("Rule successfully saved to database!")
        else:
            st.error("No rule to save. Please create a rule first.")

if __name__ == "__main__":
    main()