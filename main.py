import pygame, sys, random

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
CAR_START_POS = (3320, 3900)
BG_GRASS_COLOR = (120, 150, 80)
FIELD_COLOR = (100,140,20)
ROAD_COLOR = (80,80,70)
OBSTACLE_COLOR = (156, 36, 11)

class World:
    def __init__(self):
        self.surface = pygame.Surface((6000, 4000))
        self.surface.fill(BG_GRASS_COLOR)

        self.rect = self.surface.get_rect(topleft=(0, 0))


        self.fields = []

        for i in range(30):
            width = random.randint(300, 1000)
            height = random.randint(300, 800)

            x = random.randint(0, self.rect.width - width)
            y = random.randint(0, self.rect.height - height)

            self.fields.append(pygame.Rect(x, y, width, height))

        self.hay_bales = [
            pygame.Rect(3500, 500, 100, 200),
            pygame.Rect(4000, 500, 100, 200),
            pygame.Rect(4500, 500, 100, 200),
            pygame.Rect(5000, 500, 100, 200)
        ]

        self.houses = [
            pygame.Rect(2500, 400, 500, 500),
            pygame.Rect(2500, 2700, 500, 500)
        ]

        self.obstacles = self.houses + self.hay_bales

        self.roads = [
            pygame.Rect(3000, 0, 400, 4000),
            pygame.Rect(3400, 100, 2400, 300),
            pygame.Rect(5500, 100, 300, 3400),
            pygame.Rect(3400, 3200, 2400, 300)
        ]

        self.draw_map()

    def draw_map(self):
        for field in self.fields:
            pygame.draw.rect(self.surface, FIELD_COLOR, field)

        for obstacle in self.obstacles:
            pygame.draw.rect(self.surface, OBSTACLE_COLOR, obstacle)

        for road in self.roads:
            pygame.draw.rect(self.surface, ROAD_COLOR, road)


class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()

        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (30, 30, 255), (15, 15), 15)
        self.rect = self.image.get_rect(center=pos)

        self.direction = pygame.Vector2()
        self.speed = 3

        self.in_car = False
        self.current_car = None

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

    def update(self):

        if self.in_car:
            self.rect.center = self.current_car.rect.center

        else:
            self.input()
            self.move()

class Car(pygame.sprite.Sprite):
    def __init__(self, pos, world):
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
        self.acceleration = 0.02
        self.friction = 0.02
        self.road_speed = 8
        self.offroad_speed = 4

        self.hitbox = self.rect.inflate(-160, -135)

        self.active = False

        self.world = world

    def set_rotation(self):
        if self.speed > 0:
            if self.direction == 1:
                self.angle -= self.rotation_speed
            if self.direction == -1:
                self.angle += self.rotation_speed

        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.hitbox.center)

    def get_rotation(self):
        self.forward = pygame.Vector2(0, -1).rotate(-self.angle)

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

        for obstacle in self.world.obstacles:
            if new_hitbox.colliderect(obstacle):
                return

        if self.world.rect.contains(new_hitbox):
            self.hitbox = new_hitbox
            self.rect.center = self.hitbox.center

    def check_road(self):
        for road in self.world.roads:
            if self.hitbox.colliderect(road):
                return True
        return False

    def update(self):
        self.accelerate()
        self.set_rotation()
        self.get_rotation()


class CameraGroup(pygame.sprite.Group):
    def __init__(self, world):
        super().__init__()

        self.display_surface = pygame.display.get_surface()
        self.world = world

        self.offset = pygame.Vector2()

        self.half_w = self.display_surface.get_width() // 2
        self.half_h = self.display_surface.get_height() // 2
    
    def center_target_camera(self, target):
        """
        Moves the camera offset so that the target object stays centered
        on the screen while preventing the camera from leaving the world boundaries.
        """
        self.offset.x = target.rect.centerx - self.half_w
        self.offset.y = target.rect.centery - self.half_h

        self.offset.x = max(
    0,
    min(
        self.offset.x,
        self.world.rect.width - self.display_surface.get_width()
    )
)

        self.offset.y = max(
    0,
    min(
        self.offset.y,
        self.world.rect.height - self.display_surface.get_height()
    )
)

    def custom_draw(self, target):
        """
        Draws the world and all sprites with the camera offset applied.
        The camera position is updated first so it follows the player.
        """    
        # update camera first
        self.center_target_camera(target)

        # draw world
        world_offset = self.world.rect.topleft - self.offset
        self.display_surface.blit(self.world.surface, world_offset)

        # draw sprites
        for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.centery):
            offset_position = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_position)


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
pygame.mouse.set_visible(False)
clock = pygame.time.Clock()

# setup
world = World()
camera_group = CameraGroup(world)

cars = [
    Car(CAR_START_POS, world),
    Car((4000, 3000), world)
]

player = Player((CAR_START_POS[0] + 80, CAR_START_POS[1]))

for car in cars:
    camera_group.add(car)

camera_group.add(player)

camera_target = player


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if player.current_car:
                car = player.current_car
                if event.key == pygame.K_RIGHT: car.direction += 1
                if event.key == pygame.K_LEFT: car.direction -= 1
                if event.key == pygame.K_SPACE: car.active = True

        if event.type == pygame.KEYUP:
            if player.current_car:
                car = player.current_car
                if event.key == pygame.K_RIGHT: car.direction -= 1
                if event.key == pygame.K_LEFT: car.direction += 1
                if event.key == pygame.K_SPACE: car.active = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:

                # ENTER CAR
                if not player.in_car:
                    for car in cars:
                        if player.rect.colliderect(car.rect.inflate(50, 50)):
                            player.in_car = True
                            player.current_car = car
                            player.kill()
                            camera_target = car
                            break
                        
                # EXIT CAR
                else:
                    car = player.current_car

                    player.in_car = False
                    car.direction = 0
                    car.active = False

                    player.rect.center = (car.rect.centerx + 60, car.rect.centery)

                    camera_group.add(player)
                    camera_target = player
                    player.current_car = None

    for car in cars:
        car.update()

    player.update()

    camera_group.custom_draw(camera_target)

    pygame.display.update()
    clock.tick(120)