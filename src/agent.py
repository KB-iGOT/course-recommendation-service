import vertexai
from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    ToolConfig, HarmCategory, HarmBlockThreshold
)
from src.tools import bot_insights_tool, extract_function_calls, call_function
from src.prompts import DEFAULT_SYSTEM_PROMPT
from src.core.config import GOOGLE_PROJECT_ID, GOOGLE_LOCATION, GEMINI_MODEL, MODEL_TEMPERATURE
from src.memory.redis import store_messages_in_redis, read_messages_from_redis

vertexai.init(project=GOOGLE_PROJECT_ID, location=GOOGLE_LOCATION)

gemini_model = GenerativeModel(
    GEMINI_MODEL,
    generation_config=GenerationConfig(temperature=MODEL_TEMPERATURE),
    safety_settings= {
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY: HarmBlockThreshold.BLOCK_ONLY_HIGH
    },
    tools=[bot_insights_tool],
    tool_config = ToolConfig(
            function_calling_config=ToolConfig.FunctionCallingConfig(
                mode=ToolConfig.FunctionCallingConfig.Mode.AUTO
        )),
    system_instruction= DEFAULT_SYSTEM_PROMPT
)

def send_chat_message(query: str, session_id: str):
    chat_history = read_messages_from_redis(session_id)
    chat = gemini_model.start_chat(history= chat_history)

    # Send a chat message to the Gemini API
    response = chat.send_message(query)
    print(response.to_dict())
    
    function_call = response.candidates[0].content.parts[0].function_call
    # Check for a function call or a natural language response
    if function_call:
        function_calls = extract_function_calls(response)
        
        # Invoke a function that calls an external API
        function_api_response = call_function(function_calls)
       
        # Send the API response back to Gemini, which will generate a natural language summary or another function call
        response = chat.send_message(function_api_response)
    store_messages_in_redis(session_id, chat.history)
    return {
        "content": response.text, 
        "type" : "ai",
        "response_metadata": {
            "model_version": response.to_dict()["model_version"],
            "finish_reason": response.candidates[0].finish_reason
        }
    }
