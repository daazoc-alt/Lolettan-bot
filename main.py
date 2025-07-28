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
    "dm_message": """**✨ HEY You are verified ✅
Welcome to ♠️ ʙʟᴀᴄᴋ ᴊᴀᴄᴋ ♠️**
•
**📜 SERVER RULES:** 🔗https://discordapp.com/channels/1398556295438794773/1398939894038003782
•
**🔗 INVITE LINK:** ➡️ https://discord.com/channels/1398556295438794773/1398655859747459102
•
**💬 CHAT ZONE:** 🗨️ https://discord.com/channels/1398556295438794773/1398556296046837810
•
**👋 We're glad to have you! 🃏 Let's deal some cards ♠️ and have fun! 🎉💵**"""
}

# --- CONFIGURATION FOR USER MENTION REPLY ---
USER_MENTION_CONFIG = {
    "user_id": 1244962723872247818, # ❗ MAKE SURE YOUR ACTUAL USER ID IS PASTED HERE
    "reply_message": "👀 You mentioned my DEV — he'll be with you shortly."
}

# --- CONFIGURATION FOR WELCOME MESSAGE ---
WELCOME_CONFIG = {
    "channel_id": 1398556295916818526, # ❗ PASTE YOUR WELCOME CHANNEL ID HERE
    "welcome_description": """**✅ GET VERIFIED: 🔒**
https://discord.com/channels/1398556295438794773/1398649721521967145

**📜 SERVER RULES: **🔗https://discordapp.com/channels/1398556295438794773/1398939894038003782

**🔗 INVITE LINK:**
➡️ https://discord.com/channels/1398556295438794773/1398655859747459102

**💬 CHAT ZONE:**
🗨️ https://discord.com/channels/1398556295438794773/1398556296046837810

**♠️ Let the cards fall where they may — welcome to the game!**""" # ❗ PASTE YOUR WELCOME DESCRIPTION HERE
}

# --- CONFIGURATION FOR TICKET SYSTEM ---
TICKET_CONFIG = {
    "ticket_channel_id": 1398870471310573578, # Channel where the ticket message will be posted
    "active_tickets_category_id": 1398868213604814848, # Category where new tickets will be created
    "closed_tickets_category_id": 1398871882706583612, # Category where closed tickets will be moved
    "support_role_id": 1398867140681138267, # Role that can access tickets
    "ticket_description": """**🎰 ɴᴇᴇᴅ ᴀssɪsᴛᴀɴᴄᴇ?**
ʜɪᴛ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ᴏᴘᴇɴ ᴀ ᴛɪᴄᴋᴇᴛ.
🃏 ғᴏʀ ᴅᴇᴀʟs, sᴜᴘᴘᴏʀᴛ, ᴏʀ ɢᴀᴍᴇ ɪssᴜᴇs — ᴡᴇ ɢᴏᴛ ʏᴏᴜ!""" # Custom ticket description
}

# --- CONFIGURATION FOR MODERATION SYSTEM ---
MODERATION_CONFIG = {
    "moderator_role_id": 1399360589465391187, # Role that can use moderation commands
    "log_channel_id": 1399357783094202388, # Channel where command logs are sent
}

# Voice channel tracking for logs and settings
voice_logs = []
voice_channel_settings = {}
voice_bans = {}  # {channel_id: {user_id: timestamp}}


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
bot = commands.Bot(command_prefix='&', intents=intents, help_command=None)


# =================================================================================================
# MODERATION HELPER FUNCTIONS
# =================================================================================================

import datetime
import asyncio

def has_moderator_role():
    """Decorator to check if user has moderator role."""
    def predicate(ctx):
        moderator_role = ctx.guild.get_role(MODERATION_CONFIG["moderator_role_id"])
        return moderator_role in ctx.author.roles
    return commands.check(predicate)

