from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random

# Some Basic Global Variables 
camera_pos = (0, 500, 500)
fovY = 120
GRID_LENGTH = 600

# Grid initial rotation angles
grid_rot_horizontal = 90

# For Randomized Grid color state
grid_colors_randomized = False
grid_block_colors = None
grid_block_colors_prev = None
grid_rot_vertical = 0

# Snake config
CELL = 40                 # Increased for larger snake and food (was 32)
SNAKE_INIT_LEN = 5
SNAKE_STEP_FRAMES = 12    # Base movement frames
SNAKE_MIN_LEN = 3

# Snake speed factor (lower = faster, higher = slower)
SNAKE_SPEED_FACTOR = 10  # You can change this value to control speed

# Food spawn margins so items don't overlap walls
SPAWN_MARGIN = 60

# Game state
snake = []                # list of [x,y,z] (z fixed = 20)
direction = [CELL, 0]     # initial dir along +x
pending_turn = None       # queued turn to avoid double-turns in one step
move_frame_counter = 0
score = 0
game_over = False

# Cheat mode
cheat_mode = False

# Snake color state
snake_body_colors = None      # List of [r,g,b] for each body segment
snake_body_colors_prev = None # Backup for restore
snake_color_randomized = False # True if random color mode is active


# Items
food_normal = None        # cube: grow +1, +1 point
food_shrink = None        # cube: release 2 tail cubes, +0 points
food_special = None       # sphere: +5 points, no length change

# Camera control (keep from template)
camera_angle_horizontal = 0
camera_height = 500

# View mode: 'third' or 'first'
view_mode = 'third'

# ---------- Utility ----------
def snap_to_cell(v):
    # keep items aligned to CELL grid
    return int(round(v / CELL)) * CELL

def rand_cell_pos():
    x = random.randint(-(GRID_LENGTH - SPAWN_MARGIN)//CELL, (GRID_LENGTH - SPAWN_MARGIN)//CELL) * CELL
    y = random.randint(-(GRID_LENGTH - SPAWN_MARGIN)//CELL, (GRID_LENGTH - SPAWN_MARGIN)//CELL) * CELL
    return x, y

def spawn_food_away_from_snake():
    while True:
        x, y = rand_cell_pos()
        if all(abs(seg[0]-x) > CELL or abs(seg[1]-y) > CELL for seg in snake):
            return [x, y, 20]

# ---------- Template UI ----------
try:
    GLUT_BITMAP_HELVETICA_18
except NameError:
    GLUT_BITMAP_HELVETICA_18 = GLUT.GLUT_BITMAP_HELVETICA_18
try:
    GLUT_BITMAP_TIMES_ROMAN_24
except NameError:
    GLUT_BITMAP_TIMES_ROMAN_24 = GLUT.GLUT_BITMAP_TIMES_ROMAN_24

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18, color=(1,1,1)):
    glColor3f(*color)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# ---------- Grid (kept like your template) ----------
def draw_grid_and_boundaries():

    # ...existing code...

    global grid_colors_randomized, grid_block_colors
    glBegin(GL_QUADS)
    divisions = 4
    sec = GRID_LENGTH // divisions
    total_blocks = (divisions*2) * (divisions*2)
    if grid_block_colors is None or len(grid_block_colors) != total_blocks:
        # Default colors
        grid_block_colors = []
        for i in range(-divisions, divisions):
            for j in range(-divisions, divisions):
                if (i + j) % 2 == 0:
                    grid_block_colors.append((0.9, 0.9, 0.9))
                else:
                    grid_block_colors.append((0.7, 0.5, 0.95))
    # If randomized, set all purple blocks to the same color
    if grid_colors_randomized:
        # Find a random color
        rand_color = (random.uniform(0.5,1.0), random.uniform(0.5,1.0), random.uniform(0.5,1.0))
        for idx in range(total_blocks):
            if grid_block_colors[idx] == (0.7, 0.5, 0.95):
                grid_block_colors[idx] = rand_color
    idx = 0
    for i in range(-divisions, divisions):
        for j in range(-divisions, divisions):
            r, g, b = grid_block_colors[idx]
            glColor3f(r, g, b)
            x1 = i * sec
            x2 = (i + 1) * sec
            y1 = j * sec
            y2 = (j + 1) * sec
            glVertex3f(x1, y1, 0)
            glVertex3f(x2, y1, 0)
            glVertex3f(x2, y2, 0)
            glVertex3f(x1, y2, 0)
            idx += 1
    glEnd()

    boundary_height = 100
    glColor3f(0.15, 0.78, 0.85)
    glPushMatrix()
    glTranslatef(0, GRID_LENGTH, boundary_height / 2)
    glScalef(GRID_LENGTH * 2, 10, boundary_height)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.68, 0.84, 0.51)
    glPushMatrix()
    glTranslatef(0, -GRID_LENGTH, boundary_height / 2)
    glScalef(GRID_LENGTH * 2, 10, boundary_height)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.0, 0.0, 0.545)
    glPushMatrix()
    glTranslatef(-GRID_LENGTH, 0, boundary_height / 2)
    glScalef(10, GRID_LENGTH * 2, boundary_height)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(1, 1, 1)
    glPushMatrix()
    glTranslatef(GRID_LENGTH, 0, boundary_height / 2)
    glScalef(10, GRID_LENGTH * 2, boundary_height)
    glutSolidCube(1)
    glPopMatrix()

    # ...existing code...

