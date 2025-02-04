import google.generativeai as genai
import asyncio
class GeminiDayLimit(Exception):
    def __init__(self):
        super().__init__("reached the gemini api call limit for the day")


gemini_api_calls = 0
gemini_api_day_limit = 1500
gemini_api_min_limit = 15
gemini_lock = asyncio.Lock()
async def gemini_api_call(model:genai.GenerativeModel,prompt:str):
    global gemini_api_calls
    async with gemini_lock:
        if(gemini_api_calls > gemini_api_day_limit):
            raise GeminiDayLimit
        await asyncio.sleep(60/gemini_api_min_limit)
        gemini_api_calls+=1
        return await model.generate_content_async(prompt)



