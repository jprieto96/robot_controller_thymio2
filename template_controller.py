# 2021 version of webots

# Jose Ramon Prieto del Prado

from controller import Robot

# Hardware constants
DIST_SENS_COUNT = 7
GRND_SENS_COUNT = 2

# Control constants
MOTOR_SPEED = 4

# Dark color for ground sensors that represent the comfort zone of the robot
DARK_COLOR_PROTECTION = 150

# Variables related with motivations
MAX_ENERGY_LEVEL = 250 # Related with FATIGUE motivation
MIN_STRESS_LEVEL = 0  # Related with PROTECTION motivation

MIN_ENERGY_LEVEL = 0 # Related with FATIGUE motivation
MAX_STRESS_LEVEL = 1500  # Related with PROTECTION motivation

# create the Robot instance.
robot = Robot()

# get the time step of the current world.
timestep = int(robot.getBasicTimeStep())

# initialisation functions
def init_actuators():
    """ Initialise motors, LEDs, pen """
    global motor_l, motor_r, m_spd_l, m_spd_r, led_top, led_top_colour

    # Set up motors
    motor_l = robot.getDevice('motor.left')
    motor_r = robot.getDevice('motor.right')

    # Configure motors for velocity control
    motor_l.setPosition(float('inf'))
    motor_r.setPosition(float('inf'))
    
    # set up LEDs
    led_top = robot.getDevice('leds.top')
    # maybe more LEDs...

    # initialise variables for actuator values
    reset_actuator_values()

def init_sensors():
    """ Initialise distance sensors, ground sensors etc. """
    global ds, ds_val, gs, gs_val, ts, ts_val, rw_button_state

    # Set up distance sensors
    ds = []
    for i in range(DIST_SENS_COUNT):
        s_name = 'prox.horizontal.{:d}'.format(i)
        # print(ds_name)
        ds.append(robot.getDevice(s_name))
        ds[i].enable(timestep)

    # Create array to store distance sensor readings
    ds_val = [0] * DIST_SENS_COUNT

    # Set up ground sensors
    gs = []
    for i in range(GRND_SENS_COUNT):
        s_name = 'prox.ground.{:d}'.format(i)
        # print(ds_name) # uncomment to debug names
        gs.append(robot.getDevice(s_name))
        gs[i].enable(timestep)

    # Create array to store ground sensor readings
    gs_val = [0] * GRND_SENS_COUNT


def read_sensors():
    """ Read sensor values from hardware into variables """
    global ds, ds_val, gs, gs_val

    for i in range(DIST_SENS_COUNT):
        ds_val[i] = ds[i].getValue()

    for i in range(GRND_SENS_COUNT):
        gs_val[i] = gs[i].getValue()


def reset_actuator_values():
    """ Reset motor & LED target variables to zero/off. """
    global m_spd_l, m_spd_r, led_top_colour
    
    m_spd_l = 0
    m_spd_r = 0
    led_top_colour = 0x000000


def send_actuator_values():
    """ Write motor speed and LED colour variables to hardware.
        Called at the end of the Main loop, after actions have been calculated """
    global m_spd_l, m_spd_r, led_top_colour

    motor_l.setVelocity(m_spd_l)
    motor_r.setVelocity(m_spd_r)
    led_top.set(led_top_colour)

def is_any_obstacle_ahead():
    """ Utility function to return True if an object is detected by the front sensors
        or False otherwise. """
    global ds_val
    
    for i in range(DIST_SENS_COUNT):
        if ds_val[i] > 0:
            return True
    return False # Nothing detected in loop

def decrease_stress():
    """ Decrease stress if the actual level is high """

    global stress_level

    if stress_level >= MIN_STRESS_LEVEL:
            stress_level -= 0.05
            print("SAFE")

    if stress_level < MIN_STRESS_LEVEL:
        stress_level = MIN_STRESS_LEVEL

def decrease_energy():
    """ This function decreases the internal physiological variable energy"""
    global energy_level
    
    # This reduces the energy level slowly
    energy_level -= 0.01

# Normal behavior that makes the robot move in circles
def behaviour_move_robot():
    """ By default it is going to move the robot outside the black zone.
        I use a counter to make possible that when the robot detects with
        the ground sensor a black zone, immediately turn it to the opposite direction """

    global gs_val, time_to_wait

    l = MOTOR_SPEED
    r = MOTOR_SPEED

    now = robot.getTime()

    if gs_val[0] < DARK_COLOR_PROTECTION or gs_val[1] < DARK_COLOR_PROTECTION:
        time_to_wait = now + 1

    # Turn the robot while it detects any black color
    if now < time_to_wait:
        l = -MOTOR_SPEED
        r = MOTOR_SPEED

    return l, r

