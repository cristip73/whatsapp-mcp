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


# ── 4 tools kept as-is ──────────────────────────────────────────────────────


@mcp.tool()
def search_contacts(query: str) -> List[Dict[str, Any]]:
    """Search WhatsApp contacts by name or phone number.

    Args:
        query: Search term to match against contact names or phone numbers
    """
    return whatsapp_search_contacts(query)


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
    return whatsapp_list_messages(
        after=after, before=before, sender_phone_number=sender_phone_number,
        chat_jid=chat_jid, query=query, limit=limit, page=page,
        include_context=include_context, context_before=context_before,
        context_after=context_after,
    )


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
    return whatsapp_list_chats(
        query=query, limit=limit, page=page,
        include_last_message=include_last_message, sort_by=sort_by,
    )


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
        return {"success": True, "message": "Media downloaded successfully", "url": f"file://{file_path}"}
    return {"success": False, "message": "Failed to download media"}


# ── 8 consolidated tools ────────────────────────────────────────────────────


@mcp.tool()
def get_chat_info(
    action: str,
    jid: Optional[str] = None,
    phone_number: Optional[str] = None,
    include_last_message: bool = True,
    limit: int = 20,
    page: int = 0,
) -> Any:
    """Look up chat/contact info. Pick ONE action:

    - "get_chat": Get chat metadata by JID. Requires: jid
    - "get_direct_chat": Get chat by phone number. Requires: phone_number
    - "get_contact_chats": All chats involving a contact. Requires: jid (supports limit, page)
    - "get_contact_groups": Groups shared with a contact (live data). Requires: jid
    - "get_last_interaction": Most recent message with a contact. Requires: jid
    """
    if action == "get_chat":
        if not jid:
            return {"success": False, "message": "jid required for 'get_chat'"}
        return whatsapp_get_chat(jid, include_last_message)

    if action == "get_direct_chat":
        if not phone_number:
            return {"success": False, "message": "phone_number required for 'get_direct_chat'"}
        return whatsapp_get_direct_chat_by_contact(phone_number)

    if action == "get_contact_chats":
        if not jid:
            return {"success": False, "message": "jid required for 'get_contact_chats'"}
        return whatsapp_get_contact_chats(jid, limit, page)

    if action == "get_contact_groups":
        if not jid:
            return {"success": False, "message": "jid required for 'get_contact_groups'"}
        return whatsapp_get_contact_groups(jid)

    if action == "get_last_interaction":
        if not jid:
            return {"success": False, "message": "jid required for 'get_last_interaction'"}
        return whatsapp_get_last_interaction(jid)

    return {"success": False, "message": f"Unknown action '{action}'. Valid: get_chat, get_direct_chat, get_contact_chats, get_contact_groups, get_last_interaction"}


@mcp.tool()
def send_message(
    action: str = "text",
    recipient: Optional[str] = None,
    message: Optional[str] = None,
    media_path: Optional[str] = None,
    chat_jid: Optional[str] = None,
    quoted_message_id: Optional[str] = None,
    quoted_sender_jid: Optional[str] = None,
    quoted_content: str = "",
    group_jids: Optional[List[str]] = None,
    delay_seconds: int = 3,
) -> Any:
    """Send a WhatsApp message. Pick ONE action:

    - "text" (default): Send a text message. Requires: recipient, message
    - "file": Send a file (image/video/doc). Requires: recipient, media_path
    - "audio": Send an audio voice message. Requires: recipient, media_path
    - "reply": Reply to a specific message. Requires: chat_jid, quoted_message_id, quoted_sender_jid, message
    - "broadcast": Send same message to multiple groups. Requires: group_jids, message (optional: delay_seconds)

    recipient: phone number (no + or symbols) or JID (e.g. "123@s.whatsapp.net" or group JID)
    """
    if action == "text":
        if not recipient or not message:
            return {"success": False, "message": "recipient and message required for 'text'"}
        success, msg = whatsapp_send_message(recipient, message)
        return {"success": success, "message": msg}

    if action == "file":
        if not recipient or not media_path:
            return {"success": False, "message": "recipient and media_path required for 'file'"}
        success, msg = whatsapp_send_file(recipient, media_path)
        return {"success": success, "message": msg}

    if action == "audio":
        if not recipient or not media_path:
            return {"success": False, "message": "recipient and media_path required for 'audio'"}
        success, msg = whatsapp_audio_voice_message(recipient, media_path)
        return {"success": success, "message": msg}

    if action == "reply":
        if not chat_jid or not quoted_message_id or not quoted_sender_jid or not message:
            return {"success": False, "message": "chat_jid, quoted_message_id, quoted_sender_jid, and message required for 'reply'"}
        success, msg = whatsapp_send_reply(chat_jid, quoted_message_id, quoted_sender_jid, message, quoted_content)
        return {"success": success, "message": msg}

    if action == "broadcast":
        if not group_jids or not message:
            return {"success": False, "message": "group_jids and message required for 'broadcast'"}
        return whatsapp_broadcast_to_groups(group_jids, message, delay_seconds)

    return {"success": False, "message": f"Unknown action '{action}'. Valid: text, file, audio, reply, broadcast"}


