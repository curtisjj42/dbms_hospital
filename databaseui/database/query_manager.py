import datetime
from typing import Callable, Any, Optional

from PyQt6.QtCore import QThreadPool
from sqlalchemy import text, Result
from sqlalchemy.orm import Session

from databaseui.database import with_session
from databaseui.database.db_types import (Treatment, Disease, NamedPatient,
                                          Doctor, Patient, Availability, LabTest, DepartmentStatistics, OrderedLabTest,
                                          BaseDoctor,
                                          NamedOrderedLabTest, Appointment, NamedAppointment, NamedDiagnosis)
from databaseui.signals.signal_manager import SignalManager
from databaseui.threads.worker import Worker


def run_in_pool(pool: QThreadPool, fn: Callable, *args, **kwargs) -> Worker:
    """
    Convenience function to run a function inside a thread pool. This function will not provide a progress signal
    :param pool: Thread Pool
    :param fn: Function to run
    :param args: Positional arguments to pass to the function
    :param kwargs: Keyword arguments to pass to the function
    :return: A worker instance with signals that can be used later
    """
    worker = Worker(fn, False, *args, **kwargs)
    pool.start(worker)
    return worker


def run_in_pool_progress(pool: QThreadPool, fn: Callable, *args, **kwargs) -> Worker:
    """
    Convenience function to run a function inside a thread pool. This function will provide a progress signal,
    if a handler is passed in
    :param pool: Thread Pool
    :param fn: Function to run
    :param args: Positional arguments to pass to the function
    :param kwargs: Keyword arguments to pass to the function
    :return: A worker instance with signals that can be used later
    """
    worker = Worker(fn, True, *args, **kwargs)
    pool.start(worker)
    return worker


@with_session
def get_all_treatments(session: Session):
    """
    Selects all treatments and emits to the treatments_received signal.
    Maps to `Treatment` objects
    :param session:
    :return:
    """
    result = session.execute(text("SELECT * FROM `treatment`"))
    treatments = list(map(lambda item: Treatment(*item), result))
    print(f'Got {len(treatments)} treatments')
    SignalManager().treatments_received.emit(treatments)


@with_session
def get_all_tests(session: Session):
    """
    Selects all tests and emits to the tests_received signal.
    Maps to `LabTest` objects
    :param session:
    :return:
    """
    result = session.execute(text("SELECT * FROM `lab_test`"))
    tests = list(map(lambda item: LabTest(*item), result))
    print(f'Got {len(tests)} tests')
    SignalManager().tests_received.emit(tests)


@with_session
def get_department_statistics(session: Session):
    """
    Selects all department statistics from the department_statistics view.
    Emits in dept_statistics_received.
    Maps to `DepartmentStatistics` objects
    :param session:
    :return:
    """
    result = session.execute(text('SELECT * FROM `department_statistics`'))
    statistics = list(map(lambda item: DepartmentStatistics(*item), result))
    print(f'Got {len(statistics)} departments')
    SignalManager().dept_statistics_received.emit(statistics)


@with_session
def get_all_diseases(session: Session):
    """
    Gets all diseases and emits on diseases_received.
    Maps to `Disease` objects
    :param session:
    :return:
    """
    result = session.execute(text("SELECT * FROM `disease` "))
    diseases = list(map(lambda item: Disease(*item), result))
    print(f'Got {len(diseases)} diseases')
    SignalManager().diseases_received.emit(diseases)


@with_session
def get_all_patients(session: Session, last_patient_id: int = -1):
    """
    Gets all patients and emits on patients_received.
    Maps to `NamedPatient` objects
    :param session:
    :param last_patient_id: The last patient id to emit
    :return:
    """
    result = session.execute(text("SELECT * FROM `patient_info`"))
    patients = list(map(lambda item: NamedPatient(*item), result))
    print(f'Got {len(patients)} patients')
    SignalManager().patients_received.emit(patients, last_patient_id)


@with_session
def update_patient_information(session: Session, patient: NamedPatient):
    """
    Takes in the new patient information and updates the table. Uses several queries because SQLAlchemy requires
    single transactions for execution.
    :param session:
    :param patient: The patient to update
    :return:
    """
    query = text("UPDATE person "
                 "INNER JOIN patient ON patient.person_id = person.id "
                 "SET first_name = :first_name, last_name = :last_name "
                 "WHERE patient.person_id = :person_id; ")
    session.begin()
    session.execute(
        query,
        {"patient_id": patient.id, "person_id": patient.person_id, "first_name": patient.first_name,
         "last_name": patient.last_name}
    )

    query = text("UPDATE patient "
                 "SET gender = :gender, sex = :sex, sexual_orientation = :sexual_orientation, DOB = :dob, "
                 "phone_number = :phone_number, email = :email, address = :address "
                 "WHERE patient.id = :patient_id;")

    session.execute(query, {"patient_id": patient.id, "gender": patient.gender, "sex": patient.sex,
                            "sexual_orientation": patient.sexual_orientation, "dob": patient.DOB,
                            "phone_number": patient.phone_number, "email": patient.email, "address": patient.address})


