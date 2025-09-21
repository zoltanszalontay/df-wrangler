from statemachine import StateMachine, State
from .dataframe_service import dataframe_service

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

    def initialize_state(self):
        """
        Initializes the state of the machine based on the current state of the dataframe_service.
        """
        if dataframe_service.get_all_dataframes():
            self.current_state = self.active
        else:
            self.current_state = self.empty

session_service = SessionStateMachine()
