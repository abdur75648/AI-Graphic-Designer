import os
import json
import rich
import random
import base64
from openai import OpenAI
from anthropic import Anthropic
import google.generativeai as genai
from dotenv import load_dotenv

# import PIL.Image

# img = PIL.Image.open('image.png')
# img

load_dotenv()

client = OpenAI()
client.api_key = os.environ["OPENAI_API_KEY"]

anthroClient = Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)


genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

def compiledInput(maintext, subtext, placeOfEvent, timingOfEvent, contactDetails):
    input = {
                "title" : str(maintext),
                "tagline": str(subtext),
                "placeOfEvent": str(placeOfEvent),
                "timingOfEvent": str(timingOfEvent),
                "contactDetails": str(contactDetails)
    }
    return str(input)

def claudeCall(system_prompt, user_input = None):
    prompt = system_prompt
    messages = [
        {
            "role": "user",
            "content": str(prompt)
        }
    ]

    if user_input != None:
        messages.append(
            {
                "role": "user",
                "content": str(user_input)
            }
        )
    response = anthroClient.messages.create(
        max_tokens= 2048,
        messages = messages,
        model = "claude-3-opus-20240229"
    )

    return response.content

def geminiCall(prompt):
    model = genai.GenerativeModel('gemini-pro')
    # model = genai.GenerativeModel('gemini-pro-vision')
    response = model.generate_content(str(prompt))
    return response.text

def gpt4call(system_prompt, user_input = None):

    prompt = system_prompt

    messages = [
        {
            "role": "system",
            "content": str(prompt)
        }
    ]
    if user_input:
        messages.append({
            "role": "user",
            "content": str(user_input)
        })
    response = client.chat.completions.create(
        model = "gpt-4-0125-preview",
        response_format= {'type': 'json_object'},
        messages= messages,
        temperature=0.9
    )

    text_response = json.loads(response.choices[0].message.content)
    return text_response

# def midjourney(prompt, user_input):
#     with open("prompts/midJourney.txt") as journeyText:
#         prompt = journeyText.read()
    
def gpt4visioncall(img_url, maintext, subtext, placeOfEvent, timingOfEvent, contactDetails):
    with open("prompts/imgDescription.txt") as fileVision:
        prompt = fileVision.read()

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": str(prompt) #+ str(txt)
                },
                {
                    "type": "image_url",
                    "image_url":{
                        "url": str(img_url)
                    }
                }
            ]
        }
    ]

    response = client.chat.completions.create(
        model = "gpt-4-vision-preview",
        messages= messages,
        #response_format= {"type": "json_object"},
        temperature = 0.9
    )

    vision_response = response.choices[0].message.content
    return vision_response


user_input = input("Please input your request for the logo [press enter to choose random]: ")
if user_input == "":
    with open("prompts/random_logos.txt") as random_logos:
        logo_lines = random_logos.readlines()
    user_input = random.choice(logo_lines).strip()
print(f"User input: {user_input}")
# sys_prompt_file = open("prompts/inputParsing.txt", "r")
sys_prompt_file = open("prompts/logo_input_parsing.txt", "r")
sys_prompt = sys_prompt_file.read()
event_details = gpt4call(sys_prompt, user_input)
sys_prompt_file.close()

with open("prompts/logo_llm_element_placer.txt") as design_prompt_file:
    design_prompt = design_prompt_file.read()
rich.print_json(data = event_details)

design_prompt = design_prompt.replace(r'{title}', str(event_details["title"]))
design_prompt = design_prompt.replace(r'{tagline}', str(event_details["tagline"]))

print(design_prompt)

final_results = gpt4call(design_prompt)

###### Fix for missing 'Text_component_details_LIST' in final_results ######
if 'Text_component_details_LIST' not in final_results:
    if 'Logo_Component' in final_results:
        if 'Text_component_details_LIST' in final_results['Logo_Component']:
            final_results['Text_component_details_LIST'] = final_results['Logo_Component']['Text_component_details_LIST']
            del final_results['Logo_Component']
            print("There was a missing 'Text_component_details_LIST' in GPT response, but it was found in Logo_Component - moved to top level")
        else:
            raise Exception("Text_component_details_LIST not found in GPT response")

with open('gpt4_response.json', 'w') as f:
    json.dump(final_results, f, indent=4)

rich.print_json(data = final_results)
design_prompt_file.close()