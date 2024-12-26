# Animation of Pittsburgh Regional Transit routes

Run the python script `animation.py` to view animation of Pittsburgh Regional Transit (PRT) routes. Currently shows morning rush hour (7 - 10 AM) routes in downtown Pittsburgh. With data preprocessing, may take a while to load up the animation so it uses a cache to speed this up. Mouse click to start the animation when the window has opened.

## Making own animation

You can create your own animations by modifying the `animation.py` script.    

### Using own map
Upload the map image you would like to use into the `maps` folder. Then, update the variable `MAP_FILENAME` on line 24 to the name of your map image. You will also need to update the coordinates of the map image, and you can update the values of lines 9-12 to the coordinates of your map image. You can also update the `WIDTH` and `HEIGHT` variables on lines 17 and 18 to change size of the animation.

### Changing time of day
To change the start and end time of the animation, update the `START_TIME` and `END_TIME` variables on lines 26 and 27 to the time you would like to view. The time should be in the format `HH:MM:SS`. This may be a bit buggy with extreme values of time though. If you would like to change the day of the week of the routes, you will need to update the `TRIPS_FILTER` list on line 22. To find the values to include, look at the `calendar.txt` file in the GTFS files and find the `service_id` values for the days you would like to include.

### Changing FPS
Change the FPS variable on line 20 to change speed of animation.

## Cached Files

The script stores the processed data into pickled files in the `cache` folder. This is to speed up the loading time of the animation. If you would like to update the data, you can delete the files in the `cache` folder or pass the `--force` flag when running the script.

## Updating route data

PRT periodically updates its routes and timings. When data is outdated, download the "GTFS files (Clever version)" folder from [PRT Developer Resources](https://www.rideprt.org/business-center/developer-resources/). You will then need to replace `calendar.txt`, `routes.txt`, `shapes.txt`, `stop_times.txt`, and `stops.txt` in the `data` folder with the new files. You will then need to clear the cached files, either by deleting the files in the `cache` folder or passing the `--force` flag when running the `animation.py` script. 

## Possible Improvements

- Make the intializing trips section more efficient by using a smarter method to calculate where trips start at
- Use smarter method in storing the trips in TRIPS_DATA, including deleting trips that have ended
