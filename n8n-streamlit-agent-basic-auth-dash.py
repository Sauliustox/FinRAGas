import streamlit as st
import requests
import uuid
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from supabase import create_client

# Constants
WEBHOOK_URL = st.secrets["WEBHOOK_URL"] 
BEARER_TOKEN = st.secrets["BEARER_TOKEN"]
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

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
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.df = self.load_data_from_supabase()

    def load_data_from_supabase(self):
        # Load last 30 days of data from Supabase
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Query Supabase table
        response = self.supabase.table('chat_metrics').select('*')\
            .gte('created_at', start_date.isoformat())\
            .lte('created_at', end_date.isoformat())\
            .execute()
        
        if len(response.data) == 0:
            # Return empty DataFrame with expected columns if no data
            return pd.DataFrame({
                'Date': [],
                'Queries': [],
                'Response_Time': [],
                'Satisfaction': []
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(response.data)
        df['Date'] = pd.to_datetime(df['created_at'])
        
        # Aggregate daily metrics
        daily_metrics = df.groupby('Date').agg({
            'queries': 'sum',
            'response_time': 'mean',
            'satisfaction': 'mean'
        }).reset_index()
        
        # Rename columns to match existing code
        daily_metrics.columns = ['Date', 'Queries', 'Response_Time', 'Satisfaction']
        
        return daily_metrics

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

    # Dashboard container at the top
    with st.container():
        st.subheader("Dashboard")
        dashboard = Dashboard()
        
        # Metrics in columns
        dashboard.display_metrics()
        
        # Charts in expandable section
        st.markdown("""
            <style>
                .dashboard-charts {
                    height: 300px;
                    overflow-y: auto;
                }
            </style>
        """, unsafe_allow_html=True)
        with st.expander("Show Charts", expanded=True):
            with st.container():
                st.markdown('<div class="dashboard-charts">', unsafe_allow_html=True)
                dashboard.display_charts()
                st.markdown('</div>', unsafe_allow_html=True)

    # Chat interface below dashboard
        with st.container():
            st.subheader("Chat")
            # Initialize session state
            if "messages" not in st.session_state:
                st.session_state.messages = []
            if "session_id" not in st.session_state:
                st.session_state.session_id = generate_session_id()

            # Use custom CSS to create scrollable container for chat
            st.markdown("""
                <style>
                    .chat-container {
                        height: 600px;
                        overflow-y: auto;
                    }
                </style>
            """, unsafe_allow_html=True)

            with st.container():
                st.markdown('<div class="chat-container">', unsafe_allow_html=True)
                # Display chat messages
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.write(message["content"])
                st.markdown('</div>', unsafe_allow_html=True)

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
