import os
import sys
import asyncio
from supabase import create_client
from telegram import Bot

print("=" * 50)
print("DEBUG: Starting script...")

# Check secrets
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not SUPABASE_KEY:
    print("ERROR: SUPABASE_KEY is missing!")
    sys.exit(1)
else:
    print(f"DEBUG: SUPABASE_KEY found (starts with: {SUPABASE_KEY[:10]}...)")

if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN is missing!")
    sys.exit(1)
else:
    print(f"DEBUG: BOT_TOKEN found (starts with: {BOT_TOKEN[:10]}...)")

SUPABASE_URL = "https://lcjtkggyalebvmkexisp.supabase.co"

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("DEBUG: Supabase client created")
except Exception as e:
    print(f"ERROR creating Supabase client: {e}")
    sys.exit(1)

try:
    bot = Bot(token=BOT_TOKEN)
    print("DEBUG: Bot created")
except Exception as e:
    print(f"ERROR creating Bot: {e}")
    sys.exit(1)

async def main():
    print("\nDEBUG: Fetching users...")
    try:
        result = supabase.table('users').select('*').execute()
        print(f"DEBUG: Query result: {result}")
        print(f"DEBUG: Data returned: {result.data}")
        
        if not result.data:
            print("ERROR: No users found in database!")
            await bot.send_message(1415309098, "❌ Database query returned empty. Check if data exists.")
            return
            
        user = result.data[0]
        print(f"DEBUG: Found user: {user}")
        await bot.send_message(1415309098, f"✅ Success! Found user: {user['telegram_id']}")
        
    except Exception as e:
        print(f"ERROR querying database: {e}")
        await bot.send_message(1415309098, f"❌ Database error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
