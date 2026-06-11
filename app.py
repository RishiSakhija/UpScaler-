import streamlit as st
import os
import urllib.request
import zipfile
import subprocess
import uuid
import platform
from PIL import Image

# --- Page Configuration ---
st.set_page_config(
    page_title="Studio AI Restorer",
    page_icon="✨",
    layout="centered"
)

# --- 1. Universal OS Detection ---
# The code now detects if it's on Windows or Linux and adapts automatically
IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    NCNN_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip"
    EXE_PATH = os.path.join("realesrgan_engine", "realesrgan-ncnn-vulkan.exe")
else:
    NCNN_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-ubuntu.zip"
    EXE_PATH = os.path.join("realesrgan_engine", "realesrgan-ncnn-vulkan")

ZIP_PATH = "realesrgan_engine.zip"
EXTRACT_FOLDER = "realesrgan_engine"

@st.cache_resource
def ensure_engine_exists():
    """Downloads the portable engine once based on the operating system."""
    if not os.path.exists(EXE_PATH):
        os_name = "Windows" if IS_WINDOWS else "Linux Cloud"
        with st.spinner(f"Downloading {os_name} AI Engine (~20MB)..."):
            urllib.request.urlretrieve(NCNN_URL, ZIP_PATH)
            with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
                zip_ref.extractall(EXTRACT_FOLDER)
            os.remove(ZIP_PATH)
            
            # Only apply Linux permissions if we are actually on Linux
            if not IS_WINDOWS:
                os.chmod(EXE_PATH, 0o755)
    return True

ensure_engine_exists()

# --- 2. Core Processing Logic ---
def restore_image(uploaded_file, effect_amount):
    unique_id = str(uuid.uuid4().hex)[:8]
    input_path = f"temp_in_{unique_id}.png"
    ai_output_path = f"ai_raw_{unique_id}.png"
    final_output_path = f"studio_restored_{unique_id}.png"
    
    img = Image.open(uploaded_file)
    img.save(input_path)
    
    cmd = [
        EXE_PATH,
        "-i", input_path,
        "-o", ai_output_path,
        "-n", "realesrgan-x4plus",
        "-f", "png",
        "-t", "128"
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        st.error(f"Engine Error: {e}")
        return None
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

    if effect_amount < 100:
        original_img = Image.open(uploaded_file).convert("RGB")
        ai_img = Image.open(ai_output_path).convert("RGB")
        
        original_resized = original_img.resize(ai_img.size, Image.Resampling.BICUBIC)
        alpha = effect_amount / 100.0
        
        blended_img = Image.blend(original_resized, ai_img, alpha=alpha)
        blended_img.save(final_output_path, "PNG", dpi=(300, 300))
        
        if os.path.exists(ai_output_path):
            os.remove(ai_output_path)
            
        return final_output_path
    else:
        img = Image.open(ai_output_path)
        img.save(final_output_path, "PNG", dpi=(300, 300))
        
        if os.path.exists(ai_output_path):
            os.remove(ai_output_path)
            
        return final_output_path

# --- 3. Premium Studio UI ---
st.markdown("<h1 style='text-align: center;'>✨ Deep-Focus AI Restorer</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Fixes lens blur, rebuilds edges, and perfectly blends natural camera grain.</p>", unsafe_allow_html=True)
st.divider()

uploaded_file = st.file_uploader("Drop Blurry/Low-Res Design Here", type=["png", "jpg", "jpeg"])
effect_slider = st.slider("AI Effect Amount (%)", min_value=10, max_value=100, value=50, step=5, help="Set to 50% for a natural camera texture blend.")

if uploaded_file is not None:
    st.image(uploaded_file, caption="Original Image Snapshot", use_column_width=True)
    
    if st.button("Run Studio Blend", type="primary"):
        with st.spinner("AI is rebuilding pixels and adjusting grain... Please wait."):
            output_file_path = restore_image(uploaded_file, effect_slider)
            
            if output_file_path and os.path.exists(output_file_path):
                st.success("Restoration Complete! Sharp edges recovered.")
                
                st.image(output_file_path, caption=f"Pristine PNG Output ({effect_slider}% AI)", use_column_width=True)
                
                with open(output_file_path, "rb") as file:
                    st.download_button(
                        label="📥 Download Pristine 300 DPI PNG",
                        data=file,
                        file_name=f"studio_restored_{effect_slider}pct.png",
                        mime="image/png"
                    )
                
                os.remove(output_file_path)
