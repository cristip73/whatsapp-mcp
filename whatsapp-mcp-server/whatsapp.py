import sqlite3
import time
from datetime import datetime
from dataclasses import dataclass
from typing import Any, Dict, Optional, List, Tuple
import os.path
import requests
import json
import audio
import os # Ensure os is imported

# MESSAGES_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'whatsapp-bridge', 'store', 'messages.db')
WHATSAPP_API_BASE_URL = "http://localhost:8080/api"

_global_attachments_path = None

def initialize_attachments_path(path: str) -> None:
    global _global_attachments_path
    if not os.path.isabs(path):
        # Or raise an error, or try to make it absolute based on some convention
        # For now, let's assume the input path from main.py is already absolute as per arg help text
        print(f"Warning: Attachments path '{path}' is not absolute. This might lead to unexpected behavior.")
    _global_attachments_path = path
    # You could add a check here to see if the path exists or try to create it,
    # but the Go bridge is primarily responsible for creating it.
    # For the Python side, it's mainly for constructing the DB path.

def get_messages_db_path() -> str:
    if _global_attachments_path is None:
        raise ValueError("Attachments path has not been initialized. Call initialize_attachments_path() first.")
    # The messages.db is directly inside the _global_attachments_path, 
    # consistent with how the Go bridge will now store it (e.g., /custom_path/messages.db)
    return os.path.join(_global_attachments_path, 'messages.db')

@dataclass
class Message:
    timestamp: datetime
    sender: str
    content: str
    is_from_me: bool
    chat_jid: str
    id: str
    chat_name: Optional[str] = None
    media_type: Optional[str] = None

@dataclass
class Chat:
    jid: str
    name: Optional[str]
    last_message_time: Optional[datetime]
    last_message: Optional[str] = None
    last_sender: Optional[str] = None
    last_is_from_me: Optional[bool] = None

    @property
    def is_group(self) -> bool:
        """Determine if chat is a group based on JID pattern."""
        return self.jid.endswith("@g.us")

@dataclass
class Contact:
    phone_number: str
    name: Optional[str]
    jid: str

@dataclass
class MessageContext:
    message: Message
    before: List[Message]
    after: List[Message]

def get_sender_name(sender_jid: str) -> str:
    try:
        conn = sqlite3.connect(get_messages_db_path())
        cursor = conn.cursor()
        
        # First try matching by exact JID
        cursor.execute("""
            SELECT name
            FROM chats
            WHERE jid = ?
            LIMIT 1
        """, (sender_jid,))
        
        result = cursor.fetchone()
        
        # If no result, try looking for the number within JIDs
        if not result:
            # Extract the phone number part if it's a JID
            if '@' in sender_jid:
                phone_part = sender_jid.split('@')[0]
            else:
                phone_part = sender_jid
                
            cursor.execute("""
                SELECT name
                FROM chats
                WHERE jid LIKE ? AND jid NOT LIKE '%@g.us'
                LIMIT 1
            """, (f"%{phone_part}%",))
            
            result = cursor.fetchone()
        
        if result and result[0]:
            return result[0]
        else:
            return sender_jid
        
    except sqlite3.Error as e:
        print(f"Database error while getting sender name: {e}")
        return sender_jid
    finally:
        if 'conn' in locals():
            conn.close()

def format_message(message: Message, show_chat_info: bool = True) -> None:
    """Print a single message with consistent formatting."""
    output = ""
    
    if show_chat_info and message.chat_name:
        output += f"[{message.timestamp:%Y-%m-%d %H:%M:%S}] [ID: {message.id}] Chat: {message.chat_name} "
    else:
        output += f"[{message.timestamp:%Y-%m-%d %H:%M:%S}] [ID: {message.id}] "

    content_prefix = ""
    if hasattr(message, 'media_type') and message.media_type:
        content_prefix = f"[{message.media_type} - Chat JID: {message.chat_jid}] "

    try:
        sender_name = get_sender_name(message.sender) if not message.is_from_me else "Me"
        output += f"From: {sender_name}: {content_prefix}{message.content}\n"
    except Exception as e:
        print(f"Error formatting message: {e}")
    return output

def format_messages_list(messages: List[Message], show_chat_info: bool = True) -> None:
    output = ""
    if not messages:
        output += "No messages to display."
        return output
    
    for message in messages:
        output += format_message(message, show_chat_info)
    return output

