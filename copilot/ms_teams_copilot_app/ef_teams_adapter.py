from __future__ import annotations

from typing import Optional, Any

from flask import jsonify, Response, Request
from aiohttp.web import HTTPUnauthorized
from botbuilder.core import Bot, CloudAdapterBase
from botbuilder.schema import Activity
from botframework.connector.auth import BotFrameworkAuthentication, BotFrameworkAuthenticationFactory
from botbuilder.core import Bot
from botbuilder.integration.aiohttp import ConfigurationBotFrameworkAuthentication
from teams.user_agent import _UserAgent


class EFCloudAdapter(CloudAdapterBase):
    def __init__(self, bot_framework_authentication: BotFrameworkAuthentication = None):
        """
        Initializes a new instance of the CloudAdapter class.

        :param bot_framework_authentication: Optional BotFrameworkAuthentication instance
        """
        if not bot_framework_authentication:
            bot_framework_authentication = BotFrameworkAuthenticationFactory.create()
        self._AUTH_HEADER_NAME = "authorization"
        self._CHANNEL_ID_HEADER_NAME = "channelid"
        super().__init__(bot_framework_authentication)

    async def process(self, request: Request, bot: Bot) -> Optional[Response]:
        if not request:
            raise TypeError("request can't be None")
        if not bot:
            raise TypeError("bot can't be None")
        try:
            if request.method == "POST":
                if "application/json" in request.headers["Content-Type"]:
                    print("Trying to read request body")
                    print("request", request)
                    body = request.json
                    print("Read request body", body)
                else:
                    return Response("Unsupported Media Type", status=415) # Unsupported Media Type
                activity: Activity = Activity().deserialize(body)
                if not activity.type:
                    return Response("Bad Request - missing activity type", status=400) # Bad Request
                auth_header = request.headers["Authorization"] if "Authorization" in request.headers else ""
                invoke_response = await self.process_activity(auth_header, activity, bot.on_turn)
                if invoke_response:
                    response = jsonify(invoke_response.body)
                    response.status_code = invoke_response.status
                    return response
                return Response(status=201)
            else:
                return Response("Method Not Allowed", status=405) # Method Not Allowed
        except (HTTPUnauthorized, PermissionError) as _:
            return Response("Unauthorized", status=401) # Unauthorized


class EFTeamsAdapter(EFCloudAdapter, _UserAgent):
    """
    An adapter that implements the Bot Framework Protocol
    and can be hosted in different cloud environments both public and private.
    """

    def __init__(self, configuration: Any) -> None:
        """
        Initializes a new instance of the TeamsAdapter class.
        """
        super().__init__(ConfigurationBotFrameworkAuthentication(configuration))

    async def process(self, request: Request, bot: Bot) -> Optional[Response]:
        res = await super().process(request, bot)
        if res:
            res.headers.add("User-Agent", self.user_agent)
        return res
