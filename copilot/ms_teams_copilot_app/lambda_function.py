# pylint: disable=ef-restricted-imports, unused-variable, unused-import

from __future__ import absolute_import
import json
import os
import sys
import traceback
import requests
import asyncio
from teams import Application
from teams import ApplicationOptions
from teams.state import TurnState
from botbuilder.core.teams.teams_info import TeamsInfo
from botbuilder.core import TurnContext
from botbuilder.core import CardFactory
from botbuilder.core import MessageFactory
from botbuilder.schema import Activity
from botbuilder.schema import ActivityTypes
from botbuilder.schema import HeroCard
from botbuilder.schema import ChannelAccount
from botbuilder.schema import ConversationParameters
from botbuilder.schema.teams import MessagingExtensionQuery
from botbuilder.schema.teams import MessagingExtensionAttachment
from botbuilder.schema.teams import MessagingExtensionResult 
from botbuilder.schema.teams import MessagingExtensionResponse
from flask import Flask, request
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.schema.teams import TeamsChannelData
from teams.ai.citations.citations import AIEntity
from ef_teams_adapter import EFTeamsAdapter

request_type = 'bot'

class TeamsAppConfig:
    """Bot Configuration"""
    PORT = 8000
    APP_ID = os.environ.get("APP_ID")
    APP_PASSWORD = os.environ.get("APP_PASSWORD")

app_config = TeamsAppConfig()
teams_app = Application[TurnState](
    ApplicationOptions(
        bot_app_id=app_config.APP_ID,
        adapter=EFTeamsAdapter(app_config),
    )
)

def make_request(url, headers, payload):
    try:
        print(f"Making request to {url} with headers: {headers} and payload: {payload}")
        response = requests.post(url, json=payload, headers=headers)
        print(f"Received response from {url}: {response}")
        print(f"Response json: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred in getting the response from vscode: {e}")
        traceback.print_exc()
        return None

INSTANCE_URI = os.environ.get("INSTANCE_URI")
TENANT_INFO_URL = f"https://{INSTANCE_URI}/api/copilot/teams_api/tenant_info"
PROCESS_MESSAGE_URL = "{INSTANCE_URI}/api/copilot/teams_api/conversation"
def get_headers(region):
    REGION_TO_AUTH_HEADER_MAPPING = json.loads(os.environ.get("REGION_TO_AUTH_HEADER", {}))
    AUTH_HEADER = REGION_TO_AUTH_HEADER_MAPPING.get(region, '')
    return {
        'Authorization': AUTH_HEADER,
        'accept': 'application/json'
    }


WELCOME_CARD = {
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "type": "AdaptiveCard",
    "version": "1.4",
    "body": [
        {
            "type": "Container",
            "items": [
                {
                    "type": "TextBlock",
                    "text": "👋 Hello!",
                    "weight": "Bolder",
                    "size": "ExtraLarge",
                    "color": "Accent",
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": "I'm Eightfold Copilot Bot.",
                    "weight": "Bolder",
                    "size": "Large",
                    "spacing": "Small",
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": "Here’s what I can do for you:",
                    "weight": "Bolder",
                    "spacing": "Medium",
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": "💼 **Discover suitable projects**",
                    "spacing": "Small",
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": "🎓 **Find courses or upskilling content**",
                    "spacing": "Small",
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": "👥 **Search for experts in your organization**",
                    "spacing": "Small",
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": "Just type your query, and I'll help you with the rest.",
                    "weight": "Bolder",
                    "spacing": "Medium",
                    "wrap": True
                }
            ]
        }
    ]
}

WELCOME_MESSAGE="<h3>Hello! I am Eightfold Copilot and part of this chat.</h3>I can help you with:<ul><li><strong>Search for experts in your organization</strong></li><li><strong>Discover suitable projects</strong></li><li><strong>Find upskilling resources</strong></li></ul>"