def list_messages(
    after: Optional[str] = None,
    before: Optional[str] = None,
    sender_phone_number: Optional[str] = None,
    chat_jid: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_context: bool = True,
    context_before: int = 1,
    context_after: int = 1
) -> List[Message]:
    """Get messages matching the specified criteria with optional context."""
    try:
        conn = sqlite3.connect(get_messages_db_path())
        cursor = conn.cursor()
        
        # Build base query
        query_parts = ["SELECT messages.timestamp, messages.sender, chats.name, messages.content, messages.is_from_me, chats.jid, messages.id, messages.media_type FROM messages"]
        query_parts.append("JOIN chats ON messages.chat_jid = chats.jid")
        where_clauses = []
        params = []
        
        # Add filters
        if after:
            try:
                after = datetime.fromisoformat(after)
            except ValueError:
                raise ValueError(f"Invalid date format for 'after': {after}. Please use ISO-8601 format.")
            
            where_clauses.append("messages.timestamp > ?")
            params.append(after)

        if before:
            try:
                before = datetime.fromisoformat(before)
            except ValueError:
                raise ValueError(f"Invalid date format for 'before': {before}. Please use ISO-8601 format.")
            
            where_clauses.append("messages.timestamp < ?")
            params.append(before)

        if sender_phone_number:
            where_clauses.append("messages.sender = ?")
            params.append(sender_phone_number)
            
        if chat_jid:
            where_clauses.append("messages.chat_jid = ?")
            params.append(chat_jid)
            
        if query:
            where_clauses.append("LOWER(messages.content) LIKE LOWER(?)")
            params.append(f"%{query}%")
            
        if where_clauses:
            query_parts.append("WHERE " + " AND ".join(where_clauses))
            
        # Add pagination
        offset = page * limit
        query_parts.append("ORDER BY messages.timestamp DESC")
        query_parts.append("LIMIT ? OFFSET ?")
        params.extend([limit, offset])
        
        cursor.execute(" ".join(query_parts), tuple(params))
        messages = cursor.fetchall()
        
        result = []
        for msg in messages:
            message = Message(
                timestamp=datetime.fromisoformat(msg[0]),
                sender=msg[1],
                chat_name=msg[2],
                content=msg[3],
                is_from_me=msg[4],
                chat_jid=msg[5],
                id=msg[6],
                media_type=msg[7]
            )
            result.append(message)
            
        if include_context and result:
            # Add context for each message
            messages_with_context = []
            for msg in result:
                context = get_message_context(msg.id, context_before, context_after)
                messages_with_context.extend(context.before)
                messages_with_context.append(context.message)
                messages_with_context.extend(context.after)
            
            return format_messages_list(messages_with_context, show_chat_info=True)
            
        # Format and display messages without context
        return format_messages_list(result, show_chat_info=True)    
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def get_message_context(
    message_id: str,
    before: int = 5,
    after: int = 5
) -> MessageContext:
    """Get context around a specific message."""
    try:
        conn = sqlite3.connect(get_messages_db_path())
        cursor = conn.cursor()
        
        # Get the target message first
        cursor.execute("""
            SELECT messages.timestamp, messages.sender, chats.name, messages.content, messages.is_from_me, chats.jid, messages.id, messages.chat_jid, messages.media_type
            FROM messages
            JOIN chats ON messages.chat_jid = chats.jid
            WHERE messages.id = ?
        """, (message_id,))
        msg_data = cursor.fetchone()
        
        if not msg_data:
            raise ValueError(f"Message with ID {message_id} not found")
            
        target_message = Message(
            timestamp=datetime.fromisoformat(msg_data[0]),
            sender=msg_data[1],
            chat_name=msg_data[2],
            content=msg_data[3],
            is_from_me=msg_data[4],
            chat_jid=msg_data[5],
            id=msg_data[6],
            media_type=msg_data[8]
        )
        
        # Get messages before
        cursor.execute("""
            SELECT messages.timestamp, messages.sender, chats.name, messages.content, messages.is_from_me, chats.jid, messages.id, messages.media_type
            FROM messages
            JOIN chats ON messages.chat_jid = chats.jid
            WHERE messages.chat_jid = ? AND messages.timestamp < ?
            ORDER BY messages.timestamp DESC
            LIMIT ?
        """, (msg_data[7], msg_data[0], before))
        
        before_messages = []
        for msg in cursor.fetchall():
            before_messages.append(Message(
                timestamp=datetime.fromisoformat(msg[0]),
                sender=msg[1],
                chat_name=msg[2],
                content=msg[3],
                is_from_me=msg[4],
                chat_jid=msg[5],
                id=msg[6],
                media_type=msg[7]
            ))
        
        # Get messages after
        cursor.execute("""
            SELECT messages.timestamp, messages.sender, chats.name, messages.content, messages.is_from_me, chats.jid, messages.id, messages.media_type
            FROM messages
            JOIN chats ON messages.chat_jid = chats.jid
            WHERE messages.chat_jid = ? AND messages.timestamp > ?
            ORDER BY messages.timestamp ASC
            LIMIT ?
        """, (msg_data[7], msg_data[0], after))
        
        after_messages = []
        for msg in cursor.fetchall():
            after_messages.append(Message(
                timestamp=datetime.fromisoformat(msg[0]),
                sender=msg[1],
                chat_name=msg[2],
                content=msg[3],
                is_from_me=msg[4],
                chat_jid=msg[5],
                id=msg[6],
                media_type=msg[7]
            ))
        
        return MessageContext(
            message=target_message,
            before=before_messages,
            after=after_messages
        )
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()


