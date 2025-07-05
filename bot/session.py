from dataclasses import dataclass, field

@dataclass
class Session:
    theme: str | None = None
    my_room: str | None = None
    awaiting_my_room: bool = False


class SessionStorage:
    def __init__(self):
        self._sessions: dict[int, Session] = {}

    def get(self, user_id: int) -> Session:
        if user_id not in self._sessions:
            self._sessions[user_id] = Session()
        return self._sessions[user_id]

    def reset(self, user_id: int) -> None:
        if user_id in self._sessions:
            self._sessions[user_id] = Session()

