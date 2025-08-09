
import discord
from discord.ext import commands
import os
from keep_alive import keep_alive
import json
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
from datetime import datetime

# =================================================================================================
# ❗ YOUR CONFIGURATION SECTION - FILL THIS OUT!
# =================================================================================================

# --- CONFIGURATION FOR MODERATION SYSTEM ---
MODERATION_CONFIG = {
    "moderator_role_id": 1399360589465391187, # Role that can use casino commands
    "log_channel_id": 1399357783094202388, # Channel where command logs are sent
}

# --- CONFIGURATION FOR MENTION RESPONSES ---
MENTION_CONFIG = {
    "target_member_ids": [
        1149592349631057961,  # BlackJack Hero target user
        # Add more member IDs as needed
    ]
}

# =================================================================================================
# BOT SETUP
# =================================================================================================

# Define intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

# Create bot instance
bot = commands.Bot(command_prefix='&', intents=intents, help_command=None)

# =================================================================================================
# HELPER FUNCTIONS
# =================================================================================================

def has_moderator_role():
    """Decorator to check if user has moderator role."""
    def predicate(ctx):
        moderator_role = ctx.guild.get_role(MODERATION_CONFIG["moderator_role_id"])
        return moderator_role in ctx.author.roles
    return commands.check(predicate)

