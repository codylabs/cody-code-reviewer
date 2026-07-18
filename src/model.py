import time
import logging
import config

logging.basicConfig(level=logging.DEBUG if config.DEBUG_MODE else logging.INFO)

MODEL = config.MODEL

SYSTEM_PROMPT = "You are a senior software engineer at Google reviewing a pull request."


def query_model(prompt: str, retries=3, base_delay=1.0) -> str:
    """Send a prompt to the configured model provider and return the response.

    Models named claude-* are sent to the Anthropic API; everything else goes to OpenAI.
    """
    if MODEL.lower().startswith("claude"):
        return query_claude(prompt, retries=retries, base_delay=base_delay)
    return query_openai(prompt, retries=retries, base_delay=base_delay)


def query_openai(prompt: str, retries=3, base_delay=1.0) -> str:
    """Send a prompt to the OpenAI API and return the response or an error message, with retry logic."""
    from openai import OpenAI
    import openai

    client = OpenAI(
        api_key=config.OPENAI_API_KEY,
    )

    attempt = 0
    while attempt < retries:
        try:
            completion = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
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


def query_claude(prompt: str, retries=3, base_delay=1.0) -> str:
    """Send a prompt to the Anthropic API and return the response or an error message, with retry logic."""
    import anthropic

    client = anthropic.Anthropic(
        api_key=config.ANTHROPIC_API_KEY,
    )

    attempt = 0
    while attempt < retries:
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=16000,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            text = "".join(block.text for block in response.content if block.type == "text")
            if text:
                return text
            logging.error(f"Claude returned no text on attempt {attempt + 1} (stop_reason: {response.stop_reason})")
            return f"Claude returned no review (stop_reason: {response.stop_reason})."
        except anthropic.RateLimitError as rate_error:
            logging.error(f"Anthropic rate limit on attempt {attempt + 1}: {rate_error}")
            time.sleep(base_delay * (2 ** (attempt + 1)))
        except anthropic.APIStatusError as api_error:
            logging.error(f"Anthropic APIStatusError on attempt {attempt + 1}: {api_error}")
            time.sleep(base_delay * (2 ** attempt))
        except Exception as e:
            logging.error(f"General error on attempt {attempt + 1}: {str(e)}")
            time.sleep(base_delay * (2 ** attempt))
            if attempt == retries - 1:
                logging.critical(f"Final attempt failed with error: {str(e)}")
        finally:
            attempt += 1

    error_message = "Failed to query the Anthropic API after several attempts."
    logging.error(error_message)
    return error_message
