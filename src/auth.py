import streamlit as st
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password():
    """Returns `True` if the user had the correct password."""
    
    # Get credentials from environment variables
    VALID_USERNAME = os.getenv("APP_USERNAME", "admin")
    VALID_PASSWORD_HASH = os.getenv("APP_PASSWORD_HASH", "")
    
    # If no password hash is set, use a default (you should change this!)
    if not VALID_PASSWORD_HASH:
        # Default password: "sanctum2025" (CHANGE THIS!)
        VALID_PASSWORD_HASH = hash_password("sanctum2025")
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if (st.session_state["username"] == VALID_USERNAME and
            hash_password(st.session_state["password"]) == VALID_PASSWORD_HASH):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    # First run, show login form
    if "password_correct" not in st.session_state:
        # Show login form
        st.markdown("## 🔐 Sanctum Login")
        st.text_input(
            "Username", 
            key="username",
            placeholder="Enter username"
        )
        st.text_input(
            "Password", 
            type="password", 
            key="password",
            placeholder="Enter password"
        )
        col1, col2 = st.columns([3, 1])
        with col2:
            st.button("Login", on_click=password_entered)
        
        st.info("💡 Contact your church admin for credentials")
        return False
    
    # Password not correct, show error
    elif not st.session_state["password_correct"]:
        st.markdown("## 🔐 Sanctum Login")
        st.text_input(
            "Username", 
            key="username",
            placeholder="Enter username"
        )
        st.text_input(
            "Password", 
            type="password", 
            key="password",
            placeholder="Enter password"
        )
        col1, col2 = st.columns([3, 1])
        with col2:
            st.button("Login", on_click=password_entered)
        st.error("😕 Incorrect username or password")
        return False
    
    # Password correct
    else:
        return True

def logout():
    """Logout the current user"""
    if "password_correct" in st.session_state:
        del st.session_state["password_correct"]
    st.rerun()

# Utility function to generate password hash
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        password = sys.argv[1]
        print(f"Password hash for '{password}': {hash_password(password)}")
        print(f"Add this to your .env file:")
        print(f"APP_PASSWORD_HASH={hash_password(password)}")
    else:
        print("Usage: python auth.py <password>")
        print("This will generate a password hash to put in your .env file")