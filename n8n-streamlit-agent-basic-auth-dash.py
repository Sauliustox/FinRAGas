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
        response = self.supabase.table('lb_docs_processed').select('*').execute()
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
        
        # Select and rename relevant columns
        df = df[['Date', 'doc_id', 'company_name', 'decision', 'product', 'LB_complaint_case', 'decision_date']]
        
        # Sort by date
        df = df.sort_values('Date', ascending=False)
        
        return df

    def display_metrics(self):
        # Calculate summary metrics
        total_docs = len(self.df)
        unique_companies = self.df['company_name'].nunique()
        latest_date = self.df['Date'].max().strftime('%Y-%m-%d')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Documents", f"{total_docs}")
        with col2:
            st.metric("Unique Companies", f"{unique_companies}")
        with col3:
            st.metric("Latest Update", f"{latest_date}")

    def display_charts(self):
        # Display recent documents table
        # st.subheader("Recent Documents")
        # st.dataframe(
        #     self.df.rename(columns={
        #         'Date': 'Data',
        #         'doc_id': 'Dokumento ID',
        #         'company_name': 'Įmonė',
        #         'decision': 'Sprendimas',
        #         'product': 'Produktas',
        #         'LB_complaint_case': 'Bylos Nr.',
        #         'decision_date': 'Sprendimo data'
        #     }),
        #     hide_index=True
        # )

        # Documents by company chart
        docs_by_company = self.df['company_name'].value_counts().head(10)
        fig_company = px.bar(
            x=docs_by_company.values,
            y=docs_by_company.index,
            title='Top 10 Companies by Document Count',
            labels={'x': 'Number of Documents', 'y': 'Company'},
            orientation='h'
        )
        st.plotly_chart(fig_company, use_container_width=True)

        # Documents by product type
        docs_by_product = self.df['product'].value_counts().head(10)
        fig_product = px.bar(
            x=docs_by_product.values,
            y=docs_by_product.index,
            title='Top 10 Product Types',
            labels={'x': 'Number of Documents', 'y': 'Product Type'},
            orientation='h'
        )
        # st.plotly_chart(fig_product, use_container_width=True)

        # Monthly documents by company stacked area chart
        df_monthly = self.df.copy()
        df_monthly['Month'] = pd.to_datetime(df_monthly['decision_date']).dt.to_period('M').astype(str)
        monthly_company = pd.crosstab(df_monthly['Month'], df_monthly['company_name'])
        
        fig_monthly = px.bar(
            monthly_company,
            title='Monthly Documents by Company',
            labels={'value': 'Number of Documents', 'Month': 'Month', 'company_name': 'Company'},
            barmode='stack'
        )
        fig_monthly.update_layout(
            xaxis_title="Month",
            yaxis_title="Number of Documents",
            showlegend=True,
            legend_title="Company"
        )
        st.plotly_chart(fig_monthly, use_container_width=True)

def main():
    st.set_page_config(layout="wide")
    _, col2, _ = st.columns([0.1, 0.8, 0.1])
    
    with col2:
        st.title("FinRAGas - Lietuvos Banko Sprendimų Asistentas")
        st.markdown("*Išmanus draudimo sprendimų paieškos įrankis*")

    # Create two columns for dashboard and chat
    _, chat_col, dash_col, _ = st.columns([0.1, 0.3, 0.5, 0.1])

    # Dashboard container on the left
    with dash_col:
        st.subheader("Dashboard")
        dashboard = Dashboard()
        dashboard.display_metrics()
        
        # Charts in expandable section
        with st.expander("Show Charts", expanded=True):
            dashboard.display_charts()

    # Chat interface on the right
    with chat_col:
        
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
