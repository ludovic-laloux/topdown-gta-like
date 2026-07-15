import pygame, sys

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
CAR_START_POS = (3275, 500)

class Car(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.original_image = pygame.image.load("Audi.png")
        self.image = self.original_image
        self.rect = self.image.get_rect(center = pos)
        self.angle = -90
        self.rotation_speed = 1.2
        self.direction = 0
        self.forward = pygame.math.Vector2(1, 0)
        self.active = False

    def set_rotation(self):
        if self.direction == 1:
            self.angle -= self.rotation_speed
        if self.direction == -1:
            self.angle += self.rotation_speed

        self.image = pygame.transform.rotozoom(self.original_image, self.angle, 0.7)
        self.rect = self.image.get_rect(center = self.rect.center)

    def get_rotation(self):
        if self.direction == 1:
            self.forward.rotate_ip(self.rotation_speed)
        if self.direction == -1:
            self.forward.rotate_ip(-self.rotation_speed)

    def accelerate(self):
        if self.active:
            self.rect.center += self.forward * 6

    def update(self):
        self.set_rotation()
        self.get_rotation()
        self.accelerate()

class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        
        # camera offset
        self.offset= pygame.math.Vector2(800, 100)
        self.half_w = self.display_surface.get_size()[0] // 2
        self.half_h = self.display_surface.get_size()[1] // 2

        # Track
        self.Track_surf = pygame.image.load("track.png").convert_alpha()
        self.Track_surf = pygame.transform.smoothscale(self.Track_surf, (6000, 4000))
        self.Track_rect = self.Track_surf.get_rect(topleft = (0, 0))


    def center_target_camera(self, target):
        self.offset.x = target.rect.centerx - self.half_w
        self.offset.y = target.rect.centery - self.half_h

    def custom_draw(self, player):
        # clear the frame first
        self.display_surface.fill((0, 0, 0))

        self.center_target_camera(player)
        
        # Track
        Track_offset = self.Track_rect.topleft - self.offset
        self.display_surface.blit(self.Track_surf, Track_offset)

        # active elements
        for sprite in sorted(self.sprites(), key = lambda sprite: sprite.rect.centery):
            offset_position = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image,offset_position)


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.mouse.set_visible(False)
clock = pygame.time.Clock()
bg_Track = pygame.image.load("Track.png")
bg_Track = pygame.transform.rotozoom(bg_Track, 0, 1.2)
bg_Track_rect = bg_Track.get_rect(center = ((SCREEN_WIDTH //2) + 25, (SCREEN_HEIGHT // 2) + 16))

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