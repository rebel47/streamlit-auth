import yaml
import streamlit as st
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities import (CredentialsError,
                                               ForgotError,
                                               Hasher,
                                               LoginError,
                                               RegisterError,
                                               ResetError,
                                               UpdateError)

# Loading config file
with open('config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Display logo and version
st.metric('Version', '0.4.1')

# Display credentials (for debugging purposes)
st.code(f"""
Credentials:

First name: {config['credentials']['usernames']['jsmith']['first_name']}
Last name: {config['credentials']['usernames']['jsmith']['last_name']}
Username: jsmith
Password: {'abc' if 'pp' not in config['credentials']['usernames']['jsmith'].keys() else config['credentials']['usernames']['jsmith']['pp']}

First name: {config['credentials']['usernames']['rbriggs']['first_name']}
Last name: {config['credentials']['usernames']['rbriggs']['last_name']}
Username: rbriggs
Password: {'def' if 'pp' not in config['credentials']['usernames']['rbriggs'].keys() else config['credentials']['usernames']['rbriggs']['pp']}
"""
)

# Creating the authenticator object
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Creating a login widget
try:
    name, authentication_status, username = authenticator.login('Login', 'main')
except LoginError as e:
    st.error(e)

# Check authentication status
if st.session_state.get("authentication_status"):
    st.write('___')
    authenticator.logout('Logout', 'main')
    st.write(f'Welcome *{st.session_state["name"]}*')
    st.title('Some content')
    st.write('___')
elif st.session_state.get("authentication_status") is False:
    st.error('Username/password is incorrect')
elif st.session_state.get("authentication_status") is None:
    st.warning('Please enter your username and password')

# Creating a password reset widget
if st.session_state.get("authentication_status"):
    try:
        if authenticator.reset_password(username):
            st.success('Password modified successfully')
            with open('config.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(config, file, default_flow_style=False)
    except ResetError as e:
        st.error(e)
    except CredentialsError as e:
        st.error(e)
    st.write('_If you use the password reset widget, please revert the password to what it was before once you are done._')

# Creating a new user registration widget
try:
    (email_of_registered_user,
     username_of_registered_user,
     name_of_registered_user) = authenticator.register_user('Register user', preauthorization=False)
    if email_of_registered_user:
        st.success('User registered successfully')
        with open('config.yaml', 'w', encoding='utf-8') as file:
            yaml.dump(config, file, default_flow_style=False)
except RegisterError as e:
    st.error(e)

# Creating a forgot password widget
try:
    (username_of_forgotten_password,
     email_of_forgotten_password,
     new_random_password) = authenticator.forgot_password('Forgot password')
    if username_of_forgotten_password:
        st.success(f"New password **'{new_random_password}'** to be sent to user securely")
        config['credentials']['usernames'][username_of_forgotten_password]['password'] = stauth.Hasher([new_random_password]).generate()[0]
        with open('config.yaml', 'w', encoding='utf-8') as file:
            yaml.dump(config, file, default_flow_style=False)
    elif not username_of_forgotten_password:
        st.error('Username not found')
except ForgotError as e:
    st.error(e)

# Creating a forgot username widget
try:
    (username_of_forgotten_username,
     email_of_forgotten_username) = authenticator.forgot_username('Forgot username')
    if username_of_forgotten_username:
        st.success(f"Username **'{username_of_forgotten_username}'** to be sent to user securely")
    elif not username_of_forgotten_username:
        st.error('Email not found')
except ForgotError as e:
    st.error(e)

# Creating an update user details widget
if st.session_state.get("authentication_status"):
    try:
        if authenticator.update_user_details(username):
            st.success('Entries updated successfully')
            with open('config.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(config, file, default_flow_style=False)
    except UpdateError as e:
        st.error(e)