@with_session
def get_all_doctors(session: Session):
    """
    Get all doctors, emit on doctors_received.
    Maps to `Doctor` objects
    :param session:
    :return:
    """
    result = session.execute(text("select * from `doctor_info`"))
    doctors = list(map(lambda item: Doctor(*item), result))
    print(f'Got {len(doctors)} doctors')
    SignalManager().doctors_received.emit(doctors)


@with_session
def get_all_availability(session: Session):
    """
    Get all availability entries. Emit on availability_received.
    Maps to `Availability` objects
    :param session:
    :return:
    """
    query = "SELECT * from availability"
    result = session.execute(text(query))
    availability = list(map(lambda item: Availability(*item), result))
    print(f'Got {len(availability)} availability entries')
    SignalManager().availability_received.emit(availability)


@with_session
def get_appointments(session: Session, patient: Patient | int):
    """
    Get all appointments, include patient first name and last name. Emit on appointments_received.
    Maps to `NamedAppointment` objects
    :param session:
    :param patient:
    :return:
    """
    query = ("SELECT appointment.*, CONCAT(pe.first_name, ' ', pe.last_name) AS patient_name "
             "FROM appointment "
             "INNER JOIN patient AS pa ON pa.id = appointment.patient_id "
             "LEFT JOIN person AS pe on pe.id = pa.person_id "
             "WHERE pa.id = :patient_id")
    if isinstance(patient, Patient):
        patient = patient.id
    result = session.execute(text(query), {'patient_id': patient})
    appointments = list(map(lambda item: NamedAppointment(*item), result))
    print(f'Got {len(appointments)} appointment entries for patient {patient}')
    SignalManager().appointments_received.emit(appointments)


@with_session
def get_tests_for_patient(session: Session, patient: Patient | int, doctor: BaseDoctor | int) -> None:
    """
    Queries the database for all ordered test information, and lab test names. Emits on patient_tests_received.
    Maps to `NamedOrderedLabTest` objects
    :param session:
    :param patient:
    :param doctor:
    :return:
    """
    query = text("SELECT ordered_lab_test.*, lt.test_name FROM "
                 "`ordered_lab_test` "
                 "LEFT JOIN lab_test as lt ON ordered_lab_test.lab_test_id = lt.id "
                 "WHERE doctor_id = :dr_id AND patient_id = :pt_id")
    if isinstance(patient, Patient):
        patient = patient.id
    if isinstance(doctor, Doctor):
        doctor = doctor.id
    result = session.execute(query, {'dr_id': doctor, 'pt_id': patient})
    tests = list(map(lambda item: NamedOrderedLabTest(*item), result))
    print(f'Got {len(tests)} test for patient {patient} and doctor {doctor}')
    SignalManager().patient_tests_received.emit(tests)


@with_session
def create_diagnosis(session: Session, patient: Patient | int, doctor: Doctor | int, disease: Disease | int):
    """
    Creates a diagnosis for a given patient
    :param session:
    :param patient:
    :param doctor:
    :param disease:
    :return:
    """
    if isinstance(patient, Patient):
        patient = patient.id
    if isinstance(doctor, Doctor):
        doctor = doctor.id
    if isinstance(disease, Disease):
        disease = disease.id

    query = text("insert into diagnosis (patient_id, doctor_id, disease_id) VALUES (:p, :dr, :ds)")
    session.begin()
    session.execute(
        query,
        {'p': patient, 'dr': doctor, 'ds': disease}
    )


@with_session
def create_new_patient(session: Session, patient: NamedPatient):
    """
    Creates a new patient given name information
    :param session:
    :param patient:
    :return:
    """
    query = text("INSERT INTO person (first_name, last_name) VALUES (:first_name, :last_name);")
    session.begin()
    session.execute(
        query,
        {'first_name': patient.first_name, 'last_name': patient.last_name}
    )

    session.execute(text("SET @person_id = LAST_INSERT_ID();"))

    query = text("INSERT INTO patient (person_id, gender, sex, sexual_orientation, DOB, phone_number, email, address) "
                 "VALUES (@person_id, :gender, :sex, :sexual_orientation, :DOB, :phone_number, :email, :address);")
    session.execute(
        query,
        {"gender": patient.gender, "sex": patient.sex, "sexual_orientation": patient.sexual_orientation,
         "DOB": patient.DOB, "phone_number": patient.phone_number, "email": patient.email, "address": patient.address}
    )


@with_session
def create_room_assignment(session: Session, patient: Patient | int, room: int):
    """
    Creates a room assignment for a patient.
    :param session:
    :param patient: The patient
    :param room: Room to occupy
    :return:
    """
    if isinstance(patient, Patient):
        patient = patient.id
    query = text("INSERT INTO room_assignment (room_number, patient_id) VALUES (:r_n, :p_id)")
    session.begin()
    result = session.execute(
        query,
        {'r_n': room, 'p_id': patient}
    )
    return result