async def log_command(ctx, command_name, details=""):
    """Log command usage to the configured log channel."""
    log_channel = bot.get_channel(MODERATION_CONFIG["log_channel_id"])
    if log_channel:
        embed = discord.Embed(
            title="🔧 Command Used",
            color=0x00ff00,
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Command", value=f"`{command_name}`", inline=True)
        embed.add_field(name="User", value=ctx.author.mention, inline=True)
        embed.add_field(name="Channel", value=ctx.channel.mention, inline=True)
        if details:
            embed.add_field(name="Details", value=details, inline=False)
        embed.set_footer(text="♠️ BLACK JACK Moderation Logs")

        try:
            await log_channel.send(embed=embed)
        except:
            pass

# =================================================================================================
# BOT EVENTS AND COMMANDS
# =================================================================================================

@bot.event
async def on_ready():
    """Prints a message to the console when the bot is online."""
    print(f'Bot {bot.user} is online and ready! 🚀')

@bot.event
async def on_voice_state_update(member, before, after):
    """Track voice channel joins/leaves for logs."""
    timestamp = datetime.datetime.utcnow()

    if before.channel != after.channel:
        if before.channel is None and after.channel is not None:
            # User joined a voice channel
            log_entry = {
                "action": "joined",
                "user": member,
                "channel": after.channel,
                "timestamp": timestamp
            }
            voice_logs.append(log_entry)

        elif before.channel is not None and after.channel is None:
            # User left a voice channel
            log_entry = {
                "action": "left",
                "user": member,
                "channel": before.channel,
                "timestamp": timestamp
            }
            voice_logs.append(log_entry)

        elif before.channel is not None and after.channel is not None:
            # User moved between channels
            log_entry = {
                "action": "moved",
                "user": member,
                "from_channel": before.channel,
                "to_channel": after.channel,
                "timestamp": timestamp
            }
            voice_logs.append(log_entry)

    # Keep only last 100 log entries
    if len(voice_logs) > 100:
        voice_logs.pop(0)


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


# =================================================================================================
# VOICE CHANNEL MODERATION COMMANDS
# =================================================================================================

@bot.group(name='vc', invoke_without_command=True)
@has_moderator_role()
async def vc(ctx):
    """Voice channel moderation commands."""
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            title="🎙️ Voice Channel Commands",
            description="Available voice channel moderation commands:",
            color=0x0099ff
        )
        embed.add_field(name="&vc mute @user", value="Mute a user in voice channel", inline=False)
        embed.add_field(name="&vc unmute @user", value="Unmute a user in voice channel", inline=False)
        embed.add_field(name="&vc kick @user", value="Disconnect user from voice channel", inline=False)
        embed.add_field(name="&vc lock", value="Lock your current voice channel", inline=False)
        embed.add_field(name="&vc unlock", value="Unlock your current voice channel", inline=False)
        embed.add_field(name="&vc ban @user", value="Temporarily ban user from your VC", inline=False)
        embed.add_field(name="&vc move @user #channel", value="Move user to another voice channel", inline=False)
        embed.set_footer(text="♠️ BLACK JACK Moderation")
        await ctx.send(embed=embed)

@vc.command(name='mute')
@has_moderator_role()
async def vc_mute(ctx, member: discord.Member):
    """Mute a user in voice channel."""
    if not member.voice or not member.voice.channel:
        await ctx.send(f"❌ {member.mention} is not in a voice channel.")
        return

    try:
        await member.edit(mute=True)
        await ctx.send(f"🔇 {member.mention} has been muted in voice channel.")
        await log_command(ctx, "&vc mute", f"Muted {member.mention} in {member.voice.channel.name}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to mute this user.")

@vc.command(name='unmute')
@has_moderator_role()
async def vc_unmute(ctx, member: discord.Member):
    """Unmute a user in voice channel."""
    if not member.voice or not member.voice.channel:
        await ctx.send(f"❌ {member.mention} is not in a voice channel.")
        return

    try:
        await member.edit(mute=False)
        await ctx.send(f"🔊 {member.mention} has been unmuted in voice channel.")
        await log_command(ctx, "&vc unmute", f"Unmuted {member.mention} in {member.voice.channel.name}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to unmute this user.")

@vc.command(name='kick')
@has_moderator_role()
async def vc_kick(ctx, member: discord.Member):
    """Disconnect a user from voice channel."""
    if not member.voice or not member.voice.channel:
        await ctx.send(f"❌ {member.mention} is not in a voice channel.")
        return

    channel_name = member.voice.channel.name
    try:
        await member.move_to(None)
        await ctx.send(f"👢 {member.mention} has been disconnected from voice channel.")
        await log_command(ctx, "&vc kick", f"Kicked {member.mention} from {channel_name}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to disconnect this user.")

@vc.command(name='lock')
@has_moderator_role()
async def vc_lock(ctx):
    """Lock your current voice channel."""
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ You must be in a voice channel to use this command.")
        return

    channel = ctx.author.voice.channel
    try:
        await channel.set_permissions(ctx.guild.default_role, connect=False)
        voice_channel_settings[channel.id] = voice_channel_settings.get(channel.id, {})
        voice_channel_settings[channel.id]['locked'] = True
        await ctx.send(f"🔒 Voice channel **{channel.name}** has been locked.")
        await log_command(ctx, "&vc lock", f"Locked voice channel {channel.name}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to modify this voice channel.")

