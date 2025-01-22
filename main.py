import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
from pathlib import Path
import matplotlib.pyplot as plt
from PIL import Image

# Constants
USER_DATA_FILE = "data/user_data.json"
PROGRESS_FILE = "data/progress_data.csv"
FOOD_LOG_FILE = "data/food_log.csv"
WORKOUT_LOG_FILE = "data/workout_log.csv"

EXERCISE_CATEGORIES = {
    "Cardio": {
        "exercises": ["Walking", "Running", "Cycling", "Swimming", "Jump Rope"],
        "calories_per_minute": 7  # Average calories burned per minute
    },
    "Strength": {
        "exercises": ["Push-ups", "Pull-ups", "Squats", "Lunges", "Planks", "Deadlifts"],
        "calories_per_minute": 5
    },
    "Flexibility": {
        "exercises": ["Yoga", "Stretching", "Pilates"],
        "calories_per_minute": 3
    },
    "HIIT": {
        "exercises": ["Burpees", "Mountain Climbers", "Box Jumps", "Sprint Intervals"],
        "calories_per_minute": 10
    }
}

# Setup data directory and files
Path("data").mkdir(exist_ok=True)

# Utility Functions
def calculate_bmi(weight, height_cm):
    height_m = height_cm / 100
    return round(weight / (height_m * height_m), 2)

def get_bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"

def calculate_daily_calories(weight, height, age, gender, activity_level, goal):
    # Harris-Benedict equation
    if gender == "Male":
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    
    activity_multipliers = {
        "Sedentary": 1.2,
        "Light": 1.375,
        "Moderate": 1.55,
        "Active": 1.725,
        "Very Active": 1.9
    }
    
    maintenance_calories = bmr * activity_multipliers[activity_level]
    
    # Adjust based on goal
    if goal == "Weight Loss":
        return round(maintenance_calories - 500)  # 500 calorie deficit
    elif goal == "Weight Gain":
        return round(maintenance_calories + 500)  # 500 calorie surplus
    else:
        return round(maintenance_calories)

