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
    "ticket_channel_id": 0, # ❗ PASTE THE CHANNEL ID WHERE THE TICKET MESSAGE WILL BE POSTED
    "active_tickets_category_id": 0, # ❗ PASTE THE CATEGORY ID WHERE NEW TICKETS WILL BE CREATED
    "closed_tickets_category_id": 0, # ❗ PASTE THE CATEGORY ID WHERE CLOSED TICKETS WILL BE MOVED
    "support_role_id": 0, # ❗ PASTE THE ROLE ID THAT CAN ACCESS TICKETS
    "ticket_description": """🎫 **Open a Ticket**
Having an issue or a question?
Click the button below to create a private support ticket.

🔧 TicketTool.xyz - Ticketing without clutter""" # ❗ CUSTOMIZE YOUR TICKET DESCRIPTION
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


# Add persistent views when bot starts
@bot.event
async def on_ready():
    """Prints a message to the console when the bot is online and adds persistent views."""
    print(f'Bot {bot.user} is online and ready! 🚀')
    
    # Add persistent views
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    print("Persistent views added for ticket system!")


# =================================================================================================
# RUN THE BOT
# =================================================================================================
keep_alive()  # Starts the web server
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)