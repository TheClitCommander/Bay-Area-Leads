import streamlit as st

st.title("MidcoastLeads Simple Test")
st.write("If you can see this, Streamlit is working correctly!")

# Add a simple chart
import pandas as pd
import numpy as np

chart_data = pd.DataFrame(
    np.random.randn(20, 3),
    columns=['Property Value', 'ML Score', 'Lead Score'])

st.line_chart(chart_data)

# Add a simple input
name = st.text_input("Enter your name")
if name:
    st.write(f"Hello, {name}!")
