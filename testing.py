import streamlit as st
import requests
import json
import time
from PIL import Image
from io import BytesIO
import base64

# Page config
st.set_page_config(
    page_title="Synergopro API Testing Tool",
    layout="wide"
)

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = {}
if "current_response" not in st.session_state:
    st.session_state.current_response = None

# Center the title
st.markdown("<h1 style='text-align: center;'>Synergopro API Testing Tool</h1>", unsafe_allow_html=True)

# Create a container for the input form to center it
form_container = st.container()

# Create 3 columns with the middle one for the form (20% - 60% - 20% distribution)
col_left, col_middle, col_right = st.columns([1, 3, 1])

with col_middle:
    # Input section - centered in the page
    st.markdown("<h3 style='text-align: center;'>API Configuration</h3>", unsafe_allow_html=True)
    
    # Default API URL
    api_url = st.text_input("Enter API URL:", value="https://aibackup.synergopro.com/analyze")
    
    # Project ID selection
    project_ids = [
        "41ca78bb-5884-4f2b-b72b-5bb600c77bfa",
        "6e5b2157-5753-456b-9313-eef28f1e2151",
        "e6753225-68d3-463e-ad32-2ae2a60a6264",
        "7b115574-0677-4448-8a35-f5df0ae167d5"
    ]
    
    selected_project_id = st.selectbox("Select Project ID:", project_ids)
    
    # Image URL input
    image_url = st.text_input("Enter Image URL:", placeholder="https://example.com/image.jpg")
    
    # API Key / Authentication
    with st.expander("API Authentication", expanded=True):
        api_key = st.text_input("API Key/Token:", type="password", help="Enter your API key or authentication token if required")
        auth_type = st.selectbox("Authentication Type:", ["None", "Bearer Token", "API Key", "Basic Auth"])
    
    # Additional parameters section
    with st.expander("Additional Parameters (Optional)", expanded=False):
        # Dynamic parameter inputs
        st.subheader("Custom Parameters")
        if "params" not in st.session_state:
            st.session_state.params = [{"key": "", "value": ""}]
        
        # Display existing parameters
        for i, param in enumerate(st.session_state.params):
            cols = st.columns([3, 3, 1])
            with cols[0]:
                st.session_state.params[i]["key"] = st.text_input(
                    f"Key {i}",
                    value=param["key"],
                    key=f"param_key_{i}"
                )
            with cols[1]:
                st.session_state.params[i]["value"] = st.text_input(
                    f"Value {i}",
                    value=param["value"],
                    key=f"param_value_{i}"
                )
            with cols[2]:
                if st.button("✖", key=f"delete_{i}"):
                    st.session_state.params.pop(i)
                    st.rerun()
        
        # Add new parameter button
        if st.button("Add Parameter", key="add_param"):
            st.session_state.params.append({"key": "", "value": ""})
            st.rerun()
    
    # Center the buttons
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    button_col1, button_col2 = st.columns([1, 1])
    with button_col1:
        run_button = st.button("Run API on Image", type="primary", use_container_width=True)
    with button_col2:
        clear_button = st.button("Clear Current Result", use_container_width=True)
        if clear_button:
            st.session_state.current_response = None
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Create a horizontal line to separate input from output
st.markdown("<hr>", unsafe_allow_html=True)

# Process API request
if run_button:
    if api_url and image_url:
        try:
            with st.spinner("Processing request..."):
                # Prepare custom parameters
                custom_params = {param["key"]: param["value"] for param in st.session_state.params if param["key"]}
                
                # Build request payload according to the Synergopro API format
                payload = {
                    "project_id": selected_project_id,
                    "image_url": image_url,
                    **custom_params
                }
                
                # Prepare headers based on authentication type
                headers = {"Content-Type": "application/json"}
                
                if auth_type != "None" and api_key:
                    if auth_type == "Bearer Token":
                        headers["Authorization"] = f"Bearer {api_key}"
                    elif auth_type == "API Key":
                        headers["X-API-Key"] = api_key
                    elif auth_type == "Basic Auth":
                        # Convert username:password to base64
                        auth_str = base64.b64encode(api_key.encode()).decode()
                        headers["Authorization"] = f"Basic {auth_str}"
                
                # Show current request information for debugging
                with st.expander("Debug Request Information"):
                    st.write("Request URL:", api_url)
                    st.write("Request Headers:", headers)
                    st.write("Request Payload:", payload)
                
                # Make the request
                response = requests.post(api_url, json=payload, headers=headers)
                
                # Process response
                if response.status_code in [200, 201]:
                    try:
                        json_response = response.json()
                        st.session_state.current_response = {
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "image_url": image_url,
                            "api_url": api_url,
                            "project_id": selected_project_id,
                            "params": custom_params,
                            "status_code": response.status_code,
                            "response": json_response
                        }
                        st.session_state.history[f"{image_url}_{time.time()}"] = st.session_state.current_response
                    except ValueError:
                        st.error("Response is not valid JSON. Received text content instead.")
                        st.text_area("Response Text:", value=response.text, height=200)
                else:
                    st.error(f"Failed to fetch API response. Status Code: {response.status_code}")
                    try:
                        error_json = response.json()
                        st.json(error_json)
                    except:
                        st.text_area("Response Text:", value=response.text, height=200)
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter both API URL and Image URL.")