# Logic to send the payload to vscode for processing
def process_user_message(payload):
    # Step 1 : Get tenant_info => This will handle the regions and user impersonation
    # Todo: (vmahawar) Store the tenant_info in the cache for future use
    region = "us-west-2"
    headers = get_headers(region)
    response = make_request(TENANT_INFO_URL, headers, payload)
    # Step 2 : Make request to the target region instance
    if response.get("success"):
        tenant_info = response.get("data")
        INSTANCE_URI = tenant_info.get("instance_url")
        PROCESS_MESSAGE_FULL_URL = PROCESS_MESSAGE_URL.format(INSTANCE_URI=INSTANCE_URI)
        region = tenant_info.get("region")
        headers = get_headers(region)
        response = make_request(PROCESS_MESSAGE_FULL_URL, headers, payload)
    return region, response

async def get_user_email_and_tenant_from_context(context):
    user_id = context.activity.from_property.id
    teams_current_user = await TeamsInfo.get_member(context, user_id)
    current_user_email = teams_current_user.email
    tenant_id = context.activity.conversation.tenant_id or context.activity.channel_data.get('tenant', {}).get('id')
    return current_user_email, tenant_id

async def get_user_email_and_tenant_for_ms_copilot(context: TurnContext):
    user_id = context.activity.from_property.id
    params = ConversationParameters(
                is_group=False,
                bot=context.activity.recipient,
                members=[ChannelAccount(id=user_id)],
                tenant_id=context.activity.conversation.tenant_id or context.activity.channel_data.get('tenant', {}).get('id'),
            )
    #  create a fake conversation between the bot and the user to extract the conversation id and in turn the email
    local_adapter = BotFrameworkAdapter(BotFrameworkAdapterSettings(app_id=app_config.APP_ID, app_password=app_config.APP_PASSWORD))
    connector_client = await local_adapter.create_connector_client(context.activity.service_url)
    conversation_reference = TurnContext.get_conversation_reference(context.activity)
    conversation_resource_response = await connector_client.conversations.create_conversation(parameters=params)
    conversation_reference.conversation.id = conversation_resource_response.id
    old_conversation_id = context.activity.conversation.id
    context.activity.conversation.id = conversation_resource_response.id
    current_user_email, tenant_id = await get_user_email_and_tenant_from_context(context)
    context.activity.conversation.id = old_conversation_id
    return current_user_email, tenant_id

# This will be triggered from the M365 Copilot
@teams_app.message_extensions.query("eightfoldCopilot")
async def on_message_extension(context: TurnContext, _state: TurnState, query: MessagingExtensionQuery):
    global request_type
    request_type = 'm365_copilot'
    from_compose = False
    if context.activity.channel_data.get('source', {}).get('name') == 'powerbar' or context.activity.channel_data.get('source', {}).get('name') == 'compose':
        from_compose = True
    current_user_email, tenant_id = await get_user_email_and_tenant_for_ms_copilot(context)
    user_message = ''
    print("Trying to get the user query from the parameters")
    for param in query.parameters:
        if param.name == 'userQuery':
            user_message = param.value
            break
    if from_compose:
        source = "compose"
    else:
        source = "ms_copilot"
    print("User message received from M365 Copilot: ", user_message)
    payload = {
        "current_user_email": current_user_email,
        "tenant_id": tenant_id,
        "user_query": user_message,
        "params": None,
        "source": source
    }
    print("Payload from M365 Copilot for processing user message", payload)
    region, res = process_user_message(payload)
    if res.get("success"):
        new_messages_to_send = res.get("data")
        print("New messages to send from M365 Copilot", new_messages_to_send)
        attachments = []
        for message in new_messages_to_send:
            if "cards" in message:
                for card in message.get("cards"):
                    content_card_data = card.get("content_card")
                    preview_card_data = card.get("preview_card_data", {})
                    preview_card = HeroCard(
                        title=preview_card_data.get("title"),
                        subtitle=preview_card_data.get("subtitle"),
                        text=preview_card_data.get("text"),
                    )
                    attachments.append(
                        MessagingExtensionAttachment(
                            content_type=CardFactory.content_types.adaptive_card,
                            content=content_card_data,
                            preview=CardFactory.hero_card(preview_card)
                        )
                    )
    else:
        message = res.get("error", "Sorry, I couldn't find any results for your query.")
        print("Message received from M365 Copilot: ", message)
        if message:
            attachments = []
            preview_card = HeroCard(
            title="",
            subtitle="",
            text=message,
            )
            attachments.append(
                MessagingExtensionAttachment(
                    content_type=CardFactory.content_types.hero_card,
                    content=preview_card,
                    preview=CardFactory.hero_card(preview_card)
                )
            )
            return MessagingExtensionResponse(compose_extension=MessagingExtensionResult(type="result", attachment_layout="list", attachments=attachments))

    response = MessagingExtensionResponse(compose_extension=MessagingExtensionResult(type="result", attachment_layout="list", attachments=attachments))
    print("Sending response to M365 Copilot", response)
    return response

