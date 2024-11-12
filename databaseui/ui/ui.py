import sys
from typing import List, Optional, Tuple

from PyQt6.QtCore import QThreadPool
from PyQt6.QtWidgets import QApplication, QMainWindow, QHeaderView, QTableWidgetItem, QListWidgetItem

from databaseui.database import DatabaseManager
from databaseui.database.db_types import DBCredentials, Treatment, Disease, NamedPatient, Doctor, LabTest, \
    DepartmentStatistics, BaseDoctor, Patient, NamedOrderedLabTest, NamedAppointment, \
    Diagnosis, NamedDiagnosis
from databaseui.database.query_manager import get_all_treatments, run_in_pool, get_all_diseases, get_all_patients, \
    get_all_doctors, get_all_tests, get_department_statistics, get_all_availability, get_tests_for_patient, \
    order_lab_test, make_appointment, update_appointment_status, get_appointments, update_test_status, add_comments, \
    get_diagnoses_for_patient, update_patient_information, create_new_patient, create_diagnosis, order_prescription
from databaseui.env import load_config
from databaseui.signals.signal_manager import SignalManager
from databaseui.ui.app import Ui_MainWindow


# noinspection DuplicatedCode
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        # Init UI
        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)

        # Set up tables to stretch properly, since you can't do that in QT creator
        self._ui.activeTests_Table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(3):
            self._ui.appointmentTable.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        # Load configs, set up thread pool and init singleton signal manager
        self.config = load_config()
        self._pool = QThreadPool()
        self._signal_manager = SignalManager()

        # Set up components

        # Set up signals and listeners
        # "Do things when we get data from the Database"
        self._signal_manager.treatments_received.connect(self.on_treatments_received)
        self._signal_manager.tests_received.connect(self.on_test_types_received)
        self._signal_manager.diseases_received.connect(self.on_diseases_received)
        self._signal_manager.patients_received.connect(self.on_patients_received)
        self._signal_manager.doctors_received.connect(self.on_doctors_received)
        self._signal_manager.dept_statistics_received.connect(self.on_dept_rooms_received)
        self._signal_manager.patient_tests_received.connect(self.on_ordered_tests_received)
        self._signal_manager.appointments_received.connect(self.on_appointments_received)
        self._signal_manager.diagnoses_received.connect(self.on_diagnoses_received)

        # UI Listeners
        # "Do things when the UI changes"
        self._ui.patientSelectList_2.currentIndexChanged.connect(self.on_doctor_patient_change)
        self._ui.doctorSelectList_2.currentIndexChanged.connect(self.on_doctor_patient_change)
        self._ui.adminDepartmentSelectList.currentIndexChanged.connect(self.see_hospital_stats)
        self._ui.doctorSelectList_1.currentIndexChanged.connect(self.see_dr_appointments)
        self._ui.patientSelectList_1.currentIndexChanged.connect(self.set_pt_details)
        self._ui.patientSelectList_1.currentIndexChanged.connect(self.self_edit_patient_fields)
        self._ui.savePatientInfo.clicked.connect(self.update_patient_details)
        self._ui.activeTests_OrderTestButton.clicked.connect(self.on_doctor_order_test)
        self._ui.patientAppointmentSave.clicked.connect(self.on_make_appointment)
        self._ui.adminCheckIn.clicked.connect(self.on_admin_update_appointment)
        self._ui.updateAppointment_t1_name.currentIndexChanged.connect(self.see_pt_appointments)
        self._ui.saveTestStatus.clicked.connect(self.update_test_results)
        self._ui.saveComments.clicked.connect(self.update_comments)
        self._ui.addPatientSave.clicked.connect(self.create_patient)
        self._ui.addComments_t1_diagnosis.currentIndexChanged.connect(self.on_cur_diagnosis_changed)
        self._ui.patientEditAddDiagnosis_1.clicked.connect(self.on_add_diagnosis)
        self._ui.patientEditsave_3.clicked.connect(self.on_add_treatment)

        # Connect to Database and run pool to get data
        self.setup_connections()
        self.get_initial_data()

        print('Finished init')

    ################################################################################
    # Handle Responses from Queries
    ################################################################################

    def get_initial_data(self) -> None:
        """
        Get initial data from the database
        :return: None
        """
        print('Fetching')

        def get():
            get_all_treatments()
            get_all_diseases()
            get_all_patients()
            get_all_doctors()
            get_all_tests()
            get_department_statistics()
            get_all_availability()

        run_in_pool(self._pool, get)

    def on_treatments_received(self, treatments: list[Treatment]) -> None:
        """
        When we receive the global treatment list, update the doctor view dropdown
        with all the treatments we could prescribe to a patient
        :param treatments: List of treatments
        :return:
        """
        print('Received')
        self._ui.editPatient_t2_addScript.clear()
        for item in treatments:
            self._ui.editPatient_t2_addScript.addItem(f'{item.name}', userData=item)

    def on_diseases_received(self, diseases: list[Disease]):
        """
        When we receive the global disease list, update the doctor view dropdown for
        all things we could diagnose a patient with.
        :param diseases: List of diseases
        :return:
        """
        print('Received Disease List')
        self._ui.editPatient_t1_diagnoses.clear()
        for item in diseases:
            self._ui.editPatient_t1_diagnoses.addItem(f'{item.name}', userData=item)

    def on_test_types_received(self, tests: list[LabTest]):
        """
        When we receive the global list of tests we could order, update the doctor view dropdown
        for all the tests.
        :param tests: List of tests
        :return:
        """
        print('Received Test List')
        self._ui.activeTests_OrderTestDropdown.clear()
        for t in tests:
            self._ui.activeTests_OrderTestDropdown.addItem(t.test_name, userData=t)

    def on_patients_received(self, patients: list[NamedPatient], last_patient_id: int):
        """
        When we receive the global list of patients we update all dropdowns where you could choose a patient.
        If a last_patient_id is provided, then make sure to set the dropdowns back to where they were.
        This cascades an 'onIndexChanged' event, populating the UI with the latest data from a patient operation.
        :param patients: List of patients
        :param last_patient_id: Last id, or -1 if not used
        :return:
        """
        print('Received Patients List')
        self._ui.patientSelectList_1.clear()
        self._ui.patientSelectList_2.clear()
        self._ui.updateAppointment_t1_name.clear()
        cur_select_idx: Optional[Tuple[int, int, int]] = None
        for p in patients:
            self._ui.patientSelectList_1.addItem(f'{p.first_name} {p.last_name}', userData=p)
            self._ui.patientSelectList_2.addItem(f'{p.first_name} {p.last_name}', userData=p)
            self._ui.updateAppointment_t1_name.addItem(f'{p.first_name} {p.last_name}', userData=p)
            if p.id == last_patient_id:
                cur_select_idx = (
                    self._ui.patientSelectList_1.count() - 1,
                    self._ui.patientSelectList_2.count() - 1,
                    self._ui.updateAppointment_t1_name.count() - 1
                )
        if cur_select_idx is None:
            return
        self._ui.patientSelectList_1.setCurrentIndex(cur_select_idx[0])
        self._ui.patientSelectList_2.setCurrentIndex(cur_select_idx[1])
        self._ui.updateAppointment_t1_name.setCurrentIndex(cur_select_idx[2])

    def on_doctors_received(self, doctors: list[Doctor]):
        """
        When we receive a list of doctors from the database, update all the dropdowns with the doctor names
        :param doctors: List of doctors
        :return:
        """
        print('Received Doctors List')
        self._ui.doctorSelectList_1.clear()
        self._ui.doctorSelectList_2.clear()
        for d in doctors:
            self._ui.doctorSelectList_1.addItem(f'{d.first_name} {d.last_name}', userData=d)
            self._ui.doctorSelectList_2.addItem(f'{d.first_name} {d.last_name}', userData=d)

    def on_dept_rooms_received(self, dept_rooms: list[DepartmentStatistics]):
        """
        When we receive a list Departments and Statistics, update all the dropdowns with the department and set the
        statistics data for later use
        :param dept_rooms: List of Departments
        :return:
        """
        print('Received Department Stats')
        self._ui.adminDepartmentSelectList.clear()
        for dr in dept_rooms:
            self._ui.adminDepartmentSelectList.addItem(f'{dr.department_name}', userData=dr)

    def on_ordered_tests_received(self, ordered_tests: List[NamedOrderedLabTest]):
        """
        Called when we receive ordered tests for a selected patient from the DB.
        Clear the active tests table to list all the new tests we might have, and update the test results dropdown
        in case we need to mark a test as passed/failed/inconclusive.
        :param ordered_tests: Tests for a patient
        :return:
        """
        self._ui.activeTests_Table.clearContents()
        self._ui.activeTests_Table.setRowCount(len(ordered_tests))
        self._ui.editTestStatus_t1_test.clear()
        for idx in range(len(ordered_tests)):
            self._ui.activeTests_Table.setItem(idx, 0, QTableWidgetItem(ordered_tests[idx].test_name or 'Unknown Test'))
            self._ui.activeTests_Table.setItem(idx, 1, QTableWidgetItem(ordered_tests[idx].result or 'Not Started'))
            if ordered_tests[idx].result is None:
                self._ui.editTestStatus_t1_test.addItem(ordered_tests[idx].test_name, userData=ordered_tests[idx])

    def on_diagnoses_received(self, diagnoses: List[NamedDiagnosis]):
        """
        When we receive a list of diagnoses, update the relevant dropdowns for that patient
        :param diagnoses:
        :return:
        """
        self._ui.addComments_t1_diagnosis.clear()
        self._ui.addComments_t2_comments.clear()
        self._ui.editPatient_t1_selectDiagnosis.clear()
        for diagnosis in diagnoses:
            self._ui.addComments_t1_diagnosis.addItem(diagnosis.disease_name, userData=diagnosis)
            self._ui.editPatient_t1_selectDiagnosis.addItem(diagnosis.disease_name, userData=diagnosis)

    def on_appointments_received(self, appointments: List[NamedAppointment]):
        print('Received Appointments')
        self._ui.appointmentTable.clearContents()
        self._ui.appointmentTable.setRowCount(len(appointments))
        for idx in range(len(appointments)):
            self._ui.appointmentTable.setItem(idx, 0, QTableWidgetItem(appointments[idx].patient_name))
            self._ui.appointmentTable.setItem(idx, 1, QTableWidgetItem(appointments[idx].time))
            self._ui.appointmentTable.setItem(idx, 2, QTableWidgetItem(appointments[idx].description))
            self._ui.appointmentTable.setItem(idx, 3, QTableWidgetItem(appointments[idx].status))

    ################################################################################
    # Handle Updating Elements
    ################################################################################

    def on_doctor_patient_change(self):
        """
        Called when the patient or doctor dropdown changes in the doctor tab.
        Get the patient and doctor data from their respective dropdowns and call for updates to tests and diagnoses.
        Update / Populate lists for active diagnoses and prescriptions.
        :return:
        """
        patient_data = self._ui.patientSelectList_2.currentData()
        if patient_data is None or not isinstance(patient_data, NamedPatient):
            print(f'Bad Patient data for fields: {patient_data}')
            return

        # Need doctor data
        doctor_data = self._ui.doctorSelectList_2.currentData()
        if doctor_data is None or not isinstance(doctor_data, Doctor):
            print(f'Bad Doctor data for fields: {doctor_data}')
            return
        # Update active tests
        self._ui.editPatient_t2_activeDiagnosisList.clear()
        self._ui.editPatient_t6_activeScriptList.clear()
        for active_diagnosis in patient_data.diagnoses.split(','):
            self._ui.editPatient_t2_activeDiagnosisList.addItem(QListWidgetItem(active_diagnosis))
        for cur_treatment in patient_data.treatments.split(','):
            self._ui.editPatient_t6_activeScriptList.addItem(QListWidgetItem(cur_treatment))

        run_in_pool(self._pool, get_tests_for_patient, patient_data, doctor_data)
        run_in_pool(self._pool, get_diagnoses_for_patient, patient_data)

    def self_edit_patient_fields(self):
        """
        Called when a patient dropdown changes, update the fields to display patient info
        :return:
        """
        data = self._ui.patientSelectList_1.currentData()
        if data is None or not isinstance(data, NamedPatient):
            print(f'Bad Patient data for fields: {data}')
            return
        self._ui.editSelf_t1_firstName.setText(data.first_name)
        self._ui.editSelf_t2_lastName.setText(data.last_name)
        self._ui.editSelf_t3_sex.setText(data.sex)
        self._ui.editSelf_t4_gender.setText(data.gender)
        self._ui.editSelf_t5_orientation.setText(data.sexual_orientation)
        self._ui.editSelf_t6_dob.setDate(data.DOB)
        self._ui.editSelf_t7_phone.setText(data.phone_number)
        self._ui.editSelf_t8_email.setText(data.email)
        self._ui.editSelf_t9_address.setText(data.address)

    def see_hospital_stats(self):
        """
        When we select a department from the admin department dropdown, update the fields that show that department's
        statistics
        :return:
        """
        data = self._ui.adminDepartmentSelectList.currentData()
        if data is None or not isinstance(data, DepartmentStatistics):
            print(f'Bad department data for fields: {data}')
            return
        self._ui.hospitalStatistic_t1_rooms.setText(str(data.room_count))
        self._ui.hospitalStatistic_t2_capacity.setText(str(data.total_capacity))
        self._ui.hospitalStatistic_t3_patients.setText(str(data.number_of_patients))
        self._ui.hospitalStatistic_t4_doctors.setText(str(data.number_of_doctors))
        self._ui.hospitalStatistic_t5_appointments.setText(str(data.scheduled_appointments))

    def see_dr_appointments(self):
        """
        When a patient selects a doctor, populate the dropdown with the doctor's availability
        :return:
        """
        data = self._ui.doctorSelectList_1.currentData()
        appt_time = data.appt_time.split(",")
        if data is None or not isinstance(data, Doctor):
            print(f'No doctor selected to view appointments: {data}')
            return
        self._ui.editPatient_t3_drAvailability.clear()
        for at in appt_time:
            self._ui.editPatient_t3_drAvailability.addItem(at, userData=at)

    def see_pt_appointments(self):
        """
        When an admin selects a patient to view their appointments, populate the table and dropdown with
        all the available appointments to reference.
        Runs a query to get the full data from the DB
        :return:
        """
        cur_patient = self._ui.updateAppointment_t1_name.currentData()
        if cur_patient is None or not isinstance(cur_patient, Patient):
            print(f'Tried to get appointments for patient {cur_patient}, but encountered the wrong type')
            return
        self._ui.updateAppointment_t2_time.clear()
        self._ui.appointmentTable.clearContents()
        self._ui.appointmentTable.setRowCount(0)
        if cur_patient.appts is None:
            print('Patient has no appointments')
            return
        appts = cur_patient.appts.split(",")
        for at in appts:
            self._ui.updateAppointment_t2_time.addItem(at, userData=at)
        run_in_pool(self._pool, get_appointments, cur_patient)

    def create_patient(self):
        """
        Runs a database insert to create a patient based on the fields in the admin view
        :return:
        """
        print('Creating Patient record')
        new_patient = NamedPatient(
            first_name=self._ui.addPatient_t1_firstName.text(),
            last_name=self._ui.addPatient_t2_lastName.text(),
            sex=self._ui.addPatient_t3_sex.text(),
            gender=self._ui.addPatient_t4_gender.text(),
            sexual_orientation=self._ui.addPatient_t5_orientation.text(),
            DOB=self._ui.addPatient_t6_dob.dateTime().toPyDateTime(),
            phone_number=self._ui.addPatient_t7_phone.text(),
            email=self._ui.addPatient_t8_email.text(),
            address=self._ui.addPatient_t9_address.text(),
            appts=None, diagnoses=None, id=0, person_id=0, tests=None, treatments=None)

        print('Adding patient in pool')
        worker = run_in_pool(self._pool, create_new_patient, new_patient)
        worker.signals.finished.connect(lambda: run_in_pool(self._pool, get_all_patients))
        print('Finished updating pool')

    def set_pt_details(self):
        """
        Set patient name on selecting from the dropdown
        :return:
        """
        data = self._ui.patientSelectList_1.currentData()
        if data is None or not isinstance(data, NamedPatient):
            print('There is no patient data')
            return
        self._ui.editPatient_t1_firstName1.setText(data.first_name)
        self._ui.editPatient_t2_lastName1.setText(data.last_name)

    def update_test_results(self):
        """
        Update a test result with a positive/negative/inconclusive result.
        Then run queries to update tests and diagnoses with most recent data
        :return:
        """
        data = self._ui.editTestStatus_t1_test.currentData()
        result = self._ui.editTestStatus_t2_status.currentText()

        cur_doctor = self._ui.doctorSelectList_2.currentData()
        if cur_doctor is None or not isinstance(cur_doctor, BaseDoctor):
            print('No Doctor selected')
            return
        cur_patient = self._ui.patientSelectList_2.currentData()
        if cur_patient is None or not isinstance(cur_patient, Patient):
            print('No Patient selected')
            return

        def to_run():
            get_tests_for_patient(cur_patient, cur_doctor)
            get_diagnoses_for_patient(cur_patient)

        worker = run_in_pool(self._pool, update_test_status, data, result)
        worker.signals.finished.connect(lambda: run_in_pool(self._pool, to_run))

    def update_comments(self):
        """
        Called to update the comments about a diagnosis for a patient.
        Calls the DB after to get most recent data
        :return:
        """
        cur_doctor = self._ui.doctorSelectList_2.currentData()
        if cur_doctor is None or not isinstance(cur_doctor, BaseDoctor):
            print('No Doctor selected')
            return
        cur_patient = self._ui.patientSelectList_2.currentData()
        if cur_patient is None or not isinstance(cur_patient, Patient):
            print('No Patient selected')
            return
        cur_diagnosis = self._ui.addComments_t1_diagnosis.currentData()
        comments = self._ui.addComments_t2_comments.toPlainText()

        worker = run_in_pool(self._pool, add_comments, cur_diagnosis, comments)
        worker.signals.finished.connect(lambda: run_in_pool(self._pool, get_diagnoses_for_patient, cur_patient))

    def update_patient_details(self):
        """
        Allows a patient to update their data and store it in the database.
        Uses prepared statements to prevent injection by the user
        :return:
        """
        print('Updating Patient records')
        cur_patient: Optional[NamedPatient] = self._ui.patientSelectList_1.currentData()
        if cur_patient is None or not isinstance(cur_patient, Patient):
            print('No Patient selected')
            return
        cur_patient.first_name = self._ui.editSelf_t1_firstName.text()
        cur_patient.last_name = self._ui.editSelf_t2_lastName.text()
        cur_patient.sex = self._ui.editSelf_t3_sex.text()
        cur_patient.gender = self._ui.editSelf_t4_gender.text()
        cur_patient.sexual_orientation = self._ui.editSelf_t5_orientation.text()
        cur_patient.DOB = self._ui.editSelf_t6_dob.dateTime().toPyDateTime()
        cur_patient.phone_number = self._ui.editSelf_t7_phone.text()
        cur_patient.email = self._ui.editSelf_t8_email.text()
        cur_patient.address = self._ui.editSelf_t9_address.text()

        print('Updating patient in pool')
        worker = run_in_pool(self._pool, update_patient_information, cur_patient)
        worker.signals.finished.connect(lambda: run_in_pool(self._pool, get_all_patients, cur_patient.id))
        print('Finished updating pool')

    def on_cur_diagnosis_changed(self):
        """
        When a diagnosis is changed, update the text in the box
        :return:
        """
        print('Updating diagnosis')
        cur_diag = self._ui.addComments_t1_diagnosis.currentData()
        if cur_diag is None or not isinstance(cur_diag, Diagnosis):
            print(f'Tried to get comments from diagnosis, but {cur_diag =}')
            return
        self._ui.addComments_t2_comments.setText(cur_diag.comments)

    def on_add_diagnosis(self):
        """
        When the button to add a diagnosis is clicked, get the disease, patient, and doctor and execute the query.
        Then update patient information
        :return:
        """
        disease_to_add = self._ui.editPatient_t1_diagnoses.currentData()
        if disease_to_add is None or not isinstance(disease_to_add, Disease):
            print(f'Tried to add new diagnosis, but no disease is set: {disease_to_add}')
            return
        cur_patient: Optional[NamedPatient] = self._ui.patientSelectList_2.currentData()
        if cur_patient is None or not isinstance(cur_patient, NamedPatient):
            print(f'Tried to add new diagnosis, but no patient is set: {cur_patient}')
            return
        cur_doctor = self._ui.doctorSelectList_2.currentData()
        if cur_doctor is None or not isinstance(cur_doctor, Doctor):
            print(f'Tried to add new diagnosis, but no doctor is set: {cur_doctor}')
            return
        print(f'Trying to add a new diagnosis to {cur_patient = }, {cur_doctor = }, {disease_to_add = }')

        worker = run_in_pool(self._pool, create_diagnosis, cur_patient, cur_doctor, disease_to_add)
        worker.signals.finished.connect(lambda: run_in_pool(self._pool, get_all_patients, cur_patient.id))

    def on_add_treatment(self):
        """
        When the button to add a treatment / prescription is pressed, get the treatment,
        diagnosis, start date, end date, and instructions.
        Call DB query to add all elements and then get new patient data
        :return:
        """
        treatment_to_add = self._ui.editPatient_t2_addScript.currentData()
        if treatment_to_add is None or not isinstance(treatment_to_add, Treatment):
            print(f'Tried to add new treatment, but no treatment is set: {treatment_to_add}')
            return
        cur_diagnosis: Optional[NamedDiagnosis] = self._ui.editPatient_t1_selectDiagnosis.currentData()
        if cur_diagnosis is None or not isinstance(cur_diagnosis, NamedDiagnosis):
            print(f'Tried to add new treatment, but no diagnosis is set: {cur_diagnosis}')
            return
        start_date = self._ui.editPatient_t3_startDate.dateTime().toPyDateTime()
        end_date = self._ui.editPatient_t4_endDate.dateTime().toPyDateTime()
        instructions = self._ui.editPatient_t5_scriptInstructions.text()

        worker = run_in_pool(self._pool, order_prescription, cur_diagnosis.patient_id, cur_diagnosis.disease_id,
                             treatment_to_add, start_date, end_date, instructions)
        worker.signals.finished.connect(lambda: run_in_pool(self._pool, get_all_patients, cur_diagnosis.patient_id))

    def on_doctor_order_test(self):
        """
        Called when a doctor orders a test
        :return:
        """
        cur_test = self._ui.activeTests_OrderTestDropdown.currentData()
        if cur_test is None or not isinstance(cur_test, LabTest):
            print('No LabTest selected')
            return
        cur_doctor = self._ui.doctorSelectList_2.currentData()
        if cur_doctor is None or not isinstance(cur_doctor, BaseDoctor):
            print('No Doctor selected')
            return
        cur_patient = self._ui.patientSelectList_2.currentData()
        if cur_patient is None or not isinstance(cur_patient, Patient):
            print('No Patient selected')
            return

        print('Running order test in pool')
        worker = run_in_pool(self._pool, order_lab_test, cur_patient, cur_doctor, cur_test)
        worker.signals.finished.connect(lambda: run_in_pool(self._pool, get_tests_for_patient, cur_patient, cur_doctor))

    def on_make_appointment(self):
        """
        Called when a patient makes an appointment, gets cur time, doctor, and patient and sends to DB
        :return:
        """
        cur_appt = self._ui.editPatient_t3_drAvailability.currentData()
        if cur_appt is None:
            print('No Availability Selected')
            return
        cur_doctor = self._ui.doctorSelectList_1.currentData()
        if cur_doctor is None or not isinstance(cur_doctor, BaseDoctor):
            print('No Doctor selected')
            return
        cur_patient = self._ui.patientSelectList_1.currentData()
        if cur_patient is None or not isinstance(cur_patient, Patient):
            print('No Patient selected')
            return
        cur_description = self._ui.editPatient_t4_description.text()

        print('Running make appointment in pool')
        worker = run_in_pool(self._pool, make_appointment, cur_patient, cur_doctor, cur_appt, cur_description)
        worker.signals.finished.connect(lambda: self.see_pt_appointments())

    def on_admin_update_appointment(self):
        """
        Called when an admin checks in a patient for an appointment
        :return:
        """
        cur_patient = self._ui.updateAppointment_t1_name.currentData()
        if cur_patient is None or not isinstance(cur_patient, Patient):
            print('No Patient selected')
            return
        cur_appointment = self._ui.updateAppointment_t2_time.currentData()
        if cur_appointment is None:
            print('No Appointment selected')
            return
        cur_status = self._ui.updateAppointment_t3_status.currentText()
        if cur_status is None or cur_status == "- Select Status -":
            print('No Status selected')
            return

        print('Updating test status in pool')
        worker = run_in_pool(self._pool, update_appointment_status, cur_appointment, cur_status)
        worker.signals.finished.connect(lambda: run_in_pool(self._pool, get_appointments, cur_patient))

    def setup_connections(self) -> None:
        db_params: DBCredentials = DBCredentials(
            user=self.config.User,
            passwd=self.config.Password,
            host=self.config.Host,
            db_name=self.config.Database
        )
        DatabaseManager.connect(db_params)


def create_app():
    return QApplication(sys.argv)


def run_app(app: QApplication) -> int:
    main_window = MainWindow()
    main_window.show()
    ret_code = app.exec()

    # Shutdown logic
    DatabaseManager.shutdown()
    return ret_code
