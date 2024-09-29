from typing import Any, List
import os
import pickle
from copy import deepcopy
import streamlit as st


SESSION_FILE = "session.pkl"

class Session:
    def __init__(self, *args, **kwargs):
        self.data = {}
        if args or kwargs:
            self.data.update(dict(*args, **kwargs))

    def set(self, key: str, data: Any, overwrite: bool = True):
        if not overwrite and key in self.data:
            return
        self.data[key] = data

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def clear(self):
        self.data.clear()

    def items(self):
        return self.data.items()

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __setitem__(self, key: str, value: Any):
        self.data[key] = value

    def __delitem__(self, key: str):
        del self.data[key]

    def __contains__(self, key: str) -> bool:
        return key in self.data

    def __repr__(self):
        return repr(self.data)

def save_session(session: Session):
    with open(SESSION_FILE, 'wb') as f:
        pickle.dump(session.data, f)

def load_session() -> Session:
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'rb') as f:
                session_data = pickle.load(f)
                session = Session()
                session.data = session_data  # Load the data into the session
                return session
    except EOFError:
        pass
    return Session()  # If no session file exists, return a new session

def update_session(session: Session, urls: List[str]):
    session_keys = deepcopy(list(session["urls"].keys()))
    for url in session_keys:
        # Remove any url from the session state that's not in the input
        if url not in urls:
            session["urls"].pop(url)
    for url in urls:
        session["urls"][url] = session["urls"].get(url, {})

def update_session_state(urls: List[str]):
    session_keys = deepcopy(list(st.session_state["urls"].keys()))
    for url in session_keys:
        # Remove any url from the session state that's not in the input
        if url not in urls:
            st.session_state["urls"].pop(url)
    for url in urls:
        st.session_state["urls"][url] = st.session_state["urls"].get(url, {})

