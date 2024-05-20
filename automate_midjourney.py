import json
import asyncio
import logging
import os
import playwright
import random
import re
import requests
import shutil
import time
import uuid
from loguru import logger
from playwright.async_api import async_playwright, Page
from playwright.sync_api import sync_playwright
from playwright._impl._api_types import Error as PlaywrightError

num_iterations = 1

# Get logger for this file
logger = logging.getLogger(__name__)
# Set logging level to INFO
logger.setLevel(logging.INFO)

# Define a custom log format without %(asctime)s
log_format = logging.Formatter('[%(levelname)s] [%(pathname)s:%(lineno)d] - %(message)s - [%(process)d:%(thread)d]')

file_handler = logging.FileHandler('midjourney_automation.log', mode='a')  # Create file handler
file_handler.setFormatter(log_format)  # Set log format for file handler
logger.addHandler(file_handler)  # Add file handler to logger

console_handler = logging.StreamHandler()  # Create console handler
console_handler.setFormatter(log_format)  # Set log format for console handler
logger.addHandler(console_handler)  # Add console handler to logger

# Add condition to check if the current log statement is the same as the previous log statement, if so then don't log it
class NoRepeatFilter(logging.Filter):
    """Filter to ignore repeated log messages."""
    def __init__(self, name=''):
        """Initialize the filter.
        Args:
            name (str): Name of the filter.
        """
        super().__init__(name)
        self.last_log = None

    def filter(self, record):
        """Filter out repeated log messages.
        Args:
            record (LogRecord): Log record to be filtered.
        Returns:
            bool: True if log message is not a repeat, False otherwise.
        """

        # Ignore the %(asctime)s field when comparing log messages
        current_log = record.getMessage().split(' - ', 1)[-1]
        if current_log == self.last_log:
            return False
        self.last_log = current_log
        return True

# Create an instance of the NoRepeatFilter and add it to the logger
no_repeat_filter = NoRepeatFilter()
logger.addFilter(no_repeat_filter)

def random_sleep():
    """Sleep for a random amount of time between 1 and 5 seconds."""
    time.sleep(random.randint(1, 5))


import aiohttp

