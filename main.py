import pygame, sys, random

# SETTINGS
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
BG_GRASS_COLOR = (120, 150, 80)
FIELD_COLOR = (100,140,20)
ROAD_COLOR = (80,80,70)
BALE_COLOR = (156, 36, 11)
ZOOM = 0.75
DAY_LENGTH_SECONDS = 120
START_HOUR = 13.0


class DayNightCycle:
    """A simple 24-hour clock with a smooth ambient color overlay."""

    # (hour, tint RGB, tint opacity). Clear midday uses zero opacity.
    KEYFRAMES = (
        (0.0, (20, 28, 72), 115),
        (4.5, (30, 38, 82), 105),
        (6.0, (255, 120, 55), 62),
        (8.0, (255, 190, 110), 20),
        (9.0, (0, 0, 0), 0),
        (16.0, (0, 0, 0), 0),
        (18.0, (255, 135, 65), 48),
        (20.0, (55, 55, 115), 82),
        (24.0, (20, 28, 72), 115),
    )

    def __init__(self, screen_size, day_length_seconds=DAY_LENGTH_SECONDS, start_hour=START_HOUR):
        self.day_length_seconds = day_length_seconds
        self.hour = start_hour % 24
        self.overlay = pygame.Surface(screen_size, pygame.SRCALPHA)
        self.clock_font = pygame.font.Font(None, 28)

    def update(self, dt):
        self.hour = (self.hour + dt * 24 / self.day_length_seconds) % 24

    def _tint(self):
        hour = self.hour
        for index in range(len(self.KEYFRAMES) - 1):
            start_hour, start_color, start_alpha = self.KEYFRAMES[index]
            end_hour, end_color, end_alpha = self.KEYFRAMES[index + 1]
            if start_hour <= hour <= end_hour:
                amount = (hour - start_hour) / (end_hour - start_hour)
                color = tuple(round(a + (b - a) * amount) for a, b in zip(start_color, end_color))
                alpha = round(start_alpha + (end_alpha - start_alpha) * amount)
                return color, alpha
        return (0, 0, 0), 0

    def draw(self, screen):
        color, alpha = self._tint()
        if alpha:
            self.overlay.fill((*color, alpha))
            screen.blit(self.overlay, (0, 0))

        hours = int(self.hour)
        minutes = int((self.hour - hours) * 60)
        label = self.clock_font.render(f"{hours:02d}:{minutes:02d}", True, (255, 255, 255))
        box = pygame.Rect(SCREEN_WIDTH - 112, 18, 94, 38)
        pygame.draw.rect(screen, (20, 20, 25), box, border_radius=6)


class DayNightCycle:
    """A simple 24-hour clock with a smooth ambient color overlay."""

    # (hour, tint RGB, tint opacity). Clear midday uses zero opacity.
    KEYFRAMES = (
        (0.0, (20, 28, 72), 115),
        (4.5, (30, 38, 82), 105),
        (6.0, (255, 120, 55), 62),
        (8.0, (255, 190, 110), 20),
        (9.0, (0, 0, 0), 0),
        (16.0, (0, 0, 0), 0),
        (18.0, (255, 135, 65), 48),
        (20.0, (55, 55, 115), 82),
        (24.0, (20, 28, 72), 115),
    )

    def __init__(self, screen_size, day_length_seconds=DAY_LENGTH_SECONDS, start_hour=START_HOUR):
        self.day_length_seconds = day_length_seconds
        self.hour = start_hour % 24
        self.overlay = pygame.Surface(screen_size, pygame.SRCALPHA)
        self.clock_font = pygame.font.Font(None, 28)

    def update(self, dt):
        self.hour = (self.hour + dt * 24 / self.day_length_seconds) % 24

    def _tint(self):
        hour = self.hour
        for index in range(len(self.KEYFRAMES) - 1):
            start_hour, start_color, start_alpha = self.KEYFRAMES[index]
            end_hour, end_color, end_alpha = self.KEYFRAMES[index + 1]
            if start_hour <= hour <= end_hour:
                amount = (hour - start_hour) / (end_hour - start_hour)
                color = tuple(round(a + (b - a) * amount) for a, b in zip(start_color, end_color))
                alpha = round(start_alpha + (end_alpha - start_alpha) * amount)
                return color, alpha
        return (0, 0, 0), 0

    def draw(self, screen):
        color, alpha = self._tint()
        if alpha:
            self.overlay.fill((*color, alpha))
            screen.blit(self.overlay, (0, 0))

        hours = int(self.hour)
        minutes = int((self.hour - hours) * 60)
        label = self.clock_font.render(f"{hours:02d}:{minutes:02d}", True, (255, 255, 255))
        box = pygame.Rect(SCREEN_WIDTH - 112, 18, 94, 38)
        pygame.draw.rect(screen, (20, 20, 25), box, border_radius=6)
        screen.blit(label, label.get_rect(center=box.center))