def list_chats(
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_last_message: bool = True,
    sort_by: str = "last_active"
) -> List[Chat]:
    """Get chats matching the specified criteria."""
    try:
        conn = sqlite3.connect(get_messages_db_path())
        cursor = conn.cursor()
        
        # Build base query
        query_parts = ["""
            SELECT 
                chats.jid,
                chats.name,
                chats.last_message_time,
                messages.content as last_message,
                messages.sender as last_sender,
                messages.is_from_me as last_is_from_me
            FROM chats
        """]
        
        if include_last_message:
            query_parts.append("""
                LEFT JOIN messages ON chats.jid = messages.chat_jid 
                AND chats.last_message_time = messages.timestamp
            """)
            
        where_clauses = []
        params = []
        
        if query:
            where_clauses.append("(LOWER(chats.name) LIKE LOWER(?) OR chats.jid LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])
            
        if where_clauses:
            query_parts.append("WHERE " + " AND ".join(where_clauses))
            
        # Add sorting
        order_by = "chats.last_message_time DESC" if sort_by == "last_active" else "chats.name"
        query_parts.append(f"ORDER BY {order_by}")
        
        # Add pagination
        offset = (page ) * limit
        query_parts.append("LIMIT ? OFFSET ?")
        params.extend([limit, offset])
        
        cursor.execute(" ".join(query_parts), tuple(params))
        chats = cursor.fetchall()
        
        result = []
        for chat_data in chats:
            chat = Chat(
                jid=chat_data[0],
                name=chat_data[1],
                last_message_time=datetime.fromisoformat(chat_data[2]) if chat_data[2] else None,
                last_message=chat_data[3],
                last_sender=chat_data[4],
                last_is_from_me=chat_data[5]
            )
            result.append(chat)
            
        return result
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def search_contacts(query: str) -> List[Contact]:
    """Search contacts by name or phone number."""
    try:
        conn = sqlite3.connect(get_messages_db_path())
        cursor = conn.cursor()
        
        # Split query into characters to support partial matching
        search_pattern = '%' +query + '%'
        
        cursor.execute("""
            SELECT DISTINCT 
                jid,
                name
            FROM chats
            WHERE 
                (LOWER(name) LIKE LOWER(?) OR LOWER(jid) LIKE LOWER(?))
                AND jid NOT LIKE '%@g.us'
            ORDER BY name, jid
            LIMIT 50
        """, (search_pattern, search_pattern))
        
        contacts = cursor.fetchall()
        
        result = []
        for contact_data in contacts:
            contact = Contact(
                phone_number=contact_data[0].split('@')[0],
                name=contact_data[1],
                jid=contact_data[0]
            )
            result.append(contact)
            
        return result
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def get_contact_chats(jid: str, limit: int = 20, page: int = 0) -> List[Chat]:
    """Get all chats involving the contact.
    
    Args:
        jid: The contact's JID to search for
        limit: Maximum number of chats to return (default 20)
        page: Page number for pagination (default 0)
    """
    try:
        conn = sqlite3.connect(get_messages_db_path())
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT
                c.jid,
                c.name,
                c.last_message_time,
                m.content as last_message,
                m.sender as last_sender,
                m.is_from_me as last_is_from_me
            FROM chats c
            JOIN messages m ON c.jid = m.chat_jid
            WHERE m.sender = ? OR c.jid = ?
            ORDER BY c.last_message_time DESC
            LIMIT ? OFFSET ?
        """, (jid, jid, limit, page * limit))
        
        chats = cursor.fetchall()
        
        result = []
        for chat_data in chats:
            chat = Chat(
                jid=chat_data[0],
                name=chat_data[1],
                last_message_time=datetime.fromisoformat(chat_data[2]) if chat_data[2] else None,
                last_message=chat_data[3],
                last_sender=chat_data[4],
                last_is_from_me=chat_data[5]
            )
            result.append(chat)
            
        return result
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def get_contact_groups(jid: str) -> List[Dict[str, Any]]:
    """Get all WhatsApp groups where both you and the contact are members.
    Uses live WhatsApp data (not just message history) so finds ALL common groups.

    Args:
        jid: The contact's JID (e.g., "40730883388@s.whatsapp.net") or phone number
    """
    try:
        url = f"{WHATSAPP_API_BASE_URL}/get_contact_groups"
        payload = {"jid": jid}
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            result = response.json()
            if result.get("success", False):
                return result.get("groups", [])
            else:
                print(f"Failed: {result.get('message', 'Unknown error')}")
                return []
        else:
            print(f"Error: HTTP {response.status_code} - {response.text}")
            return []
    except requests.RequestException as e:
        print(f"Request error: {str(e)}")
        return []
    except json.JSONDecodeError:
        print(f"Error parsing response: {response.text}")
        return []


# --- Group Info & Management ---

def get_group_info(jid: str, include_participants: bool = False, participant_limit: int = 50, participant_offset: int = 0) -> Dict[str, Any]:
    """Get group metadata with optional participant list."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/get_group_info"
        payload = {"jid": jid}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            if result.get("success") and "group" in result:
                group = result["group"]
                participants = group.get("participants", [])
                group["participant_count"] = len(participants)
                if not include_participants:
                    del group["participants"]
                else:
                    group["participants"] = participants[participant_offset:participant_offset + participant_limit]
            return result
        else:
            return {"success": False, "message": f"HTTP {response.status_code}: {response.text}"}
    except requests.RequestException as e:
        return {"success": False, "message": f"Request error: {str(e)}"}


def get_group_invite_link(jid: str, reset: bool = False) -> Tuple[bool, str, str]:
    """Get or reset group invite link."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/get_group_invite_link"
        payload = {"jid": jid, "reset": reset}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", ""), result.get("link", "")
        else:
            return False, f"HTTP {response.status_code}: {response.text}", ""
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}", ""


def set_group_topic(jid: str, topic: str) -> Tuple[bool, str]:
    """Set group description/topic."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/set_group_topic"
        payload = {"jid": jid, "topic": topic}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "")
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"