# ---------- Camera (uses your template approach) ----------
def setupCamera():
    global view_mode, snake
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if view_mode == 'third':
        cam_dist = 500
        cam_x = cam_dist * math.cos(math.radians(camera_angle_horizontal))
        cam_y = cam_dist * math.sin(math.radians(camera_angle_horizontal))
        gluLookAt(cam_x, cam_y, camera_height, 0, 0, 0, 0, 0, 1)
    else:
        # First person: camera slightly above and behind snake head, looking forward
        if snake:
            hx, hy, hz = snake[0]
            dx, dy = direction[0], direction[1]
            mag = math.sqrt(dx*dx + dy*dy)
            if mag == 0:
                dx, dy = 1, 0
            else:
                dx, dy = dx/mag, dy/mag
            # Camera position: behind and above the head
            cam_x = hx - dx * CELL * 1.5
            cam_y = hy - dy * CELL * 1.5
            cam_z = hz + CELL * 2.0
            # Look at: forward from head
            look_x = hx + dx * CELL * 2.5
            look_y = hy + dy * CELL * 2.5
            look_z = hz
            gluLookAt(cam_x, cam_y, cam_z, look_x, look_y, look_z, 0, 0, 1)
        else:
            gluLookAt(0, -CELL * 2, CELL * 2, CELL * 2, 0, 0, 0, 0, 1)

# ---------- Snake Rendering ----------
def draw_snake():
    # Head (distinct color)
    if not snake:
        return
    hx, hy, hz = snake[0]
    glPushMatrix()
    glTranslatef(hx, hy, hz)
    glColor3f(0.2, 0.9, 0.2)
    glutSolidCube(CELL * 1.1)  # Slightly larger head
    glPopMatrix()

    # Body
    global snake_body_colors, snake_color_randomized
    # Ensure color list matches snake length
    if snake_body_colors is None or len(snake_body_colors) != len(snake)-1:
        if snake_color_randomized:
            snake_body_colors = [[random.uniform(0.0,1.0), random.uniform(0.0,1.0), random.uniform(0.0,1.0)] for _ in range(len(snake)-1)]
        else:
            snake_body_colors = [[0.0, 0.6, 0.0] for _ in range(len(snake)-1)]
    for idx, seg in enumerate(snake[1:]):
        glPushMatrix()
        glTranslatef(seg[0], seg[1], seg[2])
        r, g, b = snake_body_colors[idx]
        glColor3f(r, g, b)
        glutSolidCube(CELL)
        glPopMatrix()

# ---------- Food Rendering ----------
def draw_food():
    # normal cube (grow) - orange
    if food_normal:
        glPushMatrix()
        glTranslatef(food_normal[0], food_normal[1], food_normal[2])
        glColor3f(1.0, 0.6, 0.0)  # orange
        glutSolidCube(CELL * 1.1)  # larger
        glPopMatrix()

    # shrink cube (release 2) - red
    if food_shrink:
        glPushMatrix()
        glTranslatef(food_shrink[0], food_shrink[1], food_shrink[2])
        glColor3f(0.9, 0.1, 0.1)  # red
        glutSolidCube(CELL * 1.1)  # larger
        glPopMatrix()

    # special sphere (bonus) - yellow
    if food_special:
        glPushMatrix()
        glTranslatef(food_special[0], food_special[1], food_special[2])
        glColor3f(1.0, 1.0, 0.0)  # yellow
        gluSphere(gluNewQuadric(), CELL * 0.9, 24, 24)  # larger sphere
        glPopMatrix()