@vc.command(name='unlock')
@has_moderator_role()
async def vc_unlock(ctx):
    """Unlock your current voice channel."""
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ You must be in a voice channel to use this command.")
        return

    channel = ctx.author.voice.channel
    try:
        await channel.set_permissions(ctx.guild.default_role, connect=None)
        if channel.id in voice_channel_settings:
            voice_channel_settings[channel.id]['locked'] = False
        await ctx.send(f"🔓 Voice channel **{channel.name}** has been unlocked.")
        await log_command(ctx, "&vc unlock", f"Unlocked voice channel {channel.name}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to modify this voice channel.")

@vc.command(name='ban')
@has_moderator_role()
async def vc_ban(ctx, member: discord.Member):
    """Temporarily ban a user from your voice channel."""
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ You must be in a voice channel to use this command.")
        return

    channel = ctx.author.voice.channel
    try:
        # Disconnect user if they're in the channel
        if member.voice and member.voice.channel == channel:
            await member.move_to(None)

        # Set permissions to deny connect
        await channel.set_permissions(member, connect=False)

        # Track the ban (expires in 1 hour)
        if channel.id not in voice_bans:
            voice_bans[channel.id] = {}
        voice_bans[channel.id][member.id] = datetime.datetime.utcnow() + datetime.timedelta(hours=1)

        await ctx.send(f"🚫 {member.mention} has been temporarily banned from **{channel.name}** for 1 hour.")
        await log_command(ctx, "&vc ban", f"Banned {member.mention} from {channel.name}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to ban this user from the voice channel.")

@vc.command(name='move')
@has_moderator_role()
async def vc_move(ctx, member: discord.Member, channel: discord.VoiceChannel):
    """Move a user to another voice channel."""
    if not member.voice or not member.voice.channel:
        await ctx.send(f"❌ {member.mention} is not in a voice channel.")
        return

    old_channel = member.voice.channel.name
    try:
        await member.move_to(channel)
        await ctx.send(f"📤 {member.mention} has been moved to **{channel.name}**.")
        await log_command(ctx, "&vc move", f"Moved {member.mention} from {old_channel} to {channel.name}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to move this user.")

@bot.command(name='voice')
@has_moderator_role()
async def voice(ctx, action=None, value=None):
    """Voice channel management commands."""
    if action == "logs":
        if not voice_logs:
            await ctx.send("📝 No voice channel activity recorded yet.")
            return

        embed = discord.Embed(
            title="🎙️ Voice Channel Logs",
            color=0x0099ff,
            timestamp=datetime.datetime.utcnow()
        )

        # Show last 10 entries
        recent_logs = voice_logs[-10:]
        log_text = ""

        for log in recent_logs:
            time_str = log['timestamp'].strftime("%H:%M:%S")
            if log['action'] == 'joined':
                log_text += f"`{time_str}` ➡️ {log['user'].mention} joined **{log['channel'].name}**\n"
            elif log['action'] == 'left':
                log_text += f"`{time_str}` ⬅️ {log['user'].mention} left **{log['channel'].name}**\n"
            elif log['action'] == 'moved':
                log_text += f"`{time_str}` 🔄 {log['user'].mention} moved from **{log['from_channel'].name}** to **{log['to_channel'].name}**\n"

        embed.description = log_text if log_text else "No recent activity"
        embed.set_footer(text="♠️ BLACK JACK Voice Logs")
        await ctx.send(embed=embed)
        await log_command(ctx, "&voice logs", "Viewed voice channel logs")

    elif action == "settings":
        embed = discord.Embed(
            title="🎙️ Voice Channel Settings",
            description="Voice channel configuration options:",
            color=0x0099ff
        )
        embed.add_field(name="&voice limit <number>", value="Set user limit for your VC", inline=False)
        embed.add_field(name="&vc lock/unlock", value="Lock/unlock your voice channel", inline=False)
        embed.add_field(name="&vc ban @user", value="Temporarily ban user from VC", inline=False)
        embed.set_footer(text="♠️ BLACK JACK Voice Settings")
        await ctx.send(embed=embed)

    elif action == "limit" and value:
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ You must be in a voice channel to use this command.")
            return

        try:
            limit = int(value)
            if limit < 0 or limit > 99:
                await ctx.send("❌ Voice channel limit must be between 0 and 99.")
                return

            channel = ctx.author.voice.channel
            await channel.edit(user_limit=limit)
            await ctx.send(f"👥 Voice channel **{channel.name}** user limit set to {limit}.")
            await log_command(ctx, "&voice limit", f"Set {channel.name} limit to {limit}")
        except ValueError:
            await ctx.send("❌ Please provide a valid number for the limit.")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to modify this voice channel.")
    else:
        await ctx.send("❌ Usage: `&voice logs`, `&voice settings`, or `&voice limit <number>`")