class WeatherSystem:
    """Occasional rainstorms and thick fog during the morning hours."""

    STORM_CHANCE_PER_DAY = 1
    MORNING_FOG_START_HOUR = 5.0
    MORNING_FOG_END_HOUR = 9.0
    MORNING_FOG_FADE_HOURS = 0.75
    STORM_MIN_HOURS = 2.5
    STORM_MAX_HOURS = 5.5
    STORM_FADE_HOURS = 0.75
    RAIN_DROP_COUNT = 1100
    FOG_CLOUD_COUNT = 14

    def __init__(self, screen_size, day_length_seconds, start_hour, world_size):
        self.width, self.height = screen_size
        self.world_width, self.world_height = world_size
        self.day_length_seconds = day_length_seconds
        self.elapsed_game_hours = float(start_hour)
        self.current_day = int(self.elapsed_game_hours // 24)
        self.rng = random.Random()
        self.storms = {}
        self._schedule_day(self.current_day)
        self.intensity = 0.0
        self.fog_only_intensity = 0.0

        self.fog_layer = pygame.Surface(screen_size, pygame.SRCALPHA)
        self.rain_layer = pygame.Surface(screen_size, pygame.SRCALPHA)
        self.fog_clouds = []
        for _ in range(self.FOG_CLOUD_COUNT):
            cloud_width = self.rng.randint(520, 900)
            cloud_height = self.rng.randint(320, 600)
            cloud_world_image = self._make_fog_cloud(cloud_width, cloud_height)
            cloud_image = pygame.transform.smoothscale(
                cloud_world_image, (round(cloud_width * ZOOM), round(cloud_height * ZOOM))
            )
            self.fog_clouds.append({
                "image": cloud_image,
                "world_width": cloud_width,
                "x": self.rng.uniform(-cloud_width, self.world_width),
                "y": self.rng.uniform(-cloud_height / 2, self.world_height - cloud_height / 2),
                "speed": self.rng.choice((-1, 1)) * self.rng.uniform(28, 60),
            })
        self.rain_drops = [
            [self.rng.uniform(0, self.width), self.rng.uniform(0, self.height),
             self.rng.uniform(14, 30), self.rng.uniform(850, 1450)]
            for _ in range(self.RAIN_DROP_COUNT)
        ]

    def _make_fog_cloud(self, width, height):
        """Build a soft-edged fog bank from nested translucent ellipses."""
        cloud = pygame.Surface((width, height), pygame.SRCALPHA)
        bands = 40
        for band in range(bands, 0, -1):
            scale = band / bands
            ellipse_width = max(1, round(width * scale))
            ellipse_height = max(1, round(height * scale))
            rect = pygame.Rect(0, 0, ellipse_width, ellipse_height)
            rect.center = (width // 2, height // 2)
            alpha = round(8 + 190 * (1 - scale))
            pygame.draw.ellipse(cloud, (205, 215, 225, alpha), rect)
        return cloud

    def _schedule_day(self, day):
        # Schedule occasional rainstorms; morning fog follows the daily clock.
        earliest_hour = 14 if day == 0 else 0
        storm = None
        if self.rng.random() < self.STORM_CHANCE_PER_DAY:
            start = day * 24 + self.rng.uniform(earliest_hour, 24)
            duration = self.rng.uniform(self.STORM_MIN_HOURS, self.STORM_MAX_HOURS)
            storm = (start, start + duration)
        self.storms[day] = storm


    def update(self, dt):
        self.elapsed_game_hours += dt * 24 / self.day_length_seconds
        for bank in self.fog_clouds:
            bank["x"] += bank["speed"] * dt
            if bank["speed"] > 0 and bank["x"] > self.world_width:
                bank["x"] = -bank["world_width"]
            elif bank["speed"] < 0 and bank["x"] + bank["world_width"] < 0:
                bank["x"] = self.world_width
        new_day = int(self.elapsed_game_hours // 24)
        while self.current_day < new_day:
            self.current_day += 1
            self._schedule_day(self.current_day)
        for old_day in list(self.storms):
            if old_day < self.current_day - 1:
                del self.storms[old_day]

        target = 0.0
        for storm in self.storms.values():
            if storm is None:
                continue
            start, end = storm
            if start <= self.elapsed_game_hours < end:
                fade_in = min(1.0, (self.elapsed_game_hours - start) / self.STORM_FADE_HOURS)
                fade_out = min(1.0, (end - self.elapsed_game_hours) / self.STORM_FADE_HOURS)
                target = max(target, min(fade_in, fade_out))
        self.intensity = target

        # Thick fog returns every morning, independently of the rain schedule.
        morning_hour = self.elapsed_game_hours % 24
        fog_start = self.MORNING_FOG_START_HOUR
        fog_end = self.MORNING_FOG_END_HOUR
        if fog_start <= morning_hour < fog_end:
            fade_in = min(1.0, (morning_hour - fog_start) / self.MORNING_FOG_FADE_HOURS)
            fade_out = min(1.0, (fog_end - morning_hour) / self.MORNING_FOG_FADE_HOURS)
            self.fog_only_intensity = min(fade_in, fade_out)
        else:
            self.fog_only_intensity = 0.0

        if self.intensity > 0.01:
            wind = 190 * self.intensity
            for drop in self.rain_drops:
                drop[0] += wind * dt
                drop[1] += drop[3] * dt
                if drop[1] > self.height:
                    drop[0] = self.rng.uniform(-80, self.width)
                    drop[1] = -drop[2]
                    drop[2] = self.rng.uniform(14, 30)
                    drop[3] = self.rng.uniform(850, 1450)
                if drop[0] > self.width + 80:
                    drop[0] = -80

    def draw(self, screen, camera):
        if self.intensity <= 0.01 and self.fog_only_intensity <= 0.01:
            return

        if self.fog_only_intensity > 0.01:
            thick_fog_alpha = round(105 * self.fog_only_intensity)
            self.fog_layer.fill((170, 185, 200, thick_fog_alpha))
            cloud_alpha = round(210 * self.fog_only_intensity)
            for bank in self.fog_clouds:
                bank["image"].set_alpha(cloud_alpha)
                screen_x = round((bank["x"] - camera.offset.x) * ZOOM)
                screen_y = round((bank["y"] - camera.offset.y) * ZOOM)
                self.fog_layer.blit(bank["image"], (screen_x, screen_y))
            screen.blit(self.fog_layer, (0, 0))

        if self.intensity <= 0.01:
            return

        self.rain_layer.fill((0, 0, 0, 0))
        rain_alpha = round(175 * self.intensity)
        rain_color = (195, 215, 230, rain_alpha)
        visible_drop_count = round(len(self.rain_drops) * self.intensity)
        for x, y, length, _speed in self.rain_drops[:visible_drop_count]:
            start = (int(x), int(y))
            end = (int(x - 5), int(y - length))
            pygame.draw.line(self.rain_layer, rain_color, start, end, 1)
        screen.blit(self.rain_layer, (0, 0))

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

        self.pos = pygame.Vector2(self.hitbox.topleft)

        self.speed = 180
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
        new_x = self.pos.x + self.movement.x * self.speed * dt
        candidate = self.hitbox.copy()
        candidate.x = round(new_x)
        if not self.is_blocked(candidate, cars):
            self.pos.x = new_x
            self.hitbox = candidate

        # Vertical
        new_y = self.pos.y + self.movement.y * self.speed * dt
        candidate = self.hitbox.copy()
        candidate.y = round(new_y)
        if not self.is_blocked(candidate, cars):
            self.pos.y = new_y
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

        self.pos = pygame.Vector2(self.hitbox.center)

        self.active = False # self.active = True means player commands car to accelerate ie presses arrow up
        self.reverse_active = False

        self.engine_sound = None
        self.engine_volume = 0

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

    def try_push_car(self, target, displacement, proposed_rect, cars, dt):
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
        target.pos = pygame.Vector2(target.hitbox.center)
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

        new_pos = self.pos + self.forward * self.speed * dt

        new_hitbox = self.hitbox.copy()
        new_hitbox.center = (round(new_pos.x), round(new_pos.y))

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

                if self.try_push_car(
                    car, self.forward * self.speed * dt, new_rect, cars, dt
                ):                    
                    pushed_a_car = True
                    break

            if not pushed_a_car:
                return

        if self.world.rect.contains(new_hitbox):
            self.pos = new_pos
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

    def current_destination(self):
        if self.completed:
            return None
        if self.number == 1:
            return self.destination
        if self.number == 2:
            return self.destination2
        return None

def draw_minimap(surface, target, mission):
    R = MINIMAP_RADIUS
    cx = SCREEN_WIDTH - R - MINIMAP_MARGIN
    cy = SCREEN_HEIGHT - R - MINIMAP_MARGIN

    # Player position on the shrunken world
    px = target.rect.centerx * MINIMAP_SCALE
    py = target.rect.centery * MINIMAP_SCALE

    # Draw the part of the map around the player, then cut it into a circle
    minimap_view.fill((25, 25, 25, 255))
    minimap_view.blit(minimap_world, (R - px, R - py))
    minimap_view.blit(minimap_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    surface.blit(minimap_view, (cx - R, cy - R))

    # Mission objective: clamped to the rim when it's out of view
    destination = mission.current_destination()
    if destination:
        offset = pygame.Vector2(
            destination.centerx * MINIMAP_SCALE - px,
            destination.centery * MINIMAP_SCALE - py,
        )
        max_dist = R - 8
        if offset.length() > max_dist:
            offset.scale_to_length(max_dist)

        pos = (int(cx + offset.x), int(cy + offset.y))
        pygame.draw.circle(surface, (255, 255, 255), pos, 7)
        pygame.draw.circle(surface, (100, 0, 255), pos, 5)

    # Player is always in the center
    pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 6)
    pygame.draw.circle(surface, (220, 30, 30), (cx, cy), 4)

    # Border
    pygame.draw.circle(surface, (255, 255, 255), (cx, cy), R, 3)

# INIT
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
pygame.mouse.set_visible(False)
clock = pygame.time.Clock() # used for creating dt only
font = pygame.font.Font(None, 40)

day_night = DayNightCycle((SCREEN_WIDTH, SCREEN_HEIGHT))

# GAME SETUP
world = World()
weather = WeatherSystem((SCREEN_WIDTH, SCREEN_HEIGHT), DAY_LENGTH_SECONDS, START_HOUR, world.rect.size)
camera_group = CameraGroup(world)
mission = Mission()

for tree in world.trees:
    camera_group.add(tree)

# SOUND SETUP
bg_birdsounds = pygame.mixer.Sound("sounds/morning_birds.mp3")
bg_birdsounds.play(loops = -1)

car_engine_sound = pygame.mixer.Sound("sounds/car_engine_loop.ogg")
car_engine_sound.set_volume(0)

tractor_engine_sound = pygame.mixer.Sound("sounds/tractor_engine_loop.wav")
tractor_engine_sound.set_volume(0)
tractor_engine_volume = 0

buggy_engine_sound = pygame.mixer.Sound("sounds/buggy_engine_loop.wav")
buggy_engine_sound.set_volume(0)
buggy_engine_volume = 0

# VEHICLE GRAPHICS
buggy = "graphics/buggy/buggy.png"
buggy_driver = "graphics/buggy/buggy_with_player.png"

tractor = "graphics/tractor/tractor_1.png"
tractor_driver = "graphics/tractor/tractor_with_player_1.png"

# VEHICLE SETUP
tractor_car = Car((5000, 2500), world, tractor, (-100, -100), 300, 300, tractor_driver)

cars = [
    Car((4800, 3570), world, buggy, (-50, -50), 1200, 1200, buggy_driver),
    Car((2900, 3300), world, "graphics/circlus_grey.png", (-20, -20), 900, 500),
    tractor_car,
    Car((2900, 1000), world, "graphics/Jeep.png", (-60,-60), 1000, 1000),
    Car((2700, 1000), world, "graphics/bouboul.png", (-20, -20), 600, 300),
    Car((3430, 2500), world, "graphics/audi_v2.png", (-20, -20), 900, 500),
    Car((3430, 2300), world, "graphics/audi_v3.png", (-20, -20), 900, 500),
    Car((3430, 2100), world, "graphics/circlus_red.png", (-20, -20), 900, 500)
]

cars[0].angle = -90
cars[0].image, cars[0].rect, cars[0].mask = cars[0].build_image(cars[0].angle)
cars[0].get_rotation()

cars[0].engine_sound = buggy_engine_sound
tractor_car.engine_sound = tractor_engine_sound

cars[0].engine_gain = 1.0       # buggy
tractor_car.engine_gain = 1.0   # tractor

for car in cars:
    if car.engine_sound is None:
        car.engine_sound = pygame.mixer.Sound("sounds/car_engine_loop.ogg")
        car.engine_sound.play(loops=-1)
        pygame.mixer.set_num_channels(len(cars) + 1)
        car.engine_gain = 2.5   # regular cars: louder
    else:
        car.engine_sound.play(loops=-1)

    car.engine_sound.set_volume(0)

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

# MINIMAP SETUP
MINIMAP_RADIUS = 45            
MINIMAP_SCALE = 0.075               
MINIMAP_MARGIN = 20
MINIMAP_SCALE = 0.15                 # minimap px per world px (bigger = more zoomed in)
MINIMAP_D = MINIMAP_RADIUS * 2

# whole world shrunk once (6000x4000 -> 900x600)
minimap_world = pygame.transform.smoothscale(
    world.surface,
    (int(world.rect.width * MINIMAP_SCALE), int(world.rect.height * MINIMAP_SCALE))
)

# reusable surfaces
minimap_view = pygame.Surface((MINIMAP_D, MINIMAP_D), pygame.SRCALPHA)
minimap_mask = pygame.Surface((MINIMAP_D, MINIMAP_D), pygame.SRCALPHA)
minimap_mask.fill((0, 0, 0, 0))
pygame.draw.circle(minimap_mask, (255, 255, 255, 255), (MINIMAP_RADIUS, MINIMAP_RADIUS), MINIMAP_RADIUS)

# TRACTOR MOVING WHEELS
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
    dt = clock.tick() / 1000


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
                        player.pos = pygame.Vector2(spot.topleft)
                        player.rect.midbottom = player.hitbox.midbottom

                        camera_group.add(player)
                        camera_target = player
                        player.current_car = None
                    # if there is no free space, the player simply stays in the car

    # UPDATE
    day_night.update(dt)
    weather.update(dt)
    for car in cars:
        car.update(cars, dt)

    player.update(cars, dt)
    mission.update(player, dt)

    # ENGINE SOUND
    for car in cars:
        target_volume = 0

        if player.in_car and player.current_car is car:
            if car.active or car.reverse_active:
                target_volume = 0.25  # pedal pressed
            elif car.speed != 0:
                target_volume = 0.1  # coasting

        target_volume = min(1.0, target_volume * car.engine_gain)

        car.engine_volume += (target_volume - car.engine_volume) * min(1, 8 * dt)
        car.engine_sound.set_volume(car.engine_volume)
        
        # smooth fade so it doesn't cut abruptly
        car.engine_volume += (target_volume - car.engine_volume) * min(1, 8 * dt)
        car.engine_sound.set_volume(car.engine_volume)

    # DRAW
    camera_group.custom_draw(camera_target)
    weather.draw(screen, camera_group)
    day_night.draw(screen)  # tint world; keep mission/minimap UI clear
    day_night.draw(screen)  # tint world and keep the clock readable

    mission.draw(screen, camera_group)
    mission.draw_ui(screen)
    draw_minimap(screen, camera_target, mission)

    pygame.display.update()