# Discord Bot Project

## Overview

This is a Discord bot built with Python that provides server management and verification functionality. The bot handles user verification through Roblox username registration, includes staff moderation tools, and maintains persistent data storage using PostgreSQL. The application is designed to run on Railway with automatic deployment and includes both traditional command handling and modern slash command support.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

**Bot Framework**: Built using discord.py 2.6.3 with a command-based architecture. The bot uses both traditional prefix commands (!) and modern slash commands for different functionalities.

**Authentication & Permissions**: Implements role-based access control with case-insensitive role checking for "Verified" and "Staff" roles. The verification system ensures proper user access to different bot features.

**Database Layer**: Uses PostgreSQL with raw SQL queries through psycopg2 for data persistence. The database manager implements connection pooling and proper SSL handling for Railway deployments. Database tables include:
- `roblox_users`: Stores Discord user ID to Roblox username mappings
- `ticket_conversations`: Tracks support ticket states and conversations

**Message Processing**: Includes intelligent response detection with regex pattern matching for user interactions, particularly for "yes/no" responses during verification flows.

**Deployment Architecture**: Configured for Railway deployment with Nixpacks builder, automatic restarts on failure (max 10 retries), and environment-based configuration management.

**Error Handling**: Implements robust error handling with connection management using context managers and proper resource cleanup.

## External Dependencies

**Discord API**: Primary integration through discord.py library for all bot functionality including member management, role assignments, and message handling.

**PostgreSQL Database**: Hosted database (likely Railway PostgreSQL) for persistent data storage, accessed via DATABASE_URL environment variable with SSL requirement detection.

**Railway Platform**: Cloud deployment platform with automatic builds, environment variable management, and service hosting.

**Environment Configuration**: Uses python-dotenv for local development environment variable management, with production variables managed through Railway's dashboard.

**Python Runtime**: Specified Python 3.11.13 runtime for consistent deployment environment across development and production.