# Display current result in the three-column layout
if st.session_state.current_response:
    result = st.session_state.current_response
    
    # Create three columns for results: left (info), middle (image), right (JSON)
    result_col1, result_col2, result_col3 = st.columns([1, 1, 1])
    
    # Left column - Basic info
    with result_col1:
        st.subheader("Request Information")
        st.markdown(f"**Timestamp:** {result['timestamp']}")
        st.markdown(f"**API URL:** {result['api_url']}")
        st.markdown(f"**Project ID:** {result['project_id']}")
        st.markdown(f"**Status Code:** {result['status_code']}")
        if result["params"]:
            st.markdown("**Additional Parameters:**")
            for k, v in result["params"].items():
                st.markdown(f"- {k}: {v}")
    
    # Middle column - Image
    with result_col2:
        st.subheader("Processed Image")
        st.image(result["image_url"], use_column_width=True)
    
    # Right column - JSON response
    with result_col3:
        st.subheader("API JSON Response")
        json_text = json.dumps(result["response"], indent=2)
        st.json(result["response"])
    
    # Full-width section for editable JSON and download
    st.subheader("Edit JSON Response")
    edited_json = st.text_area(
        label="Edit JSON",
        value=json_text,
        height=300,
        key="json_editor"
    )
    
    # Validate and enable download
    valid_json = True
    try:
        json.loads(edited_json)
    except json.JSONDecodeError:
        st.error("Invalid JSON format! Fix it before downloading.")
        valid_json = False
    
    # Center the download button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if valid_json:
            st.download_button(
                label="Download Edited JSON",
                data=edited_json.encode("utf-8"),
                file_name=f"synergopro_response_{time.strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

# Sidebar for history
st.sidebar.title("Previous Runs")

if st.session_state.history:
    history_keys = list(st.session_state.history.keys())
    history_keys.reverse()  # Show newest first
    
    # Create readable labels for the selectbox
    labels = [f"{st.session_state.history[k]['timestamp']} - {k.split('_')[0][:20]}..." for k in history_keys]
    
    selected_label = st.sidebar.selectbox(
        "Select a previous run:",
        labels,
        index=0,
        key="history_selector"
    )
    
    # Get the corresponding key
    selected_index = labels.index(selected_label)
    selected_key = history_keys[selected_index]
    selected_item = st.session_state.history[selected_key]
    
    # Display selected history item
    st.sidebar.image(selected_item["image_url"], caption="Image", use_column_width=True)
    st.sidebar.markdown(f"**API:** {selected_item['api_url']}")
    st.sidebar.markdown(f"**Project ID:** {selected_item['project_id']}")
    
    # Action buttons
    sidebar_col1, sidebar_col2 = st.sidebar.columns(2)
    with sidebar_col1:
        if st.button("Load Selected", key="load_selected"):
            st.session_state.current_response = selected_item
            st.rerun()
    with sidebar_col2:
        if st.button("Delete Selected", key="delete_selected"):
            del st.session_state.history[selected_key]
            st.rerun()
    
    with st.sidebar.expander("Response JSON"):
        st.json(selected_item["response"])

else:
    st.sidebar.info("No previous runs yet. Run the API to see history here.")

# Footer
st.markdown("---")
st.markdown("Synergopro API Testing Tool | v1.0")
