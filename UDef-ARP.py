import sys
import os
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog, QMessageBox, QProgressDialog
from PyQt5.QtGui import QFontDatabase, QIcon, QFont
from PyQt5.uic import loadUi
from allocation_tool import AllocationTool
from vulnerability_map import VulnerabilityMap
from map_comparison import MapComparison
from osgeo import gdal

class IntroScreen(QDialog):
    def __init__(self):
        super(IntroScreen, self).__init__()
        loadUi("data\intro_screen.ui", self)
        # Set window properties
        self.setWindowTitle('JNR Allocated Risk Mapping Procedure (UDef-ARP)')
        # Set window icon
        self.setWindowIcon(QIcon('icon.ico'))
        self.Fit_Cal_button.clicked.connect(self.gotofitcal)
        self.Pre_Cnf_button.clicked.connect(self.gotoprecnf)
        self.Fit_Hrp_button.clicked.connect(self.gotofithrp)
        self.Pre_VP_button.clicked.connect(self.gotoprevp)

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

class RMT_FIT_CAL_SCREEN(QDialog):
    def __init__(self):
        super(RMT_FIT_CAL_SCREEN, self).__init__()
        # Store the initial directory path
        self.initial_directory = os.getcwd()
        loadUi(r'data\rmt_fit_cal_screen.ui', self)
        self.AT_button2.clicked.connect(self.gotoat2)
        self.Intro_button2.clicked.connect(self.gotointro2)
        self.MCT_button2.clicked.connect(self.gotomct2)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.fd_button.clicked.connect(self.select_fd)
        self.ok_button2.clicked.connect(self.process_data2)
        self.vulnerability_map = VulnerabilityMap()
        self.vulnerability_map.progress_updated.connect(self.update_progress)
        self.directory = None
        self.in_fn = None
        self.NRT = None
        self.n_classes = None
        self.out_fn = None
        self.out_fn_entry.setPlaceholderText('e.g., Acre_vulerbility_CAL.tif')
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

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        self.directory = data_folder
        self.folder_entry.setText(str(data_folder))

    def select_fd(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Map of Distance from the Forest Edge in CAL')
        if file_path:
            self.in_fn = file_path
            self.in_fn_entry.setText(file_path.split('/')[-1])

    def process_data2(self):
        if not self.directory or not self.in_fn:
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
            data_folder = self.vulnerability_map.set_working_directory(self.directory)
            mask_arr = self.vulnerability_map.geometric_classification(self.in_fn, NRT, n_classes)
            out_ds = self.vulnerability_map.array2raster(self.in_fn, out_fn, mask_arr, gdal.GDT_Int16, -99)

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
        loadUi(r"data\at_fit_cal_screen.ui", self)
        self.Intro_button3.clicked.connect(self.gotointro3)
        self.RMT_button3.clicked.connect(self.gotormt3)
        self.MCT_button3.clicked.connect(self.gotomct3)
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

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        self.directory = data_folder
        self.folder_entry.setText(str(data_folder))

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
        if not self.directory or not self.risk30_hrp or not self.municipality or not self.deforestation_hrp:
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        out_fn1 = self.image1_entry.text()
        if not out_fn1:
            QMessageBox.critical(self, "Error", "Please enter the name for Modeling Region Map in CAL!")
            return

        out_fn2 = self.image2_entry.text()
        if not out_fn2:
            QMessageBox.critical(self, "Error", "Please enter the name for Fitted Density Map in the CAL!")
            return

        csv_name = self.csv_entry.text()
        if not csv_name:
            QMessageBox.critical(self, "Error", "Please enter the name for the Relative Frequency Table!")
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
            fit_density_map = self.allocation_tool.execute_workflow_fit(self.directory,self.risk30_hrp,
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
        loadUi(r"data\mct_fit_cal_screen.ui", self)
        self.AT_button4.clicked.connect(self.gotoat4)
        self.Intro_button4.clicked.connect(self.gotointro4)
        self.RMT_button4.clicked.connect(self.gotormt4)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.mask_button.clicked.connect(self.select_mask)
        self.deforestation_hrp_button.clicked.connect(self.select_deforestation_hrp)
        self.density_button.clicked.connect(self.select_density)
        self.ok_button.clicked.connect(self.process_data4)
        self.map_comparison = MapComparison()
        self.map_comparison.progress_updated.connect(self.update_progress)
        self.directory = None
        self.mask = None
        self.deforestation_hrp = None
        self.density = None
        self.grid_area = None
        self.grid_area_entry.setPlaceholderText('Type default 100000 or other number')
        self.title = None
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

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        self.directory = data_folder
        self.folder_entry.setText(str(data_folder))

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
        if not self.mask or not self.deforestation_hrp or not self.density :
            QMessageBox.critical(self, "Error", "Please select all input files!")
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

        title = self.title_entry.text()
        if not title:
            QMessageBox.critical(self, "Error", "Please enter the title of plot!")
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
            data_folder = self.map_comparison.set_working_directory(self.directory)
            Polygonized_Mask=self.map_comparison.create_mask_polygon(self.mask)
            self.map_comparison.create_thiessen_polygon(self.grid_area, self.mask)
            clipped_gdf, csv = self.map_comparison.calculate_zonal_stats(self.density, self.deforestation_hrp)
            self.map_comparison.create_plot(clipped_gdf, title)
            self.map_comparison.remove_temp_files()

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
        loadUi(r"data\rmt_pre_cnf_screen.ui", self)
        self.AT_button2.clicked.connect(self.gotoat2)
        self.Intro_button2.clicked.connect(self.gotointro2)
        self.MCT_button2.clicked.connect(self.gotomct2)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.fd_button.clicked.connect(self.select_fd)
        self.ok_button2.clicked.connect(self.process_data2)
        self.vulnerability_map = VulnerabilityMap()
        self.vulnerability_map.progress_updated.connect(self.update_progress)
        self.directory = None
        self.in_fn = None
        self.NRT = None
        self.n_classes = None
        self.out_fn = None
        self.out_fn_entry.setPlaceholderText('e.g., Acre_vulerbility_CNF.tif')
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

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        self.directory = data_folder
        self.folder_entry.setText(str(data_folder))

    def select_fd(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Map of Distance from the Forest Edge in CNF')
        if file_path:
            self.in_fn = file_path
            self.in_fn_entry.setText(file_path.split('/')[-1])

    def process_data2(self):
        if not self.directory or not self.in_fn:
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
            data_folder = self.vulnerability_map.set_working_directory(self.directory)
            mask_arr = self.vulnerability_map.geometric_classification(self.in_fn, NRT, n_classes)
            out_ds = self.vulnerability_map.array2raster(self.in_fn, out_fn, mask_arr, gdal.GDT_Int16, -99)

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
        loadUi(r"data\at_pre_cnf_screen.ui", self)
        self.Intro_button3.clicked.connect(self.gotointro3)
        self.RMT_button3.clicked.connect(self.gotormt3)
        self.MCT_button3.clicked.connect(self.gotomct3)
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
        rmt3 = RMT_PRE_VP_SCREEN()
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

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        self.directory = data_folder
        self.folder_entry.setText(str(data_folder))

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
        if not self.municipality or not self.csv or not self.deforestation_cnf or not self.risk30_vp:
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        out_fn1 = self.image1_entry.text()
        if not out_fn1:
            QMessageBox.critical(self, "Error", "Please enter the name of Prediction Modeling Region Map in CNF!")
            return

        out_fn2 = self.image2_entry.text()
        if not out_fn2:
            QMessageBox.critical(self, "Error", "Please enter the name of Adjusted Prediction Density Map in CNF!")
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
            adjusted_prediction_density_map = self.allocation_tool.execute_workflow_cnf(self.directory,
                                                                                        self.max_iterations, self.csv,
                                                                                        self.municipality,
                                                                                        self.deforestation_cnf,
                                                                                        self.risk30_vp, out_fn1,
                                                                                        out_fn2)
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
        loadUi(r"data\mct_pre_cnf_screen.ui", self)
        self.AT_button4.clicked.connect(self.gotoat4)
        self.Intro_button4.clicked.connect(self.gotointro4)
        self.RMT_button4.clicked.connect(self.gotormt4)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.mask_button.clicked.connect(self.select_mask)
        self.deforestation_hrp_button.clicked.connect(self.select_deforestation_hrp)
        self.density_button.clicked.connect(self.select_density)
        self.ok_button.clicked.connect(self.process_data4)
        self.map_comparison = MapComparison()
        self.map_comparison.progress_updated.connect(self.update_progress)
        self.directory = None
        self.mask = None
        self.deforestation_hrp = None
        self.density = None
        self.grid_area = None
        self.grid_area_entry.setPlaceholderText('Type default 100000 or other number')
        self.title = None
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

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        self.directory = data_folder
        self.folder_entry.setText(str(data_folder))

    def select_mask(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Mask of Study Area')
        if file_path:
            self.mask = file_path
            self.mask_entry.setText(file_path.split('/')[-1])

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
        if not self.mask or not self.deforestation_hrp or not self.density :
            QMessageBox.critical(self, "Error", "Please select all input files!")
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

        title = self.title_entry.text()
        if not title:
            QMessageBox.critical(self, "Error", "Please enter the title of plot!")
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
            data_folder = self.map_comparison.set_working_directory(self.directory)
            Polygonized_Mask=self.map_comparison.create_mask_polygon(self.mask)
            self.map_comparison.create_thiessen_polygon(self.grid_area, self.mask)
            clipped_gdf, csv = self.map_comparison.calculate_zonal_stats(self.density, self.deforestation_hrp)
            self.map_comparison.create_plot(clipped_gdf, title)
            self.map_comparison.remove_temp_files()

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
        loadUi(r"data\rmt_fit_hrp_screen.ui", self)
        self.AT_button2.clicked.connect(self.gotoat2)
        self.Intro_button2.clicked.connect(self.gotointro2)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.fd_button.clicked.connect(self.select_fd)
        self.ok_button2.clicked.connect(self.process_data2)
        self.vulnerability_map = VulnerabilityMap()
        self.vulnerability_map.progress_updated.connect(self.update_progress)
        self.directory = None
        self.in_fn = None
        self.NRT = None
        self.n_classes = None
        self.out_fn = None
        self.out_fn_entry.setPlaceholderText('e.g., Acre_vulerbility_HRP.tif')
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

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        self.directory = data_folder
        self.folder_entry.setText(str(data_folder))

    def select_fd(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Map of Distance from the Forest Edge in HRP')
        if file_path:
            self.in_fn = file_path
            self.in_fn_entry.setText(file_path.split('/')[-1])

    def process_data2(self):
        if not self.directory or not self.in_fn:
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
            data_folder = self.vulnerability_map.set_working_directory(self.directory)
            mask_arr = self.vulnerability_map.geometric_classification(self.in_fn, NRT, n_classes)
            out_ds = self.vulnerability_map.array2raster(self.in_fn, out_fn, mask_arr, gdal.GDT_Int16, -99)

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
        loadUi(r"data\at_fit_hrp_screen.ui", self)
        self.Intro_button3.clicked.connect(self.gotointro3)
        self.RMT_button3.clicked.connect(self.gotormt3)
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

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        self.directory = data_folder
        self.folder_entry.setText(str(data_folder))

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
        if not self.directory or not self.risk30_hrp or not self.municipality or not self.deforestation_hrp:
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        out_fn1 = self.image1_entry.text()
        if not out_fn1:
            QMessageBox.critical(self, "Error", "Please enter the name for Modeling Region Map in HRP!")
            return

        out_fn2 = self.image2_entry.text()
        if not out_fn2:
            QMessageBox.critical(self, "Error", "Please enter the name for Fitted Density Map in the HRP!")
            return

        csv_name = self.csv_entry.text()
        if not csv_name:
            QMessageBox.critical(self, "Error", "Please enter the name for the Relative Frequency Table!")
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
            fit_density_map = self.allocation_tool.execute_workflow_fit(self.directory,self.risk30_hrp,
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
        loadUi(r"data\rmt_pre_vp_screen.ui", self)
        self.AT_button2.clicked.connect(self.gotoat2)
        self.Intro_button2.clicked.connect(self.gotointro2)
        self.select_folder_button.clicked.connect(self.select_working_directory)
        self.fd_button.clicked.connect(self.select_fd)
        self.ok_button2.clicked.connect(self.process_data2)
        self.vulnerability_map = VulnerabilityMap()
        self.vulnerability_map.progress_updated.connect(self.update_progress)
        self.directory = None
        self.in_fn = None
        self.NRT = None
        self.n_classes = None
        self.out_fn = None
        self.out_fn_entry.setPlaceholderText('e.g., Acre_vulerbility_VP.tif')
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

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        self.directory = data_folder
        self.folder_entry.setText(str(data_folder))

    def select_fd(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Map of Distance from the Forest Edge in VP')
        if file_path:
            self.in_fn = file_path
            self.in_fn_entry.setText(file_path.split('/')[-1])

    def process_data2(self):
        if not self.directory or not self.in_fn:
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
            data_folder = self.vulnerability_map.set_working_directory(self.directory)
            mask_arr = self.vulnerability_map.geometric_classification(self.in_fn, NRT, n_classes)
            out_ds = self.vulnerability_map.array2raster(self.in_fn, out_fn, mask_arr, gdal.GDT_Int16, -99)

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
        loadUi(r"data\at_pre_vp_screen.ui", self)
        self.Intro_button3.clicked.connect(self.gotointro3)
        self.RMT_button3.clicked.connect(self.gotormt3)
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
        self.expected_entry.setPlaceholderText('Number is between 10000 and 100000')
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

    def select_working_directory(self):
        data_folder = QFileDialog.getExistingDirectory(self, "Working Directory")
        self.directory = data_folder
        self.folder_entry.setText(str(data_folder))

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
        if not self.csv or not self.municipality or not self.risk30_vp:
            QMessageBox.critical(self, "Error", "Please select all input files!")
            return

        expected_deforestation = self.expected_entry.text()
        if not expected_deforestation:
            QMessageBox.critical(self, "Error", "Please enter the expected deforestation value!")
            return
        try:
            self.expected_deforestation = float(expected_deforestation)
            if not (10000 <= self.expected_deforestation <= 100000):
                QMessageBox.critical(self, "Error", "Expected deforestation is between 10000 and 100000!")
                return
        except ValueError:
            QMessageBox.critical(self, "Error", "Expected deforestation value should be a valid number!")
            return

        out_fn1 = self.image1_entry.text()
        if not out_fn1:
            QMessageBox.critical(self, "Error", "Please enter the name of Prediction Modeling Region Map in VP!")
            return

        out_fn2 = self.image2_entry.text()
        if not out_fn2:
            QMessageBox.critical(self, "Error", "Please enter the name of Adjusted Prediction Density Map in VP!")
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
            adjusted_prediction_density_map = self.allocation_tool.execute_workflow_vp(self.directory, self.max_iterations,
                                                                                       self.csv,
                                                                                       self.municipality,
                                                                                       self.expected_deforestation,
                                                                                       self.risk30_vp, out_fn1,out_fn2,
                                                                                       self.time)

            QMessageBox.information(self, "Processing Completed", "Processing completed!")
            self.progressDialog.close()

        except Exception as e:
             self.progressDialog.close()
             QMessageBox.critical(self, "Error", f"An error occurred during processing: {str(e)}")

    def update_progress(self, value):
        # Update QProgressDialog with the new value
        if self.progressDialog is not None:
            self.progressDialog.setValue(value)
# main
app = QApplication(sys.argv)
# Load custom fonts
font_id=QFontDatabase.addApplicationFont("font\AvenirNextLTPro-DemiCn.otf")

##Check if font loaded successfully
# if font_id == -1:
#     print("Failed to load font.")
# else:
#     print("Font loaded successfully.")
# font_families = QFontDatabase().families()
# print(font_families)

intro = IntroScreen()
widget = QtWidgets.QStackedWidget()
widget.addWidget(intro)
widget.setFixedHeight(1000)
widget.setFixedWidth(1800)
widget.show()
try:
    sys.exit(app.exec_())
except:
    print("Exiting")