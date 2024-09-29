import time
import logging
from openai import OpenAI
import openai
import config

logging.basicConfig(level=logging.DEBUG if config.DEBUG_MODE else logging.INFO)

OPENAI_API_KEY = config.OPENAI_API_KEY
OPENAI_MODEL = config.OPENAI_MODEL

client = OpenAI(
    api_key=OPENAI_API_KEY,
)

def query_openai(prompt: str, retries=3, base_delay=1.0) -> str:
    """Send a prompt to the OpenAI API and return the response or an error message, with retry logic."""
    attempt = 0
    while attempt < retries:
        try:
            completion = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a senior software engineer at Google reviewing a pull request."},
                    {"role": "user", "content": prompt}
                ]
            )
            return completion.choices[0].message.content
        except openai.APIError as api_error:
            logging.error(f"OpenAI APIError on attempt {attempt + 1}: {api_error}")
            if api_error.code == 429:
                logging.info("Rate limit exceeded, adjusting wait time.")
                time.sleep(base_delay * (2 ** (attempt + 1)))
            else:
                time.sleep(base_delay * (2 ** attempt))
        except Exception as e:
            logging.error(f"General error on attempt {attempt + 1}: {str(e)}")
            time.sleep(base_delay * (2 ** attempt))
            if attempt == retries - 1:
                logging.critical(f"Final attempt failed with error: {str(e)}")
        finally:
            attempt += 1

    error_message = "Failed to query OpenAI API after several attempts."
    logging.error(error_message)
    return error_message