# ---------- Game Logic ----------
def reset_game():
    global snake, direction, score, game_over
    global food_normal, food_shrink, food_special
    global move_frame_counter, pending_turn

    score = 0
    game_over = False
    move_frame_counter = 0
    pending_turn = None

    # center-start snake along +x
    snake = []
    start_x, start_y = 0, 0
    for i in range(SNAKE_INIT_LEN):
        snake.append([start_x - i * CELL, start_y, 20])
    direction = [CELL, 0]

    # Food rarity: orange (normal) most common, yellow (special) rare, red (shrink) most rare
    food_normal = spawn_food_away_from_snake()   # always at least one orange
    food_special = None
    food_shrink = None
    roll = random.random()
    if roll < 0.2:
        food_special = spawn_food_away_from_snake()  # yellow, rare
    elif roll < 0.3:
        food_shrink = spawn_food_away_from_snake()   # red, most rare

def move_snake_one_step():
    global snake, food_normal, food_shrink, food_special, score, game_over

    apply_pending_turn()

    hx, hy, hz = snake[0]
    nx = hx + direction[0]
    ny = hy + direction[1]
    nz = hz

    if abs(nx) >= GRID_LENGTH or abs(ny) >= GRID_LENGTH:
        game_over = True
        return

    for seg in snake[1:]:
        if seg[0] == nx and seg[1] == ny:
            game_over = True
            return

    snake.insert(0, [nx, ny, nz])
    # Update color list for new segment
    global snake_body_colors, snake_color_randomized
    if snake_body_colors is not None:
        if snake_color_randomized:
            # Add a new random color at the head
            snake_body_colors = [[random.uniform(0.0,1.0), random.uniform(0.0,1.0), random.uniform(0.0,1.0)]] + snake_body_colors
        else:
            # Add default green
            snake_body_colors = [[0.0, 0.6, 0.0]] + snake_body_colors
        # Remove tail color if snake shrinks
        while len(snake_body_colors) > len(snake)-1:
            snake_body_colors.pop()

    ate_normal = food_normal and nx == food_normal[0] and ny == food_normal[1]
    ate_shrink = food_shrink and nx == food_shrink[0] and ny == food_shrink[1]
    ate_special = food_special and nx == food_special[0] and ny == food_special[1]

    if ate_normal:
        score += 1
        food_normal = None
        # Orange most common, yellow rare, red most rare
        roll = random.random()
        if roll < 0.7:
            food_normal = spawn_food_away_from_snake()
        elif roll < 0.9:
            food_special = spawn_food_away_from_snake()
        else:
            food_shrink = spawn_food_away_from_snake()
        # no tail pop
    elif ate_special:
        score += 5
        food_special = None
        # Orange most common, yellow rare, red most rare
        roll = random.random()
        if roll < 0.7:
            food_normal = spawn_food_away_from_snake()
        elif roll < 0.9:
            food_special = spawn_food_away_from_snake()
        else:
            food_shrink = spawn_food_away_from_snake()
        snake.pop()
    elif ate_shrink:
        if len(snake) > SNAKE_MIN_LEN:
            snake.pop()
        if len(snake) > SNAKE_MIN_LEN:
            snake.pop()
        food_shrink = None
        # Orange most common, yellow rare, red most rare
        roll = random.random()
        if roll < 0.7:
            food_normal = spawn_food_away_from_snake()
        elif roll < 0.9:
            food_special = spawn_food_away_from_snake()
        else:
            food_shrink = spawn_food_away_from_snake()
        if len(snake) > SNAKE_MIN_LEN:
            snake.pop()
    else:
        snake.pop()
        # Remove tail color if snake shrinks
        if snake_body_colors is not None and len(snake_body_colors) > len(snake)-1:
            snake_body_colors.pop()