# Appetitive behaviour that make the robot start to find the track when its level of stress is too high
def behaviour_find_track():
    
    global gs_val, time_to_wait

    l = MOTOR_SPEED
    r = MOTOR_SPEED

    now = robot.getTime()

    # Try to make the robot find the track by approaching the colors of the track
    if 910 < gs_val[0] < 1000:
        l = -MOTOR_SPEED
        r = MOTOR_SPEED
    elif 910 < gs_val[1] < 1000:
        l = MOTOR_SPEED
        r = -MOTOR_SPEED

    if gs_val[0] < DARK_COLOR_PROTECTION or gs_val[1] < DARK_COLOR_PROTECTION:
        time_to_wait = now + 1

    # Turn the robot while it detects any black color
    if now < time_to_wait:
        l = -MOTOR_SPEED
        r = MOTOR_SPEED

    return l, r

# Consummatory Behavior that detects the track on the ground and causes the robot to follow it
def behaviour_follow_track_to_be_safe():
    global m_spd_l, m_spd_r, gs_val, stress_level
    
    l = None
    r = None
    
    # rotates to the left if the ground sensor values are higher than the right and it is between 910-1000
    # because these are the values that the color of the track have. When the robot is on the track it decreases the
    # stress of the robot.
    if (gs_val[0] > gs_val[1]) and (910 < gs_val[0] < 1000):
        print("Go left")
        l = -MOTOR_SPEED
        r = MOTOR_SPEED
        decrease_stress()
    # rotates to the left if the ground sensor values are higher than the right and it is between 910-1000
    # because these are the values that the color of the track have. When the robot is on the track it decreases the
    # stress of the robot.
    elif (gs_val[1] > gs_val[0]) and (910 < gs_val[1] < 1000):
        print("Go right")
        r = -MOTOR_SPEED
        l = MOTOR_SPEED
        decrease_stress()

    return l, r

# Appetitive behavior that make the robot start to find a black ground color when its level of energy is too low
def behaviour_find_black_ground_color():
    """ This function lets the robot to move towards the recharge resource. 
        This is an appetitve behaviour.
        Simply move the robot in a straight line until find the black area """

    l = MOTOR_SPEED
    r = MOTOR_SPEED

    return l, r

# Consummatory behavior that will stop the robot when it needs to recharge its energy
def behaviour_stop_on_black_to_rest():
    global m_spd_l, m_spd_r, gs_val, energy_level
    
    l = None
    r = None

    # It stops the robot in case that the ground sensors of the robot detect that are
    # because these are the values that the color of the track have. When the robot is on the track it decreases the
    # stress of the robot.
    if gs_val[0] < DARK_COLOR_PROTECTION and gs_val[1] < DARK_COLOR_PROTECTION:
        print("Stop")
        l = 0
        r = 0
        
        # Recharge all the energy
        while energy_level < MAX_ENERGY_LEVEL:
            energy_level += 0.05
            print("RESTING") # for test purposes to confirm the behaviour is happening
        # This ensures tha robot does not overcharge (it is not allowed so)

        if energy_level >= MAX_ENERGY_LEVEL:
            energy_level = MAX_ENERGY_LEVEL

    return l, r

# Behavior that take the values of the distance sensors to prevent the robot from colliding with any object
def behaviour_avoid_obstacles():
    global m_spd_l, m_spd_r, ds_val
    
    left = ds_val[0] + ds_val[1] + ds_val[2] + ds_val[3]
    right = ds_val[4] + ds_val[5] + ds_val[6] + ds_val[3]

    l = None
    r = None
    
    if left > right:
        l = MOTOR_SPEED
        r = -MOTOR_SPEED
    elif right > left:
        l = -MOTOR_SPEED
        r = MOTOR_SPEED

    return l, r

def check_recharge_stimulus():
    """ This function is used for sensory input of an external stimuli for the recharge resource."""
    global gs_val
    
    # this IF statment checks to see if the ground sensor on the left or the right is percieving the enegry resource (ground dark area)
    if gs_val[0] < DARK_COLOR_PROTECTION or gs_val[1] < DARK_COLOR_PROTECTION:
        stimulus = 1
    else:
        stimulus = 0
            
    return stimulus

def check_stress_stimulus():
    """ This function is used for sensory input of an external stimuli for decrease the stress."""     
    global ds_val
    
    # this IF statment checks to see if the distance sensor detects any object
    if ds_val[0] > 0 or ds_val[1] > 0 or ds_val[2] > 0 or ds_val[3] > 0 or ds_val[4] > 0 or ds_val[5] > 0 or ds_val[6] > 0:
        stimulus = 1
    else:
        stimulus = 0
            
    return stimulus

