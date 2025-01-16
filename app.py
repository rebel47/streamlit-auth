import streamlit as st
import os
import google.generativeai as genai
from PIL import Image, UnidentifiedImageError
import pillow_heif
import re
import io
from dotenv import load_dotenv

# Enable HEIC support
pillow_heif.register_heif_opener()

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Default thresholds for determining healthiness
DEFAULT_CALORIE_THRESHOLD = 200  # Per serving
DEFAULT_SUGAR_THRESHOLD = 5  # grams per serving
DEFAULT_SATURATED_FAT_THRESHOLD = 10  # percentage

# Function to convert image format
def convert_image_format(uploaded_file):
    try:
        image = Image.open(uploaded_file)
        buffer = io.BytesIO()
        image = image.convert("RGB")
        image.save(buffer, format="JPEG")
        buffer.seek(0)
        return buffer, "image/jpeg"
    except UnidentifiedImageError:
        raise ValueError("Unsupported image format. Please upload PNG, JPEG, or HEIC images.")

# Function to get response from Google Gemini API
def get_gemini_response(image_data, mime_type, prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([{"mime_type": mime_type, "data": image_data}, prompt])
    return response.text

# Function to analyze the nutritional data
def analyze_nutrition(extracted_text, calorie_threshold, sugar_threshold, saturated_fat_threshold):
    # Extract relevant information
    calories = re.search(r"Calories: (\d+)", extracted_text)
    sugar = re.search(r"Sugar: (\d+)", extracted_text)
    saturated_fat = re.search(r"Saturated Fat: (\d+)", extracted_text)

    # Handle missing values
    calories = float(calories.group(1)) if calories else 0
    sugar = float(sugar.group(1)) if sugar else 0
    saturated_fat = float(saturated_fat.group(1)) if saturated_fat else 0

    # Determine healthiness
    is_healthy = (
        calories <= calorie_threshold
        and sugar <= sugar_threshold
        and saturated_fat <= saturated_fat_threshold
    )
    return {
        "calories": calories,
        "sugar": sugar,
        "saturated_fat": saturated_fat,
        "is_healthy": is_healthy
    }

# Streamlit App Configuration
st.set_page_config(page_title="Food Ingredient Analyzer")

st.title("Food Ingredient Analyzer")
st.text("Developed by: Mohammad Ayaz Alam")
st.header("Upload a food ingredient label image")

# Sidebar for custom thresholds
st.sidebar.header("Health Threshold Settings")
calorie_threshold = st.sidebar.number_input("Max Calories per Serving", value=DEFAULT_CALORIE_THRESHOLD, step=10)
sugar_threshold = st.sidebar.number_input("Max Sugar (g)", value=DEFAULT_SUGAR_THRESHOLD, step=1)
saturated_fat_threshold = st.sidebar.number_input("Max Saturated Fat (%)", value=DEFAULT_SATURATED_FAT_THRESHOLD, step=1)

# Input for uploading file
uploaded_file = st.file_uploader("Choose an image...", type=["png", "jpg", "jpeg", "heic"])

submit = st.button("Analyze")

# Prompt for Google Gemini API
input_prompt = """
You are an expert in nutrition and text analysis. Extract the nutritional information (calories, sugars, fats, etc.) 
from the provided food ingredient label image. Include the following details in the response:
\nCalories:
\nSugar:
\nSaturated Fat:
Health Status: Healthy ✅ or Unhealthy ❌
Only provide the information about calories, sugar, saturated fat, and health status. Do not include any additional information.
"""

if submit:
    if uploaded_file:
        with st.spinner("Processing... Please wait."):
            try:
                # Convert and prepare image data
                image_data, mime_type = convert_image_format(uploaded_file)

                # Get response from Google Gemini API
                extracted_text = get_gemini_response(image_data.getvalue(), mime_type, input_prompt)

                # Analyze nutrition
                results = analyze_nutrition(extracted_text, calorie_threshold, sugar_threshold, saturated_fat_threshold)

                # Display results
                st.subheader("Extracted Nutritional Information:")
                st.write(f"Calories: {results['calories']} kcal")
                st.write(f"Sugar: {results['sugar']} g")
                st.write(f"Saturated Fat: {results['saturated_fat']}%")
                st.write("Health Status: " + ("Healthy ✅" if results["is_healthy"] else "Unhealthy ❌"))
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.warning("Please upload an image to proceed.")
