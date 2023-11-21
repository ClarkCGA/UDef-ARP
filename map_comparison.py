import os
from osgeo import gdal, osr
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import Voronoi
import geopandas as gpd
import shapely
from osgeo import ogr
from rasterstats import zonal_stats
import seaborn as sns
from shapely.geometry import Point
import pandas as pd
from PyQt5.QtCore import QObject, pyqtSignal

class MapComparison(QObject):
    progress_updated = pyqtSignal(int)
    def __init__(self):
        super(MapComparison, self).__init__()
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
        projection = in_ds.GetProjection()
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

    def create_thiessen_polygon (self, grid_area, mask, density, deforestation, csv_name):
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

        # Only preserved Thiessen Polygon within mask by intersection
        thiessen_gdf = gpd.overlay(df1=voronois, df2=polydf, how="intersection", keep_geom_type=False)
        self.progress_updated.emit(40)

        # Extract polygons and multipolygons from the entire thiessen_gdf (including GeometryCollections)
        extracted_gdf = thiessen_gdf['geometry'].apply(
            lambda geom: [g for g in geom.geoms if
                          g.geom_type in ['Polygon', 'MultiPolygon']] if geom.geom_type == 'GeometryCollection' else [
                geom]
        ).explode().reset_index(drop=True)

        extracted_gdf = gpd.GeoDataFrame({'geometry': extracted_gdf}, crs=thiessen_gdf.crs)

        # Calculate area in hectares
        extracted_gdf['Area_ha'] = extracted_gdf['geometry'].area / 10000

        # Find the maximum value of the 'area_ha' column
        max_area = extracted_gdf['Area_ha'].max()

        # Filter to keep only rows where 'area_ha' is equal to the maximum value
        clipped_gdf = extracted_gdf[extracted_gdf['Area_ha'] == max_area]
        self.progress_updated.emit(50)

        ## Calculate zonal statistics
        # Actual Deforestiona(ha)
        stats = zonal_stats(clipped_gdf.geometry, deforestation, stats="sum", nodata=0)
        self.progress_updated.emit(60)

        # Calculate areal_resolution_of_map_pixels
        in_ds4 = gdal.Open(density)
        P = in_ds4.GetGeoTransform()[1]
        areal_resolution_of_map_pixels = P * P / 10000

        # Add the results back to the GeoDataFrame
        clipped_gdf['Actual Deforestion(ha)'] = [(item['sum'] if item['sum'] is not None else 0) * areal_resolution_of_map_pixels for item in stats]
        self.progress_updated.emit(70)

        # Predicted Deforestiona(ha)
        stats1 = zonal_stats(clipped_gdf.geometry, density, stats="sum", nodata=0)
        self.progress_updated.emit(80)

        clipped_gdf['Predicted Deforestion(ha)'] = [(item['sum'] if item['sum'] is not None else 0) for item in stats1]
        self.progress_updated.emit(90)

        # ID
        clipped_gdf['ID'] = range(1, len(clipped_gdf) + 1)

        # Export to csv
        csv_file_path = csv_name
        csv=clipped_gdf.drop('geometry', axis=1).to_csv(csv_file_path, columns=['ID', 'Actual Deforestion(ha)', 'Predicted Deforestion(ha)'],
                                                    index=False)

        # Rename columns title for shapefile
        clipped_gdf = clipped_gdf.rename(columns={'Predicted Deforestion(ha)': 'PredDef',
                                                  'Actual Deforestion(ha)': 'ActualDef'})

        # Save the updated GeoDataFrame back to a shapefile
        clipped_gdf.to_file('thiessen_polygon.shp')

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
        slope, intercept = np.polyfit(X, Y, 1)
        equation = f'Y = {slope:.2f} * X + {intercept:.2f}'
        # Calculate the trend line
        trend_line = slope * X + intercept

        # ## Calculate R square
        # # Get the correlation coefficient
        # r = np.corrcoef(X, Y)[0, 1]
        # # Square the correlation coefficient
        # r_squared = r ** 2

        ##Calculate MedAE
        total_distance = []
        for i in Y:
            for j in X:
                total_distance.append(abs(i - j))
        MedAE = sum(total_distance) / len(total_distance)

        # Set the figure size
        plt.figure(figsize=(8, 6))

        # Create a scatter plot
        plt.scatter(clipped_gdf['ActualDef'], clipped_gdf['PredDef'], color='steelblue', label='Data Points')

        # Add labels and title
        plt.xlabel('Actual Deforestion(ha)', color='dimgrey')
        plt.ylabel('Predicted Deforestion(ha)', color='dimgrey')
        plt.title(title, color='firebrick', fontsize=20, pad=20)

        # Plot the trend line
        plt.plot(X, trend_line, color='mediumseagreen', linestyle='--', label='Trend Line')

        # Plot a 1-to-1 line
        plt.plot([0, max(clipped_gdf['ActualDef'])], [0, max(clipped_gdf['ActualDef'])], color='crimson', linestyle='--',
                 label='1-to-1 Line')

        # Set max value of xlim abd ylim
        max_value = max(max(X), max(Y))
        plt.xlim([0, max_value])
        plt.ylim([0, max_value])

        # Get the max value for setting text positions
        # Set text x position to 5% of the maximum value
        text_x_pos = max_value * 0.05
        # Set starting y position to 95% of the max value
        text_y_start_pos = max_value * 0.9
        # Set gap between texts to 3% of the maximum value
        text_y_gap = max_value * 0.05

        plt.text(text_x_pos, text_y_start_pos, f'Samples = {len(X):.2f}', fontsize=11, color='black')
        plt.text(text_x_pos, text_y_start_pos - text_y_gap, f'MedAE = {MedAE:.2f}', fontsize=11, color='black')

        # x, yticks
        plt.yticks(fontsize=10, color='dimgrey')
        plt.xticks(fontsize=10, color='dimgrey')

        # Save the plot
        plt.savefig(out_fn)
        return

    def remove_temp_files(self):
        # Files to check for and delete
        mask_file = 'mask'
        shapefiles_to_delete = ["TEMP_POLYGONIZED","POLYGONIZED_MASK","thiessen_polygon_temp"]

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