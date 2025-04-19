import pygame
import math
import sys
import random
from collections import deque # For storing PV data efficiently

# --- Constants ---
WIDTH, HEIGHT = 1000, 600
FPS = 60

# --- Constants ---
WIDTH, HEIGHT = 1000, 600
FPS = 60
# Colors (Keep existing)
WHITE = (255, 255, 255); BLACK = (0, 0, 0); GRAY = (150, 150, 150); DARK_GRAY = (80, 80, 80); LIGHT_GRAY = (200, 200, 200)
RED = (200, 0, 0); BLUE = (0, 0, 200); YELLOW = (255, 255, 0); ORANGE = (255, 165, 0); BRIGHT_ORANGE = (255, 100, 0)
CYLINDER_COLOR = (180, 180, 190); PISTON_COLOR = (100, 100, 110); CONROD_COLOR = (120, 120, 130); CRANK_COLOR = (90, 90, 100)
RING_COLOR = (60, 60, 70); SPRING_COLOR = (140, 140, 140)
GAS_INTAKE_COLOR = (173, 216, 230); GAS_COMPRESSED_COLOR = (100, 149, 237); GAS_COMBUSTION_START_COLOR = YELLOW
GAS_COMBUSTION_MID_COLOR = BRIGHT_ORANGE; GAS_EXHAUST_COLOR = (169, 169, 169)
PV_PLOT_COLOR = (50, 150, 50); PV_CURRENT_POINT_COLOR = RED; ANNOTATION_COLOR = (0, 0, 100)
BUTTON_COLOR = (180, 180, 220) # Light violet
BUTTON_HOVER_COLOR = (210, 210, 240)
BUTTON_TEXT_COLOR = BLACK
SLIDER_BG_COLOR = (160, 160, 160)
SLIDER_KNOB_COLOR = (90, 90, 110)

# Engine Geometry (Keep existing)
# ... (previous geometry) ...
CYLINDER_CENTER_X = 300; CYLINDER_TOP_Y = 100; CYLINDER_WIDTH = 100; PISTON_HEIGHT = 40
CRANK_RADIUS = 75; CONROD_LENGTH = 180
CRANKSHAFT_CENTER_Y = CYLINDER_TOP_Y + PISTON_HEIGHT / 2 + CONROD_LENGTH + CRANK_RADIUS
CRANKSHAFT_CENTER_X = CYLINDER_CENTER_X
STROKE_LENGTH = 2 * CRANK_RADIUS
VALVE_SIZE = 15; INTAKE_VALVE_X = CYLINDER_CENTER_X - CYLINDER_WIDTH // 4; EXHAUST_VALVE_X = CYLINDER_CENTER_X + CYLINDER_WIDTH // 4
VALVE_Y = CYLINDER_TOP_Y - VALVE_SIZE - 5; VALVE_LIFT = 12
SPARK_PLUG_X = CYLINDER_CENTER_X; SPARK_PLUG_Y = CYLINDER_TOP_Y - 15; SPARK_TIP_Y = CYLINDER_TOP_Y - 5; SPARK_DURATION_FRAMES = 5

# Enhancement Constants (Keep existing)
# ... (previous enhancement constants) ...
NUM_PARTICLES = 150; PARTICLE_RADIUS = 2.5; MAX_PARTICLE_SPEED = 2.5; PARTICLE_ACCEL_FACTOR = 0.05
PARTICLE_EXPANSION_ACCEL = 0.08; PARTICLE_FRICTION = 0.99; COMBUSTION_SPEED_MULTIPLIER = 2.5
COMBUSTION_FLASH_DURATION = 8; COMBUSTION_FADE_DURATION = 40

# --- Educational Feature Constants ---
# PV Diagram Area
PV_RECT = pygame.Rect(WIDTH - 360, 250, 330, 300) # Position and size of the PV plot
PV_PADDING = 25
PV_POINT_HISTORY = 150 # How many points to store for the plot line (2 full cycles approx @ 60fps)
# Conceptual Units for PV
CLEARANCE_VOLUME = 15.0 # Arbitrary minimum volume units at TDC
# Swept volume is proportional to stroke length, let's scale it
SWEPT_VOLUME_SCALE = 0.5 # Make swept volume proportional to pixel stroke
MIN_PRESSURE = 0.8 # Conceptual pressure units (e.g., atm) - Intake/Exhaust
MAX_PRESSURE_COMPRESSION = 15.0 # Peak pressure during compression
MAX_PRESSURE_POWER = 50.0 # Peak pressure during power stroke
COMPRESSION_EXPONENT = 1.4 # Adiabatic index (gamma) approximation for compression/expansion
POWER_EXPONENT = 1.3 # Approximation for expansion after combustion