def apply_pending_turn():
    global pending_turn, direction
    if not pending_turn:
        return
    # ignore reversal if length > 1
    ndx, ndy = pending_turn
    if len(snake) > 1 and snake[0][0] + ndx == snake[1][0] and snake[0][1] + ndy == snake[1][1]:
        pending_turn = None
        return
    direction = [ndx, ndy]
    pending_turn = None

def speed_frames():
    # Only yellow food (score +5) increases speed, others do not
    # So, speed only increases for multiples of 5 score (yellow sphere)
    yellow_score = score // 10
    # Apply speed factor
    base_speed = SNAKE_STEP_FRAMES - yellow_score
    return max(2, int(base_speed * SNAKE_SPEED_FACTOR))

# ---------- Input ----------
def keyboardListener(key, x, y):
    # Snake speed control
    global SNAKE_SPEED_FACTOR
    if key == b'+':
        SNAKE_SPEED_FACTOR = max(0.5, SNAKE_SPEED_FACTOR - 0.5)  # + = faster
        print("Snake speed increased (faster). Speed factor:", SNAKE_SPEED_FACTOR)
    elif key == b'-':
        SNAKE_SPEED_FACTOR = min(20, SNAKE_SPEED_FACTOR + 0.5)  # - = slower
        print("Snake speed decreased (slower). Speed factor:", SNAKE_SPEED_FACTOR)
    global game_over
    global grid_rot_horizontal, grid_rot_vertical
    if game_over and key == b"r":
        print("Game reset!")
        reset_game()
    # Grid rotation controls
    rot_step = 10
    if key == b'a':
        grid_rot_horizontal += rot_step
        print("Grid rotated left (horizontal):", grid_rot_horizontal)
    elif key == b'd':
        grid_rot_horizontal -= rot_step
        print("Grid rotated right (horizontal):", grid_rot_horizontal)
    elif key == b'w':
        grid_rot_vertical = min(grid_rot_vertical + rot_step, 120)
        print("Grid rotated up (vertical):", grid_rot_vertical)
    elif key == b's':
        grid_rot_vertical = max(grid_rot_vertical - rot_step, -20)
        print("Grid rotated down (vertical):", grid_rot_vertical)

    # Move snake forward/backward relative to current heading
    global pending_turn, direction, cheat_mode, grid_colors_randomized, grid_block_colors, grid_block_colors_prev
    # Grid color randomize/restore
    if key == b'h':
        if not grid_colors_randomized:
            # Save previous colors
            if grid_block_colors is not None:
                grid_block_colors_prev = [tuple(c) for c in grid_block_colors]
            grid_colors_randomized = True
            print("Grid colors randomized.")
        else:
            # Restore previous colors
            if grid_block_colors_prev is not None and len(grid_block_colors_prev) == len(grid_block_colors):
                grid_block_colors = [tuple(c) for c in grid_block_colors_prev]
            grid_colors_randomized = False
            print("Grid colors restored.")
    # Cheat mode toggle
    if key == b'g':
        cheat_mode = not cheat_mode
        print(f"Cheat mode {'enabled' if cheat_mode else 'disabled'}.")
        if key == b'w':
            pending_turn = [0, CELL]
            print("Cheat: Move snake forward.")
        elif key == b's':
            pending_turn = [0, -CELL]
            print("Cheat: Move snake backward.")

    # ---------------------- Exit program function ---------------------- 
    if key == b'q':
        print("Quitting the program...")
        glutDestroyWindow(wind)  # Destroy the OpenGL window
        sys.exit(0)  # Exit the program
    global snake_body_colors, snake_body_colors_prev, snake_color_randomized, view_mode
    # View toggle
    if key == b'f':
        view_mode = 'first' if view_mode == 'third' else 'third'
    # Color randomize/restore
    if key == b'c':
        # Save previous colors
        if snake_body_colors is not None:
            snake_body_colors_prev = [list(c) for c in snake_body_colors]
        # Randomize new colors and activate random mode
        snake_body_colors = [[random.uniform(0.0,1.0), random.uniform(0.0,1.0), random.uniform(0.0,1.0)] for _ in range(len(snake)-1)]
        snake_color_randomized = True
    elif key == b'v':
        # Restore previous colors and deactivate random mode
        if snake_body_colors_prev is not None and len(snake_body_colors_prev) == len(snake)-1:
            snake_body_colors = [list(c) for c in snake_body_colors_prev]
        snake_color_randomized = False
    glutPostRedisplay()

