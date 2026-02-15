import argparse
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
import whatsapp # Added import
from whatsapp import (
    search_contacts as whatsapp_search_contacts,
    list_messages as whatsapp_list_messages,
    list_chats as whatsapp_list_chats,
    get_chat as whatsapp_get_chat,
    get_direct_chat_by_contact as whatsapp_get_direct_chat_by_contact,
    get_contact_chats as whatsapp_get_contact_chats,
    get_contact_groups as whatsapp_get_contact_groups,
    get_last_interaction as whatsapp_get_last_interaction,
    get_message_context as whatsapp_get_message_context,
    send_message as whatsapp_send_message,
    send_file as whatsapp_send_file,
    send_audio_message as whatsapp_audio_voice_message,
    download_media as whatsapp_download_media,
    create_group as whatsapp_create_group,
    join_group_with_link as whatsapp_join_group_with_link,
    leave_group as whatsapp_leave_group,
    update_group_participants as whatsapp_update_group_participants,
    set_group_name as whatsapp_set_group_name,
    set_group_photo as whatsapp_set_group_photo,
    get_group_info as whatsapp_get_group_info,
    get_group_invite_link as whatsapp_get_group_invite_link,
    set_group_topic as whatsapp_set_group_topic,
    set_group_announce as whatsapp_set_group_announce,
    set_group_locked as whatsapp_set_group_locked,
    set_group_join_approval as whatsapp_set_group_join_approval,
    is_on_whatsapp as whatsapp_is_on_whatsapp,
    send_reaction as whatsapp_send_reaction,
    edit_message as whatsapp_edit_message,
    delete_message as whatsapp_delete_message,
    mark_read as whatsapp_mark_read,
    create_poll as whatsapp_create_poll,
    send_reply as whatsapp_send_reply,
    send_presence as whatsapp_send_presence,
    set_status_message as whatsapp_set_status_message,
    create_newsletter as whatsapp_create_newsletter,
    get_newsletters as whatsapp_get_newsletters,
    newsletter_send as whatsapp_newsletter_send,
    send_status as whatsapp_send_status,
    link_group as whatsapp_link_group,
    unlink_group as whatsapp_unlink_group,
    get_sub_groups as whatsapp_get_sub_groups,
    get_group_activity_report as whatsapp_get_group_activity_report,
    get_member_engagement as whatsapp_get_member_engagement,
    cross_group_search as whatsapp_cross_group_search,
    get_participant_journey as whatsapp_get_participant_journey,
    broadcast_to_groups as whatsapp_broadcast_to_groups,
    get_group_overlap as whatsapp_get_group_overlap,
)

# Initialize FastMCP server
mcp = FastMCP("whatsapp")

@mcp.tool()
def search_contacts(query: str) -> List[Dict[str, Any]]:
    """Search WhatsApp contacts by name or phone number.
    
    Args:
        query: Search term to match against contact names or phone numbers
    """
    contacts = whatsapp_search_contacts(query)
    return contacts

@mcp.tool()
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
) -> List[Dict[str, Any]]:
    """Get WhatsApp messages matching specified criteria with optional context.
    
    Args:
        after: Optional ISO-8601 formatted string to only return messages after this date
        before: Optional ISO-8601 formatted string to only return messages before this date
        sender_phone_number: Optional phone number to filter messages by sender
        chat_jid: Optional chat JID to filter messages by chat
        query: Optional search term to filter messages by content
        limit: Maximum number of messages to return (default 20)
        page: Page number for pagination (default 0)
        include_context: Whether to include messages before and after matches (default True)
        context_before: Number of messages to include before each match (default 1)
        context_after: Number of messages to include after each match (default 1)
    """
    messages = whatsapp_list_messages(
        after=after,
        before=before,
        sender_phone_number=sender_phone_number,
        chat_jid=chat_jid,
        query=query,
        limit=limit,
        page=page,
        include_context=include_context,
        context_before=context_before,
        context_after=context_after
    )
    return messages

@mcp.tool()
def list_chats(
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_last_message: bool = True,
    sort_by: str = "last_active"
) -> List[Dict[str, Any]]:
    """Get WhatsApp chats matching specified criteria.
    
    Args:
        query: Optional search term to filter chats by name or JID
        limit: Maximum number of chats to return (default 20)
        page: Page number for pagination (default 0)
        include_last_message: Whether to include the last message in each chat (default True)
        sort_by: Field to sort results by, either "last_active" or "name" (default "last_active")
    """
    chats = whatsapp_list_chats(
        query=query,
        limit=limit,
        page=page,
        include_last_message=include_last_message,
        sort_by=sort_by
    )
    return chats

