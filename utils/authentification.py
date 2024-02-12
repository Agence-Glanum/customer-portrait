import os
import streamlit as st
from dotenv import load_dotenv


load_dotenv()
data_username = os.environ.get('DATA_USERNAME')
data_password = os.environ.get('DATA_PASSWORD')
marketing_username = os.environ.get('MARKETING_USERNAME')
marketing_password = os.environ.get('MARKETING_PASSWORD')


def get_user_type():
    if 'user_type' not in st.session_state:
        st.session_state.user_type = None
    return st.session_state.user_type


def set_user_type(user_type):
    st.session_state.user_type = user_type


def authenticate(username, password):
    if (username == data_username) & (password == data_password):
        return 'data'
    elif (username == marketing_username) & (password == marketing_password):
        return 'marketing'
    else:
        return None


def get_auth_status():
    if 'auth_status' not in st.session_state:
        st.session_state.auth_status = False
    return st.session_state.auth_status


def set_auth_status(status):
    st.session_state.auth_status = status


def render_login_form():
    placeholder = st.empty()
    with placeholder.form('authentifiation'):
        username = st.text_input('Username')
        password = st.text_input('Password', type='password')
        login = st.form_submit_button('Login')
    if login:
        auth_result = authenticate(username, password)
        if auth_result:
            placeholder.empty()
            set_auth_status(True)
            set_user_type(auth_result)
            return auth_result
        else:
            st.write('Wrong username or password !')
            st.stop()
    return None


def logout():
    set_auth_status(False)
    set_user_type(None)
