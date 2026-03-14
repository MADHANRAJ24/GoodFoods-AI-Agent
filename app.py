import streamlit as st
import traceback

from agent.conversation import Conversation

st.set_page_config(
    page_title="GoodFoods AI Agent", 
    page_icon="🍽️", 
    layout="centered",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if "chat_session" not in st.session_state:
    st.session_state.chat_session = Conversation()

st.title("🍽️ GoodFoods AI Concierge")
st.markdown("Welcome to GoodFoods! I can help you find restaurants, check availability, and book or cancel reservations.")

# Sidebar info
with st.sidebar:
    st.header("About")
    st.markdown('''
    **Capabilities:**
    - 🔍 Search by location & cuisine
    - 📅 Check real-time availability
    - 📝 Book reservations
    - ❌ Cancel bookings
    ''')
    st.divider()
    if st.button("Reset Conversation"):
        st.session_state.chat_session = Conversation()
        st.rerun()

# Display Chat History (Filtering out system and tool messages for UI)
for msg in st.session_state.chat_session.get_history():
    role = msg.get("role") if isinstance(msg, dict) else msg.role
    
    # We skip system prompts and raw tool-call objects in the UI
    if role == "system":
        continue
        
    if role == "tool":
        # We can show a small message indicating a backend action happened
        with st.chat_message("assistant", avatar="🛠️"):
            st.caption(f"Backend action: Checked database ({msg.get('name')})")
        continue

    # Content
    content = msg.get("content") if isinstance(msg, dict) else msg.content
    
    # Check for tool_calls in message objects (which happens before a tool role)
    tool_calls = msg.get("tool_calls") if isinstance(msg, dict) else getattr(msg, "tool_calls", None)
    
    if tool_calls:
        for tc in tool_calls:
            # We can show a pending action message to show transparency
            with st.chat_message("assistant", avatar="⚙️"):
                func_name = tc.get("function", {}).get("name") if isinstance(tc, dict) else tc.function.name
                st.caption(f"Agent requested action: `{func_name}`")
    
    if content:
        # Display regular user or assistant text
        with st.chat_message(role):
            st.markdown(content)

# User Input
if prompt := st.chat_input("E.g., I want an Italian restaurant in Downtown for 2 people tonight."):
    st.session_state.chat_session.add_user_message(prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.chat_session.run_turn()
                st.markdown(response)
            except Exception as e:
                st.error(f"Error communicating with AI: {str(e)}")
                st.error(traceback.format_exc())
        st.rerun()
