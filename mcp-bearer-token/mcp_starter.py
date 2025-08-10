import os
import datetime
from typing import Any, Dict
from dotenv import load_dotenv
import google.generativeai as genai
import uvicorn

# --- IMPORTS for FastAPI ---
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# --- END IMPORTS ---


# --- SETUP ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create our FastAPI application
app = FastAPI(title="AI Oracle")

# Add the CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- DATA CALCULATION & PROMPTS ---
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
    while sum_digits > 9 and sum_digits not in [11, 22, 33]:
        sum_digits = sum(int(digit) for digit in str(sum_digits))
    return {"zodiacSign": zodiac_sign, "rulingPlanet": ruling_planets.get(zodiac_sign), "element": elements.get(zodiac_sign), "lifePathNumber": sum_digits, "dayOfWeek": date_object.strftime('%A'), "birthDate": dob_string}

def master_prompt(profile_data: dict) -> str:
    return f"""
You are 'The AI Oracle', a wise, empathetic, and modern cosmic guide. Your voice is insightful, encouraging, and profound. You are to generate a complete "Personal Blueprint" for a user based on the following data.
User's Cosmic Data:
- Zodiac Sign: {profile_data['zodiacSign']}
- Ruling Planet: {profile_data['rulingPlanet']}
- Element: {profile_data['element']}
- Numerology Life Path Number: {profile_data['lifePathNumber']}
- Day of Birth: {profile_data['dayOfWeek']}
Instructions:
Generate a response in 6 distinct sections, following the structure and tone described below precisely. Use Markdown for formatting.
Section 1: Your Core Identity
Start with a powerful, 2-3 sentence summary that weaves together their Zodiac Sign, Element, Ruling Planet, and Life Path Number. Explain how these energies combine to form their fundamental personality and purpose.
Section 2: Your Strengths & Challenges
Create two sub-sections. For each, provide exactly three bullet points.
- Your Strengths: List three key positive traits. Frame them as powers they possess.
- Your Challenges & Areas for Growth: List three potential struggles. Frame them not as weaknesses, but as constructive opportunities for growth and self-awareness.
Section 3: Your Cosmic Career Path
Based on their core traits, suggest 3 to 5 ideal career paths. For each path, provide a brief, one-sentence explanation for why their cosmic energy makes them a good fit for it.
Section 4: The Horizon Ahead: Opportunities & Problems
Provide a general outlook for the next 6-12 months. Do NOT make specific, testable predictions. Focus on broad themes.
- Opportunities on the Horizon: List two potential areas for positive growth, learning, or connection.
- Potential Problems to Navigate: List two potential internal or external challenges they should be mindful of. Frame this as advice for navigation, not a warning of inevitable doom.
Section 5: Cosmic Guidance
End with two pieces of wisdom.
- A Final Piece of Cosmic Advice: A single, profound, and memorable sentence that encapsulates a key lesson for their life path.
- Your Personal Mantra: A short, powerful "I am..." affirmation statement that they can use for empowerment. It must align with their core strengths.
Section 6: A Cosmic Wink 😉
Provide a single, fun, positive, and slightly quirky "serendipity alert" for the coming week. This should be a small, harmless event that will make the user smile if they notice it.
Examples:
- "Keep an eye out for the number {profile_data['lifePathNumber']}. It may appear in an unexpected place to let you know you're on the right path."
- "This week, you might hear a song you haven't heard in years that reminds you of a happy memory."
- "Don't be surprised if you unexpectedly reconnect with an old friend you were just thinking about."
"""
def explore_career_prompt(profile_data: dict, career: str) -> str: return f"Generate a 4-part detailed career exploration for a {profile_data['zodiacSign']} exploring the career of {career}."
def compare_prompt(p1: dict, p2: dict) -> str: return f"Generate a 4-part compatibility report for a {p1['zodiacSign']} and a {p2['zodiacSign']}."
def daily_reading_prompt(profile_data: dict) -> str: return f"Generate a short, positive daily focus for a {profile_data['zodiacSign']}."
def life_path_prompt(profile_data: dict) -> str: return f"Generate a detailed deep dive on Life Path number {profile_data['lifePathNumber']}."

async def run_gemini_prompt(prompt_text: str) -> str:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = await model.generate_content_async(prompt_text)
    return response.text

# --- TOOL LOGIC (Now as regular functions) ---
async def validate_tool(params: Dict[str, Any]) -> Dict[str, str]:
    return {"phone_number": os.getenv("MY_NUMBER")}

async def profile_tool(params: Dict[str, Any]) -> Dict[str, str]:
    profile_data = calculate_profile_data(params['dob'])
    content = await run_gemini_prompt(master_prompt(profile_data))
    return {"content": content}

async def explore_tool(params: Dict[str, Any]) -> Dict[str, str]:
    if params['topic'].lower() == 'career':
        profile_data = calculate_profile_data(params['dob'])
        content = await run_gemini_prompt(explore_career_prompt(profile_data, params['subject']))
        return {"content": content}
    return {"content": "Sorry, I can only explore 'career'."}

async def compare_tool(params: Dict[str, Any]) -> Dict[str, str]:
    profile_data1 = calculate_profile_data(params['dob1'])
    profile_data2 = calculate_profile_data(params['dob2'])
    content = await run_gemini_prompt(compare_prompt(profile_data1, profile_data2))
    return {"content": content}

async def daily_tool(params: Dict[str, Any]) -> Dict[str, str]:
    profile_data = calculate_profile_data(params['dob'])
    content = await run_gemini_prompt(daily_reading_prompt(profile_data))
    return {"content": content}

async def lifepath_tool(params: Dict[str, Any]) -> Dict[str, str]:
    profile_data = calculate_profile_data(params['dob'])
    content = await run_gemini_prompt(life_path_prompt(profile_data))
    return {"content": content}

# --- MAIN MCP ENDPOINT ---
@app.post("/mcp/")
async def mcp_endpoint(request: Request):
    try:
        body = await request.json()
        method = body.get('method')
        params = body.get('params')
        request_id = body.get('id')
        
        # Handle Authentication
        auth_header = request.headers.get('authorization')
        expected_token = f"Bearer {os.getenv('AUTH_TOKEN')}"
        if auth_header != expected_token:
            raise HTTPException(status_code=401, detail="Invalid token")

        result = None
        tool_map = {
            "validate": validate_tool,
            "profile": profile_tool,
            "explore": explore_tool,
            "compare": compare_tool,
            "daily": daily_tool,
            "lifepath": lifepath_tool,
        }

        if method in tool_map:
            result = await tool_map[method](params)
        else:
            # Handle discovery
            return {"jsonrpc": "2.0", "result": {"methods": list(tool_map.keys())}, "id": request_id}

        return {"jsonrpc": "2.0", "result": result, "id": request_id}

    except Exception as e:
        print(f"An error occurred: {e}")
        return {"jsonrpc": "2.0", "error": {"code": -32603, "message": "Internal server error"}, "id": body.get("id")}


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("mcp_starter:app", host="0.0.0.0", port=port)