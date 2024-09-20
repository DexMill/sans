import pygame
import sys
import random
import math  # Import the math module for mathematical functions

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Undertale-Inspired Boss Fight")

# Clock for controlling frame rate
clock = pygame.time.Clock()
FPS = 60

# Load assets
player_image = pygame.image.load("assets/player.png").convert_alpha()
player_image = pygame.transform.scale(player_image, (player_image.get_width() // 4, player_image.get_height() // 4))  # Make the player smaller
player_rect = player_image.get_rect(center=(WIDTH // 2, HEIGHT - 50))
player_speed = 10

attack_image = pygame.image.load("assets/attack.png").convert_alpha()
attack_image = pygame.transform.scale(attack_image, (attack_image.get_width() // 2, attack_image.get_height() // 2))

player_attack_image = pygame.image.load("assets/player-attack.png").convert_alpha()
player_attack_image = pygame.transform.scale(player_attack_image, (player_attack_image.get_width() // 2, player_attack_image.get_height() // 2))

# Load wave bone image (assuming you have a separate image for wave bones)
wave_bone_image = pygame.image.load("assets/wave_bone.png").convert_alpha()
wave_bone_image = pygame.transform.scale(wave_bone_image, (wave_bone_image.get_width() // 2, wave_bone_image.get_height() // 2))

# Load beam assets
beam_top_image = pygame.image.load("assets/beam_top.png").convert_alpha()
beam_top_image = pygame.transform.scale(beam_top_image, (WIDTH, beam_top_image.get_height()))

beam_middle_image = pygame.image.load("assets/beam_middle.png").convert_alpha()
beam_middle_image = pygame.transform.scale(beam_middle_image, (WIDTH, beam_middle_image.get_height()))

beam_bottom_image = pygame.image.load("assets/beam_bottom.png").convert_alpha()
beam_bottom_image = pygame.transform.scale(beam_bottom_image, (WIDTH, beam_bottom_image.get_height()))

# Group to manage beam attacks
beams = pygame.sprite.Group()

# Group to manage wave attacks
waves = pygame.sprite.Group()

# Group to manage regular attacks
attacks = pygame.sprite.Group()

# Enemy class
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, health, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.health = health

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.kill()

# Beam Attack class with opacity and lifetime handling
class BeamAttack(pygame.sprite.Sprite):
    def __init__(self, y_position, image, current_time, display_delay=1000, lifetime=3000):
        super().__init__()
        # Make a copy of the image to modify its alpha
        self.original_image = image.copy()
        self.image = self.original_image.copy()
        self.image.set_alpha(128)  # Start with 50% opacity (128 out of 255)
        self.rect = self.image.get_rect(topleft=(0, y_position))
        self.spawn_time = current_time
        self.display_delay = display_delay  # Time before beam becomes fully opaque (in ms)
        self.lifetime = lifetime  # How long the beam stays on screen (in ms)
        self.active = False  # Flag to indicate if beam can deal damage

    def update(self, current_time):
        elapsed = current_time - self.spawn_time

        if not self.active:
            if elapsed >= self.display_delay:
                self.image.set_alpha(255)
                self.active = True  # Beam is now active and can deal damage
            else:
                # Flashing effect: alternate visibility every 250ms
                if (elapsed // 250) % 2 == 0:
                    self.image.set_alpha(128)  # Semi-transparent
                else:
                    self.image.set_alpha(200)  # Slightly less transparent
        else:
            # Pulsating effect once active
            pulse = 128 + 127 * math.sin(elapsed / 200)  # Pulsate between 1 and 255
            pulse = max(0, min(255, int(pulse)))  # Clamp between 0 and 255
            self.image.set_alpha(pulse)

        # Remove the beam after its lifetime
        if elapsed >= self.lifetime:
            self.kill()

# Attack class
class Attack(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, speed_x, speed_y, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction
        self.speed_x = speed_x
        self.speed_y = speed_y

    def update(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        # Remove attack if it moves off-screen
        if self.rect.right < 0 or self.rect.left > WIDTH or self.rect.top > HEIGHT or self.rect.bottom < 0:
            self.kill()

# Sprite groups
attacks = pygame.sprite.Group()
enemies = pygame.sprite.Group()

# Create an enemy instance
enemy_image = pygame.image.load("assets/enemy.png").convert_alpha()
enemy_image = pygame.transform.scale(enemy_image, (enemy_image.get_width() // 2, enemy_image.get_height() // 2))
enemy = Enemy(WIDTH // 2, 50, 10, enemy_image)
enemies.add(enemy)

# Enemy attack timer
attack_event = pygame.USEREVENT + 1
pygame.time.set_timer(attack_event, 500)  # Enemy attacks every 0.5 seconds

# Player attack cooldown
can_attack = True
attack_cooldown = 1  # 1 second
last_attack_time = 0

# Attack counter
attack_count = 0
ATTACK_LIMIT = 10  # Number of attacks before a wave is summoned

# Wave parameters
WAVE_BONE_COUNT = WIDTH // (wave_bone_image.get_width())  # Adjust to cover the entire width
WAVE_GAP_WIDTH = 150  # Increased gap width for better dodging
WAVE_SPEED_Y = -5  # Increased speed for added difficulty

def spawn_wave(current_time):
    global waves, beams
    bone_width = wave_bone_image.get_width()
    gap_size = WAVE_GAP_WIDTH
    gap_position = random.randint(0, WIDTH - gap_size)

    for i in range(WAVE_BONE_COUNT):
        x = i * bone_width + bone_width // 2
        y = HEIGHT  # Start from the bottom

        # Check if the bone is within the gap range
        if gap_position <= x <= gap_position + gap_size:
            continue  # Skip spawning bones in the gap

        # Create enemy wave attacks moving upwards
        wave_bone = Attack(x, y, 'down', 0, WAVE_SPEED_Y, wave_bone_image)
        attacks.add(wave_bone)
        waves.add(wave_bone)

    # Randomly decide to spawn a beam attack
    if random.random() < 0.3:  # 30% chance to spawn a beam
        beam_type = random.choice(['top', 'middle', 'bottom'])
        if beam_type == 'top':
            y_position = 50
            beam_image = beam_top_image
        elif beam_type == 'middle':
            y_position = HEIGHT // 2 - beam_middle_image.get_height() // 2
            beam_image = beam_middle_image
        else:
            y_position = HEIGHT - 100
            beam_image = beam_bottom_image

        # Optional: Check if the beam overlaps with the player
        beam_rect = pygame.Rect(0, y_position, beam_image.get_width(), beam_image.get_height())
        if beam_rect.colliderect(player_rect.inflate(-100, -100)):  # Inflate to create a buffer zone
            print("Beam spawn overlapped with player. Skipping beam spawn.")
            return  # Skip spawning this beam

        beam = BeamAttack(y_position, beam_image, current_time)
        beams.add(beam)

        # Remove a few existing attacks to balance
        for _ in range(3):
            if attacks:
                attack = attacks.sprites()[0]
                attack.kill()

def main():
    global can_attack, last_attack_time, attack_count, player_health

    # Add before the main loop
    player_health = 5
    enemy_health = 10
    score = 0

    def draw_health():
        font = pygame.font.SysFont(None, 36)
        health_text = font.render(f'Health: {player_health}', True, (255, 255, 255))
        screen.blit(health_text, (10, 10))

    def draw_score():
        font = pygame.font.SysFont(None, 36)
        score_text = font.render(f'Score: {score}', True, (255, 255, 255))
        screen.blit(score_text, (10, 50))

    # Load sounds
    attack_sound = pygame.mixer.Sound("assets/attack.wav")
    hit_sound = pygame.mixer.Sound("assets/hit.wav")
    pygame.mixer.music.load("assets/background.mp3")
    pygame.mixer.music.play(-1)  # Loop indefinitely

    while True:
        keys = pygame.key.get_pressed()
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == attack_event:
                if attack_count < ATTACK_LIMIT:
                    # Spawn regular enemy attacks
                    direction = random.choice(['left_down', 'right_down'])
                    speed_x = random.uniform(-3, 3)  # Varying left/right speed
                    speed_y = random.uniform(2, 5)   # Varying downward speed
                    x = WIDTH // 2  # Spawn in the middle
                    y = 0  # Spawn at the top
                    attack = Attack(x, y, direction, speed_x, speed_y, attack_image)
                    attacks.add(attack)
                    attack_count += 1
                else:
                    # Spawn wave attack and possibly beam
                    spawn_wave(current_time)
                    attack_count = 0  # Reset the attack counter

        # Player movement
        if keys[pygame.K_LEFT] and player_rect.left > 0:
            player_rect.x -= player_speed
        if keys[pygame.K_RIGHT] and player_rect.right < WIDTH:
            player_rect.x += player_speed
        if keys[pygame.K_UP] and player_rect.top > 0:
            player_rect.y -= player_speed
        if keys[pygame.K_DOWN] and player_rect.bottom < HEIGHT:
            player_rect.y += player_speed

        # Player attack
        if can_attack and keys[pygame.K_SPACE]:
            player_attack = Attack(player_rect.centerx, player_rect.top, 'up', 0, -7, player_attack_image)
            attacks.add(player_attack)
            can_attack = False
            last_attack_time = current_time
            attack_sound.play()

        # Reset attack cooldown
        if not can_attack and current_time - last_attack_time > attack_cooldown * 1000:  # Convert cooldown to milliseconds
            can_attack = True

        # Update attacks and beams
        attacks.update()
        beams.update(current_time)  # Pass current_time to update method

        # Check collisions for regular attacks
        for attack in attacks:
            if attack.direction != 'up' and player_rect.colliderect(attack.rect):
                print("Player hit!")
                player_health -= 1
                attack.kill()
                hit_sound.play()  # Play hit sound when player is hit
                if player_health <= 0:
                    pygame.quit()
                    sys.exit()
            elif attack.direction == 'up':
                enemy_hit = pygame.sprite.spritecollideany(attack, enemies)
                if enemy_hit:
                    enemy_hit.take_damage(1)
                    attack.kill()
                    score += 10
                    if enemy_hit.health <= 0:
                        score += 50  # Bonus for defeating enemy

        # Check collisions for beam attacks **only if they are active**
        for beam in beams:
            if beam.active and player_rect.colliderect(beam.rect):
                print("Player hit by beam!")
                player_health -= 2  # Beam might cause more damage
                beam.kill()
                hit_sound.play()
                if player_health <= 0:
                    pygame.quit()
                    sys.exit()

        # Render
        screen.fill((0, 0, 0))  # Black background
        screen.blit(player_image, player_rect)
        attacks.draw(screen)
        beams.draw(screen)  # Draw beams
        enemies.draw(screen)
        draw_health()
        draw_score()
        pygame.display.flip()

        clock.tick(FPS)

if __name__ == "__main__":
    main()