@bot.command(name='nick')
@has_moderator_role()
async def change_nick(ctx, member: discord.Member, *, new_name):
    """Change a user's nickname."""
    old_name = member.display_name
    try:
        await member.edit(nick=new_name)
        await ctx.send(f"✏️ Changed {member.mention}'s nickname from **{old_name}** to **{new_name}**.")
        await log_command(ctx, "&nick", f"Changed {member.mention}'s nickname from {old_name} to {new_name}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to change this user's nickname.")
    except discord.HTTPException:
        await ctx.send("❌ Failed to change nickname. The name might be too long or invalid.")

# Error handlers for moderation commands
@vc.error
async def vc_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("❌ You don't have permission to use moderation commands.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ User not found. Please mention a valid user.")
    elif isinstance(error, commands.ChannelNotFound):
        await ctx.send("❌ Voice channel not found. Please mention a valid voice channel.")

@voice.error
async def voice_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("❌ You don't have permission to use moderation commands.")

@change_nick.error
async def nick_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("❌ You don't have permission to use moderation commands.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ User not found. Please mention a valid user.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Usage: `&nick @user [new_name]`")


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
# TICKET SYSTEM
# =================================================================================================

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='📧 Create ticket', style=discord.ButtonStyle.primary, custom_id='create_ticket')
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Creates a new ticket when the button is clicked."""
        guild = interaction.guild
        user = interaction.user

        # Get the category for active tickets
        active_category = guild.get_channel(TICKET_CONFIG["active_tickets_category_id"])
        if not active_category:
            await interaction.response.send_message("❌ Ticket system is not properly configured.", ephemeral=True)
            return

        # Check if user already has an open ticket
        existing_ticket = discord.utils.find(
            lambda c: c.name == f"ticket-{user.name.lower()}" and c.category_id == TICKET_CONFIG["active_tickets_category_id"],
            guild.channels
        )

        if existing_ticket:
            await interaction.response.send_message(f"❌ You already have an open ticket: {existing_ticket.mention}", ephemeral=True)
            return

        # Create the ticket channel
        support_role = guild.get_role(TICKET_CONFIG["support_role_id"])

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        try:
            ticket_channel = await guild.create_text_channel(
                name=f"ticket-{user.name.lower()}",
                category=active_category,
                overwrites=overwrites
            )

            # Create the close ticket view
            close_view = CloseTicketView()

            embed = discord.Embed(
                title="🎫 Support Ticket Created",
                description=f"Welcome {user.mention}! \n\n📝 **Please describe your issue or question below.**\n\n🔒 This is a private channel only visible to you and our support team.",
                color=0x00ff00
            )
            embed.set_footer(text="♠️ BLACK JACK Support Team")

            await ticket_channel.send(embed=embed, view=close_view)

            # Notify support role if configured
            if support_role:
                await ticket_channel.send(f"🔔 {support_role.mention} - New support ticket created!")

            await interaction.response.send_message(f"✅ Ticket created! Please check {ticket_channel.mention}", ephemeral=True)
            print(f"Created ticket for {user.name}")

        except Exception as e:
            await interaction.response.send_message("❌ Failed to create ticket. Please contact an administrator.", ephemeral=True)
            print(f"Failed to create ticket: {e}")


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='🔒 Close Ticket', style=discord.ButtonStyle.danger, custom_id='close_ticket')
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Closes the ticket and moves it to closed category."""
        guild = interaction.guild
        channel = interaction.channel

        # Check if user has permission to close (ticket creator or support role)
        support_role = guild.get_role(TICKET_CONFIG["support_role_id"])
        can_close = (
            channel.name == f"ticket-{interaction.user.name.lower()}" or
            (support_role and support_role in interaction.user.roles) or
            interaction.user.guild_permissions.manage_channels
        )

        if not can_close:
            await interaction.response.send_message("❌ You don't have permission to close this ticket.", ephemeral=True)
            return

        # Get closed tickets category
        closed_category = guild.get_channel(TICKET_CONFIG["closed_tickets_category_id"])
        if not closed_category:
            await interaction.response.send_message("❌ Closed tickets category not configured.", ephemeral=True)
            return

        try:
            # Update channel permissions to remove user access
            user_name = channel.name.replace("ticket-", "")
            user = discord.utils.find(lambda m: m.name.lower() == user_name, guild.members)

            if user:
                await channel.set_permissions(user, read_messages=False)

            # Move to closed category
            await channel.edit(category=closed_category, name=f"closed-{channel.name}")

            embed = discord.Embed(
                title="🔒 Ticket Closed",
                description=f"This ticket has been closed by {interaction.user.mention}.\n\n📁 Moved to closed tickets category.",
                color=0xff0000
            )
            embed.set_footer(text="♠️ BLACK JACK Support Team")

            # Remove the close button
            await interaction.response.edit_message(embed=embed, view=None)

            print(f"Closed ticket: {channel.name}")

        except Exception as e:
            await interaction.response.send_message("❌ Failed to close ticket.", ephemeral=True)
            print(f"Failed to close ticket: {e}")