# Data Management Functions
def load_data():
    try:
        with open(USER_DATA_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(USER_DATA_FILE, "w") as file:
        json.dump(data, file)

def load_progress():
    try:
        return pd.read_csv(PROGRESS_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=['date', 'weight', 'calories_consumed', 'exercise_minutes'])

def save_progress(df):
    df.to_csv(PROGRESS_FILE, index=False)

def load_food_log():
    try:
        return pd.read_csv(FOOD_LOG_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=['date', 'meal_type', 'food_item', 'calories', 'protein', 'carbs', 'fat'])

def save_food_log(df):
    df.to_csv(FOOD_LOG_FILE, index=False)

def load_workout_log():
    try:
        return pd.read_csv(WORKOUT_LOG_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=['date', 'exercise_type', 'exercise', 'duration', 'calories_burned'])

def save_workout_log(df):
    df.to_csv(WORKOUT_LOG_FILE, index=False)

# Page Functions
def home_page():
    st.title("Health & Fitness Tracker")
    user_data = load_data()
    
    if not user_data:
        st.info("👋 Welcome! Please complete your profile to get started.")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Profile Overview")
        bmi = calculate_bmi(user_data['weight'], user_data['height'])
        st.metric("BMI", f"{bmi} ({get_bmi_category(bmi)})")
        st.metric("Weight Goal", f"{user_data['target_weight']} kg")
        
    with col2:
        st.subheader("Today's Progress")
        daily_calories = calculate_daily_calories(
            user_data['weight'], user_data['height'], user_data['age'],
            user_data['gender'], user_data['exercise_level'], user_data['goal']
        )
        food_log = load_food_log()
        today_food = food_log[food_log['date'] == datetime.now().strftime("%Y-%m-%d")]
        calories_consumed = today_food['calories'].sum()
        st.metric("Calories", f"{calories_consumed}/{daily_calories}",
          delta=float(daily_calories - calories_consumed))  # Convert to float
        
    with col3:
        st.subheader("Exercise Log")
        workout_log = load_workout_log()
        today_workout = workout_log[workout_log['date'] == datetime.now().strftime("%Y-%m-%d")]
        calories_burned = today_workout['calories_burned'].sum()
        st.metric("Calories Burned", f"{calories_burned}")

def profile_page():
    st.header("User Profile")
    user_data = load_data()
    
    col1, col2 = st.columns(2)
    
    with col1:
        weight = st.number_input("Current Weight (kg)", 30.0, 200.0, 
                               value=user_data.get('weight', 70.0))
        height = st.number_input("Height (cm)", 100.0, 250.0, 
                               value=user_data.get('height', 170.0))
        age = st.number_input("Age", 15, 100, value=user_data.get('age', 30))
        gender = st.selectbox("Gender", ["Male", "Female"], 
                            index=0 if user_data.get('gender') == "Male" else 1)
    
    with col2:
        target_weight = st.number_input("Target Weight (kg)", 30.0, 200.0, 
                                      value=user_data.get('target_weight', 65.0))
        goal = st.selectbox("Goal", ["Weight Loss", "Maintenance", "Weight Gain"],
                          index=["Weight Loss", "Maintenance", "Weight Gain"].index(
                              user_data.get('goal', 'Maintenance')))
        exercise_level = st.selectbox(
            "Activity Level",
            ["Sedentary", "Light", "Moderate", "Active", "Very Active"],
            index=["Sedentary", "Light", "Moderate", "Active", "Very Active"].index(
                user_data.get('exercise_level', 'Moderate'))
        )
        dietary_pref = st.selectbox(
            "Dietary Preference",
            ["Vegetarian", "Vegan", "Non-Vegetarian"],
            index=["Vegetarian", "Vegan", "Non-Vegetarian"].index(
                user_data.get('dietary_pref', 'Vegetarian'))
        )
    
    allergies = st.multiselect(
        "Allergies/Intolerances",
        ["Dairy", "Nuts", "Gluten", "Shellfish", "Soy", "Eggs"],
        default=user_data.get('allergies', [])
    )
    
    if st.button("Save Profile"):
        user_data = {
            "weight": weight,
            "height": height,
            "age": age,
            "gender": gender,
            "target_weight": target_weight,
            "goal": goal,
            "exercise_level": exercise_level,
            "dietary_pref": dietary_pref,
            "allergies": allergies,
            "last_updated": datetime.now().strftime("%Y-%m-%d")
        }
        save_data(user_data)
        st.success("Profile updated successfully!")

def food_analyzer_page():
    st.header("Food Analyzer & Logger")
    
    # Create tabs for different input methods
    tab1, tab2 = st.tabs(["📸 Food Image Analysis", "✍️ Manual Entry"])
    
    with tab1:
        st.subheader("Analyze Food Image")
        image_type = st.radio("What are you uploading?", ["Food Label", "Food Image"])
        uploaded_file = st.file_uploader(
            "Upload Image", 
            type=['png', 'jpg', 'jpeg'],
            help="Upload either a nutrition label or a photo of your food"
        )
        
        if uploaded_file and st.button("Analyze"):
            with st.spinner("Analyzing image..."):
                try:
                    from app import analyze_nutrition
                    result = analyze_nutrition(uploaded_file, image_type)
                    
                    # Display results in a clean format
                    st.subheader("Analysis Results")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
                    
                    with col2:
                        if image_type == "Food Label":
                            st.write("📊 Nutritional Information:")
                            st.write(f"🔸 Calories: {result['nutrition_data']['calories']} kcal")
                            st.write(f"🔸 Protein: {result['nutrition_data'].get('protein', 0)}g")
                            st.write(f"🔸 Carbs: {result['nutrition_data'].get('carbohydrates', 0)}g")
                            st.write(f"🔸 Fat: {result['nutrition_data'].get('fat', 0)}g")
                        else:
                            st.write("🍽️ Detected Food Items:")
                            for item in result['food_items']:
                                st.write(f"🔸 {item['name']}: {item['calories']} kcal")
                    
                    # Add to food log section
                    st.subheader("Add to Food Log")
                    col1, col2 = st.columns(2)
                    with col1:
                        meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"])
                        food_name = st.text_input("Food Name", 
                                                value="Analyzed Food Item" if image_type == "Food Label" 
                                                else ", ".join([item['name'] for item in result.get('food_items', [])]))
                    
                    if st.button("Add to Food Log"):
                        food_log = load_food_log()
                        total_calories = (result['nutrition_data']['calories'] if image_type == "Food Label"
                                        else sum(item['calories'] for item in result['food_items']))
                        
                        new_entry = pd.DataFrame({
                            'date': [datetime.now().strftime("%Y-%m-%d")],
                            'meal_type': [meal_type],
                            'food_item': [food_name],
                            'calories': [float(total_calories)],
                            'protein': [float(result['nutrition_data'].get('protein', 0)) if image_type == "Food Label" else 0],
                            'carbs': [float(result['nutrition_data'].get('carbohydrates', 0)) if image_type == "Food Label" else 0],
                            'fat': [float(result['nutrition_data'].get('fat', 0)) if image_type == "Food Label" else 0]
                        })
                        food_log = pd.concat([food_log, new_entry], ignore_index=True)
                        save_food_log(food_log)
                        st.success("✅ Food added to log successfully!")
                        
                except Exception as e:
                    st.error(f"Error during analysis: {str(e)}")
    
    with tab2:
        st.subheader("Manual Food Entry")
        col1, col2 = st.columns(2)
        with col1:
            meal_type = st.selectbox("Select Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"])
            food_name = st.text_input("Food Item Name")
            calories = st.number_input("Calories", 0, 2000)
        with col2:
            protein = st.number_input("Protein (g)", 0.0, 200.0)
            carbs = st.number_input("Carbohydrates (g)", 0.0, 200.0)
            fat = st.number_input("Fat (g)", 0.0, 200.0)
        
        if st.button("Add Food Item"):
            food_log = load_food_log()
            new_entry = pd.DataFrame({
                'date': [datetime.now().strftime("%Y-%m-%d")],
                'meal_type': [meal_type],
                'food_item': [food_name],
                'calories': [float(calories)],
                'protein': [float(protein)],
                'carbs': [float(carbs)],
                'fat': [float(fat)]
            })
            food_log = pd.concat([food_log, new_entry], ignore_index=True)
            save_food_log(food_log)
            st.success("✅ Food item added to log!")
    
    # Display today's food log
    st.subheader("Today's Food Log")
    food_log = load_food_log()
    today_log = food_log[food_log['date'] == datetime.now().strftime("%Y-%m-%d")]
    if not today_log.empty:
        st.dataframe(today_log)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Calories", f"{today_log['calories'].sum():.0f} kcal")
        with col2:
            st.metric("Total Protein", f"{today_log['protein'].sum():.1f}g")
        with col3:
            st.metric("Total Carbs", f"{today_log['carbs'].sum():.1f}g")