@mcp.tool()
def get_chat(chat_jid: str, include_last_message: bool = True) -> Dict[str, Any]:
    """Get WhatsApp chat metadata by JID.
    
    Args:
        chat_jid: The JID of the chat to retrieve
        include_last_message: Whether to include the last message (default True)
    """
    chat = whatsapp_get_chat(chat_jid, include_last_message)
    return chat

@mcp.tool()
def get_direct_chat_by_contact(sender_phone_number: str) -> Dict[str, Any]:
    """Get WhatsApp chat metadata by sender phone number.
    
    Args:
        sender_phone_number: The phone number to search for
    """
    chat = whatsapp_get_direct_chat_by_contact(sender_phone_number)
    return chat

@mcp.tool()
def get_contact_chats(jid: str, limit: int = 20, page: int = 0) -> List[Dict[str, Any]]:
    """Get all WhatsApp chats involving the contact.
    
    Args:
        jid: The contact's JID to search for
        limit: Maximum number of chats to return (default 20)
        page: Page number for pagination (default 0)
    """
    chats = whatsapp_get_contact_chats(jid, limit, page)
    return chats

@mcp.tool()
def get_contact_groups(jid: str) -> List[Dict[str, Any]]:
    """Get all WhatsApp groups where both you and the contact are members.
    Uses live WhatsApp data (not just message history) so finds ALL common groups.

    Args:
        jid: The contact's JID to search for
    """
    groups = whatsapp_get_contact_groups(jid)
    return groups

@mcp.tool()
def get_last_interaction(jid: str) -> str:
    """Get most recent WhatsApp message involving the contact.

    Args:
        jid: The JID of the contact to search for
    """
    message = whatsapp_get_last_interaction(jid)
    return message

@mcp.tool()
def get_message_context(
    message_id: str,
    before: int = 5,
    after: int = 5
) -> Dict[str, Any]:
    """Get context around a specific WhatsApp message.
    
    Args:
        message_id: The ID of the message to get context for
        before: Number of messages to include before the target message (default 5)
        after: Number of messages to include after the target message (default 5)
    """
    context = whatsapp_get_message_context(message_id, before, after)
    return context

@mcp.tool()
def send_message(
    recipient: str,
    message: str
) -> Dict[str, Any]:
    """Send a WhatsApp message to a person or group. For group chats use the JID.

    Args:
        recipient: The recipient - either a phone number with country code but no + or other symbols,
                 or a JID (e.g., "123456789@s.whatsapp.net" or a group JID like "123456789@g.us")
        message: The message text to send
    
    Returns:
        A dictionary containing success status and a status message
    """
    # Validate input
    if not recipient:
        return {
            "success": False,
            "message": "Recipient must be provided"
        }
    
    # Call the whatsapp_send_message function with the unified recipient parameter
    success, status_message = whatsapp_send_message(recipient, message)
    return {
        "success": success,
        "message": status_message
    }

@mcp.tool()
def send_file(recipient: str, media_path: str) -> Dict[str, Any]:
    """Send a file such as a picture, raw audio, video or document via WhatsApp to the specified recipient. For group messages use the JID.
    
    Args:
        recipient: The recipient - either a phone number with country code but no + or other symbols,
                 or a JID (e.g., "123456789@s.whatsapp.net" or a group JID like "123456789@g.us")
        media_path: The absolute path to the media file to send (image, video, document)
    
    Returns:
        A dictionary containing success status and a status message
    """
    
    # Call the whatsapp_send_file function
    success, status_message = whatsapp_send_file(recipient, media_path)
    return {
        "success": success,
        "message": status_message
    }

@mcp.tool()
def send_audio_message(recipient: str, media_path: str) -> Dict[str, Any]:
    """Send any audio file as a WhatsApp audio message to the specified recipient. For group messages use the JID. If it errors due to ffmpeg not being installed, use send_file instead.
    
    Args:
        recipient: The recipient - either a phone number with country code but no + or other symbols,
                 or a JID (e.g., "123456789@s.whatsapp.net" or a group JID like "123456789@g.us")
        media_path: The absolute path to the audio file to send (will be converted to Opus .ogg if it's not a .ogg file)
    
    Returns:
        A dictionary containing success status and a status message
    """
    success, status_message = whatsapp_audio_voice_message(recipient, media_path)
    return {
        "success": success,
        "message": status_message
    }