# --- Feature 5: Ticket System Commands ---
@bot.command()
@commands.has_permissions(manage_channels=True)
async def setup_tickets(ctx):
    """Sets up the ticket system by sending the ticket creation message."""
    if not TICKET_CONFIG["ticket_channel_id"]:
        await ctx.send("❌ Ticket system is not configured. Please set the channel ID in the configuration.")
        return

    ticket_channel = bot.get_channel(TICKET_CONFIG["ticket_channel_id"])
    if not ticket_channel:
        await ctx.send("❌ Ticket channel not found. Please check the channel ID in the configuration.")
        return

    embed = discord.Embed(
        title="🎫 Support Tickets",
        description=TICKET_CONFIG["ticket_description"],
        color=0x0099ff
    )
    embed.set_footer(text="♠️ BLACK JACK Support System")

    view = TicketView()
    await ticket_channel.send(embed=embed, view=view)
    await ctx.send(f"✅ Ticket system set up in {ticket_channel.mention}")

@setup_tickets.error
async def setup_tickets_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need 'Manage Channels' permission to set up the ticket system.")


# =================================================================================================
# ADDITIONAL MODERATION COMMANDS
# =================================================================================================

@bot.command(name='say')
@has_moderator_role()
async def say_command(ctx, *, message):
    """Bot sends a message and deletes the command."""
    try:
        await ctx.message.delete()
        await ctx.send(message)
        await log_command(ctx, "&say", f"Message: {message[:100]}...")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to delete messages.")

@bot.command(name='embed')
@has_moderator_role()
async def embed_command(ctx, *, message):
    """Bot sends an embedded message and deletes the command."""
    try:
        await ctx.message.delete()
        embed = discord.Embed(description=message, color=0x0099ff)
        embed.set_footer(text="♠️ BLACK JACK")
        await ctx.send(embed=embed)
        await log_command(ctx, "&embed", f"Embedded message: {message[:100]}...")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to delete messages.")

@bot.command(name='announce')
@has_moderator_role()
async def announce_command(ctx, channel: discord.TextChannel, *, message):
    """Sends an announcement message in the mentioned channel."""
    try:
        await ctx.message.delete()
        embed = discord.Embed(
            title="📢 Announcement",
            description=message,
            color=0xff6600
        )
        embed.set_footer(text="♠️ BLACK JACK Announcement")
        await channel.send(embed=embed)
        await log_command(ctx, "&announce", f"Announced in {channel.mention}: {message[:100]}...")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to send messages in that channel or delete this message.")

@bot.command(name='poll')
@has_moderator_role()
async def poll_command(ctx, *, content):
    """Creates a poll with reactions."""
    try:
        await ctx.message.delete()
        parts = content.split(' | ')
        if len(parts) != 3:
            await ctx.send("❌ Usage: `&poll [question] | [option1] | [option2]`", delete_after=5)
            return

        question, option1, option2 = parts
        embed = discord.Embed(
            title="📊 Poll",
            description=f"**{question}**\n\n🇦 {option1}\n🇧 {option2}",
            color=0x00ff00
        )
        embed.set_footer(text="♠️ BLACK JACK Poll System")

        poll_msg = await ctx.send(embed=embed)
        await poll_msg.add_reaction('🇦')
        await poll_msg.add_reaction('🇧')
        await log_command(ctx, "&poll", f"Created poll: {question}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to delete messages or add reactions.")

@bot.command(name='warn')
@has_moderator_role()
async def warn_command(ctx, member: discord.Member, *, reason):
    """Warns a user and logs it."""
    try:
        await ctx.message.delete()
        log_channel = bot.get_channel(MODERATION_CONFIG["log_channel_id"])

        embed = discord.Embed(
            title="⚠️ User Warning",
            color=0xffaa00,
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text="♠️ BLACK JACK Moderation")

        if log_channel:
            await log_channel.send(embed=embed)

        try:
            await member.send(f"⚠️ You have been warned in **{ctx.guild.name}**\n**Reason:** {reason}")
        except:
            pass

        await log_command(ctx, "&warn", f"Warned {member.mention} for: {reason}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to delete messages.")