def exercise_page():
    st.header("Exercise Tracker")
    
    user_data = load_data()
    if not user_data:
        st.warning("Please complete your profile first!")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Log Exercise")
        exercise_type = st.selectbox("Exercise Type", list(EXERCISE_CATEGORIES.keys()))
        exercise = st.selectbox("Exercise", EXERCISE_CATEGORIES[exercise_type]["exercises"])
        duration = st.number_input("Duration (minutes)", 1, 180)
        
        calories_burned = duration * EXERCISE_CATEGORIES[exercise_type]["calories_per_minute"]
        
        if st.button("Log Exercise"):
            workout_log = load_workout_log()
            new_entry = pd.DataFrame({
                'date': [datetime.now().strftime("%Y-%m-%d")],
                'exercise_type': [exercise_type],
                'exercise': [exercise],
                'duration': [duration],
                'calories_burned': [calories_burned]
            })
            workout_log = pd.concat([workout_log, new_entry], ignore_index=True)
            save_workout_log(workout_log)
            st.success("Exercise logged successfully!")
    
    with col2:
        st.subheader("Today's Exercise Summary")
        workout_log = load_workout_log()
        today_workout = workout_log[workout_log['date'] == datetime.now().strftime("%Y-%m-%d")]
        if not today_workout.empty:
            st.dataframe(today_workout)
            st.metric("Total Calories Burned", f"{today_workout['calories_burned'].sum():.0f}")

