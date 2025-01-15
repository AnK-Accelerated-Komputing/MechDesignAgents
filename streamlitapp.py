import streamlit as st
from streamlit_stl import stl_from_file
import sys
import os
import shutil
import tempfile
from pathlib import Path

# Add the mechdesignagents directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "mechdesignagents")))
from mechdesignagents.agentic_chats import multimodal_designers_chat

def initialize_session_state():
    if 'prompt' not in st.session_state:
        st.session_state.prompt = ""
    if 'current_stl_path' not in st.session_state:
        st.session_state.current_stl_path = 'data/ANK_CAD.stl'
    if 'current_image_path' not in st.session_state:
        st.session_state.current_image_path = None
    if 'color' not in st.session_state:
        st.session_state.color = "#FF9900"
    if 'material' not in st.session_state:
        st.session_state.material = "material"
    if 'auto_rotate' not in st.session_state:
        st.session_state.auto_rotate = True
    if 'opacity' not in st.session_state:
        st.session_state.opacity = 1.0
    if 'height' not in st.session_state:
        st.session_state.height = 500
    if 'cam_v_angle' not in st.session_state:
        st.session_state.cam_v_angle = 60
    if 'cam_h_angle' not in st.session_state:
        st.session_state.cam_h_angle = -90
    if 'cam_distance' not in st.session_state:
        st.session_state.cam_distance = 0
    if 'max_view_distance' not in st.session_state:
        st.session_state.max_view_distance = 1000

def update_stl_path(new_path):
    st.session_state.current_stl_path = new_path

def save_uploaded_file(uploaded_file):
    """Save uploaded file to a permanent location and return the path"""
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    # Create a file path for the uploaded file
    file_path = upload_dir / uploaded_file.name
    
    # Save the file
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Clean up old files if they exist
    if st.session_state.current_image_path and os.path.exists(st.session_state.current_image_path):
        try:
            os.remove(st.session_state.current_image_path)
        except Exception:
            pass
    
    return str(file_path.absolute())

def build_prompt(text_prompt, image_path):
    """Build the final prompt combining text and image if available"""
    final_prompt = ""
    
    # Add text prompt if it exists
    if text_prompt and text_prompt.strip():
        final_prompt += text_prompt.strip()
    
    # Add image path if it exists
    if image_path:
        # Add a space before image tag if there's already text
        if final_prompt:
            final_prompt += " "
        final_prompt += f"{image_path}>"
    
    return final_prompt if final_prompt else None

def save_uploaded_file(uploaded_file):
    """Save uploaded file to a temporary location and return the path"""
    try:
        # Create a temporary directory if it doesn't exist
        temp_dir = Path(tempfile.gettempdir()) / "streamlit_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate a unique filename
        file_extension = Path(uploaded_file.name).suffix
        temp_file_path = temp_dir / f"temp_upload_{hash(uploaded_file.name)}{file_extension}"
        
        # Save the file
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Ensure file permissions are correct
        temp_file_path.chmod(0o644)
        
        return str(temp_file_path.absolute())
    
    except Exception as e:
        st.error(f"Error saving file: {str(e)}")
        return None