@mcp.tool()
def download_media(message_id: str, chat_jid: str) -> Dict[str, Any]:
    """Download media from a WhatsApp message and get the local file path.
    
    Args:
        message_id: The ID of the message containing the media
        chat_jid: The JID of the chat containing the message
    
    Returns:
        A dictionary containing success status, a status message, and the file URL with file:// prefix
    """
    file_path = whatsapp_download_media(message_id, chat_jid)
    
    if file_path:
        # Adaugă prefixul file:// la calea fișierului
        file_url = f"file://{file_path}"
        return {
            "success": True,
            "message": "Media downloaded successfully",
            "url": file_url
        }
    else:
        return {
            "success": False,
            "message": "Failed to download media"
        }


@mcp.tool()
def create_group(name: str, participants: List[str]) -> Dict[str, Any]:
    """Create a new WhatsApp group."""
    success, message, jid = whatsapp_create_group(name, participants)
    return {"success": success, "message": message, "jid": jid}


@mcp.tool()
def join_group_with_link(invite: str) -> Dict[str, Any]:
    """Join a WhatsApp group using an invite link."""
    success, message, jid = whatsapp_join_group_with_link(invite)
    return {"success": success, "message": message, "jid": jid}


@mcp.tool()
def leave_group(jid: str) -> Dict[str, Any]:
    """Leave a WhatsApp group."""
    success, message = whatsapp_leave_group(jid)
    return {"success": success, "message": message}


@mcp.tool()
def update_group_participants(jid: str, action: str, participants: List[str]) -> Dict[str, Any]:
    """Add, remove, promote or demote participants in a WhatsApp group."""
    success, message = whatsapp_update_group_participants(jid, action, participants)
    return {"success": success, "message": message}


@mcp.tool()
def set_group_name(jid: str, name: str) -> Dict[str, Any]:
    """Change a WhatsApp group's name."""
    success, message = whatsapp_set_group_name(jid, name)
    return {"success": success, "message": message}


@mcp.tool()
def set_group_photo(jid: str, image_path: str) -> Dict[str, Any]:
    """Update the group's photo."""
    success, message = whatsapp_set_group_photo(jid, image_path)
    return {"success": success, "message": message}


# --- Extended Group Management Tools ---

@mcp.tool()
def get_group_info(jid: str, include_participants: bool = False, participant_limit: int = 50, participant_offset: int = 0) -> Dict[str, Any]:
    """Get WhatsApp group metadata including participant list.

    Args:
        jid: The group JID (e.g., "120363XXX@g.us")
        include_participants: Whether to include the participant list (default False). Metadata (name, topic, settings, participant_count) is always returned.
        participant_limit: Max participants to return when include_participants=True (default 50)
        participant_offset: Offset for participant pagination (default 0)
    """
    return whatsapp_get_group_info(jid, include_participants, participant_limit, participant_offset)


@mcp.tool()
def get_group_invite_link(jid: str, reset: bool = False) -> Dict[str, Any]:
    """Get or reset a WhatsApp group invite link.

    Args:
        jid: The group JID
        reset: Whether to reset the invite link (default False). WARNING: reset=true invalidates the previous invite link permanently.
    """
    success, message, link = whatsapp_get_group_invite_link(jid, reset)
    return {"success": success, "message": message, "link": link}


@mcp.tool()
def set_group_topic(jid: str, topic: str) -> Dict[str, Any]:
    """Set a WhatsApp group's description/topic.

    Args:
        jid: The group JID
        topic: The new group description
    """
    success, message = whatsapp_set_group_topic(jid, topic)
    return {"success": success, "message": message, "topic": topic}


@mcp.tool()
def set_group_announce(jid: str, announce: bool) -> Dict[str, Any]:
    """Toggle admin-only messaging for a WhatsApp group.

    Args:
        jid: The group JID
        announce: True for admin-only messaging, False to allow all members
    """
    success, message = whatsapp_set_group_announce(jid, announce)
    return {"success": success, "message": message, "announce": announce}


@mcp.tool()
def set_group_locked(jid: str, locked: bool) -> Dict[str, Any]:
    """Toggle admin-only group info editing.

    Args:
        jid: The group JID
        locked: True for admin-only editing, False for all members
    """
    success, message = whatsapp_set_group_locked(jid, locked)
    return {"success": success, "message": message, "locked": locked}


@mcp.tool()
def set_group_join_approval(jid: str, mode: bool) -> Dict[str, Any]:
    """Toggle join approval mode for a WhatsApp group.

    Args:
        jid: The group JID
        mode: True to require admin approval for new members
    """
    success, message = whatsapp_set_group_join_approval(jid, mode)
    return {"success": success, "message": message, "mode": mode}


