import discord
from discord.ext import commands
import os
from keep_alive import keep_alive

# =================================================================================================
# ❗ YOUR CONFIGURATION SECTION - FILL THIS OUT!
# =================================================================================================

# --- CONFIGURATION FOR REACTION ROLES ---
REACTION_CONFIG = {
    "message_id": 1399030796223909920,
    "emoji": "♠️",
    "role_id": 1398556295438794776,
    "dm_message": "✅ You’re verified! 👋 We’re glad to have you 🃏 Let’s deal some cards ♠️ Have fun 🎉💵 | 📜 Don’t forget to read the rules!"
}

# --- CONFIGURATION FOR USER MENTION REPLY ---
USER_MENTION_CONFIG = {
    "user_id": 1244962723872247818, # ❗ MAKE SURE YOUR ACTUAL USER ID IS PASTED HERE
    "reply_message": "👀 You mentioned my DEV — he'll be with you shortly."
}

# --- CONFIGURATION FOR WELCOME MESSAGE ---
WELCOME_CONFIG = {
    "channel_id": None, # ❗ PASTE YOUR WELCOME CHANNEL ID HERE
    "welcome_description": "Your custom welcome message will go here!" # ❗ PASTE YOUR WELCOME DESCRIPTION HERE
}


# =================================================================================================
# BOT SETUP (You don't need to change this part)
# =================================================================================================

# Define intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.reactions = True

# Create bot instance
bot = commands.Bot(command_prefix='&', intents=intents)


# =================================================================================================
# BOT EVENTS AND COMMANDS
# =================================================================================================

@bot.event
async def on_ready():
    """Prints a message to the console when the bot is online."""
    print(f'Bot {bot.user} is online and ready! 🚀')


# --- Feature 1: Reaction Roles & DM on Verify ---
@bot.event
async def on_raw_reaction_add(payload):
    """Gives a role and sends a DM when a user reacts to a specific message."""
    if (payload.message_id == REACTION_CONFIG["message_id"] and
        str(payload.emoji) == REACTION_CONFIG["emoji"] and
        not payload.member.bot):

        guild = bot.get_guild(payload.guild_id)
        role = guild.get_role(REACTION_CONFIG["role_id"])

        if role:
            await payload.member.add_roles(role)
            print(f"Added role '{role.name}' to {payload.member.name}")
            try:
                await payload.member.send(REACTION_CONFIG["dm_message"])
                print(f"Sent verification DM to {payload.member.name}")
            except discord.Forbidden:
                print(f"Could not send DM to {payload.member.name}. DMs are disabled.")
        else:
            print(f"Error: Role with ID {REACTION_CONFIG['role_id']} not found.")

@bot.event
async def on_raw_reaction_remove(payload):
    """Removes a role when a user removes their reaction."""
    if (payload.message_id == REACTION_CONFIG["message_id"] and
        str(payload.emoji) == REACTION_CONFIG["emoji"]):

        guild = bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role = guild.get_role(REACTION_CONFIG["role_id"])

        if role and member:
            await member.remove_roles(role)
            print(f"Removed role '{role.name}' from {member.name}")


# --- Feature 2: Welcome Message ---
@bot.event
async def on_member_join(member):
    """Sends a welcome message when a new member joins the server."""
    # Check if welcome message is configured
    if not WELCOME_CONFIG["channel_id"]:
        print("Welcome message not configured - no channel ID set")
        return

    # Get the configured welcome channel
    welcome_channel = bot.get_channel(WELCOME_CONFIG["channel_id"])

    if welcome_channel:
        welcome_message = f"""🎉 **Welcome to {member.guild.name}!** 🎉

Hey {member.mention}! 👋

{WELCOME_CONFIG["welcome_description"]}

Welcome aboard, {member.display_name}! 🌟"""

        try:
            await welcome_channel.send(welcome_message)
            print(f"Sent welcome message for {member.name}")
        except Exception as e:
            print(f"Could not send welcome message: {e}")
    else:
        print(f"Welcome channel with ID {WELCOME_CONFIG['channel_id']} not found")


# --- Feature 3: Voice Channel Moderation ---
@bot.command()
@commands.has_permissions(move_members=True)
async def movevc(ctx, member: discord.Member, channel: discord.VoiceChannel):
    """Moves a member to a specified voice channel."""
    if member.voice is None:
        await ctx.send(f"{member.display_name} is not in a voice channel.")
        return
    await member.move_to(channel)
    await ctx.send(f"Successfully moved {member.display_name} to {channel.name}!")

@movevc.error
async def movevc_error(ctx, error):
    """Handles errors for the movevc command."""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Sorry, you don't have the 'Move Members' permission to do that.")
    else:
        await ctx.send("Usage: `&movevc @User #voice-channel-name`")


# --- Feature 4: Reply on Role Mention ---
@bot.event
async def on_message(message):
    """Processes messages for user mentions and commands."""
    # Ignore messages sent by the bot itself
    if message.author == bot.user:
        return

    # --- User Mention Logic ---
    # Check if any users were mentioned in the message
    if message.mentions:
        for member in message.mentions:
            # Check if the mentioned member's ID matches our target user's ID
            if member.id == USER_MENTION_CONFIG["user_id"]:
                try:
                    await message.reply(USER_MENTION_CONFIG["reply_message"])
                    print(f"Replied to a mention of user ID {USER_MENTION_CONFIG['user_id']}")
                    # Break the loop so it doesn't reply multiple times
                    break 
                except Exception as e:
                    print(f"Could not reply to user mention: {e}")

    # --- Important: Process Commands ---
    # This line allows the bot to still process commands like &movevc
    await bot.process_commands(message)


# =================================================================================================
# RUN THE BOT
# =================================================================================================
keep_alive()  # Starts the web server
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)