def render_controls():
    # Text input for prompt
    text_prompt = st.text_input("Let's design", 
                          value=st.session_state.prompt,
                          placeholder="Enter a text prompt here",
                          key="input_prompt")
    
    # File uploader widget
    uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    
    # Handle file upload with better error handling
    if uploaded_file is not None:
        try:
            image_path = save_uploaded_file(uploaded_file)
            if image_path and os.path.exists(image_path):
                st.session_state.current_image_path = image_path
                st.image(image_path, caption="Uploaded Image", use_container_width=True)
            else:
                st.error("Failed to save uploaded file")
        except Exception as e:
            st.error(f"Error processing uploaded file: {str(e)}")
    
    # Generate button
    if st.button("Generate CAD Model"):
        final_prompt = build_prompt(text_prompt, st.session_state.current_image_path)
        
        if final_prompt:
            with st.spinner("Generating CAD model..."):
                try:
                    stl_file = multimodal_designers_chat(final_prompt)
                    update_stl_path(stl_file)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error generating CAD model: {str(e)}")
        else:
            st.warning("Please provide either a text prompt or upload an image (or both)")

    
    
    st.subheader("Visualization Controls")
    
    # Rest of your existing controls code...
    color = st.color_picker("Pick a color", 
                           value=st.session_state.color, 
                           key='color_picker')
    st.session_state.color = color
    
    material = st.selectbox("Select a material", 
                           ["material", "flat", "wireframe"], 
                           index=["material", "flat", "wireframe"].index(st.session_state.material),
                           key='material_selector')
    st.session_state.material = material
    
    auto_rotate = st.toggle("Auto rotation", 
                           value=st.session_state.auto_rotate,
                           key='rotation_toggle')
    st.session_state.auto_rotate = auto_rotate
    
    opacity = st.slider("Opacity", 
                       min_value=0.0, 
                       max_value=1.0, 
                       value=st.session_state.opacity,
                       key='opacity_slider')
    st.session_state.opacity = opacity
    
    height = st.slider("Height", 
                      min_value=50, 
                      max_value=1000, 
                      value=st.session_state.height,
                      key='height_slider')
    st.session_state.height = height

    st.subheader("Camera Controls")
    
    cam_v_angle = st.number_input("Camera Vertical Angle", 
                                 value=st.session_state.cam_v_angle,
                                 key='cam_v_angle_input')
    st.session_state.cam_v_angle = cam_v_angle
    
    cam_h_angle = st.number_input("Camera Horizontal Angle", 
                                 value=st.session_state.cam_h_angle,
                                 key='cam_h_angle_input')
    st.session_state.cam_h_angle = cam_h_angle
    
    cam_distance = st.number_input("Camera Distance", 
                                  value=st.session_state.cam_distance,
                                  key='cam_distance_input')
    st.session_state.cam_distance = cam_distance
    
    max_view_distance = st.number_input("Max view distance", 
                                       min_value=1, 
                                       value=st.session_state.max_view_distance,
                                       key='max_view_distance_input')
    st.session_state.max_view_distance = max_view_distance

def render_stl_viewer():
    stl_from_file(
        file_path=st.session_state.current_stl_path,
        color=st.session_state.color,
        material=st.session_state.material,
        auto_rotate=st.session_state.auto_rotate,
        opacity=st.session_state.opacity,
        height=st.session_state.height,
        shininess=100,
        cam_v_angle=st.session_state.cam_v_angle,
        cam_h_angle=st.session_state.cam_h_angle,
        cam_distance=st.session_state.cam_distance,
        max_view_distance=st.session_state.max_view_distance,
        key='stl_viewer'
    )

def cleanup_temp_files():
    """Clean up temporary files when the session ends"""
    if st.session_state.current_image_path and os.path.exists(st.session_state.current_image_path):
        try:
            os.remove(st.session_state.current_image_path)
        except Exception:
            pass


if __name__ == "__main__":
    st.set_page_config(layout="wide")
    initialize_session_state()
    # Register cleanup function to run when the session ends
    st.session_state['cleanup_requested'] = True
    
    if st.session_state.get('cleanup_requested'):
        cleanup_temp_files()

    st.title("AnK CAD")

    # Create two columns
    left_col, right_col = st.columns([1, 2])

    with left_col:
        render_controls()

    with right_col:
        render_stl_viewer()
        stl_file = st.session_state.current_stl_path 
        stl_file_name = os.path.basename(stl_file)

        with open(stl_file, "rb") as file:
            btn = st.download_button(
                label="Download CAD Model",
                data=file,
                file_name=stl_file_name,
                mime="application/octet-stream"
            )

    # Add example prompts
    with right_col:
        st.subheader("Example Prompts")
        examples = [
            "A box with a through hole in the center.",
            "Create a pipe of outer diameter 50mm and inside diameter 40mm.",
            "Create a circular plate of radius 2mm and thickness 0.125mm with four holes of radius 0.25mm patterned at distance of 1.5mm from the centre along the axes."
        ]
        for example in examples:
            if st.button(example, key=f"example_{example}"):
                st.session_state.prompt = example
                st.rerun()

