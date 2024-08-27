#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 24 15:01:33 2024

@author: praneeth
"""

#To run App open a terminal, navigate to directory where the .py file is  
#and run  python -m streamlit run app.py

import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd

import sqlite3
from sqlalchemy import create_engine 

from langchain_community.utilities import SQLDatabase
from langchain.agents import create_sql_agent
from langchain_openai import ChatOpenAI

from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import AgentAction

openai_api_key = st.secrets["openai_key"]

# Streamlit app layout
st.title("Text-to-SQL Agent to chat with your Data:")
st.markdown("*For this prototype app, we will be using CSV Files to create the Database, you can modify the code to Connect to a database of your choice.  \nNote - Data is sent to openAI, please do not upload any Confidential Data.*")
st.markdown("**Step -1:** Upload CSV Files of data, where each file corresponds to a table. You can use Sample Data Files and Sample Questions Provided [Here.](https://github.com/praneethkvs/text_to_sql_bot)  \n**Step -2:** Once files are successfully uploaded, you should see first 5 rows of data in the tables, Enter your Query in the space provided and hit Submit Query.")



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


#Callback handler to Get SQL Query
class SQLHandler(BaseCallbackHandler):
    def __init__(self):
        self.sql_result = None
        self.sql_result_log = []

    def on_agent_action(self, action: AgentAction, **kwargs):
        #print(f"Action Tool: {action.tool}")
        """Run on agent action. If the tool being used is sql_db_query,
        it means we're submitting the SQL and we can record it as the final SQL."""
        if action.tool == "sql_db_query":
            self.sql_result = action.tool_input
        
        self.sql_result_log.append(action.log)    
            #print(f"SQL Query Captured: {self.sql_result}")

sql_handler = SQLHandler()


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

output_text = ""

# Input prompt and get response
if tables:
    prompt = st.text_area("Enter your query:", 
                           value="What is the Total number of Unique Transactions, Senders and Recipients with Successful transactions ?",
                           height = 100)
    if st.button("Submit Query"):
        if prompt:
            response = sql_agent.run(prompt, callbacks=[sql_handler])
            
            st.write("**Answer:**")
            with st.container():
                st.write(response)
                
            st.write("")  
            st.write("**SQL Query:**")
            st.code(sql_handler.sql_result, language='sql')

            st.write("")  
            st.write("**Steps and Actions taken by the Agent:**")
            for (line,i) in zip(sql_handler.sql_result_log,range(0,len(sql_handler.sql_result_log) + 1)):
                output_text += f"Step - {i+1}:\n{line}\n\n"
            st.text(output_text)
            
        else:
            st.write("Please enter a query.")

