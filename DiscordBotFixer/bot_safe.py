import os
import asyncio
import discord
import re
import time
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv
from models import DatabaseManager

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise Exception("DISCORD_TOKEN not found. Please set DISCORD_TOKEN in your .env file.")

# Initialize database
db = DatabaseManager()

# Bot setup
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

def get_role_ci(guild, target_name):
    """Get role by case-insensitive name matching"""
    for role in guild.roles:
        if role.name.lower() == target_name.lower():
            return role
    return None

def is_verified(member):
    """Check if member has Verified role (case insensitive)"""
    return any(role.name.lower() == "verified" for role in member.roles)

def is_staff(member):
    """Check if member has Staff role (case insensitive)"""
    return any(role.name.lower() == "staff" for role in member.roles)

def is_yes_response(text):
    """Detect if response indicates 'yes'"""
    text = text.lower().strip()
    yes_patterns = [
        r'^yes$', r'^y$', r'^yeah$', r'^yep$', r'^yup$', r'^sure$', r'^ok$', r'^okay$',
        r'^definitely$', r'^absolutely$', r'^correct$', r'^right$', r'^true$',
        r'yes\b', r'\byes\b', r'yeah\b', r'\byeah\b'
    ]
    return any(re.search(pattern, text) for pattern in yes_patterns)

def is_no_response(text):
    """Detect if response indicates 'no'"""
    text = text.lower().strip()
    no_patterns = [
        r'^no$', r'^n$', r'^nope$', r'^nah$', r'^never$', r'^not$', r'^negative$',
        r'^incorrect$', r'^wrong$', r'^false$',
        r'no\b', r'\bno\b', r'nope\b', r'\bnope\b', r'not\b', r'\bnot\b'
    ]
    return any(re.search(pattern, text) for pattern in no_patterns)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")
    print(f"Bot is ready and connected to {len(bot.guilds)} servers")

@bot.tree.command(name="ping", description="Check the bot's latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! 🏓 Latency: {round(bot.latency * 1000)}ms")

@bot.tree.command(name="hello", description="Say hello")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.mention}! 👋")

@bot.tree.command(name="roblox_verify", description="Verify your Roblox username")
@discord.app_commands.describe(roblox_username="Your Roblox username")
async def roblox_verify(interaction: discord.Interaction, roblox_username: str):
    member = interaction.user
    
    if not is_verified(member):
        await interaction.response.send_message("❌ You must have the Verified role to use this command.", ephemeral=True)
        return
    
    try:
        # Save to database
        db.save_roblox_username(member.id, roblox_username)
        await interaction.response.send_message(f"✅ Your Roblox username `{roblox_username}` has been saved to the database, {member.mention}!", ephemeral=True)
    except Exception as e:
        print(f"Error saving Roblox username: {e}")
        await interaction.response.send_message("❌ There was an error saving your username. Please try again later.", ephemeral=True)

@bot.tree.command(name="ticket", description="Create a private ticket channel for support")
async def ticket(interaction: discord.Interaction):
    member = interaction.user
    guild = interaction.guild
    
    if not guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    
    if not is_verified(member):
        await interaction.response.send_message("❌ You must have the Verified role to use this command.", ephemeral=True)
        return
    
    staff_role = get_role_ci(guild, "Staff")
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    
    if staff_role:
        overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    
    channel_name = f"ticket-{member.name}".lower().replace(" ", "-")
    existing = discord.utils.get(guild.text_channels, name=channel_name)
    
    if existing:
        await interaction.response.send_message(f"You already have an open ticket: {existing.mention}", ephemeral=True)
        return
    
    ticket_channel = await guild.create_text_channel(
        channel_name,
        overwrites=overwrites,
        topic=f"Support ticket for {member.display_name}"
    )
    
    # Save ticket conversation to database
    try:
        db.save_ticket_conversation(member.id, ticket_channel.id, 'started')
    except Exception as e:
        print(f"Error saving ticket conversation: {e}")
    
    # Send initial bot message in ticket channel
    await ticket_channel.send(
        f"{member.mention} Thank you for opening a ticket! 🎫\n\n"
        f"I need to ask you a quick question first:\n"
        f"**Are you here to report a Member/Allie?** (Please respond with yes or no)"
    )
    
    await interaction.response.send_message(f"Your ticket has been created: {ticket_channel.mention}", ephemeral=True)

