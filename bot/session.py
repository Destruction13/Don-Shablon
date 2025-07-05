from dataclasses import dataclass, field

@dataclass
class Session:
    theme: str | None = None
    my_room: str | None = None
    awaiting_my_room: bool = False
    meeting_link: str | None = None
    awaiting_link: bool = False
    auto_enabled: bool = False
    awaiting_auto_login: bool = False
    awaiting_auto_tg: bool = False
    organizer_login: str | None = None
    organizer_tg: str | None = None


class SessionStorage:
    def __init__(self):
        self._sessions: dict[int, Session] = {}

    def get(self, user_id: int) -> Session:
        if user_id not in self._sessions:
            self._sessions[user_id] = Session()
        return self._sessions[user_id]

    def reset(self, user_id: int) -> None:
        if user_id in self._sessions:
            current = self._sessions[user_id]
            preserved = Session(
                auto_enabled=current.auto_enabled,
                organizer_login=current.organizer_login,
                organizer_tg=current.organizer_tg,
            )
            self._sessions[user_id] = preserved

