# fullmoon
interact with teapot server and records data

## Getting started
1. install docker and docker-compose
2. clone this repository
3. run the init.sh to create the docker_mount dir
4. update the config.py as necessary
4. run docker-compose.yaml

## services
* calculate_lux - periodically calcualte lux values using the camera feed adn store them in db
* record - periodically collect and stores(in db) dc values and lux values from rpi devices running teapot server
* control - change the led brightness as required
    1. infinite loop (handle_newly_occupied thread)
        1. get the OCCUPANCY_VECTOR (Boolean) for all sections
        2. if occupancy made the transform false -> true: set that section’s corresponding light to COMFORT_VALUE (because we don’t want to keep people in dark while we incrementally increase the light)
        3. sleep 1 sec
    2. infinite loop (calculate_optimized_dc_thread)
        1. get the OCCUPANCY_VECTOR (Boolean) for all sections
        2. [NEW]define the OPTIMUM_LUX vector based on occupancy [eg : occupancy vector = (True, False, False, True) -> OPTIMUM_LUX = (COMFORT_VALUE, MINIMUM_VALUE, MINIMUM_VALUE, COMFORT_VALUE)]
        3. [NEW]get the CURRENT_LUX vector (using pixel values)
        4. [NEW]calculate the DEFICIT_LUX vector (DEFICIT_LUX = OPTIMUM_LUX - CURRENT_LUX)
        5. calculate the optimum lux dc levels vector(TARGET_DC) for each section using the DEFICIT_LUX and WEIGHT_MATRIX
        6. post update the TARGET_DC to db
        7. sleep for CALCULATE_SLEEP_TIME(configurable constant)
    3. infinite loop (set_optimized_dc_in_device thread)
        1. read the TARGET_DC from db
        2. for each section 
            1. calculate the current lux using the method in step 3 get the current dc
            2. if TARGET_DC > current dc: increase by DELTA_DC(configurable constant)
            3. else : decrease by DELTA_DC(configurable constant)
        3. sleep for ADJUST_SLEEP_TIME(configurable constant)