async def log_command(ctx, command_name, details=""):
    """Log command usage to the configured log channel."""
    try:
        log_channel = bot.get_channel(MODERATION_CONFIG["log_channel_id"])
        if log_channel:
            embed = discord.Embed(
                title="🔧 Command Used",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Command", value=f"`{command_name}`", inline=True)
            embed.add_field(name="User", value=ctx.author.mention, inline=True)
            embed.add_field(name="Channel", value=ctx.channel.mention, inline=True)
            if details:
                embed.add_field(name="Details", value=details, inline=False)
            embed.set_footer(text="♠️ ʟᴏʟᴇᴛᴛᴀɴ Logs")

            await log_channel.send(embed=embed)
            print(f"✅ Logged command: {command_name} by {ctx.author}")
        else:
            print(f"❌ Log channel not found: {MODERATION_CONFIG['log_channel_id']}")
    except Exception as e:
        print(f"❌ Error logging command {command_name}: {e}")

# =================================================================================================
# BOT EVENTS
# =================================================================================================

@bot.event
async def on_ready():
    """Prints a message to the console when the bot is online and adds persistent views."""
    print(f'ʟᴏʟᴇᴛᴛᴀɴ {bot.user} is online and ready! 🚀')

    # Add persistent views
    bot.add_view(CasinoView())
    bot.add_view(GameView(0))  # Default instance
    print("Persistent views added for casino system!")

@bot.event
async def on_message(message):
    """Handle messages and respond to mentions."""
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Check if the bot is mentioned
    if bot.user in message.mentions:
        embed = discord.Embed(
            title="👋 Hey there!",
            description="**ʟᴏʟᴇᴛᴛᴀɴ BlackJack Casino Bot**\n\nI'm here to help you track your BlackJack sessions!",
            color=0xffd700
        )
        embed.add_field(
            name="🎰 Quick Start",
            value="Use `&casino` to open the casino interface and start tracking your games!",
            inline=False
        )
        embed.add_field(
            name="📊 Features",
            value="• Session tracking with statistics\n• Win/loss analysis with charts\n• Side bets support\n• Split & double down tracking",
            inline=False
        )
        embed.add_field(
            name="❓ Need Help?",
            value="Use `&help` for a complete list of commands!",
            inline=False
        )
        embed.set_footer(text="♠️ Professional BlackJack Statistics Tracker")
        
        await message.channel.send(embed=embed)

    # Check if any specific target members are mentioned (excluding the bot)
    target_mentions = [mention for mention in message.mentions if mention != bot.user and mention.id in MENTION_CONFIG["target_member_ids"]]
    if target_mentions:
        # Custom response for BlackJack hero
        embed = discord.Embed(
            description="ʜᴇʏʏ..👋🏼 ᴛʜᴀᴛ's ᴏᴜʀ ʙʟᴀᴄᴋᴊᴀᴄᴋ ʜᴇʀᴏ♠️, ʜᴇ ᴡɪʟʟ ʀᴇsᴘᴏɴᴅ sᴏᴏɴ..",
            color=0x000000
        )
        
        await message.channel.send(embed=embed)

    # Process commands
    await bot.process_commands(message)

# =================================================================================================
# CASINO SYSTEM - BlackJack Statistics Tracker
# =================================================================================================

# Casino data storage (in-memory, persists during bot runtime)
casino_data = {
    "balance": 0,
    "games": [],
    "session_active": False,
    "session_start": None,
    "session_games": []
}

def get_session_duration():
    """Calculates the current session duration in minutes."""
    if casino_data["session_start"]:
        duration = datetime.now() - casino_data["session_start"]
        minutes = int(duration.total_seconds() / 60)
        return f"{minutes} minutes"
    return "0 minutes"

class CasinoView(discord.ui.View):
    def __init__(self):
        # Set timeout to None to make the view truly persistent for unlimited session duration
        super().__init__(timeout=None)

    @discord.ui.button(label='💰 Start Session', style=discord.ButtonStyle.green, custom_id='start_session')
    async def start_session(self, interaction: discord.Interaction, button: discord.ui.Button):
        if casino_data["session_active"]:
            await interaction.response.send_message("❌ A session is already active! End the current session first.", ephemeral=True)
            return
        modal = BalanceModal(action="start")
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='🎲 Play', style=discord.ButtonStyle.primary, custom_id='play_game', disabled=True)
    async def play_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not casino_data["session_active"]:
            await interaction.response.send_message("❌ No active session! Start a session first.", ephemeral=True)
            return
        modal = BetAmountModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='⏸️ Skip', style=discord.ButtonStyle.secondary, custom_id='skip_game', disabled=True)
    async def skip_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not casino_data["session_active"]:
            await interaction.response.send_message("❌ No active session! Start a session first.", ephemeral=True)
            return
        view = CasinoView()
        view.play_game.disabled = False
        view.skip_game.disabled = False
        view.end_session.disabled = False
        view.cash_out.disabled = False
        embed = discord.Embed(
            title="🎰 BlackJack Casino - Session Active",
            description="**🎲 Ready to play another round!**\n\n**Options:**\n🎲 **Play**\n⏸️ **Skip**\n🛑 **End Session**",
            color=0x00ff00
        )
        embed.add_field(name="💰 Current Balance", value=f"₹{casino_data['balance']:,}", inline=True)
        embed.add_field(name="🎮 Session Games", value=f"{len(casino_data['session_games'])}", inline=True)
        embed.add_field(name="⏱️ Session Duration", value=f"{get_session_duration()} minutes", inline=True)
        embed.set_footer(text="♠️ BlackJack Casino | Session in Progress")
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label='🛑 End Session', style=discord.ButtonStyle.danger, custom_id='end_session', disabled=True)
    async def end_session(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not casino_data["session_active"]:
            await interaction.response.send_message("❌ No active session to end!", ephemeral=True)
            return

        # Defer the interaction immediately to prevent timeout during chart generation
        await interaction.response.defer(ephemeral=False)

        try:
            await self.generate_session_report(interaction)
        except Exception as e:
            print(f"Error generating session report: {e}")
            await interaction.followup.send("❌ An error occurred while generating the session report. Please try again.", ephemeral=True)

    @discord.ui.button(label='💵 Cash Out', style=discord.ButtonStyle.success, custom_id='cash_out', disabled=True)
    async def cash_out(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not casino_data["session_active"]:
            await interaction.response.send_message("❌ No active session to cash out from!", ephemeral=True)
            return
        modal = CashOutModal()
        await interaction.response.send_modal(modal)

    async def generate_session_report(self, interaction: discord.Interaction):
        session_games = casino_data["session_games"]
        if not session_games:
            await interaction.followup.send("❌ No games played in this session!", ephemeral=True)
            return

        # Calculate comprehensive statistics
        total_games = len(session_games)
        wins = sum(1 for game in session_games if game["outcome"] == "win")
        losses = sum(1 for game in session_games if game["outcome"] == "lose")
        ties = sum(1 for game in session_games if game["outcome"] == "tie")
        blackjacks = sum(1 for game in session_games if game["outcome"] == "blackjack")
        cashouts = sum(1 for game in session_games if game["outcome"] == "cashout")
        splits = sum(1 for game in session_games if game.get("is_split", False))
        doubles = sum(1 for game in session_games if game.get("is_double", False))

        win_rate = (wins / total_games) * 100 if total_games > 0 else 0

        # Calculate proper betting amounts including splits and doubles
        total_bet = 0
        total_won = 0
        total_lost = 0
        total_cashout_refunds = 0
        total_cashout_losses = 0

        for game in session_games:
            if game["outcome"] == "cashout":
                # Cash out: count refund and loss separately
                total_cashout_refunds += game.get("refund_amount", 0)
                total_cashout_losses += game.get("lost_amount", 0)
                total_bet += game["amount"]
            elif game.get("is_double", False):
                # Double down: bet amount is already doubled
                total_bet += game["amount"]
                if game["outcome"] in ["win", "blackjack"]:
                    if game["outcome"] == "blackjack":
                        total_won += game["amount"]  # 1:1 payout
                    else:
                        total_won += game["amount"]  # 1:1 payout
                elif game["outcome"] == "lose":
                    total_lost += game["amount"]
            elif game.get("is_split", False):
                # Split: each hand is tracked separately
                total_bet += game["amount"]
                if game["outcome"] in ["win", "blackjack"]:
                    if game["outcome"] == "blackjack":
                        total_won += int(game["amount"] * 1.5)  # 3:2 for blackjack
                    else:
                        total_won += game["amount"]  # 1:1 for win
                elif game["outcome"] == "lose":
                    total_lost += game["amount"]
            else:
                # Regular hands
                total_bet += game["amount"]
                if game["outcome"] in ["win", "blackjack"]:
                    if game["outcome"] == "blackjack":
                        total_won += int(game["amount"] * 1.5)  # 3:2 payout
                    else:
                        total_won += game["amount"]  # 1:1 payout
                elif game["outcome"] == "lose":
                    total_lost += game["amount"]

        total_side_bet_winnings = sum(game.get("side_bet_winnings", 0) for game in session_games)
        net_profit = total_won - total_lost + total_side_bet_winnings + total_cashout_refunds - total_cashout_losses

        # Calculate additional statistics
        avg_bet = total_bet / total_games if total_games > 0 else 0
        biggest_win = max([g["amount"] for g in session_games if g["outcome"] == "win"], default=0)
        biggest_loss = max([g["amount"] for g in session_games if g["outcome"] == "lose"], default=0)

        # Calculate win/loss streaks
        max_win_streak = 0
        max_loss_streak = 0
        temp_win_streak = 0
        temp_loss_streak = 0

        for game in session_games:
            if game["outcome"] == "win":
                temp_win_streak += 1
                temp_loss_streak = 0
                max_win_streak = max(max_win_streak, temp_win_streak)
            elif game["outcome"] == "lose":
                temp_loss_streak += 1
                temp_win_streak = 0
                max_loss_streak = max(max_loss_streak, temp_loss_streak)

        # Generate chart with error handling
        chart_file = None
        try:
            chart_file = self.create_game_chart(session_games)
        except Exception as e:
            print(f"Error creating chart: {e}")

        # Create detailed embed report
        embed = discord.Embed(
            title="📊 BlackJack Session Report - Complete Analysis",
            description="**🎰 Comprehensive session statistics and performance analysis**",
            color=0xffd700
        )

        # Session Overview
        embed.add_field(
            name="⏱️ Session Overview",
            value=f"**Duration:** {get_session_duration()}\n**Games Played:** {total_games}\n**Starting Balance:** ₹{casino_data.get('starting_balance', 'Unknown'):,}\n**Final Balance:** ₹{casino_data['balance']:,}",
            inline=True
        )

        # Performance Statistics
        embed.add_field(
            name="🎯 Performance Stats",
            value=f"**Wins:** {wins} 🟢\n**Losses:** {losses} 🔴\n**Ties:** {ties} 🟡\n**Blackjacks:** {blackjacks} 🂡\n**Win Rate:** {win_rate:.1f}%",
            inline=True
        )

        # Financial Summary
        embed.add_field(
            name="💰 Financial Summary",
            value=f"**Total Bet:** ₹{total_bet:,}\n**Total Won:** ₹{total_won:,}\n**Total Lost:** ₹{total_lost:,}\n**Net Profit:** ₹{net_profit:+,}",
            inline=True
        )

        # Betting Statistics
        embed.add_field(
            name="📈 Betting Analysis",
            value=f"**Biggest Win:** ₹{biggest_win:,}\n**Biggest Loss:** ₹{biggest_loss:,}\n**Profit Margin:** {((net_profit/total_bet)*100) if total_bet > 0 else 0:.1f}%\n**ROI:** {((net_profit/total_bet)*100) if total_bet > 0 else 0:.1f}%",
            inline=True
        )

        # Advanced Features
        embed.add_field(
            name="🎲 Advanced Features",
            value=f"**Splits:** {splits} hands\n**Double Downs:** {doubles} hands\n**Cash Outs:** {cashouts} times\n**Side Bet Wins:** ₹{total_side_bet_winnings:,}",
            inline=True
        )

        # Streak Analysis
        embed.add_field(
            name="🔥 Streak Analysis",
            value=f"**Max Win Streak:** {max_win_streak} games\n**Max Loss Streak:** {max_loss_streak} games\n**Current Form:** {'🟢 Winning' if session_games[-1]['outcome'] in ['win', 'blackjack'] else ('🔴 Losing' if session_games[-1]['outcome'] == 'lose' else '🟡 Push') if session_games else 'N/A'}",
            inline=True
        )

        # Performance Analysis
        if win_rate >= 70:
            analysis = "🔥 **EXCEPTIONAL SESSION!** Outstanding performance! You're dominating the tables!"
        elif win_rate >= 60:
            analysis = "✨ **EXCELLENT SESSION!** Great job! You're playing like a pro!"
        elif win_rate >= 50:
            analysis = "📈 **GOOD SESSION!** Solid performance! You're beating the house!"
        elif win_rate >= 40:
            analysis = "⚖️ **DECENT SESSION!** Close to break-even with room for improvement!"
        else:
            analysis = "💪 **TOUGH SESSION!** Every player faces challenges - learn and improve!"

        embed.add_field(name="📊 Performance Analysis", value=analysis, inline=False)

        # Add timestamp
        embed.add_field(
            name="🕐 Session Completed",
            value=f"<t:{int(datetime.now().timestamp())}:F>",
            inline=False
        )

        embed.set_footer(text="♠️ BlackJack Casino | Professional Statistics Tracker | Session Complete")

        # Reset session data
        casino_data["session_active"] = False
        casino_data["session_start"] = None
        casino_data["session_games"] = []

        # Send the report with or without chart
        try:
            if chart_file:
                await interaction.edit_original_response(embed=embed, view=CasinoView(), attachments=[chart_file])
            else:
                await interaction.edit_original_response(embed=embed, view=CasinoView())
        except Exception as e:
            print(f"Error sending session report: {e}")
            if chart_file:
                await interaction.followup.send(embed=embed, view=CasinoView(), file=chart_file)
            else:
                await interaction.followup.send(embed=embed, view=CasinoView())

    def create_game_chart(self, games):
        try:
            plt.style.use('dark_background')
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
            fig.patch.set_facecolor('#2f3136')

            # Prepare data
            game_numbers = list(range(1, len(games) + 1))
            outcomes = []
            amounts = []
            running_profit = []
            colors = []
            game_changes = []  # Track profit/loss change for each game
            total_balances = []  # Track total balance after each game

            cumulative_profit = 0
            starting_balance = casino_data.get('starting_balance', 0)
            
            for i, g in enumerate(games):
                game_change = 0  # Profit/loss for this specific game
                
                if g["outcome"] == "win":
                    outcomes.append(1)
                    game_change = g["amount"]  # Won the bet amount
                    cumulative_profit += game_change
                    colors.append('#00ff41')
                elif g["outcome"] == "lose":
                    outcomes.append(-1)
                    game_change = -g["amount"]  # Lost the bet amount
                    cumulative_profit += game_change
                    colors.append('#ff4757')
                elif g["outcome"] == "blackjack":
                    outcomes.append(1.5)
                    game_change = int(g["amount"] * 1.5)  # Blackjack 3:2 payout
                    cumulative_profit += game_change
                    colors.append('#ffd700')
                elif g["outcome"] == "cashout":
                    outcomes.append(0.5)
                    refund = g.get("refund_amount", g["amount"])
                    lost = g.get("lost_amount", 0)
                    game_change = refund - lost
                    cumulative_profit += game_change
                    colors.append('#00aaff')
                else:  # tie
                    outcomes.append(0)
                    game_change = 0  # No money change on tie
                    colors.append('#ffaa00')

                # Add side bet winnings to the game change
                side_bet_winnings = g.get("side_bet_winnings", 0)
                game_change += side_bet_winnings
                
                amounts.append(g["amount"])
                running_profit.append(cumulative_profit + side_bet_winnings)
                game_changes.append(game_change)
                total_balances.append(starting_balance + cumulative_profit + side_bet_winnings)

            # Top chart - Bet amounts and outcomes
            ax1.set_facecolor('#36393f')
            bars = ax1.bar(game_numbers, amounts, color=colors, alpha=0.7, edgecolor='white', linewidth=0.5)
            
            # Add profit/loss labels on bars
            for i, (bar, change) in enumerate(zip(bars, game_changes)):
                height = bar.get_height()
                label_text = f"₹{change:+,}" if change != 0 else "₹0"
                ax1.text(bar.get_x() + bar.get_width()/2., height + max(amounts)*0.02,
                        label_text, ha='center', va='bottom', color='white', fontweight='bold', fontsize=9)
            
            ax1.set_xlabel('Game Number', color='white', fontweight='bold')
            ax1.set_ylabel('Bet Amount (₹)', color='white', fontweight='bold')
            ax1.set_title('🎰 BlackJack Session - Individual Game Results', color='#ffd700', fontsize=14, fontweight='bold', pad=15)
            ax1.grid(True, axis='y', alpha=0.3, linestyle=':')

            # Bottom chart - Running profit trend with balance annotations
            ax2.set_facecolor('#36393f')
            line = ax2.plot(game_numbers, running_profit, color='#ffd700', linewidth=3, marker='o', markersize=10, label='Net Profit')
            ax2.axhline(0, color='white', linestyle='--', linewidth=2, alpha=0.7)
            ax2.fill_between(game_numbers, running_profit, 0, where=[p >= 0 for p in running_profit],
                           color='#00ff41', alpha=0.3, interpolate=True, label='Profit Zone')
            ax2.fill_between(game_numbers, running_profit, 0, where=[p < 0 for p in running_profit],
                           color='#ff4757', alpha=0.3, interpolate=True, label='Loss Zone')

            # Add annotations showing profit/loss change and total balance at each point
            for i, (x, y, change, balance) in enumerate(zip(game_numbers, running_profit, game_changes, total_balances)):
                # Show profit/loss change and total balance
                change_text = f"₹{change:+,}" if change != 0 else "₹0"
                balance_text = f"(₹{balance:,})"
                annotation_text = f"{change_text}\n{balance_text}"
                
                # Position annotation above or below point based on space
                y_offset = 15 if i % 2 == 0 else -25
                ax2.annotate(annotation_text, (x, y), 
                           xytext=(0, y_offset), textcoords='offset points',
                           ha='center', va='center' if y_offset > 0 else 'top',
                           fontsize=8, fontweight='bold', color='white',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7, edgecolor='#ffd700'))

            ax2.set_xlabel('Game Number', color='white', fontweight='bold')
            ax2.set_ylabel('Session Net Profit (₹)', color='white', fontweight='bold')
            ax2.set_title('📈 Cumulative Profit/Loss Trend', color='#ffd700', fontsize=14, fontweight='bold', pad=15)
            ax2.grid(True, alpha=0.3, linestyle=':')
            ax2.legend(loc='upper left')

            # Add statistics text box
            total_games = len(games)
            wins = sum(1 for g in games if g["outcome"] == "win")
            losses = sum(1 for g in games if g["outcome"] == "lose")
            ties = sum(1 for g in games if g["outcome"] == "tie")
            blackjacks = sum(1 for g in games if g["outcome"] == "blackjack")
            win_rate = ((wins + blackjacks) / total_games) * 100 if total_games > 0 else 0
            final_profit = running_profit[-1] if running_profit else 0

            stats_text = f'📊 Session Stats:\nGames: {total_games} | W: {wins} | L: {losses} | T: {ties} | BJ: {blackjacks}\nWin Rate: {win_rate:.1f}% | Final P&L: ₹{final_profit:+,}'
            ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes, fontsize=10,
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='#36393f', alpha=0.8),
                    color='white')

            plt.tight_layout()

            # Save to buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', facecolor=fig.get_facecolor(), dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plt.close(fig)

            return discord.File(buffer, filename='blackjack_session_chart.png')

        except Exception as e:
            print(f"Error creating chart: {e}")
            plt.close('all')
            raise e

