"""
Provides commonly used decorators and metaclasses
"""


def singleton(cls):
    """
    Singleton decorator for classes.
    Use this if the class itself do not need to be referenced in the future.
    This will convert the class to a function that returns the singleton instance.
    Syntax is as follows:
    ```
    @decorator.singleton
    class MySingletonClass():
        ...
    ```
    Reference: https://divyakhatnar.medium.com/singleton-in-python-be59f7698a51
    """
    instances = {}

    def getinstance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return getinstance


class Singleton(type):
    """
    Singleton metaclass for classes.
    Use this if the class itself is still needed.
    Syntax is as follows:
    ```
    class MySingletonClass(metaclass=Singleton):
        ...
    ```
    REVIEW: this is not a decorator, it is put here for now
    Reference: https://divyakhatnar.medium.com/singleton-in-python-be59f7698a51
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


def overrides(interface_class):
    """
    Use this to indicate that a method is overriding a method in the superclass.
    This is useful for static type checkers to ensure that the method signature matches.
    Syntax is as follows:
    ```
    class <subclass>(<superclass>):
        @decorator.overrides(<superclass>)
        def <method>(self, ...):
            ...
    ```
    Reference: https://stackoverflow.com/questions/1167617/in-python-how-do-i-indicate-im-overriding-a-method
    """

    def overrider(method):
        assert method.__name__ in dir(interface_class)
        return method

    return overrider
