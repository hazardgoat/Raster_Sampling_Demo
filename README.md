# Raster Sampling Demo
<p align="center">
  <img alt="" style=" margin-left: 50px;margin-right: 50px;" src="https://user-images.githubusercontent.com/74040471/140021517-2f4229b0-cc56-4cea-ac93-9c77c2086e74.png"/>
</p>
<p align="center">
  (Resulting graph of this demo)
</p>

# Background
Sampling values of a raster at specific geographic coordinates can be done with a number of Python libraries, but I believe the task is most easily accomplished with the geospatial library PyGMT. One common reason to do this is for correlating raster values with sample data.

# The Demonstration
In this tutorial, raster models of soil depth and soil water holding capacity for the United States will be sampled at random geographic coordinates within the state of Colorado. A linear regression of the data will then be plotted to show what relationship*, if any, exists between the datasets. This comprehensive tutorial covers every step from data acquisition to plotting a graph.

Please keep in mind that with the exception of the folder creation script, all code blocks shown in this demo are intended to be run as part of a complete script, which is included at the bottom of the page.

*This tutorial makes no attempt to interpret the regression plot, nor does it assert the accuracy of the results. It is created purely to demonstrate what might be done with values sampled from rasters at specific geographic coordinates.

# Getting Started
### Create Project Folders
To follow this demo as written, project folders need to be created on the Desktop. A diagram of the desired directory tree for Windows 10 is shown below:

<p align="center">
  <img alt="" style=" margin-left: 50px;margin-right: 50px;" src="https://user-images.githubusercontent.com/74040471/140021585-27dbfa23-3d2a-4970-a7df-266239e03637.png"/>
</p>
<p align="center">
  (Image created with Lucidchart)
</p>

These folders can be created either by running the script provided below from anywhere after changing the `main_dir` file path to reflect your username, or by manually creating a *Grid_Track_Demo* folder and within it *Data*, *Methods*, and *Results* folders.

```
'''
Decription:
This script creates project folers if they don't already exist
'''

import os

# main directory path
main_dir = r'C:\Users\USER\Desktop\Grid_Track_Demo'

# path to the directory holding the project data files
data_folder = os.path.join(main_dir, 'Data')

# path to the directory holding the project Python scripts
methods_folder = os.path.join(main_dir, 'Methods')

# path to the directory holding the map generated by the scripts
results_folder = os.path.join(main_dir, 'Results')

directories = [main_dir, data_folder, methods_folder, results_folder]

# Iterates through the list of directories and creates them if they don't already exist
for directory in directories:
    os.makedirs(directory, exist_ok = True)
```

Data files used and created by the demo script will be located in the *Data* folder, and the linear regression graph will save to the *Results* folder. The *Methods* folder should contain the demo scripts.

# Create Project Files
### Download Rasters
After creating the project folders, we need to download the rasters that will be used in this demo. This tutorial uses raster models of soil depth and available water holding capacity acquired from the [UC Davis SoilWeb website](https://casoilresource.lawr.ucdavis.edu/soil-properties/download.php).

While these files aren’t very large, it is good practice to download them in chunks so that larger files can be downloaded if needed in the future; this is done in the demo script function below:

```
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
```

### Generate Random Coordinates
In the absence of real observations at specific coordinates, random coordinates are generated to sample the two rasters. The state of Colorado is chosen as the region in which the random coordinates are generated because it is a square and as such, is easy to define.

This demo script function generates random coordinates within the state of Colorado and saves them to a CSV file:

```
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
```

### Reproject Rasters
Before the rasters can be sampled with our random coordinates, they need to be converted from their native [coordinate reference system](https://docs.qgis.org/3.16/en/docs/gentle_gis_introduction/coordinate_reference_systems.html) to [WGS84 so that GPS coordinates can be used to sample the data](https://gisgeography.com/geodetic-datums-nad27-nad83-wgs84/). Permanently transforming a raster isn’t ideal because doing so can introduce inaccuracies, but in this particular case that concern isn’t overly important as this a demo of how it could be done if needed.

This demo script function reprojects the rasters to the WGS84 coordinate system and saves them as new GeoTIFF files:

```
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

            model_output = os.path.join(main_dir, 'Data', '{}_epsg4326_reprojected.tif').format(model)

            # saves the reprojected raster as a raster
            projected.rio.to_raster(model_output)
```

# Sample Raster Values
Now that the rasters are in the correct projection, they can be sampled with the previously generated coordinates.

This demo script function loops over each raster and samples it at the randomly generated coordinates. [A bilinear interpolation is used when doing so because the data is not categorical](https://support.esri.com/en/technical-article/000005606). Once both rasters have been sampled, the data is saved to a CSV file:

```
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
```

# Create Linear Regression Graph
Now that we have our data, it’s time to visualize it. Linear regressions are a common way to explore potential relationships between datasets, so that’s what will be plotted next.

This demo script function uses the Python library [Seaborn](https://seaborn.pydata.org/) to create a scatter-plot of available water holding capacity as a function of soil depth. A linear regression of the data is then plotted on top of it and histograms with density curves are displayed in the margins.

```
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
```

# Result
<p align="center">
  <img alt="" style=" margin-left: 50px;margin-right: 50px;" src="https://user-images.githubusercontent.com/74040471/140021517-2f4229b0-cc56-4cea-ac93-9c77c2086e74.png"/>
</p>
<p align="center">
  (Resulting graph of this demo. This tutorial makes no attempt to interpret the regression plot, nor does it assert accuracy of the result)
</p>

I hope this tutorial has been helpful for anyone looking to sample values from rasters using specific coordinates.

# Complete Code
```
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

            model_output = os.path.join(main_dir, 'Data', '{}_epsg4326_reprojected.tif').format(model)

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
```
