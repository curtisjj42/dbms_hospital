from __future__ import annotations
from PyQt6.QtCore import QObject, pyqtSignal
from databaseui.utils import QSingleton


class SignalManager(QObject, metaclass=QSingleton):
    # Signals to emit new data
    treatments_received = pyqtSignal(list)
    diseases_received = pyqtSignal(list)
    tests_received = pyqtSignal(list)
    patients_received = pyqtSignal(list, int)
    doctors_received = pyqtSignal(list)
    availability_received = pyqtSignal(list)
    dept_statistics_received = pyqtSignal(list)
    patient_tests_received = pyqtSignal(list)
    appointments_received = pyqtSignal(list)
    diagnoses_received = pyqtSignal(list)

    def __init__(self, parent=None, **kwargs):
        # noinspection PyArgumentList
        super().__init__(parent, **kwargs)
