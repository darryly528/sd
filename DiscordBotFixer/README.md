# Enhanced Discord Bot

## Features

🎫 **Interactive Ticket System**
- Users create tickets with `/ticket` command
- Bot asks: "Are you here to report a Member/Allie?"
- Smart yes/no response detection
- Conditional staff responses based on user answers

🚨 **Emergency Response System**
- Detects "getting jumped" or "need help" messages
- Posts `/snipe bloxiana baddies {username}` command
- Automatically pings @members role

🎮 **Roblox Username Integration**
- `/roblox_verify` command stores usernames in PostgreSQL
- Usernames are used in emergency responses
- Persistent database storage

## Files

- `bot.py` - Main bot file (production ready)
- `bot_safe.py` - Rate limit safe version (currently running)
- `models.py` - Database models and PostgreSQL integration
- `requirements.txt` - Python dependencies
- `railway.json` - Railway deployment configuration
- `Procfile` - Process configuration
- `runtime.txt` - Python version specification

## Running the Bot

The bot is currently running with smart rate limit handling. It will automatically retry connections if Discord temporarily blocks access.

## Deployment

Ready for Railway.com deployment with all configuration files included.