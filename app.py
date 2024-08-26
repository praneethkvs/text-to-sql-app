#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 24 15:01:33 2024

@author: praneeth
"""

#To run App open a terminal, navigate to directory where the .py file is  
#and run  python -m streamlit run app.py

import streamlit as st
import pandas as pd

import sqlite3
from sqlalchemy import create_engine 

from langchain_community.utilities import SQLDatabase
from langchain.agents import create_sql_agent
from langchain_openai import ChatOpenAI

openai_api_key = st.secrets["openai_key"]

# Streamlit app layout
st.title("Text-to-SQL Agent to chat with your Data:")
st.markdown("*For this prototype app, we will be using CSV Files to create the Database,  \n you can modify the code to Connect to a database of your choice.*")
st.markdown("**Step -1:** Upload CSV Files of data, where each file corresponds to a table.  \nYou can use Sample Data Files and Sample Questions Provided [Here.](https://github.com/praneethkvs/text_to_sql_bot)  \n**Step -2:** Once files are successfully uploaded, you should see first 5 rows of data in the tables,    \nEnter your Query in the space provided and hit Submit Query.")




# Function to upload and display files
def upload_files():
    uploaded_files = st.file_uploader("Choose CSV files", type="csv", accept_multiple_files=True)
    
    if uploaded_files:
        tables = []
        for file in uploaded_files:
            df = pd.read_csv(file)
            df.to_sql(file.name.split('.')[0], engine, index=False, if_exists='replace')
            st.write(f"Table from file **{file.name}**:")
            st.dataframe(df.head(5))
            tables.append(file.name.split('.')[0])
        return tables
    return []

# # Create an in-memory SQLite database and engine
conn = sqlite3.connect(":memory:")
engine = create_engine('sqlite:///:memory:')


# Upload files and display tables
tables = upload_files()


# # Initialize the SQLDatabase object
db = SQLDatabase(engine)
# # Initialize the OpenAI LLM
llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo-0125", openai_api_key=openai_api_key )
# # Create the SQL agent
sql_agent = create_sql_agent(llm=llm, db=db, verbose=True, agent_type="zero-shot-react-description")



# Input prompt and get response
if tables:
    prompt = st.text_area("Enter your query:", 
                           value="What is the Total number of Unique Transactions, Senders and Recipients with Successful transactions ?",
                           height = 100)
    if st.button("Submit Query"):
        if prompt:
            response = sql_agent.run(prompt)
            st.write("**Response from SQL agent:**")
            st.write(response)
        else:
            st.write("Please enter a query.")

