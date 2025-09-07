# Snakescape3D
A 3D Snake Game developed by Python using OpenGL for BRAC University CSE undergraduate course CSE423: Computer Graphics.



# 3D Snake Game (OpenGL, Python)

A 3D Snake game implemented in Python using PyOpenGL and GLUT.  
Control a snake on a 3D grid, eat food to grow, and avoid hitting yourself or the walls!

## Features

- **3D graphics** with OpenGL
- **Snake grows** when eating orange food
- **Special foods:**
  - **Orange cube:** Grow +1
  - **Red cube:** Shrink (release 2 tail cubes)
  - **Yellow sphere:** Bonus +5 points
- **Food rarity:** Orange is most common, yellow is rare, red is rarest
- **Breathing effect:** Foods gently grow and shrink in size
- **Score tracking**
- **Restart** with `R` after game over

## Controls

- **Arrow keys:** Turn the snake
- **R:** Restart (after game over)

## Requirements

- Python 3.x
- PyOpenGL
- PyOpenGL_accelerate (optional, for speed)

Install dependencies with:

```sh
pip install PyOpenGL PyOpenGL_accelerate
```

## How to Run

1. Make sure you have Python and the required packages installed.
2. Run the game:

```sh
python project.py
```

## Notes

- The game window is 1000x800 pixels.
- The snake and foods are large for better visibility.
- The game ends if the snake hits itself or the wall.

---

Enjoy





### Features added After 6:08 PM
 * Press q to quit the game
 * 'w', 'a', 's', 'd' to rotate the grid (but it has a limit for the up and down direction)
 * press 'c' to randomize the snake body color
 * press 'v' enable/disable to snake body color randomly
 * press 'g' to enable/disable cheat mode [Omi]
 * press 'h' to enable/disable grid color change randomly
 * press '+' and '-' to increase and decrease snake's speed [Omi]