def set_group_announce(jid: str, announce: bool) -> Tuple[bool, str]:
    """Toggle admin-only messaging for a group."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/set_group_announce"
        payload = {"jid": jid, "announce": announce}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "")
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"


def set_group_locked(jid: str, locked: bool) -> Tuple[bool, str]:
    """Toggle admin-only info editing for a group."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/set_group_locked"
        payload = {"jid": jid, "locked": locked}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "")
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"


def set_group_join_approval(jid: str, mode: bool) -> Tuple[bool, str]:
    """Toggle join approval mode for a group."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/set_group_join_approval"
        payload = {"jid": jid, "mode": mode}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "")
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"


def is_on_whatsapp(phones: List[str]) -> Dict[str, Any]:
    """Check if phone numbers are registered on WhatsApp."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/is_on_whatsapp"
        payload = {"phones": phones}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "message": f"HTTP {response.status_code}: {response.text}"}
    except requests.RequestException as e:
        return {"success": False, "message": f"Request error: {str(e)}"}


# --- Message Operations ---

def send_reaction(chat_jid: str, sender_jid: str, message_id: str, reaction: str) -> Tuple[bool, str]:
    """Send a reaction to a message."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/send_reaction"
        payload = {"chat_jid": chat_jid, "sender_jid": sender_jid, "message_id": message_id, "reaction": reaction}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "")
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"


def edit_message(chat_jid: str, message_id: str, new_text: str) -> Tuple[bool, str]:
    """Edit a sent message."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/edit_message"
        payload = {"chat_jid": chat_jid, "message_id": message_id, "new_text": new_text}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "")
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"


def delete_message(chat_jid: str, sender_jid: str, message_id: str) -> Tuple[bool, str]:
    """Delete/revoke a message."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/delete_message"
        payload = {"chat_jid": chat_jid, "sender_jid": sender_jid, "message_id": message_id}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "")
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"


def mark_read(chat_jid: str, sender_jid: str, message_ids: List[str]) -> Tuple[bool, str]:
    """Mark messages as read."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/mark_read"
        payload = {"chat_jid": chat_jid, "sender_jid": sender_jid, "message_ids": message_ids}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "")
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"


