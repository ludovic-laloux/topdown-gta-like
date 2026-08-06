import pygame, sys

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
CAR_START_POS = (3320, 3900)
HESBAYE_GREEN = (120, 150, 80)

class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()

        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (30, 30, 255), (15, 15), 15)
        self.rect = self.image.get_rect(center=pos)

        self.direction = pygame.Vector2()
        self.speed = 3

        self.in_car = False

    def input(self):
        keys = pygame.key.get_pressed()

        self.direction.x = 0
        self.direction.y = 0


        # left: AZERTY Q / QWERTY A
        if keys[pygame.K_q] or keys[pygame.K_a]:
            self.direction.x = -1

        # right: D on both layouts
        if keys[pygame.K_d]:
            self.direction.x = 1

        # up: AZERTY Z / QWERTY W
        if keys[pygame.K_z] or keys[pygame.K_w]:
            self.direction.y = -1

        # down: S on both layouts
        if keys[pygame.K_s]:
            self.direction.y = 1

    def move(self):
        if self.direction.length() > 0:
            self.direction = self.direction.normalize()

        self.rect.center += self.direction * self.speed

    def update(self, car=None):

        if self.in_car:
            self.rect.center = car.rect.center

        else:
            self.input()
            self.move()

class Car(pygame.sprite.Sprite):
    def __init__(self, pos, obstacles, roads):
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
        
        self.speed = 0
        self.max_speed = 8
        self.acceleration = 0.02
        self.friction = 0.02
        self.road_speed = 8
        self.offroad_speed = 4

        self.hitbox = self.rect.inflate(-160, -135)

        self.active = False
        self.world_rect = pygame.Rect(0, 0, 6000, 4000)

        self.obstacles = obstacles
        self.roads = roads

        self.driver_offset = pygame.Vector2(0, 0)

    def set_rotation(self):
        if self.direction == 1:
            self.angle -= self.rotation_speed
        if self.direction == -1:
            self.angle += self.rotation_speed

        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center = self.hitbox.center)

    def get_rotation(self):
        if self.direction == 1:
            self.forward.rotate_ip(self.rotation_speed)
        if self.direction == -1:
            self.forward.rotate_ip(-self.rotation_speed)

    def accelerate(self):
        if self.check_road():
            max_speed = self.road_speed
        else:
            max_speed = self.offroad_speed

        if self.active:
            self.speed += self.acceleration
            self.speed = min(self.speed, max_speed)
        else:
            self.speed -= self.friction
            self.speed = max(self.speed, 0)

        new_hitbox = self.hitbox.copy()
        new_hitbox.center += self.forward * self.speed

        for obstacle in self.obstacles:
            if new_hitbox.colliderect(obstacle):
                return

        if self.world_rect.contains(new_hitbox):
            self.hitbox = new_hitbox
            self.rect.center = self.hitbox.center

    def check_road(self):
        for road in self.roads:
            if self.hitbox.colliderect(road):
                return True
        return False

    def update(self):
        self.set_rotation()
        self.get_rotation()
        self.accelerate()


class CameraGroup(pygame.sprite.Group):
    """
    A sprite group that handles drawing the large world and moving the camera
    so it follows a target object.
    """

    def __init__(self):
        """
        Creates the camera group, the large world surface, and initializes
        the camera position and screen dimensions.
        """
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.world = pygame.Surface((6000, 4000))
        self.world.fill(HESBAYE_GREEN)
        self.world_rect = self.world.get_rect(topleft=(0,0))
        
        self.obstacles = [
            pygame.Rect(2500, 400, 500, 500),
            pygame.Rect(2500, 2700, 500, 500),
            pygame.Rect(3500, 500, 100, 200),
            pygame.Rect(4000, 500, 100, 200),
            pygame.Rect(4500, 500, 100, 200),
            pygame.Rect(5000, 500, 100, 200)
        ]

        self.roads = [
            pygame.Rect(3000, 0, 400, 4000),
            pygame.Rect(3400, 100, 2400, 300),
            pygame.Rect(5500, 100, 300, 3400),
            pygame.Rect(3400, 3200, 2400, 300)
        ]

        # test fields
        pygame.draw.rect(self.world, (130, 170, 90), (500,300,800,600))
        pygame.draw.rect(self.world, (100, 140, 70), (2000,1000,1000,700))
        pygame.draw.rect(self.world, (80, 120, 60), (3200,0,2800,800))

        # test roads
        pygame.draw.rect(self.world, (80,80,70), (3000,0,400,4000))
        pygame.draw.rect(self.world, (100,85,65), (3400,100,2400,300))
        pygame.draw.rect(self.world, (100,85,65), (5500,100,300,3400))
        pygame.draw.rect(self.world, (100,85,65), (3400,3200,2400,300))

        # test houses
        pygame.draw.rect(self.world, (156,36,11),(2500,400,500,500))
        pygame.draw.rect(self.world, (115,70,70),(2500,2700,500,500))

        # test bales of straw
        pygame.draw.rect(self.world, (219,192,0),(3500,500,100,200))
        pygame.draw.rect(self.world, (219,192,0),(4000,500,100,200))
        pygame.draw.rect(self.world, (219,192,0),(4500,500,100,200))
        pygame.draw.rect(self.world, (219,192,0),(5000,500,100,200))

        # camera offset
        self.offset= pygame.math.Vector2(0, 0)
        self.half_w = self.display_surface.get_size()[0] // 2
        self.half_h = self.display_surface.get_size()[1] // 2

    def center_target_camera(self, target):
        """
        Moves the camera offset so that the target object stays centered
        on the screen while preventing the camera from leaving the world boundaries.
        """
        self.offset.x = target.rect.centerx - self.half_w
        self.offset.y = target.rect.centery - self.half_h

        self.offset.x = max(
            0, min(self.offset.x, self.world_rect.width - self.display_surface.get_width())
            )

        self.offset.y = max(
            0, min(self.offset.y, self.world_rect.height - self.display_surface.get_height())
            )

    def custom_draw(self, player):
        """
        Draws the world and all sprites with the camera offset applied.
        The camera position is updated first so it follows the player.
        """    
        # update camera first
        self.center_target_camera(player)

        # draw world
        world_offset = self.world_rect.topleft - self.offset
        self.display_surface.blit(self.world, world_offset)

        # draw sprites
        for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.centery):
            offset_position = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_position)

        pygame.draw.rect(
            self.display_surface,
            (255, 0, 0),
            car.hitbox.move(-self.offset.x, -self.offset.y),
            2
        )


pygame.init()
screen = pygame.display.set_mode((1280, 720), pygame.NOFRAME)
pygame.mouse.set_visible(False)
clock = pygame.time.Clock()

# setup
camera_group = CameraGroup()

car = Car(CAR_START_POS, camera_group.obstacles, camera_group.roads)
player = Player((CAR_START_POS[0] + 80, CAR_START_POS[1]))

camera_group.add(car)
camera_group.add(player)

camera_target = player


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

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:

                # ENTER CAR
                if not player.in_car:
                    if player.rect.colliderect(car.rect.inflate(50, 50)):
                        player.in_car = True
                        player.kill()
                        camera_target = car

                # EXIT CAR
                else:
                    player.in_car = False
                    player.rect.center = (car.rect.centerx + 60, car.rect.centery)
                    camera_group.add(player)
                    car.active = False
                    camera_target = player

    # camera_group.update()
    car.update()
    player.update(car)

    camera_group.custom_draw(camera_target)

    pygame.display.update()
    clock.tick(120)