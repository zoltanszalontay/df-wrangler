from statemachine import StateMachine, State
from .dataframe_service import dataframe_service
from .logging_service import logging_service
from datetime import datetime
from datetime import datetime

class SessionStateMachine(StateMachine):
    # States
    empty = State('Empty', initial=True)
    active = State('Active')

    # Transitions
    load_dataframe = empty.to(active) | active.to.itself()
    remove_last_dataframe = active.to(empty)
    pop_to_empty_state = active.to(empty)

    def __init__(self):
        super(SessionStateMachine, self).__init__()
        self.initialize_state()

    def log(self, message):
        if logging_service.get_logging_level("session") == "on":
            log_file = logging_service.get_log_file("session")
            if log_file:
                with open(log_file, "a", buffering=1) as f: # buffering=1 for line-buffering                    f.write(f"{datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")} - INFO - [SessionService] {message}
")
            else:
                print(f"[SessionService] {message}")

    def health(self):
        # For now, this service is always considered healthy
        return "OK"

    def initialize_state(self):
        """
        Initializes the state of the machine based on the current state of the dataframe_service.
        """
        if dataframe_service.get_all_dataframes():
            self.current_state = self.active
        else:
            self.current_state = self.empty

session_service = SessionStateMachine()