async def download_upscaled_images(page, prompt_text: str):
    """
    Function to download upscaled images.

    Parameters:
    - page: The page to operate on.
    - prompt_text (str): The text of the prompt.

    Returns:
    - None
    """
    try:
        # Get all image URLs
        image_urls = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a.originalLink__0d99e'))
                .map(a => a.href)
                .filter(href => href.startsWith('https://cdn.discordapp.com/attachments'));
        }''')
        
        # Select last 4 images
        image_urls = image_urls[-4:]
        
        # Clear the txt file before writing new URLs
        with open("mid_journey_images.txt", 'w') as f:
            f.write("")
        
        # Download each image and each URL to a .txt file
        async with aiohttp.ClientSession() as session:
            for i,url in enumerate(image_urls):
                async with session.get(url) as resp:
                    if resp.status == 200:
                        with open("mid_journey_images.txt", 'a') as f:
                            f.write(url + "\n")
                        file_name = "image_"+str(i+1)+".png"
                        with open(file_name, 'wb') as f:
                            f.write(await resp.read())
                        logger.info(f"Successfully downloaded {url} to {file_name}")
                    else:
                        logger.error(f"Failed to download {url}: {resp.status}")
    except Exception as e:
        logger.error(f"An error occurred while downloading upscaled images: {e}")
        raise e

async def submit_command(page, prompt: str):
    try:
        # prompt_text = gpt3_midjourney_prompt(prompt)
        prompt_text = prompt # "Generate a logo for coffee place with coffee mug, coasters, coffee beans. It should in realistic and in vibrant blue color"
        random_sleep()
        pill_value_locator = 'span.optionPillValue__495fe'
        await page.fill(pill_value_locator, prompt_text)
        random_sleep()
        await page.keyboard.press("Enter")
        logger.info(f'Successfully submitted prompt: {prompt_text}')
        await wait_and_select_upscale_options(page, prompt_text)
    except Exception as e:
        logger.error(f"An error occurred while submitting the prompt: {e}")
        raise e


async def get_last_message(page) -> str:
    """
    Function to get the last message from the provided page.

    Parameters:
    - page: The page from which to fetch the last message.

    Returns:
    - str: The text of the last message.
    """
    try:
        # await page.click('div[aria-label="Inbox"]')
        messages = await page.query_selector_all(".messageListItem__050f9")
        # messages = await page.query_selector_all(".container__7c2c1")
        # import pdb;
        # pdb.set_trace()
        if not messages:
            logger.error("No messages found on the page.")
            raise ValueError("No messages found on the page.")
        
        last_message = messages[-1]
        last_message_text = await last_message.evaluate('(node) => node.innerText')
       
        if not last_message_text:
            logger.error("Last message text cannot be empty.")
            raise ValueError("Last message text cannot be empty.")
        
        last_message_text = str(last_message_text)
        # import pdb;
        # pdb.set_trace()
        # Commented out for now, as it's not needed.
        # logger.info(f"Last message: {last_message_text}")

        # last_message_text = []
        # for message in messages:
            
        #     message_text = await message.evaluate('(node) => node.innerText')
        
        #     if not message_text:
        #         logger.error("Last message text cannot be empty.")
        #         raise ValueError("Last message text cannot be empty.")
            
        #     message_text = str(message_text)
        #     last_message_text.append(message_text)


        return last_message_text
    
    except Exception as e:
        logger.error(f"Error occurred: {e} while getting the last message.")
        raise e



async def main(bot_command: str, channel_url: str, PROMPT: str):
    """
    Main function that starts the bot and interacts with the page.

    Parameters:
    - bot_command (str): The command for the bot to execute.
    - channel_url (str): The URL of the channel where the bot should operate.
    - PROMPT (str): The prompt text.

    Returns:
    - None
    """
    try:
        browser = None
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://www.discord.com/login")

            # Get credentials securely
            email = os.environ.get("DISCORD_EMAIL")
            password = os.environ.get("DISCORD_PASSWORD")
            if not email or not password:
                logger.error("Error loading discord email or password from environment variables")
            
            await page.fill("input[name='email']", email)
            await asyncio.sleep(random.randint(1, 5))
            await page.fill("input[name='password']", password)
            await asyncio.sleep(random.randint(1, 5))
            await page.click("button[type='submit']")
            await asyncio.sleep(random.randint(5, 10))
            await page.wait_for_url("https://discord.com/channels/@me", timeout=15000)
            logger.info("Successfully logged into Discord.")
            await asyncio.sleep(random.randint(1, 5))

            for i in range(num_iterations):
                logger.info(f"Trying to open the channel. Iteration {i+1}")
                await open_discord_channel(page, channel_url, bot_command, PROMPT)
                logger.info(f"Iteration {i+1} completed.")
    except Exception as e:
        logger.error(f"Error occurred: {e} while executing the main function.")
        raise e
    finally:
        if browser:
            try:
                await browser.close()
            except PlaywrightError as e:
                if "Connection closed" in str(e):
                    logger.info("Browser connection already closed.")
                else:
                    logger.error(f"Error occurred: {e} while closing the browser.")
                    raise e


async def open_discord_channel(page, channel_url: str, bot_command: str, PROMPT: str):
    """
    Function to open a Discord channel and send a bot command.

    Parameters:
    - page: The page object representing the current browser context.
    - channel_url (str): The URL of the channel to open.
    - bot_command (str): The bot command to send.
    - PROMPT (str): The prompt text.

    Returns:
    - None
    """
    try:
        await page.goto(f"{channel_url}")
        await asyncio.sleep(random.randint(1, 5))
        await page.wait_for_load_state("networkidle")
        logger.info("Successfully opened the appropriate channel.")

        logger.info("Entering the specified bot command.")
        await send_bot_command(page, bot_command, PROMPT)
    
    except Exception as e:
        logger.error(f"An error occurred while opening the channel and entering the bot command: {e}")
        raise e


async def select_upscale_option(page, option_text: str):
    """
    Function to select an upscale option based on the provided text.

    Parameters:
    - page: The page object representing the current browser context.
    - option_text (str): The text of the upscale option to select.

    Returns:
    - None
    """
    try:
        upscale_option = page.locator(f"button:has-text('{option_text}')").locator("nth=-1")
        if not upscale_option:
            logger.error(f"No upscale option found with text: {option_text}.")
            raise ValueError(f"No upscale option found with text: {option_text}.")
        
        await upscale_option.click()
        logger.info(f"Successfully clicked {option_text} upscale option.")
    
    except Exception as e:
        logger.error(f"An error occurred while selecting the upscale option: {e}")
        raise e


async def send_bot_command(page, command: str, PROMPT: str):
    """
    Function to send a command to the bot in the chat bar.

    Parameters:
    - page: The page object representing the current browser context.
    - command (str): The command to send to the bot.
    - PROMPT (str): The prompt for the command.

    Returns:
    - None
    """
    try:
        logger.info("Clicking on chat bar.")
        chat_bar = page.get_by_role('textbox', name='Message @Midjourney Bot')
        await asyncio.sleep(random.randint(1, 5))

        logger.info("Typing in bot command")
        await chat_bar.fill(command + " ")
        #await chat_bar.fill(command)
        await asyncio.sleep(random.randint(1, 5))

        logger.info("Submitting the bot command.")
        await submit_command(page, PROMPT)

    except Exception as e:
        logger.exception(f"An error occurred while sending the bot command: {e}")
        raise e


def start_bot(art_type: str, bot_command: str, channel_url: str, descriptors: str, topic: str):
    """
    Function to start the bot with the specified parameters.

    Parameters:
    - art_type (str): The type of art to generate.
    - bot_command (str): The command to send to the bot.
    - channel_url (str): The URL of the channel where the bot is located.
    - descriptors (str): The descriptors to include in the prompt.
    - topic (str): The topic of the image to generate.

    Returns:
    - None
    """
    try:
        PROMPT = f"Generate a Midjourney prompt to result in an {art_type} image about {topic} include {descriptors}"
        logger.info(f"Prompt: {PROMPT}")

        asyncio.run(main(bot_command, channel_url, PROMPT))

    except Exception as e:
        logger.error(f"An error occurred while starting the bot: {e}")
        raise e


async def wait_and_select_upscale_options(page, prompt_text: str):
    """
    Function to wait for and select upscale options.

    Parameters:
    - page: The page to operate on.
    - prompt_text (str): The text of the prompt.

    Returns:
    - None
    """
    try:
        prompt_text = prompt_text.lower()

        # Repeat until upscale options are found
        while True:
            last_message = await get_last_message(page)
            # Check for 'U1' in the last message
            # for last_message in last_messages:

            if 'U1' in last_message:
                logger.info("Found upscale options. Attempting to upscale all generated images.")
                try:
                    await select_upscale_option(page, 'U1')
                    time.sleep(random.randint(3, 5))
                    await select_upscale_option(page, 'U2')
                    time.sleep(random.randint(3, 5))
                    await select_upscale_option(page, 'U3')
                    time.sleep(random.randint(3, 5))
                    await select_upscale_option(page, 'U4')
                    time.sleep(random.randint(3, 5))
                except Exception as e:
                    logger.error(f"An error occurred while selecting upscale options: {e}")
                    raise e

                try:
                    await download_upscaled_images(page, prompt_text)
                except Exception as e:
                    logger.error(f"An error occurred while downloading upscaled images: {e}")
                    raise e
                break  # Exit the loop when upscale options have been found and selected

            else:
                logger.info("Upscale options not yet available, waiting...")
                time.sleep(random.randint(3, 5))

    except Exception as e:
        logger.error(f"An error occurred while finding the last message: {e}")
        raise e

def check_api_key(api_key: str) -> str:
    """
    Function to check if the OpenAI API key is already set, if not, it prompts the user to set it.

    Parameters:
    - api_key (str): The OpenAI API key.

    Returns:
    - str: The OpenAI API key.
    """
    try:
        if api_key:
            logger.info("OpenAI API key for Midjourney Automation bot is already set in the environment.")
        else:
            raise ValueError("OpenAI API key not found in the environment.")
        
        return api_key
    except Exception as e:
        logger.error(f"An error occurred while checking or setting the OpenAI API key: {e}")
        raise e

def check_discord_credentials(email: str, password: str) -> None:
    """
    Function to check if the Discord credentials are already set, if not, it prompts the user to set them.

    Parameters:
    - None

    Returns:
    - None
    """
    try:
        if email and password:
            logger.info("Discord credentials for Midjourney Automation bot are already set in the environment.")
        else:
            raise ValueError("Discord credentials not found in the environment.")
    except Exception as e:
        logger.error(f"An error occurred while checking the Discord credentials: {e}")
        raise e
if __name__ == '__main__':
    api_key = os.environ.get("OPENAI_API_KEY")
    api_key = check_api_key(api_key)
    email = os.environ.get("DISCORD_EMAIL")
    password = os.environ.get("DISCORD_PASSWORD")
    check_discord_credentials(email, password)
    prompt_file_path = "gpt4_response.json"    
    with open(prompt_file_path, 'r') as file:
        prompt = json.load(file)
    logo_descriptions_without_text = prompt["Logo_Component"]["logo_descriptions_without_text"]
    bot_command = "/imagine"
    channel_url = "https://discord.com/channels/@me/1222529795347185760"
    asyncio.run(main(bot_command, channel_url, logo_descriptions_without_text))