@mcp.tool()
def is_on_whatsapp(phones: List[str]) -> Dict[str, Any]:
    """Check if phone numbers are registered on WhatsApp.

    Args:
        phones: List of phone numbers with country code (e.g., ["+40730883388"])
    """
    return whatsapp_is_on_whatsapp(phones)


# --- Message Operation Tools ---

@mcp.tool()
def send_reaction(chat_jid: str, sender_jid: str, message_id: str, reaction: str) -> Dict[str, Any]:
    """React to a WhatsApp message with an emoji.

    Args:
        chat_jid: The chat JID containing the message
        sender_jid: JID of who sent the original message (use "me" for own messages)
        message_id: The ID of the message to react to
        reaction: The emoji reaction (empty string to remove reaction)
    """
    success, message = whatsapp_send_reaction(chat_jid, sender_jid, message_id, reaction)
    return {"success": success, "message": message}


@mcp.tool()
def edit_message(chat_jid: str, message_id: str, new_text: str) -> Dict[str, Any]:
    """Edit a previously sent WhatsApp message.

    Args:
        chat_jid: The chat JID containing the message
        message_id: The ID of the message to edit
        new_text: The new message text
    """
    success, message = whatsapp_edit_message(chat_jid, message_id, new_text)
    return {"success": success, "message": message}


@mcp.tool()
def delete_message(chat_jid: str, sender_jid: str, message_id: str) -> Dict[str, Any]:
    """Delete/revoke a WhatsApp message.

    Args:
        chat_jid: The chat JID containing the message
        sender_jid: JID of who sent the message (use "me" for own messages)
        message_id: The ID of the message to delete
    """
    success, message = whatsapp_delete_message(chat_jid, sender_jid, message_id)
    return {"success": success, "message": message}


@mcp.tool()
def mark_read(chat_jid: str, sender_jid: str, message_ids: List[str]) -> Dict[str, Any]:
    """Mark WhatsApp messages as read.

    Args:
        chat_jid: The chat JID containing the messages
        sender_jid: JID of who sent the messages
        message_ids: List of message IDs to mark as read
    """
    success, message = whatsapp_mark_read(chat_jid, sender_jid, message_ids)
    return {"success": success, "message": message}


@mcp.tool()
def create_poll(chat_jid: str, question: str, options: List[str], max_selections: int = 1) -> Dict[str, Any]:
    """Create a WhatsApp poll in a chat.

    Args:
        chat_jid: The chat JID to create the poll in
        question: The poll question
        options: List of poll options (at least 2)
        max_selections: Maximum number of options a user can select (default 1)
    """
    success, message = whatsapp_create_poll(chat_jid, question, options, max_selections)
    return {"success": success, "message": message}


@mcp.tool()
def send_reply(chat_jid: str, quoted_message_id: str, quoted_sender_jid: str, message: str, quoted_content: str = "") -> Dict[str, Any]:
    """Reply to a specific WhatsApp message.

    Args:
        chat_jid: The chat JID
        quoted_message_id: The ID of the message to reply to
        quoted_sender_jid: JID of who sent the quoted message
        message: The reply text
        quoted_content: The original message content (for display)
    """
    success, msg = whatsapp_send_reply(chat_jid, quoted_message_id, quoted_sender_jid, message, quoted_content)
    return {"success": success, "message": msg}


# --- Presence & Status Tools ---

@mcp.tool()
def send_presence(presence: str) -> Dict[str, Any]:
    """Set WhatsApp online/offline presence.

    Args:
        presence: Either "available" or "unavailable"
    """
    if presence not in ("available", "unavailable"):
        return {"success": False, "message": f"Invalid presence '{presence}'. Must be 'available' or 'unavailable'."}
    success, message = whatsapp_send_presence(presence)
    return {"success": success, "message": message}


@mcp.tool()
def set_status_message(message: str) -> Dict[str, Any]:
    """Change the WhatsApp 'About' status text.

    Args:
        message: The new status message (max 139 characters per WhatsApp limit)
    """
    success, msg = whatsapp_set_status_message(message)
    return {"success": success, "message": msg}


@mcp.tool()
def send_status(message: str) -> Dict[str, Any]:
    """Post a text message to WhatsApp Status (stories, visible for 24h).

    Args:
        message: The status message text
    """
    success, msg = whatsapp_send_status(message)
    return {"success": success, "message": msg}


# --- Newsletter Tools ---

@mcp.tool()
def create_newsletter(name: str, description: str = "") -> Dict[str, Any]:
    """Create a new WhatsApp Channel/Newsletter.

    Args:
        name: The channel name
        description: Optional channel description
    """
    return whatsapp_create_newsletter(name, description)


