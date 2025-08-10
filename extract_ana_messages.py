#!/usr/bin/env python3
# /// script
# dependencies = []
# ///

import sqlite3
import json
from datetime import datetime
import os

def extract_ana_sipciu_messages():
    # Database path
    db_path = "whatsapp-bridge/store/messages.db"
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # First find Ana Sipciu's chat
        print("Searching for Ana Sipciu's chat...")
        cursor.execute("""
            SELECT jid, name, last_message_time 
            FROM chats 
            WHERE LOWER(name) LIKE '%ana%sipciu%' 
               OR LOWER(name) LIKE '%sipciu%ana%'
        """)
        
        chats = cursor.fetchall()
        
        if not chats:
            print("No chat found with Ana Sipciu")
            print("\nAvailable chats:")
            cursor.execute("SELECT jid, name FROM chats WHERE name IS NOT NULL ORDER BY name")
            for chat in cursor.fetchall():
                print(f"  - {chat['name']} ({chat['jid']})")
            return
        
        # If multiple chats found, show them
        if len(chats) > 1:
            print(f"Found {len(chats)} chats matching 'Ana Sipciu':")
            for i, chat in enumerate(chats):
                print(f"  {i+1}. {chat['name']} - {chat['jid']}")
            print("Using the first one...")
        
        chat = chats[0]
        chat_jid = chat['jid']
        chat_name = chat['name']
        
        print(f"Found chat: {chat_name} ({chat_jid})")
        
        # Get all messages from this chat
        cursor.execute("""
            SELECT 
                id,
                chat_jid,
                sender,
                content,
                timestamp,
                is_from_me,
                media_type,
                filename,
                url
            FROM messages 
            WHERE chat_jid = ? 
            ORDER BY timestamp ASC
        """, (chat_jid,))
        
        messages = cursor.fetchall()
        
        if not messages:
            print(f"No messages found in chat with {chat_name}")
            return
        
        print(f"Found {len(messages)} messages")
        
        # Convert to JSON-serializable format - only relevant info
        messages_list = []
        for msg in messages:
            # Truncate content to 300 characters
            content = msg['content'] or ''
            if len(content) > 300:
                content = content[:297] + '...'
            
            # Start with essential fields
            message_dict = {
                'timestamp': msg['timestamp'],
                'sender': 'You' if msg['is_from_me'] else msg['sender'] or chat_name,
                'content': content
            }
            
            # Add media info only if present
            if msg['media_type']:
                message_dict['media'] = msg['media_type']
                if msg['filename']:
                    message_dict['filename'] = msg['filename']
            
            messages_list.append(message_dict)
        
        # Export data - simplified format
        output_data = {
            'chat': chat_name,
            'total_messages': len(messages_list),
            'messages': messages_list
        }
        
        # Save to JSON file
        output_file = f"ana_conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nMessages exported successfully to: {output_file}")
        
        # Show some statistics
        print(f"\nStatistics:")
        print(f"  Total messages: {len(messages_list)}")
        
        # Count messages by sender
        from_me = sum(1 for m in messages_list if m['sender'] == 'You')
        from_ana = len(messages_list) - from_me
        print(f"  From you: {from_me}")
        print(f"  From Ana: {from_ana}")
        
        # Count media messages
        media_messages = sum(1 for m in messages_list if 'media' in m)
        print(f"  Media messages: {media_messages}")
        
        if messages_list:
            first_msg = messages_list[0]
            last_msg = messages_list[-1]
            print(f"  First message: {first_msg['timestamp']}")
            print(f"  Last message: {last_msg['timestamp']}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == "__main__":
    extract_ana_sipciu_messages()