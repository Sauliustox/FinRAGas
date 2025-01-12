import streamlit as st
import requests
import uuid
from typing import Optional
import time
import pandas as pd
import plotly.express as px
import numpy as np  # Added this import
from datetime import datetime, timedelta

# Rest of the code remains exactly the same
# Custom CSS for both dashboard and chat
st.markdown("""
<style>
/* Dashboard styling */
.dashboard {
    padding: 1rem 0;
    margin-bottom: 2rem;
    border-bottom: 2px solid #f0f0f0;
}
.metric-card {
    background-color: white;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Chat styling */
[data-testid="stChatMessage"] {
    display: flex;
    flex-direction: row;
    align-items: flex-start;
    justify-content: flex-start;
}
[data-testid="stChatMessage"].user-message {
    justify-content: flex-end;
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
    max-width: 80%;
}
.user-message [data-testid="stMarkdownContainer"] {
    margin-left: auto;
    background-color: #0084ff;
    color: white;
    border-radius: 15px;
    padding: 10px;
    float: right;
    clear: both;
}
.assistant-message [data-testid="stMarkdownContainer"] {
    margin-right: auto;
    background-color: #f0f0f0;
    border-radius: 15px;
    padding: 10px;
    float: left;
    clear: both;
}
.error-message {
    color: #ff4b4b;
    padding: 10px;
    border-radius: 5px;
    margin: 10px 0;
}
.typing-indicator {
    display: inline-block;
    padding: 10px;
    background-color: #f0f0f0;
    border-radius: 15px;
    margin: 5px 0;
    float: left;
    clear: both;
}
[data-testid="stChatMessage"]::after {
    content: "";
    display: table;
    clear: both;
}
</style>
""", unsafe_allow_html=True)

# Constants
WEBHOOK_URL = "https://n8n.savaitgalioprojektai.lt/webhook/f9f3653a-633e-4949-91c7-70bad1425006"
BEARER_TOKEN = "LABAS"
MAX_RETRIES = 3
RETRY_DELAY = 1

class Dashboard:
    def __init__(self):
        self.generate_mock_data()

    def generate_mock_data(self):
        """Generate mock data for dashboard"""
        # Mock data for daily interactions
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        self.daily_data = pd.DataFrame({
            'date': dates,
            'conversations': np.random.randint(50, 200, size=30),
            'user_satisfaction': np.random.uniform(4.0, 5.0, size=30),
            'response_time': np.random.uniform(0.5, 3.0, size=30)
        })

    def display_metrics(self):
        """Display key metrics in the dashboard"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Conversations",
                f"{self.daily_data['conversations'].sum():,}",
                "+12%"
            )
        
        with col2:
            st.metric(
                "Avg Response Time",
                f"{self.daily_data['response_time'].mean():.1f}s",
                "-0.5s"
            )
        
        with col3:
            st.metric(
                "User Satisfaction",
                f"{self.daily_data['user_satisfaction'].mean():.1f}/5.0",
                "+0.2"
            )
        
        with col4:
            st.metric(
                "Active Users",
                "1,234",
                "+8%"
            )

    def display_charts(self):
        """Display dashboard charts"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Conversations trend
            fig_conversations = px.line(
                self.daily_data,
                x='date',
                y='conversations',
                title='Daily Conversations'
            )
            fig_conversations.update_layout(height=250)
            st.plotly_chart(fig_conversations, use_container_width=True)
        
        with col2:
            # Satisfaction trend
            fig_satisfaction = px.line(
                self.daily_data,
                x='date',
                y='user_satisfaction',
                title='User Satisfaction Trend'
            )
            fig_satisfaction.update_layout(height=250)
            st.plotly_chart(fig_satisfaction, use_container_width=True)

class ChatInterface:
    def __init__(self):
        self.initialize_session_state()
        
    def initialize_session_state(self):
        """Initialize all session state variables"""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
        if "error" not in st.session_state:
            st.session_state.error = None

    def send_message_to_llm(self, message: str) -> Optional[str]:
        """Send message to LLM with retry logic and error handling"""
        headers = {
            "Authorization": f"Bearer {BEARER_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "sessionId": st.session_state.session_id,
            "chatInput": message
        }
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    WEBHOOK_URL, 
                    json=payload, 
                    headers=headers,
                    timeout=30
                )
                response.raise_for_status()
                return response.json()["output"]
            except requests.exceptions.RequestException as e:
                if attempt == MAX_RETRIES - 1:
                    error_message = f"Failed to get response: {str(e)}"
                    st.session_state.error = error_message
                    return None
                time.sleep(RETRY_DELAY)
        return None

    def display_messages(self):
        """Display all messages in the chat history"""
        for message in st.session_state.messages:
            message_class = "user-message" if message["role"] == "user" else "assistant-message"
            with st.chat_message(message["role"], avatar=None):
                st.markdown(
                    f'<div class="{message_class}">{message["content"]}</div>', 
                    unsafe_allow_html=True
                )

    def display_error(self):
        """Display error message if exists"""
        if st.session_state.error:
            st.markdown(
                f'<div class="error-message">{st.session_state.error}</div>', 
                unsafe_allow_html=True
            )
            st.session_state.error = None

    def handle_user_input(self):
        """Handle user input and get LLM response"""
        user_input = st.chat_input("Type your message here...")
        
        if user_input:
            st.session_state.error = None
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            with st.chat_message("assistant", avatar=None):
                with st.empty():
                    st.markdown(
                        '<div class="typing-indicator">Thinking...</div>', 
                        unsafe_allow_html=True
                    )
                    
                    llm_response = self.send_message_to_llm(user_input)
                    
                    if llm_response:
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": llm_response
                        })
                        st.markdown(
                            f'<div class="assistant-message">{llm_response}</div>', 
                            unsafe_allow_html=True
                        )

def main():
    st.title("AI Chat Dashboard")
    
    # Initialize dashboard and display components
    with st.container():
        st.subheader("Dashboard")
        dashboard = Dashboard()
        dashboard.display_metrics()
        dashboard.display_charts()
    
    # Add a divider between dashboard and chat
    st.markdown("---")
    
    # Initialize chat interface and display components
    st.subheader("Chat Interface")
    chat = ChatInterface()
    chat.display_error()
    chat.display_messages()
    chat.handle_user_input()

if __name__ == "__main__":
    main()