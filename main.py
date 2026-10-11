import pygame, sys, random

# SETTINGS
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
CAR_START_POS = (3320, 3900)
BG_GRASS_COLOR = (120, 150, 80)
FIELD_COLOR = (100,140,20)
ROAD_COLOR = (80,80,70)
BALE_COLOR = (156, 36, 11)
ZOOM = 0.75

class World:
    def __init__(self):
        self.surface = pygame.Surface((6000, 4000))
        self.surface.fill(BG_GRASS_COLOR)

        self.rect = self.surface.get_rect(topleft = (0, 0))

        self.wheat_rect = pygame.Rect(3400, 400, 2100, 2800)   # island between the four roads

        self.roads = [
                    pygame.Rect(3000, 0, 400, 4000),
                    pygame.Rect(3400, 100, 2400, 300),
                    pygame.Rect(5500, 100, 300, 3400),
                    pygame.Rect(3400, 3200, 2400, 300)
                ]

        self.fields = []

        for i in range(10):

            while True:
                width = random.randint(600, 1000)
                height = random.randint(400, 800)

                x = random.randint(0, self.rect.width - width)
                y = random.randint(0, self.rect.height - height)

                new_field = pygame.Rect(x, y, width, height)
                check_field = new_field.inflate(10, 10)

                if (
                    not any(check_field.colliderect(field) for field in self.fields)
                    and not any(new_field.colliderect(road) for road in self.roads)
                    and not new_field.colliderect(self.wheat_rect)
                ):
                    break
                
            self.fields.append(new_field)

        self.hay_bale_image = pygame.image.load("graphics/hay_bale.png").convert_alpha()
        self.hay_bale_image = pygame.transform.scale(self.hay_bale_image, (48, 96))

        self.hay_bales = []

        for _ in range(18):
            width, height = 48, 96

            while True:
                x = random.randint(self.wheat_rect.left, self.wheat_rect.right - width)
                y = random.randint(self.wheat_rect.top, self.wheat_rect.bottom - height)
                new_bale = pygame.Rect(x, y, width, height)

                if not any(
                    new_bale.inflate(600, 600).colliderect(bale)
                    for bale in self.hay_bales
                ):
                    self.hay_bales.append(new_bale)
                    break
        
        house_1 = pygame.image.load("graphics/house_1.png").convert_alpha()
        house_1 = pygame.transform.scale(house_1, (500, 500))

        house_2 = pygame.image.load("graphics/house_2.png").convert_alpha()
        house_2 = pygame.transform.scale(house_2, (500, 700))

        self.houses = [
            pygame.Rect(2450, 400, 500, 500),
            pygame.Rect(2480, 2500, 500, 700)
        ]

        self.house_images = [house_1, house_2]

        self.obstacles = self.houses + self.hay_bales

        self.obstacle_masks = (
            [pygame.mask.from_surface(image) for image in self.house_images]
            + [pygame.mask.Mask(bale.size, fill=True) for bale in self.hay_bales]
        )

        self.paths_to_houses = [
            pygame.Rect(2950, 770 , 50, 100),
            pygame.Rect(2840, 900, 60, 15),
            pygame.Rect(2710, 3200, 60, 200),
            pygame.Rect(2710, 3380, 290, 60)
        ] 

        self.tree_image = pygame.image.load("graphics/tree.png").convert_alpha()

        self.trees = []

        for i in range(35):

            while True:
                tree_width = 216
                tree_height = 216

                x = random.randint(0, self.rect.width - tree_width)
                y = random.randint(0, self.rect.height - tree_height)

                tree_rect = pygame.Rect(
                    x, y, tree_width, tree_height
                )

                if (
                    not any(tree_rect.colliderect(field) for field in self.fields)
                    and not any(tree_rect.colliderect(road) for road in self.roads)
                    and not any(tree_rect.colliderect(obstacle) for obstacle in self.obstacles) 
                    and not any(tree_rect.colliderect(path) for path in self.paths_to_houses)
                    and not tree_rect.colliderect(self.wheat_rect)
                ):
                    break
                
            tree = Tree((x, y), self.tree_image)
            self.trees.append(tree)

        self.flower_bed_triangle_image = pygame.image.load(
            "graphics/flower_bed_triangle.png"
        ).convert_alpha()

        self.flower_bed_triangle_rect = self.flower_bed_triangle_image.get_rect(
            topleft=(2770, 3248)
        )

        self.flower_bed_rect_image = pygame.image.load("graphics/flower_bed_rect.png").convert_alpha()
        self.flower_bed_rect_rect = self.flower_bed_rect_image.get_rect(topleft =(2630, 3200))

        self.draw_map()

        self.scaled_surface = pygame.transform.scale(
            self.surface,(int(self.surface.get_width() * ZOOM), int(self.surface.get_height() * ZOOM))
            )

    def draw_map(self):

        for field in self.fields:
            pygame.draw.rect(self.surface, FIELD_COLOR, field)

        tile = pygame.image.load("graphics/wheat_tile.png").convert()

        self.surface.set_clip(self.wheat_rect)
        for x in range(self.wheat_rect.left, self.wheat_rect.right, tile.get_width()):
            for y in range(self.wheat_rect.top, self.wheat_rect.bottom, tile.get_height()):
                self.surface.blit(tile, (x, y))
        self.surface.set_clip(None)

        for bale in self.hay_bales:
            self.surface.blit(self.hay_bale_image, bale.topleft)

        for road in self.roads:
            pygame.draw.rect(self.surface, ROAD_COLOR, road) 

        for house, image in zip(self.houses, self.house_images):
            self.surface.blit(image, house.topleft)

        for path in self.paths_to_houses:
            pygame.draw.rect(self.surface, ROAD_COLOR, path)

        self.surface.blit(self.flower_bed_triangle_image, self.flower_bed_triangle_rect)
        self.surface.blit(self.flower_bed_rect_image, self.flower_bed_rect_rect)

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, world):
        super().__init__()

        self.world = world

        # -------------------------
        # LOAD SPRITE SHEET
        # -------------------------
        sheet = pygame.image.load("graphics/player.png").convert_alpha()

        self.frames = {"down": [], "up": [], "left": [], "right": []}

        directions = ["down", "up", "left", "right"]

        for row, direction in enumerate(directions):
        # =
        # for row in range(len(directions)):
        #         direction = directions[row]

            for col in range(4):

                frame = sheet.subsurface(pygame.Rect(col * 32, row * 32, 32, 32))

                # Scale the 32×32 frame
                frame = pygame.transform.scale(frame, (64, 64))

                self.frames[direction].append(frame)
        # -------------------------
        # PLAYER STATE
        # -------------------------

        self.direction = "down"

        self.frame_index = 0
        self.animation_timer = 0

        self.image = self.frames["down"][0]
        self.rect = self.image.get_rect(center=pos)

        self.collision_mask = pygame.mask.from_surface(self.frames["down"][0])

        # 300 pixels/second is roughly
        # equivalent to your old 3 pixels/frame
        # when running around 100 FPS.
        self.speed = 270

        self.movement = pygame.Vector2()

        self.in_car = False
        self.current_car = None

    def input(self):

        keys = pygame.key.get_pressed()

        self.movement.x = 0
        self.movement.y = 0

        # LEFT
        if keys[pygame.K_q] or keys[pygame.K_a]:
            self.movement.x -= 1

        # RIGHT
        if keys[pygame.K_d]:
            self.movement.x += 1

        # UP
        if keys[pygame.K_z] or keys[pygame.K_w]:
            self.movement.y -= 1

        # DOWN
        if keys[pygame.K_s]:
            self.movement.y += 1

    def move(self, cars, dt):
        if self.movement.length() > 0:
            self.movement = self.movement.normalize()

        player_mask = self.collision_mask

        def blocked(test_rect):
            if not self.world.rect.contains(test_rect):
                return True

            for car in cars:
                if test_rect.colliderect(car.rect):
                    offset = (
                        car.rect.x - test_rect.x,
                        car.rect.y - test_rect.y
                    )
                    if player_mask.overlap(car.mask, offset):
                        return True

            for obstacle, obstacle_mask in zip(
                self.world.obstacles,
                self.world.obstacle_masks
            ):
                if test_rect.colliderect(obstacle):
                    offset = (
                        obstacle.x - test_rect.x,
                        obstacle.y - test_rect.y
                    )
                    if player_mask.overlap(obstacle_mask, offset):
                        return True

            return False

        moved_rect = self.rect.copy()

        # Try horizontal movement first.
        candidate = moved_rect.copy()
        candidate.x += self.movement.x * self.speed * dt
        if not blocked(candidate):
            moved_rect = candidate

        # Then try vertical movement.
        candidate = moved_rect.copy()
        candidate.y += self.movement.y * self.speed * dt
        if not blocked(candidate):
            moved_rect = candidate

        self.rect = moved_rect

    def animate(self, dt):

        # -------------------------
        # NOT WALKING
        # -------------------------

        if self.movement.length() == 0:

            self.frame_index = 3

            self.image = self.frames[self.direction][3]

            return

        # -------------------------
        # WALKING
        # -------------------------

        self.animation_timer += dt

        if self.animation_timer >= 0.12:

            self.animation_timer = 0

            self.frame_index += 1

            if self.frame_index >= 4:
                self.frame_index = 0

        self.image = self.frames[self.direction][self.frame_index]

    def update(self, cars, dt):

        # Player is hidden while inside a car
        if self.in_car:
            return

        # everything below this only happens when NOT in a car
        self.input()

        # Determine which direction the character is facing.
        if self.movement.x < 0:
            self.direction = "left"

        elif self.movement.x > 0:
            self.direction = "right"

        elif self.movement.y < 0:
            self.direction = "up"

        elif self.movement.y > 0:
            self.direction = "down"

        self.move(cars, dt)

        self.animate(dt)

