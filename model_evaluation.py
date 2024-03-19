import os
import sys
from osgeo import gdal, osr, ogr
from osgeo.gdalconst import *
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import Voronoi
import scipy.stats as stats
import geopandas as gpd
import shapely
import seaborn as sns
from shapely.geometry import Point
import pandas as pd
from PyQt5.QtCore import QObject, pyqtSignal
import shutil
from geopandas import GeoDataFrame

# GDAL exceptions
gdal.UseExceptions()

class ModelEvaluation(QObject):
    progress_updated = pyqtSignal(int)
    def __init__(self):
        super(ModelEvaluation, self).__init__()
        self.data_folder = None

    def set_working_directory(self, directory: object) -> object:
        '''
        Set up the working directory
        :param directory: your local directory with all dat files
        '''
        self.progress_updated.emit(0)
        self.data_folder = directory
        os.chdir(self.data_folder)

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

    def replace_legend(self, out_fn):
        '''
         RST raster format: correct legend in rdc file of Combined Deforestation Review Map
         :param out_fn: rst raster file
        '''
        if out_fn.split('.')[-1] == 'rst':
            base_name, _ = os.path.splitext(out_fn)
            temp_file_path = 'rdc_temp.rdc'

            with open(base_name + '.rdc', 'r') as read_file, open(temp_file_path, 'w') as write_file:
                for line in read_file:
                    if line.startswith("legend cats :"):
                        write_file.write("legend cats : " + '3'+'\n')
                        # Write the three new lines
                        write_file.write("code 1      : "+"Forest at the start of HRP"+"\n")
                        write_file.write("code 2      : "+"Deforestation within CAL"+"\n")
                        write_file.write("code 3      : "+"Deforestation within CNF"+"\n")
                    else:
                        write_file.write(line)
            shutil.move(temp_file_path, base_name + '.rdc')

    def create_mask_polygon(self, mask):
        '''
        Create municipality mask polygon
        :param mask: mask of the jurisdiction (binary map)
        :return:
        '''
        in_ds = gdal.Open(mask)
        in_band = in_ds.GetRasterBand(1)

        # Set up osr spatial reference
        projection = in_ds.GetProjection().encode('utf-8', 'backslashreplace').decode('utf-8')
        self.progress_updated.emit(10)
        spatial_ref = osr.SpatialReference()
        spatial_ref.ImportFromWkt(projection)

        # Create a temporary shapefile to store all polygons
        temp_layername = "TEMP_POLYGONIZED"
        driver = ogr.GetDriverByName("ESRI Shapefile")
        temp_ds = driver.CreateDataSource(temp_layername + ".shp")
        temp_layer = temp_ds.CreateLayer(temp_layername, srs=spatial_ref)
        gdal.Polygonize(in_band, in_band, temp_layer, -1, [], callback=None)
        self.progress_updated.emit(20)

        features = [(feature.GetGeometryRef().GetArea(), feature) for feature in temp_layer]
        largest_polygon = max(features, key=lambda item: item[0])[1]

        # Fetch the geometry of the largest feature
        largest_polygon_geom = largest_polygon.GetGeometryRef().Clone()

        # Close the temporary data source
        temp_ds.Destroy()

        # Create the final shapefile to store the largest polygon
        final_layername = "POLYGONIZED_MASK"
        final_ds = driver.CreateDataSource(final_layername + ".shp")
        final_layer = final_ds.CreateLayer(final_layername, srs=spatial_ref, geom_type=ogr.wkbPolygon)

        # Create a new feature
        feature_defn = final_layer.GetLayerDefn()
        out_feature = ogr.Feature(feature_defn)
        out_feature.SetGeometry(largest_polygon_geom)

        # Add the feature to the final layer
        final_layer.CreateFeature(out_feature)

        # Cleanup
        out_feature = None
        final_ds.Destroy()

        return

    def bbox_to_pixel_offsets(self,gt, bbox):
        '''
        https://gist.github.com/perrygeo/5667173
        '''
        originX = gt[0]
        originY = gt[3]
        pixel_width = gt[1]
        pixel_height = gt[5]
        x1 = int((bbox[0] - originX) / pixel_width)
        x2 = int((bbox[1] - originX) / pixel_width) + 1

        y1 = int((bbox[3] - originY) / pixel_height)
        y2 = int((bbox[2] - originY) / pixel_height) + 1

        xsize = x2 - x1
        ysize = y2 - y1
        return (x1, y1, xsize, ysize)

    def zonal_stats(self, vector_path, raster_path, nodata_value=None, global_src_extent=False):
        '''
        https://gist.github.com/perrygeo/5667173
        '''
        rds = gdal.Open(raster_path, GA_ReadOnly)
        assert (rds)
        rb = rds.GetRasterBand(1)
        rgt = rds.GetGeoTransform()

        if nodata_value:
            nodata_value = float(nodata_value)
            rb.SetNoDataValue(nodata_value)

        vds = ogr.Open(vector_path, GA_ReadOnly)  # TODO maybe open update if we want to write stats
        assert (vds)
        vlyr = vds.GetLayer(0)

        # create an in-memory numpy array of the source raster data
        # covering the whole extent of the vector layer
        if global_src_extent:
            # use global source extent
            # useful only when disk IO or raster scanning inefficiencies are your limiting factor
            # advantage: reads raster data in one pass
            # disadvantage: large vector extents may have big memory requirements
            src_offset = self.bbox_to_pixel_offsets(rgt, vlyr.GetExtent())
            src_array = rb.ReadAsArray(*src_offset)

            # calculate new geotransform of the layer subset
            new_gt = (
                (rgt[0] + (src_offset[0] * rgt[1])),
                rgt[1],
                0.0,
                (rgt[3] + (src_offset[1] * rgt[5])),
                0.0,
                rgt[5]
            )

        mem_drv = ogr.GetDriverByName('Memory')
        driver = gdal.GetDriverByName('MEM')

        # Loop through vectors
        stats = []
        feat = vlyr.GetNextFeature()
        while feat is not None:

            if not global_src_extent:
                # use local source extent
                # fastest option when you have fast disks and well indexed raster (ie tiled Geotiff)
                # advantage: each feature uses the smallest raster chunk
                # disadvantage: lots of reads on the source raster
                src_offset = self.bbox_to_pixel_offsets(rgt, feat.geometry().GetEnvelope())
                src_array = rb.ReadAsArray(*src_offset)

                # calculate new geotransform of the feature subset
                new_gt = (
                    (rgt[0] + (src_offset[0] * rgt[1])),
                    rgt[1],
                    0.0,
                    (rgt[3] + (src_offset[1] * rgt[5])),
                    0.0,
                    rgt[5]
                )

            # Create a temporary vector layer in memory
            mem_ds = mem_drv.CreateDataSource('out')
            mem_layer = mem_ds.CreateLayer('poly', None, ogr.wkbPolygon)
            mem_layer.CreateFeature(feat.Clone())

            # Rasterize it
            rvds = driver.Create('', src_offset[2], src_offset[3], 1, gdal.GDT_Byte)
            rvds.SetGeoTransform(new_gt)
            gdal.RasterizeLayer(rvds, [1], mem_layer, burn_values=[1])
            rv_array = rvds.ReadAsArray()

            # Mask the source data array with our current feature
            # we take the logical_not to flip 0<->1 to get the correct mask effect
            # we also mask out nodata values explictly
            masked = np.ma.MaskedArray(
                src_array,
                mask=np.logical_or(
                    src_array == nodata_value,
                    np.logical_not(rv_array)
                )
            )

            feature_stats = {
                'sum': float(masked.sum())}

            stats.append(feature_stats)

            rvds = None
            mem_ds = None
            feat = vlyr.GetNextFeature()

        vds = None
        rds = None
        return stats

    def vector_to_raster(self,vector_fn,in_fn,raster_fn,data_type, nodata=None):
        '''
          Create residual raster image from vector file
         :param vector_fn: vector datasource
         :param in_fn: datasource to copy projection and geotransform from
         :param raster_fn:path to create raster file
         :param data_type:output data type
         :param nodata:optional NoData value
         :return
        '''
        # Open the vector data source
        source_ds = ogr.Open(vector_fn)
        source_layer = source_ds.GetLayer()

        in_ds = gdal.Open(in_fn)
        output_format = raster_fn.split('.')[-1].upper()
        if (output_format == 'TIF'):
            output_format = 'GTIFF'
        elif (output_format == 'RST'):
            output_format = 'rst'
        driver = gdal.GetDriverByName(output_format)
        out_ds = driver.Create(raster_fn, in_ds.RasterXSize, in_ds.RasterYSize, 1, data_type, options=["BigTIFF=YES"])
        out_band = out_ds.GetRasterBand(1)
        out_ds.SetGeoTransform(in_ds.GetGeoTransform())

        out_ds.SetProjection(in_ds.GetProjection().encode('utf-8', 'backslashreplace').decode('utf-8'))

        if nodata is not None:
            out_band.SetNoDataValue(nodata)
        # Rasterize
        gdal.RasterizeLayer(out_ds, [1], source_layer, options=["ATTRIBUTE=Residuals"])

        # Cleanup
        out_band.FlushCache()
        out_ds.FlushCache()
        return

    def remove_edge_cells(self, full_voronoi_grid: GeoDataFrame, area_mask: GeoDataFrame,
                          area_percentile_threshold: float) -> GeoDataFrame:
        '''
        Ensure thiessen polygon cells retain percentile threshold of maximum size after intersection with mask of the jurisdiction
         :param full_voronoi_grid: thiessen polygon dataframe
         :param area_mask: mask of the jurisdiction
         :param area_percentile_threshold: area percentile threshold
         :return  thiessen_gdf: result dataframe
        '''
        thiessen_gdf = gpd.overlay(full_voronoi_grid, area_mask, how="intersection")
        # get area of each polygon
        thiessen_gdf["area"] = thiessen_gdf.area

        max_area = thiessen_gdf["area"].max()
        # using the area, calculate size of cell compared to max
        thiessen_gdf["percentcell"] = thiessen_gdf["area"] / max_area

        # select cells with more than thresh% of their area within the mask
        thiessen_gdf = thiessen_gdf[thiessen_gdf["percentcell"] > area_percentile_threshold]

        return thiessen_gdf

    def create_thiessen_polygon (self, grid_area, mask, density, deforestation, out_fn, raster_fn):
        '''
          Create thiessen polygon
         :param grid_area: assessment grid cell area or 100,000 (ha)
         :param mask: mask of the jurisdiction (binary map)
         :param density: adjusted prediction density map
         :param deforestation:Deforestation Map during the HRP
         :param csv_name:Name of performance chart
         :return  clipped_gdf: thiessen polygon dataframe
        '''
        ## Create sample points:
        # Open the Polygonized_Mask shapefile
        mask_df = gpd.GeoDataFrame.from_file('POLYGONIZED_MASK.shp')

        # Calculate grid size
        in_ds = gdal.Open(mask)
        grid_size = int(np.sqrt(grid_area * 10000)) // int(in_ds.GetGeoTransform()[1])

        # Systematic Sampling
        sample_points = []
        for y in range(-1 * grid_size, in_ds.RasterYSize + 1 * grid_size, grid_size):
            for x in range(-1 * grid_size, in_ds.RasterXSize + 1 * grid_size, grid_size):
                # Convert raster coordinates to geographic coordinates
                geo_x = in_ds.GetGeoTransform()[0] + x * in_ds.GetGeoTransform()[1]
                geo_y = in_ds.GetGeoTransform()[3] + y * in_ds.GetGeoTransform()[5]
                sample_points.append((geo_x, geo_y))

        # Convert sample_points list to DataFrame
        df = pd.DataFrame(sample_points, columns=['geo_x', 'geo_y'])
        df['coords'] = list(zip(df['geo_x'], df['geo_y']))
        df['coords_P'] = df['coords'].apply(Point)
        points_df = gpd.GeoDataFrame(df, geometry='coords_P', crs=mask_df.crs)

        # Convert the 'coords' column to a numpy array
        coords = np.array(points_df['coords'].tolist())

        ## Create thiessen polygon
        polygon = mask_df.geometry.unary_union

        vor = Voronoi(points=coords)

        # Polygonize the line ridge is not infinity
        lines = [shapely.geometry.LineString(vor.vertices[line]) for line in
                 vor.ridge_vertices if -1 not in line]

        polys = shapely.ops.polygonize(lines)

        # Convert Voronoi polygons (polys) into a GeoDataFrame.
        voronois = gpd.GeoDataFrame(geometry=gpd.GeoSeries(polys), crs=mask_df.crs)
        self.progress_updated.emit(30)

        # Convert the study area to GeoDataFrame.
        polydf = gpd.GeoDataFrame(geometry=[polygon], crs=mask_df.crs)

        # Ensure Thiessen Polygon cells retain 99.9% of maximum size after intersection with study area
        thiessen_gdf = self.remove_edge_cells(voronois, polydf, 0.999)

        self.progress_updated.emit(40)

        # Extract polygons and multipolygons from the entire thiessen_gdf (including GeometryCollections)
        extracted_gdf = thiessen_gdf['geometry'].apply(
            lambda geom: [g for g in geom.geoms if
                          g.geom_type in ['Polygon', 'MultiPolygon']] if geom.geom_type == 'GeometryCollection' else [
                geom]
        ).explode().reset_index(drop=True)

        clipped_gdf = gpd.GeoDataFrame({'geometry': extracted_gdf}, crs=thiessen_gdf.crs)

        # Calculate area in hectares
        clipped_gdf['Area_ha'] = clipped_gdf['geometry'].area / 10000

        ## Calculate zonal statistics

        ## Convert clipped_gdf to shapefile
        vector_temp_path = "temp_vector.shp"
        clipped_gdf.to_file(vector_temp_path)

        # Actual Deforestation(ha)
        stats = self.zonal_stats(vector_temp_path, deforestation, nodata_value=0)

        self.progress_updated.emit(50)

        # Calculate areal_resolution_of_map_pixels
        in_ds4 = gdal.Open(density)
        P1 = in_ds4.GetGeoTransform()[1]
        P2 = abs(in_ds4.GetGeoTransform()[5])
        areal_resolution_of_map_pixels = P1 * P2 / 10000

        # Add the results back to the GeoDataFrame
        clipped_gdf['Actual Deforestation(ha)'] = [(item['sum'] if item['sum'] is not None else 0) * areal_resolution_of_map_pixels for item in stats]
        self.progress_updated.emit(60)

        # Predicted Deforestation(ha)
        stats1 = self.zonal_stats(vector_temp_path, density, nodata_value=0)
        self.progress_updated.emit(70)

        clipped_gdf['Predicted Deforestation(ha)'] = [(item['sum'] if item['sum'] is not None else 0) for item in stats1]

        # ID
        clipped_gdf['ID'] = range(1, len(clipped_gdf) + 1)

        # Replace NaN or blank values with '0'
        columns_to_fill = ['Actual Deforestation(ha)', 'Predicted Deforestation(ha)']
        for column in columns_to_fill:
            clipped_gdf[column] = clipped_gdf[column].fillna(0)

        # Calculate residuals
        clipped_gdf['Residuals(ha)'] = clipped_gdf['Predicted Deforestation(ha)'] - clipped_gdf['Actual Deforestation(ha)']

        # Export to csv
        csv_file_path = out_fn.split('.')[0]+'.csv'
        clipped_gdf.drop('geometry', axis=1).to_csv(csv_file_path, columns=['ID', 'Actual Deforestation(ha)', 'Predicted Deforestation(ha)','Residuals(ha)'],
                                                    index=False)

        # Rename columns title for shapefile
        clipped_gdf = clipped_gdf.rename(columns={'Predicted Deforestation(ha)': 'PredDef',
                                                  'Actual Deforestation(ha)': 'ActualDef',
                                                  'Residuals(ha)':'Residuals'})

        # Save the updated GeoDataFrame back to a shapefile

        tp_file_path = out_fn.split('.')[0]+'.shp'
        clipped_gdf.to_file(tp_file_path)

        # Create residual map
        self.vector_to_raster(tp_file_path, mask, raster_fn, gdal.GDT_Float32,-1)

        return clipped_gdf

    def create_deforestation_map (self, fmask, deforestation_cal, deforestation_cnf, out_fn_def):
        self.progress_updated.emit(80)
        arr_fmask = self.image_to_array(fmask)
        arr_def_cal = self.image_to_array(deforestation_cal)
        arr_def_cnf = self.image_to_array(deforestation_cnf)

        deforestation_arr=np.copy(arr_fmask)

        deforestation_arr[arr_def_cnf == 1] = 3
        deforestation_arr[(arr_def_cnf == 0) & (arr_def_cal == 1)] = 2
        deforestation_arr[(arr_def_cnf == 0) & (arr_def_cal == 0) & (fmask == 1)] = 1

        #write deforestation_map
        self.array_to_image(fmask, out_fn_def, deforestation_arr, gdal.GDT_Int16, -1)

        return

    def create_plot(self, grid_area, clipped_gdf, title, out_fn,xmax=None, ymax=None):
        '''
        Create plot and save to local directory
        :param grid_area: assessment grid cell area or 100,000 (ha)
        :param clipped_gdf: thiessen_polygon geo-dataframe
        :param title:plot title
        :param out_fn: plot path
        :param xmax: maximum x-axis value
        :param ymax: maximum y-axis value
        :return
        '''
        self.progress_updated.emit(90)
        # Set Seaborn Style
        sns.set()

        # prepare the X/Y data
        X = np.array(clipped_gdf['ActualDef'], dtype=np.float64)
        Y = np.array(clipped_gdf['PredDef'], dtype=np.float64)

        ## Perform linear regression
        slope, intercept, _, _, _ = stats.linregress(X, Y)

        # Create the equation string
        equation = f'Y = {slope:.4f} * X + {intercept:.2f}'

        # Calculate the trend line
        trend_line = slope * X + intercept

        ## Calculate R square
        # Get the correlation coefficient
        r = np.corrcoef(X, Y)[0, 1]
        # Square the correlation coefficient
        r_squared = r ** 2

        ##Calculate MedAE
        distance_arr = [abs(X[i] - Y[i]) for i in range(len(X))]
        MedAE = np.median(distance_arr)

        ## Calculate MedAE percent
        MedAE_percent = (MedAE / int(grid_area)) * 100

        # Set the figure size
        plt.figure(figsize=(8, 6))

        # Create a scatter plot
        plt.scatter(clipped_gdf['ActualDef'], clipped_gdf['PredDef'], color='steelblue', edgecolors='white', linewidth=1.0, s=50)

        # Add labels and title
        plt.xlabel('Actual Deforestation (ha)', color='black', fontweight='bold', labelpad=10)
        plt.ylabel('Predicted Deforestation (ha)', color='black', fontweight='bold', labelpad=10)
        plt.title(title, color='firebrick', fontweight='bold', fontsize=20, pad=20)

        # Plot the trend line
        plt.plot(X, trend_line, color='mediumseagreen', linestyle='-', label='Best Fit Line')

        # Plot a 1-to-1 line
        plt.plot([0, max(clipped_gdf['ActualDef'])], [0, max(clipped_gdf['ActualDef'])], color='crimson', linestyle='--',
                 label='1:1 Line')

        # Add a legend in the bottom right position
        plt.legend(loc='lower right')

        # Set a proportion to extend the limits
        extension_f = 0.1

        # Check if lim is string and "default"
        if isinstance(xmax, str) and xmax.lower() == "default":
            xmax = max(X) * (1 + extension_f)
        else:
            xmax = float(xmax)

        if isinstance(ymax, str) and ymax.lower() == "default":
            ymax = max(Y) * (1 + extension_f)
        else:
            ymax = float(ymax)

        plt.xlim([0, xmax])
        plt.ylim([0, ymax])

        text_x_pos = ymax * 0.05
        text_y_start_pos = ymax * 0.9
        text_y_gap = ymax * 0.05

        # Adjust plt texts with the new calculated positions
        plt.text(text_x_pos, text_y_start_pos, equation, fontsize=11, color='black')
        plt.text(text_x_pos, text_y_start_pos - text_y_gap, f'Samples = {len(X)}', fontsize=11, color='black')
        plt.text(text_x_pos, text_y_start_pos - 2 * text_y_gap, f'R^2 = {r_squared:.4f}', fontsize=11, color='black')
        plt.text(text_x_pos, text_y_start_pos - 3 * text_y_gap, f'MedAE = {MedAE:.2f} ({MedAE_percent:.2f}%)',
                 fontsize=11, color='black')

        # x, yticks
        plt.yticks(fontsize=10, color='dimgrey')
        plt.xticks(fontsize=10, color='dimgrey')

        # Save the plot
        plt.savefig(out_fn)
        return

    def remove_temp_files(self):
        # Files to check for and delete
        mask_file = 'mask'
        shapefiles_to_delete = ["TEMP_POLYGONIZED","POLYGONIZED_MASK","thiessen_polygon_temp","temp_vector"]

        # Shapefile associated extensions
        mask_file_extensions =[".tif",".rst",".rdc",".RST",".RST.aux.xml",".ref"]
        shapefile_extensions = [".shp", ".shx", ".dbf", ".prj", ".sbn", ".sbx",".cpg", ".shp.xml"]

        # Delete mask files
        for mask_ext in mask_file_extensions:
            mask_filename = f"{mask_file}{mask_ext}"
            if os.path.exists(mask_filename):
                os.remove(mask_filename)

        # Delete shapefiles with associated extensions
        for shp_base in shapefiles_to_delete:
            for ext in shapefile_extensions:
                full_filename = f"{shp_base}{ext}"
                if os.path.exists(full_filename):
                    os.remove(full_filename)
        self.progress_updated.emit(100)
        return