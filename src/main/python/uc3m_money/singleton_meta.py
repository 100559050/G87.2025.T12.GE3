"""Module providing a metaclass for implementing the Singleton pattern."""

class SingletonMeta(type):
    """
    A Singleton metaclass to ensure only one instance is created.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
