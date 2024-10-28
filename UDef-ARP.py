import sys
import os
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt,QUrl
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox, QProgressDialog, QApplication, QWidget
from PyQt5.QtGui import QFontDatabase, QIcon, QFont, QDesktopServices
from PyQt5.uic import loadUi
from allocation_tool import AllocationTool
from vulnerability_map import VulnerabilityMap
from model_evaluation import ModelEvaluation
from osgeo import gdal
from pathlib import Path, PureWindowsPath
import numpy as np

# GDAL exceptions
gdal.UseExceptions()

class IntroScreen(QDialog):
    def __init__(self):
        super(IntroScreen, self).__init__()
        loadUi(Path(PureWindowsPath("data\\intro_screen.ui")), self)
        # Set window properties
        self.setWindowTitle('JNR Allocated Risk Mapping Procedure (UDef-ARP)')
        # Set window icon
        self.setWindowIcon(QIcon(str(Path(PureWindowsPath("data\\icon.ico")))))
        self.Fit_Cal_button.clicked.connect(self.gotofitcal)
        self.Pre_Cnf_button.clicked.connect(self.gotoprecnf)
        self.Fit_Hrp_button.clicked.connect(self.gotofithrp)
        self.Pre_VP_button.clicked.connect(self.gotoprevp)
        self.doc_button.clicked.connect(self.openDocument)

    def gotofitcal(self):
        rmt_fit_cal = RMT_FIT_CAL_SCREEN()
        widget.addWidget(rmt_fit_cal)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotoprecnf(self):
        rmt_pre_cnf = RMT_PRE_CNF_SCREEN()
        widget.addWidget(rmt_pre_cnf)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotofithrp(self):
        rmt_fit_hrp = RMT_FIT_HRP_SCREEN()
        widget.addWidget(rmt_fit_hrp)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotoprevp(self):
        rmt_pre_vp = RMT_PRE_VP_SCREEN()
        widget.addWidget(rmt_pre_vp)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def openDocument(self):
        pdf_path = Path(PureWindowsPath("doc\\UDef-ARP_Introduction.pdf"))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

