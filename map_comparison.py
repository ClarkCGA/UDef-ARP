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

    def create_mask_polygon (self, mask):
        '''
        Create municipality mask polygon
        :param mask: mask of the jurisdiction (binary map)
        :return:Polygonized_Mask: municipality mask polygon
        '''
        in_ds1 = gdal.Open(mask)
        in_band1 = in_ds1.GetRasterBand(1)

        # Set up osr spatial reference
        projection = in_ds1.GetProjection()
        spatial_ref = osr.SpatialReference()
        spatial_ref.ImportFromWkt(projection)

        #Create shapefile
        dst_layername = "POLYGONIZED_MASK"
        driver = ogr.GetDriverByName("ESRI Shapefile")
        dst_ds = driver.CreateDataSource(dst_layername + ".shp")
        dst_layer = dst_ds.CreateLayer(dst_layername, srs=spatial_ref)
        self.progress_updated.emit(10)
        Polygonized_Mask=gdal.Polygonize(in_band1, in_band1, dst_layer, -1, [], callback=None)
        dst_ds.Destroy()
        return Polygonized_Mask

    def create_thiessen_polygon (self, grid_area, mask):
        '''
          Create thiessen polygon
         :param grid_area: The 30-class vulnerability map for the HRP
         :param mask: mask of the jurisdiction (binary map)
         :return
        '''
        ## Create inside polygon sample points:
        # Open the Polygonized_Mask shapefile
        mask_df = gpd.GeoDataFrame.from_file('POLYGONIZED_MASK.shp')

        # Calculate grid size
        in_ds = gdal.Open(mask)
        grid_size = int(np.sqrt(grid_area * 10000)) // int(in_ds.GetGeoTransform()[1])

        # Systematic Sampling
        sample_points = []
        for y in range(-2 * grid_size, in_ds.RasterYSize + 2 * grid_size, grid_size):
            for x in range(-2 * grid_size, in_ds.RasterXSize + 2 * grid_size, grid_size):
                # Convert raster coordinates to geographic coordinates
                geo_x = in_ds.GetGeoTransform()[0] + x * in_ds.GetGeoTransform()[1]
                geo_y = in_ds.GetGeoTransform()[3] + y * in_ds.GetGeoTransform()[5]
                sample_points.append((geo_x, geo_y))
        self.progress_updated.emit(20)
        # Convert sample_points list to DataFrame
        df = pd.DataFrame(sample_points, columns=['geo_x', 'geo_y'])
        df['coords'] = list(zip(df['geo_x'], df['geo_y']))
        df['coords_Point'] = df['coords'].apply(Point)
        points_df = gpd.GeoDataFrame(df, geometry='coords_Point', crs=mask_df.crs)

        # Intersection the samples in mask
        pointInPolys = gpd.overlay(points_df, mask_df, how='intersection')

        # Convert the 'coords' column to a numpy array
        coords = np.array(pointInPolys['coords'].tolist())

        ## Create boundary sample points:
        # Choose the largest polygon (study area) in mask_df
        polygon = mask_df.geometry[len(mask_df) - 1]
        self.progress_updated.emit(30)
        # Create a large rectangle surrounding it
        bound = polygon.buffer(2000).envelope.boundary
        self.progress_updated.emit(60)
        # Create boundary sample points(one every 100 m) along the rectangle boundary
        boundarypoints = [bound.interpolate(distance=d) for d in range(0, np.ceil(bound.length).astype(int), 100)]
        boundarycoords = np.array([[p.x, p.y] for p in boundarypoints])
        self.progress_updated.emit(70)
        ## Combine two array of all points
        all_coords = np.concatenate((boundarycoords, coords))

        ##Create Thiessen Polygon
        vor = Voronoi(points=all_coords)

        # Polygonize the line ridge is not infinity
        lines = [shapely.geometry.LineString(vor.vertices[line]) for line in
                 vor.ridge_vertices if -1 not in line]
        polys = shapely.ops.polygonize(lines)

        # Convert Voronoi polygons (polys) into a GeoDataFrame.
        voronois = gpd.GeoDataFrame(geometry=gpd.GeoSeries(polys), crs=mask_df.crs)

        # Convert the study area to GeoDataFrame.
        polydf = gpd.GeoDataFrame(geometry=[polygon], crs=mask_df.crs)

        # Only preserved Thiessen Polygon within mask by intersection
        thiessen_gdf = gpd.overlay(df1=voronois, df2=polydf, how="intersection", keep_geom_type=False)
        # Extract polygons and multipolygons from the entire thiessen_gdf (including GeometryCollections)
        extracted_gdf = thiessen_gdf['geometry'].apply(
            lambda geom: [g for g in geom.geoms if
                          g.geom_type in ['Polygon', 'MultiPolygon']] if geom.geom_type == 'GeometryCollection' else [
                geom]
        ).explode().reset_index(drop=True)

        extracted_gdf = gpd.GeoDataFrame({'geometry': extracted_gdf}, crs=thiessen_gdf.crs)

        ## Save to shapefile
        thiessen_polygon_name = 'thiessen_polygon.shp'
        extracted_gdf.to_file(thiessen_polygon_name)
        self.progress_updated.emit(80)
        return

    def calculate_zonal_stats(self, density, deforestation):
        '''
          Calculate zonal stats
         :param density: adjusted prediction density map
         :param deforestation:Deforestation Map during the HRP
         :return:out_ds:result image
        '''
        ##Actual Deforestiona(ha)
        # Compute the zonal statistics
        stats = zonal_stats('thiessen_polygon.shp', deforestation, stats="sum", nodata=-999)

        # Create 'Actual' column
        clipped_gdf = gpd.read_file('thiessen_polygon.shp')
        clipped_gdf['Actual Deforestiona(ha)'] = [item['sum'] * 0.09 for item in stats]

        ## Predicted Deforestiona(ha)
        # Compute the zonal statistics
        stats1 = zonal_stats('thiessen_polygon.shp', density, stats="sum", nodata=-999)
        clipped_gdf['Predicted Deforestiona(ha)'] = [item['sum'] for item in stats1]

        ## ID
        clipped_gdf['ID'] = range(1, len(clipped_gdf) + 1)

        ##Export to csv
        csv=clipped_gdf.drop('geometry', axis=1).to_csv('Performance_Chart.csv', columns=['ID', 'Actual Deforestiona(ha)', 'Predicted Deforestiona(ha)'],
                                                    index=False)
        self.progress_updated.emit(90)
        return clipped_gdf, csv

    def create_plot(self, clipped_gdf,title):
        '''
        Create plot and save to local directory
        :param clipped_gdf: thiessen_polygon geo-dataframe
        :param title:plot title
        :return
        '''
        # Set Seaborn Style
        sns.set()

        # prepare the X/Y data
        X = np.array(clipped_gdf['Actual Deforestiona(ha)'], dtype=np.float64)
        Y = np.array(clipped_gdf['Predicted Deforestiona(ha)'], dtype=np.float64)

        # ## Perform linear regression
        # slope, intercept = np.polyfit(X, Y, 1)
        # equation = f'Y = {slope:.2f} * X + {intercept:.2f}'
        # # Calculate the trend line
        # trend_line = slope * X + intercept

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
        plt.scatter(clipped_gdf['Actual Deforestiona(ha)'], clipped_gdf['Predicted Deforestiona(ha)'], color='steelblue', label='Data Points')

        # Add labels and title
        plt.xlabel('Actual Deforestiona(ha)', color='dimgrey')
        plt.ylabel('Predicted Deforestiona(ha)', color='dimgrey')
        plt.title(title, color='firebrick', fontsize=20, pad=20)

        # # Plot the trend line
        # plt.plot(X, trend_line, color='mediumseagreen', linestyle='--', label='Trend Line')

        # Plot a 1-to-1 line
        plt.plot([0, max(clipped_gdf['Actual Deforestiona(ha)'])], [0, max(clipped_gdf['Actual Deforestiona(ha)'])], color='crimson', linestyle='--',
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

        # Adjust plt texts with the new calculated positions
        # plt.text(text_x_pos, text_y_start_pos, equation, fontsize=11, color='black')
        # plt.text(text_x_pos, text_y_start_pos - text_y_gap, f'Samples = {len(X):.2f}', fontsize=11, color='black')
        # # plt.text(text_x_pos, text_y_start_pos - 2 * text_y_gap, f'R^2 = {r_squared:.2f}', fontsize=11, color='black')
        # plt.text(text_x_pos, text_y_start_pos - 3 * text_y_gap, f'MedAE = {MedAE:.2f}', fontsize=11, color='black')

        plt.text(text_x_pos, text_y_start_pos, f'Samples = {len(X):.2f}', fontsize=11, color='black')
        plt.text(text_x_pos, text_y_start_pos - text_y_gap, f'MedAE = {MedAE:.2f}', fontsize=11, color='black')

        # x, yticks
        plt.yticks(fontsize=10, color='dimgrey')
        plt.xticks(fontsize=10, color='dimgrey')

        # Display the plot
        plt.savefig('Plot.png')
        return

    def remove_temp_files(self):
        # Files to check for and delete
        mask_file = 'mask'
        shapefiles_to_delete = ["POLYGONIZED_MASK"]

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