def create_poll(chat_jid: str, question: str, options: List[str], max_selections: int = 1) -> Tuple[bool, str]:
    """Create a WhatsApp poll."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/create_poll"
        payload = {"chat_jid": chat_jid, "question": question, "options": options, "max_selections": max_selections}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "")
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"


def send_reply(chat_jid: str, quoted_message_id: str, quoted_sender_jid: str, message: str, quoted_content: str = "") -> Tuple[bool, str]:
    """Reply to a specific message."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/send_reply"
        payload = {
            "chat_jid": chat_jid,
            "quoted_message_id": quoted_message_id,
            "quoted_sender_jid": quoted_sender_jid,
            "message": message,
            "quoted_content": quoted_content,
        }
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "")
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"


# --- Advanced ---

def send_presence(presence: str) -> Tuple[bool, str]:
    """Set online/offline presence."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/send_presence"
        payload = {"presence": presence}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "")
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"


def set_status_message(message: str) -> Tuple[bool, str]:
    """Change the 'About' status text."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/set_status_message"
        payload = {"message": message}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "")
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"


def create_newsletter(name: str, description: str = "") -> Dict[str, Any]:
    """Create a WhatsApp Channel/Newsletter."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/create_newsletter"
        payload = {"name": name, "description": description}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "message": f"HTTP {response.status_code}: {response.text}"}
    except requests.RequestException as e:
        return {"success": False, "message": f"Request error: {str(e)}"}


def get_newsletters() -> Dict[str, Any]:
    """List subscribed newsletters/channels."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/get_newsletters"
        response = requests.post(url, json={})
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "message": f"HTTP {response.status_code}: {response.text}"}
    except requests.RequestException as e:
        return {"success": False, "message": f"Request error: {str(e)}"}


def newsletter_send(jid: str, message: str) -> Tuple[bool, str]:
    """Send a message to a newsletter channel."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/newsletter_send"
        payload = {"jid": jid, "message": message}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "")
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"


def send_status(message: str) -> Tuple[bool, str]:
    """Post to WhatsApp Status (stories, 24h)."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/send_status"
        payload = {"message": message}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "")
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"


# --- Community ---

def link_group(parent_jid: str, child_jid: str) -> Tuple[bool, str]:
    """Link a group to a community."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/link_group"
        payload = {"parent_jid": parent_jid, "child_jid": child_jid}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "")
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"


def unlink_group(parent_jid: str, child_jid: str) -> Tuple[bool, str]:
    """Unlink a group from a community."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/unlink_group"
        payload = {"parent_jid": parent_jid, "child_jid": child_jid}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "")
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"


def get_sub_groups(jid: str) -> Dict[str, Any]:
    """Get community sub-groups."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/get_sub_groups"
        payload = {"jid": jid}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "message": f"HTTP {response.status_code}: {response.text}"}
    except requests.RequestException as e:
        return {"success": False, "message": f"Request error: {str(e)}"}


# --- SQL Analytics (direct SQLite, no Go bridge needed) ---

def get_group_activity_report(chat_jid: str, days: int = 30) -> Dict[str, Any]:
    """Message count, unique senders, messages/day for a group over N days."""
    try:
        conn = sqlite3.connect(get_messages_db_path())
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total_messages,
                COUNT(DISTINCT sender) as unique_senders,
                MIN(timestamp) as first_message,
                MAX(timestamp) as last_message
            FROM messages
            WHERE chat_jid = ? AND timestamp > datetime('now', ?)
        """, (chat_jid, f"-{days} days"))
        row = cursor.fetchone()
        if not row or row[0] == 0:
            return {"success": True, "chat_jid": chat_jid, "days": days, "total_messages": 0, "unique_senders": 0, "messages_per_day": 0.0}
        total = row[0]
        return {
            "success": True,
            "chat_jid": chat_jid,
            "days": days,
            "total_messages": total,
            "unique_senders": row[1],
            "first_message": row[2],
            "last_message": row[3],
            "messages_per_day": round(total / max(days, 1), 2),
        }
    except sqlite3.Error as e:
        return {"success": False, "message": f"Database error: {e}"}
    finally:
        if 'conn' in locals():
            conn.close()


