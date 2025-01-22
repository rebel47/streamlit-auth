import streamlit as st
import os
import google.generativeai as genai
from PIL import Image
import io
from dotenv import load_dotenv
import json
import numpy as np

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

genai.configure(api_key=GOOGLE_API_KEY)

class NutritionAnalyzer:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.thresholds = {
            "calories": 300,
            "sugar": 25,
            "saturated_fat": 5,
            "sodium": 600,
            "protein": 5
        }
    
    def preprocess_image(self, image_file):
        try:
            image = Image.open(image_file)
            # Convert to RGB if necessary
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            # Resize if too large
            max_size = 1024
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            return image
        except Exception as e:
            raise ValueError(f"Error processing image: {str(e)}")

    def extract_nutrition_info(self, image):
        prompt = """
        Analyze this nutrition label and extract the following information in JSON format:
        {
            "calories": number,
            "protein": number (in grams),
            "carbohydrates": number (in grams),
            "sugar": number (in grams),
            "fat": number (in grams),
            "saturated_fat": number (in grams),
            "sodium": number (in mg),
            "fiber": number (in grams),
            "serving_size": string
        }
        Only include numerical values, no units in the numbers.
        """
        
        try:
            response = self.model.generate_content([image, prompt])
            # Extract JSON from response
            json_str = response.text.strip('`').strip()
            if json_str.startswith('json'):
                json_str = json_str[4:]
            return json.loads(json_str)
        except Exception as e:
            raise ValueError(f"Error analyzing image: {str(e)}")

    def calculate_health_score(self, nutrition_data):
        scores = {
            "calories": 1 if nutrition_data.get("calories", 0) <= self.thresholds["calories"] else 0,
            "sugar": 1 if nutrition_data.get("sugar", 0) <= self.thresholds["sugar"] else 0,
            "saturated_fat": 1 if nutrition_data.get("saturated_fat", 0) <= self.thresholds["saturated_fat"] else 0,
            "sodium": 1 if nutrition_data.get("sodium", 0) <= self.thresholds["sodium"] else 0,
            "protein": 1 if nutrition_data.get("protein", 0) >= self.thresholds["protein"] else 0
        }
        return {
            "total_score": sum(scores.values()) / len(scores) * 100,
            "component_scores": scores
        }
    def get_analysis_prompt(image_type):
        if image_type == "Food Label":
            return """
            You are an expert nutritionist analyzing a nutrition label. Extract the following information:
            - Calories (per serving)
            - Protein (g)
            - Carbohydrates (g)
            - Fat (g)
            - Serving size
            
            Respond in JSON format with these exact keys: 
            {
                "calories": number,
                "protein": number,
                "carbohydrates": number,
                "fat": number,
                "serving_size": string
            }
            Only provide the JSON data, no additional text.
            """
        else:
            return """
            You are an expert nutritionist. Analyze this food image and:
            1. Identify all visible food items
            2. Estimate portion sizes
            3. Calculate approximate calories for each item
            
            Respond in JSON format:
            {
                "food_items": [
                    {
                        "name": "item name",
                        "portion": "portion size",
                        "calories": number
                    }
                ],
                "total_calories": number
            }
            Be specific about portions but don't include disclaimers about estimates.
            Only provide the JSON data, no additional text.
            """



def analyze_nutrition(image_file, image_type="Food Label"):
    analyzer = NutritionAnalyzer()
    
    try:
        # Preprocess image
        processed_image = analyzer.preprocess_image(image_file)
        
        # Get appropriate prompt
        prompt = analyzer.get_analysis_prompt(image_type)
        
        # Extract nutrition information
        result = analyzer.extract_nutrition_info(processed_image, prompt)
        
        if image_type == "Food Label":
            return {
                "nutrition_data": result,
                "health_score": analyzer.calculate_health_score(result)
            }
        else:
            return {
                "food_items": result["food_items"],
                "nutrition_data": {
                    "calories": result["total_calories"],
                    "protein": 0,  # These would need estimation
                    "carbohydrates": 0,
                    "fat": 0
                }
            }
    except Exception as e:
        raise ValueError(f"Analysis failed: {str(e)}")


def generate_recommendations(nutrition_data, health_score):
    recommendations = []
    
    if nutrition_data.get("calories", 0) > 300:
        recommendations.append("Consider portion control to reduce calorie intake")
    
    if nutrition_data.get("sugar", 0) > 25:
        recommendations.append("High in sugar - try finding alternatives with less added sugar")
    
    if nutrition_data.get("saturated_fat", 0) > 5:
        recommendations.append("High in saturated fat - look for options with healthier fats")
    
    if nutrition_data.get("sodium", 0) > 600:
        recommendations.append("High sodium content - consider low-sodium alternatives")
    
    if not recommendations:
        recommendations.append("This food item fits within healthy nutritional guidelines")
    
    return recommendations