import os
import numpy as np
import pandas as pd
from osgeo import gdal
from PyQt5.QtCore import QObject, pyqtSignal
import shutil

# GDAL exceptions
gdal.UseExceptions()

class AllocationTool(QObject):
    progress_updated = pyqtSignal(int)

    def __init__(self):
        super(AllocationTool, self).__init__()
        self.data_folder = None

    def set_working_directory(self, directory):
        '''
        Set up the working directory
        :param directory: your local directory with all dat files
        '''
        self.data_folder = directory
        os.chdir(self.data_folder)

###Step1 Create the Fitting Modeling Region Map###
    def image_to_array(self,image):
        # Set up a GDAL dataset
        in_ds = gdal.Open(image)
        # Set up a GDAL band
        in_band = in_ds.GetRasterBand(1)
        # Create Numpy Array1
        arr = in_band.ReadAsArray()
        return arr

    def array_to_image(self, in_fn, out_fn, data, data_type, nodata=None):
        '''
          Create image from array
         :param in_fn: datasource to copy projection and geotransform from
         :param out_fn:path to the file to create
         :param data:the NumPy array
         :param data_type:output data type
         :param nodata:optional NoData value
         :return:
        '''
        in_ds = gdal.Open(in_fn)
        output_format = out_fn.split('.')[-1].upper()
        if (output_format == 'TIF'):
            output_format = 'GTIFF'
        elif (output_format == 'RST'):
            output_format = 'rst'
        driver = gdal.GetDriverByName(output_format)
        out_ds = driver.Create(out_fn, in_ds.RasterXSize, in_ds.RasterYSize, 1, data_type, options=["BigTIFF=YES"])
        out_band = out_ds.GetRasterBand(1)
        out_ds.SetGeoTransform(in_ds.GetGeoTransform())
        out_ds.SetProjection(in_ds.GetProjection().encode('utf-8', 'backslashreplace').decode('utf-8'))
        if nodata is not None:
            out_band.SetNoDataValue(nodata)
        out_band.WriteArray(data)
        out_band.FlushCache()
        out_ds.FlushCache()
        return

    def tabulation_bin_id_HRP(self, risk30_hrp, municipality, out_fn1):
        """
        This function is to create fitting modeling region array(tabulation_bin_id_masked)
        and fitting modeling region map(tabulation_bin_image)
        :param risk30_hrp: The 30-class vulnerability map for the CAL/HRP
        :param municipality: Subdivision image
        :param out_fn1: user input
        :return: tabulation_bin_id_masked: tabulation bin id array in CAL/HRP
        """
        # Convert risk30_hrp to NumPy array
        arr1 = self.image_to_array(risk30_hrp)

        # Convert municipality to NumPy array2
        arr2 = self.image_to_array(municipality)

        # Create a mask where the risk30_hrp value larger than 1 reclassed into 1
        mask_arr_HRP = np.where(arr1 > 0,1, arr1)

        # Calculate tabulation bin id with mask
        tabulation_bin_id_masked = np.add(arr1*1000, arr2) * mask_arr_HRP

        # Convert the array to signed 16-bit integer (int16) data type
        tabulation_bin_id_masked = tabulation_bin_id_masked.astype(np.int16)

        # Create the final image using tabulation_bin_image function
        self.array_to_image(risk30_hrp, out_fn1, tabulation_bin_id_masked,
                                     gdal.GDT_Int16, -1)
        return tabulation_bin_id_masked