@mcp.tool()
def message_action(
    action: str,
    chat_jid: str,
    message_id: Optional[str] = None,
    message_ids: Optional[List[str]] = None,
    sender_jid: Optional[str] = None,
    reaction: Optional[str] = None,
    new_text: Optional[str] = None,
    question: Optional[str] = None,
    options: Optional[List[str]] = None,
    max_selections: int = 1,
) -> Dict[str, Any]:
    """Act on existing messages in a chat. Pick ONE action:

    - "react": React with emoji. Requires: chat_jid, sender_jid, message_id, reaction (empty string to remove)
    - "edit": Edit a sent message. Requires: chat_jid, message_id, new_text
    - "delete": Delete/revoke a message. Requires: chat_jid, sender_jid, message_id
    - "mark_read": Mark messages as read. Requires: chat_jid, sender_jid, message_ids (list)
    - "poll": Create a poll. Requires: chat_jid, question, options (optional: max_selections)
    """
    if action == "react":
        if not sender_jid or not message_id or reaction is None:
            return {"success": False, "message": "sender_jid, message_id, and reaction required for 'react'"}
        success, msg = whatsapp_send_reaction(chat_jid, sender_jid, message_id, reaction)
        return {"success": success, "message": msg}

    if action == "edit":
        if not message_id or not new_text:
            return {"success": False, "message": "message_id and new_text required for 'edit'"}
        success, msg = whatsapp_edit_message(chat_jid, message_id, new_text)
        return {"success": success, "message": msg}

    if action == "delete":
        if not sender_jid or not message_id:
            return {"success": False, "message": "sender_jid and message_id required for 'delete'"}
        success, msg = whatsapp_delete_message(chat_jid, sender_jid, message_id)
        return {"success": success, "message": msg}

    if action == "mark_read":
        if not sender_jid or not message_ids:
            return {"success": False, "message": "sender_jid and message_ids required for 'mark_read'"}
        success, msg = whatsapp_mark_read(chat_jid, sender_jid, message_ids)
        return {"success": success, "message": msg}

    if action == "poll":
        if not question or not options:
            return {"success": False, "message": "question and options required for 'poll'"}
        success, msg = whatsapp_create_poll(chat_jid, question, options, max_selections)
        return {"success": success, "message": msg}

    return {"success": False, "message": f"Unknown action '{action}'. Valid: react, edit, delete, mark_read, poll"}


