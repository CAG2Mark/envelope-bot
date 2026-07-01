import logging
import time
import disnake

from threading import Thread

from disnake import ForumChannel, HTTPException, InteractionContextTypes
from disnake.ext import commands
from disnake import TextInputStyle

from util.messagedata import MessageData, MessageDatabase

def make_embed(title: str, message: str) -> disnake.Embed:
    return disnake.Embed(
        title=title,
        description= message,
        color=disnake.Colour.green()
    )

def error_embed(message: str) -> disnake.Embed:
    return disnake.Embed(
        description=":x: " + message,
        color=disnake.Colour.red()
    )

def warn_embed(message: str) -> disnake.Embed:
    return disnake.Embed(
        description=":warning: " + message,
        color=disnake.Colour.yellow()
    )

# Subclassing the modal.
class MessageModal(disnake.ui.Modal):
    def __init__(self, duration: int, database: MessageDatabase):
        self.database = database
        self.duration = duration

        # The details of the modal, and its components
        components = [
            disnake.ui.TextInput(
                label="Enter your message.",
                placeholder="Your message. Encrypt your message for maximum privacy.",
                custom_id="message",
                style=TextInputStyle.paragraph,
            ),
        ]
        super().__init__(title="Send Envelope", components=components)

    # The callback received when the user input is completed.
    async def callback(self, inter: disnake.ModalInteraction):
        title = inter.user.display_name + " sent you an envelope!"
        expiry = int(time.time()) + 86400 * self.duration
        desc = f"Press the button below to view the message. This action will notify {inter.user.mention}.\n\nExpires <t:{expiry}:R>."
        btn = disnake.ui.Button(label="View Message", style=disnake.ButtonStyle.blurple, custom_id="view_message"),
        await inter.response.send_message(embed=make_embed(title, desc), components=[btn])
        message = (await inter.original_response())
        data = MessageData(
            expiry,
            message.id,
            message.jump_url,
            inter.user.id,
            inter.text_values["message"]
        )
        self.database.add(data)

class Bot:
    logger = logging.getLogger("envelope-bot")
    
    database: MessageDatabase

    def __init__(self, token, database: MessageDatabase) -> None:
        intents = disnake.Intents.default()

        self.database = database
        
        client = commands.InteractionBot(intents=intents)
        self.client = client

        self.initialized = False
        
        @client.event
        async def on_ready():
            self.logger.info(f"Successfully logged in to Discord with username {client.user}")
            # self.timer.start()
            self.initialized = True 

        @client.slash_command(name='envelope', 
                              description='Creates a message that others must notify you to open.', 
                              contexts=InteractionContextTypes.all())
        @commands.install_types(user=True)
        async def envelope_command(
            inter: disnake.ApplicationCommandInteraction,
            duration: int = commands.Param(default=5, name="duration", description="How long others have to open the message. Must be between 1 and 7 days. Defaults to 5.", gt=1, lt=7)
        ):
            await inter.response.send_modal(MessageModal(duration, database))
        
        @client.listen("on_button_click")
        async def button_listener(inter: disnake.MessageInteraction):
            if inter.component.custom_id not in ["view_message"]:
                # We filter out any other button presses except
                # the components we wish to process.
                return
            
            msg_id = inter.message.id
            data = self.database.get(msg_id)
            if data == None:
                embed = error_embed("This envelope is invalid or has expired.")
                await inter.response.send_message(embed=embed, ephemeral=True)
                return
            
            await inter.response.send_message(data.message, ephemeral=True)

            author = await client.get_or_fetch_user(data.author)
            if not author: return
            await author.send(f"{inter.user.mention} accessed your envelope: {data.url}.")

        client.run(token)