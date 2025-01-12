import streamlit as st
import requests
import uuid
import pandas as pd
import plotly.express as px
import random
from datetime import datetime, timedelta

# Constants
WEBHOOK_URL = st.secrets["WEBHOOK_URL"] 
BEARER_TOKEN = st.secrets["BEARER_TOKEN"] 

def generate_session_id():
    return str(uuid.uuid4())

def send_message_to_llm(session_id, message):
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "sessionId": session_id,
        "chatInput": message
    }
    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
    #print (response.json())
    if response.status_code == 200:
        return response.json()["output"]
    else:
        return f"Error: {response.status_code} - {response.text}"

class Dashboard:
    def __init__(self):
        self.df = self.generate_mock_data()

    def generate_mock_data(self):
        # Generate mock data for the dashboard
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        data = {
            'Date': dates,
            'Queries': [random.randint(50, 200) for _ in range(30)],
            'Response_Time': [random.uniform(0.5, 3.0) for _ in range(30)],
            'Satisfaction': [random.uniform(4.0, 5.0) for _ in range(30)]
        }
        return pd.DataFrame(data)

    def display_metrics(self):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Daily Queries", f"{self.df['Queries'].iloc[-1]}")
        with col2:
            st.metric("Avg Response Time", f"{self.df['Response_Time'].iloc[-1]:.2f}s")
        with col3:
            st.metric("User Satisfaction", f"{self.df['Satisfaction'].iloc[-1]:.1f}/5.0")

    def display_charts(self):
        # Queries over time
        fig_queries = px.line(self.df, x='Date', y='Queries', 
                            title='Daily Queries Trend')
        st.plotly_chart(fig_queries, use_container_width=True)

        # Response time trend
        fig_response = px.line(self.df, x='Date', y='Response_Time',
                             title='Response Time Trend')
        st.plotly_chart(fig_response, use_container_width=True)

def main():
    st.title("FinRAGas - Lietuvos Banko Sprendimų Asistentas")
    st.markdown("*Išmanus draudimo sprendimų paieškos įrankis*")

    # Create dashboard
    st.subheader("Dashboard")
    dashboard = Dashboard()
    dashboard.display_metrics()
    dashboard.display_charts()

    # Chat interface below dashboard
        # Initialize session state
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "session_id" not in st.session_state:
            st.session_state.session_id = generate_session_id()

        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # User input
        user_input = st.chat_input("Type your message here...")
     
        if user_input:
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)

            # Get LLM response with spinner on while waiting
            with st.spinner('Sekundėlę ...'):
                llm_response = send_message_to_llm(st.session_state.session_id, user_input)
            
            # Add LLM response to chat history
            st.session_state.messages.append({"role": "assistant", "content": llm_response})
            
            with st.chat_message("assistant"):
                st.write(llm_response)

if __name__ == "__main__":
    main()