@with_session
def order_lab_test(session: Session, patient: Patient | int, doctor: Doctor | int, test: LabTest) -> Result[Any]:
    """
    Orders a lab test given the parameter information
    :param session:
    :param patient: Patient object or id
    :param doctor: Doctor object or ID
    :param test: Lab test to order
    :return:
    """
    print('Ordering Lab Test')
    if isinstance(patient, Patient):
        patient = patient.id
    if isinstance(doctor, Doctor):
        doctor = doctor.id

    query = text("INSERT INTO ordered_lab_test (patient_id, lab_test_id, doctor_id) "
                 "VALUES (:p_id, :test_id, :dr_id);")

    session.begin()
    result = session.execute(
        query,
        {'d_id': test.disease_id, 'test_id': test.id, 'p_id': patient, 'dr_id': doctor}
    )
    print('Returning Lab Test Result')
    return result


@with_session
def order_prescription(session: Session, patient: Patient | int, disease: Disease | int, treatment: Treatment | int,
                       start_date: datetime, end_date: datetime, comments: Optional[str]):
    """
    Orders a prescription for a patient
    :param session:
    :param patient: Patient or ID
    :param disease: Disease or ID
    :param treatment: Treatment or ID
    :param start_date: Date to start
    :param end_date: Date to end
    :param comments: Instructions on usage, or None
    :return:
    """
    if isinstance(patient, Patient):
        patient = patient.id
    if isinstance(disease, Disease):
        disease = disease.id
    if isinstance(treatment, Treatment):
        treatment = treatment.id
    print(f'Ordering Rx for {patient = }, {disease = }, {treatment = }')

    query = text(
        "INSERT INTO patient_prescription "
        "(patient_id, disease_id, treatment_id, start_date, end_date, dosage_instructions) "
        "VALUES (:patient_id, :disease_id, :treatment_id, :start_date, :end_date, :comments);")

    session.begin()
    session.execute(
        query,
        {'patient_id': patient, 'disease_id': disease, 'treatment_id': treatment, 'start_date': start_date,
         'end_date': end_date, 'comments': comments}
    )


@with_session
def make_appointment(session: Session, patient: Patient | int, doctor: Doctor | int, appointment: str,
                     description: str):
    """
    Creates an appointment for a patient
    :param session:
    :param patient: Patient or ID
    :param doctor: Doctor or ID
    :param appointment: Appointment string
    :param description: Reason for appointment
    :return:
    """
    print('Making appointment')
    if isinstance(patient, Patient):
        patient = patient.id
    if isinstance(doctor, Doctor):
        doctor = doctor.id

    query = text("CALL ScheduleAppointment(:patient_id, :doctor_id, :appointment, :description);")

    session.begin()
    result = session.execute(
        query,
        {'patient_id': patient, 'doctor_id': doctor, 'appointment': appointment, 'description': description}
    )
    print('Returning appointment result')
    return result


@with_session
def update_appointment_status(session: Session, appointment: Appointment | str, status: str):
    """
    Updates the appointment status of a patient. e.g. when they check in
    :param session:
    :param appointment: Appointment to update
    :param status: New Status
    :return:
    """
    print('Updating appointment')

    query = text("CALL UpdateAppointmentStatus(:appointment_id, :status);")

    session.begin()
    result = session.execute(
        query, {"appointment_id": appointment, "status": status}
    )
    return result


@with_session
def update_test_status(session: Session, ordered_test: OrderedLabTest, result: str):
    """
    Updates a test with a result
    :param session:
    :param ordered_test: Test
    :param result: result string
    :return:
    """
    print('Updating test')
    query = text("CALL UpdateTestStatus(:patient_id, :labtest_id, :doctor_id, :result);")
    session.begin()
    session.execute(
        query,
        {"patient_id": ordered_test.patient_id, "labtest_id": ordered_test.lab_test_id,
         "doctor_id": ordered_test.doctor_id, "result": result}
    )


@with_session
def get_diagnoses_for_patient(session: Session, patient: Patient):
    """
    Gets all diagnoses for a patient. Emits on diagnoses_received.
    Maps to `NamedDiagnosis` objects
    :param session:
    :param patient:
    :return:
    """
    query = text("SELECT dia.*, dis.name "
                 "FROM diagnosis AS dia "
                 "LEFT JOIN disease AS dis ON dia.disease_id = dis.id "
                 "WHERE patient_id = :pt_id")
    result = session.execute(
        query, {"pt_id": patient.id}
    )
    diagnoses = list(map(lambda item: NamedDiagnosis(*item), result))
    print(f'Got {len(diagnoses)} test for patient {patient}')
    SignalManager().diagnoses_received.emit(diagnoses)


@with_session
def add_comments(session: Session, diagnosis: NamedDiagnosis, comment: str):
    """
    Adds comments to a diagnosis for a patient
    :param session:
    :param diagnosis: Diagnosis object
    :param comment: new comments
    :return:
    """
    query = text("UPDATE diagnosis "
                 "SET comments = :comment "
                 "WHERE patient_id = :patient_id "
                 "AND doctor_id = :doctor_id "
                 "AND disease_id = :disease_id;")
    session.begin()
    session.execute(
        query,
        {"comment": comment, "patient_id": diagnosis.patient_id, "doctor_id": diagnosis.doctor_id,
         "disease_id": diagnosis.disease_id}
    )
