import requests
import streamlit as st
import json

@st.cache_data()
def search(query):
    base_url = st.secrets["BASE_URL"]
    r = requests.get(base_url + "?query=" + query)

    return json.loads(r.text)

