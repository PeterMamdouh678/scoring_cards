import streamlit as st
import pandas as pd
import uuid
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

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
#         max-width: 900px;  /* Set the desired maximum width */
#         margin: 0 auto;     /* Center the content */
#         padding: 20px;      /* Optional: add padding for better appearance */
#     }
#     </style>
#     """,
#     unsafe_allow_html=True
# )

# Constants from original script
table_columns = {
    "customers": {
        "name": "Customers",
        "columns": [
            'n_months_default_max', 'perc_months_default',
            'downpayment', 'repayment_status',
            'Remaining Limit', 'car_brand', 'car_model', 'car_manfucture_year',
            'Club Name', 'Age', 'Marital Status', 'NID Area', 'NID City',
            'NID Occupation', 'Number Of Dependents', 'employment_type',
            'Total Income', 'debt_level',"category","status"
        ]
    }
}

logical_operators = ['AND','OR']

int_Operator = {
    'EQUALS': "=", 'NOT_EQUALS': "!=", 
    "GREATER_THAN": ">", "LESS_THAN": "<",
    "GREATER_EQUAL": ">=", "LESS_EQUAL": "<=",
    "CONTAINS": "IN", "NOT_CONTAINS": "NOT IN"
}

Actions = ["proceed_to_next_step", "change_data_record",
           "add_data_record", "Auto-Reject", "Auto_approve"]


def create_database_engine():
    """Create SQLAlchemy database engine."""
    # Database connection details
    DB_USERNAME = 'admin'
    DB_PASSWORD = 'Youssef123$'
    DB_HOST = 'adva-warehouse.c45dykr9xlqi.eu-west-3.rds.amazonaws.com'
    DB_PORT = '3306'
    DB_NAME = 'Rule_based'

    DATABASE_URL = f'mysql+mysqlconnector://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    try:
        return create_engine(DATABASE_URL, echo=False)
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

@st.cache_data
def fetch_business_rules():
    """Fetch all business rules from the database."""
    engine = create_database_engine()
    if not engine:
        return pd.DataFrame()
    
    try:
        with engine.connect() as connection:
            query = text("SELECT * FROM business_rules")
            # print(query)
            result = connection.execute(query)
            # print(result)
            columns = result.keys()
            
            rules = []
            for row in result:
                print("============")
                print("row : ",row)
                rule = dict(zip(columns, row))
                print("rule: ",rule)
                rule['condition_groups'] = json.loads(rule['condition_groups'])
                rule['true_actions'] = json.loads(rule['true_actions'])
                rule['false_actions'] = json.loads(rule['false_actions'])
                rules.append(rule)
            
            return pd.DataFrame(rules)
    except Exception as e:
        st.error(f"Error fetching business rules: {e}")
        return pd.DataFrame()

def update_business_rule(rule_id, updated_rule_data):
    """Update a specific business rule in the database."""
    engine = create_database_engine()
    if not engine:
        st.error("Could not establish database connection.")
        return False
    
    try:
        with engine.begin() as connection:
            update_query = text("""
                UPDATE business_rules 
                SET name = :name, 
                    description = :description, 
                    priority = :priority, 
                    condition_groups = :condition_groups, 
                    true_actions = :true_actions, 
                    false_actions = :false_actions, 
                    enabled = :enabled
                WHERE id = :id
            """)
            connection.execute(update_query, {
                'id': rule_id,
                'name': updated_rule_data['name'],
                'description': updated_rule_data['description'],
                'priority': updated_rule_data['priority'],
                'condition_groups': json.dumps(updated_rule_data['condition_groups']),
                'true_actions': json.dumps(updated_rule_data['true_actions']),
                'false_actions': json.dumps(updated_rule_data['false_actions']),
                'enabled': updated_rule_data['enabled']
            })
        
        st.success("Rule updated successfully!")
        return True
    except Exception as e:
        st.error(f"Error updating rule: {e}")
        return False

