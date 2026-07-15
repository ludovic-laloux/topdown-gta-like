import pygame, sys

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

class Car(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.original_image = pygame.image.load("Audi.png")
        self.image = self.original_image
        self.rect = self.image.get_rect(center = (726, 52))
        self.angle = -90
        self.rotation_speed = 2.2
        self.direction = 0
        self.forward = pygame.math.Vector2(1, 0)
        self.active = False

    def set_rotation(self):
        if self.direction == 1:
            self.angle -= self.rotation_speed
        if self.direction == -1:
            self.angle += self.rotation_speed

        self.image = pygame.transform.rotozoom(self.original_image, self.angle, 0.25)
        self.rect = self.image.get_rect(center = self.rect.center)

    def get_rotation(self):
        if self.direction == 1:
            self.forward.rotate_ip(self.rotation_speed)
        if self.direction == -1:
            self.forward.rotate_ip(-self.rotation_speed)

    def accelerate(self):
        if self.active:
            self.rect.center += self.forward * 4

    def update(self):
        self.set_rotation()
        self.get_rotation()
        self.accelerate()


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.mouse.set_visible(False)
clock = pygame.time.Clock()
bg_track = pygame.image.load("Track.png")
bg_track = pygame.transform.rotozoom(bg_track, 0, 1.2)
bg_track_rect = bg_track.get_rect(center = ((SCREEN_WIDTH //2) + 25, (SCREEN_HEIGHT // 2) + 16))

car = pygame.sprite.GroupSingle(Car())

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT: car.sprite.direction += 1
            if event.key == pygame.K_LEFT: car.sprite.direction -= 1
            if event.key == pygame.K_SPACE: car.sprite.active = True

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_RIGHT: car.sprite.direction -= 1
            if event.key == pygame.K_LEFT: car.sprite.direction += 1
            if event.key == pygame.K_SPACE: car.sprite.active = False


    screen.blit(bg_track, bg_track_rect)
    car.update()
    car.draw(screen)
    pygame.display.update()
    clock.tick(120)