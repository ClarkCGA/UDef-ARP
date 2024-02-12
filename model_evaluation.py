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

    def create_mask_polygon(self, mask):
        '''
        Create municipality mask polygon
        :param mask: mask of the jurisdiction (binary map)
        :return:Polygonized_Mask: municipality mask polygon
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

    def create_thiessen_polygon (self, grid_area, mask, density, deforestation, csv_name, tp_name):
        '''
          Create thiessen polygon
         :param grid_area: assessment grid cell area or 100,000 (ha)
         :param mask: mask of the jurisdiction (binary map)
         :param density: adjusted prediction density map
         :param deforestation:Deforestation Map during the HRP
         :param csv_name:Name of performance chart
         :return  clipped_gdf: thiessen polygon dataframe
                  csv: performance chart
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

        # Only preserved Thiessen Polygon within mask by spatial join with mask polygon
        thiessen_gdf = gpd.sjoin(voronois, polydf, how="inner", predicate="within")
        #explicitly set the crs
        thiessen_gdf.crs = mask_df.crs

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

        # remove all columns except area_ha and geometry
        clipped_gdf = clipped_gdf[['Area_ha', 'geometry']]

        ## Calculate zonal statistics

        ## Convert clipped_gdf to shapefile
        vector_temp_path = "temp_vector.shp"
        clipped_gdf.to_file(vector_temp_path)

        # Actual Deforestation(ha)
        stats = self.zonal_stats(vector_temp_path, deforestation, nodata_value=0)

        self.progress_updated.emit(60)

        # Calculate areal_resolution_of_map_pixels
        in_ds4 = gdal.Open(density)
        P1 = in_ds4.GetGeoTransform()[1]
        P2 = abs(in_ds4.GetGeoTransform()[5])
        areal_resolution_of_map_pixels = P1 * P2 / 10000

        # Add the results back to the GeoDataFrame
        clipped_gdf['Actual Deforestation(ha)'] = [(item['sum'] if item['sum'] is not None else 0) * areal_resolution_of_map_pixels for item in stats]
        self.progress_updated.emit(70)

        # Predicted Deforestation(ha)
        stats1 = self.zonal_stats(vector_temp_path, density, nodata_value=0)
        self.progress_updated.emit(80)

        clipped_gdf['Predicted Deforestation(ha)'] = [(item['sum'] if item['sum'] is not None else 0) for item in stats1]
        self.progress_updated.emit(90)

        # ID
        clipped_gdf['ID'] = range(1, len(clipped_gdf) + 1)

        # Replace NaN or blank values with '0'
        columns_to_fill = ['Actual Deforestation(ha)', 'Predicted Deforestation(ha)']
        for column in columns_to_fill:
            clipped_gdf[column] = clipped_gdf[column].fillna(0)

        # Export to csv
        csv_file_path = csv_name
        csv=clipped_gdf.drop('geometry', axis=1).to_csv(csv_file_path, columns=['ID', 'Actual Deforestation(ha)', 'Predicted Deforestation(ha)'],
                                                    index=False)

        # Rename columns title for shapefile
        clipped_gdf = clipped_gdf.rename(columns={'Predicted Deforestation(ha)': 'PredDef',
                                                  'Actual Deforestation(ha)': 'ActualDef'})

        # Save the updated GeoDataFrame back to a shapefile
        tp_file_path = tp_name
        clipped_gdf.to_file(tp_file_path)

        return clipped_gdf, csv

    def create_plot(self, clipped_gdf, title, out_fn):
        '''
        Create plot and save to local directory
        :param clipped_gdf: thiessen_polygon geo-dataframe
        :param title:plot title
        :return
        '''
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

        # Set the figure size
        plt.figure(figsize=(8, 6))

        # Create a scatter plot
        plt.scatter(clipped_gdf['ActualDef'], clipped_gdf['PredDef'], color='steelblue', label='Data Points')

        # Add labels and title
        plt.xlabel('Actual Deforestation(ha)', color='dimgrey')
        plt.ylabel('Predicted Deforestation(ha)', color='dimgrey')
        plt.title(title, color='firebrick', fontsize=20, pad=20)

        # Plot the trend line
        plt.plot(X, trend_line, color='mediumseagreen', linestyle='--', label='Trend Line')

        # Plot a 1-to-1 line
        plt.plot([0, max(clipped_gdf['ActualDef'])], [0, max(clipped_gdf['ActualDef'])], color='crimson', linestyle='--',
                 label='1-to-1 Line')

        # Set a proportion to extend the limits
        extension_f = 0.1

        # Set max value of xlim and ylim
        plt.xlim([0, max(X)*(1+extension_f)])
        plt.ylim([0, max(Y)*(1+extension_f)])

        # Set text x position to 5% of the maximum value
        text_x_pos = max(Y) * 0.05

        # Set starting y position to 95% of the max value
        text_y_start_pos = max(Y) * 0.9

        # Set gap between texts to 3% of the maximum value
        text_y_gap = max(Y) * 0.05


        # Adjust plt texts with the new calculated positions
        plt.text(text_x_pos, text_y_start_pos, equation, fontsize=11, color='black')
        plt.text(text_x_pos, text_y_start_pos - text_y_gap, f'Samples = {len(X)}', fontsize=11, color='black')
        plt.text(text_x_pos, text_y_start_pos - 2 * text_y_gap, f'R^2 = {r_squared:.4f}', fontsize=11, color='black')
        plt.text(text_x_pos, text_y_start_pos - 3 * text_y_gap, f'MedAE = {MedAE:.2f}', fontsize=11, color='black')

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