@bot.tree.command(name="close", description="Close the current ticket channel (Staff only)")
async def close(interaction: discord.Interaction):
    member = interaction.user
    guild = interaction.guild
    
    if not guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    
    if not is_staff(member):
        await interaction.response.send_message("❌ You must have the Staff role to use this command.", ephemeral=True)
        return
    
    channel = interaction.channel
    if channel and channel.name.startswith("ticket-"):
        await interaction.response.send_message("Closing ticket in 5 seconds...")
        await asyncio.sleep(5)
        await channel.delete()
    else:
        await interaction.response.send_message("This command can only be used in ticket channels.", ephemeral=True)

@bot.event
async def on_message(message):
    # Ignore bot messages
    if message.author.bot:
        return
    
    guild = message.guild
    if not guild:
        return
    
    # Emergency detection system
    content = message.content.lower()
    emergency_phrases = ["getting jumped", "need help"]
    
    if any(phrase in content for phrase in emergency_phrases):
        # Get the user's Roblox username from database
        try:
            roblox_username = db.get_roblox_username(message.author.id)
            if roblox_username:
                # Send /snipe command with bloxiana and target
                members_role = get_role_ci(guild, "members")
                if members_role:
                    members_mention = members_role.mention
                else:
                    # Fallback to @here if members role not found
                    members_mention = "@here"
                
                await message.channel.send(
                    f"🚨 **EMERGENCY DETECTED** 🚨\n"
                    f"/snipe bloxiana baddies {roblox_username}\n"
                    f"{members_mention} Emergency assistance needed for {message.author.mention}!"
                )
            else:
                # Fallback if no Roblox username found
                staff_role = get_role_ci(guild, "Staff")
                staff_mention = staff_role.mention if staff_role else "@here"
                await message.channel.send(
                    f"🚨 **EMERGENCY DETECTED** 🚨\n"
                    f"{staff_mention} {message.author.mention} needs immediate assistance!"
                )
        except Exception as e:
            print(f"Error in emergency detection: {e}")
            # Fallback emergency response
            staff_role = get_role_ci(guild, "Staff")
            staff_mention = staff_role.mention if staff_role else "@here"
            await message.channel.send(
                f"🚨 **EMERGENCY DETECTED** 🚨\n"
                f"{staff_mention} {message.author.mention} needs immediate assistance!"
            )
    
    # Ticket conversation handling
    if message.channel.name.startswith("ticket-"):
        try:
            ticket_data = db.get_ticket_conversation(message.channel.id)
            if ticket_data and ticket_data['conversation_state'] == 'started':
                # Check if this is a response to the member/allie question
                if is_yes_response(message.content):
                    # User is reporting a member/allie
                    db.update_ticket_conversation(message.channel.id, 'reporting_member', True)
                    staff_role = get_role_ci(guild, "Staff")
                    staff_mention = staff_role.mention if staff_role else "@here"
                    
                    await message.channel.send(
                        f"Ok a {staff_mention} member is otw, in the meantime Type what happened and send proof."
                    )
                    
                elif is_no_response(message.content):
                    # User is not reporting a member/allie
                    db.update_ticket_conversation(message.channel.id, 'general_help', False)
                    staff_role = get_role_ci(guild, "Staff")
                    staff_mention = staff_role.mention if staff_role else "@here"
                    
                    await message.channel.send(
                        f"Ok then {staff_mention} Help is otw"
                    )
                    
        except Exception as e:
            print(f"Error in ticket conversation handling: {e}")
    
    # Process commands
    await bot.process_commands(message)

# Rate limit handling with exponential backoff
async def run_bot_with_retry():
    retry_count = 0
    max_retries = 5
    base_delay = 60  # Start with 1 minute
    
    while retry_count < max_retries:
        try:
            print(f"🤖 Starting Discord bot (attempt {retry_count + 1}/{max_retries})...")
            await bot.start(TOKEN)
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                retry_count += 1
                if retry_count >= max_retries:
                    print(f"❌ Max retries reached. Discord is rate limiting. Please wait and try again later.")
                    return
                
                delay = base_delay * (2 ** (retry_count - 1))  # Exponential backoff
                print(f"⏱️ Rate limited by Discord. Waiting {delay} seconds before retry {retry_count + 1}/{max_retries}...")
                await asyncio.sleep(delay)
            else:
                print(f"❌ Discord error: {e}")
                return
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return

# Run the bot with retry logic
if __name__ == "__main__":
    asyncio.run(run_bot_with_retry())