@bot.command(name='dm')
@has_moderator_role()
async def dm_command(ctx, member: discord.Member, *, message):
    """Sends a DM to a user."""
    try:
        await ctx.message.delete()
        try:
            await member.send(f"📩 **Message from {ctx.guild.name}:**\n{message}")
            await log_command(ctx, "&dm", f"Sent DM to {member.mention}: {message[:100]}...")
        except discord.Forbidden:
            await ctx.send(f"❌ Could not send DM to {member.mention}. They may have DMs disabled.", delete_after=5)
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to delete messages.")

@bot.command(name='clear')
@has_moderator_role()
async def clear_command(ctx, amount: int):
    """Deletes a specified number of messages."""
    if amount <= 0 or amount > 100:
        await ctx.send("❌ Please specify a number between 1 and 100.", delete_after=5)
        return

    try:
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message
        await ctx.send(f"🧹 Deleted {len(deleted) - 1} messages.", delete_after=3)
        await log_command(ctx, "&clear", f"Cleared {len(deleted) - 1} messages")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to delete messages.")

@bot.command(name='mute')
@has_moderator_role()
async def mute_command(ctx, member: discord.Member, duration=None, *, reason="No reason provided"):
    """Mutes a user."""
    try:
        await ctx.message.delete()

        # Parse duration (simple implementation)
        mute_time = None
        if duration:
            try:
                if duration.endswith('m'):
                    mute_time = datetime.timedelta(minutes=int(duration[:-1]))
                elif duration.endswith('h'):
                    mute_time = datetime.timedelta(hours=int(duration[:-1]))
                elif duration.endswith('d'):
                    mute_time = datetime.timedelta(days=int(duration[:-1]))
            except:
                pass

        until = datetime.datetime.utcnow() + mute_time if mute_time else None
        await member.timeout(until, reason=reason)

        duration_text = f" for {duration}" if duration else ""
        await ctx.send(f"🔇 {member.mention} has been muted{duration_text}.", delete_after=5)
        await log_command(ctx, "&mute", f"Muted {member.mention}{duration_text} for: {reason}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to mute this user or delete messages.")

@bot.command(name='kick')
@has_moderator_role()
async def kick_command(ctx, member: discord.Member, *, reason="No reason provided"):
    """Kicks a member from the server."""
    try:
        await ctx.message.delete()
        await member.kick(reason=reason)
        await ctx.send(f"👢 {member.mention} has been kicked from the server.", delete_after=5)
        await log_command(ctx, "&kick", f"Kicked {member.mention} for: {reason}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to kick this user or delete messages.")

@bot.command(name='ban')
@has_moderator_role()
async def ban_command(ctx, member: discord.Member, *, reason="No reason provided"):
    """Bans a user from the server."""
    try:
        await ctx.message.delete()
        await member.ban(reason=reason)
        await ctx.send(f"🔨 {member.mention} has been banned from the server.", delete_after=5)
        await log_command(ctx, "&ban", f"Banned {member.mention} for: {reason}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to ban this user or delete messages.")

@bot.command(name='lock')
@has_moderator_role()
async def lock_command(ctx):
    """Locks the current channel."""
    try:
        await ctx.message.delete()
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send("🔒 This channel has been locked.", delete_after=5)
        await log_command(ctx, "&lock", f"Locked channel {ctx.channel.mention}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to modify this channel or delete messages.")

@bot.command(name='unlock')
@has_moderator_role()
async def unlock_command(ctx):
    """Unlocks the current channel."""
    try:
        await ctx.message.delete()
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
        await ctx.send("🔓 This channel has been unlocked.", delete_after=5)
        await log_command(ctx, "&unlock", f"Unlocked channel {ctx.channel.mention}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to modify this channel or delete messages.")

@bot.command(name='shrug')
@has_moderator_role()
async def shrug_command(ctx, *, message):
    """Bot sends a message with shrug emoji."""
    try:
        await ctx.message.delete()
        await ctx.send(f"{message} ¯\\_(ツ)_/¯")
        await log_command(ctx, "&shrug", f"Shrug message: {message}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to delete messages.")

@bot.command(name='reverse')
@has_moderator_role()
async def reverse_command(ctx, *, message):
    """Bot replies with reversed text."""
    try:
        await ctx.message.delete()
        reversed_text = message[::-1]
        await ctx.send(f"🔄 {reversed_text}")
        await log_command(ctx, "&reverse", f"Reversed: {message}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to delete messages.")

