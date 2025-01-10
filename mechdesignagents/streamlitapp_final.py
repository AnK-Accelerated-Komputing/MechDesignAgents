import streamlit as st
from streamlit_stl import stl_from_file
import os
from chat_with_designer_expert_multimodal import multimodal_designers_chat

def initialize_session_state():
    if 'prompt' not in st.session_state:
        st.session_state.prompt = ""
    if 'current_stl_path' not in st.session_state:
        st.session_state.current_stl_path = '/home/niel77/MechDesignAgents/mechdesignagents/NewCADs/airplane_wing_naca2412.stl'
    if 'color' not in st.session_state:
        st.session_state.color = "#FF9900"
    if 'material' not in st.session_state:
        st.session_state.material = "material"
    if 'auto_rotate' not in st.session_state:
        st.session_state.auto_rotate = False
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

def render_controls():
    # Text input for prompt
    prompt = st.text_input("Let's design", 
                          value=st.session_state.prompt,
                          placeholder="Enter a text prompt here",
                          key="input_prompt")
    
    if st.button("Generate CAD Model"):
        if prompt:
            with st.spinner("Generating CAD model..."):
                stl_file = multimodal_designers_chat(prompt)
                update_stl_path(stl_file)
                st.rerun()

    st.subheader("Visualization Controls")
    
    # Color and Material controls
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
    
    # Opacity and Height sliders
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

    # Camera controls
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

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    initialize_session_state()

    st.title("AnK CAD")

    # Create two columns: controls on the left (1/3 width) and viewer on the right (2/3 width)
    left_col, right_col = st.columns([1, 2])

    # Render controls in the left column
    with left_col:
        render_controls()

    # Render STL viewer in the right column
    with right_col:
        render_stl_viewer()

    # Add example prompts to the right column below the viewer
    examples = [
        "A box with a through hole in the center.",
        "Create a pipe of outer diameter 50mm and inside diameter 40mm.",
        "Create a circular plate of radius 2mm and thickness 0.125mm with four holes of radius 0.25mm patterned at distance of 1.5mm from the centre along the axes."
    ]
    with right_col:
        st.subheader("Example Prompts")
        for example in examples:
            if st.button(example, key=f"example_{example}"):
                st.session_state.prompt = example
                st.rerun()