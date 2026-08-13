import pygame, sys, random

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
CAR_START_POS = (3320, 3900)
BG_GRASS_COLOR = (120, 150, 80)
FIELD_COLOR = (100,140,20)
ROAD_COLOR = (80,80,70)
OBSTACLE_COLOR = (156, 36, 11)
ZOOM = 0.75

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

        self.scaled_surface = pygame.transform.scale(
    self.surface,
    (
        int(self.surface.get_width() * ZOOM),
        int(self.surface.get_height() * ZOOM)
    )
)

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
        self.speed = 400

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

    def move(self, cars, dt):
        if self.direction.length() > 0:
            self.direction = self.direction.normalize()

        new_rect = self.rect.copy()
        new_rect.center += self.direction * self.speed * dt

        for car in cars:
            if new_rect.colliderect(car.hitbox):
                return

        self.rect = new_rect

    def update(self, cars, dt):

        if self.in_car:
            self.rect.center = self.current_car.rect.center

        else:
            self.input()
            self.move(cars, dt)

class Car(pygame.sprite.Sprite):
    def __init__(self, pos, world, image_path, hitbox_inflate,road_speed, offroad_speed):
        super().__init__()
        raw = pygame.image.load(image_path).convert_alpha()
        # scale once, here — not every frame
        w, h = raw.get_size()
        self.original_image = pygame.transform.smoothscale(raw, (int(w * 0.7), int(h * 0.7)))
        self.image = self.original_image
        self.rect = self.image.get_rect(center = pos)
        self.angle = 0
        self.rotation_speed = 180
        self.direction = 0
        self.forward = pygame.math.Vector2(0, -1)
        
        self.speed = 0
        self.acceleration = 400
        self.friction = 500
        self.road_speed = road_speed
        self.offroad_speed = offroad_speed

        self.hitbox = self.rect.inflate(*hitbox_inflate)

        self.active = False

        self.world = world

    def set_rotation(self, dt):
        if self.speed > 0:
            if self.direction == 1:
                self.angle -= self.rotation_speed * dt
            if self.direction == -1:
                self.angle += self.rotation_speed * dt

        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.hitbox.center)

    def get_rotation(self):
        self.forward = pygame.Vector2(0, -1).rotate(-self.angle)

    def accelerate(self, cars, dt):
        if self.check_road():
            max_speed = self.road_speed
        else:
            max_speed = self.offroad_speed

        if self.active:
            self.speed += self.acceleration * dt
            self.speed = min(self.speed, max_speed)
        else:
            self.speed -= self.friction * dt
            self.speed = max(self.speed, 0)

        new_hitbox = self.hitbox.copy()
        new_hitbox.center += self.forward * self.speed * dt

        for obstacle in self.world.obstacles:
            if new_hitbox.colliderect(obstacle):
                return

        for car in cars:
            if car != self and new_hitbox.colliderect(car.hitbox):
                return

        if self.world.rect.contains(new_hitbox):
            self.hitbox = new_hitbox
            self.rect.center = self.hitbox.center

    def check_road(self):
        for road in self.world.roads:
            if self.hitbox.colliderect(road):
                return True
        return False

    def update(self,cars, dt):
        self.accelerate(cars, dt)
        self.set_rotation(dt)
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

        # Camera position in WORLD coordinates
        self.offset.x = target.rect.centerx - self.half_w / ZOOM
        self.offset.y = target.rect.centery - self.half_h / ZOOM

        # Prevent camera from leaving the world
        self.offset.x = max(
            0,min(
                self.offset.x, self.world.rect.width - self.display_surface.get_width() / ZOOM)
                )

        self.offset.y = max(
            0,
            min(
                self.offset.y,
                self.world.rect.height - self.display_surface.get_height() / ZOOM
            )
        )

    def custom_draw(self, target):
        self.center_target_camera(target)

        world_offset = -self.offset * ZOOM

        self.display_surface.blit(self.world.scaled_surface, world_offset)

        for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.centery):
            
            scaled_image = pygame.transform.scale(
                sprite.image,
                (
                    int(sprite.image.get_width() * ZOOM),
                    int(sprite.image.get_height() * ZOOM)
                )
            )

            position = (
                pygame.Vector2(sprite.rect.topleft) * ZOOM
                - self.offset * ZOOM
            )

            self.display_surface.blit(
                scaled_image,
                position
            )