@bot.command(name='spoiler')
@has_moderator_role()
async def spoiler_command(ctx, *, message):
    """Bot sends message wrapped in spoiler formatting."""
    try:
        await ctx.message.delete()
        await ctx.send(f"||{message}||")
        await log_command(ctx, "&spoiler", f"Spoiler message: {message[:50]}...")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to delete messages.")

# Error handlers for new commands
for command_name in ['say', 'embed', 'announce', 'poll', 'warn', 'dm', 'clear', 'mute', 'kick', 'ban', 'lock', 'unlock', 'shrug', 'reverse', 'spoiler']:
    command = bot.get_command(command_name)
    if command:
        @command.error
        async def command_error(ctx, error):
            if isinstance(error, commands.CheckFailure):
                await ctx.send("❌ You don't have permission to use this command.", delete_after=5)
            elif isinstance(error, commands.MissingRequiredArgument):
                await ctx.send(f"❌ Missing required argument. Use `&help` for command usage.", delete_after=5)
            elif isinstance(error, commands.MemberNotFound):
                await ctx.send("❌ User not found. Please mention a valid user.", delete_after=5)
            elif isinstance(error, commands.ChannelNotFound):
                await ctx.send("❌ Channel not found. Please mention a valid channel.", delete_after=5)

# =================================================================================================
# INTERACTIVE HELP PANEL SYSTEM
# =================================================================================================

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label='🎙️ Voice Commands', style=discord.ButtonStyle.primary, custom_id='help_voice')
    async def help_voice(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎙️ Voice Channel Moderation Commands",
            description="**Professional voice channel management tools**",
            color=0x0099ff
        )

        embed.add_field(
            name="**Basic Voice Control**",
            value="`&vc mute @user` - Mute user in voice channel\n"
                  "`&vc unmute @user` - Unmute user in voice channel\n"
                  "`&vc kick @user` - Disconnect user from VC\n"
                  "`&vc move @user #channel` - Move user to another VC",
            inline=False
        )

        embed.add_field(
            name="**Channel Management**",
            value="`&vc lock` - Lock your current voice channel\n"
                  "`&vc unlock` - Unlock your current voice channel\n"
                  "`&vc ban @user` - Temporarily ban user from VC\n"
                  "`&voice limit <number>` - Set VC user limit (0-99)",
            inline=False
        )

        embed.add_field(
            name="**Monitoring & Settings**",
            value="`&voice logs` - Show recent VC join/leave activity\n"
                  "`&voice settings` - Configure voice channel options",
            inline=False
        )

        embed.set_footer(text="🔒 Requires Low-level or Main Moderator Role | ♠️ BLACK JACK Moderation")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='⚙️ General Commands', style=discord.ButtonStyle.secondary, custom_id='help_general')
    async def help_general(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="⚙️ General Moderation Commands",
            description="**Complete moderation toolkit for server management**",
            color=0xff9900
        )

        embed.add_field(
            name="**Message Commands**",
            value="`&say [message]` - Bot sends message, deletes command\n"
                  "`&embed [message]` - Send embedded message\n"
                  "`&announce #channel [message]` - Send announcement\n"
                  "`&poll [question] | [option1] | [option2]` - Create poll",
            inline=False
        )

        embed.add_field(
            name="**User Management**",
            value="`&warn @user [reason]` - Warn user with logging\n"
                  "`&dm @user [message]` - Send DM to user\n"
                  "`&nick @user [new_name]` - Change user nickname\n"
                  "`&mute @user [duration] [reason]` - Mute user",
            inline=False
        )

        embed.add_field(
            name="**Moderation Actions**",
            value="`&kick @user [reason]` - Kick user from server\n"
                  "`&ban @user [reason]` - Ban user from server\n"
                  "`&clear [number]` - Delete messages (1-100)\n"
                  "`&lock` / `&unlock` - Lock/unlock channel",
            inline=False
        )

        embed.add_field(
            name="**Fun Commands**",
            value="`&shrug [message]` - Add shrug emoji to message\n"
                  "`&reverse [message]` - Send reversed text\n"
                  "`&spoiler [message]` - Send spoiler-wrapped text",
            inline=False
        )

        embed.set_footer(text="🔒 Requires Main Moderator Role | ♠️ BLACK JACK Moderation")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='🎫 Ticket System', style=discord.ButtonStyle.success, custom_id='help_tickets')
    async def help_tickets(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎫 Ticket System Commands",
            description="**Professional support ticket management**",
            color=0x00ff00
        )

        embed.add_field(
            name="**Ticket Management**",
            value="`&setup_tickets` - Initialize ticket system in configured channel\n"
                  "**Interactive Buttons:**\n"
                  "• 📧 Create ticket - Opens new support ticket\n"
                  "• 🔒 Close ticket - Closes and archives ticket",
            inline=False
        )

        embed.add_field(
            name="**Features**",
            value="• Private ticket channels\n"
                  "• Auto-role permissions\n"
                  "• Ticket archiving system\n"
                  "• Duplicate prevention\n"
                  "• Professional embeds",
            inline=False
        )

        embed.add_field(
            name="**Automated Systems**",
            value="• **Reaction Roles** - Auto-role assignment\n"
                  "• **Welcome Messages** - New member greetings\n"
                  "• **User Mention Alerts** - Dev notification system\n"
                  "• **Voice Activity Logging** - Join/leave tracking",
            inline=False
        )

        embed.set_footer(text="🔧 Setup required in configuration | ♠️ BLACK JACK Support")
        await interaction.response.edit_message(embed=embed, view=self)