def edit_condition(condition, group_index, condition_index,conditions):
    """Edit a single condition within a condition group."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        table = st.selectbox(
            "Table", 
            list(table_columns.keys()), 
            index=list(table_columns.keys()).index(condition['table']),
            key=f"table_{group_index}_{condition_index}"
        )
    
    with col2:
        field = st.selectbox(
            "Field", 
            table_columns[table]['columns'], 
            index=table_columns[table]['columns'].index(condition['field']),
            key=f"field_{group_index}_{condition_index}"
        )
    
    with col3:
        operator = st.selectbox(
            "Operator", 
            list(int_Operator.keys()),
            index=list(int_Operator.keys()).index(condition['operator']),
            key=f"operator_{group_index}_{condition_index}"
        )
    
    with col4:
        value = st.text_input(
            "Value *", 
            value=condition['value'],
            key=f"value_{group_index}_{condition_index}"
        )
    
    # Relation to next condition (for all but last condition)
    relation = None
    # if condition_index < len(st.session_state.current_rule['condition_groups'][group_index]['grouped_conditions']) - 1:
    if condition_index < conditions - 1:

        relation = st.selectbox(
            "Relation to Next Condition", 
            logical_operators,
            index=logical_operators.index(condition['relation_next_condition']) if condition['relation_next_condition'] in logical_operators else 0,
            key=f"relation_{group_index}_{condition_index}"
        )
    # st.write("conditions: ", conditions)
    
    return {
        "table": table,
        "field": field,
        "operator": operator,
        "value": value,
        "relation_next_condition": relation
    }


def edit_action(action, action_index, action_type):

    """Edit a single action with robust dynamic column selection."""
    col1, col2, col3, col4 = st.columns(4)
    print("action_index inside diff : ", action_index)
    
    with col1:
        # Safely select action with robust index handling
        current_action = action.get('action', Actions[0])
        selected_action = st.selectbox(
            "Action Type", 
            Actions,
            index=max(0, Actions.index(current_action)) if current_action in Actions else 0,
            key=f"{action_type}_action_{action_index}"
        )
        # print("selected actions : ", selected_action)
        # st.write("selected actions : ", selected_action     )
    
    # Initialize variables
    table, field, value = None, None, None
    
    # Dynamic fields for record-related actions
    if selected_action in ['change_data_record', 'add_data_record']:
        with col2:
            # Safer table selection with fallback
            available_tables = list(table_columns.keys())
            current_table = action.get('table', available_tables[0])
            table = st.selectbox(
                "Table", 
                available_tables, 
                index=max(0, available_tables.index(current_table)) if current_table in available_tables else 0,
                key=f"{action_type}_table_{action_index}"
            )
        
        if table:  # Only show fields if a table is selected
            with col3:
                # Dynamic field selection based on selected table
                table_columns_list = table_columns.get(table, {}).get('columns', [])
                current_field = action.get('field', table_columns_list[0] if table_columns_list else None)
                
                field = st.selectbox(
                    "Field", 
                    table_columns_list, 
                    index=max(0, table_columns_list.index(current_field)) if current_field in table_columns_list else 0,
                    key=f"{action_type}_field_{action_index}"
                )
            
            with col4:
                value = st.text_input(
                    "Value *", 
                    value=action.get('value', ''),
                    key=f"{action_type}_value_{action_index}"
                )
    
    return {
        "action": selected_action,
        "table": table,
        "field": field,
        "value": value,
        "status": selected_action if selected_action in ["proceed_to_next_step", "Auto-Reject", "Auto_approve"] else None
    }
    
def edit_rule_interface():
    st.title("Advanced Business Rules Editor")

    
    # Fetch rules
    rules_df = fetch_business_rules()
    
    if rules_df.empty:
        st.warning("No rules found in the database.")
        return
    
    # Select rule to edit
    selected_rule_id = st.selectbox(
        "Select Rule to Edit", 
        rules_df['id'], 
        format_func=lambda x: rules_df[rules_df['id'] == x]['name'].values[0]
    )
    
    # Get selected rule details
    selected_rule = rules_df[rules_df['id'] == selected_rule_id].iloc[0]
    
    # Store current rule in session state for use in edit functions
    st.session_state.current_rule = selected_rule
    
    # Edit form
    # with st.form("edit_rule_form"):
    st.subheader("Basic Rule Information")
    rule_name = st.text_input("Rule Name *", value=selected_rule['name'])
    rule_description = st.text_area("Rule Description.", value=selected_rule['description'])
    rule_priority = st.number_input("Rule Priority", value=selected_rule['priority'])
    rule_enabled = st.checkbox("Rule Enabled.", value=selected_rule['enabled'])
    
    # Condition Groups Editing
    st.subheader("Condition Groups")
    edited_condition_groups = []
    # print("selected_rule['condition_groups']", )
    # groups = 
    groups_num = len(selected_rule['condition_groups'])
    groups= st.number_input("Number of Condition Groups.", min_value=1, value=groups_num)

    if groups > groups_num:
        diff = groups - groups_num
        # print("diff : ",diff)
        for d in range(diff):
            # print(d)
            new_condition_group = {
            'grouped_conditions': [
                {
                    'table': "customers",
                    'field': "n_months_default_max",
                    'operator': "EQUALS",
                    'value': None,
                    'relation_next_condition': None
                }
            ],
            'operator_prev_group': None
            }
            selected_rule['condition_groups'].append(new_condition_group)
    elif groups < groups_num:
        selected_rule['condition_groups'].pop()


    # print("selected_rule['condition_groups']: ",selected_rule['condition_groups'])

    
    for group_index, group in enumerate(selected_rule['condition_groups']):
        # print("group index: ", group_index)
        st.divider()
        st.markdown(f"### Condition Group {group_index + 1}")
        
        # Group operator (for multi-group rules)
        if group_index > 0:
            group_operator = st.selectbox(
                f"Operator with Previous Group.", 
                logical_operators,
                index=logical_operators.index(group['operator_prev_group']) if group['operator_prev_group'] in logical_operators else 0,
                key=f"group_op__{group_index}"
            )
        else:
            group_operator = None
        

        # Edit conditions within the group
        edited_conditions = []
        # print("len : ",len(group['grouped_conditions']))
        conditions= st.number_input(f"Number of Condition in Group {group_index + 1}", min_value=1, value=len(group['grouped_conditions']))

        while conditions < len(group['grouped_conditions']):
            # for _ in range(conditions - len(group['grouped_conditions']) ):
            group['grouped_conditions'].pop()

        for condition_index, condition in enumerate(group['grouped_conditions']):
            # print("conditon:",condition_index)
            edited_condition = edit_condition(condition, group_index, condition_index,conditions)
            edited_conditions.append(edited_condition)

        if conditions > len(group['grouped_conditions']):
            num_diff = conditions - len(group['grouped_conditions'])
            # print("num_diff: ",num_diff)

            for i in range(num_diff):
                i = i+1
                # print("condition_index:",i)
                condition = edit_condition(condition, group_index, condition_index+i,conditions)
                edited_conditions.append(condition)


        print("conditions : ", group['grouped_conditions'])
        # add_condition = st.button("add condition")
        edited_condition_groups.append({
            "grouped_conditions": edited_conditions,
            "operator_prev_group": group_operator
        })
    
    # True Actions Editing
    st.divider()
    st.subheader("True Actions")
    edited_true_actions = []
    
    true_actions= st.number_input("Number of true actions", min_value=1, value= len(selected_rule['true_actions']) )
    if true_actions < len(selected_rule['true_actions']):
        selected_rule['true_actions'].pop()
        
    for action_index, action in enumerate(selected_rule['true_actions']):
        # print("action : ", action)
        edited_action = edit_action(action, action_index, "true")
        edited_true_actions.append(edited_action)

    if true_actions > len(selected_rule['true_actions']):
        num_diff2 = true_actions - len(selected_rule['true_actions'])
        # print("num_diff2: ",num_diff2)

        for z in range(num_diff2):
            z = z+1
            # print("condition_index:",i)
            print("action_index  ",action_index)
            print("i:",z)
            edited_action = edit_action(action, action_index+z, "true")
            edited_true_actions.append(edited_action)
            # edited_true_actions = st.session_state.edited_true_actions
        
    # False Actions Editing
    st.divider()
    st.subheader("False Actions")
    edited_false_actions = []

    fasle_actions= st.number_input("Number of flase actions", min_value=1, value= len(selected_rule['false_actions']) )
    if fasle_actions < len(selected_rule['false_actions']):
        selected_rule['false_actions'].pop()

    for action_index, action in enumerate(selected_rule['false_actions']):
        edited_action = edit_action(action, action_index, "false")
        edited_false_actions.append(edited_action)
    
    if fasle_actions > len(selected_rule['false_actions']):
        num_diff3 = fasle_actions - len(selected_rule['false_actions'])
        # print("num_diff3: ",num_diff3)

        for y in range(num_diff3):
            y = y+1
            # print("condition_index:",i)
            print("action_index  ",action_index)
            print("i:",y)
            edited_action = edit_action(action, action_index+y, "false")
            edited_false_actions.append(edited_action)
    
    # Submit button
    submit = st.button("Update Rule")
    
    if submit:
        updated_rule_data = {
            'name': rule_name,
            'description': rule_description,
            'priority': rule_priority,
            'condition_groups': edited_condition_groups,
            'true_actions': edited_true_actions,
            'false_actions': edited_false_actions,
            'enabled': rule_enabled
        }
        
        update_business_rule(selected_rule_id, updated_rule_data)

# Run the app
if __name__ == "__main__":
    edit_rule_interface()