# Annotation Positions (relative adjustments might be needed)
LABEL_FONT_SIZE = 16
ANNOTATIONS = {
    "Spark Plug": (SPARK_PLUG_X + 10, SPARK_PLUG_Y - 15, SPARK_PLUG_X, SPARK_PLUG_Y),
    "Intake Valve": (INTAKE_VALVE_X - 60, VALVE_Y - 30, INTAKE_VALVE_X, VALVE_Y-5),
    "Exhaust Valve": (EXHAUST_VALVE_X + 50, VALVE_Y - 30, EXHAUST_VALVE_X, VALVE_Y-5),
    "Combustion Chamber": (CYLINDER_CENTER_X - 100, CYLINDER_TOP_Y + 20, CYLINDER_CENTER_X - CYLINDER_WIDTH//2 + 5, CYLINDER_TOP_Y + 10),
    "Piston": (CYLINDER_CENTER_X - 70, -1, CYLINDER_CENTER_X - CYLINDER_WIDTH//2 + 5, -1), # Y depends on piston
    "Connecting Rod": (CYLINDER_CENTER_X - 80, -1, CYLINDER_CENTER_X-5, -1), # Y depends on conrod center
    "Crankshaft": (CRANKSHAFT_CENTER_X + 50, CRANKSHAFT_CENTER_Y + 40, CRANKSHAFT_CENTER_X+5, CRANKSHAFT_CENTER_Y+5),
}

# Stroke Descriptions
STROKE_DESCRIPTIONS = {
    "Intake": "Piston moves down, drawing air-fuel mixture through the open intake valve.",
    "Compression": "Valves close. Piston moves up, compressing the air-fuel mixture, raising pressure and temperature.",
    "Power": "Spark plug ignites mixture. Rapid expansion forces piston down, producing power.",
    "Exhaust": "Exhaust valve opens. Piston moves up, pushing burned gases out of the cylinder.",
}
DESCRIPTION_RECT = pygame.Rect(WIDTH - 360, 100, 330, 120) # Area for stroke description
DESCRIPTION_RECT_H = 80 # Height for description box

# --- Interactivity Constants ---
BUTTON_W, BUTTON_H = 80, 30
SLIDER_W, SLIDER_H = 200, 15
SLIDER_KNOB_W, SLIDER_KNOB_H = 10, 25
MIN_RPM = 10
MAX_RPM = 1000
STEP_ANGLE_DEGREES = 2.0 # How much angle advances per step

# --- Helper Functions ---
# Keep draw_text
def draw_text(surface, text, size, x, y, color=BLACK, align="center", wrap_width=0):
    font = pygame.font.Font(None, size)
    if wrap_width > 0:
        words = text.split(' ')
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            if font.size(test_line)[0] < wrap_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)

        rendered_lines = [font.render(line, True, color) for line in lines]
        line_height = font.get_linesize()
        if align == "topleft":
            start_y = y
            for i, line_surface in enumerate(rendered_lines):
                text_rect = line_surface.get_rect()
                text_rect.topleft = (x, start_y + i * line_height)
                surface.blit(line_surface, text_rect)
        # Add other alignments if needed for wrapped text
    else:
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if align == "center":
            text_rect.midtop = (x, y)
        elif align == "topleft":
            text_rect.topleft = (x, y)
        elif align == "topright":
            text_rect.topright = (x, y)
        surface.blit(text_surface, text_rect)

# --- PV Diagram Drawing Function (Minor tweak for label) ---
def draw_pv_diagram(screen, pv_rect, pv_data, current_v, current_p, v_min, v_max, p_min, p_max):
    pygame.draw.rect(screen, WHITE, pv_rect) # Background
    pygame.draw.rect(screen, BLACK, pv_rect, 2) # Border

    origin_x = pv_rect.left + PV_PADDING
    origin_y = pv_rect.bottom - PV_PADDING
    axis_width = pv_rect.width - 2 * PV_PADDING
    axis_height = pv_rect.height - 2 * PV_PADDING

    pygame.draw.line(screen, BLACK, (origin_x, origin_y), (origin_x + axis_width, origin_y), 2) # X-axis (Volume)
    pygame.draw.line(screen, BLACK, (origin_x, origin_y), (origin_x, origin_y - axis_height), 2) # Y-axis (Pressure)

    draw_text(screen, "Volume", 18, origin_x + axis_width // 2, origin_y + 5, BLACK, "center")
    # Adjusted Pressure label X position slightly left
    draw_text(screen, "Pressure", 18, origin_x - 20, origin_y - axis_height // 2, BLACK, "center") # Needs rotation ideally

    def scale_point(v, p):
        v_range = max(0.1, v_max - v_min)
        x = origin_x + axis_width * ( (v - v_min) / v_range )
        p_range = max(0.1, p_max - p_min)
        y = origin_y - axis_height * ( (p - p_min) / p_range )
        x = max(origin_x, min(origin_x + axis_width, x))
        y = max(origin_y - axis_height, min(origin_y, y))
        return int(x), int(y)

    if len(pv_data) >= 2:
        scaled_points = [scale_point(v, p) for v, p in pv_data]
        pygame.draw.lines(screen, PV_PLOT_COLOR, False, scaled_points, 2)

    current_x, current_y = scale_point(current_v, current_p)
    pygame.draw.circle(screen, PV_CURRENT_POINT_COLOR, (current_x, current_y), 4)

# --- Classes ---

# Keep Particle Class the same as the previous version
class Particle:
    def __init__(self, bounds_rect):
        self.bounds = bounds_rect
        self.x = random.uniform(self.bounds.left + PARTICLE_RADIUS, self.bounds.right - PARTICLE_RADIUS)
        self.y = random.uniform(self.bounds.top + PARTICLE_RADIUS, self.bounds.bottom - PARTICLE_RADIUS)
        self.color = GAS_INTAKE_COLOR
        self.vx = random.uniform(-MAX_PARTICLE_SPEED / 2, MAX_PARTICLE_SPEED / 2)
        self.vy = random.uniform(-MAX_PARTICLE_SPEED / 2, MAX_PARTICLE_SPEED / 2)

    def move_and_draw(self, screen, current_bounds, engine_state):
        self.bounds = current_bounds
        stroke = engine_state['stroke']
        combustion_timer = engine_state['combustion_timer']
        is_combustion_flash = combustion_timer > (COMBUSTION_FADE_DURATION - COMBUSTION_FLASH_DURATION)

        # Acceleration/Forces
        self.vx += random.uniform(-PARTICLE_ACCEL_FACTOR, PARTICLE_ACCEL_FACTOR)
        self.vy += random.uniform(-PARTICLE_ACCEL_FACTOR, PARTICLE_ACCEL_FACTOR)
        if stroke in ["Intake", "Power"]:
            self.vy += PARTICLE_EXPANSION_ACCEL
        speed_multiplier = COMBUSTION_SPEED_MULTIPLIER if is_combustion_flash else 1.0

        # Limit speed & Friction
        speed = math.hypot(self.vx, self.vy) # More robust than sqrt(x**2+y**2)
        max_speed = MAX_PARTICLE_SPEED * speed_multiplier
        if speed > max_speed:
            scale = max_speed / speed
            self.vx *= scale
            self.vy *= scale
        self.vx *= PARTICLE_FRICTION
        self.vy *= PARTICLE_FRICTION

        # Update Position
        self.x += self.vx
        self.y += self.vy

        # Boundary Collisions
        collided = False
        if self.x - PARTICLE_RADIUS < self.bounds.left:
            self.x = self.bounds.left + PARTICLE_RADIUS; self.vx *= -0.8; collided = True
        elif self.x + PARTICLE_RADIUS > self.bounds.right:
            self.x = self.bounds.right - PARTICLE_RADIUS; self.vx *= -0.8; collided = True
        if self.y - PARTICLE_RADIUS < self.bounds.top:
            self.y = self.bounds.top + PARTICLE_RADIUS; self.vy *= -0.8; collided = True
        elif self.y + PARTICLE_RADIUS > self.bounds.bottom:
            self.y = self.bounds.bottom - PARTICLE_RADIUS
            reflect_factor = -0.9 if stroke in ["Compression", "Exhaust"] else -0.5
            self.vy *= reflect_factor
            self.vy -= 0.1
            collided = True

        # Determine Color
        if stroke == "Intake": self.color = GAS_INTAKE_COLOR
        elif stroke == "Compression": self.color = GAS_COMPRESSED_COLOR
        elif stroke == "Power":
            if combustion_timer > 0:
                 if is_combustion_flash: self.color = GAS_COMBUSTION_START_COLOR
                 else:
                      fade_ratio = max(0, combustion_timer - COMBUSTION_FLASH_DURATION) / (COMBUSTION_FADE_DURATION - COMBUSTION_FLASH_DURATION)
                      self.color = ( int(GAS_COMBUSTION_MID_COLOR[0] + (GAS_COMBUSTION_START_COLOR[0] - GAS_COMBUSTION_MID_COLOR[0]) * fade_ratio),
                                     int(GAS_COMBUSTION_MID_COLOR[1] + (GAS_COMBUSTION_START_COLOR[1] - GAS_COMBUSTION_MID_COLOR[1]) * fade_ratio),
                                     int(GAS_COMBUSTION_MID_COLOR[2] + (GAS_COMBUSTION_START_COLOR[2] - GAS_COMBUSTION_MID_COLOR[2]) * fade_ratio) )
            else: self.color = GAS_COMBUSTION_MID_COLOR
        elif stroke == "Exhaust": self.color = GAS_EXHAUST_COLOR

        # Draw
        if self.y >= self.bounds.top + PARTICLE_RADIUS and self.y <= self.bounds.bottom - PARTICLE_RADIUS :
             pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), PARTICLE_RADIUS)


class Engine:
    def __init__(self):
        self.reset() # Initialize state via reset method

    def reset(self):
        """ Resets the engine state to its initial condition. """
        self.crank_angle = 0.0 # Start at BDC
        self.rpm = 60
        self.paused = True # Start paused
        self.stroke = "Compression" # Initial stroke if starting at angle 0 (BDC)
        self.intake_valve_open = False; self.exhaust_valve_open = False
        self.spark_firing = False; self.spark_timer = 0
        self.combustion_timer = 0

        # Kinematic variables
        self.piston_y = 0; self.piston_pin_y = 0; self.crank_pin_x = 0; self.crank_pin_y = 0
        self.piston_pin_x = CYLINDER_CENTER_X

        # TDC/BDC calculation
        self.tdc_pin_y = CRANKSHAFT_CENTER_Y - CRANK_RADIUS - CONROD_LENGTH
        self.bdc_pin_y = CRANKSHAFT_CENTER_Y + CRANK_RADIUS - CONROD_LENGTH
        self.tdc_y = self.tdc_pin_y - PISTON_HEIGHT / 2
        self.bdc_y = self.bdc_pin_y - PISTON_HEIGHT / 2
        self.actual_stroke_pixels = self.bdc_y - self.tdc_y

        # Gas simulation (re-initialize particles or just their state if complex)
        initial_bounds = pygame.Rect(CYLINDER_CENTER_X - CYLINDER_WIDTH // 2, int(self.tdc_y),
                                     CYLINDER_WIDTH, int(self.bdc_y - self.tdc_y))
        # Recreate particles to reset positions/velocities
        self.particles = [Particle(initial_bounds) for _ in range(NUM_PARTICLES)]

        # Educational Feature Data
        self.cylinder_volume = CLEARANCE_VOLUME
        self.pressure = MIN_PRESSURE
        self.pv_data = deque(maxlen=PV_POINT_HISTORY)
        self.swept_volume = self.actual_stroke_pixels * SWEPT_VOLUME_SCALE
        self.max_volume = CLEARANCE_VOLUME + self.swept_volume
        self.min_volume = CLEARANCE_VOLUME

        # Force initial update to set positions correctly for angle 0
        self.perform_update_calculations(0.0) # Update kinematics/state for angle 0

    def perform_update_calculations(self, dt, is_step=False):
        """ Contains the core logic for updating engine state based on angle change. """
        # --- Angle Update ---
        # Only update angle automatically if not paused and not stepping manually
        if not self.paused and not is_step:
             deg_per_second = self.rpm * 360 / 60
             delta_angle = deg_per_second * dt
             self.crank_angle = (self.crank_angle + delta_angle) % 720
        elif is_step:
            self.crank_angle = (self.crank_angle + STEP_ANGLE_DEGREES) % 720

        # --- Kinematics ---
        angle_rad = math.radians(self.crank_angle % 360)
        r = CRANK_RADIUS; l = CONROD_LENGTH; cx = CRANKSHAFT_CENTER_X; cy = CRANKSHAFT_CENTER_Y
        self.crank_pin_x = cx + r * math.sin(angle_rad)
        self.crank_pin_y = cy + r * math.cos(angle_rad)
        sqrt_term_val = l**2 - (r * math.sin(angle_rad))**2
        sqrt_term_val = max(0, sqrt_term_val)
        conrod_vertical_component = math.sqrt(sqrt_term_val)
        self.piston_pin_y = self.crank_pin_y - conrod_vertical_component
        self.piston_y = self.piston_pin_y - PISTON_HEIGHT / 2

        # --- Update Volume ---
        stroke_fraction = (self.piston_y - self.tdc_y) / max(0.1, self.actual_stroke_pixels)
        stroke_fraction = max(0, min(1, stroke_fraction))
        self.cylinder_volume = CLEARANCE_VOLUME + self.swept_volume * stroke_fraction

        # --- Combustion Timer ---
        if self.combustion_timer > 0:
             self.combustion_timer -= 1

        # --- Stroke Logic & Pressure Update ---
        old_stroke = self.stroke
        if 0 <= self.crank_angle < 180: # UP: Compression
            self.stroke = "Compression"; self.intake_valve_open = False; self.exhaust_valve_open = False
            p_start = MIN_PRESSURE * 1.1; vol_ratio = self.max_volume / max(0.1, self.cylinder_volume)
            self.pressure = p_start * (vol_ratio ** COMPRESSION_EXPONENT); self.pressure = min(self.pressure, MAX_PRESSURE_COMPRESSION)
            if 170 <= self.crank_angle < 180 and not self.spark_firing and self.combustion_timer <= 0:
                 self.spark_firing = True; self.spark_timer = SPARK_DURATION_FRAMES
                 self.combustion_timer = COMBUSTION_FADE_DURATION; self.pressure = MAX_PRESSURE_POWER
        elif 180 <= self.crank_angle < 360: # DOWN: Power
            self.stroke = "Power"; self.intake_valve_open = False; self.exhaust_valve_open = False
            p_start = MAX_PRESSURE_POWER; vol_ratio = self.min_volume / max(0.1, self.cylinder_volume)
            self.pressure = p_start * (vol_ratio ** POWER_EXPONENT); self.pressure = max(MIN_PRESSURE, self.pressure)
        elif 360 <= self.crank_angle < 540: # UP: Exhaust
            self.stroke = "Exhaust"; self.intake_valve_open = False; self.exhaust_valve_open = True
            self.pressure = MIN_PRESSURE * 1.05
        else: # 540 <= self.crank_angle < 720 (DOWN: Intake)
            self.stroke = "Intake"; self.intake_valve_open = True; self.exhaust_valve_open = False
            self.pressure = MIN_PRESSURE

        # Update spark visual timer
        if self.spark_timer > 0:
            self.spark_timer -= 1
            if self.spark_timer <= 0: self.spark_firing = False

        # --- Store PV Data Point ---
        # Store point if not paused OR if it's a manual step
        if not self.paused or is_step:
             self.pv_data.append((self.cylinder_volume, self.pressure))

    def update(self, dt):
        """ High-level update called each frame. Delegates calculation if not paused. """
        if not self.paused:
             self.perform_update_calculations(dt, is_step=False)
        # If paused, calculations are only done via step()

    def step(self):
        """ Advances the engine state by a small fixed angle increment. Only works when paused. """
        if self.paused:
            self.perform_update_calculations(0.0, is_step=True) # Pass dt=0, set is_step=True

    def set_rpm(self, new_rpm):
        self.rpm = max(MIN_RPM, min(MAX_RPM, new_rpm)) # Clamp RPM within range

    def toggle_pause(self):
        self.paused = not self.paused

    # --- draw method (needs significant additions for UI) ---
    def draw(self, screen, ui_state):
        # --- Draw Background & Engine Components (same as before) ---
        pygame.draw.rect(screen, DARK_GRAY, (CYLINDER_CENTER_X - CYLINDER_WIDTH*1.5, self.tdc_y + PISTON_HEIGHT , CYLINDER_WIDTH*3, HEIGHT ))
        # ... (Sections 1-7: Cylinder, Flash, Particles, Crank, Conrod, Piston, Valves, Spark Plug - No changes needed here) ...
         # 1. Cylinder/Head
        wall_thickness = 8; head_base_y = CYLINDER_TOP_Y - 30
        pygame.draw.rect(screen, CYLINDER_COLOR, (CYLINDER_CENTER_X - CYLINDER_WIDTH // 2 - wall_thickness, head_base_y, CYLINDER_WIDTH + 2 * wall_thickness, (CYLINDER_TOP_Y-head_base_y) + wall_thickness//2))
        pygame.draw.line(screen, CYLINDER_COLOR, (CYLINDER_CENTER_X - CYLINDER_WIDTH // 2, CYLINDER_TOP_Y), (CYLINDER_CENTER_X - CYLINDER_WIDTH // 2, self.bdc_y + PISTON_HEIGHT + 10), wall_thickness)
        pygame.draw.line(screen, CYLINDER_COLOR, (CYLINDER_CENTER_X + CYLINDER_WIDTH // 2, CYLINDER_TOP_Y), (CYLINDER_CENTER_X + CYLINDER_WIDTH // 2, self.bdc_y + PISTON_HEIGHT + 10), wall_thickness)
        # Combustion Flash
        combustion_chamber_rect = pygame.Rect( CYLINDER_CENTER_X - CYLINDER_WIDTH // 2, CYLINDER_TOP_Y, CYLINDER_WIDTH, max(1, self.piston_y - CYLINDER_TOP_Y) )
        if self.combustion_timer > (COMBUSTION_FADE_DURATION - COMBUSTION_FLASH_DURATION):
             flash_surface = pygame.Surface((combustion_chamber_rect.width, combustion_chamber_rect.height), pygame.SRCALPHA)
             alpha = 150 * ( (self.combustion_timer - (COMBUSTION_FADE_DURATION - COMBUSTION_FLASH_DURATION)) / COMBUSTION_FLASH_DURATION )
             flash_surface.fill((255, 255, 100, int(alpha)))
             screen.blit(flash_surface, combustion_chamber_rect.topleft)
        # 2. Particles
        if combustion_chamber_rect.height > 1:
             engine_state = {'stroke': self.stroke, 'combustion_timer': self.combustion_timer}
             for particle in self.particles: particle.move_and_draw(screen, combustion_chamber_rect, engine_state)
        # 3. Crankshaft
        counter_weight_angle_rad = math.radians((self.crank_angle % 360) + 180); counter_weight_radius = CRANK_RADIUS * 0.9
        start_angle = counter_weight_angle_rad - math.pi/2; stop_angle = counter_weight_angle_rad + math.pi/2
        try: pygame.draw.arc(screen, CRANK_COLOR, (CRANKSHAFT_CENTER_X - counter_weight_radius, CRANKSHAFT_CENTER_Y - counter_weight_radius, 2*counter_weight_radius, 2*counter_weight_radius), start_angle, stop_angle, int(counter_weight_radius//1.2))
        except ValueError: pass
        pygame.draw.circle(screen, DARK_GRAY, (int(CRANKSHAFT_CENTER_X), int(CRANKSHAFT_CENTER_Y)), 15)
        pygame.draw.line(screen, CRANK_COLOR, (CRANKSHAFT_CENTER_X, CRANKSHAFT_CENTER_Y), (self.crank_pin_x, self.crank_pin_y), 12)
        pygame.draw.circle(screen, GRAY, (int(self.crank_pin_x), int(self.crank_pin_y)), 8)
        # 4. Conrod
        pygame.draw.line(screen, CONROD_COLOR, (self.piston_pin_x, self.piston_pin_y), (self.crank_pin_x, self.crank_pin_y), 10)
        # 5. Piston
        piston_rect = pygame.Rect(CYLINDER_CENTER_X - CYLINDER_WIDTH // 2, self.piston_y, CYLINDER_WIDTH, PISTON_HEIGHT)
        pygame.draw.rect(screen, PISTON_COLOR, piston_rect); pygame.draw.rect(screen, DARK_GRAY, piston_rect, 2)
        ring_y_offset = PISTON_HEIGHT * 0.15; ring_height = 2
        for i in range(3): ring_y = self.piston_y + ring_y_offset + i * (ring_height + 3); pygame.draw.rect(screen, RING_COLOR, (piston_rect.left + 2, ring_y, piston_rect.width - 4, ring_height))
        pygame.draw.circle(screen, GRAY, (int(self.piston_pin_x), int(self.piston_pin_y)), 6)
        # 6. Valves
        intake_color = BLUE if self.intake_valve_open else DARK_GRAY; intake_y_offset = VALVE_LIFT if self.intake_valve_open else 0
        intake_valve_rect = pygame.Rect(INTAKE_VALVE_X - VALVE_SIZE // 2, VALVE_Y - intake_y_offset, VALVE_SIZE, VALVE_SIZE)
        pygame.draw.rect(screen, intake_color, intake_valve_rect); stem_top_y = intake_valve_rect.top; stem_bottom_y = stem_top_y - 15
        pygame.draw.line(screen, DARK_GRAY, (INTAKE_VALVE_X, stem_top_y), (INTAKE_VALVE_X, stem_bottom_y), 3)
        for i in range(4): spring_y = stem_bottom_y - i * 3; pygame.draw.line(screen, SPRING_COLOR, (INTAKE_VALVE_X - 4, spring_y), (INTAKE_VALVE_X + 4, spring_y - 1.5), 2)
        exhaust_color = RED if self.exhaust_valve_open else DARK_GRAY; exhaust_y_offset = VALVE_LIFT if self.exhaust_valve_open else 0
        exhaust_valve_rect = pygame.Rect(EXHAUST_VALVE_X - VALVE_SIZE // 2, VALVE_Y - exhaust_y_offset, VALVE_SIZE, VALVE_SIZE)
        pygame.draw.rect(screen, exhaust_color, exhaust_valve_rect); stem_top_y = exhaust_valve_rect.top; stem_bottom_y = stem_top_y - 15
        pygame.draw.line(screen, DARK_GRAY, (EXHAUST_VALVE_X, stem_top_y), (EXHAUST_VALVE_X, stem_bottom_y), 3)
        for i in range(4): spring_y = stem_bottom_y - i * 3; pygame.draw.line(screen, SPRING_COLOR, (EXHAUST_VALVE_X - 4, spring_y), (EXHAUST_VALVE_X + 4, spring_y - 1.5), 2)
        # 7. Spark Plug
        pygame.draw.line(screen, DARK_GRAY, (SPARK_PLUG_X, SPARK_PLUG_Y), (SPARK_PLUG_X, SPARK_TIP_Y), 4); pygame.draw.line(screen, BLACK, (SPARK_PLUG_X, SPARK_TIP_Y), (SPARK_PLUG_X, SPARK_TIP_Y+3), 2)
        if self.spark_firing:
            spark_center = (SPARK_PLUG_X, SPARK_TIP_Y + 7); num_points = 7; outer_radius = 12; inner_radius = 5
            for i in range(num_points * 2): radius = outer_radius if i % 2 == 0 else inner_radius; angle = math.pi * 2 * i / (num_points * 2) - math.pi / 2; p1 = spark_center; p2 = (spark_center[0] + radius * math.cos(angle), spark_center[1] + radius * math.sin(angle)); pygame.draw.line(screen, YELLOW, p1, p2, random.randint(1,3))

        # --- Draw Educational UI Elements & New Controls ---
        ui_x = PV_RECT.left # Base X for the UI panel
        ui_panel_width = PV_RECT.width
        current_y = 30 # Track current Y position for layout

        # Title
        draw_text(screen, "4-Stroke Engine Simulation", 28, ui_x + ui_panel_width // 2, current_y, align="center")
        current_y += 35 # Space after title

        # --- Buttons ---
        button_y = current_y
        button_spacing = 15
        # Play/Pause Button
        play_pause_text = "Play" if self.paused else "Pause"
        play_pause_rect = pygame.Rect(ui_x, button_y, BUTTON_W, BUTTON_H)
        pygame.draw.rect(screen, BUTTON_HOVER_COLOR if play_pause_rect.collidepoint(ui_state['mouse_pos']) else BUTTON_COLOR, play_pause_rect, border_radius=5)
        draw_text(screen, play_pause_text, 20, play_pause_rect.centerx, play_pause_rect.centery - 10, BUTTON_TEXT_COLOR, "center")

        # Reset Button
        reset_rect = pygame.Rect(play_pause_rect.right + button_spacing, button_y, BUTTON_W, BUTTON_H)
        pygame.draw.rect(screen, BUTTON_HOVER_COLOR if reset_rect.collidepoint(ui_state['mouse_pos']) else BUTTON_COLOR, reset_rect, border_radius=5)
        draw_text(screen, "Reset", 20, reset_rect.centerx, reset_rect.centery - 10, BUTTON_TEXT_COLOR, "center")

        # Step Button (Only functional when paused)
        step_rect = pygame.Rect(reset_rect.right + button_spacing, button_y, BUTTON_W, BUTTON_H)
        step_button_color = BUTTON_COLOR
        step_text_color = BUTTON_TEXT_COLOR
        if not self.paused:
             step_button_color = GRAY # Dim if not paused
             step_text_color = DARK_GRAY
        elif step_rect.collidepoint(ui_state['mouse_pos']):
             step_button_color = BUTTON_HOVER_COLOR

        pygame.draw.rect(screen, step_button_color, step_rect, border_radius=5)
        draw_text(screen, "Step", 20, step_rect.centerx, step_rect.centery - 10, step_text_color, "center")

        current_y += BUTTON_H + 15 # Space after buttons

        # --- RPM Slider ---
        slider_label_y = current_y
        draw_text(screen, f"RPM: {self.rpm:.0f}", 20, ui_x, slider_label_y, align="topleft", color=BLACK)
        slider_y = slider_label_y + 25
        slider_rect = pygame.Rect(ui_x, slider_y, SLIDER_W, SLIDER_H)
        pygame.draw.rect(screen, SLIDER_BG_COLOR, slider_rect, border_radius=3)
        # Calculate knob position based on RPM
        rpm_fraction = (self.rpm - MIN_RPM) / max(1, MAX_RPM - MIN_RPM)
        knob_x = slider_rect.left + rpm_fraction * (slider_rect.width - SLIDER_KNOB_W) # Adjust for knob width
        knob_rect = pygame.Rect(knob_x, slider_rect.centery - SLIDER_KNOB_H // 2, SLIDER_KNOB_W, SLIDER_KNOB_H)
        pygame.draw.rect(screen, SLIDER_KNOB_COLOR, knob_rect, border_radius=3)

        current_y = slider_rect.bottom + 15 # Space after slider

        # --- Info Text (Angle, Stroke, V, P) ---
        # Repositioned below slider
        line_height_info = 26
        draw_text(screen, f"Cycle Angle: {self.crank_angle:.1f}°", 20, ui_x, current_y, align="topleft", color=BLACK)
        current_y += line_height_info
        draw_text(screen, f"Stroke: {self.stroke}", 20, ui_x, current_y, align="topleft", color=BLACK)
        current_y += line_height_info
        draw_text(screen, f"Volume: {self.cylinder_volume:.1f}", 18, ui_x, current_y, align="topleft", color=BLACK)
        current_y += line_height_info - 2
        draw_text(screen, f"Pressure: {self.pressure:.1f}", 18, ui_x, current_y, align="topleft", color=BLACK)
        current_y += line_height_info + 5

        # --- Stroke Description ---
        dynamic_description_rect = pygame.Rect(ui_x, current_y, ui_panel_width, DESCRIPTION_RECT_H)
        pygame.draw.rect(screen, WHITE, dynamic_description_rect); pygame.draw.rect(screen, BLACK, dynamic_description_rect, 1)
        description = STROKE_DESCRIPTIONS.get(self.stroke, "")
        draw_text(screen, description, 18, dynamic_description_rect.left + 10, dynamic_description_rect.top + 10,
                  color=BLACK, align="topleft", wrap_width=dynamic_description_rect.width - 20)
        current_y = dynamic_description_rect.bottom + 10

        # --- PV Diagram ---
        # Make PV diagram take remaining space or fixed size
        pv_rect_final_h = HEIGHT - current_y - 15 # Calculate remaining height with bottom padding
        pv_rect_final = pygame.Rect(ui_x, current_y, ui_panel_width, pv_rect_final_h)
        draw_pv_diagram(screen, pv_rect_final, self.pv_data,
                        self.cylinder_volume, self.pressure,
                        self.min_volume, self.max_volume,
                        MIN_PRESSURE * 0.8, MAX_PRESSURE_POWER * 1.1)

        # --- Draw Annotations (Same as before) ---
        # ... (Annotation drawing loop) ...
        for name, (text_x, text_y, point_x, point_y) in ANNOTATIONS.items():
            current_point_y = point_y; current_point_x = point_x # Defaults
            if name == "Piston":
                 text_y = self.piston_y + PISTON_HEIGHT * 0.5; current_point_y = self.piston_y + PISTON_HEIGHT * 0.5
            elif name == "Connecting Rod":
                 mid_conrod_x = (self.piston_pin_x + self.crank_pin_x) / 2; mid_conrod_y = (self.piston_pin_y + self.crank_pin_y) / 2
                 text_y = mid_conrod_y; current_point_x = mid_conrod_x; current_point_y = mid_conrod_y
            pygame.draw.line(screen, ANNOTATION_COLOR, (text_x, text_y), (current_point_x + 3, current_point_y), 1)
            draw_text(screen, name, LABEL_FONT_SIZE, text_x, text_y - LABEL_FONT_SIZE // 2 -1, ANNOTATION_COLOR, align="center")


        # --- Pause Overlay ---
        if self.paused and not ui_state.get("is_dragging_slider", False): # Don't obscure UI while dragging slider
             overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill((0, 0, 0, 128))
             screen.blit(overlay, (0,0))
             # Draw smaller PAUSED text to avoid covering buttons/slider too much
             draw_text(screen, "PAUSED", 48, ui_x - 50, 50 , RED, align="center")


# --- Main Game Loop --- (Modified for UI interaction)
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("4-Stroke Engine Simulation - Interactive UI")
    clock = pygame.time.Clock()
    engine = Engine()

    # --- UI State Variables ---
    is_dragging_slider = False
    # Store UI element rects for click detection (defined within the draw logic for dynamic positioning)
    # We will get them dynamically within the loop for now

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                # Keep spacebar as alternative toggle? Optional.
                # if event.key == pygame.K_SPACE: engine.toggle_pause()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left mouse button
                    # Define button rects based on current draw positions (could be optimized)
                    # Note: This assumes fixed positions - better to calculate them once before the draw call
                    # or pass them back from draw if truly dynamic. Using approximate fixed positions for simplicity here.
                    ui_x = PV_RECT.left # Approx start of UI panel
                    btn_y_approx = 30 + 35 # Approx Y of buttons

                    play_pause_btn_rect = pygame.Rect(ui_x, btn_y_approx, BUTTON_W, BUTTON_H)
                    reset_btn_rect = pygame.Rect(play_pause_btn_rect.right + 15, btn_y_approx, BUTTON_W, BUTTON_H)
                    step_btn_rect = pygame.Rect(reset_btn_rect.right + 15, btn_y_approx, BUTTON_W, BUTTON_H)

                    # RPM Slider Knob Rect (Needs calculation based on current RPM)
                    slider_base_y = btn_y_approx + BUTTON_H + 15 + 25 # Approx Y of slider bar
                    slider_base_rect = pygame.Rect(ui_x, slider_base_y, SLIDER_W, SLIDER_H)
                    rpm_frac = (engine.rpm - MIN_RPM) / max(1, MAX_RPM - MIN_RPM)
                    knob_x_pos = slider_base_rect.left + rpm_frac * (slider_base_rect.width - SLIDER_KNOB_W)
                    slider_knob_rect = pygame.Rect(knob_x_pos, slider_base_rect.centery - SLIDER_KNOB_H // 2, SLIDER_KNOB_W, SLIDER_KNOB_H)


                    # Button Clicks
                    if play_pause_btn_rect.collidepoint(event.pos):
                        engine.toggle_pause()
                    elif reset_btn_rect.collidepoint(event.pos):
                        engine.reset()
                        is_dragging_slider = False # Stop dragging on reset
                    elif step_btn_rect.collidepoint(event.pos) and engine.paused:
                        engine.step()
                    # Slider Click/Drag Start
                    elif slider_knob_rect.collidepoint(event.pos):
                        is_dragging_slider = True


            if event.type == pygame.MOUSEBUTTONUP:
                 if event.button == 1: # Left mouse button
                      is_dragging_slider = False

            if event.type == pygame.MOUSEMOTION:
                 if is_dragging_slider and mouse_pressed[0]: # Check if left button is still held
                    # Define slider rect again (could be optimized)
                    ui_x = PV_RECT.left
                    btn_y_approx = 30 + 35
                    slider_base_y = btn_y_approx + BUTTON_H + 15 + 25
                    slider_bar_rect = pygame.Rect(ui_x, slider_base_y, SLIDER_W, SLIDER_H)

                    # Update knob position and RPM based on mouse X
                    relative_x = event.pos[0] - slider_bar_rect.left
                    new_rpm_fraction = max(0, min(1, relative_x / slider_bar_rect.width))
                    new_rpm = MIN_RPM + new_rpm_fraction * (MAX_RPM - MIN_RPM)
                    engine.set_rpm(new_rpm)


        # --- Update ---
        engine.update(dt) # Engine internal update logic

        # --- Draw ---
        screen.fill(LIGHT_GRAY)
        # Pass UI state needed for drawing (mouse pos, dragging state)
        ui_draw_state = {
            'mouse_pos': mouse_pos,
            'is_dragging_slider': is_dragging_slider
        }
        engine.draw(screen, ui_draw_state)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()