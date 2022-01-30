'''
PyGMT v0.4.1

This script domonstrates how to extract values from rasters using specific coordinates and then apply the values to explore the relationship between soil depth and avalible water holding capacity.

The script automatically downloads rasters of soil depth and avalible water holding capacity for the contiguous continential United States from the University of California, Davis SoilWeb website.
It then reprojects the rasters to the WGS84 geographic coordinate system so that gps coordinates can be used to pull data from it. Next, random coordinates are generated within the extent of the state of Colorado,
and they are used to extract values from the two rasters. Finally, the values are regressed against each other and plotted on a graph.
'''

# main directory for the demo files
main_dir = r'C:\Users\USER\Desktop\Grid_Track_Demo'

# controls whether the project rasters are automatically downloaded
download_rasters = True
# controls whether the rasters are reprojected
reproject_rasters = True
# controls whether a CSV of random coordinates within the state of Colorado is created
get_random_coordinates = True


# class that holds all the functions related to extracting values from rasters with specific coordinates
class Grid_Track():

    # automatically downloads soil depth and avalible water holding capacity rasters from the UC Davis SoilWeb website
    def Download_Raster_Files(self):
        import requests
        import os

        # urls of the rasters to be downloaded
        file_urls = {
            'soil_depth':'https://soilmap2-1.lawr.ucdavis.edu/800m_grids/rasters/soil_depth.tif', 
            'water_capacity':'https://soilmap2-1.lawr.ucdavis.edu/800m_grids/rasters/water_storage.tif'
        }

        # iterates through each url and downloads them in chunks to avoid reading large files into strings (https://www.geeksforgeeks.org/downloading-files-web-using-python/)
        for name, url in file_urls.items():

            # creates a response object, but because stream is set to True it only downloads the response headers, while keeping the connection open
            r = requests.get(url, stream = True)

            file_save_name = os.path.join(main_dir, 'Data', '{}.tif'.format(name))

            # downloads a portion of the file data that is 1024 bytes large, writes it to the file, and repeats this until the whole file is downloaded
            with open(file_save_name, 'wb') as tif:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        tif.write(chunk)


    # generates a set number of random coordinates within the state of Colorado, then saves them to a CSV file
    def Get_Random_Land_Coordinates(self):
        import random
        import pandas as pd
        import os

        # creates the dataframe that will hold the coordinates
        df_random_coordinates = pd.DataFrame(columns = ['longitude', 'latitude'])
        # number of random coordinates to generate 
        n_random_coordinates = 500

        for i in range(n_random_coordinates):
            # random longitude
            lon = random.uniform(-109.03711, -102.05859)
            lon = round(lon, 5)
            # random latitude
            lat = random.uniform(37.01855, 41.00789)
            lat = round(lat, 5)
            
            # adds the coordinates to the dataframe
            df_random_coordinates = df_random_coordinates.append({'longitude':lon, 'latitude':lat}, ignore_index=True)

        random_us_land_coordinates = os.path.join(main_dir, 'Data', 'random_us_land_coordinates.csv')
        df_random_coordinates.to_csv(random_us_land_coordinates, sep='\t', index=False)


    # reprojects the rasters so they are in the WGS84 geographic coordinate system, which will allow GPS coordinates to be used to extract values from them (https://gis.stackexchange.com/questions/346745/how-to-reproject-raster-image-from-wgs84-pseudo-mercator-to-ecef-to-enu-in-pytho)
    def Reproject_Rasters(self):
        import rioxarray
        import os

        models = ['soil_depth','water_capacity']

        for model in models:

            model_input = os.path.join(main_dir, 'Data', '{}.tif').format(model)
            
            # opens the raster
            rds = rioxarray.open_rasterio(model_input)

            # sets the coordinate system that the raster will be reprojected to
            crs = 'EPSG:4326'

            # reprojects the raster to the desired coordinate system
            projected = rds.rio.reproject(crs)

            model_output = os.path.join(main_dir, 'Data', '{}_epsg{}_reprojected.tif').format(model, crs)

            # saves the reprojected raster as a raster
            projected.rio.to_raster(model_output)
        

    # extracts values from the rasters at the previously generated random coordinates, then combines the data into a single dataframe and saves it as a CSV file
    def Extract_Values(self):
        import pygmt
        import pandas as pd
        import os

        soil_depth_data = os.path.join(main_dir, 'Data', 'soil_depth_epsg4326_reprojected.tif')
        water_capacity_data = os.path.join(main_dir, 'Data', 'water_capacity_epsg4326_reprojected.tif')
        rasters = {'soil_depth':soil_depth_data, 'water_capacity':water_capacity_data}
        
        coordinates = os.path.join(main_dir, 'Data', 'random_us_land_coordinates.csv')
        df_coordinates = pd.read_csv(coordinates, sep='\t')

        # dataframe that will hold the values extracted from both rasters
        df_unified_raster_data = pd.DataFrame()
        df_unified_raster_data['longitude'] = df_coordinates.longitude
        df_unified_raster_data['latitude'] = df_coordinates.latitude

        # iterates through each raster and extracts data from them using the random coordinates, then adds the data to the df_unified_raster_data dataframe
        for name, raster in rasters.items():

            # creates a dataframe of the random coordinates and the values of the raster at those coordinates
            df_track = pygmt.grdtrack(
                # reads a dataframe of only longitudes and latitudes to get coordinates
                points = df_coordinates,
                # reads the raster
                grid = raster,
                # uses bilinear because soil depth and avalible water holding capacity are not catagorical
                interpolation = 'l',
                # name of the column in the new "df_track" dataframe that will hold the extracted raster values
                newcolname = name
            )
            
            # adds the extracted raster values to the unified dataframe
            df_unified_raster_data[name] = df_track[name]

        unified_raster_data_output = os.path.join(main_dir, 'Data', 'unified_raster_data.csv')
        df_unified_raster_data.to_csv(unified_raster_data_output, sep='\t', index=False)