class RMT_FIT_CAL_SCREEN(QDialog):
    def __init__(self):
        super(RMT_FIT_CAL_SCREEN, self).__init__()
        # Store the initial directory path
        self.initial_directory = os.getcwd()
        loadUi(Path(PureWindowsPath("data\\rmt_fit_cal_screen.ui")), self)
        if central_data_store.directory is not None and self.folder_entry is not None:
            self.directory = central_data_store.directory
            self.folder_entry.setText(str(central_data_store.directory))
        if central_data_store.directory is not None and self.folder_entry_2 is not None:
            self.directory_2 = central_data_store.directory
            self.folder_entry_2.setText(str(central_data_store.directory))
        self.AT_button2.clicked.connect(self.gotoat2)
        self.Intro_button2.clicked.connect(self.gotointro2)
        self.MCT_button2.clicked.connect(self.gotomct2)
        self.doc_button = self.tab1.findChild(QWidget, "doc_button")
        self.select_folder_button = self.tab1.findChild(QWidget, "select_folder_button")
        self.deforestation_hrp_button = self.tab1.findChild(QWidget, "deforestation_hrp_button")
        self.mask_button = self.tab1.findChild(QWidget, "mask_button")
        self.fd_button = self.tab1.findChild(QWidget, "fd_button")
        self.calculate_button2 = self.tab1.findChild(QWidget, "calculate_button2")
        self.ok_button2 = self.tab1.findChild(QWidget, "ok_button2")

        self.doc_button_2 = self.tab2.findChild(QWidget, "doc_button_2")
        self.select_folder_button_2 = self.tab2.findChild(QWidget, "select_folder_button_2")
        self.mask_button_2 = self.tab2.findChild(QWidget, "mask_button_2")
        self.fmask_button_2 = self.tab2.findChild(QWidget, "fmask_button_2")
        self.fd_button_2 = self.tab2.findChild(QWidget, "fd_button_2")
        self.ok_button2_2 = self.tab2.findChild(QWidget, "ok_button2_2")

        self.doc_button.clicked.connect(self.openDocument)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.deforestation_hrp_button.clicked.connect(self.select_deforestation_hrp)
        self.mask_button.clicked.connect(self.select_mask)
        self.fd_button.clicked.connect(self.select_fd)
        self.calculate_button2.clicked.connect(self.process_data2_nrt)
        self.ok_button2.clicked.connect(self.process_data2)

        self.doc_button_2.clicked.connect(self.openDocument_2)
        self.select_folder_button_2.clicked.connect(self.select_working_directory_2)
        self.mask_button_2.clicked.connect(self.select_mask_2)
        self.fmask_button_2.clicked.connect(self.select_fmask_2)
        self.fd_button_2.clicked.connect(self.select_fd_2)
        self.ok_button2_2.clicked.connect(self.process_data2_2)

        self.vulnerability_map = VulnerabilityMap()
        self.vulnerability_map.progress_updated.connect(self.update_progress)
        self.directory = None
        self.in_fn = None
        self.deforestation_hrp = None
        self.mask = None
        self.NRT = None
        if central_data_store.NRT is not None:
            self.nrt_entry.setText(str(central_data_store.NRT))
        self.n_classes = None
        self.out_fn = None
        self.out_fn_entry.setPlaceholderText('e.g., Acre_Vulnerability_CAL.tif')
        self.directory_2 = None
        self.mask_2 = None
        self.fmask_2 = None
        self.in_fn_2 = None
        self.out_fn_2 = None
        self.n_classes_2 = None
        self.out_fn_entry_2.setPlaceholderText('e.g., Acre_Vulnerability_CAL.tif')
        self.setWindowTitle("JNR Integrated Risk/Allocation Tool")

    def gotoat2(self):
        os.chdir(self.initial_directory)
        at2 = AT_FIT_CAL_Screen()
        widget.addWidget(at2)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotomct2(self):
        os.chdir(self.initial_directory)
        mct2 = MCT_FIT_CAL_Screen()
        widget.addWidget(mct2)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotointro2(self):
        os.chdir(self.initial_directory)
        intro2 = IntroScreen()
        widget.addWidget(intro2)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def openDocument(self):
        pdf_path = Path(PureWindowsPath("doc\\TestFitVM.pdf"))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def openDocument_2(self):
        pdf_path = Path(PureWindowsPath("doc\\TestFitVM.pdf"))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path = Path(data_folder)
        self.directory = str(data_folder_path)
        self.folder_entry.setText(self.directory)
        self.folder_entry_2.setText(self.directory)
        central_data_store.directory = self.directory

    def select_fd(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Map of Distance from the Forest Edge in CAL')
        if file_path:
            self.in_fn = file_path
            self.in_fn_entry.setText(file_path.split('/')[-1])

    def select_deforestation_hrp(self):
        file_path3, _ = QFileDialog.getOpenFileName(self, "Map of Deforestation in the CAL")
        if file_path3:
            self.deforestation_hrp = file_path3
            self.deforestation_hrp_entry.setText(file_path3.split('/')[-1])

    def select_mask(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Mask of Study Area')
        if file_path:
            self.mask = file_path
            self.mask_entry.setText(file_path.split('/')[-1])

    def select_working_directory_2(self):
        data_folder_2 = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path_2 = Path(data_folder_2)
        self.directory_2 = str(data_folder_path_2)
        self.folder_entry_2.setText(self.directory_2)
        self.folder_entry.setText(self.directory_2)
        central_data_store.directory = self.directory_2

    def select_fd_2(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Map of Distance from the Forest Edge in CAL')
        if file_path:
            self.in_fn_2 = file_path
            self.in_fn_entry_2.setText(file_path.split('/')[-1])

    def select_mask_2(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Mask of Study Area')
        if file_path:
            self.mask_2 = file_path
            self.mask_entry_2.setText(file_path.split('/')[-1])

    def select_fmask_2(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Mask of Forest Area')
        if file_path:
            self.fmask_2 = file_path
            self.fmask_entry_2.setText(file_path.split('/')[-1])

    def process_data2_nrt(self):
        directory = self.folder_entry.text()
        if not directory:
            QMessageBox.critical(self, "Error", "Please select the working directory!")
            return

        if not self.in_fn or not self.deforestation_hrp or not self.mask:
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        images = [self.in_fn, self.deforestation_hrp, self.mask]

        # Check if all images have the same resolution
        resolutions = [map_checker.get_image_resolution(img) for img in images]
        if len(set(resolutions)) != 1:
            QMessageBox.critical(None, "Error", "All the input raster images must have the same spatial resolution!")
            return

        # Check if all images have the same number of rows and columns
        dimensions = [map_checker.get_image_dimensions(img) for img in images]
        if len(set(dimensions)) != 1:
            QMessageBox.critical(None, "Error",
                                 "All the input raster images must have the same number of rows and columns!")
            return

        if not map_checker.check_binary_map(self.deforestation_hrp):
            QMessageBox.critical(None, "Error",
                                 "'MAP OF DEFORESTATION IN THE HRP' must be a binary map (0 and 1) where the 1’s indicate deforestation.")
            return

        if not map_checker.check_binary_map(self.mask):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF THE JURISDICTION' must be a binary map (0 and 1) where the 1’s indicate jurisdiction.")
            return

        # Show "Processing" message
        processing_message = "Calculating NRT..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Calculating")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.vulnerability_map.set_working_directory(directory)
            NRT = self.vulnerability_map.nrt_calculation(self.in_fn, self.deforestation_hrp, self.mask)
            # Update the central data store
            central_data_store.NRT = NRT

            QMessageBox.information(self, "Processing Completed", f"Processing completed!\nNRT is: {NRT}")

            self.nrt_entry.setText(str(NRT))

            self.progressDialog.close()

        except Exception as e:
            self.progressDialog.close()
            QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def process_data2(self):
        directory = self.folder_entry.text()
        if not directory:
            QMessageBox.critical(self, "Error", "Please select the working directory!")
            return

        if not self.in_fn or not self.mask:
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        NRT = self.nrt_entry.text()
        if not NRT:
            QMessageBox.critical(self, "Error", "Please enter the NRT value!")
            return
        try:
            self.NRT = int(NRT)
            if (self.NRT <= 0):
                QMessageBox.critical(self, "Error", "NRT value should be larger than 0!")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "NRT value should be a valid number!")
            return

        n_classes = int(29)
        if not n_classes:
            QMessageBox.critical(self, "Error", "Please enter the number of classes!")
            return
        try:
            self.n_classes = int(n_classes)
            if (self.n_classes <= 0):
                QMessageBox.critical(self, "Error", "Number of classes should be larger than 0!")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "Number of classes value should be a valid number!")
            return

        out_fn = self.out_fn_entry.text()
        if not out_fn:
            QMessageBox.critical(self, "Error", "Please enter the name of Vulnerability Map in CAL!")
            return

        # Check if the out_fn has the correct file extension
        if not (out_fn.endswith('.tif') or out_fn.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Vulnerability Map in CAL!")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.vulnerability_map.set_working_directory(directory)
            mask_arr = self.vulnerability_map.geometric_classification(self.in_fn, NRT, n_classes, self.mask)
            self.vulnerability_map.array_to_image(self.in_fn, out_fn, mask_arr, gdal.GDT_Int16, -1)
            self.vulnerability_map.replace_ref_system(self.in_fn, out_fn)

            QMessageBox.information(self, "Processing Completed", "Processing completed!")

            self.progressDialog.close()

        except Exception as e:
            self.progressDialog.close()
            QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")


    def process_data2_2(self):
        directory_2 = self.folder_entry_2.text()
        if not directory_2 :
            QMessageBox.critical(self, "Error", "Please select the working directory!")
            return

        if not self.in_fn_2 or not self.mask_2 or not self.fmask_2:
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        images = [self.in_fn_2, self.mask_2, self.fmask_2]

        # Check if all images have the same resolution
        resolutions = [map_checker.get_image_resolution(img) for img in images]
        if len(set(resolutions)) != 1:
            QMessageBox.critical(None, "Error", "All the input raster images must have the same spatial resolution!")
            return

        # Check if all images have the same number of rows and columns
        dimensions = [map_checker.get_image_dimensions(img) for img in images]
        if len(set(dimensions)) != 1:
            QMessageBox.critical(None, "Error",
                                 "All the input raster images must have the same number of rows and columns!")
            return

        n_classes_2 = int(30)
        out_fn_2 = self.out_fn_entry_2.text()
        if not out_fn_2:
            QMessageBox.critical(self, "Error", "Please enter the name of Vulnerability Map in CAL!")
            return

        # Check if the out_fn has the correct file extension
        if not (out_fn_2.endswith('.tif') or out_fn_2.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Vulnerability Map in CAL!")
            return

        if not map_checker.check_binary_map(self.fmask_2):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF FOREST AREAS IN THE CAL' must be a binary map (0 and 1) where the 1’s indicate forest areas.")
            return

        if not map_checker.check_binary_map(self.mask_2):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF THE NON-EXCLUDED JURISDICTION' must be a binary map (0 and 1) where the 1’s indicate areas inside the jurisdiction.")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.vulnerability_map.set_working_directory(directory_2)
            mask_arr = self.vulnerability_map.geometric_classification_alternative(self.in_fn_2, n_classes_2, self.mask_2, self.fmask_2)
            self.vulnerability_map.array_to_image(self.in_fn_2, out_fn_2, mask_arr, gdal.GDT_Int16, -1)
            self.vulnerability_map.replace_ref_system(self.in_fn_2, out_fn_2)

            QMessageBox.information(self, "Processing Completed", "Processing completed!")

            self.progressDialog.close()

        except Exception as e:
            self.progressDialog.close()
            QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def update_progress(self, value):
        # Update QProgressDialog with the new value
        if self.progressDialog is not None:
            self.progressDialog.setValue(value)

class AT_FIT_CAL_Screen(QDialog):
    def __init__(self):
        super(AT_FIT_CAL_Screen, self).__init__()
        self.initial_directory = os.getcwd()
        loadUi(Path(PureWindowsPath("data\\at_fit_cal_screen.ui")), self)
        if central_data_store.directory is not None and self.folder_entry is not None:
            self.directory = central_data_store.directory
            self.folder_entry.setText(str(central_data_store.directory))
        self.Intro_button3.clicked.connect(self.gotointro3)
        self.RMT_button3.clicked.connect(self.gotormt3)
        self.MCT_button3.clicked.connect(self.gotomct3)
        self.doc_button.clicked.connect(self.openDocument)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.municipality_button.clicked.connect(self.select_municipality)
        self.risk30_hrp_button.clicked.connect(self.select_risk30_hrp)
        self.deforestation_hrp_button.clicked.connect(self.select_deforestation_hrp)
        self.ok_button3.clicked.connect(self.process_data3)
        self.allocation_tool = AllocationTool()
        # Connect the progress_updated signal to the update_progress method
        self.allocation_tool.progress_updated.connect(self.update_progress)
        self.directory = None
        self.risk30_hrp = None
        self.municipality = None
        self.deforestation_hrp = None
        self.out_fn1 = None
        self.out_fn2 = None
        self.csv_name = None
        self.image1_entry.setPlaceholderText('e.g., Acre_Modeling_Region_CAL.tif')
        self.csv_entry.setPlaceholderText('e.g., Relative_Frequency_Table_CAL.csv')
        self.image2_entry.setPlaceholderText('e.g., Acre_Fitted_Density_Map_CAL.tif')
        self.setWindowTitle("JNR Integrated Risk/Allocation Tool")

    def gotormt3(self):
        os.chdir(self.initial_directory)
        rmt3 = RMT_FIT_CAL_SCREEN()
        widget.addWidget(rmt3)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotointro3(self):
        os.chdir(self.initial_directory)
        intro3 = IntroScreen()
        widget.addWidget(intro3)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotomct3(self):
        os.chdir(self.initial_directory)
        mct3 = MCT_FIT_CAL_Screen()
        widget.addWidget(mct3)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def openDocument(self):
        pdf_path = Path(PureWindowsPath("doc\\TestFitAM.pdf"))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path = Path(data_folder)
        self.directory = str(data_folder_path)
        self.folder_entry.setText(self.directory)
        central_data_store.directory = self.directory

    def select_municipality(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Map of Administrative Divisions')
        if file_path:
            self.municipality = file_path
            self.municipality_entry.setText(file_path.split('/')[-1])

    def select_risk30_hrp(self):
        file_path1, _ = QFileDialog.getOpenFileName(self, "Vulnerability Map in CAL")
        if file_path1:
            self.risk30_hrp = file_path1
            self.risk30_hrp_entry.setText(file_path1.split('/')[-1])

    def select_deforestation_hrp(self):
        file_path3, _ = QFileDialog.getOpenFileName(self, "Map of Deforestation in the CAL")
        if file_path3:
            self.deforestation_hrp = file_path3
            self.deforestation_hrp_entry.setText(file_path3.split('/')[-1])

    def process_data3(self):
        directory = self.folder_entry.text()
        if not directory:
            QMessageBox.critical(self, "Error", "Please select the working directory!")
            return

        if not self.risk30_hrp or not self.municipality or not self.deforestation_hrp:
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        images = [self.risk30_hrp, self.municipality, self.deforestation_hrp]

        # Check if all images have the same resolution
        resolutions = [map_checker.get_image_resolution(img) for img in images]
        if len(set(resolutions)) != 1:
            QMessageBox.critical(None, "Error", "All the input raster images must have the same spatial resolution!")
            return

        # Check if all images have the same number of rows and columns
        dimensions = [map_checker.get_image_dimensions(img) for img in images]
        if len(set(dimensions)) != 1:
            QMessageBox.critical(None, "Error",
                                 "All the input raster images must have the same number of rows and columns!")
            return

        out_fn1 = self.image1_entry.text()
        if not out_fn1:
            QMessageBox.critical(self, "Error", "Please enter the name for Modeling Region Map in CAL!")
            return

        if not (out_fn1.endswith('.tif') or out_fn1.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name for Modeling Region Map in CAL!")
            return

        csv_name = self.csv_entry.text()
        if not csv_name:
            QMessageBox.critical(self, "Error", "Please enter the name for the Relative Frequency Table!")
            return

        if not (csv_name.endswith('.csv')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .csv extension in the name of Relative Frequency Table!")
            return

        out_fn2 = self.image2_entry.text()
        if not out_fn2:
            QMessageBox.critical(self, "Error", "Please enter the name for Fitted Density Map in the CAL!")
            return

        if not (out_fn2.endswith('.tif') or out_fn2.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name for Fitted Density Map in the CAL!")
            return

        if not map_checker.check_binary_map(self.deforestation_hrp):
            QMessageBox.critical(None, "Error",
                                 "'MAP OF DEFORESTATION IN THE CAL' must be a binary map (0 and 1) where the 1’s indicate deforestation.")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.allocation_tool.execute_workflow_fit(directory, self.risk30_hrp,
                                                        self.municipality,self.deforestation_hrp, csv_name,
                                                        out_fn1,out_fn2)
            QMessageBox.information(self, "Processing Completed", "Processing completed!")
            self.progressDialog.close()

        except Exception as e:
             self.progressDialog.close()
             QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def update_progress(self, value):
        # Update QProgressDialog with the new value
        if self.progressDialog is not None:
            self.progressDialog.setValue(value)


class MCT_FIT_CAL_Screen(QDialog):
    def __init__(self):
        super(MCT_FIT_CAL_Screen, self).__init__()
        # Store the initial directory path
        self.initial_directory = os.getcwd()
        loadUi(Path(PureWindowsPath("data\\mct_fit_cal_screen.ui")), self)
        if central_data_store.directory is not None and self.folder_entry is not None:
            self.directory = central_data_store.directory
            self.folder_entry.setText(str(central_data_store.directory))
        self.AT_button4.clicked.connect(self.gotoat4)
        self.Intro_button4.clicked.connect(self.gotointro4)
        self.RMT_button4.clicked.connect(self.gotormt4)
        self.doc_button.clicked.connect(self.openDocument)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.mask_button.clicked.connect(self.select_mask)
        self.deforestation_hrp_button.clicked.connect(self.select_deforestation_hrp)
        self.density_button.clicked.connect(self.select_density)
        self.ok_button.clicked.connect(self.process_data4)
        self.model_evaluation = ModelEvaluation()
        self.model_evaluation.progress_updated.connect(self.update_progress)
        self.directory = None
        self.mask = None
        self.deforestation_hrp = None
        self.density = None
        self.grid_area = None
        self.grid_area_entry.setPlaceholderText('Type default 100000 or other number')
        self.title = None
        self.out_fn = None
        self.out_fn_entry.setPlaceholderText('e.g., Plot_CAL.png')
        self.raster_fn = None
        self.raster_fn_entry.setPlaceholderText('e.g., Acre_Residuals_CAL.tif')
        self.xmax = None
        self.xmax = None
        self.setWindowTitle("JNR Integrated Risk/Allocation Tool")

    def gotoat4(self):
        os.chdir(self.initial_directory)
        at4 = AT_FIT_CAL_Screen()
        widget.addWidget(at4)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotointro4(self):
        os.chdir(self.initial_directory)
        intro4 = IntroScreen()
        widget.addWidget(intro4)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotormt4(self):
        os.chdir(self.initial_directory)
        rmt4 = RMT_FIT_CAL_SCREEN()
        widget.addWidget(rmt4)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def openDocument(self):
        pdf_path = Path(PureWindowsPath("doc\\TestFitMA.pdf"))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path = Path(data_folder)
        self.directory = str(data_folder_path)
        self.folder_entry.setText(self.directory)
        central_data_store.directory = self.directory

    def select_mask(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Mask of Study Area')
        if file_path:
            self.mask = file_path
            self.mask_entry.setText(file_path.split('/')[-1])

    def select_deforestation_hrp(self):
        file_path3, _ = QFileDialog.getOpenFileName(self, "Map of Deforestation in the HRP")
        if file_path3:
            self.deforestation_hrp = file_path3
            self.deforestation_hrp_entry.setText(file_path3.split('/')[-1])

    def select_density(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Deforestation Density Map')
        if file_path:
            self.density = file_path
            self.density_entry.setText(file_path.split('/')[-1])

    def process_data4(self):
        directory = self.folder_entry.text()
        if not directory:
            QMessageBox.critical(self, "Error", "Please select the working directory!")
            return

        if not self.mask or not self.deforestation_hrp or not self.density :
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        images = [self.mask, self.deforestation_hrp, self.density]

        # Check if all images have the same resolution
        resolutions = [map_checker.get_image_resolution(img) for img in images]
        if len(set(resolutions)) != 1:
            QMessageBox.critical(None, "Error", "All the input raster images must have the same spatial resolution!")
            return

        # Check if all images have the same number of rows and columns
        dimensions = [map_checker.get_image_dimensions(img) for img in images]
        if len(set(dimensions)) != 1:
            QMessageBox.critical(None, "Error",
                                 "All the input raster images must have the same number of rows and columns!")
            return

        grid_area = self.grid_area_entry.text()
        if not grid_area:
            QMessageBox.critical(self, "Error", "Please enter the thiessen polygon grid area value!")
            return
        try:
            self.grid_area = float(grid_area)
            if not (0 < self.grid_area):
                QMessageBox.critical(self, "Error", "Thiessen polygon grid area value should larger than 0!")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "Thiessen polygon grid area value should be a valid number!")
            return


        xmax = self.xmax_entry.text()
        if xmax.lower() != "default":
            try:
                xmax = float(xmax)
                if xmax <= 0:
                    raise ValueError("The plot x-axis limit should be larger than 0!")
            except ValueError:
                QMessageBox.critical(self, "Error", "The plot x-axis limit should be a valid number or 'Default'!")
                return

        ymax = self.ymax_entry.text()
        if ymax.lower() != "default":
            try:
                ymax = float(ymax)
                if ymax <= 0:
                    raise ValueError("The plot y-axis limit should be larger than 0!")
            except ValueError:
                QMessageBox.critical(self, "Error", "The plot y-axis limit should be a valid number or 'Default'!")
                return

        title = self.title_entry.text()
        if not title:
            QMessageBox.critical(self, "Error", "Please enter the title of plot!")
            return

        out_fn = self.out_fn_entry.text()
        if not out_fn:
            QMessageBox.critical(self, "Error", "Please enter the name of plot!")
            return

        # Check if the out_fn has the correct file extension
        if not (out_fn.endswith('.png') or out_fn.endswith('.jpg') or out_fn.endswith('.pdf') or out_fn.endswith(
                '.svg') or out_fn.endswith('.eps') or out_fn.endswith('.ps') or out_fn.endswith('.tif')):
            QMessageBox.critical(self, "Error",
                                 "Please enter extension(.png/.jpg/.pdf/.svg/.eps/.ps/.tif) in the name of plot!")
            return

        raster_fn = self.raster_fn_entry.text()
        if not raster_fn:
            QMessageBox.critical(self, "Error", "Please enter the name for Residual Map!")
            return

        if not (raster_fn.endswith('.tif') or raster_fn.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Residual Map!")
            return

        if not map_checker.check_binary_map(self.mask):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF THE NON-EXCLUDED JURISDICTION' must be a binary map (0 and 1) where the 1’s indicate areas inside the jurisdiction.")
            return

        if not map_checker.check_binary_map(self.deforestation_hrp):
            QMessageBox.critical(None, "Error",
                                 "'MAP OF DEFORESTATION IN THE CAL' must be a binary map (0 and 1) where the 1’s indicate deforestation.")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.model_evaluation.set_working_directory(directory)
            self.model_evaluation.create_mask_polygon(self.mask)
            clipped_gdf = self.model_evaluation.create_thiessen_polygon(self.grid_area, self.mask,self.density, self.deforestation_hrp, out_fn,raster_fn)
            self.model_evaluation.replace_ref_system(self.mask, raster_fn)
            self.model_evaluation.create_plot(grid_area,clipped_gdf, title, out_fn, xmax, ymax)
            self.model_evaluation.remove_temp_files()

            QMessageBox.information(self, "Processing Completed", "Processing completed!")
            self.progressDialog.close()

        except Exception as e:
             self.progressDialog.close()
             QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def update_progress(self, value):
        # Update QProgressDialog with the new value
        if self.progressDialog is not None:
            self.progressDialog.setValue(value)

class RMT_PRE_CNF_SCREEN(QDialog):
    def __init__(self):
        super(RMT_PRE_CNF_SCREEN, self).__init__()
        # Store the initial directory path
        self.initial_directory = os.getcwd()
        loadUi(Path(PureWindowsPath("data\\rmt_pre_cnf_screen.ui")), self)
        if central_data_store.directory is not None and self.folder_entry is not None:
            self.directory = central_data_store.directory
            self.folder_entry.setText(str(central_data_store.directory))
        if central_data_store.directory is not None and self.folder_entry_2 is not None:
            self.directory_2 = central_data_store.directory
            self.folder_entry_2.setText(str(central_data_store.directory))
        self.AT_button2.clicked.connect(self.gotoat2)
        self.Intro_button2.clicked.connect(self.gotointro2)
        self.MCT_button2.clicked.connect(self.gotomct2)
        self.doc_button = self.tab1.findChild(QWidget, "doc_button")
        self.select_folder_button = self.tab1.findChild(QWidget, "select_folder_button")
        self.fd_button = self.tab1.findChild(QWidget, "fd_button")
        self.mask_button = self.tab1.findChild(QWidget, "mask_button")
        self.ok_button2 = self.tab1.findChild(QWidget, "ok_button2")

        self.doc_button_2 = self.tab2.findChild(QWidget, "doc_button_2")
        self.select_folder_button_2 = self.tab2.findChild(QWidget, "select_folder_button_2")
        self.mask_button_2 = self.tab2.findChild(QWidget, "mask_button_2")
        self.fmask_button_2 = self.tab2.findChild(QWidget, "fmask_button_2")
        self.fd_button_2 = self.tab2.findChild(QWidget, "fd_button_2")
        self.ok_button2_2 = self.tab2.findChild(QWidget, "ok_button2_2")

        self.doc_button.clicked.connect(self.openDocument)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.fd_button.clicked.connect(self.select_fd)
        self.mask_button.clicked.connect(self.select_mask)
        self.ok_button2.clicked.connect(self.process_data2)

        self.doc_button_2.clicked.connect(self.openDocument_2)
        self.select_folder_button_2.clicked.connect(self.select_working_directory_2)
        self.mask_button_2.clicked.connect(self.select_mask_2)
        self.fmask_button_2.clicked.connect(self.select_fmask_2)
        self.fd_button_2.clicked.connect(self.select_fd_2)
        self.ok_button2_2.clicked.connect(self.process_data2_2)

        self.vulnerability_map = VulnerabilityMap()
        self.vulnerability_map.progress_updated.connect(self.update_progress)
        self.directory = None
        self.in_fn = None
        self.NRT = None
        self.mask = None
        # Use NRT from the data store
        if central_data_store.NRT is not None:
            self.nrt_entry.setText(str(central_data_store.NRT))
        self.n_classes = None
        self.out_fn = None
        self.out_fn_entry.setPlaceholderText('e.g., Acre_Vulnerability_CNF.tif')

        self.directory_2 = None
        self.mask_2 = None
        self.fmask_2 = None
        self.in_fn_2 = None
        self.out_fn_2 = None
        self.n_classes_2 = None
        self.out_fn_entry_2.setPlaceholderText('e.g., Acre_Vulnerability_CNF.tif')

        self.setWindowTitle("JNR Integrated Risk/Allocation Tool")

    def gotoat2(self):
        os.chdir(self.initial_directory)
        at2 = AT_PRE_CNF_Screen()
        widget.addWidget(at2)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotomct2(self):
        os.chdir(self.initial_directory)
        mct2 = MCT_PRE_CNF_Screen()
        widget.addWidget(mct2)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotointro2(self):
        os.chdir(self.initial_directory)
        intro2 = IntroScreen()
        widget.addWidget(intro2)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def openDocument(self):
        pdf_path = Path(PureWindowsPath("doc\\TestPreVM.pdf"))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def openDocument_2(self):
        pdf_path = Path(PureWindowsPath("doc\\TestPreVM.pdf"))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path = Path(data_folder)
        self.directory = str(data_folder_path)
        self.folder_entry.setText(self.directory)
        self.folder_entry_2.setText(self.directory)
        central_data_store.directory = self.directory

    def select_fd(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Map of Distance from the Forest Edge in CNF')
        if file_path:
            self.in_fn = file_path
            self.in_fn_entry.setText(file_path.split('/')[-1])
    def select_mask(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Mask of Study Area')
        if file_path:
            self.mask = file_path
            self.mask_entry.setText(file_path.split('/')[-1])

    def select_working_directory_2(self):
        data_folder_2 = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path_2 = Path(data_folder_2)
        self.directory_2 = str(data_folder_path_2)
        self.folder_entry_2.setText(self.directory_2)
        self.folder_entry.setText(self.directory_2)
        central_data_store.directory = self.directory_2

    def select_fd_2(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Map of Distance from the Forest Edge in CNF')
        if file_path:
            self.in_fn_2 = file_path
            self.in_fn_entry_2.setText(file_path.split('/')[-1])

    def select_mask_2(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Mask of Study Area')
        if file_path:
            self.mask_2 = file_path
            self.mask_entry_2.setText(file_path.split('/')[-1])

    def select_fmask_2(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Mask of Forest Area')
        if file_path:
            self.fmask_2 = file_path
            self.fmask_entry_2.setText(file_path.split('/')[-1])

    def process_data2(self):
        directory = self.folder_entry.text()
        if not directory:
            QMessageBox.critical(self, "Error", "Please select the working directory!")
            return

        if not self.in_fn or not self.mask:
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        NRT = self.nrt_entry.text()
        if not NRT:
            QMessageBox.critical(self, "Error", "Please enter the NRT value!")
            return
        try:
            self.NRT = int(NRT)
            if (self.NRT <= 0):
                QMessageBox.critical(self, "Error", "NRT value should be larger than 0!")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "NRT value should be a valid number!")
            return

        n_classes = int(29)
        if not n_classes:
            QMessageBox.critical(self, "Error", "Please enter the number of classes!")
            return
        try:
            self.n_classes = int(n_classes)
            if (self.n_classes <= 0):
                QMessageBox.critical(self, "Error", "Number of classes should be larger than 0!")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "Number of classes value should be a valid number!")
            return

        out_fn = self.out_fn_entry.text()
        if not out_fn:
            QMessageBox.critical(self, "Error", "Please enter the name of Vulnerability Map in CNF!")
            return

        if not (out_fn.endswith('.tif') or out_fn.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Vulnerability Map in CNF!")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.vulnerability_map.set_working_directory(directory)
            mask_arr = self.vulnerability_map.geometric_classification(self.in_fn, NRT, n_classes, self.mask)
            self.vulnerability_map.array_to_image(self.in_fn, out_fn, mask_arr, gdal.GDT_Int16, -1)
            self.vulnerability_map.replace_ref_system(self.in_fn, out_fn)

            QMessageBox.information(self, "Processing Completed", "Processing completed!")
            self.progressDialog.close()

        except Exception as e:
            self.progressDialog.close()
            QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def process_data2_2(self):
        directory_2 = self.folder_entry_2.text()
        if not directory_2 :
            QMessageBox.critical(self, "Error", "Please select the working directory!")
            return

        if not self.in_fn_2 or not self.mask_2 or not self.fmask_2:
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        images = [self.in_fn_2, self.mask_2, self.fmask_2]

        # Check if all images have the same resolution
        resolutions = [map_checker.get_image_resolution(img) for img in images]
        if len(set(resolutions)) != 1:
            QMessageBox.critical(None, "Error", "All the input raster images must have the same spatial resolution!")
            return

        # Check if all images have the same number of rows and columns
        dimensions = [map_checker.get_image_dimensions(img) for img in images]
        if len(set(dimensions)) != 1:
            QMessageBox.critical(None, "Error",
                                 "All the input raster images must have the same number of rows and columns!")
            return

        n_classes_2 = int(30)
        out_fn_2 = self.out_fn_entry_2.text()
        if not out_fn_2:
            QMessageBox.critical(self, "Error", "Please enter the name of Vulnerability Map in CNF!")
            return

        # Check if the out_fn has the correct file extension
        if not (out_fn_2.endswith('.tif') or out_fn_2.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Vulnerability Map in CNF!")
            return

        if not map_checker.check_binary_map(self.fmask_2):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF FOREST AREAS IN THE CNF' must be a binary map (0 and 1) where the 1’s indicate forest areas.")
            return

        if not map_checker.check_binary_map(self.mask_2):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF THE NON-EXCLUDED JURISDICTION' must be a binary map (0 and 1) where the 1’s indicate areas inside the jurisdiction.")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.vulnerability_map.set_working_directory(directory_2)
            mask_arr = self.vulnerability_map.geometric_classification_alternative(self.in_fn_2, n_classes_2,
                                                                                   self.mask_2, self.fmask_2)
            self.vulnerability_map.array_to_image(self.in_fn_2, out_fn_2, mask_arr, gdal.GDT_Int16, -1)
            self.vulnerability_map.replace_ref_system(self.in_fn_2, out_fn_2)

            QMessageBox.information(self, "Processing Completed", "Processing completed!")

            self.progressDialog.close()

        except Exception as e:
            self.progressDialog.close()
            QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def update_progress(self, value):
        # Update QProgressDialog with the new value
        if self.progressDialog is not None:
            self.progressDialog.setValue(value)

class AT_PRE_CNF_Screen(QDialog):
    def __init__(self):
        super(AT_PRE_CNF_Screen, self).__init__()
        self.initial_directory = os.getcwd()
        loadUi(Path(PureWindowsPath("data\\at_pre_cnf_screen.ui")), self)
        if central_data_store.directory is not None and self.folder_entry is not None:
            self.directory = central_data_store.directory
            self.folder_entry.setText(str(central_data_store.directory))
        self.Intro_button3.clicked.connect(self.gotointro3)
        self.RMT_button3.clicked.connect(self.gotormt3)
        self.MCT_button3.clicked.connect(self.gotomct3)
        self.doc_button.clicked.connect(self.openDocument)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.municipality_button.clicked.connect(self.select_municipality)
        self.csv_button.clicked.connect(self.select_csv)
        self.risk30_vp_button.clicked.connect(self.select_risk30_vp)
        self.deforestation_cnf_button.clicked.connect(self.select_deforestation_cnf)
        self.ok_button3.clicked.connect(self.process_data3)
        self.allocation_tool = AllocationTool()
        self.allocation_tool.progress_updated.connect(self.update_progress)
        self.directory = None
        self.csv = None
        self.municipality = None
        self.risk30_vp = None
        self.deforestation_cnf = None
        self.max_iterations = None
        self.image1 = None
        self.image2 = None
        self.iteration_entry.setPlaceholderText('The suggestion max iteration number is 5')
        self.image1_entry.setPlaceholderText('e.g., Acre_Prediction_Modeling_Region_CNF.tif')
        self.image2_entry.setPlaceholderText('e.g., Acre_Adjucted_Density_Map_CNF.tif')
        self.setWindowTitle("JNR Integrated Risk/Allocation Tool")

    def gotormt3(self):
        os.chdir(self.initial_directory)
        rmt3 = RMT_PRE_CNF_SCREEN()
        widget.addWidget(rmt3)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotointro3(self):
        os.chdir(self.initial_directory)
        intro3 = IntroScreen()
        widget.addWidget(intro3)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotomct3(self):
        os.chdir(self.initial_directory)
        mct3 = MCT_PRE_CNF_Screen()
        widget.addWidget(mct3)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def openDocument(self):
        pdf_path = Path(PureWindowsPath("doc\\TestPreAM.pdf"))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path = Path(data_folder)
        self.directory = str(data_folder_path)
        self.folder_entry.setText(self.directory)
        central_data_store.directory = self.directory

    def select_municipality(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Map of Administrative Divisions')
        if file_path:
            self.municipality = file_path
            self.municipality_entry.setText(file_path.split('/')[-1])

    def select_csv(self):
        file_path1, _ = QFileDialog.getOpenFileName(self, "CAL Relative Frequency Table (.csv)")
        if file_path1:
            self.csv = file_path1
            self.csv_entry.setText(file_path1.split('/')[-1])

    def select_risk30_vp(self):
        file_path2, _ = QFileDialog.getOpenFileName(self, "Vulnerability Map in CNF")
        if file_path2:
            self.risk30_vp = file_path2
            self.risk30_vp_entry.setText(file_path2.split('/')[-1])

    def select_deforestation_cnf(self):
        file_path3, _ = QFileDialog.getOpenFileName(self, "Map of Deforestation in CNF")
        if file_path3:
            self.deforestation_cnf = file_path3
            self.deforestation_cnf_entry.setText(file_path3.split('/')[-1])

    def process_data3(self):
        directory = self.folder_entry.text()
        if not directory:
            QMessageBox.critical(self, "Error", "Please select the working directory!")
            return

        if not self.municipality or not self.csv or not self.deforestation_cnf or not self.risk30_vp:
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        images = [self.municipality, self.deforestation_cnf, self.risk30_vp]

        # Check if all images have the same resolution
        resolutions = [map_checker.get_image_resolution(img) for img in images]
        if len(set(resolutions)) != 1:
            QMessageBox.critical(None, "Error", "All the input raster images must have the same spatial resolution!")
            return

        # Check if all images have the same number of rows and columns
        dimensions = [map_checker.get_image_dimensions(img) for img in images]
        if len(set(dimensions)) != 1:
            QMessageBox.critical(None, "Error",
                                 "All the input raster images must have the same number of rows and columns!")
            return

        out_fn1 = self.image1_entry.text()
        if not out_fn1:
            QMessageBox.critical(self, "Error", "Please enter the name of Prediction Modeling Region Map in CNF!")
            return

        if not (out_fn1.endswith('.tif') or out_fn1.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Prediction Modeling Region Map in CNF!")
            return

        out_fn2 = self.image2_entry.text()
        if not out_fn2:
            QMessageBox.critical(self, "Error", "Please enter the name of Adjusted Prediction Density Map in CNF!")
            return

        if not (out_fn2.endswith('.tif') or out_fn2.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Adjusted Prediction Density Map in CNF!")
            return

        max_iterations = self.iteration_entry.text()
        if not max_iterations:
            QMessageBox.critical(self, "Error", "Please enter the max iterations! The suggestion number is 5.")
            return
        try:
            self.max_iterations = int(max_iterations)
        except ValueError:
            QMessageBox.critical(self, "Error", "Max iteration value should be a valid number!")
            return

        if not map_checker.check_binary_map(self.deforestation_cnf):
            QMessageBox.critical(None, "Error",
                                 "'MAP OF DEFORESTATION IN THE CNF' must be a binary map (0 and 1) where the 1’s indicate deforestation.")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            id_difference,iteration_count = self.allocation_tool.execute_workflow_cnf(directory,
                                                            self.max_iterations, self.csv,
                                                            self.municipality,
                                                            self.deforestation_cnf,
                                                            self.risk30_vp, out_fn1,
                                                            out_fn2)
            if id_difference.size > 0:
                QMessageBox.warning(self, " Warning ", f"Modeling Region ID {','.join(map(str, id_difference))} do not exist in the Calculation Period. A new CSV has been created for the CAL where relative frequencies for missing bins have been estimated from corresponding vulnerability zones over the entire jurisdiction.")
            if iteration_count > int(max_iterations):
                QMessageBox.warning(self, " Warning ", f"Maximum iterations limit reached. Please increase the Maximum Iterations and try running the tool again.")
            else:
                QMessageBox.information(self, "Processing Completed", "Processing completed!")
            self.progressDialog.close()

        except Exception as e:
             self.progressDialog.close()
             QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def update_progress(self, value):
        # Update QProgressDialog with the new value
        if self.progressDialog is not None:
            self.progressDialog.setValue(value)

class MCT_PRE_CNF_Screen(QDialog):
    def __init__(self):
        super(MCT_PRE_CNF_Screen, self).__init__()
        # Store the initial directory path
        self.initial_directory = os.getcwd()
        loadUi(Path(PureWindowsPath("data\\mct_pre_cnf_screen.ui")), self)
        if central_data_store.directory is not None and self.folder_entry is not None:
            self.directory = central_data_store.directory
            self.folder_entry.setText(str(central_data_store.directory))
        self.AT_button4.clicked.connect(self.gotoat4)
        self.Intro_button4.clicked.connect(self.gotointro4)
        self.RMT_button4.clicked.connect(self.gotormt4)
        self.doc_button.clicked.connect(self.openDocument)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.mask_button.clicked.connect(self.select_mask)
        self.fmask_button.clicked.connect(self.select_fmask)
        self.deforestation_cal_button.clicked.connect(self.select_deforestation_cal)
        self.deforestation_hrp_button.clicked.connect(self.select_deforestation_hrp)
        self.density_button.clicked.connect(self.select_density)
        self.ok_button.clicked.connect(self.process_data4)
        self.model_evaluation = ModelEvaluation()
        self.model_evaluation.progress_updated.connect(self.update_progress)
        self.directory = None
        self.mask = None
        self.fmask = None
        self.deforestation_cal = None
        self.deforestation_hrp = None
        self.density = None
        self.grid_area = None
        self.grid_area_entry.setPlaceholderText('Type default 100000 or other number')
        self.title = None
        self.out_fn = None
        self.out_fn_def = None
        self.raster_fn = None
        self.out_fn_entry.setPlaceholderText('e.g., Plot_CNF.png')
        self.out_fn_def_entry.setPlaceholderText('e.g., Acre_Def_Review.tif')
        self.raster_fn_entry.setPlaceholderText('e.g., Acre_Residuals_CNF.tif')
        self.setWindowTitle("JNR Integrated Risk/Allocation Tool")

    def gotoat4(self):
        os.chdir(self.initial_directory)
        at4 = AT_PRE_CNF_Screen()
        widget.addWidget(at4)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotointro4(self):
        os.chdir(self.initial_directory)
        intro4 = IntroScreen()
        widget.addWidget(intro4)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotormt4(self):
        os.chdir(self.initial_directory)
        rmt4 = RMT_PRE_CNF_SCREEN()
        widget.addWidget(rmt4)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def openDocument(self):
        pdf_path = Path(PureWindowsPath("doc\\TestPreMA.pdf"))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path = Path(data_folder)
        self.directory = str(data_folder_path)
        self.folder_entry.setText(self.directory)
        central_data_store.directory = self.directory

    def select_mask(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Mask of Study Area')
        if file_path:
            self.mask = file_path
            self.mask_entry.setText(file_path.split('/')[-1])

    def select_fmask(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Mask of Forest Area')
        if file_path:
            self.fmask = file_path
            self.fmask_entry.setText(file_path.split('/')[-1])

    def select_deforestation_cal(self):
        file_path3, _ = QFileDialog.getOpenFileName(self, "Actual Deforestation Map in CAL")
        if file_path3:
            self.deforestation_cal = file_path3
            self.deforestation_cal_entry.setText(file_path3.split('/')[-1])

    def select_deforestation_hrp(self):
        file_path3, _ = QFileDialog.getOpenFileName(self, "Actual Deforestation Map in CNF")
        if file_path3:
            self.deforestation_hrp = file_path3
            self.deforestation_hrp_entry.setText(file_path3.split('/')[-1])

    def select_density(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Adjusted Prediction Density Map in CNF')
        if file_path:
            self.density = file_path
            self.density_entry.setText(file_path.split('/')[-1])

    def process_data4(self):
        directory = self.folder_entry.text()
        if not directory:
            QMessageBox.critical(self, "Error", "Please select the working directory!")
            return

        if not self.mask or not self.fmask or not self.deforestation_cal or not self.deforestation_hrp or not self.density :
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        images = [self.mask, self.fmask, self.deforestation_cal, self.deforestation_hrp, self.density]

        # Check if all images have the same resolution
        resolutions = [map_checker.get_image_resolution(img) for img in images]
        if len(set(resolutions)) != 1:
            QMessageBox.critical(None, "Error", "All the input raster images must have the same spatial resolution!")
            return

        # Check if all images have the same number of rows and columns
        dimensions = [map_checker.get_image_dimensions(img) for img in images]
        if len(set(dimensions)) != 1:
            QMessageBox.critical(None, "Error",
                                 "All the input raster images must have the same number of rows and columns!")
            return

        grid_area = self.grid_area_entry.text()
        if not grid_area:
            QMessageBox.critical(self, "Error", "Please enter the thiessen polygon grid area value!")
            return
        try:
            self.grid_area = float(grid_area)
            if not (0 < self.grid_area):
                QMessageBox.critical(self, "Error", "Thiessen polygon grid area value should larger than 0!")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "Thiessen polygon grid area value should be a valid number!")
            return

        xmax = self.xmax_entry.text()
        if xmax.lower() != "default":
            try:
                xmax = float(xmax)
                if xmax <= 0:
                    raise ValueError("The plot x-axis limit should be larger than 0!")
            except ValueError:
                QMessageBox.critical(self, "Error", "The plot x-axis limit should be a valid number or 'Default'!")
                return

        ymax = self.ymax_entry.text()
        if ymax.lower() != "default":
            try:
                ymax = float(ymax)
                if ymax <= 0:
                    raise ValueError("The plot y-axis limit should be larger than 0!")
            except ValueError:
                QMessageBox.critical(self, "Error", "The plot y-axis limit should be a valid number or 'Default'!")
                return

        title = self.title_entry.text()
        if not title:
            QMessageBox.critical(self, "Error", "Please enter the title of plot!")
            return

        out_fn = self.out_fn_entry.text()
        if not out_fn:
            QMessageBox.critical(self, "Error", "Please enter the name used for the plot, performace chart and assessment polygons!")
            return

        # Check if the out_fn has the correct file extension
        if not (out_fn.endswith('.png') or out_fn.endswith('.jpg') or out_fn.endswith('.pdf') or out_fn.endswith(
                '.svg') or out_fn.endswith('.eps') or out_fn.endswith('.ps') or out_fn.endswith('.tif')):
            QMessageBox.critical(self, "Error",
                                 "Please enter extension(.png/.jpg/.pdf/.svg/.eps/.ps/.tif) in the name of plot!")
            return

        raster_fn = self.raster_fn_entry.text()
        if not raster_fn:
            QMessageBox.critical(self, "Error", "Please enter the name for Residual Map!")
            return

        if not (raster_fn.endswith('.tif') or raster_fn.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Residual Map!")
            return

        out_fn_def = self.out_fn_def_entry.text()
        if not out_fn_def:
            QMessageBox.critical(self, "Error", "Please enter the name for Combined Deforestation Reference Map!")
            return

        if not (out_fn_def.endswith('.tif') or out_fn_def.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Combined Deforestation Reference Map!")
            return

        if not map_checker.check_binary_map(self.mask):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF THE NON-EXCLUDED JURISDICTION' must be a binary map (0 and 1) where the 1’s indicate areas inside the jurisdiction.")
            return

        if not map_checker.check_binary_map(self.deforestation_hrp):
            QMessageBox.critical(None, "Error",
                                 "'MAP OF DEFORESTATION IN THE CNF' must be a binary map (0 and 1) where the 1’s indicate deforestation.")
            return

        if not map_checker.check_binary_map(self.deforestation_cal):
            QMessageBox.critical(None, "Error",
                                 "'MAP OF DEFORESTATION IN THE CAL' must be a binary map (0 and 1) where the 1’s indicate deforestation.")
            return

        if not map_checker.check_binary_map(self.fmask):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF FOREST AREAS IN THE CAL' must be a binary map (0 and 1) where the 1’s indicate forest areas.")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.model_evaluation.set_working_directory(directory)
            self.model_evaluation.create_mask_polygon(self.mask)
            clipped_gdf = self.model_evaluation.create_thiessen_polygon(self.grid_area, self.mask, self.density,
                                                                             self.deforestation_hrp, out_fn, raster_fn)
            self.model_evaluation.replace_ref_system(self.mask, raster_fn)
            self.model_evaluation.create_deforestation_map(self.fmask, self.deforestation_cal, self.deforestation_hrp,
                                                           out_fn_def)
            self.model_evaluation.replace_ref_system(self.fmask, out_fn_def)
            self.model_evaluation.replace_legend(out_fn_def)
            self.model_evaluation.create_plot(grid_area,clipped_gdf, title, out_fn, xmax, ymax)
            self.model_evaluation.remove_temp_files()

            QMessageBox.information(self, "Processing Completed", "Processing completed!")
            self.progressDialog.close()

        except Exception as e:
             self.progressDialog.close()
             QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def update_progress(self, value):
        # Update QProgressDialog with the new value
        if self.progressDialog is not None:
            self.progressDialog.setValue(value)

class RMT_FIT_HRP_SCREEN(QDialog):
    def __init__(self):
        super(RMT_FIT_HRP_SCREEN, self).__init__()
        # Store the initial directory path
        self.initial_directory = os.getcwd()
        loadUi(Path(PureWindowsPath("data\\rmt_fit_hrp_screen.ui")), self)
        if central_data_store.directory is not None and self.folder_entry is not None:
            self.directory = central_data_store.directory
            self.folder_entry.setText(str(central_data_store.directory))
        if central_data_store.directory is not None and self.folder_entry_2 is not None:
            self.directory_2 = central_data_store.directory
            self.folder_entry_2.setText(str(central_data_store.directory))
        self.AT_button2.clicked.connect(self.gotoat2)
        self.Intro_button2.clicked.connect(self.gotointro2)

        self.doc_button = self.tab1.findChild(QWidget, "doc_button")
        self.select_folder_button = self.tab1.findChild(QWidget, "select_folder_button")
        self.fd_button = self.tab1.findChild(QWidget, "fd_button")
        self.mask_button = self.tab1.findChild(QWidget, "mask_button")
        self.ok_button2 = self.tab1.findChild(QWidget, "ok_button2")

        self.doc_button_2 = self.tab2.findChild(QWidget, "doc_button_2")
        self.select_folder_button_2 = self.tab2.findChild(QWidget, "select_folder_button_2")
        self.mask_button_2 = self.tab2.findChild(QWidget, "mask_button_2")
        self.fmask_button_2 = self.tab2.findChild(QWidget, "fmask_button_2")
        self.fd_button_2 = self.tab2.findChild(QWidget, "fd_button_2")
        self.ok_button2_2 = self.tab2.findChild(QWidget, "ok_button2_2")

        self.doc_button.clicked.connect(self.openDocument)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.fd_button.clicked.connect(self.select_fd)
        self.mask_button.clicked.connect(self.select_mask)
        self.ok_button2.clicked.connect(self.process_data2)

        self.doc_button_2.clicked.connect(self.openDocument_2)
        self.select_folder_button_2.clicked.connect(self.select_working_directory_2)
        self.mask_button_2.clicked.connect(self.select_mask_2)
        self.fmask_button_2.clicked.connect(self.select_fmask_2)
        self.fd_button_2.clicked.connect(self.select_fd_2)
        self.ok_button2_2.clicked.connect(self.process_data2_2)

        self.vulnerability_map = VulnerabilityMap()
        self.vulnerability_map.progress_updated.connect(self.update_progress)
        self.directory = None
        self.in_fn = None
        self.NRT = None
        if central_data_store.NRT is not None:
            self.nrt_entry.setText(str(central_data_store.NRT))
        self.n_classes = None
        self.mask = None
        self.out_fn = None
        self.out_fn_entry.setPlaceholderText('e.g., Acre_Vulnerability_HRP.tif')

        self.directory_2 = None
        self.mask_2 = None
        self.fmask_2 = None
        self.in_fn_2 = None
        self.out_fn_2 = None
        self.n_classes_2 = None
        self.out_fn_entry_2.setPlaceholderText('e.g., Acre_Vulnerability_HRP.tif')

        self.setWindowTitle("JNR Integrated Risk/Allocation Tool")

    def gotoat2(self):
        os.chdir(self.initial_directory)
        at2 = AT_FIT_HRP_Screen()
        widget.addWidget(at2)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotointro2(self):
        os.chdir(self.initial_directory)
        intro2 = IntroScreen()
        widget.addWidget(intro2)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def openDocument(self):
        pdf_path = Path(PureWindowsPath("doc\\AppFitVM.pdf"))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def openDocument_2(self):
        pdf_path = Path(PureWindowsPath("doc\\AppFitVM.pdf"))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path = Path(data_folder)
        self.directory = str(data_folder_path)
        self.folder_entry.setText(self.directory)
        self.folder_entry_2.setText(self.directory)
        central_data_store.directory = self.directory

    def select_fd(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Map of Distance from the Forest Edge in HRP')
        if file_path:
            self.in_fn = file_path
            self.in_fn_entry.setText(file_path.split('/')[-1])
    def select_mask(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Mask of Study Area')
        if file_path:
            self.mask = file_path
            self.mask_entry.setText(file_path.split('/')[-1])
    def select_working_directory_2(self):
        data_folder_2 = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path_2 = Path(data_folder_2)
        self.directory_2 = str(data_folder_path_2)
        self.folder_entry_2.setText(self.directory_2)
        self.folder_entry.setText(self.directory_2)
        central_data_store.directory = self.directory_2

    def select_fd_2(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Map of Distance from the Forest Edge in HRP')
        if file_path:
            self.in_fn_2 = file_path
            self.in_fn_entry_2.setText(file_path.split('/')[-1])

    def select_mask_2(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Mask of Study Area')
        if file_path:
            self.mask_2 = file_path
            self.mask_entry_2.setText(file_path.split('/')[-1])

    def select_fmask_2(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Mask of Forest Area')
        if file_path:
            self.fmask_2 = file_path
            self.fmask_entry_2.setText(file_path.split('/')[-1])

    def process_data2(self):
        directory = self.folder_entry.text()
        if not directory:
            QMessageBox.critical(self, "Error", "Please select the working directory!")
            return

        if not self.in_fn or not self.mask:
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        NRT = self.nrt_entry.text()
        if not NRT:
            QMessageBox.critical(self, "Error", "Please enter the NRT value!")
            return
        try:
            self.NRT = int(NRT)
            if (self.NRT <= 0):
                QMessageBox.critical(self, "Error", "NRT value should be larger than 0!")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "NRT value should be a valid number!")
            return

        n_classes = int(29)
        if not n_classes:
            QMessageBox.critical(self, "Error", "Please enter the number of classes!")
            return
        try:
            self.n_classes = int(n_classes)
            if (self.n_classes <= 0):
                QMessageBox.critical(self, "Error", "Number of classes should be larger than 0!")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "Number of classes value should be a valid number!")
            return

        out_fn = self.out_fn_entry.text()
        if not out_fn:
            QMessageBox.critical(self, "Error", "Please enter the name of Vulnerability Map in HRP!")
            return

        if not (out_fn.endswith('.tif') or out_fn.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Vulnerability Map in HRP!")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.vulnerability_map.set_working_directory(directory)
            mask_arr = self.vulnerability_map.geometric_classification(self.in_fn, NRT, n_classes, self.mask)
            self.vulnerability_map.array_to_image(self.in_fn, out_fn, mask_arr, gdal.GDT_Int16, -1)
            self.vulnerability_map.replace_ref_system(self.in_fn, out_fn)

            QMessageBox.information(self, "Processing Completed", "Processing completed!")
            self.progressDialog.close()

        except Exception as e:
            self.progressDialog.close()
            QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def process_data2_2(self):
        directory_2 = self.folder_entry_2.text()
        if not directory_2 :
            QMessageBox.critical(self, "Error", "Please select the working directory!")
            return

        if not self.in_fn_2 or not self.mask_2 or not self.fmask_2:
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        images = [self.in_fn_2, self.mask_2, self.fmask_2]

        # Check if all images have the same resolution
        resolutions = [map_checker.get_image_resolution(img) for img in images]
        if len(set(resolutions)) != 1:
            QMessageBox.critical(None, "Error", "All the input raster images must have the same spatial resolution!")
            return

        # Check if all images have the same number of rows and columns
        dimensions = [map_checker.get_image_dimensions(img) for img in images]
        if len(set(dimensions)) != 1:
            QMessageBox.critical(None, "Error",
                                 "All the input raster images must have the same number of rows and columns!")
            return

        n_classes_2 = int(30)
        out_fn_2 = self.out_fn_entry_2.text()
        if not out_fn_2:
            QMessageBox.critical(self, "Error", "Please enter the name of Vulnerability Map in HRP!")
            return

        # Check if the out_fn has the correct file extension
        if not (out_fn_2.endswith('.tif') or out_fn_2.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Vulnerability Map in HRP!")
            return

        if not map_checker.check_binary_map(self.mask_2):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF THE NON-EXCLUDED JURISDICTION' must be a binary map (0 and 1) where the 1’s indicate areas inside the jurisdiction.")
            return

        if not map_checker.check_binary_map(self.fmask_2):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF FOREST AREAS IN THE HRP' must be a binary map (0 and 1) where the 1’s indicate forest areas.")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.vulnerability_map.set_working_directory(directory_2)
            mask_arr = self.vulnerability_map.geometric_classification_alternative(self.in_fn_2, n_classes_2,
                                                                                   self.mask_2, self.fmask_2)
            self.vulnerability_map.array_to_image(self.in_fn_2, out_fn_2, mask_arr, gdal.GDT_Int16, -1)
            self.vulnerability_map.replace_ref_system(self.in_fn_2, out_fn_2)

            QMessageBox.information(self, "Processing Completed", "Processing completed!")

            self.progressDialog.close()

        except Exception as e:
            self.progressDialog.close()
            QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def update_progress(self, value):
        # Update QProgressDialog with the new value
        if self.progressDialog is not None:
            self.progressDialog.setValue(value)

class AT_FIT_HRP_Screen(QDialog):
    def __init__(self):
        super(AT_FIT_HRP_Screen, self).__init__()
        self.initial_directory = os.getcwd()
        loadUi(Path(PureWindowsPath("data\\at_fit_hrp_screen.ui")), self)
        if central_data_store.directory is not None and self.folder_entry is not None:
            self.directory = central_data_store.directory
            self.folder_entry.setText(str(central_data_store.directory))
        self.Intro_button3.clicked.connect(self.gotointro3)
        self.RMT_button3.clicked.connect(self.gotormt3)
        self.doc_button.clicked.connect(self.openDocument)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.municipality_button.clicked.connect(self.select_municipality)
        self.risk30_hrp_button.clicked.connect(self.select_risk30_hrp)
        self.deforestation_hrp_button.clicked.connect(self.select_deforestation_hrp)
        self.ok_button3.clicked.connect(self.process_data3)
        self.allocation_tool = AllocationTool()
        self.allocation_tool.progress_updated.connect(self.update_progress)
        self.directory = None
        self.risk30_hrp = None
        self.municipality = None
        self.deforestation_hrp = None
        self.out_fn1 = None
        self.out_fn2 = None
        self.csv_name = None
        self.image1_entry.setPlaceholderText('e.g., Acre_Modeling_Region_HRP.tif')
        self.csv_entry.setPlaceholderText('e.g., Relative_Frequency_Table_HRP.csv')
        self.image2_entry.setPlaceholderText('e.g., Acre_Fitted_Density_Map_HRP.tif')

        self.setWindowTitle("JNR Integrated Risk/Allocation Tool")

    def gotormt3(self):
        os.chdir(self.initial_directory)
        rmt3 = RMT_FIT_HRP_SCREEN()
        widget.addWidget(rmt3)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotointro3(self):
        os.chdir(self.initial_directory)
        intro3 = IntroScreen()
        widget.addWidget(intro3)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def openDocument(self):
        pdf_path = Path(PureWindowsPath("doc\\AppFitAM.pdf"))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path = Path(data_folder)
        self.directory = str(data_folder_path)
        self.folder_entry.setText(self.directory)
        central_data_store.directory = self.directory

    def select_municipality(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Map of Administrative Divisions')
        if file_path:
            self.municipality = file_path
            self.municipality_entry.setText(file_path.split('/')[-1])

    def select_risk30_hrp(self):
        file_path1, _ = QFileDialog.getOpenFileName(self, "Vulnerability Map in HRP")
        if file_path1:
            self.risk30_hrp = file_path1
            self.risk30_hrp_entry.setText(file_path1.split('/')[-1])

    def select_deforestation_hrp(self):
        file_path3, _ = QFileDialog.getOpenFileName(self, "Map of Deforestation in the HRP")
        if file_path3:
            self.deforestation_hrp = file_path3
            self.deforestation_hrp_entry.setText(file_path3.split('/')[-1])

    def process_data3(self):
        directory = self.folder_entry.text()
        if not directory:
            QMessageBox.critical(self, "Error", "Please select the working directory!")
            return

        if not self.risk30_hrp or not self.municipality or not self.deforestation_hrp:
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        images = [self.risk30_hrp, self.municipality, self.deforestation_hrp]

        # Check if all images have the same resolution
        resolutions = [map_checker.get_image_resolution(img) for img in images]
        if len(set(resolutions)) != 1:
            QMessageBox.critical(None, "Error", "All the input raster images must have the same spatial resolution!")
            return

        # Check if all images have the same number of rows and columns
        dimensions = [map_checker.get_image_dimensions(img) for img in images]
        if len(set(dimensions)) != 1:
            QMessageBox.critical(None, "Error",
                                 "All the input raster images must have the same number of rows and columns!")
            return

        out_fn1 = self.image1_entry.text()
        if not out_fn1:
            QMessageBox.critical(self, "Error", "Please enter the name for Modeling Region Map in HRP!")
            return

        if not (out_fn1.endswith('.tif') or out_fn1.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name for Modeling Region Map in HRP!")
            return

        csv_name = self.csv_entry.text()
        if not csv_name:
            QMessageBox.critical(self, "Error", "Please enter the name for the Relative Frequency Table!")
            return

        if not (csv_name.endswith('.csv')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .csv extension in the name of Relative Frequency Table!")
            return

        out_fn2 = self.image2_entry.text()
        if not out_fn2:
            QMessageBox.critical(self, "Error", "Please enter the name for Fitted Density Map in the HRP!")
            return

        if not (out_fn2.endswith('.tif') or out_fn2.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Fitted Density Map in the HRP!")
            return

        if not map_checker.check_binary_map(self.deforestation_hrp):
            QMessageBox.critical(None, "Error",
                                 "'MAP OF DEFORESTATION IN THE HRP' must be a binary map (0 and 1) where the 1’s indicate deforestation.")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.allocation_tool.execute_workflow_fit(directory, self.risk30_hrp,
                                                        self.municipality,self.deforestation_hrp, csv_name,
                                                        out_fn1,out_fn2)
            QMessageBox.information(self, "Processing Completed", "Processing completed!")
            self.progressDialog.close()

        except Exception as e:
             self.progressDialog.close()
             QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def update_progress(self, value):
        # Update QProgressDialog with the new value
        if self.progressDialog is not None:
            self.progressDialog.setValue(value)


class RMT_PRE_VP_SCREEN(QDialog):
    def __init__(self):
        super(RMT_PRE_VP_SCREEN, self).__init__()
        # Store the initial directory path
        self.initial_directory = os.getcwd()
        loadUi(Path(PureWindowsPath("data\\rmt_pre_vp_screen.ui")), self)
        if central_data_store.directory is not None and self.folder_entry is not None:
            self.directory = central_data_store.directory
            self.folder_entry.setText(str(central_data_store.directory))
        if central_data_store.directory is not None and self.folder_entry_2 is not None:
            self.directory_2 = central_data_store.directory
            self.folder_entry_2.setText(str(central_data_store.directory))
        self.AT_button2.clicked.connect(self.gotoat2)
        self.Intro_button2.clicked.connect(self.gotointro2)

        self.doc_button = self.tab1.findChild(QWidget, "doc_button")
        self.select_folder_button = self.tab1.findChild(QWidget, "select_folder_button")
        self.fd_button = self.tab1.findChild(QWidget, "fd_button")
        self.mask_button = self.tab1.findChild(QWidget, "mask_button")
        self.ok_button2 = self.tab1.findChild(QWidget, "ok_button2")

        self.doc_button_2 = self.tab2.findChild(QWidget, "doc_button_2")
        self.select_folder_button_2 = self.tab2.findChild(QWidget, "select_folder_button_2")
        self.mask_button_2 = self.tab2.findChild(QWidget, "mask_button_2")
        self.fmask_button_2 = self.tab2.findChild(QWidget, "fmask_button_2")
        self.fd_button_2 = self.tab2.findChild(QWidget, "fd_button_2")
        self.ok_button2_2 = self.tab2.findChild(QWidget, "ok_button2_2")

        self.doc_button.clicked.connect(self.openDocument)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.fd_button.clicked.connect(self.select_fd)
        self.mask_button.clicked.connect(self.select_mask)
        self.ok_button2.clicked.connect(self.process_data2)

        self.doc_button_2.clicked.connect(self.openDocument_2)
        self.select_folder_button_2.clicked.connect(self.select_working_directory_2)
        self.mask_button_2.clicked.connect(self.select_mask_2)
        self.fmask_button_2.clicked.connect(self.select_fmask_2)
        self.fd_button_2.clicked.connect(self.select_fd_2)
        self.ok_button2_2.clicked.connect(self.process_data2_2)

        self.vulnerability_map = VulnerabilityMap()
        self.vulnerability_map.progress_updated.connect(self.update_progress)
        self.directory = None
        self.in_fn = None
        self.NRT = None
        if central_data_store.NRT is not None:
            self.nrt_entry.setText(str(central_data_store.NRT))
        self.n_classes = None
        self.mask = None
        self.out_fn = None
        self.out_fn_entry.setPlaceholderText('e.g., Acre_Vulnerability_VP.tif')

        self.directory_2 = None
        self.mask_2 = None
        self.fmask_2 = None
        self.in_fn_2 = None
        self.out_fn_2 = None
        self.n_classes_2 = None
        self.out_fn_entry_2.setPlaceholderText('e.g., Acre_Vulnerability_VP.tif')

        self.setWindowTitle("JNR Integrated Risk/Allocation Tool")

    def gotoat2(self):
        os.chdir(self.initial_directory)
        at2 = AT_PRE_VP_Screen()
        widget.addWidget(at2)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotointro2(self):
        os.chdir(self.initial_directory)
        intro2 = IntroScreen()
        widget.addWidget(intro2)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def openDocument(self):
        pdf_path = Path(PureWindowsPath("doc\\AppPreVM.pdf"))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def openDocument_2(self):
        pdf_path = Path(PureWindowsPath("doc\\AppPreVM.pdf"))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path = Path(data_folder)
        self.directory = str(data_folder_path)
        self.folder_entry.setText(self.directory)
        self.folder_entry_2.setText(self.directory)
        central_data_store.directory = self.directory

    def select_fd(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Map of Distance from the Forest Edge in VP')
        if file_path:
            self.in_fn = file_path
            self.in_fn_entry.setText(file_path.split('/')[-1])
    def select_mask(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Mask of Study Area')
        if file_path:
            self.mask = file_path
            self.mask_entry.setText(file_path.split('/')[-1])

    def select_working_directory_2(self):
        data_folder_2 = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path_2 = Path(data_folder_2)
        self.directory_2 = str(data_folder_path_2)
        self.folder_entry_2.setText(self.directory_2)
        self.folder_entry.setText(self.directory_2)
        central_data_store.directory = self.directory_2

    def select_fd_2(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Map of Distance from the Forest Edge in VP')
        if file_path:
            self.in_fn_2 = file_path
            self.in_fn_entry_2.setText(file_path.split('/')[-1])

    def select_mask_2(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Mask of Study Area')
        if file_path:
            self.mask_2 = file_path
            self.mask_entry_2.setText(file_path.split('/')[-1])

    def select_fmask_2(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Mask of Forest Area')
        if file_path:
            self.fmask_2 = file_path
            self.fmask_entry_2.setText(file_path.split('/')[-1])

    def process_data2(self):
        directory = self.folder_entry.text()
        if not directory:
            QMessageBox.critical(self, "Error", "Please select the working directory!")
            return

        if not self.in_fn or not self.mask:
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        NRT = self.nrt_entry.text()
        if not NRT:
            QMessageBox.critical(self, "Error", "Please enter the NRT value!")
            return
        try:
            self.NRT = int(NRT)
            if (self.NRT <= 0):
                QMessageBox.critical(self, "Error", "NRT value should be larger than 0!")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "NRT value should be a valid number!")
            return

        n_classes = int(29)
        if not n_classes:
            QMessageBox.critical(self, "Error", "Please enter the number of classes!")
            return
        try:
            self.n_classes = int(n_classes)
            if (self.n_classes <= 0):
                QMessageBox.critical(self, "Error", "Number of classes should be larger than 0!")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "Number of classes value should be a valid number!")
            return

        out_fn = self.out_fn_entry.text()
        if not out_fn:
            QMessageBox.critical(self, "Error", "Please enter the name of Vulnerability Map in VP!")
            return

        if not (out_fn.endswith('.tif') or out_fn.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Vulnerability Map in VP!")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.vulnerability_map.set_working_directory(directory)
            mask_arr = self.vulnerability_map.geometric_classification(self.in_fn, NRT, n_classes, self.mask)
            self.vulnerability_map.array_to_image(self.in_fn, out_fn, mask_arr, gdal.GDT_Int16, -1)
            self.vulnerability_map.replace_ref_system(self.in_fn, out_fn)

            QMessageBox.information(self, "Processing Completed", "Processing completed!")
            self.progressDialog.close()

        except Exception as e:
            self.progressDialog.close()
            QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def process_data2_2(self):
        directory_2 = self.folder_entry_2.text()
        if not directory_2 :
            QMessageBox.critical(self, "Error", "Please select the working directory!")
            return

        if not self.in_fn_2 or not self.mask_2 or not self.fmask_2:
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        images = [self.in_fn_2, self.mask_2, self.fmask_2]

        # Check if all images have the same resolution
        resolutions = [map_checker.get_image_resolution(img) for img in images]
        if len(set(resolutions)) != 1:
            QMessageBox.critical(None, "Error", "All the input raster images must have the same spatial resolution!")
            return

        # Check if all images have the same number of rows and columns
        dimensions = [map_checker.get_image_dimensions(img) for img in images]
        if len(set(dimensions)) != 1:
            QMessageBox.critical(None, "Error",
                                 "All the input raster images must have the same number of rows and columns!")
            return

        n_classes_2 = int(30)
        out_fn_2 = self.out_fn_entry_2.text()
        if not out_fn_2:
            QMessageBox.critical(self, "Error", "Please enter the name of Vulnerability Map in VP!")
            return

        # Check if the out_fn has the correct file extension
        if not (out_fn_2.endswith('.tif') or out_fn_2.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Vulnerability Map in VP!")
            return

        if not map_checker.check_binary_map(self.mask_2):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF THE NON-EXCLUDED JURISDICTION' must be a binary map (0 and 1) where the 1’s indicate areas inside the jurisdiction.")
            return

        if not map_checker.check_binary_map(self.fmask_2):
            QMessageBox.critical(None, "Error",
                                 "'MASK OF FOREST AREAS IN THE VP' must be a binary map (0 and 1) where the 1’s indicate forest areas.")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            self.vulnerability_map.set_working_directory(directory_2)
            mask_arr = self.vulnerability_map.geometric_classification_alternative(self.in_fn_2, n_classes_2,
                                                                                   self.mask_2, self.fmask_2)
            self.vulnerability_map.array_to_image(self.in_fn_2, out_fn_2, mask_arr, gdal.GDT_Int16, -1)
            self.vulnerability_map.replace_ref_system(self.in_fn_2, out_fn_2)

            QMessageBox.information(self, "Processing Completed", "Processing completed!")

            self.progressDialog.close()

        except Exception as e:
            self.progressDialog.close()
            QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def update_progress(self, value):
        # Update QProgressDialog with the new value
        if self.progressDialog is not None:
            self.progressDialog.setValue(value)

class AT_PRE_VP_Screen(QDialog):
    def __init__(self):
        super(AT_PRE_VP_Screen, self).__init__()
        self.initial_directory = os.getcwd()
        loadUi(Path(PureWindowsPath("data\\at_pre_vp_screen.ui")), self)
        if central_data_store.directory is not None and self.folder_entry is not None:
            self.directory = central_data_store.directory
            self.folder_entry.setText(str(central_data_store.directory))
        self.Intro_button3.clicked.connect(self.gotointro3)
        self.RMT_button3.clicked.connect(self.gotormt3)
        self.doc_button.clicked.connect(self.openDocument)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.municipality_button.clicked.connect(self.select_municipality)
        self.csv_button.clicked.connect(self.select_csv)
        self.risk30_vp_button.clicked.connect(self.select_risk30_vp)
        self.ok_button3.clicked.connect(self.process_data3)
        self.allocation_tool = AllocationTool()
        # Connect the progress_updated signal to the update_progress method
        self.allocation_tool.progress_updated.connect(self.update_progress)
        self.directory = None
        self.csv = None
        self.municipality = None
        self.risk30_vp = None
        self.expected_deforestation = None
        self.max_iterations = None
        self.time = None
        self.image1 = None
        self.image2 = None
        self.iteration_entry.setPlaceholderText('The suggestion max iteration number is 5')
        self.image1_entry.setPlaceholderText('e.g., Acre_Prediction_Modeling_Region_VP.tif')
        self.image2_entry.setPlaceholderText('e.g., Acre_Adjucted_Density_Map_VP.tif')
        self.setWindowTitle("JNR Integrated Risk/Allocation Tool")

    def gotormt3(self):
        os.chdir(self.initial_directory)
        rmt3 = RMT_PRE_VP_SCREEN()
        widget.addWidget(rmt3)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotointro3(self):
        os.chdir(self.initial_directory)
        intro3 = IntroScreen()
        widget.addWidget(intro3)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def openDocument(self):
        pdf_path = Path(PureWindowsPath("doc\\AppPreAM.pdf"))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        data_folder_path = Path(data_folder)
        self.directory = str(data_folder_path)
        self.folder_entry.setText(self.directory)
        central_data_store.directory = self.directory

    def select_municipality(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Map of Administrative Divisions')
        if file_path:
            self.municipality = file_path
            self.municipality_entry.setText(file_path.split('/')[-1])

    def select_csv(self):
        file_path1, _ = QFileDialog.getOpenFileName(self, "HRP Relative Frequency Table (.csv)")
        if file_path1:
            self.csv = file_path1
            self.csv_entry.setText(file_path1.split('/')[-1])

    def select_risk30_vp(self):
        file_path2, _ = QFileDialog.getOpenFileName(self, "Vulnerability Map in VP")
        if file_path2:
            self.risk30_vp = file_path2
            self.risk30_vp_entry.setText(file_path2.split('/')[-1])

    def process_data3(self):
        directory = self.folder_entry.text()
        if not directory:
            QMessageBox.critical(self, "Error", "Please select the working directory!")
            return

        if not self.csv or not self.municipality or not self.risk30_vp:
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        images = [self.municipality, self.risk30_vp]

        # Check if all images have the same resolution
        resolutions = [map_checker.get_image_resolution(img) for img in images]
        if len(set(resolutions)) != 1:
            QMessageBox.critical(None, "Error", "All the input raster images must have the same spatial resolution!")
            return

        # Check if all images have the same number of rows and columns
        dimensions = [map_checker.get_image_dimensions(img) for img in images]
        if len(set(dimensions)) != 1:
            QMessageBox.critical(None, "Error",
                                 "All the input raster images must have the same number of rows and columns!")
            return

        expected_deforestation = self.expected_entry.text()
        if not expected_deforestation:
            QMessageBox.critical(self, "Error", "Please enter the expected deforestation value!")
            return
        try:
            self.expected_deforestation = float(expected_deforestation)
        except ValueError:
            QMessageBox.critical(self, "Error", "Expected deforestation value should be a valid number!")
            return

        out_fn1 = self.image1_entry.text()
        if not out_fn1:
            QMessageBox.critical(self, "Error", "Please enter the name of Prediction Modeling Region Map in VP!")
            return

        if not (out_fn1.endswith('.tif') or out_fn1.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Prediction Modeling Region Map in VP!")
            return

        out_fn2 = self.image2_entry.text()
        if not out_fn2:
            QMessageBox.critical(self, "Error", "Please enter the name of Adjusted Prediction Density Map in VP!")
            return

        if not (out_fn2.endswith('.tif') or out_fn2.endswith('.rst')):
            QMessageBox.critical(self, "Error",
                                 "Please enter .rst or .tif extension in the name of Adjusted Prediction Density Map in VP!")
            return

        max_iterations = self.iteration_entry.text()
        if not max_iterations:
            QMessageBox.critical(self, "Error", "Please enter the max iterations! The suggestion number is 5.")
            return
        try:
            self.max_iterations = int(max_iterations)
        except ValueError:
            QMessageBox.critical(self, "Error", "Max iteration value should be a valid number!")
            return

        time = self.year_entry.text()
        if not time:
            QMessageBox.critical(self, "Error", "Please enter the number of years in the VP! ")
            return
        try:
            self.time = int(time)
        except ValueError:
            QMessageBox.critical(self, "Error", "The number of years in the VP should be a valid number!")
            return

        # Show "Processing" message
        processing_message = "Processing data..."
        self.progressDialog = QProgressDialog(processing_message, None, 0, 100, self)

        # Change the font size
        font = QFont()
        font.setPointSize(9)
        self.progressDialog.setFont(font)

        self.progressDialog.setWindowTitle("Processing")
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)
        self.progressDialog.resize(400, 300)
        self.progressDialog.show()
        QApplication.processEvents()

        try:
            id_difference,iteration_count = self.allocation_tool.execute_workflow_vp(directory, self.max_iterations,
                                                                           self.csv,
                                                                           self.municipality,
                                                                           self.expected_deforestation,
                                                                           self.risk30_vp, out_fn1,out_fn2,
                                                                           self.time)

            if id_difference.size > 0:
                QMessageBox.warning(self, " Warning ", f"Modeling Region ID {','.join(map(str, id_difference))} do not exist in the Historical Reference Period. A new CSV has been created for the HRP where relative frequencies for missing bins have been estimated from corresponding vulnerability zones over the entire jurisdiction.")
            if iteration_count > int(max_iterations):
                QMessageBox.warning(self, " Warning ",
                                    f"Maximum iterations limit reached. Please increase the Maximum Iterations and try running the tool again.")
            else:
                QMessageBox.information(self, "Processing Completed", "Processing completed!")
            self.progressDialog.close()

        except Exception as e:
             self.progressDialog.close()
             QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def update_progress(self, value):
        # Update QProgressDialog with the new value
        if self.progressDialog is not None:
            self.progressDialog.setValue(value)

class CentralDataStore:
    def __init__(self):
        self.NRT = None
        self.directory = None

class MapChecker:
    def __init__(self):
        self.image=None
        self.arr=None
        self.in_fn=None

    def get_image_resolution(self,image):
        in_ds = gdal.Open(image)
        P = in_ds.GetGeoTransform()[1]
        return P

    def get_image_dimensions(self, image):
        dataset = gdal.Open(image)
        cols = dataset.RasterXSize
        rows = dataset.RasterYSize
        return rows, cols

    def get_image_datatype(self, image):
        in_ds = gdal.Open(image)
        in_band = in_ds.GetRasterBand(1)
        datatype = gdal.GetDataTypeName(in_band.DataType)
        return datatype

    def get_image_max_min(self, image):
        in_ds = gdal.Open(image)
        in_band = in_ds.GetRasterBand(1)
        min, max= in_band.ComputeRasterMinMax()
        return min, max

    def find_unique_values(self, arr, limit=2):
        unique_values = set()
        for value in np.nditer(arr):
            unique_values.add(value.item())
            if len(unique_values) > limit:
                return False
        return True

    def check_binary_map(self, in_fn):
        '''
        Check if input image is binary map
        :param in_fn: input image
        :return: True if the file is a binary map, False otherwise
        '''
        file_extension = in_fn.split('.')[-1].lower()
        file_name, _ = os.path.splitext(in_fn)
        if file_extension == 'rst':
            with open(file_name + '.rdc', 'r') as read_file:
                rdc_content = read_file.read().lower()
                byte_or_integer_binary = "data type   : byte" in rdc_content or (
                        "data type   : integer" in rdc_content and "min. value  : 0" in rdc_content and "max. value  : 1" in rdc_content)
                float_binary = "data type   : real" in rdc_content and "min. value  : 0.0000000" in rdc_content and "max. value  : 1.0000000" in rdc_content
        elif file_extension == 'tif':
            datatype = self.get_image_datatype(in_fn)
            min_val, max_val = self.get_image_max_min(in_fn)
            byte_or_integer_binary = datatype in ['Byte', 'CInt16', 'CInt32', 'Int16', 'Int32', 'UInt16',
                                                      'UInt32'] and max_val == 1 and min_val == 0
            float_binary = datatype in ['Float32', 'Float64', 'CFloat32', 'CFloat64'] and max_val == 1.0000000 and min_val == 0.0000000

        if byte_or_integer_binary or (float_binary):
            # For float_binary, use find_unique_values function to check if data only have two unique values [0.0000000, 1.0000000].
            if float_binary:
                in_ds = gdal.Open(in_fn)
                in_band = in_ds.GetRasterBand(1)
                arr = in_band.ReadAsArray()
                # If more than two unique values are found, it's not a binary map, return False.
                if not self.find_unique_values(arr, 2):
                    return False
            # Binary map: byte_or_integer_binary or float_binary with two unique values [0.0000000, 1.0000000], it returns True.
            return True
        # For any other scenario, it returns False.
        return False

if __name__ == "__main__":
    # main
    app = QApplication(sys.argv)
    # Load custom fonts
    font_id = QFontDatabase.addApplicationFont(str(Path(PureWindowsPath("font\\AvenirNextLTPro-DemiCn.otf"))))

    intro = IntroScreen()
    # Create a global instance of this store
    central_data_store = CentralDataStore()
    map_checker = MapChecker()

    widget = QtWidgets.QStackedWidget()
    widget.addWidget(intro)
    widget.setFixedHeight(1000)
    widget.setFixedWidth(1800)
    widget.show()

    try:
        sys.exit(app.exec_())
    except:
        print("Exiting")