def get_member_engagement(chat_jid: str, days: int = 30) -> Dict[str, Any]:
    """Per-member stats: message count, last active, classification.

    Classification criteria: very_active (50+ msgs), active (20+), moderate (5+), inactive (<5).
    """
    try:
        conn = sqlite3.connect(get_messages_db_path())
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                sender,
                COUNT(*) as message_count,
                MAX(timestamp) as last_active
            FROM messages
            WHERE chat_jid = ? AND timestamp > datetime('now', ?)
            GROUP BY sender
            ORDER BY message_count DESC
        """, (chat_jid, f"-{days} days"))
        rows = cursor.fetchall()
        members = []
        total_messages = 0
        for row in rows:
            count = row[1]
            total_messages += count
            if count >= 50:
                classification = "very_active"
            elif count >= 20:
                classification = "active"
            elif count >= 5:
                classification = "moderate"
            else:
                classification = "inactive"
            name = get_sender_name(row[0])
            members.append({
                "sender": row[0],
                "name": name,
                "message_count": count,
                "last_active": row[2],
                "classification": classification,
            })
        return {"total_messages": total_messages, "unique_senders": len(members), "members": members}
    except sqlite3.Error as e:
        return [{"error": f"Database error: {e}"}]
    finally:
        if 'conn' in locals():
            conn.close()


def cross_group_search(query: str, chat_jid_pattern: Optional[str] = None, limit: int = 50, max_content_length: int = 200) -> List[Dict[str, Any]]:
    """Search messages across all groups or groups matching a pattern."""
    try:
        conn = sqlite3.connect(get_messages_db_path())
        cursor = conn.cursor()
        if chat_jid_pattern:
            cursor.execute("""
                SELECT m.id, m.chat_jid, c.name, m.sender, m.content, m.timestamp, m.is_from_me
                FROM messages m
                JOIN chats c ON m.chat_jid = c.jid
                WHERE LOWER(m.content) LIKE LOWER(?) AND m.chat_jid LIKE ?
                ORDER BY m.timestamp DESC
                LIMIT ?
            """, (f"%{query}%", chat_jid_pattern, limit))
        else:
            cursor.execute("""
                SELECT m.id, m.chat_jid, c.name, m.sender, m.content, m.timestamp, m.is_from_me
                FROM messages m
                JOIN chats c ON m.chat_jid = c.jid
                WHERE LOWER(m.content) LIKE LOWER(?)
                ORDER BY m.timestamp DESC
                LIMIT ?
            """, (f"%{query}%", limit))
        rows = cursor.fetchall()
        result = []
        for row in rows:
            content = row[4] or ""
            if max_content_length and len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            result.append({
                "message_id": row[0],
                "chat_jid": row[1],
                "chat_name": row[2],
                "sender": row[3],
                "content": content,
                "timestamp": row[5],
                "is_from_me": bool(row[6]),
            })
        return result
    except sqlite3.Error as e:
        return [{"error": f"Database error: {e}"}]
    finally:
        if 'conn' in locals():
            conn.close()


def get_participant_journey(jid: str, include_empty: bool = False) -> List[Dict[str, Any]]:
    """All groups + activity timeline for a contact."""
    groups = get_contact_groups(jid)
    result = []
    try:
        conn = sqlite3.connect(get_messages_db_path())
        cursor = conn.cursor()
        for group in groups:
            group_jid = group.get("jid", "")
            cursor.execute("""
                SELECT COUNT(*), MIN(timestamp), MAX(timestamp)
                FROM messages
                WHERE chat_jid = ? AND sender LIKE ?
            """, (group_jid, f"%{jid.split('@')[0] if '@' in jid else jid}%"))
            row = cursor.fetchone()
            msg_count = row[0] if row else 0
            if not include_empty and msg_count == 0:
                continue
            result.append({
                "group_jid": group_jid,
                "group_name": group.get("name", ""),
                "message_count": msg_count,
                "first_message": row[1] if row else None,
                "last_message": row[2] if row else None,
            })
        return result
    except sqlite3.Error as e:
        return [{"error": f"Database error: {e}"}]
    finally:
        if 'conn' in locals():
            conn.close()


def broadcast_to_groups(group_jids: List[str], message: str, delay_seconds: int = 3) -> List[Dict[str, Any]]:
    """Send same message to multiple groups with delay between sends."""
    results = []
    for jid in group_jids:
        success, msg = send_message(jid, message)
        results.append({"jid": jid, "success": success, "message": msg})
        if jid != group_jids[-1]:
            time.sleep(delay_seconds)
    return results


def get_group_overlap(group_jids: List[str], include_members: bool = False) -> Dict[str, Any]:
    """Compare members across 2+ groups. Returns counts by default."""
    all_participants = {}
    group_names = {}
    for jid in group_jids:
        info = get_group_info(jid, include_participants=True, participant_limit=10000)
        if info.get("success") and info.get("group"):
            group_data = info["group"]
            group_names[jid] = group_data.get("name", jid)
            members = set()
            for p in group_data.get("participants", []):
                members.add(p.get("jid", ""))
            all_participants[jid] = members
        else:
            all_participants[jid] = set()
            group_names[jid] = jid

    if not all_participants:
        return {"success": False, "message": "Could not fetch group info"}

    # Find common members (in ALL groups)
    sets = list(all_participants.values())
    common = sets[0].copy() if sets else set()
    for s in sets[1:]:
        common &= s

    # Find unique per group
    unique_per_group = {}
    for jid, members in all_participants.items():
        others = set()
        for other_jid, other_members in all_participants.items():
            if other_jid != jid:
                others |= other_members
        unique_per_group[group_names[jid]] = list(members - others) if include_members else len(members - others)

    result = {
        "success": True,
        "groups_analyzed": len(group_jids),
        "common_count": len(common),
        "unique_per_group": unique_per_group,
    }
    if include_members:
        result["common_members"] = list(common)
    return result


def get_last_interaction(jid: str) -> str:
    """Get most recent message involving the contact."""
    try:
        conn = sqlite3.connect(get_messages_db_path())
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                m.timestamp,
                m.sender,
                c.name,
                m.content,
                m.is_from_me,
                c.jid,
                m.id,
                m.media_type
            FROM messages m
            JOIN chats c ON m.chat_jid = c.jid
            WHERE m.sender = ? OR c.jid = ?
            ORDER BY m.timestamp DESC
            LIMIT 1
        """, (jid, jid))
        
        msg_data = cursor.fetchone()
        
        if not msg_data:
            return None
            
        message = Message(
            timestamp=datetime.fromisoformat(msg_data[0]),
            sender=msg_data[1],
            chat_name=msg_data[2],
            content=msg_data[3],
            is_from_me=msg_data[4],
            chat_jid=msg_data[5],
            id=msg_data[6],
            media_type=msg_data[7]
        )
        
        return format_message(message)
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()


