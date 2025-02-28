import streamlit as st
import requests
import json
import time
from PIL import Image
from io import BytesIO
import base64

# Page config
st.set_page_config(
    page_title="API Testing Tool for Image URLs",
    layout="wide"
)

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = {}
if "current_response" not in st.session_state:
    st.session_state.current_response = None

# Center the title
st.markdown("<h1 style='text-align: center;'>API Testing Tool for Image URLs</h1>", unsafe_allow_html=True)

# Create a container for the input form to center it
form_container = st.container()

# Create 3 columns with the middle one for the form (20% - 60% - 20% distribution)
col_left, col_middle, col_right = st.columns([1, 3, 1])

with col_middle:
    # Input section - centered in the page
    st.markdown("<h3 style='text-align: center;'>API Configuration</h3>", unsafe_allow_html=True)
    api_url = st.text_input("Enter API URL:", placeholder="https://api.example.com/process")
    
    # Method selection
    method = st.radio("Request Method:", ["POST", "GET"], horizontal=True)
    
    # Image URL input
    image_url = st.text_input("Enter Image URL:", placeholder="https://example.com/image.jpg")
    
    # Additional parameters section
    with st.expander("Additional Parameters", expanded=False):
        param_type = st.radio("Parameter Type:", ["Form Data", "JSON"], horizontal=True)
        
        # Dynamic parameter inputs
        st.subheader("Custom Parameters")
        if "params" not in st.session_state:
            st.session_state.params = [{"key": "correct", "value": "true"}]
        
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

# Process API request - this happens regardless of UI layout
if run_button:
    if api_url and image_url:
        try:
            with st.spinner("Processing request..."):
                # Prepare request parameters
                custom_params = {param["key"]: param["value"] for param in st.session_state.params if param["key"]}
                
                # Get image content
                img_response = requests.get(image_url, timeout=10)
                img_content = img_response.content
                
                # Prepare request based on selected method and parameter type
                if method == "POST":
                    if param_type == "Form Data":
                        files = {"image_file": (image_url.split("/")[-1], img_content, "image/jpeg")}
                        response = requests.post(api_url, files=files, data=custom_params)
                    else:  # JSON
                        # Convert image to base64 for JSON payload
                        encoded_img = base64.b64encode(img_content).decode('utf-8')
                        json_data = {
                            "image": encoded_img,
                            **custom_params
                        }
                        response = requests.post(api_url, json=json_data)
                else:  # GET
                    response = requests.get(api_url, params={**custom_params, "image_url": image_url})
                
                # Process response
                if response.status_code in [200, 201]:
                    try:
                        json_response = response.json()
                        st.session_state.current_response = {
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "image_url": image_url,
                            "api_url": api_url,
                            "method": method,
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
        st.markdown(f"**Method:** {result['method']}")
        st.markdown(f"**Status Code:** {result['status_code']}")
        st.markdown("**Parameters:**")
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
                file_name=f"api_response_{time.strftime('%Y%m%d_%H%M%S')}.json",
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
    st.sidebar.markdown(f"**Method:** {selected_item['method']}")
    
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
st.markdown("API Testing Tool for Image URLs | v1.0")