def create_ai_generated_activity(text=None, attachments=None, channel_data=None):
    """Helper function to create an Activity with AI-generated content."""
    return Activity(
        type=ActivityTypes.message,
        text=text,
        attachments=attachments,
        channel_data=channel_data,
        entities=[
            AIEntity(
                citation=[],
                additional_type=["AIGeneratedContent"],
            ),
        ],
    )

@teams_app.activity("message")
async def on_message(context: TurnContext, _state: TurnState):
    global request_type
    request_type = 'bot'
    current_user_email, tenant_id = await get_user_email_and_tenant_from_context(context)
    user_query = context.activity.text
    if context.activity.entities:
        for entity in context.activity.entities:
            if entity.type == "mention" and entity.additional_properties and entity.additional_properties.get('mentioned', {}).get('id') == context.activity.recipient.id:
                user_query = user_query.replace(entity.additional_properties.get('mentioned', {}).get('name', {}), "").strip()
                if not user_query:
                    await asyncio.sleep(2)
                    await context.send_activity(MessageFactory.text("Please provide a non-empty user query after the app name."))
                    return True
    params = context.activity.value
    print("Received context activity: ", context.activity)
    if reply_to_id := context.activity.reply_to_id:
        params['reply_to_id'] = reply_to_id
    payload = {
        "current_user_email": current_user_email,
        "tenant_id": tenant_id,
        "user_query": user_query,
        "params": params,
    }
    region, res = process_user_message(payload)
    if res.get("success"):
        new_messages_to_send = res.get("data")
        contains_cards = False
        for message in new_messages_to_send:
            msg = None
            if "message" in message:
                if "reply_to" in message:
                    quote = user_query
                    reply = message["message"]
                    response_text = f"> {quote}\n\n{reply}"
                    msg = await context.send_activity(response_text)
                    message["message_id"] = msg.id
                else:
                    msg = await context.send_activity(create_ai_generated_activity(text=message["message"], channel_data=TeamsChannelData().deserialize(context.activity.channel_data)))
                    message["message_id"] = msg.id
            elif "cards" in message:
                contains_cards = True
                cards = []
                for card in message["cards"]:
                    cards.append(CardFactory.adaptive_card(card))
                if len(cards) == 1:
                    msg = create_ai_generated_activity(attachments=cards, channel_data=TeamsChannelData().deserialize(context.activity.channel_data))
                elif len(cards) > 1:
                    msg = MessageFactory.carousel(cards[:10])
                    msg.entities = [
                        AIEntity(
                            citation=[],
                            additional_type=["AIGeneratedContent"],
                        ),
                    ]
                    msg.channel_data = TeamsChannelData().deserialize(context.activity.channel_data)
                if msg and "update_message_id" in message:
                    msg.id = message["update_message_id"]
                    sent_msg = await context.update_activity(msg)
                else:
                    sent_msg = await context.send_activity(msg)
                message["message_id"] = sent_msg.id
        if contains_cards:
            print("Updated msgs with id: ", new_messages_to_send)
            make_request(f"https://{INSTANCE_URI}/api/copilot/teams_api/cache", get_headers(region), new_messages_to_send)
    else:
        error = res.get("error") or "An error occurred in processing the user query, please try again later."
        await context.send_activity(error)
    return True

