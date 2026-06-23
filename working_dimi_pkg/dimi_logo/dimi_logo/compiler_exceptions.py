class IllegalVariableNameError(Exception):
    def __init__(self, variableName, message="Your variable cannot be named: "):

        message = message + f"\"{variableName}\""
        super().__init__(message)