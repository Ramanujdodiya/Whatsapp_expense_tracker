import sys
import os
import logging
# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Form, Response, status,HTTPException
from twilio.twiml.messaging_response import MessagingResponse

from .commands import COMMANDS
from .logger import configure_logs
from .messages import (
    COMMAND_UNSUPPORTED_ERROR_MSG,
    UNEXPECTED_ERROR_MSG,
    USER_ORG_ERROR_MSG,
)

# Configure logs to appear in the terminal.
configure_logs()

# Creates the FastAPI web server.
server = FastAPI()


@server.get("/", status_code=status.HTTP_200_OK)
def health_check() -> str:
    """Endpoint to check that the server is running."""
    return "ok"


@server.post("/twilio", status_code=status.HTTP_202_ACCEPTED)
async def twilio(response: Response, From: str = Form(...), Body: str = Form(...)) -> str:
    try:
        logging.info(f"Received message from {From} with body {Body}")

        # Build the default Twilio TwiML response.
        twilio_response = MessagingResponse()
        twilio_response.message(UNEXPECTED_ERROR_MSG)

        message = ""
        for command in COMMANDS.values():
            logging.info(f"Checking command: {command.regexp}")
            if not command.match(body=Body):
                logging.info(f"Command {command.regexp} did not match.")
                continue

            whatsapp_phone = From.replace(" ", "+").split(":")[1]
            logging.info(f"Authorized phone: {whatsapp_phone}")
            is_authorized, user, organization = command.is_authorized(whatsapp_phone)
            logging.info(f"Authorization status: {is_authorized}, User: {user}, Organization: {organization}")
            if not is_authorized:
                message = USER_ORG_ERROR_MSG.format(phone=whatsapp_phone)
                break
            try:        
                result = command.execute(
                    organization,
                    commands=list(COMMANDS.values()),
                    body=Body,
                    user=user,
                    whatsapp_phone=whatsapp_phone,
                )
                logging.info(f"Command execution result: {result}")
            except Exception as e:
                    logging.error(f"Error executing command {command.regexp}: {e}")
                    raise HTTPException(status_code=500, detail="Error executing command")    
            try:
                    if isinstance(result, dict):
                        message = command.message(organization, user, **result)
                    elif isinstance(result, str):
                        message = result
                    else:
                        message = command.message(organization, user)
                    break
            except Exception as e:
                    logging.error(f"Error creating message for command {command.regexp}: {e}")
                    raise HTTPException(status_code=500, detail="Error creating message")   

        if message == "":
            message = COMMAND_UNSUPPORTED_ERROR_MSG.format(val_1=Body)

        # The final response is assembled.
        twilio_response = MessagingResponse()
        twilio_response.message(message)
        return Response(
            content=str(twilio_response),
            status_code=status.HTTP_202_ACCEPTED,
            headers={"Content-Type": "text/xml"},
            media_type="text/xml",
        )
    except Exception as e:
        logging.error(f"Error processing the request: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")