###Step2 Calculate the Relative Frequencies###
    def create_relative_frequency_table(self, tabulation_bin_id_masked, deforestation_hrp, csv_name):
        """
        Create dataframe
        :param tabulation_bin_id_masked: array with id and total deforestation
        :param deforestation_hrp: Deforestation Map during the CAL/HRP
        :return: merged_df: relative frequency dataframe
        """
        # Calculate array area of the bin [integer] (in pixels) for Col3 using np.unique and counts function, excluding 0
        unique, counts = np.unique(tabulation_bin_id_masked[tabulation_bin_id_masked != 0], return_counts=True)
        # Convert to array
        arr_counts = np.asarray((unique, counts)).T

        # Calculate total deforestation within the bin [integer] array for Col2
        arr3 = self.image_to_array(deforestation_hrp)

        # deforestation_within_bin will have tabulation_bin_id value in deforestation pixel
        deforestation_within_bin = tabulation_bin_id_masked * arr3
        # Use np.unique to counts total deforestation in each bin
        unique1, counts1 = np.unique(deforestation_within_bin[deforestation_within_bin != 0], return_counts=True)
        # Convert to array
        arr_counts_deforestion = np.asarray((unique1, counts1)).T

        # Create pandas DataFrames
        df1 = pd.DataFrame(arr_counts_deforestion, columns=['ID', 'Total Deforestation(pixel)'])
        df2 = pd.DataFrame(arr_counts, columns=['ID', 'Area of the Bin(pixel)'])

        # Merge the two DataFrames based on the 'id' column using an outer join to include all rows from both DataFrames
        merged_df = pd.merge(df1, df2, on='ID', how='outer').fillna(0)

        # Calculate Average Deforestation by performing the division operation of col2 and col3 and add a new column to merged_df
        merged_df['Average Deforestation(pixel)'] = merged_df.iloc[:, 1].astype(float) / merged_df.iloc[:, 2].astype(float)

        # Sort the DataFrame based on the 'ID'
        merged_df = merged_df.sort_values(by='ID')

        # Reset the index to have consecutive integer indices
        merged_df = merged_df.reset_index(drop=True)

        csv_file_path = csv_name
        merged_df.to_csv(csv_file_path, index=False)

        return merged_df

###Step 3 Fitting Phase: create the fitted density map###
    def create_fit_density_map(self,risk30_hrp, tabulation_bin_id_masked, merged_df, out_fn2):
        '''
        Create the fitting density map, this function used for fitting phase (CAL and HRP)
        :param risk30_hrp: the 30-class vulnerability map for the CAL/HRP
        :param tabulation_bin_id_masked: array for tabulation bin id in fitting Phase
        :param merged_df: relative frequency dataframe
        :return:
        '''
        # Insert index=0 row into first row of merged_df DataFrame
        new_row = pd.DataFrame({'ID': [0], 'Total Deforestation(pixel)': [0], 'Area of the Bin(pixel)': [0],
                                'Average Deforestation(pixel)': [0]})
        merged_df = pd.concat([new_row, merged_df]).reset_index(drop=True)

        # Using numpy.searchsorted() to assign values to 'id'
        df_sorted = merged_df.sort_values('ID')
        sorted_indices = df_sorted['ID'].searchsorted(tabulation_bin_id_masked)
        relative_frequency_arr = tabulation_bin_id_masked[:] = df_sorted['Average Deforestation(pixel)'].values[sorted_indices]

        # Calculate areal_resolution_of_map_pixels
        in_ds4 = gdal.Open(risk30_hrp)
        P1 = in_ds4.GetGeoTransform()[1]
        P2 = abs(in_ds4.GetGeoTransform()[5])
        areal_resolution_of_map_pixels = P1 * P2 / 10000

        # Relative_frequency multiplied by the areal resolution of the map pixels to express the probabilities as densities
        fit_density_arr=relative_frequency_arr * areal_resolution_of_map_pixels

        # Create the final fit_density_map image using tabulation_bin_image function
        self.array_to_image(risk30_hrp, out_fn2, fit_density_arr, gdal.GDT_Float32, -1)

        return

