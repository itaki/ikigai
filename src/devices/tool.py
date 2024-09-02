class Tool:
    def __init__(self, label, tool_type, tool_id, physical_location, preferences, connection):
        self.label = label
        self.type = tool_type
        self.id = tool_id
        self.physical_location = physical_location
        self.preferences = preferences
        self.connection = connection

    def perform_action(self):
        # Define actions based on tool type and preferences
        pass