def progress_tracker_page():
    st.header("Progress Tracker")
    
    user_data = load_data()
    if not user_data:
        st.warning("Please complete your profile first!")
        return
    
    # Weight tracking
    progress_df = load_progress()
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Log Today's Weight")
        weight = st.number_input("Weight (kg)", 30.0, 200.0, user_data['weight'])
        if st.button("Log Weight"):
            new_entry = pd.DataFrame({
                'date': [datetime.now().strftime("%Y-%m-%d")],
                'weight': [weight]
            })
            progress_df = pd.concat([progress_df, new_entry], ignore_index=True)
            save_progress(progress_df)
            st.success("Weight logged successfully!")
    
    # Progress visualization
    if not progress_df.empty:
        st.subheader("Weight Progress")
        fig = px.line(progress_df, x='date', y='weight', 
                     title='Weight Over Time')
        st.plotly_chart(fig)
        
        # Calculate stats
        if len(progress_df) > 1:
            total_loss = progress_df['weight'].iloc[-1] - progress_df['weight'].iloc[0]
            st.metric("Total Weight Change", f"{total_loss:.1f} kg")

def main():
    st.set_page_config(page_title="Health & Fitness Tracker", layout="wide")
    
    # Navigation
    pages = {
        "Home": home_page,
        "User Profile": profile_page,
        "Food Analyzer": food_analyzer_page,
        "Exercise Tracker": exercise_page,
        "Progress Tracker": progress_tracker_page
    }
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", list(pages.keys()))
    
    # Show user stats in sidebar if profile exists
    user_data = load_data()
    if user_data:
        st.sidebar.subheader("Daily Targets")
        daily_calories = calculate_daily_calories(
            user_data['weight'], user_data['height'], user_data['age'],
            user_data['gender'], user_data['exercise_level'], user_data['goal']
        )
        
        # Get today's totals
        food_log = load_food_log()
        workout_log = load_workout_log()
        today = datetime.now().strftime("%Y-%m-%d")
        
        calories_consumed = food_log[food_log['date'] == today]['calories'].sum()
        calories_burned = workout_log[workout_log['date'] == today]['calories_burned'].sum()
        
        # Display metrics
        st.sidebar.metric("Calorie Target", f"{daily_calories}")
        st.sidebar.metric("Calories Consumed", f"{calories_consumed:.0f}")
        st.sidebar.metric("Calories Burned", f"{calories_burned:.0f}")
        st.sidebar.metric("Net Calories", 
                         f"{calories_consumed - calories_burned:.0f}")
        
        # Display macronutrient breakdown
        if not food_log[food_log['date'] == today].empty:
            st.sidebar.subheader("Today's Macros")
            today_food = food_log[food_log['date'] == today]
            st.sidebar.metric("Protein", f"{today_food['protein'].sum():.1f}g")
            st.sidebar.metric("Carbs", f"{today_food['carbs'].sum():.1f}g")
            st.sidebar.metric("Fat", f"{today_food['fat'].sum():.1f}g")
    
    # Render selected page
    pages[page]()

if __name__ == "__main__":
    main()