# =================================================================================================
# OWNER COMMAND
# =================================================================================================

@bot.command(name='owner')
async def owner_command(ctx):
    """Display detailed information about the bot owner."""
    embed = discord.Embed(
        title="👑 Bot Owner Information",
        description="**Meet the creator behind ♠️ BLACK JACK Bot**",
        color=0xffd700
    )

    embed.add_field(
        name="🎯 Owner Details",
        value="**Name:** ᴅᴀᴀᴢᴏ | ʀɪᴏ\n**User ID:** `1244962723872247818`\n**Status:** 🟢 Active Developer",
        inline=True
    )

    embed.add_field(
        name="🚀 About the Developer",
        value="• **🎮 Gaming Enthusiast** - Passionate about Discord communities\n• **⚡ Bot Developer** - Creating premium Discord solutions\n• **🃏 Casino Theme Expert** - Specializing in gaming servers\n• **24/7 Support** - Dedicated to bot maintenance",
        inline=False
    )

    embed.add_field(
        name="🛠️ Bot Features Created",
        value="• **🎫 Advanced Ticket System** - Professional support management\n• **🎙️ Voice Moderation** - Complete VC control\n• **⚙️ Moderation Suite** - 15+ admin commands\n• **🤖 Automation** - Reaction roles, welcome messages",
        inline=False
    )

    embed.add_field(
        name="📞 Get in Touch",
        value="• **Direct Contact:** <@1244962723872247818>\n• **Server Support:** Use ticket system\n• **Development Requests:** Contact owner directly",
        inline=False
    )

    embed.set_footer(text="♠️ BLACK JACK Bot - Crafted with ❤️ by ᴅᴀᴀᴢᴏ | ʀɪᴏ")
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1234567890123456789.png")  # You can replace with actual owner avatar

    await ctx.send(embed=embed)

# =================================================================================================
# HELP COMMAND
# =================================================================================================

@bot.command(name='help')
async def help_command(ctx):
    """Interactive help panel with buttons for different command categories."""
    embed = discord.Embed(
        title="♠️ BLACK JACK BOT - Command Help Panel",
        description="**Premium Discord Bot for Server Management & Moderation**\n\n🎮 **Select a category below to view detailed commands:**",
        color=0x000000
    )

    embed.add_field(
        name="📊 Bot Information",
        value="• **Prefix:** `&`\n• **Version:** 3.0\n• **Features:** Voice, Tickets, Moderation\n• **Uptime:** 24/7",
        inline=True
    )

    embed.add_field(
        name="👑 Bot Owner",
        value="• **Owner:** ᴅᴀᴀᴢᴏ | ʀɪᴏ\n• **Developer:** Professional Discord Bot Creator\n• **Contact:** <@1244962723872247818>\n• **Status:** 🟢 Active",
        inline=True
    )

    embed.add_field(
        name="🔒 Access Control",
        value="• **Voice & Tickets:** Low-level Moderator Role\n• **Advanced Commands:** Main Moderator Role\n• **Help:** Available to everyone",
        inline=False
    )

    embed.set_footer(text="♠️ Click the buttons below to explore different command categories")
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)

    view = HelpView()
    await ctx.send(embed=embed, view=view)


# Add persistent views when bot starts
@bot.event
async def on_ready():
    """Prints a message to the console when the bot is online and adds persistent views."""
    print(f'Bot {bot.user} is online and ready! 🚀')

    # Add persistent views
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    bot.add_view(HelpView())
    print("Persistent views added for ticket system and help panel!")


# =================================================================================================
# RUN THE BOT
# =================================================================================================
keep_alive()  # Starts the web server
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)