import pygame, sys

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
CAR_START_POS = (3100, 3900)
HESBAYE_GREEN = (120, 150, 80)



# # Fresh spring crop field
# (130, 170, 90)

# # Grass pasture
# (100, 140, 70)

# # Darker realistic grass
# (80, 120, 60)

# # Dry summer field
# (160, 170, 90)

# # Very natural muted green
# (110, 145, 85)

# (0, 255, 0)     # pure bright green
# (0, 100, 0)     # dark green
# (120, 150, 80)  # natural grass


class Car(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        raw = pygame.image.load("Audi.png").convert_alpha()
        # scale once, here — not every frame
        w, h = raw.get_size()
        self.original_image = pygame.transform.smoothscale(raw, (int(w * 0.7), int(h * 0.7)))
        self.image = self.original_image
        self.rect = self.image.get_rect(center = pos)
        self.angle = 0
        self.rotation_speed = 1.2
        self.direction = 0
        self.forward = pygame.math.Vector2(0, -1)
        self.active = False
        self.world_rect = pygame.Rect(0, 0, 6000, 4000)

    def set_rotation(self):
        if self.direction == 1:
            self.angle -= self.rotation_speed
        if self.direction == -1:
            self.angle += self.rotation_speed

        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center = self.rect.center)

    def get_rotation(self):
        if self.direction == 1:
            self.forward.rotate_ip(self.rotation_speed)
        if self.direction == -1:
            self.forward.rotate_ip(-self.rotation_speed)

    def accelerate(self):
        if self.active:
            new_rect = self.rect.copy()
            new_rect.center += self.forward * 6

            if self.world_rect.contains(new_rect):
                self.rect = new_rect

    def update(self):
        self.set_rotation()
        self.get_rotation()
        self.accelerate()

class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.world = pygame.Surface((6000, 4000))
        self.world.fill(HESBAYE_GREEN)
        self.world_rect = self.world.get_rect(topleft=(0,0))

        # test fields
        pygame.draw.rect(self.world, (130,170,90), (500,300,800,600))
        pygame.draw.rect(self.world, (100,140,70), (2000,1000,1000,700))

        # test roads
        pygame.draw.rect(self.world, (80,80,70), (3000,0,200,4000))
        
        # camera offset
        self.offset= pygame.math.Vector2(800, 100)
        self.half_w = self.display_surface.get_size()[0] // 2
        self.half_h = self.display_surface.get_size()[1] // 2

    def center_target_camera(self, target):
        self.offset.x = target.rect.centerx - self.half_w
        self.offset.y = target.rect.centery - self.half_h

        self.offset.x = max(0, min(self.offset.x, self.world_rect.width - self.display_surface.get_width()))

        self.offset.y = max(0, min(self.offset.y, self.world_rect.height - self.display_surface.get_height()))

    def custom_draw(self, player):
        # update camera first
        self.center_target_camera(player)

        # draw world
        world_offset = self.world_rect.topleft - self.offset
        self.display_surface.blit(self.world, world_offset)

        # draw sprites
        for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.centery):
            offset_position = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_position)


pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.NOFRAME)
pygame.mouse.set_visible(False)
clock = pygame.time.Clock()

# setup
camera_group = CameraGroup()
car = Car(CAR_START_POS)
camera_group.add(car)


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT: car.direction += 1
            if event.key == pygame.K_LEFT: car.direction -= 1
            if event.key == pygame.K_SPACE: car.active = True

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_RIGHT: car.direction -= 1
            if event.key == pygame.K_LEFT: car.direction += 1
            if event.key == pygame.K_SPACE: car.active = False


    camera_group.custom_draw(car)
    camera_group.update()

    pygame.display.update()
    clock.tick(120)