def keyboardUpListener(key, x, y):
    pass  # not needed for snake

def specialKeyListener(key, x, y):
    # queue turn to apply exactly on next step
    global pending_turn, camera_angle_horizontal, camera_height, direction, view_mode
    if view_mode == 'third':
        # Remap for grid rotated 90 degrees left
        if key == GLUT_KEY_UP:
            pending_turn = [0, CELL]    # up
        elif key == GLUT_KEY_DOWN:
            pending_turn = [0, -CELL]  # down
        elif key == GLUT_KEY_LEFT:
            pending_turn = [-CELL, 0]  # left
        elif key == GLUT_KEY_RIGHT:
            pending_turn = [CELL, 0]   # right
    else:
        # First-person: rotate direction relative to current heading
        dx, dy = direction[0], direction[1]
        # Only allow movement in cardinal directions
        if abs(dx) > 0 and dy == 0:
            # Moving along x axis
            if key == GLUT_KEY_LEFT:
                pending_turn = [0, -CELL]  # turn left (to -y)
            elif key == GLUT_KEY_RIGHT:
                pending_turn = [0, CELL]   # turn right (to +y)
            elif key == GLUT_KEY_UP:
                pending_turn = [dx, 0]     # keep moving forward
            elif key == GLUT_KEY_DOWN:
                pending_turn = [-dx, 0]    # reverse
        elif abs(dy) > 0 and dx == 0:
            # Moving along y axis
            if key == GLUT_KEY_LEFT:
                pending_turn = [-CELL, 0]  # turn left (to -x)
            elif key == GLUT_KEY_RIGHT:
                pending_turn = [CELL, 0]   # turn right (to +x)
            elif key == GLUT_KEY_UP:
                pending_turn = [0, dy]     # keep moving forward
            elif key == GLUT_KEY_DOWN:
                pending_turn = [0, -dy]    # reverse

def mouseListener(button, state, x, y):
    # not used in snake; kept for template consistency
    pass

# ---------- Idle / Draw ----------
def idle():
    global move_frame_counter, game_over, cheat_mode, pending_turn, snake, food_normal, food_shrink, food_special, direction
    if not game_over:
        if cheat_mode:
            # Find nearest food
            foods = [f for f in [food_normal, food_shrink, food_special] if f]
            if foods and snake:
                head = snake[0]
                # Find closest food
                target = min(foods, key=lambda f: abs(f[0]-head[0]) + abs(f[1]-head[1]))
                dx = target[0] - head[0]
                dy = target[1] - head[1]
                # Move in x if not aligned, else move in y
                if abs(dx) > 0:
                    step_x = CELL if dx > 0 else -CELL
                    pending_turn = [step_x, 0]
                elif abs(dy) > 0:
                    step_y = CELL if dy > 0 else -CELL
                    pending_turn = [0, step_y]
        move_frame_counter += 1
        if move_frame_counter >= speed_frames():
            move_frame_counter = 0
            move_snake_one_step()
    glutPostRedisplay()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    setupCamera()

    # Apply grid rotation to all game objects
    global grid_rot_horizontal, grid_rot_vertical
    glPushMatrix()
    glRotatef(grid_rot_horizontal, 0, 0, 1)  # left/right (Z axis)
    glRotatef(grid_rot_vertical, 1, 0, 0)    # up/down (X axis)

    draw_grid_and_boundaries()
    draw_snake()
    draw_food()
    glPopMatrix()

    draw_text(10, 770, f"Score: {score}")
    draw_text(10, 740, "Controls: Arrow keys to turn | R to Restart (after game over)")
    draw_text(10, 710, "Foods: Orange=Grow +1 | Red=Release 2 | Yellow Sphere=+5")


    if game_over:
        # Centered, very large and redq 
        draw_text(400, 420, "GAME OVER!", font=GLUT_BITMAP_TIMES_ROMAN_24, color=(1,0,0))
        draw_text(400, 380, "Press R to restart", font=GLUT_BITMAP_TIMES_ROMAN_24, color=(1,0,0))

    glutSwapBuffers()

# ---------- Main ----------
def main():
    reset_game()
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"3D Snake - OpenGL (Template-Compliant)")

    glEnable(GL_DEPTH_TEST)

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    glutMainLoop()

if __name__ == "__main__":
    main()