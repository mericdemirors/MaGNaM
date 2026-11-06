import json

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .websocket_connection import add_connection, remove_connection


class MessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]

        if not user.is_authenticated:
            await self.close()
            return

        profile_id = await self.get_user_profile_id(user)

        self.profile_id = self.scope["url_route"]["kwargs"]["profile_id"]

        if str(profile_id) != str(self.profile_id):
            await self.close()
            return

        self.group_name = f"profile_{self.profile_id}"

        connection_allowed = await sync_to_async(add_connection)(
            user.id, self.channel_name
        )

        if not connection_allowed:
            await self.close()
            return

        self.connection_registered = True

        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()

    @database_sync_to_async
    def get_user_profile_id(self, user):
        return user.profile.id

    async def disconnect(self, close_code):
        if getattr(self, "connection_registered", False):
            await sync_to_async(remove_connection)(
                self.scope["user"].id, self.channel_name
            )

        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def new_message(self, event):
        data = event["message_data"]

        await self.send(
            text_data=json.dumps(
                {
                    "id": data["id"],
                    "sender": data["sender"],
                    "receiver": data["receiver"],
                    "message": data["message"],
                    "timestamp": data["timestamp"],
                    "is_read": data["is_read"],
                }
            )
        )

    async def read_message(self, event):
        data = event["read_data"]

        await self.send(
            text_data=json.dumps(
                {
                    "type": "read_message",
                    "id": data["id"],
                    "sender": data["sender"],
                    "receiver": data["receiver"],
                }
            )
        )