def motivation():
    """ This is the main function for the motivational architecture of the robot."""
    global energy_level, stress_level
    
    behaviour_to_rest = None

    # This block of code calculates the motivation for the energy resource
    energy_deficit = MAX_ENERGY_LEVEL - energy_level
    recharge_stimulus = check_recharge_stimulus()
    energy_motivation = energy_deficit + (energy_deficit * recharge_stimulus)

    print("ENERGY MOTIVATION: {}".format(energy_motivation))

    # When energy motivation is over 60 the robot controller is going to
    # execute the appetitive and consummatory behaviour to recharge energy
    if energy_motivation > 60:
        behaviour_to_rest = "REST"    


    behaviour_to_be_protected = None

    # This block of code calculates the motivation for the anti stress source
    stress_deficit = MIN_STRESS_LEVEL + stress_level
    stress_stimulus = check_stress_stimulus()
    stress_motivation = stress_deficit + (stress_deficit * stress_stimulus)

    print("STRESS MOTIVATION: {}".format(stress_motivation))

    # When the stress motivation is over 15 the robot controller is going to
    # execute the appetitive and consummatory behaviour to be protected
    if stress_motivation > 15:
        behaviour_to_be_protected = "PROTECTION"    


    return behaviour_to_rest, behaviour_to_be_protected

# This function is the coordination of my behaviours
def coordination_subsumption():
    """ Function to ccordinate appetitive an consummatory behaviours besides the default behaviour of the robot . """
    global m_spd_l, m_spd_r
    
    motivated_behaviour_energy, motivated_behaviour_stress = motivation()

    # Behaviours related with energy variable
    b_consume_l = None
    b_consume_r = None
    b_find_black_l = None
    b_find_black_r = None

    # Behaviours related with stress variable
    b_follow_track_l = None
    b_follow_track_r = None
    b_find_track_l = None
    b_find_track_r = None

    if motivated_behaviour_energy == "REST":
        b_find_black_l, b_find_black_r = behaviour_find_black_ground_color()
        b_consume_l, b_consume_r = behaviour_stop_on_black_to_rest()

    if motivated_behaviour_stress == "PROTECTION":
        b_find_track_l, b_find_track_r = behaviour_find_track()
        b_follow_track_l, b_follow_track_r = behaviour_follow_track_to_be_safe()

    b_default_l, b_default_r = behaviour_move_robot()

    b_avd_l, b_avd_r = behaviour_avoid_obstacles()
        
   # These IFs below, are the representation of the layer architecture. The most important behaviour is the avoid obstacles behaviour
   # that is going to overwrite all the behaviours if the distance sensors detect any object.
   # From this behavior we can take into account the behaviors related to the motivational variables.
   # In my architecture the most important motivation is that of energy since if the robot runs out of energy it could "die" so it is more important that 
   # the robot recharge the energy even if it feels stressed and wants to go to its comfort zone. 
   # Therefore, behaviors related to recharging energy will overwrite those who seek protection from the robot in case it needs it. '''

   # Output from the avoid obstacles behaviour can inhibit the recharge energy consummatory behaviour
    if b_avd_l is not None:
        b_consume_l = b_avd_l
    if b_avd_r is not None:
        b_consume_r = b_avd_r
        
    # Output from the recharge energy consummatory behaviour can inhibit the find recharge point appetitive behaviour
    if b_consume_l is not None:
        b_find_black_l = b_consume_l
    if b_consume_r is not None:
        b_find_black_r = b_consume_r

    # Output from the find recharge point appetitive behaviour can inhibit the follow the track consummatory behaviour
    if b_find_black_l is not None:
        b_follow_track_l = b_find_black_l
    if b_find_black_r is not None:
        b_follow_track_r = b_find_black_r

    # Output from the follow the track consummatory behaviour can inhibit the the find the track appetitive behaviour
    if b_follow_track_l is not None:
        b_find_track_l = b_follow_track_l
    if b_follow_track_r is not None:
        b_find_track_r = b_follow_track_r

    # Output from the find the track appetitive behaviour can inhibit the default behaviour of the robot
    if b_find_track_l is not None:
        b_default_l = b_find_track_l
    if b_find_track_r is not None:
        b_default_r = b_find_track_r
        
    # All the behaviours return the speed of the left and right motor
    m_spd_l = b_default_l
    m_spd_r = b_default_r
     
#
# Main entry point for code
# 

# Internal physiological states. These are global variables initialised as their respective max values
energy_level = MAX_ENERGY_LEVEL
stress_level = MIN_STRESS_LEVEL

time_to_wait = 0

# Initialisation
init_actuators()
init_sensors()

# Main loop:
# - perform simulation steps until Webots is stopping the controller
while robot.step(timestep) != -1:
    # Read the sensors:
    read_sensors()

    # Process sensor data here.
    reset_actuator_values()
    
    # Execute behaviours...
    # This calls the function that decreases the value energy
    decrease_energy()
    print("ENERGY LEVEL: {}".format(energy_level))

    # This IF is checking if the robot finds an obstacle, in that case it is going to increment
    # the stress level
    if is_any_obstacle_ahead():
        stress_level += 1

    # IF the stress level is over 1500 or the energy is less or equal 0 the robot dies
    if stress_level >= MAX_STRESS_LEVEL or energy_level <= MIN_ENERGY_LEVEL:
        break
     
    # Behaviour coordination
    coordination_subsumption()

    # Send actuator commands:
    send_actuator_values()

# End of Main loop
# Exit & cleanup code.
# (none required)