@mcp.tool()
def get_newsletters() -> Dict[str, Any]:
    """List all subscribed WhatsApp newsletters/channels."""
    return whatsapp_get_newsletters()


@mcp.tool()
def newsletter_send(jid: str, message: str) -> Dict[str, Any]:
    """Send a message to a WhatsApp newsletter channel.

    Args:
        jid: The newsletter JID
        message: The message text
    """
    success, msg = whatsapp_newsletter_send(jid, message)
    return {"success": success, "message": msg}


# --- Community Tools ---

@mcp.tool()
def link_group(parent_jid: str, child_jid: str) -> Dict[str, Any]:
    """Link a group to a WhatsApp community. WARNING: This modifies community structure.

    Args:
        parent_jid: The community JID
        child_jid: The group JID to link
    """
    success, message = whatsapp_link_group(parent_jid, child_jid)
    return {"success": success, "message": message}


@mcp.tool()
def unlink_group(parent_jid: str, child_jid: str) -> Dict[str, Any]:
    """Unlink a group from a WhatsApp community. WARNING: This modifies community structure.

    Args:
        parent_jid: The community JID
        child_jid: The group JID to unlink
    """
    success, message = whatsapp_unlink_group(parent_jid, child_jid)
    return {"success": success, "message": message}


@mcp.tool()
def get_sub_groups(jid: str) -> Dict[str, Any]:
    """Get all sub-groups of a WhatsApp community.

    Args:
        jid: The community JID
    """
    return whatsapp_get_sub_groups(jid)


# --- Analytics Tools (SQL-based, no Go bridge needed) ---

@mcp.tool()
def get_group_activity_report(chat_jid: str, days: int = 30) -> Dict[str, Any]:
    """Get activity report for a WhatsApp group over N days.

    Args:
        chat_jid: The group JID to analyze
        days: Number of days to look back (default 30)
    """
    return whatsapp_get_group_activity_report(chat_jid, days)


@mcp.tool()
def get_member_engagement(chat_jid: str, days: int = 30) -> Dict[str, Any]:
    """Get per-member engagement stats for a WhatsApp group.

    Args:
        chat_jid: The group JID to analyze
        days: Number of days to look back (default 30)

    Classification: very_active (50+ msgs), active (20+), moderate (5+), inactive (<5).
    Returns total_messages, unique_senders, and per-member breakdown.
    """
    return whatsapp_get_member_engagement(chat_jid, days)


@mcp.tool()
def cross_group_search(query: str, chat_jid_pattern: Optional[str] = None, limit: int = 50, max_content_length: int = 200) -> List[Dict[str, Any]]:
    """Search messages across all WhatsApp groups.

    Args:
        query: Search term to find in message content
        chat_jid_pattern: Optional SQL LIKE pattern to filter groups (e.g., "%@g.us")
        limit: Maximum results (default 50)
        max_content_length: Truncate message content to this length (default 200). Set to 0 for full content.
    """
    return whatsapp_cross_group_search(query, chat_jid_pattern, limit, max_content_length)


@mcp.tool()
def get_participant_journey(jid: str, include_empty: bool = False) -> List[Dict[str, Any]]:
    """Get all groups and activity timeline for a WhatsApp contact.

    Args:
        jid: The contact's JID or phone number
        include_empty: Include groups where contact has 0 messages (default False)
    """
    return whatsapp_get_participant_journey(jid, include_empty)


@mcp.tool()
def broadcast_to_groups(group_jids: List[str], message: str, delay_seconds: int = 3) -> List[Dict[str, Any]]:
    """Send the same message to multiple WhatsApp groups with delay between sends.
    WARNING: This sends real messages to all specified groups. Use with caution.

    Args:
        group_jids: List of group JIDs to send to
        message: The message text to broadcast
        delay_seconds: Seconds to wait between sends (default 3)
    """
    return whatsapp_broadcast_to_groups(group_jids, message, delay_seconds)


@mcp.tool()
def get_group_overlap(group_jids: List[str], include_members: bool = False) -> Dict[str, Any]:
    """Compare members across multiple WhatsApp groups.

    Args:
        group_jids: List of group JIDs to compare (at least 2)
        include_members: Whether to include full member lists (default False). When False, returns only counts.
    """
    return whatsapp_get_group_overlap(group_jids, include_members)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WhatsApp MCP Server")
    parser.add_argument(
        '--attachments-path',
        type=str,
        required=True,
        help='Absolute path for storing attachments and the message database.'
    )
    args = parser.parse_args()

    # Initialize the attachments path in the whatsapp module
    whatsapp.initialize_attachments_path(args.attachments_path)

    # Initialize and run the server
    mcp.run(transport='stdio')