class Tree(pygame.sprite.Sprite):
    def __init__(self, pos, image):
        super().__init__()

        self.image = image
        self.rect = self.image.get_rect(topleft=pos)

class Car(pygame.sprite.Sprite):
    def __init__(
            self, pos, world, image_path, hitbox_inflate, road_speed, offroad_speed, driver_image_path=None
            ):
        super().__init__()

        raw = pygame.image.load(image_path).convert_alpha()
        w, h = raw.get_size()

        self.original_image = pygame.transform.smoothscale(raw, (int(w * 0.7), int(h * 0.7)))

        # Normal car image (without driver)
        self.normal_image = self.original_image

        self.driver_image = None
        self.driver_visible = False

        if driver_image_path:
            driver_raw = pygame.image.load(driver_image_path).convert_alpha()

            self.driver_image = pygame.transform.smoothscale(driver_raw, (int(w * 0.7), int(h * 0.7)))
        
        self.image = self.original_image
        self.rect = self.image.get_rect(center = pos)
        self.mask = pygame.mask.from_surface(self.image)
        self.angle = 0
        self.rotation_speed = 180
        self.direction = 0
        self.forward = pygame.math.Vector2(0, -1)
        
        self.speed = 0
        self.acceleration = 400
        self.friction = 500
        self.brake = 1200
        self.road_speed = road_speed
        self.offroad_speed = offroad_speed

        self.hitbox = self.rect.inflate(*hitbox_inflate)

        self.active = False # self.active = True means player commands car to accelerate ie presses arrow up
        self.reverse_active = False

        self.world = world

    def set_rotation(self, cars, dt):
        new_angle = self.angle

        if self.speed != 0:
            steer = self.rotation_speed * dt
            if self.speed < 0:
                steer = -steer  # steering flips when reversing, like a real car

            if self.direction == 1:
                new_angle -= steer
            if self.direction == -1:
                new_angle += steer

        image, rect, mask = self.build_image(new_angle)

        # Cancel the turn if it would make the car overlap another car
        if new_angle != self.angle and (
            self.hits_car(rect, mask, cars) or self.hits_obstacle(rect, mask)
        ):
            image, rect, mask = self.build_image(self.angle)
        else:
            self.angle = new_angle

        self.image, self.rect, self.mask = image, rect, mask
            
    def build_image(self, angle):
        image = pygame.transform.rotate(self.original_image, angle)
        rect = image.get_rect(center=self.hitbox.center)
        mask = pygame.mask.from_surface(image)
        return image, rect, mask

    def hits_car(self, rect, mask, cars):
        for car in cars:
            if car is self:
                continue
            if rect.colliderect(car.rect):
                offset = (car.rect.x - rect.x, car.rect.y - rect.y)
                if mask.overlap(car.mask, offset):
                    return True
        return False

    def hits_obstacle(self, rect, mask):
        for obstacle, obstacle_mask in zip(self.world.obstacles, self.world.obstacle_masks):
            if rect.colliderect(obstacle):
                offset = (obstacle.x - rect.x, obstacle.y - rect.y)
                if mask.overlap(obstacle_mask, offset):
                    return True
        return False

    def get_rotation(self):
        self.forward = pygame.Vector2(0, -1).rotate(-self.angle)

    def set_driver(self, visible):
        self.driver_visible = bool(visible and self.driver_image)

        if self.driver_visible:
            self.original_image = self.driver_image
        else:
            self.original_image = self.normal_image
            # original_image = the base image currently selected for the car

        self.image = pygame.transform.rotate(self.original_image,self.angle)

    def accelerate(self, cars, dt):
        if self.check_road():
            max_speed = self.road_speed
        else:
            max_speed = self.offroad_speed

        if self.active:
            self.speed += self.acceleration * dt
            self.speed = min(self.speed, max_speed)
        elif self.reverse_active:
            if self.speed > 0:
                # still rolling forward: brake first
                self.speed = max(self.speed - self.brake * dt, 0)
            else:
                # stopped or already going backwards: reverse
                self.speed -= self.acceleration * dt
                self.speed = max(self.speed, -max_speed * 0.4)
        else:
            # friction slows the car toward 0 from either direction
            if self.speed > 0:
                self.speed = max(self.speed - self.friction * dt, 0)
            elif self.speed < 0:
                self.speed = min(self.speed + self.friction * dt, 0)
                
        new_hitbox = self.hitbox.copy()
        new_hitbox.center += self.forward * self.speed * dt

        new_rect = self.rect.copy()
        new_rect.center = new_hitbox.center

        if self.hits_obstacle(new_rect, self.mask):
            return

        if self.hits_car(new_rect, self.mask, cars):
            return

        if self.world.rect.contains(new_hitbox):
            self.hitbox = new_hitbox
            self.rect.center = self.hitbox.center

    def check_road(self):
        for road in self.world.roads:
            if self.hitbox.colliderect(road):
                return True
        return False

    def update(self, cars, dt):
        self.accelerate(cars, dt)

        # Only vehicles with configured animation frames use this path.
        # Tractor frames animate while moving (forward or backward) and return to frame 1 at rest.
        if hasattr(self, "animation_frames"):
            if self.speed != 0:
                self.animation_timer += dt

                if self.animation_timer >= 0.07:
                    self.animation_timer %= 0.07
                    step = 1 if self.speed > 0 else -1
                    self.animation_index = (self.animation_index + step) % 4
            else:
                self.animation_timer = 0
                self.animation_index = 0

            frames = (
                self.driver_animation_frames
                if self.driver_visible
                else self.animation_frames
            )
            self.original_image = frames[self.animation_index]

        self.set_rotation(cars, dt)
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

        self.offset.x = target.rect.centerx - self.half_w / ZOOM
        self.offset.y = target.rect.centery - self.half_h / ZOOM

        # Prevent camera from leaving the world
        self.offset.x = max(
            0,
            min(
                self.offset.x,
                self.world.rect.width - self.display_surface.get_width() / ZOOM
            )
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
                (100, 0, 255),
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

# INIT
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
pygame.mouse.set_visible(False)
clock = pygame.time.Clock() # used for creating dt only
font = pygame.font.Font(None, 40)

# GAME SETUP
world = World()
camera_group = CameraGroup(world)
mission = Mission()

for tree in world.trees:
    camera_group.add(tree)


# VEHICLE GRAPHICS
buggy = "graphics/buggy/buggy.png"
buggy_driver = "graphics/buggy/buggy_with_player.png"

tractor = "graphics/tractor/tractor_1.png"
tractor_driver = "graphics/tractor/tractor_with_player_1.png"

# VEHICLE SETUP
tractor_car = Car((5380, 3070), world, tractor, (-100, -100), 400, 400, tractor_driver)

cars = [
    Car((CAR_START_POS), world, buggy, (-50, -50), 1200, 1200, buggy_driver),
    Car((2900,3300), world, "graphics/circlus_grey.png", (-20, -20), 900, 500),
    tractor_car,
    Car((2900, 1000), world, "graphics/Jeep.png", (-60,-60), 1000, 1000),
    Car((2700, 1000), world, "graphics/bouboul.png", (-20, -20), 600, 200),
    Car((3430,2500), world, "graphics/audi_v2.png", (-20, -20), 900, 500),
    Car((3430,2300), world, "graphics/audi_v3.png", (-20, -20), 900, 500),
    Car((3430,2100), world, "graphics/circlus_red.png", (-20, -20), 900, 500)
]

for bale in world.hay_bales:
    while True:
        candidate = pygame.Rect(
            random.randint(world.wheat_rect.left, world.wheat_rect.right - bale.width),
            random.randint(world.wheat_rect.top, world.wheat_rect.bottom - bale.height),
            bale.width,
            bale.height
        )

        overlaps_car = any(
            candidate.inflate(10, 10).colliderect(car.rect)
            for car in cars
        )
        overlaps_bale = any(
            candidate.inflate(10, 10).colliderect(other)
            for other in world.hay_bales
            if other is not bale
        )

        if not overlaps_car and not overlaps_bale:
            bale.topleft = candidate.topleft
            break

world.surface.fill(BG_GRASS_COLOR)
world.draw_map()
world.scaled_surface = pygame.transform.scale(
    world.surface,
    (
        int(world.surface.get_width() * ZOOM),
        int(world.surface.get_height() * ZOOM)
    )
)

# Create forward-rolling tread phases from the tractor's base image.
def make_tractor_frames(base_image):
    source = base_image.copy()
    scale_x = base_image.get_width() / 199
    scale_y = base_image.get_height() / 263
    wheel_bounds = [
        (27, 28, 63, 98),
        (136, 28, 172, 98),
        (2, 150, 51, 260),
        (147, 150, 197, 260),
    ]
    frames = []

    for tread_shift in (0, 4, 8, 12):
        frame = source.copy()

        if tread_shift:
            shift = max(1, round(tread_shift * scale_y))

            for left, top, right, bottom in wheel_bounds:
                left = round(left * scale_x)
                right = round(right * scale_x)
                top = round(top * scale_y)
                bottom = round(bottom * scale_y)
                height = bottom - top

                for y in range(top, bottom):
                    source_y = top + (y - top - shift) % height

                    for x in range(left, right):
                        original_pixel = source.get_at((x, y))
                        tread_pixel = source.get_at((x, source_y))

                        if original_pixel.a and tread_pixel.a:
                            frame.set_at(
                                (x, y),
                                (*tread_pixel[:3], original_pixel.a)
                            )

        frames.append(frame)

    return frames


# Animate only the tractor, with matching frames for both driver states.
tractor_car.animation_frames = make_tractor_frames(tractor_car.normal_image)
tractor_car.driver_animation_frames = make_tractor_frames(tractor_car.driver_image)
tractor_car.animation_timer = 0
tractor_car.animation_index = 0

# PLAYER SETUP
player = Player((CAR_START_POS[0] + 80, CAR_START_POS[1]), world)

# CAMERA SETUP
for car in cars:
    camera_group.add(car)

camera_group.add(player)

camera_target = player

# GAME LOOP
while True:

    # DT
    dt = clock.tick(120) / 1000


    # EVENTS
    for event in pygame.event.get():


        # SHUTDOWN
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()

        elif event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()


        # CAR CONTROLS
        if event.type == pygame.KEYDOWN:
            if player.current_car:
                car = player.current_car

                if event.key == pygame.K_RIGHT:
                    car.direction += 1
                if event.key == pygame.K_LEFT:
                    car.direction -= 1
                if event.key == pygame.K_UP:
                    car.active = True
                if event.key == pygame.K_DOWN:
                    car.reverse_active = True

        if event.type == pygame.KEYUP:
            if player.current_car:
                car = player.current_car

                if event.key == pygame.K_RIGHT:
                    car.direction -= 1
                if event.key == pygame.K_LEFT:
                    car.direction += 1
                if event.key == pygame.K_UP:
                    car.active = False
                if event.key == pygame.K_DOWN:
                    car.reverse_active = False

        # ENTER / EXIT CAR
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:

                ENTER_DISTANCE = 120

                # ENTER CAR
                if not player.in_car:
                    closest_car = None
                    closest_distance = ENTER_DISTANCE

                    for car in cars:
                        distance = pygame.math.Vector2(
                            player.rect.center
                        ).distance_to(car.rect.center)

                        if distance < closest_distance:
                            closest_distance = distance
                            closest_car = car

                    if closest_car:
                        player.in_car = True
                        player.current_car = closest_car
                        closest_car.set_driver(True)

                        player.kill()
                        camera_target = closest_car

                # EXIT CAR
                else:
                    car = player.current_car

                    player.in_car = False
                    car.set_driver(False)
                    car.direction = 0
                    car.active = False
                    car.reverse_active = False

                    player.rect.center = (
                        car.rect.right + player.rect.width,
                        car.hitbox.centery
                    )

                    camera_group.add(player)
                    camera_target = player
                    player.current_car = None


    # UPDATE
    for car in cars:
        car.update(cars, dt)

    player.update(cars, dt)
    mission.update(player, dt)


    # DRAW
    camera_group.custom_draw(camera_target)

    mission.draw(screen, camera_group)
    mission.draw_ui(screen)

    pygame.display.update()