def get_chat(chat_jid: str, include_last_message: bool = True) -> Optional[Chat]:
    """Get chat metadata by JID."""
    try:
        conn = sqlite3.connect(get_messages_db_path())
        cursor = conn.cursor()
        
        query = """
            SELECT 
                c.jid,
                c.name,
                c.last_message_time,
                m.content as last_message,
                m.sender as last_sender,
                m.is_from_me as last_is_from_me
            FROM chats c
        """
        
        if include_last_message:
            query += """
                LEFT JOIN messages m ON c.jid = m.chat_jid 
                AND c.last_message_time = m.timestamp
            """
            
        query += " WHERE c.jid = ?"
        
        cursor.execute(query, (chat_jid,))
        chat_data = cursor.fetchone()
        
        if not chat_data:
            return None
            
        return Chat(
            jid=chat_data[0],
            name=chat_data[1],
            last_message_time=datetime.fromisoformat(chat_data[2]) if chat_data[2] else None,
            last_message=chat_data[3],
            last_sender=chat_data[4],
            last_is_from_me=chat_data[5]
        )
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()


def get_direct_chat_by_contact(sender_phone_number: str) -> Optional[Chat]:
    """Get chat metadata by sender phone number."""
    try:
        conn = sqlite3.connect(get_messages_db_path())
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                c.jid,
                c.name,
                c.last_message_time,
                m.content as last_message,
                m.sender as last_sender,
                m.is_from_me as last_is_from_me
            FROM chats c
            LEFT JOIN messages m ON c.jid = m.chat_jid 
                AND c.last_message_time = m.timestamp
            WHERE c.jid LIKE ? AND c.jid NOT LIKE '%@g.us'
            LIMIT 1
        """, (f"%{sender_phone_number}%",))
        
        chat_data = cursor.fetchone()
        
        if not chat_data:
            return None
            
        return Chat(
            jid=chat_data[0],
            name=chat_data[1],
            last_message_time=datetime.fromisoformat(chat_data[2]) if chat_data[2] else None,
            last_message=chat_data[3],
            last_sender=chat_data[4],
            last_is_from_me=chat_data[5]
        )
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

def send_message(recipient: str, message: str) -> Tuple[bool, str]:
    try:
        # Validate input
        if not recipient:
            return False, "Recipient must be provided"
        
        url = f"{WHATSAPP_API_BASE_URL}/send"
        payload = {
            "recipient": recipient,
            "message": message,
        }
        
        response = requests.post(url, json=payload)
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "Unknown response")
        else:
            return False, f"Error: HTTP {response.status_code} - {response.text}"
            
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"
    except json.JSONDecodeError:
        return False, f"Error parsing response: {response.text}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def send_file(recipient: str, media_path: str) -> Tuple[bool, str]:
    try:
        # Validate input
        if not recipient:
            return False, "Recipient must be provided"
        
        if not media_path:
            return False, "Media path must be provided"
        
        if not os.path.isfile(media_path):
            return False, f"Media file not found: {media_path}"
        
        url = f"{WHATSAPP_API_BASE_URL}/send"
        payload = {
            "recipient": recipient,
            "media_path": media_path
        }
        
        response = requests.post(url, json=payload)
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "Unknown response")
        else:
            return False, f"Error: HTTP {response.status_code} - {response.text}"
            
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"
    except json.JSONDecodeError:
        return False, f"Error parsing response: {response.text}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def send_audio_message(recipient: str, media_path: str) -> Tuple[bool, str]:
    try:
        # Validate input
        if not recipient:
            return False, "Recipient must be provided"
        
        if not media_path:
            return False, "Media path must be provided"
        
        if not os.path.isfile(media_path):
            return False, f"Media file not found: {media_path}"

        if not media_path.endswith(".ogg"):
            try:
                media_path = audio.convert_to_opus_ogg_temp(media_path)
            except Exception as e:
                return False, f"Error converting file to opus ogg. You likely need to install ffmpeg: {str(e)}"
        
        url = f"{WHATSAPP_API_BASE_URL}/send"
        payload = {
            "recipient": recipient,
            "media_path": media_path
        }
        
        response = requests.post(url, json=payload)
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "Unknown response")
        else:
            return False, f"Error: HTTP {response.status_code} - {response.text}"
            
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"
    except json.JSONDecodeError:
        return False, f"Error parsing response: {response.text}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def download_media(message_id: str, chat_jid: str) -> Optional[str]:
    """Download media from a message and return the local file path.
    
    Args:
        message_id: The ID of the message containing the media
        chat_jid: The JID of the chat containing the message
    
    Returns:
        The local file path if download was successful, None otherwise
    """
    try:
        url = f"{WHATSAPP_API_BASE_URL}/download"
        payload = {
            "message_id": message_id,
            "chat_jid": chat_jid
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success", False):
                path = result.get("path")
                print(f"Media downloaded successfully: {path}")
                return path
            else:
                print(f"Download failed: {result.get('message', 'Unknown error')}")
                return None
        else:
            print(f"Error: HTTP {response.status_code} - {response.text}")
            return None
            
    except requests.RequestException as e:
        print(f"Request error: {str(e)}")
        return None
    except json.JSONDecodeError:
        print(f"Error parsing response: {response.text}")
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None


def create_group(name: str, participants: List[str]) -> Tuple[bool, str, Optional[str]]:
    """Create a new WhatsApp group."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/create_group"
        payload = {"name": name, "participants": participants}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", ""), result.get("jid")
        else:
            return False, f"Error: HTTP {response.status_code} - {response.text}", None
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}", None
    except json.JSONDecodeError:
        return False, f"Error parsing response: {response.text}", None