@mcp.tool()
def manage_group(
    action: str,
    jid: Optional[str] = None,
    name: Optional[str] = None,
    participants: Optional[List[str]] = None,
    participant_action: Optional[str] = None,
    topic: Optional[str] = None,
    image_path: Optional[str] = None,
    invite_link: Optional[str] = None,
    reset_invite: bool = False,
    announce: Optional[bool] = None,
    locked: Optional[bool] = None,
    join_approval: Optional[bool] = None,
    include_participants: bool = False,
    participant_limit: int = 50,
    participant_offset: int = 0,
) -> Dict[str, Any]:
    """Manage WhatsApp groups. Pick ONE action:

    - "create": Create a new group. Requires: name, participants
    - "join": Join via invite link. Requires: invite_link
    - "leave": Leave a group. Requires: jid
    - "get_info": Get group metadata. Requires: jid (optional: include_participants, participant_limit, participant_offset)
    - "get_invite_link": Get/reset invite link. Requires: jid (optional: reset_invite)
    - "update_participants": Add/remove/promote/demote members. Requires: jid, participant_action (add|remove|promote|demote), participants
    - "set_name": Rename group. Requires: jid, name
    - "set_topic": Set group description. Requires: jid, topic
    - "set_photo": Update group photo. Requires: jid, image_path
    - "set_announce": Toggle admin-only messaging. Requires: jid, announce (bool)
    - "set_locked": Toggle admin-only info editing. Requires: jid, locked (bool)
    - "set_join_approval": Toggle join approval. Requires: jid, join_approval (bool)
    """
    if action == "create":
        if not name or not participants:
            return {"success": False, "message": "name and participants required for 'create'"}
        success, msg, group_jid = whatsapp_create_group(name, participants)
        return {"success": success, "message": msg, "jid": group_jid}

    if action == "join":
        if not invite_link:
            return {"success": False, "message": "invite_link required for 'join'"}
        success, msg, group_jid = whatsapp_join_group_with_link(invite_link)
        return {"success": success, "message": msg, "jid": group_jid}

    if action == "leave":
        if not jid:
            return {"success": False, "message": "jid required for 'leave'"}
        success, msg = whatsapp_leave_group(jid)
        return {"success": success, "message": msg}

    if action == "get_info":
        if not jid:
            return {"success": False, "message": "jid required for 'get_info'"}
        return whatsapp_get_group_info(jid, include_participants, participant_limit, participant_offset)

    if action == "get_invite_link":
        if not jid:
            return {"success": False, "message": "jid required for 'get_invite_link'"}
        success, msg, link = whatsapp_get_group_invite_link(jid, reset_invite)
        return {"success": success, "message": msg, "link": link}

    if action == "update_participants":
        if not jid or not participant_action or not participants:
            return {"success": False, "message": "jid, participant_action, and participants required for 'update_participants'"}
        success, msg = whatsapp_update_group_participants(jid, participant_action, participants)
        return {"success": success, "message": msg}

    if action == "set_name":
        if not jid or not name:
            return {"success": False, "message": "jid and name required for 'set_name'"}
        success, msg = whatsapp_set_group_name(jid, name)
        return {"success": success, "message": msg}

    if action == "set_topic":
        if not jid or not topic:
            return {"success": False, "message": "jid and topic required for 'set_topic'"}
        success, msg = whatsapp_set_group_topic(jid, topic)
        return {"success": success, "message": msg, "topic": topic}

    if action == "set_photo":
        if not jid or not image_path:
            return {"success": False, "message": "jid and image_path required for 'set_photo'"}
        success, msg = whatsapp_set_group_photo(jid, image_path)
        return {"success": success, "message": msg}

    if action == "set_announce":
        if not jid or announce is None:
            return {"success": False, "message": "jid and announce required for 'set_announce'"}
        success, msg = whatsapp_set_group_announce(jid, announce)
        return {"success": success, "message": msg, "announce": announce}

    if action == "set_locked":
        if not jid or locked is None:
            return {"success": False, "message": "jid and locked required for 'set_locked'"}
        success, msg = whatsapp_set_group_locked(jid, locked)
        return {"success": success, "message": msg, "locked": locked}

    if action == "set_join_approval":
        if not jid or join_approval is None:
            return {"success": False, "message": "jid and join_approval required for 'set_join_approval'"}
        success, msg = whatsapp_set_group_join_approval(jid, join_approval)
        return {"success": success, "message": msg, "join_approval": join_approval}

    return {"success": False, "message": f"Unknown action '{action}'. Valid: create, join, leave, get_info, get_invite_link, update_participants, set_name, set_topic, set_photo, set_announce, set_locked, set_join_approval"}


@mcp.tool()
def search_messages(
    action: str,
    message_id: Optional[str] = None,
    query: Optional[str] = None,
    chat_jid_pattern: Optional[str] = None,
    before: int = 5,
    after: int = 5,
    limit: int = 50,
    max_content_length: int = 200,
) -> Any:
    """Search or get context around WhatsApp messages. Pick ONE action:

    - "context": Get messages around a specific message. Requires: message_id (optional: before, after)
    - "cross_group": Search messages across all groups. Requires: query (optional: chat_jid_pattern, limit, max_content_length)
    """
    if action == "context":
        if not message_id:
            return {"success": False, "message": "message_id required for 'context'"}
        return whatsapp_get_message_context(message_id, before, after)

    if action == "cross_group":
        if not query:
            return {"success": False, "message": "query required for 'cross_group'"}
        return whatsapp_cross_group_search(query, chat_jid_pattern, limit, max_content_length)

    return {"success": False, "message": f"Unknown action '{action}'. Valid: context, cross_group"}


