from PyQt6.QtCore import QObject, pyqtSlot, pyqtProperty


class QSingleton(type(QObject), type):  # type: ignore
    def __init__(cls, name, bases, param_dict):
        super().__init__(name, bases, param_dict)
        cls.instance = None

    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super().__call__(*args, **kw)
        return cls.instance


class ExampleQSingleton(QObject, metaclass=QSingleton):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self._x = 0

    def x(self): return self._x

    @pyqtSlot(int)
    def setX(self, x): self._x = x

    x = pyqtProperty(int, x, setX)


if __name__ == "__main__":
    print(ExampleQSingleton().x)
    ExampleQSingleton().x = 1
    print(ExampleQSingleton().x)