# class that holds all the functions pretaining to graphing the data
class Create_Graphs():
    
    # creates a scatter plot of avalible water holding capacity as a function soil depth, and plots a linear regression line through the points. Histograms are plotted in the margins of the graph
    def Create_Graph(self):
        import matplotlib.pyplot as plt
        import seaborn as sns
        import pandas as pd
        import os

        unified_raster_data = os.path.join(main_dir, 'Data', 'unified_raster_data.csv')

        df_unified_raster = pd.read_csv(unified_raster_data, sep='\t')
        df_unified_raster = df_unified_raster.dropna()

        # sets the data for independant variable
        x = df_unified_raster.soil_depth
        # sets the data for teh dependant variable
        y = df_unified_raster.water_capacity

        # sets the color plaette for the graph background
        sns.set_style("darkgrid")

        # creates a scatter plot with a linear regression line. Histograms are plotted in the margins and have a density curve plotted over the bins
        g_reg = sns.jointplot(
            data = df_unified_raster, 
            x = x,
            y = y,
            # plots a linear regression line 
            kind = "reg",
            # sets the regression line and confidence interval color to something other than the default blue
            line_kws = {'color':'red'}, 
            # sets the scatterplot point opacity and size <opacity><size>   
            joint_kws = {'scatter_kws':dict(alpha=0.5, s=15)},   
        )

        # creates rug plots at the bottom of each marginal histogram to more show a more granual data distribution 
        g_reg.plot_marginals(
            # creates a rug plot
            sns.rugplot, 
            color='royalblue',
            # sets the height of the rug plot lines 
            height=.05,
        )

        # replaces the automatically applied axis labels with custom ones using bold font
        g_reg.ax_joint.set_xlabel('$\\bf{Soil\ Depth\ (cm)}$')
        g_reg.ax_joint.set_ylabel('$\\bf{Avail.\ Water\ Holding\ Capacity\ (cm)}$')

        graph_output = os.path.join(main_dir, 'Results', 'soil-depth_vs_water_capacity_linear_regression_demo.png')
        # dpi is the resolution of the saved image
        plt.savefig(graph_output, dpi=150)



grid_track = Grid_Track()
grid_track.Download_Raster_Files()

toggles = {grid_track.Download_Raster_Files:download_rasters, grid_track.Get_Random_Land_Coordinates:get_random_coordinates, grid_track.Reproject_Rasters:reproject_rasters}
for function, toggle in toggles.items():
    if toggle == True:
        function()

grid_track.Extract_Values()


graph = Create_Graphs()
graph.Create_Graph()