@teams_app.activity("messageUpdate")
async def on_message_update(context: TurnContext, _state: TurnState):
    await context.send_activity("Please re-enter a new prompt; editing is not currently supported.")
    return True

# This will be triggered whenever there are any errors raised in the bot
# TODO: (vmahawar) Add logic to send those errors to emails
@teams_app.error
async def on_error(context: TurnContext, error: Exception):
    print(f"\n [on_turn_error] Unhandled Exception in Teams Application: {error}", file=sys.stderr)
    traceback.print_exc()
    await context.send_activity("We are unable to process your request at the moment. Please type ‘Reset’ to refresh and restart the conversation. This will not delete your previous conversation but will reset the current context.")

async def send_welcome_message(context: TurnContext, message: str):
    """Function to send a welcome message to newly added members."""
    if context.activity.members_added:
        for member in context.activity.members_added:
            if member.id != context.activity.recipient.id:
                await context.send_activity(MessageFactory.text(message))

@teams_app.activity("installationUpdate")
async def on_installation_update(context: TurnContext, _state: TurnState):
    """Triggered whenever the bot is installed or updated in a team."""
    await context.send_activity(MessageFactory.attachment(CardFactory.adaptive_card(WELCOME_CARD)))
    current_user_email, tenant_id = await get_user_email_and_tenant_from_context(context=context)
    region = "us-west-2"
    headers = get_headers(region)
    payload = {
        "current_user_email": current_user_email,
        "tenant_id": tenant_id,
        "user_query": None,
        "params": None,
    }
    response = make_request(TENANT_INFO_URL, headers, payload)
    if not response.get("success"):
        await context.send_activity("To access this app, your organisation must have an active Eightfold Copilot license. Please contact your HR team for further assistance.")
    return True


@teams_app.activity("conversationUpdate")
async def on_members_added(context: TurnContext, _state: TurnState):
    """Triggered whenever new members are added to the team."""
    # if conversation type is group, send welcome message
    if context.activity.conversation.conversation_type == "personal":
        return True
    await send_welcome_message(context, WELCOME_MESSAGE)
    return True

# creating the flask request for teams Application
flask_app = Flask(__name__)
flask_app.route('/process_user_query', methods=['POST'])
def process_user_query():
    res = asyncio.run(teams_app.process(request))
    if not isinstance(res, bool):
        res = res.json
    return res

# handler for the lambda
def app_handler(event, context):
    print("Received event: ", event)
    try:
        method = event.get('httpMethod')
        headers = event.get('headers')
        data = event.get('body')
        print("Making request to process user query")
        print("Headers: ", headers)
        print("Payload: ", data)
        with flask_app.test_request_context('/process_user_query', method=method, headers=headers, data=data):
            res = process_user_query()
            print("Response received: ", res)
    except Exception as e:
        print(e)
        traceback.print_exc()
        res = False
    if request_type == 'm365_copilot':
        try:
            res = json.loads(json.dumps(res))
            if isinstance(res, dict) and "composeExtension" in res and "composeExtension" in res["composeExtension"]:
                res = res["composeExtension"]
        except Exception as e:
            print("An error occurred in parsing the response from the bot", e)
            traceback.print_exc()
            res = False
    else:
        res = True
    resp_obj = {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
        },
        'body': json.dumps(res)
    }
    print("Sending back the following response", resp_obj)
    return resp_obj
