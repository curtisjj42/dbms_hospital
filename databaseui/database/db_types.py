from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class DBCredentials:
    user: str
    passwd: str
    host: str
    db_name: str


@dataclass
class Treatment:
    id: int
    name: str
    generic_id: Optional[int]


@dataclass
class Disease:
    id: int
    name: str
    description: str


@dataclass
class Diagnosis:
    patient_id: int
    doctor_id: int
    disease_id: int
    date: datetime
    comments: str


@dataclass
class NamedDiagnosis(Diagnosis):
    disease_name: str


@dataclass
class Person:
    id: int
    first_name: str
    last_name: str


@dataclass
class Patient:
    id: int
    person_id: int
    gender: str
    sex: str
    sexual_orientation: Optional[str]
    DOB: datetime
    phone_number: Optional[str]
    email: Optional[str]
    address: Optional[str]
    diagnoses: Optional[str]
    treatments: Optional[str]
    tests: Optional[str]
    appts: Optional[str]


@dataclass
class NamedPatient(Patient):
    first_name: str
    last_name: str


@dataclass
class BaseDoctor:
    id: int
    person_id: str
    department_id: str
    specialty_id: str


@dataclass
class Doctor(BaseDoctor):
    first_name: str
    last_name: str
    department_name: str
    specialty_name: str
    appt_time: list


@dataclass
class Availability:
    id: int
    doctor_id: int
    days_available: str
    start_time: datetime
    duration_h: int
    dates: datetime


@dataclass
class Appointment:
    id: int
    patient_id: int
    doctor_id: int
    department_id: int
    time: str
    status: str
    description: str


@dataclass
class NamedAppointment(Appointment):
    patient_name: str


@dataclass
class Room:
    room_number: int
    capacity: int
    dept_id: int


@dataclass
class LabTest:
    id: int
    disease_id: int
    test_name: str


@dataclass
class OrderedLabTest:
    patient_id: int
    lab_test_id: int
    doctor_id: int
    result: Optional[str]


@dataclass
class NamedOrderedLabTest(OrderedLabTest):
    test_name: str


@dataclass
class FilledOrderedLabTest(OrderedLabTest):
    first_name: str
    last_name: str
    test_name: str
    test_result: Optional[str]
    disease_name: str
    doctor_first_name: str
    doctor_last_name: str


@dataclass
class DepartmentStatistics:
    id: int
    department_name: str
    room_count: int
    total_capacity: int
    number_of_patients: int
    number_of_doctors: int
    scheduled_appointments: int
