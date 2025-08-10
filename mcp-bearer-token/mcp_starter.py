from fastmcp.server.transport.http import CORSMiddleware
import os
import datetime
from typing import Annotated
from dotenv import load_dotenv
import google.generativeai as genai
from mcp_server import McpServer, McpTool, Field

# --- SETUP ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
mcp = McpServer()
mcp.app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
# --- DATA CALCULATION LOGIC ---
def calculate_profile_data(dob_string: str) -> dict:
    day, month, year = map(int, dob_string.split('-'))
    date_object = datetime.date(year, month, day)
    zodiac_sign = ''
    if (month == 3 and day >= 21) or (month == 4 and day <= 19): zodiac_sign = 'Aries'
    elif (month == 4 and day >= 20) or (month == 5 and day <= 20): zodiac_sign = 'Taurus'
    elif (month == 5 and day >= 21) or (month == 6 and day <= 20): zodiac_sign = 'Gemini'
    elif (month == 6 and day >= 21) or (month == 7 and day <= 22): zodiac_sign = 'Cancer'
    elif (month == 7 and day >= 23) or (month == 8 and day <= 22): zodiac_sign = 'Leo'
    elif (month == 8 and day >= 23) or (month == 9 and day <= 22): zodiac_sign = 'Virgo'
    elif (month == 9 and day >= 23) or (month == 10 and day <= 22): zodiac_sign = 'Libra'
    elif (month == 10 and day >= 23) or (month == 11 and day <= 21): zodiac_sign = 'Scorpio'
    elif (month == 11 and day >= 22) or (month == 12 and day <= 21): zodiac_sign = 'Sagittarius'
    elif (month == 12 and day >= 22) or (month == 1 and day <= 19): zodiac_sign = 'Capricorn'
    elif (month == 1 and day >= 20) or (month == 2 and day <= 18): zodiac_sign = 'Aquarius'
    elif (month == 2 and day >= 19) or (month == 3 and day <= 20): zodiac_sign = 'Pisces'
    
    ruling_planets = {'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury', 'Cancer': 'Moon', 'Leo': 'Sun', 'Virgo': 'Mercury', 'Libra': 'Venus', 'Scorpio': 'Pluto & Mars', 'Sagittarius': 'Jupiter', 'Capricorn': 'Saturn', 'Aquarius': 'Uranus & Saturn', 'Pisces': 'Neptune & Jupiter'}
    elements = {'Aries': 'Fire', 'Taurus': 'Earth', 'Gemini': 'Air', 'Cancer': 'Water', 'Leo': 'Fire', 'Virgo': 'Earth', 'Libra': 'Air', 'Scorpio': 'Water', 'Sagittarius': 'Fire', 'Capricorn': 'Earth', 'Aquarius': 'Air', 'Pisces': 'Water'}
    
    sum_digits = sum(int(digit) for digit in f"{day}{month}{year}")
    while sum_digits > 9:
        sum_digits = sum(int(digit) for digit in str(sum_digits))
    
    return {
        "zodiacSign": zodiac_sign, "rulingPlanet": ruling_planets.get(zodiac_sign), "element": elements.get(zodiac_sign),
        "lifePathNumber": sum_digits, "dayOfWeek": date_object.strftime('%A'), "birthDate": dob_string
    }

# --- PROMPT TEMPLATES ---
# (You can copy your full detailed prompts here later, these are summaries for speed)
def master_prompt(profile_data: dict) -> str:
    return f"Generate a 6-part personal blueprint for a user with these traits: {profile_data}"
def explore_career_prompt(profile_data: dict, career: str) -> str:
    return f"Generate a 4-part detailed career exploration for a {profile_data['zodiacSign']} exploring the career of {career}."
def compare_prompt(p1: dict, p2: dict) -> str:
    return f"Generate a 4-part compatibility report for a {p1['zodiacSign']} and a {p2['zodiacSign']}."
def daily_reading_prompt(profile_data: dict) -> str:
    return f"Generate a short, positive daily focus for a {profile_data['zodiacSign']}."
def life_path_prompt(profile_data: dict) -> str:
    return f"Generate a detailed deep dive on Life Path number {profile_data['lifePathNumber']}."

# --- MCP TOOLS ---
@mcp.tool(description="Validates the server for the Puch AI hackathon.")
async def validate(token: Annotated[str, Field(description="The bearer token.")]) -> dict:
    return {"phone_number": os.getenv("MY_NUMBER")}

async def run_gemini_prompt(prompt_text: str) -> str:
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = await model.generate_content_async(prompt_text)
    return response.text

@mcp.tool(description="Generates a deep, personal cosmic profile.")
async def profile(dob: Annotated[str, Field(description="Birthdate in dd-mm-yyyy.")]) -> str:
    profile_data = calculate_profile_data(dob)
    return await run_gemini_prompt(master_prompt(profile_data))

@mcp.tool(description="Explores a career path in more detail.")
async def explore(topic: str, subject: str, dob: str) -> str:
    if topic.lower() == 'career':
        profile_data = calculate_profile_data(dob)
        return await run_gemini_prompt(explore_career_prompt(profile_data, subject))
    return "Sorry, I can only explore 'career'."

@mcp.tool(description="Compares two birthdates for compatibility.")
async def compare(dob1: str, dob2: str) -> str:
    profile_data1 = calculate_profile_data(dob1)
    profile_data2 = calculate_profile_data(dob2)
    return await run_gemini_prompt(compare_prompt(profile_data1, profile_data2))

@mcp.tool(description="Gets a daily cosmic focus.")
async def daily(dob: str) -> str:
    profile_data = calculate_profile_data(dob)
    return await run_gemini_prompt(daily_reading_prompt(profile_data))

@mcp.tool(description="Gets a deep dive on your Life Path number.")
async def lifepath(dob: str) -> str:
    profile_data = calculate_profile_data(dob)
    return await run_gemini_prompt(life_path_prompt(profile_data))

if __name__ == "__main__":
    mcp.run()