class Mission:
    def __init__(self):
        self.number = 1
        self.completed = False
        self.completion_time = 0

        # Destination in world coordinates
        self.destination = pygame.Rect(4200, 2500, 200, 200)
        self.destination2 = pygame.Rect(5000, 1500, 200, 200)

        # Used to pause between missions
        self.complete_timer = 0

    def update(self, player, dt):

        # -------------------------
        # MISSION 1
        # -------------------------
        if self.number == 1:

            # Must be driving a car
            if player.in_car:
                car = player.current_car

                if not self.completed and car.hitbox.colliderect(self.destination):
                    self.completed = True
                    self.completion_time = pygame.time.get_ticks()
                    self.complete_timer = 2
        # -------------------------
        # WAIT AFTER MISSION 1
        # -------------------------
        elif self.number == 2:

            # Must be on foot
            if not player.in_car:

                if not self.completed and player.rect.colliderect(self.destination2):
                    self.completed = True
                    self.completion_time = pygame.time.get_ticks()
                    self.complete_timer = 2

        # Countdown after completing mission
        if self.completed:
            self.complete_timer -= dt

            if self.complete_timer <= 0:
                self.completed = False
                self.number += 1

    def draw(self, surface, camera):

        if not self.completed:

            if self.number == 1:
                destination = self.destination

            elif self.number == 2:
                destination = self.destination2

            else:
                return
            
            position = (
                destination.x * ZOOM - camera.offset.x * ZOOM,
                destination.y * ZOOM - camera.offset.y * ZOOM
            )

            size = (
                int(destination.width * ZOOM),
                int(destination.height * ZOOM)
            )

            pygame.draw.rect(
                surface,
                (255, 255, 0),
                (*position, *size),
                5
            )

    def draw_ui(self, surface):

        if self.completed:

            elapsed = pygame.time.get_ticks() - self.completion_time

            if elapsed < 2000:
                text = font.render(
                    "MISSION COMPLETE!",
                    True,
                    (255, 255, 255)
                )

                surface.blit(text, (30, 30))

        else:

            if self.number == 1:
                message = "MISSION 1: Drive to the marked location"

            elif self.number == 2:
                message = "MISSION 2: Get out and walk to the marked location"

            else:
                return

            text = font.render(
                message,
                True,
                (255, 255, 255)
            )

            surface.blit(text, (30, 30))

pygame.init()
font = pygame.font.Font(None, 40)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
pygame.mouse.set_visible(False)
clock = pygame.time.Clock()

# setup
font = pygame.font.Font(None, 40)
world = World()
camera_group = CameraGroup(world)
mission = Mission()

cars = [
    Car(CAR_START_POS, world, "Audi.png", (-160, -135), 900, 500),
    Car((4000, 3000), world, "Audi.png", (-160, -135), 900, 500),
    Car((4500, 3000), world, "Offroad.png", (-20, -20), 700, 700),
    Car((5000, 3000), world, "buggy.png", (-20, -20), 1200, 1200),
    Car((2900, 3300), world, "tractor.png", (-50, -50), 400, 400),
    Car((2900, 1000), world, "Jeep.png", (-60,-60), 700, 700),
    Car((2700, 1000), world, "bouboul.png", (-20, -20), 500, 200),
    Car((3430,2500), world, "audi_v2.png", (-20, -20), 900, 500),
    Car((3430,2300), world, "audi_v3.png", (-20, -20), 900, 500),
    Car((3430,2100), world, "circle_car.png", (-20, -20), 900, 500)


]

player = Player((CAR_START_POS[0] + 80, CAR_START_POS[1]))

for car in cars:
    camera_group.add(car)

camera_group.add(player)

camera_target = player


while True:
    dt = clock.tick(120) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
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
                ENTER_DISTANCE = 100

                if not player.in_car:
                    closest_car = None
                    closest_distance = ENTER_DISTANCE

                    for car in cars:
                        distance = pygame.math.Vector2(player.rect.center).distance_to(car.rect.center)

                        if distance < closest_distance:
                            closest_distance = distance
                            closest_car = car

                    if closest_car:
                        player.in_car = True
                        player.current_car = closest_car
                        player.kill()
                        camera_target = closest_car

                # EXIT CAR
                else:
                    car = player.current_car

                    player.in_car = False
                    car.direction = 0
                    car.active = False

                    player.rect.center = (
                        car.hitbox.right + player.rect.width + 80,
                        car.hitbox.centery
                    )

                    camera_group.add(player)
                    camera_target = player
                    player.current_car = None

    for car in cars:
        car.update(cars, dt)

    player.update(cars, dt)

    mission.update(player, dt)

    camera_group.custom_draw(camera_target)

    mission.draw(screen, camera_group)
    mission.draw_ui(screen)

    pygame.display.update()