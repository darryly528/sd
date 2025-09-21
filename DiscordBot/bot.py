import os
import asyncio
import discord
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv
import json

# Load environment variables from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise Exception("Bot token not found. Please set DISCORD_TOKEN in your .env file.")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(intents=intents)

USERNAMES_FILE = "usernames.json"

def load_usernames():
    if not os.path.exists(USERNAMES_FILE):
        return {}
    with open(USERNAMES_FILE, "r") as f:
        return json.load(f)

def save_usernames(data):
    with open(USERNAMES_FILE, "w") as f:
        json.dump(data, f, indent=4)

def is_verified(member):
    return any(role.name == "Verified" for role in member.roles)

def is_staff(member):
    return any(role.name == "Staff" for role in member.roles)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

# Ping slash command
@bot.tree.command(name="ping", description="Check the bot's latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! 🏓")

# Hello slash command
@bot.tree.command(name="hello", description="Say hello")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.mention}! 👋")

# Roblox verification slash command
@bot.tree.command(name="verify", description="Verify your Roblox username")
@discord.app_commands.describe(roblox_username="Your Roblox username")
async def verify(interaction: discord.Interaction, roblox_username: str):
    member = interaction.user
    if not is_verified(member):
        await interaction.response.send_message("❌ You must have the Verified role to use this command.", ephemeral=True)
        return
    usernames = load_usernames()
    usernames[str(member.id)] = roblox_username
    save_usernames(usernames)
    await interaction.response.send_message(f"✅ Your Roblox username `{roblox_username}` has been saved, {member.mention}!")

# Ticket system slash command
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
    staff_role = get(guild.roles, name="Staff")
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
    await ticket_channel.send(
        f"{member.mention} Thank you for opening a ticket! A staff member will be with you shortly."
    )
    await interaction.response.send_message(f"Your ticket has been created: {ticket_channel.mention}", ephemeral=True)

# Close ticket slash command (Staff only)
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

# Emergency listener
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    content = message.content.lower()
    emergencies = ["getting jumped", "need help"]
    if any(phrase in content for phrase in emergencies):
        guild = message.guild
        if guild:
            staff_role = get(guild.roles, name="Staff")
            if staff_role:
                staff_mentions = staff_role.mention
            else:
                staff_mentions = "@here"
            try:
                await message.channel.send(
                    f"🚨 Emergency detected from {message.author.mention}! {staff_mentions} please assist immediately."
                )
            except Exception:
                pass
    await bot.process_commands(message)

# Ready for Railway deployment
bot.run(TOKEN)