import pygame
import sys
import random
import math
import time

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GRAVITY = 0.8
JUMP_FORCE = -18  # Stronger jump
MOVE_SPEED = 5
SCROLL_SPEED = 1.5
PLATFORM_SPACING = 400
PLATFORM_OVERLAP = 5  # Overlap to prevent gaps

# Colors
SKY_BLUE = (135, 206, 235)
GROUND_COLOR = (139, 69, 19)
MOUNTAIN_COLOR = (128, 128, 128)
CLOUD_COLOR = (255, 255, 255)
HIPPO_COLOR = (180, 180, 180)
HIPPO_DARK = (140, 140, 140)

class Platform:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
    
    def update(self, scroll_speed):
        self.x -= scroll_speed
        self.rect.x = self.x
        
    def draw(self, screen):
        pygame.draw.rect(screen, GROUND_COLOR, self.rect)

class Hippo:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 80
        self.height = 60
        self.vel_y = 0
        self.vel_x = 0
        self.jumping = False
        self.rect = pygame.Rect(x, y, self.width - 20, self.height)  # Smaller hitbox
        self.facing_right = True
        self.walking = False
        self.walk_cycle = 0
        self.walk_speed = 0.2
        self.coyote_time = 0  # Time after leaving platform where we can still jump
        self.jump_buffer = 0  # Time to buffer jump input before landing
        
    def update(self, scroll_speed, platforms):
        # Update coyote time and jump buffer
        if self.jumping:
            self.coyote_time = 0
        else:
            self.coyote_time = max(0, self.coyote_time - 1)
            
        self.jump_buffer = max(0, self.jump_buffer - 1)
        
        # Apply gravity
        self.vel_y += GRAVITY
        
        # Debug prints for movement
        print(f"Before move - x: {self.x:.2f}, vel_x: {self.vel_x:.2f}, scroll: {scroll_speed:.2f}")
        
        # Store original position for collision resolution
        original_x = self.x
        
        # Simple movement: just subtract scroll and add velocity
        self.x = self.x - scroll_speed + self.vel_x
        
        # Update rectangle for collision check
        self.rect.x = self.x
        self.rect.y = self.y
        
        # Platform collision
        was_jumping = self.jumping
        self.jumping = True  # Assume we're in air unless we find a platform below
        
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                # Bottom collision (landing)
                if self.vel_y > 0 and self.rect.bottom > platform.rect.top:
                    self.rect.bottom = platform.rect.top
                    self.y = self.rect.y
                    self.vel_y = 0
                    self.jumping = False
                    self.coyote_time = 5  # ~0.08 seconds of coyote time
                    if self.jump_buffer > 0:  # If we buffered a jump, execute it
                        self.do_jump()
                    print("Ground collision detected")
                
                # Side collision - if we hit a wall, go back to original x
                if (self.vel_x > 0 and self.rect.right > platform.rect.left) or \
                   (self.vel_x < 0 and self.rect.left < platform.rect.right):
                    self.x = original_x - scroll_speed  # Keep the scroll but undo movement
                    self.rect.x = self.x
                    print("Side collision - restored position")
        
        # If we just started falling, give us coyote time
        if not was_jumping and self.jumping:
            self.coyote_time = 5  # ~0.08 seconds of coyote time
        
        print(f"Final x: {self.x:.2f}")
        
        # Update y position
        self.y += self.vel_y
        self.rect.y = self.y
        
        # Update walk cycle
        if self.walking or scroll_speed != 0:
            self.walk_cycle += self.walk_speed
            if self.walk_cycle >= 2 * math.pi:
                self.walk_cycle = 0
        else:
            self.walk_cycle = 0
            
    def jump(self):
        if not self.jumping or self.coyote_time > 0:
            self.do_jump()
        else:
            self.jump_buffer = 5  # Buffer the jump for ~0.08 seconds
            
    def do_jump(self):
        self.vel_y = JUMP_FORCE
        self.jumping = True
        self.coyote_time = 0
        self.jump_buffer = 0
        
    def move(self, dx):
        print(f"Move called with dx: {dx}")
        if dx != 0:
            self.walking = True
            self.facing_right = dx > 0
            # Only update velocity if we're moving right or if we're not at screen edge
            if dx > 0 or self.x > 0:
                self.vel_x = dx
                print(f"Updated vel_x to: {self.vel_x}")
        else:
            self.walking = False
            self.vel_x = 0

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Hippo Runner")
        self.clock = pygame.time.Clock()
        self.reset_game()
        
    def reset_game(self):
        self.hippo = Hippo(SCREEN_WIDTH // 4, SCREEN_HEIGHT - 200)
        self.scroll = 0
        self.clouds = []
        self.mountains = []
        self.platforms = []
        self.paused = False
        self.game_over = False
        self.start_time = time.time()
        self.score = 0
        self.generate_initial_content()
        
    def generate_initial_content(self):
        # Generate initial mountains and clouds
        for i in range(5):
            x = i * 300
            height = random.randint(100, 200)
            self.mountains.append({'x': x, 'height': height})
            
        for i in range(8):
            x = random.randint(0, SCREEN_WIDTH * 2)
            y = random.randint(50, 200)
            width = random.randint(50, 100)
            self.clouds.append({'x': x, 'y': y, 'width': width})
            
        # Generate initial ground platforms
        self.generate_new_platform(0)
            
    def generate_new_platform(self, start_x):
        # Base height follows a sine wave with some randomness
        base_height = 50 + math.sin(start_x * 0.01) * 20
        platform_type = random.random()
        
        if platform_type < 0.6:  # 60% chance for varied ground
            width = PLATFORM_SPACING + PLATFORM_OVERLAP
            height = base_height + random.randint(-10, 10)
            y = SCREEN_HEIGHT - height
            self.platforms.append(Platform(start_x - PLATFORM_OVERLAP, y, width, height))
            
        elif platform_type < 0.8:  # 20% chance for elevated platform with varied height
            # Main platform
            width = random.randint(80, 150)
            height = base_height + random.randint(60, 120)
            y = SCREEN_HEIGHT - height - random.randint(30, 70)
            self.platforms.append(Platform(start_x - PLATFORM_OVERLAP, y, width + PLATFORM_OVERLAP, height))
            
            # Ground after gap (ensure no gaps)
            ground_width = PLATFORM_SPACING - width + PLATFORM_OVERLAP
            ground_height = base_height + random.randint(-10, 10)
            self.platforms.append(Platform(
                start_x + width - PLATFORM_OVERLAP,
                SCREEN_HEIGHT - ground_height,
                ground_width + PLATFORM_OVERLAP,
                ground_height
            ))
            
        else:  # 20% chance for gap with varied width and ground height
            gap_width = random.randint(80, 120)
            ground_width = PLATFORM_SPACING - gap_width + PLATFORM_OVERLAP
            ground_height = base_height + random.randint(-10, 10)
            self.platforms.append(Platform(
                start_x + gap_width - PLATFORM_OVERLAP,
                SCREEN_HEIGHT - ground_height,
                ground_width + PLATFORM_OVERLAP,
                ground_height
            ))
            
    def update_world(self, scroll_speed):
        # Update mountains and clouds
        for mountain in self.mountains:
            mountain['x'] -= scroll_speed
        self.mountains = [m for m in self.mountains if m['x'] > -200]
        if self.mountains[-1]['x'] < SCREEN_WIDTH:
            new_x = self.mountains[-1]['x'] + 300
            self.mountains.append({
                'x': new_x,
                'height': random.randint(100, 200)
            })
            
        for cloud in self.clouds:
            cloud['x'] -= scroll_speed * 0.5
        self.clouds = [c for c in self.clouds if c['x'] > -100]
        if len(self.clouds) < 8:
            self.clouds.append({
                'x': SCREEN_WIDTH + 100,
                'y': random.randint(50, 200),
                'width': random.randint(50, 100)
            })
            
        # Update platforms
        for platform in self.platforms:
            platform.update(scroll_speed)
            
        # Remove off-screen platforms and generate new ones
        self.platforms = [p for p in self.platforms if p.x > -p.width]
        if not self.platforms:
            self.generate_new_platform(SCREEN_WIDTH)
        else:
            last_x = max(p.x + p.width for p in self.platforms)
            if last_x < SCREEN_WIDTH:
                self.generate_new_platform(last_x)
                
    def check_death(self):
        # Check if hippo is off screen to the left or fell off the bottom
        return (self.hippo.rect.right < 0 or 
                self.hippo.y > SCREEN_HEIGHT)
            
    def draw_background(self):
        # Draw sky
        self.screen.fill(SKY_BLUE)
        
        # Draw mountains
        for mountain in self.mountains:
            pygame.draw.polygon(self.screen, MOUNTAIN_COLOR, [
                (mountain['x'], SCREEN_HEIGHT),
                (mountain['x'] + 100, SCREEN_HEIGHT - mountain['height']),
                (mountain['x'] + 200, SCREEN_HEIGHT)
            ])
            
        # Draw clouds
        for cloud in self.clouds:
            pygame.draw.ellipse(self.screen, CLOUD_COLOR, 
                              (cloud['x'], cloud['y'], cloud['width'], 30))
            
        # Draw platforms
        for platform in self.platforms:
            platform.draw(self.screen)

    def draw_score(self):
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {int(self.score)}", True, (0, 0, 0))
        score_rect = score_text.get_rect(topright=(SCREEN_WIDTH - 20, 20))
        self.screen.blit(score_text, score_rect)
        
    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 74)
        text = font.render("GAME OVER", True, (255, 0, 0))
        text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
        self.screen.blit(text, text_rect)
        
        score_font = pygame.font.Font(None, 48)
        score_text = score_font.render(f"Final Score: {int(self.score)}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 50))
        self.screen.blit(score_text, score_rect)
        
        font_small = pygame.font.Font(None, 36)
        restart_text = font_small.render("Press SPACE to restart", True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 100))
        self.screen.blit(restart_text, restart_rect)

    def draw_hippo(self):
        h = self.hippo
        
        # Calculate leg positions based on walk cycle
        leg_offset = math.sin(h.walk_cycle) * 10
        back_leg_y = h.y + h.height - 10 + (leg_offset if h.walking or self.scroll > 0 else 0)
        front_leg_y = h.y + h.height - 10 + (-leg_offset if h.walking or self.scroll > 0 else 0)
        
        # Draw back legs
        pygame.draw.ellipse(self.screen, HIPPO_DARK, 
                          (h.x + 10, back_leg_y, 15, 20))
        pygame.draw.ellipse(self.screen, HIPPO_DARK, 
                          (h.x + 30, back_leg_y, 15, 20))
        
        # Draw body
        pygame.draw.ellipse(self.screen, HIPPO_COLOR, 
                          (h.x, h.y, h.width - 20, h.height))
        
        # Draw head
        head_x = h.x + (h.width - 40 if h.facing_right else -20)
        pygame.draw.ellipse(self.screen, HIPPO_COLOR, 
                          (head_x, h.y - 10, 60, 50))
        
        # Draw front legs
        pygame.draw.ellipse(self.screen, HIPPO_DARK, 
                          (h.x + h.width - 65, front_leg_y, 15, 20))
        pygame.draw.ellipse(self.screen, HIPPO_DARK, 
                          (h.x + h.width - 45, front_leg_y, 15, 20))
        
        # Draw ears
        ear_x = head_x + (40 if h.facing_right else 5)
        pygame.draw.ellipse(self.screen, HIPPO_DARK, 
                          (ear_x, h.y - 5, 15, 20))
        
        # Draw eyes
        eye_x = head_x + (35 if h.facing_right else 15)
        pygame.draw.circle(self.screen, (0, 0, 0), 
                         (eye_x, h.y + 15), 4)
        
        # Draw nose
        nose_x = head_x + (50 if h.facing_right else 5)
        pygame.draw.ellipse(self.screen, HIPPO_DARK, 
                          (nose_x, h.y + 20, 8, 12))
        
        # Draw tail
        tail_x = h.x + (0 if h.facing_right else h.width - 20)
        pygame.draw.line(self.screen, HIPPO_DARK, 
                        (tail_x, h.y + h.height//2),
                        (tail_x + (-20 if h.facing_right else 20), 
                         h.y + h.height//2 - 10), 3)
        
    def draw_pause_screen(self):
        # Create a semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))
        
        # Create font and render pause text
        font = pygame.font.Font(None, 74)
        text = font.render("PAUSED", True, (255, 255, 255))
        text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
        self.screen.blit(text, text_rect)
        
        # Add "Press ENTER to resume" text
        font_small = pygame.font.Font(None, 36)
        resume_text = font_small.render("Press ENTER to resume", True, (255, 255, 255))
        resume_rect = resume_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 50))
        self.screen.blit(resume_text, resume_rect)

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if self.game_over:
                            self.reset_game()
                        elif not self.paused:
                            self.hippo.jump()
                    if event.key == pygame.K_RETURN and not self.game_over:
                        self.paused = not self.paused
            
            if not self.paused and not self.game_over:
                # Update score
                self.score = time.time() - self.start_time
                
                # Keep constant scroll speed
                self.scroll = SCROLL_SPEED
                
                # Handle movement
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    self.hippo.move(-MOVE_SPEED)
                elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    self.hippo.move(MOVE_SPEED)
                else:
                    self.hippo.move(0)
                    
                # Update world and hippo
                self.update_world(self.scroll)
                self.hippo.update(self.scroll, self.platforms)
                
                # Check for death
                if self.check_death():
                    self.game_over = True
            
            # Draw
            self.draw_background()
            self.draw_hippo()
            self.draw_score()
            
            if self.paused:
                self.draw_pause_screen()
            elif self.game_over:
                self.draw_game_over()
            
            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run() 