class GameView(discord.ui.View):
    def __init__(self, bet_amount, side_bets=None, is_split=False, is_double=False):
        # Set timeout to None for unlimited session duration
        super().__init__(timeout=None)
        self.bet_amount = bet_amount
        self.side_bets = side_bets or {}
        self.is_split = is_split
        self.is_double = is_double

        if is_split:
            self.split_hands_completed = getattr(casino_data, 'split_hands_completed', 0)

    @discord.ui.button(label='🟢 WIN', style=discord.ButtonStyle.success, custom_id='game_win')
    async def game_win(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.record_game(interaction, "win", self.bet_amount)

    @discord.ui.button(label='🔴 LOSE', style=discord.ButtonStyle.danger, custom_id='game_lose')
    async def game_lose(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.record_game(interaction, "lose", self.bet_amount)

    @discord.ui.button(label='🟡 TIE', style=discord.ButtonStyle.secondary, custom_id='game_tie')
    async def game_tie(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.record_game(interaction, "tie", self.bet_amount)

    @discord.ui.button(label='🂡 BLACKJACK', style=discord.ButtonStyle.primary, custom_id='game_blackjack')
    async def game_blackjack(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.record_game(interaction, "blackjack", self.bet_amount)

    @discord.ui.button(label='💵 CASH OUT', style=discord.ButtonStyle.success, custom_id='game_cashout')
    async def game_cashout(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = GameCashOutModal(self.bet_amount)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='🧩 SPLIT', style=discord.ButtonStyle.secondary, custom_id='game_split')
    async def game_split(self, interaction: discord.Interaction, button: discord.ui.Button):
        if casino_data["balance"] < self.bet_amount:
            await interaction.response.send_message("❌ Insufficient balance to split!", ephemeral=True)
            return

        # Split: deduct additional bet amount for second hand
        casino_data["balance"] -= self.bet_amount
        casino_data['split_hands_completed'] = 0

        embed = discord.Embed(
            title="🧩 Split Hand - First Hand",
            description=f"**Playing first hand of split**\n\n**Each Hand Bet:** ₹{self.bet_amount:,}\n**Total Bet:** ₹{self.bet_amount * 2:,}",
            color=0x00aaff
        )
        embed.add_field(name="💰 Current Balance", value=f"₹{casino_data['balance']:,}", inline=True)
        embed.set_footer(text="♠️ BlackJack Casino | Split Hand 1/2")

        view = GameView(self.bet_amount, self.side_bets, is_split=True)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label='🔁DOUBLE', style=discord.ButtonStyle.secondary, custom_id='game_double')
    async def game_double(self, interaction: discord.Interaction, button: discord.ui.Button):
        if casino_data["balance"] < self.bet_amount:
            await interaction.response.send_message("❌ Insufficient balance to double down!", ephemeral=True)
            return

        # Double down: deduct additional bet amount
        casino_data["balance"] -= self.bet_amount
        doubled_amount = self.bet_amount * 2

        embed = discord.Embed(
            title="🔁 Double Down",
            description=f"**Bet doubled! Choose outcome:**\n\n**Original Bet:** ₹{self.bet_amount:,}\n**Total Bet:** ₹{doubled_amount:,}",
            color=0xff9900
        )
        embed.add_field(name="💰 Current Balance", value=f"₹{casino_data['balance']:,}", inline=True)
        embed.set_footer(text="♠️ BlackJack Casino | Double Down")

        view = GameView(doubled_amount, self.side_bets, is_double=True)
        await interaction.response.edit_message(embed=embed, view=view)

    async def record_game(self, interaction, outcome, amount):
        # Process side bets first
        side_bet_winnings = 0
        side_bet_text = ""

        if self.side_bets:
            for bet_type, bet_amount in self.side_bets.items():
                if bet_amount > 0:
                    # For demo purposes, 25% chance side bet wins
                    import random
                    if random.choice([True, False, False, False]):
                        multiplier = {"Perfect Pair": 5, "21 + 3": 10, "Dealer Bust": 30}.get(bet_type, 5)
                        side_bet_win = bet_amount * multiplier
                        casino_data["balance"] += side_bet_win
                        side_bet_winnings += side_bet_win
                        side_bet_text += f"🎉 {bet_type} WON: +₹{side_bet_win:,}\n"
                    else:
                        casino_data["balance"] -= bet_amount
                        side_bet_text += f"❌ {bet_type} LOST: -₹{bet_amount:,}\n"

        # Record the main game
        game_data = {
            "outcome": outcome, 
            "amount": amount, 
            "timestamp": datetime.now().isoformat(),
            "side_bets": self.side_bets,
            "side_bet_winnings": side_bet_winnings,
            "is_split": self.is_split,
            "is_double": self.is_double
        }
        casino_data["session_games"].append(game_data)
        casino_data["games"].append(game_data)

        # Update balance based on outcome
        if outcome == "win":
            casino_data["balance"] += amount * 2
            balance_change = f"+₹{amount * 2:,}"
            color = 0x00ff00
            outcome_text = "🟢 WIN"
        elif outcome == "lose":
            balance_change = f"-₹{amount:,}"
            color = 0xff0000
            outcome_text = "🔴 LOSE"
        elif outcome == "tie":
            casino_data["balance"] += amount
            balance_change = "₹0 (Push)"
            color = 0xffaa00
            outcome_text = "🟡 TIE"
        elif outcome == "blackjack":
            payout = int(amount * 2.5)
            casino_data["balance"] += payout
            balance_change = f"+₹{payout:,}"
            color = 0x00ff00
            outcome_text = "🂡 BLACKJACK"

        # Handle split hands
        if self.is_split:
            casino_data['split_hands_completed'] += 1
            if casino_data['split_hands_completed'] < 2:
                embed = discord.Embed(
                    title="🧩 Split Hand - Second Hand",
                    description=f"**{outcome_text}** (Hand 1)\n\n**Playing second hand of split**\n**Hand Bet:** ₹{self.bet_amount:,}",
                    color=0x00aaff
                )
                embed.add_field(name="💰 Current Balance", value=f"₹{casino_data['balance']:,}", inline=True)
                embed.set_footer(text="♠️ BlackJack Casino | Split Hand 2/2")

                view = GameView(self.bet_amount, self.side_bets, is_split=True)
                await interaction.response.edit_message(embed=embed, view=view)
                return

        description = f"**{outcome_text}**\n\n**Bet Amount:** ₹{amount:,}\n**Balance Change:** {balance_change}"

        if side_bet_text:
            description += f"\n\n**Side Bets:**\n{side_bet_text}"

        if self.is_split:
            description += f"\n\n**Split Complete** - Both hands played"

        if self.is_double:
            description += f"\n\n**Double Down** - Bet was doubled"

        # Create return view
        view = CasinoView()
        view.play_game.disabled = False
        view.skip_game.disabled = False
        view.end_session.disabled = False
        view.cash_out.disabled = False

        embed = discord.Embed(
            title="🎰 BlackJack Casino - Game Recorded!",
            description=description,
            color=color
        )
        embed.add_field(name="💰 New Balance", value=f"₹{casino_data['balance']:,}", inline=True)
        embed.add_field(name="🎮 Session Games", value=f"{len(casino_data['session_games'])}", inline=True)
        embed.add_field(name="⏱️ Session Duration", value=f"{get_session_duration()}", inline=True)

        wins = sum(1 for g in casino_data['session_games'] if g['outcome'] == 'win')
        losses = sum(1 for g in casino_data['session_games'] if g['outcome'] == 'lose')
        ties = sum(1 for g in casino_data['session_games'] if g['outcome'] == 'tie')
        blackjacks = sum(1 for g in casino_data['session_games'] if g['outcome'] == 'blackjack')

        embed.add_field(name="📊 Session Stats", value=f"W: {wins} | L: {losses} | T: {ties} | BJ: {blackjacks}", inline=False)
        embed.set_footer(text="♠️ BlackJack Casino | Choose your next action")
        await interaction.response.edit_message(embed=embed, view=view)

class CashOutModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="💵 Enter Amount to Cash Out")
        self.amount_input = discord.ui.TextInput(label="Enter amount to cash out", placeholder="e.g., 500", required=True, max_length=10)
        self.add_item(self.amount_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.amount_input.value.replace('₹', '').replace(',', ''))
            if amount <= 0:
                await interaction.response.send_message("❌ Amount must be a positive number!", ephemeral=True)
                return
            if amount > casino_data["balance"]:
                await interaction.response.send_message("❌ Amount cannot be greater than current balance!", ephemeral=True)
                return
            casino_data["balance"] -= amount

            game_data = {"outcome": "cashout", "amount": amount, "timestamp": datetime.now().isoformat()}
            casino_data["session_games"].append(game_data)
            casino_data["games"].append(game_data)

            view = CasinoView()
            view.play_game.disabled = False
            view.skip_game.disabled = False
            view.end_session.disabled = False
            view.cash_out.disabled = False

            embed = discord.Embed(
                title="💵 Cash Out Successful!",
                description=f"**Cashed out: ₹{amount:,}**\n\nAmount has been added to your main balance.",
                color=0x00ff00
            )
            embed.add_field(name="💰 New Balance", value=f"₹{casino_data['balance']:,}", inline=True)
            embed.set_footer(text="♠️ BlackJack Casino")
            await interaction.response.edit_message(embed=embed, view=view)
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number for the amount!", ephemeral=True)

class GameCashOutModal(discord.ui.Modal):
    def __init__(self, bet_amount):
        super().__init__(title="💵 Cash Out From Bet")
        self.bet_amount = bet_amount
        self.amount_input = discord.ui.TextInput(
            label="Enter amount to cash out from bet", 
            placeholder=f"Max: {bet_amount}", 
            required=True, 
            max_length=10
        )
        self.add_item(self.amount_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            cashout_amount = int(self.amount_input.value.replace('₹', '').replace(',', ''))
            if cashout_amount <= 0:
                await interaction.response.send_message("❌ Amount must be a positive number!", ephemeral=True)
                return
            if cashout_amount > self.bet_amount:
                await interaction.response.send_message(f"❌ Cannot cash out more than bet amount (₹{self.bet_amount:,})!", ephemeral=True)
                return

            casino_data["balance"] += cashout_amount
            remaining_amount = self.bet_amount - cashout_amount

            game_data = {
                "outcome": "cashout", 
                "amount": self.bet_amount,
                "refund_amount": cashout_amount,
                "lost_amount": remaining_amount,
                "timestamp": datetime.now().isoformat()
            }
            casino_data["session_games"].append(game_data)
            casino_data["games"].append(game_data)

            view = CasinoView()
            view.play_game.disabled = False
            view.skip_game.disabled = False
            view.end_session.disabled = False
            view.cash_out.disabled = False

            embed = discord.Embed(
                title="💵 Partial Cash Out!",
                description=f"**Cashed out: ₹{cashout_amount:,}**\n**Lost from bet: ₹{remaining_amount:,}**\n\nCashed amount added to balance.",
                color=0x00aa00
            )
            embed.add_field(name="💰 New Balance", value=f"₹{casino_data['balance']:,}", inline=True)
            embed.set_footer(text="♠️ BlackJack Casino")
            await interaction.response.edit_message(embed=embed, view=view)
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number for the amount!", ephemeral=True)

class BalanceModal(discord.ui.Modal):
    def __init__(self, action="start"):
        super().__init__(title="💰 Set Starting Balance")
        self.balance_input = discord.ui.TextInput(label="Enter Starting Balance", placeholder="e.g., 1000", required=True, max_length=10)
        self.add_item(self.balance_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            balance = int(self.balance_input.value.replace('$', '').replace(',', ''))
            if balance <= 0:
                await interaction.response.send_message("❌ Balance must be a positive number!", ephemeral=True)
                return
            casino_data.update({
                "balance": balance,
                "starting_balance": balance,
                "session_active": True,
                "session_start": datetime.now(),
                "session_games": []
            })
            view = CasinoView()
            view.play_game.disabled = False
            view.skip_game.disabled = False
            view.end_session.disabled = False
            view.cash_out.disabled = False
            embed = discord.Embed(
                title="🎰 BlackJack Casino - Session Started!", 
                description="**🎲 Your casino session is now active!**\n\n**Options:**\n🎲 **Play**\n⏸️ **Skip**\n🛑 **End Session**", 
                color=0x00ff00
            )
            embed.add_field(name="💰 Starting Balance", value=f"₹{balance:,}", inline=True)
            embed.add_field(name="🎮 Games Played", value="0", inline=True)
            embed.add_field(name="⏱️ Session Started", value="Just now", inline=True)
            embed.set_footer(text="♠️ BlackJack Casino | Good luck!")
            await interaction.response.edit_message(embed=embed, view=view)
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number for the balance!", ephemeral=True)

class BetAmountModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="💰 Enter Bet Amount & Side Bets")
        self.amount_input = discord.ui.TextInput(label="Main bet amount", placeholder="e.g., 100", required=True, max_length=10)
        self.perfect_pair_input = discord.ui.TextInput(label="Perfect Pair side bet (optional)", placeholder="e.g., 20", required=False, max_length=10)
        self.twentyone_plus_three_input = discord.ui.TextInput(label="21+3 side bet (optional)", placeholder="e.g., 15", required=False, max_length=10)
        self.dealer_bust_input = discord.ui.TextInput(label="Dealer Bust side bet (optional)", placeholder="e.g., 10", required=False, max_length=10)

        self.add_item(self.amount_input)
        self.add_item(self.perfect_pair_input)
        self.add_item(self.twentyone_plus_three_input)
        self.add_item(self.dealer_bust_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            main_amount = int(self.amount_input.value.replace('₹', '').replace(',', ''))
            if main_amount <= 0:
                await interaction.response.send_message("❌ Main bet amount must be a positive number!", ephemeral=True)
                return

            # Parse side bets
            side_bets = {}
            total_side_bet = 0

            if self.perfect_pair_input.value:
                pp_amount = int(self.perfect_pair_input.value.replace('₹', '').replace(',', ''))
                if pp_amount > 0:
                    side_bets["Perfect Pair"] = pp_amount
                    total_side_bet += pp_amount

            if self.twentyone_plus_three_input.value:
                tpt_amount = int(self.twentyone_plus_three_input.value.replace('₹', '').replace(',', ''))
                if tpt_amount > 0:
                    side_bets["21 + 3"] = tpt_amount
                    total_side_bet += tpt_amount

            if self.dealer_bust_input.value:
                db_amount = int(self.dealer_bust_input.value.replace('₹', '').replace(',', ''))
                if db_amount > 0:
                    side_bets["Dealer Bust"] = db_amount
                    total_side_bet += db_amount

            total_bet = main_amount + total_side_bet
            if total_bet > casino_data["balance"]:
                await interaction.response.send_message(f"❌ Insufficient balance! Total bet: ₹{total_bet:,}, Balance: ₹{casino_data['balance']:,}", ephemeral=True)
                return

            # Deduct bet amount from balance when bet is placed
            casino_data["balance"] -= main_amount

            view = GameView(bet_amount=main_amount, side_bets=side_bets)

            description = f"**Choose your game outcome:**\n\n🟢 **WIN** - You won this round!\n🔴 **LOSE** - You lost this round!\n🟡 **TIE** - Push/Draw (no money change)\n🂡 **BLACKJACK** - Natural 21 (1.5x payout)\n💵 **CASH OUT** - Partial cash out from bet\n\n💰 **Main Bet:** ₹{main_amount:,}"

            if side_bets:
                description += "\n\n**Side Bets:**"
                for bet_type, bet_amount in side_bets.items():
                    description += f"\n• {bet_type}: ₹{bet_amount:,}"
                description += f"\n\n**Total Wagered:** ₹{total_bet:,}"

            embed = discord.Embed(
                title="🎲 BlackJack Game",
                description=description,
                color=0xffd700
            )
            embed.add_field(name="💰 Current Balance", value=f"₹{casino_data['balance']:,}", inline=True)
            embed.add_field(name="🎮 Session Games", value=f"{len(casino_data['session_games'])}", inline=True)
            embed.set_footer(text="♠️ BlackJack Casino | Choose your outcome")
            await interaction.response.edit_message(embed=embed, view=view)
        except ValueError:
            await interaction.response.send_message("❌ Please enter valid numbers for bet amounts!", ephemeral=True)

# =================================================================================================
# CASINO COMMANDS
# =================================================================================================

@bot.command(name='casino', aliases=['blackjack', 'bj'])
@has_moderator_role()
async def casino_command(ctx):
    """Open the casino interface."""
    try: 
        await ctx.message.delete()
    except discord.Forbidden: 
        pass

    await log_command(ctx, "&casino", "Opened casino interface")

    view = CasinoView()
    if casino_data["session_active"]:
        view.play_game.disabled = False
        view.skip_game.disabled = False
        view.end_session.disabled = False
        view.cash_out.disabled = False
        embed = discord.Embed(
            title="🎰 BlackJack Casino - Session Active", 
            description="**🎲 Welcome back to your active session!**", 
            color=0x00ff00
        )
        embed.add_field(name="💰 Current Balance", value=f"₹{casino_data['balance']:,}", inline=True)
        embed.add_field(name="🎮 Session Games", value=f"{len(casino_data['session_games'])}", inline=True)
        embed.add_field(name="⏱️ Session Duration", value=f"{get_session_duration()} minutes", inline=True)
    else:
        embed = discord.Embed(
            title="🎰 BlackJack Casino", 
            description="**Welcome to the premium BlackJack statistics tracker!**\n\nClick 'Start Session' to begin tracking!", 
            color=0xffd700
        )
        embed.add_field(
            name="🎲 How it Works", 
            value="1️⃣ Start a session with your balance\n2️⃣ Record each game as WIN or LOSE\n3️⃣ Enter bet amounts for tracking\n4️⃣ View detailed statistics & charts", 
            inline=False
        )

    embed.set_footer(text="♠️ BlackJack Casino | Professional Statistics Tracker")
    await ctx.send(embed=embed, view=view)

@bot.command(name='balance')
@has_moderator_role()
async def balance_command(ctx, member: discord.Member = None):
    """Check current casino balance."""
    if member:
        embed = discord.Embed(
            title="💰 Casino Balance Check",
            description=f"**{member.display_name}'s Balance:** ₹{casino_data['balance']:,}",
            color=0xffd700
        )
        await log_command(ctx, "&balance", f"Checked {member.mention}'s balance: ₹{casino_data['balance']:,}")
    else:
        embed = discord.Embed(
            title="💰 Casino Balance",
            description=f"**Current Balance:** ₹{casino_data['balance']:,}",
            color=0xffd700
        )
        await log_command(ctx, "&balance", f"Checked own balance: ₹{casino_data['balance']:,}")
    await ctx.send(embed=embed)

@bot.command(name='resetbalance')
@has_moderator_role()
async def reset_balance_command(ctx, member: discord.Member, amount: int):
    """Reset a user's casino balance."""
    try:
        await ctx.message.delete()
        if amount < 0:
            await ctx.send("❌ Balance amount must be positive!", delete_after=5)
            return

        old_balance = casino_data['balance']
        casino_data['balance'] = amount

        embed = discord.Embed(
            title="💰 Balance Reset",
            description=f"**{member.display_name}'s balance has been reset**\n\n**Old Balance:** ₹{old_balance:,}\n**New Balance:** ₹{amount:,}",
            color=0x00ff00
        )
        await ctx.send(embed=embed, delete_after=10)
        await log_command(ctx, "&resetbalance", f"Reset {member.mention}'s balance from ₹{old_balance:,} to ₹{amount:,}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to delete messages.")

@bot.command(name='help')
async def help_command(ctx):
    """Display help information for casino commands."""
    embed = discord.Embed(
        title="♠️ ʟᴏʟᴇᴛᴛᴀɴ - Help",
        description="**Premium Discord Bot for BlackJack Statistics Tracking**",
        color=0x000000
    )

    embed.add_field(
        name="📊 Bot Information",
        value="• **Prefix:** `&`\n• **Version:** Casino-Only\n• **Features:** Advanced BlackJack Tracking\n• **Uptime:** 24/7",
        inline=True
    )

    embed.add_field(
        name="🎰 Casino Commands",
        value="• **&casino** - Open casino interface\n• **&balance [@user]** - Check casino balance\n• **&resetbalance @user [amount]** - Reset balance\n• **Interactive Sessions** - Win/loss tracking with statistics",
        inline=False
    )

    embed.add_field(
        name="🎲 Casino Features",
        value="• **Session Tracking** - Complete game history\n• **Advanced Statistics** - Win rates, streaks, profit analysis\n• **Visual Charts** - Performance graphs\n• **Side Bets** - Perfect Pair, 21+3, Dealer Bust\n• **Split & Double** - Advanced BlackJack features\n• **Cash Out System** - Flexible balance management",
        inline=False
    )

    embed.set_footer(text="♠️ Use &casino to get started!")
    await ctx.send(embed=embed)

# =================================================================================================
# RUN THE BOT
# =================================================================================================

if __name__ == "__main__":
    # Start the web server to keep the bot alive
    keep_alive()

    # Get token from environment variable
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("❌ ERROR: DISCORD_TOKEN not found in environment variables!")
        print("Please add your Discord bot token to the Secrets tab.")
        print("1. Go to the Secrets tab (🔒) in the left sidebar")
        print("2. Add a new secret with key: DISCORD_TOKEN")
        print("3. Add your bot token as the value")
    else:
        # Run the bot
        try:
            print("🚀 Starting ʟᴏʟᴇᴛᴛᴀɴ...")
            bot.run(TOKEN)
        except Exception as e:
            print(f"❌ Error starting bot: {e}")
            print("Make sure your Discord token is valid and the bot has proper permissions.")