###Step 3 Prediction Phase: create the adjusted predicted density map###
    def tabulation_bin_id_VP (self, risk30_vp, municipality, out_fn1):
        """
        This function is to create modeling region array(tabulation_bin_id_VP_masked)
        and modeling region map(tabulation_bin_image_vp)
        :param risk30_vp: The 30-class vulnerability map for the CNF/VP
        :param municipality: Subdivision image
        :param out_fn1: user input
        :return: tabulation_bin_id_VP_masked: tabulation bin id array in CNF/VP
        """

        # Convert municipality and risk30_vp to NumPy array
        arr2 = self.image_to_array(municipality)
        arr4 = self.image_to_array(risk30_vp)

        # Create a mask where the risk30_hrp value larger than 1 reclassed into 1
        mask_arr_VP = np.where(arr4 > 0, 1, arr4)

        # Calculate tabulation bin id of CNF/VP with mask
        tabulation_bin_id_VP_masked = np.add(arr4 * 1000, arr2) * mask_arr_VP

        # Convert the array to signed 16-bit integer (int16) data type
        tabulation_bin_id_VP_masked = tabulation_bin_id_VP_masked.astype(np.int16)
        #Write image to disk
        self.array_to_image(risk30_vp, out_fn1, tabulation_bin_id_VP_masked,
                                     gdal.GDT_Int16, -1)

        return tabulation_bin_id_VP_masked


    def calculate_prediction_density_arr(self,risk30_vp, tabulation_bin_id_VP_masked, csv):
        '''
        Calculate the prediction density arry
        :param tabulation_bin_id_VP_masked: array for tabulation bin id in CNF/VP
        :param csv: relative frequency table
        :param risk30_vp: the 30-class vulnerability map for the CNF/VP
        :return: prediction_density_arr: modeled deforestation (MD)
        '''
        # Read Relative Frequency csv file
        merged_df=pd.read_csv(csv)

        # Insert index=0 row into first row of merged_df DataFrame
        new_row = pd.DataFrame({'ID': [0], 'Total Deforestation(pixel)': [0], 'Area of the Bin(pixel)': [0],
                                'Average Deforestation(pixel)': [0]})
        merged_df = pd.concat([new_row, merged_df]).reset_index(drop=True)

        # Using numpy.searchsorted() to assign values to 'id'
        df_sorted = merged_df.sort_values('ID')
        sorted_indices = df_sorted['ID'].searchsorted(tabulation_bin_id_VP_masked)
        relative_frequency_arr = tabulation_bin_id_VP_masked[:] = df_sorted['Average Deforestation(pixel)'].values[sorted_indices]

        # Calculate areal_resolution_of_map_pixels
        in_ds4 = gdal.Open(risk30_vp)
        P1 = in_ds4.GetGeoTransform()[1]
        P2 = abs(in_ds4.GetGeoTransform()[5])
        areal_resolution_of_map_pixels = P1 * P2 / 10000

        # Relative_frequency multiplied by the areal resolution of the map pixels to express the probabilities as densities
        prediction_density_arr=relative_frequency_arr * areal_resolution_of_map_pixels

        return prediction_density_arr

    def calculate_adjustment_ratio_cnf(self, prediction_density_arr, deforestation_cnf):
        '''
        Calculate the Adjustment Ratio (AR) in CNF
        :param prediction_density_arr: modeled deforestation (MD)
        :param deforestation_cnf: deforestation binary map in cnf
        :return: AR
        '''

        # Sum up the pixels in the prediction density map. This is the modeled deforestation (MD).
        MD = np.sum(prediction_density_arr)

        # Calculate areal_resolution_of_map_pixels
        in_ds5 = gdal.Open(deforestation_cnf)
        P1 = in_ds5.GetGeoTransform()[1]
        P2 = abs(in_ds5.GetGeoTransform()[5])
        areal_resolution_of_map_pixels = P1 * P2 / 10000

        # Convert deforestation_cnf to array in ha
        arr5 = self.image_to_array(deforestation_cnf)
        arr5_ha=arr5 * areal_resolution_of_map_pixels

        # Calculate the Actual Deforestation (AD) during the confirmation period
        AD = np.sum(arr5_ha)

        # AR = AD / MD
        AR = AD / MD
        return AR

    def calculate_adjustment_ratio(self,prediction_density_arr, expected_deforestation):
        '''
        Calculate the Adjustment Ratio (AR) in VP
        :param prediction_density_arr: modeled deforestation (MD)
        :param expected_deforestation: user input
        :return: AR
        '''

        # Sum up the pixels in the prediction density map. This is the modeled deforestation (MD).
        MD = np.sum(prediction_density_arr)

        # AR = ED / MD
        AR = expected_deforestation / MD
        return AR

    def adjusted_prediction_density_array (self, prediction_density_arr, risk30_vp, AR):
        '''
        Create adjusted prediction density array
        :param prediction_density_arr:modeled deforestation (MD)
        :param risk30_vp: risk30_vp image
        :param AR:Adjustment Ratio
        :return: adjusted_prediction_density_np_arr
        '''

        # Calculate the maximum density
        # Calculate areal_resolution_of_map_pixels
        in_ds4 = gdal.Open(risk30_vp)
        P1 = in_ds4.GetGeoTransform()[1]
        P2 = abs(in_ds4.GetGeoTransform()[5])
        maximum_density = P1 * P2 / 10000

        # Adjusted_Prediction_Density_Map = AR x Prediction_Density _Map
        adjusted_prediction_density_arr=AR*prediction_density_arr

        # Reclassify all pixels greater than the maximum (e.g., 0.09) to be the maximum
        adjusted_prediction_density_arr[adjusted_prediction_density_arr > maximum_density] = maximum_density

        return adjusted_prediction_density_arr


    def adjusted_prediction_density_map (self, prediction_density_arr, risk30_vp, AR, out_fn2):
        '''
        Create adjusted prediction density map
        :param prediction_density_arr:modeled deforestation (MD)
        :param risk30_vp: risk30_vp image
        :param AR:Adjustment Ratio
        :param out_fn2: user input
        :return:
        '''

        # Calculate the maximum density
        # Calculate areal_resolution_of_map_pixels
        in_ds4 = gdal.Open(risk30_vp)
        P1 = in_ds4.GetGeoTransform()[1]
        P2 = abs(in_ds4.GetGeoTransform()[5])
        maximum_density = P1 * P2 / 10000

        # Adjusted_Prediction_Density_Map = AR x Prediction_Density _Map
        adjusted_prediction_density_arr=AR*prediction_density_arr

        # Reclassify all pixels greater than the maximum (e.g., 0.09) to be the maximum
        adjusted_prediction_density_arr[adjusted_prediction_density_arr > maximum_density] = maximum_density

        # Create imagery
        self.array_to_image(risk30_vp, out_fn2, adjusted_prediction_density_arr, gdal.GDT_Float32, -1)

        return

    def adjusted_prediction_density_map_annual (self, prediction_density_arr, risk30_vp, AR, out_fn2, time):
        '''
        Create adjusted prediction density map for annual
        :param prediction_density_arr:modeled deforestation (MD)
        :param risk30_vp: risk30_vp image
        :param AR:Adjustment Ratio
        :param out_fn2: user input
        :return:
        '''

        # Calculate the maximum density
        # Calculate areal_resolution_of_map_pixels
        in_ds4 = gdal.Open(risk30_vp)
        P1 = in_ds4.GetGeoTransform()[1]
        P2 = abs(in_ds4.GetGeoTransform()[5])
        maximum_density = P1 * P2 / 10000

        # Adjusted_Prediction_Density_Map = AR x Prediction_Density _Map
        adjusted_prediction_density_arr=AR*prediction_density_arr

        # Reclassify all pixels greater than the maximum (e.g., 0.09) to be the maximum
        adjusted_prediction_density_arr[adjusted_prediction_density_arr > maximum_density] = maximum_density

        # Convert the result back to an annual rate by dividing by the number of years in the VP
        adjusted_prediction_density_arr_annual=adjusted_prediction_density_arr/time

        # Create imagery
        self.array_to_image(risk30_vp, out_fn2, adjusted_prediction_density_arr_annual, gdal.GDT_Float32, -1)

        return

    def replace_ref_system(self, in_fn, out_fn):
        '''
         RST raster format: correct reference system name in rdc file
         :param in_fn: datasource to copy correct projection name
         :param out_fn: rst raster file
        '''
        if out_fn.split('.')[-1] == 'rst':
            read_file_name, _ = os.path.splitext(in_fn)
            write_file_name, _ = os.path.splitext(out_fn)
            temp_file_path = 'rdc_temp.rdc'

            with open(read_file_name + '.rdc', 'r') as read_file:
                for line in read_file:
                    if line.startswith("ref. system :"):
                        correct_name=line
                        break

            if correct_name:
                with open(write_file_name + '.rdc', 'r') as read_file, open(temp_file_path, 'w') as write_file:
                    for line in read_file:
                        if line.startswith("ref. system :"):
                            write_file.write(correct_name)
                        else:
                            write_file.write(line)

                # Move the temp file to replace the original
                shutil.move(temp_file_path, write_file_name + '.rdc')


    def execute_workflow_fit(self, directory,risk30_hrp,municipality, deforestation_hrp, csv_name, out_fn1, out_fn2):
        '''
        Create workflow function for CAL and HRP
        '''
        self.progress_updated.emit(0)
        data_folder = self.set_working_directory(directory)
        self.progress_updated.emit(10)
        tabulation_bin_id_masked = self.tabulation_bin_id_HRP(risk30_hrp,municipality,out_fn1)
        self.replace_ref_system(municipality, out_fn1)
        self.progress_updated.emit(50)
        merged_df = self.create_relative_frequency_table(tabulation_bin_id_masked,
                                                                              deforestation_hrp, csv_name)
        self.progress_updated.emit(75)
        self.create_fit_density_map(risk30_hrp, tabulation_bin_id_masked,
                                                              merged_df, out_fn2)
        self.replace_ref_system(municipality, out_fn2)
        self.progress_updated.emit(100)
        # After processing, emit processCompleted or any other signal as needed
        return

    def execute_workflow_cnf(self, directory, max_iterations, csv, municipality, deforestation_cnf, risk30_vp, out_fn1, out_fn2):
        '''
        Create workflow function for CNF
        :param max_iterations: maximum number of iterations
        '''
        self.progress_updated.emit(0)
        data_folder = self.set_working_directory(directory)
        self.progress_updated.emit(10)
        tabulation_bin_id_VP_masked = self.tabulation_bin_id_VP(risk30_vp, municipality, out_fn1)
        self.replace_ref_system(municipality, out_fn1)
        self.progress_updated.emit(30)

        # Check modeling region IDs present in the prediction stage but absent in the fitting stage
        id_difference = self.check_modeling_region_ids(csv, out_fn1)

        # If there are missing bins, calculate the relative frequency and create a new csv file
        if id_difference.size > 0:
            self.calculate_missing_bins_rf(id_difference, csv)

        self.progress_updated.emit(40)

        prediction_density_arr = self.calculate_prediction_density_arr(risk30_vp, tabulation_bin_id_VP_masked,csv)
        self.progress_updated.emit(50)
        AR = self.calculate_adjustment_ratio_cnf(prediction_density_arr, deforestation_cnf)
        self.progress_updated.emit(75)
        # Set a maximum number of iterations to avoid infinite loop
        iteration_count = 0
        new_prediction_density_arr = None

        # When AR > 1.00001 and iteration_count <= max_iterations, treat the result as new prediction density map to iterate the AR util AR is <=1.00001 or iteration_count = max_iterations
        while AR > 1.00001 and iteration_count <= max_iterations:
            new_prediction_density_arr = self.adjusted_prediction_density_array(prediction_density_arr, risk30_vp, AR)
            AR = self.calculate_adjustment_ratio_cnf(new_prediction_density_arr, deforestation_cnf)
            iteration_count += 1
        if iteration_count <= int(max_iterations):
            selected_density_arr = new_prediction_density_arr if new_prediction_density_arr is not None else prediction_density_arr
            self.adjusted_prediction_density_map(selected_density_arr, risk30_vp, AR, out_fn2)
            self.replace_ref_system(municipality, out_fn2)

        else:
            print("Maximum number of iterations reached. Please reset the maximum number of iterations.")

        self.progress_updated.emit(100)

        return id_difference

    def execute_workflow_vp(self, directory,max_iterations, csv, municipality, expected_deforestation, risk30_vp, out_fn1, out_fn2, time):
        '''
        Create workflow function for VP
        :param max_iterations: maximum number of iterations
        '''
        self.progress_updated.emit(0)
        data_folder = self.set_working_directory(directory)
        self.progress_updated.emit(10)
        tabulation_bin_id_VP_masked = self.tabulation_bin_id_VP(risk30_vp, municipality, out_fn1)
        self.replace_ref_system(municipality, out_fn1)
        self.progress_updated.emit(30)

        # Check modeling region IDs present in the prediction stage but absent in the fitting stage
        id_difference = self.check_modeling_region_ids(csv, out_fn1)

        # If there are missing bins, calculate the relative frequency and create a new csv file
        if id_difference.size > 0:
            self.calculate_missing_bins_rf(id_difference, csv)

        self.progress_updated.emit(40)

        prediction_density_arr = self.calculate_prediction_density_arr(risk30_vp, tabulation_bin_id_VP_masked,csv)
        self.progress_updated.emit(50)
        AR = self.calculate_adjustment_ratio(prediction_density_arr, expected_deforestation)
        self.progress_updated.emit(75)
        # Set a maximum number of iterations to avoid infinite loop
        iteration_count = 0
        new_prediction_density_arr = None

        # When AR > 1.00001 and iteration_count <= max_iterations, treat the result as new prediction density map to iterate the AR util AR is <=1.00001 or iteration_count = max_iterations
        while AR > 1.00001 and iteration_count <= max_iterations:
            new_prediction_density_arr = self.adjusted_prediction_density_array(prediction_density_arr, risk30_vp, AR)
            AR = self.calculate_adjustment_ratio(new_prediction_density_arr, expected_deforestation)
            iteration_count += 1
            # Emitting progress based on the current iteration_count and max_iterations
        if iteration_count <= int(max_iterations):
            selected_density_arr = new_prediction_density_arr if new_prediction_density_arr is not None else prediction_density_arr
            self.adjusted_prediction_density_map_annual(selected_density_arr, risk30_vp, AR, out_fn2, time)
            self.replace_ref_system(municipality, out_fn2)
        else:
            print("Maximum number of iterations reached. Please reset the maximum number of iterations.")

        self.progress_updated.emit(100)

        return id_difference

    def check_modeling_region_ids(self, csv, out_fn):
        '''
        Check modeling region IDs present in the prediction stage but absent in the fitting stage.
        :param csv: csv file of relative frequency in fitiing stage
        :param out_fn: modeling region image in prediction stage
        :return: id_difference: A set of modeling region IDs np array that exist only in the prediction stage
        '''
        fit_model_region_id = pd.read_csv(csv)['ID'].to_numpy()
        pre_model_region_arr = self.image_to_array(out_fn)
        pre_model_region_id = np.unique(pre_model_region_arr[pre_model_region_arr != 0])
        id_difference = np.setdiff1d(pre_model_region_id, fit_model_region_id)

        return id_difference

    def calculate_missing_bins_rf (self, id_difference, csv):
        '''
        If one or more empty bins are found, compute the jurisdiction-wide weighted average of relative frequencies for
        missing bins and create a new csv file
        :param csv: csv file of relative frequency in the fitting stage
        :param id_difference: A set of modeling region IDs np array that exist only in the prediction stage
        :return
        '''
        # Convert modeling region ids to vulnerability zone id
        df=pd.read_csv(csv)
        df['v_zone'] = (df['ID'] // 1000).astype(int)

        # Convert missing bin ids to vulnerability zone id
        missing_v_zone = [x // 1000 for x in id_difference]

        # Select rows
        filtered_df = df[df['v_zone'].isin(missing_v_zone)].copy()

        # Created new column
        filtered_df['Total Deforestation(pixel)'] = filtered_df['Area of the Bin(pixel)'] * filtered_df['Average Deforestation(pixel)']

        # Group by and sum area and weighted relative frequency
        aggregated_df = filtered_df.groupby('v_zone')[['Total Deforestation(pixel)', 'Area of the Bin(pixel)']].sum().reset_index()

        # Calculate Average Deforestation
        aggregated_df['Average Deforestation(pixel)']=aggregated_df['Total Deforestation(pixel)']/aggregated_df['Area of the Bin(pixel)']

        # Create a new dataframe id_difference_df
        id_difference_df = pd.DataFrame(id_difference, columns=['ID'])
        id_difference_df['v_zone'] = missing_v_zone

        # Create missing bins dataframe by outer join aggregated_df and id_difference_df
        missing_bins_df = pd.merge(id_difference_df,aggregated_df , on='v_zone', how='outer')

        # Insert missing bins dataframe back to csv file
        df_new = pd.concat([df, missing_bins_df], ignore_index=True)

        # Sorting by column "ID"
        df_new=df_new.sort_values(by=['ID'], ascending=True)

        # Drop column 'v_zone'
        df_new=df_new.drop(['v_zone'], axis=1)

        # Copy the original csv file copy and rename it to csv_orig
        shutil.copyfile(csv, csv.split('.')[0] + '_orig' + '.csv')

        # Save the new result to csv
        df_new.to_csv(csv, index=False)