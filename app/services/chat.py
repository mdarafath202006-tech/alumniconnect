"""
app/services/chat.py – Real-time chat via Socket.IO.

Features:
  • Room-based messaging (student ↔ alumni per mentorship pair)
  • Online presence tracking
  • Message broadcast within room
"""
from flask import session
from flask_socketio import join_room, leave_room, emit

# In-memory online users {user_id: name}
_online = {}


def register_socket_events(socketio):

    @socketio.on("connect")
    def handle_connect():
        uid = session.get("user_id")
        if uid:
            _online[uid] = session.get("name", "User")
            emit("online_users", list(_online.values()), broadcast=True)

    @socketio.on("disconnect")
    def handle_disconnect():
        uid = session.get("user_id")
        if uid and uid in _online:
            del _online[uid]
            emit("online_users", list(_online.values()), broadcast=True)

    @socketio.on("join_room")
    def handle_join(data):
        room = str(data.get("room", ""))
        if room:
            join_room(room)
            emit("system_message", {
                "text": f"{session.get('name', 'Someone')} joined the chat."
            }, to=room)

    @socketio.on("leave_room")
    def handle_leave(data):
        room = str(data.get("room", ""))
        if room:
            leave_room(room)

    @socketio.on("send_message")
    def handle_message(data):
        room    = str(data.get("room", ""))
        message = str(data.get("message", "")).strip()[:500]
        if room and message:
            emit("receive_message", {
                "sender":  session.get("name", "Unknown"),
                "role":    session.get("role", ""),
                "message": message,
            }, to=room)
