# streamlit run streamlit_app.py --server.enableCORS false --server.enableXsrfProtection false --server.address 0.0.0.0 --server.port 8501 --server.headless true


import streamlit as st
import hashlib
import importlib

# Initialize session state for login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def check_password(username, password):
    try:
        stored_users = st.secrets["credentials"]["usernames"]
        if username in stored_users and stored_users[username] == make_hash(password):
            return True
    except Exception as e:
        st.error(f"Error checking credentials: {e}")
    return False

def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def login_form():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if check_password(username, password):
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.rerun()
        else:
            st.error("Invalid username or password")
    # col1, col2, col3 = st.columns([1,2,1])
    # with col2:

def main_app():
    st.set_page_config(
        page_title="Rule Creator App",
        layout="wide",
    )

    st.title("Scoring App")

    # Add logout button in sidebar
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    # Create tabs first
    tab1, tab2, tab3, tab4 = st.tabs(["Score_weights", "Score_card", "Rule_creation", "Rule_editor"])

    # Execute in tabs using try-except for better error handling
    with tab1:
        try:
            import Scoring_streamlit
            # importlib.reload(Scoring_streamlit)  # Reload the module
            Scoring_streamlit.main()  # Assuming there's a main() function
        except Exception as e:
            st.error(f"Error in Score_weights tab: {str(e)}")

    with tab2:
        try:
            import streamlit_score_card
            # importlib.reload(streamlit_score_card)
            streamlit_score_card.main()
        except Exception as e:
            st.error(f"Error in Score_card tab: {str(e)}")

    with tab3:
        try:
            import Rule_creation
            # importlib.reload(Rule_creation)
            Rule_creation.main()  # Assuming there's a main() function
        except Exception as e:
            st.error(f"Error in Rule_creation tab: {str(e)}")

    with tab4:
        try:
            import rule_editor
            # importlib.reload(rule_editor)
            rule_editor.edit_rule_interface()
        except Exception as e:
            st.error(f"Error in Rule_editor tab: {str(e)}")

if __name__ == "__main__":
    if not st.session_state['logged_in']:
        login_form()
    else:
        main_app()