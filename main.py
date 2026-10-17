import pygame, sys, random

# SETTINGS
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
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

        self.island_rect = pygame.Rect(3400, 400, 2100, 2800)    # whole island between the roads
        self.grass_border = 40
        self.wheat_rect = self.island_rect.inflate(-2 * self.grass_border, -2 * self.grass_border)

        self.roads = [
                    pygame.Rect(3000, 0, 400, 4000),
                    pygame.Rect(3400, 100, 2400, 300),
                    pygame.Rect(5500, 0, 300, 3400),
                    pygame.Rect(3400, 3200, 2400, 300)
                ]

        self.field_dirt_rect = pygame.Rect(4700, 2200, 800, 200)

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
                    and not new_field.colliderect(self.island_rect)
                ):
                    break
                
            self.fields.append(new_field)

        self.hay_bale_image = pygame.image.load("graphics/hay_bale.png").convert_alpha()
        self.hay_bale_image = pygame.transform.scale(self.hay_bale_image, (48, 96))

        self.hay_bales = []

        self.hay_bales = []

        for _ in range(10):
            width, height = 48, 96

            while True:
                x = random.randint(self.wheat_rect.left, self.wheat_rect.right - width)
                y = random.randint(self.wheat_rect.top, self.wheat_rect.bottom - height)
                new_bale = pygame.Rect(x, y, width, height)

                if (
                    not any(
                        new_bale.inflate(600, 600).colliderect(bale)
                        for bale in self.hay_bales
                    )
                    and not new_bale.colliderect(self.field_dirt_rect)
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

        # Flower beds (defined early so they can be part of obstacles)
        self.flower_bed_triangle_image = pygame.image.load(
            "graphics/flower_bed_triangle.png"
        ).convert_alpha()
        self.flower_bed_triangle_rect = self.flower_bed_triangle_image.get_rect(
            topleft=(2770, 3248)
        )

        self.flower_bed_rect_image = pygame.image.load(
            "graphics/flower_bed_rect.png"
        ).convert_alpha()
        self.flower_bed_rect_rect = self.flower_bed_rect_image.get_rect(
            topleft=(2630, 3200)
        )

        self.flower_beds = [
            self.flower_bed_triangle_rect,
            self.flower_bed_rect_rect
        ]

        # Obstacles now include houses + hay bales + flower beds
        self.obstacles = self.houses + self.hay_bales + self.flower_beds

        self.obstacle_masks = (
            [pygame.mask.from_surface(image) for image in self.house_images]
            + [pygame.mask.Mask(bale.size, fill=True) for bale in self.hay_bales]
            + [
                pygame.mask.from_surface(self.flower_bed_triangle_image),
                pygame.mask.from_surface(self.flower_bed_rect_image)
            ]
        )

        self.paths_to_houses = [
            pygame.Rect(2950, 770 , 50, 100),
            pygame.Rect(2840, 900, 60, 15),
            pygame.Rect(2710, 3200, 60, 200),
            pygame.Rect(2710, 3380, 290, 60)
        ] 

        self.tree_image = pygame.image.load("graphics/tree.png").convert_alpha()

        self.trees = []

        for i in range(20):

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
                    and not any(tree_rect.inflate(40, 40).colliderect(tree.rect) for tree in self.trees)
                    and not tree_rect.colliderect(self.island_rect)
                ):
                    break
                
            tree = Tree((x, y), self.tree_image)
            self.trees.append(tree)

        self.draw_map()

        self.scaled_surface = pygame.transform.scale(
            self.surface,(int(self.surface.get_width() * ZOOM), int(self.surface.get_height() * ZOOM))
            )

    def fill_tiled(self, rect, tile):
        self.surface.set_clip(rect)
        for x in range(rect.left, rect.right, tile.get_width()):
            for y in range(rect.top, rect.bottom, tile.get_height()):
                self.surface.blit(tile, (x, y))
        self.surface.set_clip(None)

    def draw_map(self):

        for field in self.fields:
            pygame.draw.rect(self.surface, FIELD_COLOR, field)

        grass_tile = pygame.image.load("graphics/grass_tile.png").convert()
        dirt_tile = pygame.image.load("graphics/dirt_tile.png").convert()
        wheat_tile = pygame.image.load("graphics/wheat_tile.png").convert()

        self.fill_tiled(self.island_rect, grass_tile)  # grass border
        self.fill_tiled(self.wheat_rect, wheat_tile)   # wheat center

        pygame.draw.rect(self.surface, (95, 135, 60), self.island_rect, 4)

        upper_dirt_rect = pygame.Rect(3400, 0, 2100, 100)
        self.fill_tiled(upper_dirt_rect, dirt_tile)

        self.fill_tiled(self.field_dirt_rect, dirt_tile)

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
            for col in range(4):
                frame = sheet.subsurface(pygame.Rect(col * 32, row * 32, 32, 32))
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

        # Smaller hitbox focused on the feet / lower body
        # Tune these two numbers until it feels right
        self.hitbox = pygame.Rect(0, 0, 36, 26)
        self.hitbox.midbottom = self.rect.midbottom
        self.feet_mask = pygame.mask.Mask(self.hitbox.size, fill=True)

        self.speed = 270
        self.movement = pygame.Vector2()

        self.in_car = False
        self.current_car = None

    def input(self):
        keys = pygame.key.get_pressed()

        self.movement.x = 0
        self.movement.y = 0

        if keys[pygame.K_q] or keys[pygame.K_a]:
            self.movement.x -= 1
        if keys[pygame.K_d]:
            self.movement.x += 1
        if keys[pygame.K_z] or keys[pygame.K_w]:
            self.movement.y -= 1
        if keys[pygame.K_s]:
            self.movement.y += 1

    def is_blocked(self, test_hitbox, cars):
        # Stay inside the world
        if not self.world.rect.contains(test_hitbox):
            return True

        # Cars: feet box against the car's real shape
        for car in cars:
            if test_hitbox.colliderect(car.rect):
                offset = (car.rect.x - test_hitbox.x, car.rect.y - test_hitbox.y)
                if self.feet_mask.overlap(car.mask, offset):
                    return True

        # Obstacles: houses, bales, flower beds
        for obstacle, obstacle_mask in zip(self.world.obstacles, self.world.obstacle_masks):
            if test_hitbox.colliderect(obstacle):
                offset = (obstacle.x - test_hitbox.x, obstacle.y - test_hitbox.y)
                if self.feet_mask.overlap(obstacle_mask, offset):
                    return True

        return False

    def find_exit_spot(self, car, cars):
        # right, left, below, above, then the four corners
        directions = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1))

        for gap in (10, 40, 90, 150):          # closest first
            for dx, dy in directions:
                test = self.hitbox.copy()
                test.centerx = car.rect.centerx + dx * (car.rect.width // 2 + test.width // 2 + gap)
                test.centery = car.rect.centery + dy * (car.rect.height // 2 + test.height // 2 + gap)

                if not self.is_blocked(test, cars):
                    return test

        return None

    def move(self, cars, dt):
        if self.movement.length() > 0:
            self.movement = self.movement.normalize()

        # Horizontal
        candidate = self.hitbox.copy()
        candidate.x += self.movement.x * self.speed * dt
        if not self.is_blocked(candidate, cars):
            self.hitbox = candidate

        # Vertical
        candidate = self.hitbox.copy()
        candidate.y += self.movement.y * self.speed * dt
        if not self.is_blocked(candidate, cars):
            self.hitbox = candidate

        # Keep the visual sprite aligned with the feet
        self.rect.midbottom = self.hitbox.midbottom

    def animate(self, dt):
        if self.movement.length() == 0:
            self.frame_index = 3
            self.image = self.frames[self.direction][3]
            return

        self.animation_timer += dt

        if self.animation_timer >= 0.12:
            self.animation_timer = 0
            self.frame_index += 1
            if self.frame_index >= 4:
                self.frame_index = 0

        self.image = self.frames[self.direction][self.frame_index]

    def update(self, cars, dt):
        if self.in_car:
            return

        self.input()

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
        self.push_remainder = pygame.Vector2()
        self.acceleration = 400
        self.friction = 500
        self.brake = 1500
        self.reverse_acceleration = 700  # how quickly it picks up speed in reverse
        self.reverse_factor = 0.5        # top reverse speed as a share of top speed
        
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

    def try_push_car(self, target, displacement, proposed_rect, cars):
        """Push an aligned car ahead when this car hits it front-to-rear."""
        if displacement.length_squared() == 0:
            return False

        travel_direction = displacement.normalize()
        between = pygame.Vector2(target.rect.center) - pygame.Vector2(self.rect.center)

        # Reject side impacts. Only push a car that is ahead along the
        # direction of travel and roughly in line with this car.
        forward_distance = between.dot(travel_direction)
        sideways_distance = abs(between.dot(travel_direction.rotate(90)))
        lateral_tolerance = (self.original_image.get_width() + target.original_image.get_width()) * 0.3

        if forward_distance <= 0 or sideways_distance > lateral_tolerance:
            return False

        # Transfer a shove at 20% of the pushing car's current speed.
        # The pushing car waits until there is room to advance.
        requested_push = (
            travel_direction * (abs(self.speed) * 0.2 * dt)
            + target.push_remainder
        )
        push = pygame.Vector2(round(requested_push.x), round(requested_push.y))
        if push.length_squared() == 0:
            target.push_remainder = requested_push
            return False
        pushed_hitbox = target.hitbox.copy()
        pushed_hitbox.centerx += round(push.x)
        pushed_hitbox.centery += round(push.y)
        pushed_rect = target.rect.copy()
        pushed_rect.center = pushed_hitbox.center

        if not self.world.rect.contains(pushed_hitbox):
            return False
        if target.hits_obstacle(pushed_rect, target.mask):
            return False

        for other in cars:
            if other is self or other is target:
                continue
            if pushed_rect.colliderect(other.rect):
                offset = (other.rect.x - pushed_rect.x, other.rect.y - pushed_rect.y)
                if pygame.mask.from_surface(target.image).overlap(other.mask, offset):
                    return False

        target.hitbox = pushed_hitbox
        target.rect.center = pushed_hitbox.center
        target.push_remainder = requested_push - push

        # If the target still blocks the proposed movement, it has been nudged
        # but the pushing car must remain in place for this frame.
        if pushed_rect.colliderect(proposed_rect):
            offset = (proposed_rect.x - pushed_rect.x, proposed_rect.y - pushed_rect.y)
            if target.mask.overlap(self.mask, offset):
                return False

        return True

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

        if self.active and self.reverse_active:
            # both pressed: brake to a standstill, never reverse
            if self.speed > 0:
                self.speed = max(self.speed - self.brake * dt, 0)
            elif self.speed < 0:
                self.speed = min(self.speed + self.brake * dt, 0)
        elif self.active:
            if self.speed < 0:
                # rolling backwards: brake out of the reverse first
                self.speed = min(self.speed + self.brake * dt, 0)
            else:
                self.speed += self.acceleration * dt
                self.speed = min(self.speed, max_speed)
        elif self.reverse_active:
            if self.speed > 0:
                # still rolling forward: brake first
                self.speed = max(self.speed - self.brake * dt, 0)
            else:
                # stopped or already going backwards: reverse
                self.speed -= self.reverse_acceleration * dt
                self.speed = max(self.speed, -max_speed * self.reverse_factor)
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
            pushed_a_car = False

            for car in cars:
                if car is self or not new_rect.colliderect(car.rect):
                    continue

                offset = (car.rect.x - new_rect.x, car.rect.y - new_rect.y)
                if not self.mask.overlap(car.mask, offset):
                    continue

                if self.try_push_car(car, self.forward * self.speed * dt, new_rect, cars):
                    pushed_a_car = True
                    break

            if not pushed_a_car:
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
        self.destination = pygame.Rect(4700, 2400, 200, 200)
        self.destination2 = pygame.Rect(2650, 3500, 200, 200)

        # Used to pause between missions
        self.complete_timer = 0

    def update(self, player, dt):

        # -------------------------
        # MISSION 1
        # -------------------------
        if self.number == 1:

            # Must be walking
            if not player.in_car:

                if not self.completed and player.hitbox.colliderect(self.destination):
                    self.completed = True
                    self.completion_time = pygame.time.get_ticks()
                    self.complete_timer = 2
        # -------------------------
        # WAIT AFTER MISSION 1
        # -------------------------
        elif self.number == 2:

            # Must be driving
            if player.in_car and player.current_car:
                if not self.completed and player.current_car.rect.colliderect(self.destination2):
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
                message = "MISSION 1: Walk to the marked location"

            elif self.number == 2:
                message = "MISSION 2: Drive to the marked location"

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
tractor_car = Car((5000, 2500), world, tractor, (-100, -100), 400, 400, tractor_driver)

cars = [
    Car((4800, 3570), world, buggy, (-50, -50), 1200, 1200, buggy_driver),
    Car((2900, 3300), world, "graphics/circlus_grey.png", (-20, -20), 900, 500),
    tractor_car,
    Car((2900, 1000), world, "graphics/Jeep.png", (-60,-60), 1000, 1000),
    Car((2700, 1000), world, "graphics/bouboul.png", (-20, -20), 600, 200),
    Car((3430, 2500), world, "graphics/audi_v2.png", (-20, -20), 900, 500),
    Car((3430, 2300), world, "graphics/audi_v3.png", (-20, -20), 900, 500),
    Car((3430, 2100), world, "graphics/circlus_red.png", (-20, -20), 900, 500)
]

cars[0].angle = -90
cars[0].image, cars[0].rect, cars[0].mask = cars[0].build_image(cars[0].angle)
cars[0].get_rotation()

# PLAYER SETUP
player = Player((4350,1000), world)

# Move bales that overlap a car, the player, or the dirt area.
for bale in world.hay_bales:
    while (
        any(bale.inflate(10, 10).colliderect(car.rect) for car in cars)
        or bale.inflate(10, 10).colliderect(player.hitbox)
        or bale.colliderect(world.field_dirt_rect)
    ):
        while True:
            candidate = pygame.Rect(
                random.randint(world.wheat_rect.left, world.wheat_rect.right - bale.width),
                random.randint(world.wheat_rect.top, world.wheat_rect.bottom - bale.height),
                bale.width,
                bale.height,
            )

            far_enough = not any(
                candidate.inflate(600, 600).colliderect(other)
                for other in world.hay_bales
                if other is not bale
            )
            clear_of_cars = not any(
                candidate.inflate(10, 10).colliderect(car.rect)
                for car in cars
            )
            clear_of_player = not candidate.inflate(10, 10).colliderect(player.hitbox)
            clear_of_dirt = not candidate.colliderect(world.field_dirt_rect)

            if far_enough and clear_of_cars and clear_of_player and clear_of_dirt:
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
                if event.key == pygame.K_z:
                    car.active = True
                if event.key == pygame.K_d:
                    car.reverse_active = True

        if event.type == pygame.KEYUP:
            if player.current_car:
                car = player.current_car

                if event.key == pygame.K_RIGHT:
                    car.direction -= 1
                if event.key == pygame.K_LEFT:
                    car.direction += 1
                if event.key == pygame.K_z:
                    car.active = False
                if event.key == pygame.K_d:
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
                    spot = player.find_exit_spot(car, cars)

                    if spot is not None:
                        player.in_car = False
                        car.set_driver(False)
                        car.direction = 0
                        car.active = False
                        car.reverse_active = False

                        player.hitbox = spot
                        player.rect.midbottom = player.hitbox.midbottom

                        camera_group.add(player)
                        camera_target = player
                        player.current_car = None
                    # if there is no free space, the player simply stays in the car

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
