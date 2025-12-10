#!/usr/bin/env python3
"""
Generate Discord Bot Invite URL
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_invite_url():
    """Generate Discord bot invite URL with correct permissions"""
    
    # Get application ID from .env
    application_id = os.getenv('APPLICATION_ID')
    
    if not application_id:
        print("❌ APPLICATION_ID not found in .env file")
        return None
    
    # Permissions we need (based on what we discussed)
    permissions = [
        "SendMessages",           # Send messages
        "EmbedLinks",             # Send embeds
        "AttachFiles",            # Upload files
        "ReadMessageHistory",     # Read message history
        "AddReactions",           # Add reactions
        "ViewChannel",            # View channels
        "UseSlashCommands",       # Use slash commands (if needed later)
        "ManageMessages",         # Manage messages (optional)
    ]
    
    # Calculate permission integer
    permission_bits = {
        "SendMessages": 0x8000,
        "EmbedLinks": 0x4000,
        "AttachFiles": 0x8000,
        "ReadMessageHistory": 0x10000,
        "AddReactions": 0x40,
        "ViewChannel": 0x400,
        "UseSlashCommands": 0x800000000,
        "ManageMessages": 0x2000,
    }
    
    total_permissions = sum(permission_bits[perm] for perm in permissions)
    
    # Generate invite URL
    invite_url = f"https://discord.com/api/oauth2/authorize?client_id={application_id}&permissions={total_permissions}&scope=bot%20applications.commands"
    
    return invite_url

def main():
    """Main function"""
    print("🔗 Generating Discord Bot Invite URL...")
    
    invite_url = generate_invite_url()
    
    if invite_url:
        print("\n✅ Your bot invite URL:")
        print("=" * 50)
        print(invite_url)
        print("=" * 50)
        print("\n📋 Instructions:")
        print("1. Copy the URL above")
        print("2. Open it in your browser")
        print("3. Select your server")
        print("4. Click 'Authorize'")
        print("5. Complete the captcha if prompted")
        print("\n⚠️  Make sure you've enabled the required intents in Discord Developer Portal:")
        print("   - Go to https://discord.com/developers/applications/")
        print("   - Select your application")
        print("   - Go to 'Bot' section")
        print("   - Enable 'Message Content Intent'")
        print("   - Save changes")
    else:
        print("❌ Failed to generate invite URL")

if __name__ == '__main__':
    main() 