def join_group_with_link(invite: str) -> Tuple[bool, str, Optional[str]]:
    """Join a WhatsApp group via invite link."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/join_group"
        payload = {"invite": invite}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", ""), result.get("jid")
        else:
            return False, f"Error: HTTP {response.status_code} - {response.text}", None
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}", None
    except json.JSONDecodeError:
        return False, f"Error parsing response: {response.text}", None


def leave_group(jid: str) -> Tuple[bool, str]:
    """Leave a WhatsApp group."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/leave_group"
        payload = {"jid": jid}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "")
        else:
            return False, f"Error: HTTP {response.status_code} - {response.text}"
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"
    except json.JSONDecodeError:
        return False, f"Error parsing response: {response.text}"


def update_group_participants(jid: str, action: str, participants: List[str]) -> Tuple[bool, str]:
    """Manage participants in a WhatsApp group."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/update_group_participants"
        payload = {"jid": jid, "action": action, "participants": participants}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "")
        else:
            return False, f"Error: HTTP {response.status_code} - {response.text}"
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"
    except json.JSONDecodeError:
        return False, f"Error parsing response: {response.text}"


def set_group_name(jid: str, name: str) -> Tuple[bool, str]:
    """Set WhatsApp group name."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/set_group_name"
        payload = {"jid": jid, "name": name}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "")
        else:
            return False, f"Error: HTTP {response.status_code} - {response.text}"
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"
    except json.JSONDecodeError:
        return False, f"Error parsing response: {response.text}"


def set_group_photo(jid: str, image_path: str) -> Tuple[bool, str]:
    """Set WhatsApp group photo."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/set_group_photo"
        payload = {"jid": jid, "image_path": image_path}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "")
        else:
            return False, f"Error: HTTP {response.status_code} - {response.text}"
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"
    except json.JSONDecodeError:
        return False, f"Error parsing response: {response.text}"