@mcp.tool()
def analytics(
    action: str,
    chat_jid: Optional[str] = None,
    jid: Optional[str] = None,
    group_jids: Optional[List[str]] = None,
    days: int = 30,
    include_empty: bool = False,
    include_members: bool = False,
) -> Any:
    """WhatsApp analytics and engagement data. Pick ONE action:

    - "group_activity": Activity report for a group over N days. Requires: chat_jid (optional: days)
    - "member_engagement": Per-member engagement stats. Requires: chat_jid (optional: days)
    - "participant_journey": All groups and activity timeline for a contact. Requires: jid (optional: include_empty)
    - "group_overlap": Compare members across groups. Requires: group_jids (list, at least 2) (optional: include_members)
    """
    if action == "group_activity":
        if not chat_jid:
            return {"success": False, "message": "chat_jid required for 'group_activity'"}
        return whatsapp_get_group_activity_report(chat_jid, days)

    if action == "member_engagement":
        if not chat_jid:
            return {"success": False, "message": "chat_jid required for 'member_engagement'"}
        return whatsapp_get_member_engagement(chat_jid, days)

    if action == "participant_journey":
        if not jid:
            return {"success": False, "message": "jid required for 'participant_journey'"}
        return whatsapp_get_participant_journey(jid, include_empty)

    if action == "group_overlap":
        if not group_jids:
            return {"success": False, "message": "group_jids required for 'group_overlap'"}
        return whatsapp_get_group_overlap(group_jids, include_members)

    return {"success": False, "message": f"Unknown action '{action}'. Valid: group_activity, member_engagement, participant_journey, group_overlap"}


@mcp.tool()
def manage_profile(
    action: str,
    presence: Optional[str] = None,
    message: Optional[str] = None,
    phones: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Manage your WhatsApp profile and presence. Pick ONE action:

    - "set_presence": Set online/offline. Requires: presence ("available" or "unavailable")
    - "set_about": Change About text. Requires: message (max 139 chars)
    - "post_status": Post to Status/stories (24h). Requires: message
    - "check_registration": Check if phone numbers are on WhatsApp. Requires: phones (list with country code, e.g. ["+40730883388"])
    """
    if action == "set_presence":
        if not presence:
            return {"success": False, "message": "presence required for 'set_presence'"}
        if presence not in ("available", "unavailable"):
            return {"success": False, "message": f"Invalid presence '{presence}'. Must be 'available' or 'unavailable'."}
        success, msg = whatsapp_send_presence(presence)
        return {"success": success, "message": msg}

    if action == "set_about":
        if not message:
            return {"success": False, "message": "message required for 'set_about'"}
        success, msg = whatsapp_set_status_message(message)
        return {"success": success, "message": msg}

    if action == "post_status":
        if not message:
            return {"success": False, "message": "message required for 'post_status'"}
        success, msg = whatsapp_send_status(message)
        return {"success": success, "message": msg}

    if action == "check_registration":
        if not phones:
            return {"success": False, "message": "phones required for 'check_registration'"}
        return whatsapp_is_on_whatsapp(phones)

    return {"success": False, "message": f"Unknown action '{action}'. Valid: set_presence, set_about, post_status, check_registration"}


@mcp.tool()
def manage_channel(
    action: str,
    jid: Optional[str] = None,
    name: Optional[str] = None,
    description: str = "",
    message: Optional[str] = None,
    parent_jid: Optional[str] = None,
    child_jid: Optional[str] = None,
) -> Any:
    """Manage WhatsApp channels/newsletters and community groups. Pick ONE action:

    - "create_newsletter": Create a channel. Requires: name (optional: description)
    - "list_newsletters": List subscribed channels. No extra params.
    - "send_newsletter": Send to a channel. Requires: jid, message
    - "link_group": Link a group to a community. Requires: parent_jid, child_jid
    - "unlink_group": Unlink a group from a community. Requires: parent_jid, child_jid
    - "get_sub_groups": Get community sub-groups. Requires: jid
    """
    if action == "create_newsletter":
        if not name:
            return {"success": False, "message": "name required for 'create_newsletter'"}
        return whatsapp_create_newsletter(name, description)

    if action == "list_newsletters":
        return whatsapp_get_newsletters()

    if action == "send_newsletter":
        if not jid or not message:
            return {"success": False, "message": "jid and message required for 'send_newsletter'"}
        success, msg = whatsapp_newsletter_send(jid, message)
        return {"success": success, "message": msg}

    if action == "link_group":
        if not parent_jid or not child_jid:
            return {"success": False, "message": "parent_jid and child_jid required for 'link_group'"}
        success, msg = whatsapp_link_group(parent_jid, child_jid)
        return {"success": success, "message": msg}

    if action == "unlink_group":
        if not parent_jid or not child_jid:
            return {"success": False, "message": "parent_jid and child_jid required for 'unlink_group'"}
        success, msg = whatsapp_unlink_group(parent_jid, child_jid)
        return {"success": success, "message": msg}

    if action == "get_sub_groups":
        if not jid:
            return {"success": False, "message": "jid required for 'get_sub_groups'"}
        return whatsapp_get_sub_groups(jid)

    return {"success": False, "message": f"Unknown action '{action}'. Valid: create_newsletter, list_newsletters, send_newsletter, link_group, unlink_group, get_sub_groups"}


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
