import pygame, sys, random, math

# SETTINGS
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
BG_GRASS_COLOR = (120, 150, 80)
FIELD_COLOR = (100,140,20)
ROAD_COLOR = (80,80,70)
ZOOM = 0.75
DAY_LENGTH_SECONDS = 120
START_HOUR = 13.0
BIRDSOUND_FADE_START_HOUR = 19.0
BIRDSOUND_SILENT_HOUR = 20.0
BIRDSOUND_START_HOUR = 5.0
BIRDSOUND_FULL_HOUR = 6.0
OWL_FADE_START_HOUR = 19.0
OWL_FULL_VOLUME_HOUR = 20.0
OWL_FADE_OUT_START_HOUR = 5.0
OWL_SILENT_HOUR = 6.0
OWL_AMBIENCE_VOLUME = 0.45
RIVAL_2_IMAGE = "graphics/buggy/rival_buggy_2.png"
MINIMAP_RADIUS = 45            
MINIMAP_MARGIN = 20
MINIMAP_SCALE = 0.15                 # minimap px per world px (bigger = more zoomed in)

class WheelAnimation:
    """Fake rolling wheels by scrolling the tread pixels inside given wheel areas."""

    def __init__(self, normal_image, driver_image, wheel_bounds, reference_size,
                 shifts=(0, 4, 8, 12), frame_time=0.07):
        self.wheel_bounds = wheel_bounds      # (left, top, right, bottom) in reference-image pixels
        self.reference_size = reference_size  # size of the image the bounds were measured on
        self.shifts = shifts
        self.frame_time = frame_time

        self.normal_frames = self._make_frames(normal_image)
        self.driver_frames = self._make_frames(driver_image) if driver_image else None

        self.timer = 0.0
        self.index = 0

    def _make_frames(self, base_image):
        source = base_image.copy()
        scale_x = base_image.get_width() / self.reference_size[0]
        scale_y = base_image.get_height() / self.reference_size[1]
        frames = []

        for tread_shift in self.shifts:
            frame = source.copy()

            if tread_shift:
                shift = max(1, round(tread_shift * scale_y))

                for left, top, right, bottom in self.wheel_bounds:
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
                                frame.set_at((x, y), (*tread_pixel[:3], original_pixel.a))

            frames.append(frame)

        return frames

    def update(self, speed, dt):
        if speed == 0:
            self.timer = 0.0
            self.index = 0
            return

        self.timer += dt
        if self.timer >= self.frame_time:
            self.timer %= self.frame_time
            step = 1 if speed > 0 else -1
            self.index = (self.index + step) % len(self.shifts)

    def get_image(self, driver_visible):
        if driver_visible and self.driver_frames:
            return self.driver_frames[self.index]
        return self.normal_frames[self.index]

class Minimap:
    """Circular minimap that follows a target and points at the mission objective."""

    def __init__(self, world, radius=MINIMAP_RADIUS, margin=MINIMAP_MARGIN,
                 scale=MINIMAP_SCALE, screen_size=(SCREEN_WIDTH, SCREEN_HEIGHT)):
        self.world = world
        self.radius = radius
        self.scale = scale
        self.diameter = radius * 2
        self.center = (screen_size[0] - radius - margin,
                       screen_size[1] - radius - margin)

        self.view = pygame.Surface((self.diameter, self.diameter), pygame.SRCALPHA)
        self.mask = pygame.Surface((self.diameter, self.diameter), pygame.SRCALPHA)
        pygame.draw.circle(self.mask, (255, 255, 255, 255), (radius, radius), radius)

        self.rebuild()

    def rebuild(self):
        """Re-shrink the world. Call again if the world surface is redrawn."""
        size = (int(self.world.rect.width * self.scale),
                int(self.world.rect.height * self.scale))
        self.world_image = pygame.transform.smoothscale(self.world.surface, size)

    def draw(self, surface, target, mission):
        R = self.radius
        cx, cy = self.center

        # Player position on the shrunken world
        px = target.rect.centerx * self.scale
        py = target.rect.centery * self.scale

        # Draw the area around the player, then cut it into a circle
        self.view.fill((25, 25, 25, 255))
        self.view.blit(self.world_image, (R - px, R - py))
        self.view.blit(self.mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(self.view, (cx - R, cy - R))

        self._draw_objective(surface, mission, px, py)

        # Player is always in the center
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 6)
        pygame.draw.circle(surface, (220, 30, 30), (cx, cy), 4)

        # Border
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), R, 3)

    def _draw_objective(self, surface, mission, px, py):
        destination = mission.current_destination()
        if not destination:
            return

        cx, cy = self.center
        offset = pygame.Vector2(
            destination.centerx * self.scale - px,
            destination.centery * self.scale - py,
        )
        max_dist = self.radius - 8
        if offset.length() > max_dist:
            offset.scale_to_length(max_dist)

        pos = (int(cx + offset.x), int(cy + offset.y))
        pygame.draw.circle(surface, (255, 255, 255), pos, 7)
        pygame.draw.circle(surface, (100, 0, 255), pos, 5)

class RevengeRaceTrack:
    """Geometry, racing lines, checkpoints, and ground marks for Mission 4."""

    LEFT, TOP, RIGHT, BOTTOM = 600, 1000, 2000, 2400
    WIDTH = 300
    HALF_WIDTH = WIDTH // 2
    LANE_OFFSET = 55

    def __init__(self):
        # Keep scenery out of the track area while the world is generated.
        self.zone = pygame.Rect(350, 750, 1950, 1900)

        self.centerline = self._loop_waypoints(
            self.LEFT, self.TOP, self.RIGHT, self.BOTTOM
        )
        self.inner_lane = self._loop_waypoints(
            self.LEFT + self.LANE_OFFSET,
            self.TOP + self.LANE_OFFSET,
            self.RIGHT - self.LANE_OFFSET,
            self.BOTTOM - self.LANE_OFFSET,
        )
        self.outer_lane = self._loop_waypoints(
            self.LEFT - self.LANE_OFFSET,
            self.TOP - self.LANE_OFFSET,
            self.RIGHT + self.LANE_OFFSET,
            self.BOTTOM + self.LANE_OFFSET,
        )
        self.inner_spawn = (1250, self.BOTTOM - self.LANE_OFFSET)
        self.outer_spawn = (1100, self.BOTTOM + self.LANE_OFFSET)

        self.start = pygame.Rect(
            1500, self.BOTTOM - self.HALF_WIDTH, 350, self.WIDTH
        )
        self.finish = self.start.copy()
        self.checkpoints = [
            pygame.Rect(self.LEFT - self.HALF_WIDTH, 1500, self.WIDTH, 400),
            pygame.Rect(1100, self.TOP - self.HALF_WIDTH, 400, self.WIDTH),
            pygame.Rect(self.RIGHT - self.HALF_WIDTH, 1850, self.WIDTH, 350),
        ]
        self.rut_lines = self._build_rut_lines(self.centerline)

    @staticmethod
    def _loop_waypoints(left, top, right, bottom, lead=300):
        """Make eight clockwise lane targets with diagonal corner cuts."""
        return [
            (left + lead, bottom), (left, bottom - lead),
            (left, top + lead), (left + lead, top),
            (right - lead, top), (right, top + lead),
            (right, bottom - lead), (right - lead, bottom),
        ]

    @staticmethod
    def _round_track_corners(points, corner_cut=125, curve_steps=10):
        """Replace sharp polyline corners with short quadratic curves."""
        count = len(points)
        entries = []
        exits = []

        for index, point in enumerate(points):
            previous = pygame.Vector2(points[(index - 1) % count])
            current = pygame.Vector2(point)
            following = pygame.Vector2(points[(index + 1) % count])
            incoming = (current - previous).normalize()
            outgoing = (following - current).normalize()
            cut = min(
                corner_cut,
                (current - previous).length() * 0.35,
                (following - current).length() * 0.35,
            )
            entries.append(current - incoming * cut)
            exits.append(current + outgoing * cut)

        rounded = []
        for index in range(count):
            entry = entries[index]
            corner = pygame.Vector2(points[index])
            exit_point = exits[index]

            for step in range(curve_steps):
                amount = step / curve_steps
                point = (
                    entry * (1 - amount) ** 2
                    + corner * (2 * (1 - amount) * amount)
                    + exit_point * amount ** 2
                )
                rounded.append(point)

            next_entry = entries[(index + 1) % count]
            straight_length = (next_entry - exit_point).length()
            straight_steps = max(1, math.ceil(straight_length / 34))
            for step in range(straight_steps):
                amount = step / straight_steps
                rounded.append(exit_point + (next_entry - exit_point) * amount)

        return rounded

    @classmethod
    def _build_rut_lines(cls, centerline, tire_spacing=52, sample_spacing=34, seed=404):
        """Build two slightly uneven tire ruts along a closed racing line."""
        centerline = cls._round_track_corners(centerline)
        rng = random.Random(seed)
        lines = []
        count = len(centerline)

        for side in (-1, 1):
            offset_points = []
            for index, point in enumerate(centerline):
                previous = pygame.Vector2(centerline[(index - 1) % count])
                current = pygame.Vector2(point)
                following = pygame.Vector2(centerline[(index + 1) % count])
                incoming = (current - previous).normalize()
                outgoing = (following - current).normalize()
                normal_in = pygame.Vector2(-incoming.y, incoming.x)
                normal_out = pygame.Vector2(-outgoing.y, outgoing.x)
                bisector = normal_in + normal_out
                if bisector.length_squared() == 0:
                    bisector = normal_out
                else:
                    bisector = bisector.normalize()
                scale = tire_spacing / max(0.35, abs(bisector.dot(normal_out)))
                offset_points.append(current + bisector * scale * side)

            sampled = []
            for index, start in enumerate(offset_points):
                end = offset_points[(index + 1) % count]
                segment = end - start
                distance = segment.length()
                steps = max(1, math.ceil(distance / sample_spacing))
                normal = pygame.Vector2(-segment.y, segment.x).normalize()
                for step in range(steps):
                    amount = step / steps
                    point = start + segment * amount
                    point += normal * rng.uniform(-4.5, 4.5)
                    sampled.append((round(point.x), round(point.y)))
            lines.append(sampled)

        return lines

    def draw_ruts(self, surface, camera):
        """Draw the ruts on the ground before vehicles and characters."""
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        layers = (
            ((76, 65, 47, 145), 34),
            ((158, 132, 88, 150), 25),
            ((83, 72, 52, 115), 7),
        )
        for path in self.rut_lines:
            screen_points = [
                (round((x - camera.offset.x) * ZOOM),
                 round((y - camera.offset.y) * ZOOM))
                for x, y in path
            ]
            for color, world_width in layers:
                width = max(1, round(world_width * ZOOM))
                pygame.draw.lines(overlay, color, True, screen_points, width)
                radius = max(1, width // 2)
                for point in screen_points:
                    pygame.draw.circle(overlay, color, point, radius)

        surface.blit(overlay, (0, 0))

class DayNightCycle:
    """A simple 24-hour clock with a smooth ambient color overlay."""

    # (hour, tint RGB, tint opacity). Clear midday uses zero opacity.
    KEYFRAMES = (
        (0.0, (14, 22, 56), 140),
        (3.5, (18, 28, 66), 130),
        (5.0, (70, 65, 82), 100),
        (6.5, (255, 120, 55), 62),
        (8.0, (255, 165, 90), 35),
        (9.5, (0, 0, 0), 0),
        (16.0, (0, 0, 0), 0),
        (17.5, (255, 170, 90), 24),
        (19.0, (255, 135, 65), 48),
        (21.0, (45, 45, 105), 100),
        (24.0, (14, 22, 56), 140),
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
    def __init__(self, revenge_track):
        self.revenge_track = revenge_track
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
                    and not new_field.colliderect(self.revenge_track.zone)
                ):
                    break
                
            self.fields.append(new_field)

        self.hay_bale_image = pygame.image.load("graphics/hay_bale.png").convert_alpha()
        self.hay_bale_image = pygame.transform.scale(self.hay_bale_image, (48, 96))

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

        # Lamps run along the same roadside, spaced 600 world pixels apart.
        lamp_image = pygame.image.load("graphics/street_lamp_post.png").convert_alpha()
        self.street_lamp_image = pygame.transform.flip(lamp_image, True, False)
        self.street_lamp_grounds = [(3420, y) for y in range(750, 3151, 600)]
        self.street_lamp_sprites = []
        self.street_lamp_collision_rects = []
        self.street_lamp_collision_masks = []
        for ground in self.street_lamp_grounds:
            sprite = pygame.sprite.Sprite()
            sprite.image = self.street_lamp_image
            sprite.rect = self.street_lamp_image.get_rect(midbottom=ground)
            self.street_lamp_sprites.append(sprite)

            # Only each pole's base blocks movement; its raised arm and head do not.
            self.street_lamp_collision_rects.append(
                pygame.Rect(ground[0] - 14, ground[1] - 24, 28, 24)
            )
            self.street_lamp_collision_masks.append(pygame.mask.Mask((28, 24), fill=True))

        self.street_lamp_bulbs_world = [(x - 70, y - 260) for x, y in self.street_lamp_grounds]
        lamp_wire_points = [(x - 10, y - 280) for x, y in self.street_lamp_grounds]
        self.overhead_cable_spans = list(zip(lamp_wire_points, lamp_wire_points[1:]))
        for house_index, house in enumerate(self.houses):
            nearest_index = min(
                range(len(self.street_lamp_grounds)),
                key=lambda index: (
                    (self.street_lamp_grounds[index][0] - house.right) ** 2
                    + (self.street_lamp_grounds[index][1] - house.centery) ** 2
                ),
            )
            lamp_anchor = lamp_wire_points[nearest_index]
            if house_index == 1:
                # Connect at the marked upper-right roof-to-wall corner.
                house_anchor = (house.left + 430, house.top + 40)
            else:
                # Use the matching upper-right roof-to-wall corner on house one.
                house_anchor = (house.left + 460, house.top + 40)
            self.overhead_cable_spans.append(
                (lamp_anchor, house_anchor)
            )

        horizontal_cone = self._make_cone_glow_surface(
            (round(350 * ZOOM), round(240 * ZOOM)), 145
        )
        # The generated beam points left (pi); rotate it to the requested
        # -pi/2 screen direction so it runs from the bulb down toward the street.
        self.street_lamp_cone_glow = pygame.transform.rotate(
            horizontal_cone, math.degrees(-math.pi / 2 - math.pi)
        )
        self.street_lamp_bulb_core = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(self.street_lamp_bulb_core, (255, 236, 178, 255), (6, 6), 4)

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
        self.obstacles = (
            self.houses + self.hay_bales + self.flower_beds
            + self.street_lamp_collision_rects
        )

        self.obstacle_masks = (
            [pygame.mask.from_surface(image) for image in self.house_images]
            + [pygame.mask.Mask(bale.size, fill=True) for bale in self.hay_bales]
            + [
                pygame.mask.from_surface(self.flower_bed_triangle_image),
                pygame.mask.from_surface(self.flower_bed_rect_image),
            ]
            + self.street_lamp_collision_masks
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
                    and not tree_rect.colliderect(self.revenge_track.zone)
                ):
                    break
                
            tree = Tree((x, y), self.tree_image)
            self.trees.append(tree)

    @staticmethod
    def _make_cone_glow_surface(size, max_alpha):
        """Build a soft cone with its source at the right, aimed across the road."""
        cone = pygame.Surface(size, pygame.SRCALPHA)
        width, height = size
        center_y = height // 2
        layers = 64
        for layer in range(layers, 0, -1):
            fraction = layer / layers
            half_height = max(1, round((height / 2 - 1) * fraction))
            length = max(1, round((width - 1 - (height / 2 - 1)) * fraction))
            alpha = round(10 + (max_alpha - 10) * (1 - fraction) ** 0.8)
            source_x = width - 1
            end_x = source_x - length
            points = [(source_x, center_y)]
            samples = 24
            for sample in range(1, samples + 1):
                amount = sample / samples
                x = source_x - length * amount
                radius = half_height * math.sqrt(amount)
                points.append((round(x), round(center_y - radius)))
            for sample in range(1, samples + 1):
                angle = -math.pi / 2 + math.pi * sample / samples
                x = end_x - half_height * math.cos(angle)
                y = center_y + half_height * math.sin(angle)
                points.append((round(x), round(y)))
            for sample in range(samples - 1, 0, -1):
                amount = sample / samples
                x = source_x - length * amount
                radius = half_height * math.sqrt(amount)
                points.append((round(x), round(center_y + radius)))
            points.append((source_x, center_y))
            pygame.draw.polygon(cone, (255, 205, 125, alpha), points)
        return cone

    def draw_street_lamp_light(self, screen, camera, hour):
        """Draw a west-facing road-light cone and bulb halo at night."""
        if 17.5 <= hour < 20.5:
            intensity = (hour - 17.5) / 3.0
        elif hour >= 20.5 or hour < 5.0:
            intensity = 1.0
        elif 5.0 <= hour < 8.0:
            intensity = (8.0 - hour) / 3.0
        else:
            intensity = 0.0
        if intensity <= 0:
            return

        cone = self.street_lamp_cone_glow
        cone.set_alpha(round(255 * intensity))
        core = self.street_lamp_bulb_core
        core.set_alpha(round(255 * intensity))
        for bulb_x, bulb_y in self.street_lamp_bulbs_world:
            bulb_center = (
                round((bulb_x - camera.offset.x) * ZOOM),
                round((bulb_y - camera.offset.y) * ZOOM),
            )
            screen.blit(cone, cone.get_rect(midtop=bulb_center))
            screen.blit(core, core.get_rect(center=bulb_center))

    def draw_overhead_cables(self, screen, camera):
        """Render sagging power cables over the world sprites, without collision."""
        for start, end in self.overhead_cable_spans:
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            length = max(1.0, math.hypot(dx, dy))
            normal_x = -dy / length
            normal_y = dx / length
            # Let the cable sag toward the road; for a horizontal span, sag down.
            if normal_x > 0 or (abs(normal_x) < 0.001 and normal_y < 0):
                normal_x = -normal_x
                normal_y = -normal_y
            sag = min(30.0, max(12.0, length * 0.025))
            control = (
                (start[0] + end[0]) / 2 + normal_x * sag,
                (start[1] + end[1]) / 2 + normal_y * sag,
            )

            points = []
            for step in range(33):
                amount = step / 32
                inverse = 1 - amount
                world_x = (
                    inverse * inverse * start[0]
                    + 2 * inverse * amount * control[0]
                    + amount * amount * end[0]
                )
                world_y = (
                    inverse * inverse * start[1]
                    + 2 * inverse * amount * control[1]
                    + amount * amount * end[1]
                )
                points.append((
                    round((world_x - camera.offset.x) * ZOOM),
                    round((world_y - camera.offset.y) * ZOOM),
                ))

            pygame.draw.lines(screen, (32, 31, 29), False, points, 2)
            pygame.draw.aalines(screen, (78, 74, 67), False, points)

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
            self, pos, world, image_path, hitbox_inflate, road_speed, offroad_speed,
            driver_image_path=None, wheel_bounds=None, reference_size=None
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

        self.wheel_animation = None
        if wheel_bounds:
            self.wheel_animation = WheelAnimation(
                self.normal_image, self.driver_image, wheel_bounds, reference_size
            )
        
        self.image = self.original_image
        self.rect = self.image.get_rect(center = pos)
        self.mask = pygame.mask.from_surface(self.image)
        self.collision_mask = self.build_collision_mask(0)
        self.angle = 0
        self.rotation_speed = 180
        self.direction = 0
        self.forward = pygame.math.Vector2(0, -1)
        
        self.speed = 0
        self.collision_velocity = pygame.Vector2()
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

        image, rect, mask, collision_mask = self.build_image(new_angle)

        # Cancel the turn if it would make the car overlap another car
        if new_angle != self.angle and (
            self.hits_car(rect, collision_mask, cars) or self.hits_obstacle(rect, mask)
        ):
            image, rect, mask, collision_mask = self.build_image(self.angle)
        else:
            self.angle = new_angle

        self.image, self.rect, self.mask, self.collision_mask = image, rect, mask, collision_mask
            
    def build_collision_mask(self, angle):
        """Use a padded rounded body shape so wheel gaps cannot interlock."""
        width, height = self.original_image.get_size()
        body = pygame.Surface((width, height), pygame.SRCALPHA)
        body_rect = body.get_rect().inflate(-max(2, width // 18), -max(2, height // 24))
        pygame.draw.rect(body, (255, 255, 255, 255), body_rect, border_radius=max(2, min(width, height) // 12))
        rotated_body = pygame.transform.rotate(body, angle)
        return pygame.mask.from_surface(rotated_body)

    def build_image(self, angle):
        image = pygame.transform.rotate(self.original_image, angle)
        rect = image.get_rect(center=self.hitbox.center)
        mask = pygame.mask.from_surface(image)
        collision_mask = self.build_collision_mask(angle)
        return image, rect, mask, collision_mask

    def hits_car(self, rect, collision_mask, cars):
        for car in cars:
            if car is self:
                continue
            if rect.colliderect(car.rect):
                offset = (car.rect.x - rect.x, car.rect.y - rect.y)
                if collision_mask.overlap(car.collision_mask, offset):
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
                if target.collision_mask.overlap(other.collision_mask, offset):
                    return False

        target.hitbox = pushed_hitbox
        target.pos = pygame.Vector2(target.hitbox.center)
        target.rect.center = pushed_hitbox.center
        target.push_remainder = requested_push - push

        # If the target still blocks the proposed movement, it has been nudged
        # but the pushing car must remain in place for this frame.
        if pushed_rect.colliderect(proposed_rect):
            offset = (proposed_rect.x - pushed_rect.x, proposed_rect.y - pushed_rect.y)
            if target.collision_mask.overlap(self.collision_mask, offset):
                return False

        return True

    def bounce_off_car(self, other):
        """Reduce speed and push both cars apart on impact."""
        normal = pygame.Vector2(self.hitbox.center) - pygame.Vector2(other.hitbox.center)
        if normal.length_squared() == 0:
            normal = -self.forward
        else:
            normal.normalize_ip()

        self_velocity = self.forward * self.speed + self.collision_velocity
        other_velocity = other.forward * other.speed + other.collision_velocity
        closing_speed = max(0, -(self_velocity - other_velocity).dot(normal))
        impulse = max(220, min(450, closing_speed * 0.75))
        self.speed *= 0.7
        other.speed *= 0.7
        self.collision_velocity += normal * impulse
        other.collision_velocity -= normal * impulse

        for car, direction in ((self, normal), (other, -normal)):
            shifted_hitbox = car.hitbox.copy()
            shifted_hitbox.centerx += round(direction.x * 8)
            shifted_hitbox.centery += round(direction.y * 8)
            shifted_rect = car.rect.copy()
            shifted_rect.center = shifted_hitbox.center
            if (car.world.rect.contains(shifted_hitbox)
                    and not car.hits_obstacle(shifted_rect, car.mask)):
                car.hitbox = shifted_hitbox
                car.pos = pygame.Vector2(shifted_hitbox.center)
                car.rect.center = shifted_hitbox.center

    def set_driver(self, visible):
        self.driver_visible = bool(visible and self.driver_image)

        if self.driver_visible:
            self.original_image = self.driver_image
        else:
            self.original_image = self.normal_image
            # original_image = the base image currently selected for the car

        self.image = pygame.transform.rotate(self.original_image,self.angle)
        self.rect = self.image.get_rect(center=self.hitbox.center)
        self.mask = pygame.mask.from_surface(self.image)

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

        new_pos = self.pos + (self.forward * self.speed + self.collision_velocity) * dt
        self.collision_velocity *= max(0, 1 - 5 * dt)

        new_hitbox = self.hitbox.copy()
        new_hitbox.center = (round(new_pos.x), round(new_pos.y))

        new_rect = self.rect.copy()
        new_rect.center = new_hitbox.center

        if self.hits_obstacle(new_rect, self.mask):
            return

        if self.hits_car(new_rect, self.collision_mask, cars):
            pushed_a_car = False

            for car in cars:
                if car is self or not new_rect.colliderect(car.rect):
                    continue

                offset = (car.rect.x - new_rect.x, car.rect.y - new_rect.y)
                if not self.collision_mask.overlap(car.collision_mask, offset):
                    continue

                if self.try_push_car(
                    car, self.forward * self.speed * dt, new_rect, cars, dt
                ):                    
                    pushed_a_car = True
                    break

            if not pushed_a_car:
                for car in cars:
                    if car is self or not new_rect.colliderect(car.rect):
                        continue

                    offset = (car.rect.x - new_rect.x, car.rect.y - new_rect.y)
                    if self.collision_mask.overlap(car.collision_mask, offset):
                        self.bounce_off_car(car)
                        break
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

        if self.wheel_animation:
            self.wheel_animation.update(self.speed, dt)
            self.original_image = self.wheel_animation.get_image(self.driver_visible)

        self.set_rotation(cars, dt)
        self.get_rotation()

class SmokeParticle(pygame.sprite.Sprite):
    """A soft dark puff emitted from the tractor's exhaust pipe."""

    def __init__(self, position, velocity, lifetime):
        super().__init__()
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(velocity)
        self.lifetime = lifetime
        self.age = 0.0
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(round(position[0]), round(position[1])))
        self.refresh_image()

    def refresh_image(self):
        self.image.fill((0, 0, 0, 0))
        center = (16, 16)
        radius = min(14, round(4 + self.age * 10))
        pygame.draw.circle(self.image, (42, 40, 38, 140), center, radius)
        pygame.draw.circle(
            self.image, (20, 19, 18, 195), center, max(1, round(radius * 0.68))
        )
        pygame.draw.circle(
            self.image, (8, 8, 8, 225), center, max(1, round(radius * 0.34))
        )
        self.image.set_alpha(round(255 * max(0.0, 1.0 - self.age / self.lifetime)))
        self.rect = self.image.get_rect(
            center=(round(self.position.x), round(self.position.y))
        )

    def draw(self, surface, camera):
        image = pygame.transform.scale(
            self.image,
            (
                max(1, round(self.image.get_width() * ZOOM)),
                max(1, round(self.image.get_height() * ZOOM)),
            ),
        )
        screen_center = (
            round((self.position.x - camera.offset.x) * ZOOM),
            round((self.position.y - camera.offset.y) * ZOOM),
        )
        surface.blit(image, image.get_rect(center=screen_center))

    def update(self, dt):
        self.age += dt
        if self.age >= self.lifetime:
            self.kill()
            return False

        self.position += self.velocity * dt
        self.velocity *= max(0.0, 1.0 - 0.8 * dt)
        self.refresh_image()
        return True

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

        # Draw the ground marks first, then depth-sort every world sprite.
        # The bottom edge is the sprite's ground contact point, so trees
        # overlap players and vehicles correctly as they move past the trunk.
        self.world.revenge_track.draw_ruts(self.display_surface, self)

        sprites = sorted(self.sprites(), key=lambda sprite: sprite.rect.bottom)
        for sprite in sprites:
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
            self.display_surface.blit(scaled_image, position)

class RaceRival:
    """One AI opponent in a race: its car, its racing line and its lap count."""

    def __init__(self, car, setup):
        self.car = car
        self.spawn = setup["spawn"]
        self.angle = setup["angle"]
        self.waypoints = setup["waypoints"]
        self.reach = setup["reach"]                    # how close it must get to a waypoint
        self.road_speed = setup["road_speed"]
        self.acceleration = setup["acceleration"]
        self.corner_scale = setup["corner_scale"]      # >1 = takes corners faster
        self.reset()

    def reset(self):
        self.waypoint_index = 0
        self.lap = 1

class Mission:
    def __init__(self, revenge_track):
        self.revenge_track = revenge_track
        self.number = 1
        self.completed = False
        self.completion_time = 0

        self.destination = pygame.Rect(4700, 2400, 200, 200)
        self.destination2 = pygame.Rect(2650, 3500, 200, 200)
        self.complete_timer = 0

        self.all_complete_timer = None

        # Filled in by the game setup: every car in the world and the rival cars.
        self.cars = []
        self.rival_car = None      # rival of mission 3 (also the leader of mission 4)
        self.rival_car_2 = None    # his friend, only racing in mission 4

        # Race state shared by missions 3 and 4
        self.race = None
        self.rivals = []
        # locked -> waiting -> countdown -> running -> finished (-> locked again after a loss)
        self.race_state = "locked"
        self.race_countdown = 0.0
        self.race_result = ""
        self.race_result_timer = 0.0
        self.player_won = False
        self.player_checkpoint_index = 0
        self.player_lap = 1

        mission_3_start = pygame.Rect(3400, 3200, 400, 300)
        mission_3_finish = pygame.Rect(4080, 3200, 40, 300)
        self.race_configs = {
            # MISSION 3: two laps around the island roads against the rival.
            3: {
                "laps": 2,
                "start": mission_3_start,
                "finish": mission_3_finish,
                "stripe_x": 4100,
                "checkpoints": [
                    pygame.Rect(5100, 3200, 550, 300),  # bottom/east turn
                    pygame.Rect(5500, 450, 300, 1100),   # east road
                    pygame.Rect(3900, 100, 600, 300),    # top road
                    pygame.Rect(3000, 2000, 400, 500),   # west road
                ],
                "intro": "MISSION 3: Drive to the race start",
                "win": "YOU WON THE RACE!",
                "lose": "THE RIVAL WON THE RACE!",
                "rivals": [
                    {
                        "car": "rival_car",
                        "spawn": (3900, 3270),
                        "angle": -90,  # face east along the bottom road
                        "waypoints": [
                            (5350, 3350), (5650, 2800), (5650, 450), (5300, 250),
                            (3500, 250), (3200, 500), (3200, 3000), (4100, 3350),
                        ],
                        "reach": 320,
                        "road_speed": 900,
                        "acceleration": 750,
                        "corner_scale": 1.0,
                    },
                ],
            },
            # MISSION 4: the revenge. Four laps against two buggies on the
            # track west of the houses. Tune the rivals' speed here.
            4: {
                "laps": 4,
                "start": self.revenge_track.start,
                "finish": self.revenge_track.finish,
                "checkpoints": self.revenge_track.checkpoints,
                "intro": "MISSION 4: THE REVENGE - Drive to the race start",
                "win": "YOU BEAT THEM BOTH!",
                "lose": "THE RIVALS WON THE RACE!",
                "rivals": [
                    {
                        "car": "rival_car",
                        "spawn": self.revenge_track.inner_spawn,
                        "angle": 90,   # face west along the bottom road
                        "waypoints": self.revenge_track.inner_lane,
                        "reach": 150,
                        "road_speed": 1000,
                        "acceleration": 800,
                        "corner_scale": 1.08,
                    },
                    {
                        "car": "rival_car_2",
                        "spawn": self.revenge_track.outer_spawn,
                        "angle": 90,
                        "waypoints": self.revenge_track.outer_lane,
                        "reach": 150,
                        "road_speed": 950,
                        "acceleration": 780,
                        "corner_scale": 1.0,
                    },
                ],
            },
        }

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @property
    def rival_cars(self):
        return [car for car in (self.rival_car, self.rival_car_2) if car is not None]

    def racing_cars(self):
        """Rival cars taking part in the current race."""
        return [rival.car for rival in self.rivals]

    def _begin_race(self):
        """Called once when a race mission (3 or 4) becomes the current mission."""
        config = self.race_configs[self.number]
        self.race = config
        self.rivals = []
        for setup in config["rivals"]:
            car = getattr(self, setup["car"])
            if car is not None:
                self.rivals.append(RaceRival(car, setup))

        self.race_state = "locked"
        self.race_countdown = 0.0
        self.race_result = ""
        self.race_result_timer = 0.0
        self.player_won = False
        self.player_checkpoint_index = 0
        self.player_lap = 1

    def _grid_is_clear(self, player):
        """True when nobody is parked on the rivals' starting spots."""
        zones = []
        for rival in self.rivals:
            zone = pygame.Rect(0, 0, 220, 220)
            zone.center = rival.spawn
            zones.append(zone)

        for car in self.cars:
            if car in self.rival_cars:
                continue
            if any(car.rect.colliderect(zone) for zone in zones):
                return False

        if not player.in_car and any(player.hitbox.colliderect(zone) for zone in zones):
            return False

        return True

    def _place_rivals(self):
        """Put every rival back on the starting grid, ready for the countdown."""
        for rival in self.rivals:
            car = rival.car
            car.set_driver(True)
            car.hitbox.center = rival.spawn
            car.pos = pygame.Vector2(car.hitbox.center)
            car.rect.center = car.hitbox.center
            car.angle = rival.angle
            car.rotation_speed = 250
            car.acceleration = rival.acceleration
            car.brake = 1900
            car.road_speed = rival.road_speed
            car.speed = 0
            car.direction = 0
            car.active = False
            car.reverse_active = False
            car.push_remainder = pygame.Vector2()
            car.image, car.rect, car.mask, car.collision_mask = car.build_image(car.angle)
            car.get_rotation()
            rival.reset()

        self.race_state = "waiting"

    def _finish_race(self, player_won):
        self.race_state = "finished"
        self.player_won = player_won
        self.race_result = self.race["win"] if player_won else self.race["lose"]
        self.race_result_timer = 5.0
        for rival in self.rivals:
            rival.car.active = False
            rival.car.reverse_active = False
            rival.car.direction = 0

    def _race_won(self):
        # Leave the Mission 3 rival in place for Mission 4, but clear the grid after Mission 4.
        if self.number == 4:
            for car in self.racing_cars():
                car.active = False
                car.reverse_active = False
                car.direction = 0
                car.speed = 0
                car.collision_velocity = pygame.Vector2()
                car.set_driver(False)
                car.hitbox.center = (-1000, -1000)
                car.pos = pygame.Vector2(car.hitbox.center)
                car.rect.center = car.hitbox.center
            self.rivals = []

        # Reuse the normal "MISSION COMPLETE!" banner, then the next mission starts.
        self.race_state = "done"
        self.completed = True
        self.completion_time = pygame.time.get_ticks()
        self.complete_timer = 2

    def _advance_rival(self, rival):
        """Next waypoint; returns False once the rival has finished its last lap."""
        rival.waypoint_index += 1
        if rival.waypoint_index >= len(rival.waypoints):
            if rival.lap < self.race["laps"]:
                rival.lap += 1
                rival.waypoint_index = 0
            else:
                return False
        return True

    def _drive_rival(self, rival):
        car = rival.car

        target = pygame.Vector2(rival.waypoints[rival.waypoint_index])
        to_target = target - pygame.Vector2(car.rect.center)
        if to_target.length() < rival.reach:
            if not self._advance_rival(rival):
                self._finish_race(False)
                return
            target = pygame.Vector2(rival.waypoints[rival.waypoint_index])
            to_target = target - pygame.Vector2(car.rect.center)

        desired_angle = math.degrees(math.atan2(-to_target.x, -to_target.y))
        angle_difference = (desired_angle - car.angle + 180) % 360 - 180
        if abs(angle_difference) < 3:
            car.direction = 0
        else:
            car.direction = 1 if angle_difference < 0 else -1

        turn_size = abs(angle_difference)
        if turn_size > 110:
            target_speed = 500 * rival.corner_scale
        elif turn_size > 70:
            target_speed = 650 * rival.corner_scale
        elif turn_size > 35:
            target_speed = 780 * rival.corner_scale
        else:
            target_speed = car.road_speed

        if car.speed > target_speed + 45:
            # Brake before a tight turn, then accelerate hard out of it.
            car.active = True
            car.reverse_active = True
        else:
            car.active = car.speed < target_speed
            car.reverse_active = False

    # ------------------------------------------------------------------
    # race state machine (missions 3 and 4)
    # ------------------------------------------------------------------
    def _update_race(self, player, dt):
        if self.race is not self.race_configs[self.number]:
            self._begin_race()

        if self.race_state == "locked":
            # (Re)grid the rivals as soon as nobody is parked on their spots.
            if self._grid_is_clear(player):
                self._place_rivals()

        elif self.race_state == "waiting":
            if (player.in_car and player.current_car
                    and player.current_car.rect.colliderect(self.race["start"])):
                self.race_state = "countdown"
                self.race_countdown = 3.0
                self.player_checkpoint_index = 0
                self.player_lap = 1
                for rival in self.rivals:
                    rival.reset()

        elif self.race_state == "countdown":
            if player.current_car:
                player.current_car.active = False
                player.current_car.reverse_active = False
                player.current_car.direction = 0
                player.current_car.speed = 0
            self.race_countdown -= dt
            if self.race_countdown <= 0:
                self.race_state = "running"
                for rival in self.rivals:
                    rival.car.active = True

        elif self.race_state == "running":
            for rival in self.rivals:
                self._drive_rival(rival)
                if self.race_state != "running":
                    break

            if self.race_state == "running" and player.in_car and player.current_car:
                checkpoints = self.race["checkpoints"]
                if self.player_checkpoint_index < len(checkpoints):
                    if player.current_car.rect.colliderect(checkpoints[self.player_checkpoint_index]):
                        self.player_checkpoint_index += 1
                elif player.current_car.rect.colliderect(self.race["finish"]):
                    if self.player_lap < self.race["laps"]:
                        self.player_lap += 1
                        self.player_checkpoint_index = 0
                    else:
                        self._finish_race(True)

        elif self.race_state == "finished":
            self.race_result_timer = max(0.0, self.race_result_timer - dt)
            if self.race_result_timer == 0:
                self.race_result = ""
                if self.player_won:
                    self._race_won()      # victory: on to the next mission
                else:
                    self.race_state = "locked"   # defeat: back to the start line to try again

    def update(self, player, dt):
        if self.number == 1:
            if not self.completed and not player.in_car and player.hitbox.colliderect(self.destination):
                self.completed = True
                self.completion_time = pygame.time.get_ticks()
                self.complete_timer = 2

        elif self.number == 2:
            if (not self.completed and player.in_car and player.current_car
                    and player.current_car.rect.colliderect(self.destination2)):
                self.completed = True
                self.completion_time = pygame.time.get_ticks()
                self.complete_timer = 2

        elif self.number in self.race_configs:
            self._update_race(player, dt)

        if self.completed:
            self.complete_timer -= dt
            if self.complete_timer <= 0:
                self.completed = False
                self.number += 1

        if self.number > max(self.race_configs):
            if self.all_complete_timer is None:
                self.all_complete_timer = 5.0
            else:
                self.all_complete_timer = max(0.0, self.all_complete_timer - dt)

    def draw(self, surface, camera):
        if self.number == 3 and self.race_state in ("waiting", "countdown", "running"):
            start = self.race_configs[3]["start"]
            cell = 20
            stripe_x = self.race_configs[3]["stripe_x"] - cell

            for row in range(start.height // cell):
                for col in range(2):
                    color = (240, 240, 240) if (row + col) % 2 == 0 else (20, 20, 20)
                    screen_x = round((stripe_x + col * cell - camera.offset.x) * ZOOM)
                    screen_y = round((start.y + row * cell - camera.offset.y) * ZOOM)
                    size = round(cell * ZOOM)
                    pygame.draw.rect(surface, color, (screen_x, screen_y, size, size))
                    
        destination = self.current_destination()
        if destination is None:
            return

        position = (
            destination.x * ZOOM - camera.offset.x * ZOOM,
            destination.y * ZOOM - camera.offset.y * ZOOM
        )
        size = (int(destination.width * ZOOM), int(destination.height * ZOOM))
        pygame.draw.rect(surface, (100, 0, 255), (*position, *size), 5)

    def draw_ui(self, surface):
        if self.completed:
            elapsed = pygame.time.get_ticks() - self.completion_time
            if elapsed < 2000:
                message = "MISSION COMPLETE!"
            else:
                return
        elif self.number == 1:
            message = "MISSION 1: Walk to the marked location"
        elif self.number == 2:
            message = "MISSION 2: Drive to the marked location"
        elif self.number in self.race_configs:
            config = self.race_configs[self.number]
            if self.race_state in ("locked", "waiting"):
                message = config["intro"]
            elif self.race_state == "countdown":
                message = f"RACE STARTS IN {max(1, math.ceil(self.race_countdown))}"
            elif self.race_state == "running":
                if self.player_checkpoint_index < len(config["checkpoints"]):
                    message = f"LAP {self.player_lap}/{config['laps']} - CHECKPOINT {self.player_checkpoint_index + 1}/{len(config['checkpoints'])}"
                else:
                    message = f"LAP {self.player_lap}/{config['laps']} - RETURN TO START/FINISH"
            else:
                if not self.race_result:
                    return
                message = self.race_result
        elif self.number > max(self.race_configs):
            if self.all_complete_timer is None or self.all_complete_timer > 0:
                message = "ALL MISSIONS COMPLETE!"
            else:
                return
        else:
            return

        text = font.render(message, True, (255, 255, 255))
        surface.blit(text, (30, 30))

    def current_destination(self):
        if self.completed:
            return None
        if self.number == 1:
            return self.destination
        if self.number == 2:
            return self.destination2
        if self.number in self.race_configs:
            config = self.race_configs[self.number]
            if self.race_state == "waiting":
                return config["start"]
            if self.race_state == "running":
                if self.player_checkpoint_index < len(config["checkpoints"]):
                    return config["checkpoints"][self.player_checkpoint_index]
                return config["finish"]
        return None


# INIT
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
pygame.mouse.set_visible(False)
clock = pygame.time.Clock() # used for creating dt only
font = pygame.font.Font(None, 40)

day_night = DayNightCycle((SCREEN_WIDTH, SCREEN_HEIGHT))

# GAME SETUP
revenge_track = RevengeRaceTrack()
world = World(revenge_track)
weather = WeatherSystem((SCREEN_WIDTH, SCREEN_HEIGHT), DAY_LENGTH_SECONDS, START_HOUR, world.rect.size)
camera_group = CameraGroup(world)
mission = Mission(revenge_track)

for tree in world.trees:
    camera_group.add(tree)
camera_group.add(*world.street_lamp_sprites)

# SOUND SETUP
bg_birdsounds = pygame.mixer.Sound("sounds/morning_birds.mp3")
bg_birdsounds.play(loops = -1)
bg_birdsounds.set_volume(0)
owl_ambience = pygame.mixer.Sound("sounds/owl.mp3")
owl_ambience_channel = owl_ambience.play(loops=-1)
if owl_ambience_channel:
    owl_ambience_channel.set_volume(0)

tractor_engine_sound = pygame.mixer.Sound("sounds/tractor_engine_loop.wav")
tractor_engine_sound.set_volume(0)

buggy_engine_sound = pygame.mixer.Sound("sounds/buggy_engine_loop.wav")
buggy_engine_sound.set_volume(0)

# VEHICLE GRAPHICS
buggy = "graphics/buggy/buggy.png"
buggy_driver = "graphics/buggy/buggy_with_player.png"

tractor = "graphics/tractor/tractor_1.png"
tractor_driver = "graphics/tractor/tractor_with_player_1.png"

# WHEEL ANIMATION SETUP
TRACTOR_WHEEL_BOUNDS = [
    (27, 28, 63, 98),
    (136, 28, 172, 98),
    (2, 150, 51, 260),
    (147, 150, 197, 260),
]
TRACTOR_SIZE = (199, 263)

# All buggies share the same sprite layout (157 x 220)
BUGGY_WHEEL_BOUNDS = [
    (3, 16, 33, 71),      # front left
    (124, 16, 154, 71),   # front right
    (4, 143, 33, 194),    # rear left
    (124, 143, 153, 194), # rear right
]
BUGGY_SIZE = (157, 220)

# VEHICLE SETUP
tractor_car = Car((5000, 2500), world, tractor, (-100, -100), 300, 300, tractor_driver,
                  TRACTOR_WHEEL_BOUNDS, TRACTOR_SIZE)

cars = [
    Car((4800, 3570), world, buggy, (-50, -50), 1200, 1200, buggy_driver,
        BUGGY_WHEEL_BOUNDS, BUGGY_SIZE),
    Car((2900, 3300), world, "graphics/circlus_grey.png", (-20, -20), 900, 500),
    tractor_car,
    Car((2900, 1000), world, "graphics/Jeep.png", (-60,-60), 1000, 1000),
    Car((2700, 1000), world, "graphics/bouboul.png", (-20, -20), 600, 300),
    Car((3430, 1500), world, "graphics/audi_v2.png", (-20, -20), 900, 500),
    Car((3430, 2200), world, "graphics/audi_v3.png", (-20, -20), 900, 500),
    Car((3430, 2000), world, "graphics/circlus_red.png", (-20, -20), 900, 500)
]

# Race rivals wait off the map until their mission starts.
race_rival_car = Car((-1000, -1000), world, "graphics/buggy/rival_buggy.png", (-50, -50), 900, 600,
                     wheel_bounds=BUGGY_WHEEL_BOUNDS, reference_size=BUGGY_SIZE)
race_rival_car_2 = Car((-1000, -1400), world, RIVAL_2_IMAGE, (-50, -50), 900, 600,
                       wheel_bounds=BUGGY_WHEEL_BOUNDS, reference_size=BUGGY_SIZE)
cars.append(race_rival_car)
cars.append(race_rival_car_2)
mission.rival_car = race_rival_car
mission.rival_car_2 = race_rival_car_2
mission.cars = cars

cars[0].angle = -90
cars[0].image, cars[0].rect, cars[0].mask, cars[0].collision_mask = cars[0].build_image(cars[0].angle)
cars[0].get_rotation()

cars[0].engine_sound = buggy_engine_sound
tractor_car.engine_sound = tractor_engine_sound

cars[0].engine_gain = 1.0       # buggy
tractor_car.engine_gain = 1.0   # tractor

# every car plays its own looping engine sound, so make sure there are enough mixer channels
pygame.mixer.set_num_channels(len(cars) + 4)

for car in cars:
    if car.engine_sound is None:
        car.engine_sound = pygame.mixer.Sound("sounds/car_engine_loop.ogg")
        car.engine_sound.play(loops=-1)
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

world.draw_map()
world.scaled_surface = pygame.transform.scale(
    world.surface,
    (
        int(world.surface.get_width() * ZOOM),
        int(world.surface.get_height() * ZOOM)
    )
)

minimap = Minimap(world)


# CAMERA SETUP
for car in cars:
    camera_group.add(car)

camera_group.add(player)
tractor_smoke_particles = []
tractor_smoke_timer = 0.0

camera_target = player

debug_menu_open = False
debug_selected_mission = 0

def start_debug_mission(number):
    global camera_target

    mission.number = number
    mission.completed = False
    mission.complete_timer = 0
    mission.all_complete_timer = None
    mission.race = None
    mission.rivals = []
    mission.race_state = "locked"
    mission.race_countdown = 0.0
    mission.race_result = ""
    mission.race_result_timer = 0.0
    mission.player_won = False
    mission.player_checkpoint_index = 0
    mission.player_lap = 1

    # Park every rival off-screen; the selected race will place its opponents.
    for rival_car in mission.rival_cars:
        rival_car.active = False
        rival_car.reverse_active = False
        rival_car.direction = 0
        rival_car.speed = 0
        rival_car.collision_velocity = pygame.Vector2()
        rival_car.set_driver(False)
        rival_car.hitbox.center = (-1000, -1000)
        rival_car.pos = pygame.Vector2(rival_car.hitbox.center)
        rival_car.rect.center = rival_car.hitbox.center

    # Return the player to walking mode before positioning for the chosen mission.
    if player.current_car:
        player.current_car.active = False
        player.current_car.reverse_active = False
        player.current_car.direction = 0
        player.current_car.speed = 0
        player.current_car.set_driver(False)
    player.in_car = False
    player.current_car = None
    player.hitbox.midbottom = (4350, 1000)
    player.pos = pygame.Vector2(player.hitbox.topleft)
    player.rect.midbottom = player.hitbox.midbottom
    player.movement = pygame.Vector2()
    camera_group.add(player)
    camera_target = player

    if number == 1:
        return

    test_car = cars[0]
    test_car.active = False
    test_car.reverse_active = False
    test_car.direction = 0
    test_car.speed = 0
    test_car.collision_velocity = pygame.Vector2()
    test_car.push_remainder = pygame.Vector2()
    test_car.set_driver(True)

    if number == 2:
        spawn = (3050, 3500)
        angle = 90
    elif number == 3:
        spawn = (3550, 3350)
        angle = -90
    else:
        start = mission.race_configs[4]["start"]
        spawn = (start.centerx + 50, start.centery)
        angle = 90

    test_car.hitbox.center = spawn
    test_car.pos = pygame.Vector2(test_car.hitbox.center)
    test_car.angle = angle
    test_car.image, test_car.rect, test_car.mask, test_car.collision_mask = test_car.build_image(angle)
    test_car.get_rotation()
    player.in_car = True
    player.current_car = test_car
    player.kill()
    camera_target = test_car

def draw_debug_menu(surface, selected):
    shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    shade.fill((0, 0, 0, 175))
    surface.blit(shade, (0, 0))

    panel = pygame.Rect(0, 0, 580, 330)
    panel.center = surface.get_rect().center
    pygame.draw.rect(surface, (35, 40, 48), panel)
    pygame.draw.rect(surface, (220, 225, 235), panel, 2)

    title = font.render("DEBUG MENU - SELECT MISSION", True, (255, 230, 120))
    surface.blit(title, (panel.x + 28, panel.y + 22))
    options = [
        "Mission 1 - Walk to location",
        "Mission 2 - Drive to location",
        "Mission 3 - Two-lap race",
        "Mission 4 - The revenge",
    ]
    for index, option in enumerate(options):
        color = (255, 240, 130) if index == selected else (240, 240, 240)
        prefix = "> " if index == selected else "  "
        label = font.render(prefix + option, True, color)
        surface.blit(label, (panel.x + 30, panel.y + 78 + index * 48))

    hint = font.render("ENTER: start   ESC: close", True, (190, 200, 210))
    surface.blit(hint, (panel.x + 28, panel.bottom - 45))

# GAME LOOP
while True:

    # DT
    dt = clock.tick() / 1000


    # EVENTS
    for event in pygame.event.get():


        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if debug_menu_open:
                debug_menu_open = False
            else:
                pygame.quit()
                sys.exit()
            continue

        if event.type == pygame.KEYDOWN and event.key == pygame.K_1:
            debug_menu_open = not debug_menu_open
            if debug_menu_open:
                for car in cars:
                    car.active = False
                    car.reverse_active = False
            continue

        if debug_menu_open:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    debug_selected_mission = (debug_selected_mission - 1) % 4
                elif event.key == pygame.K_DOWN:
                    debug_selected_mission = (debug_selected_mission + 1) % 4
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    start_debug_mission(debug_selected_mission + 1)
                    debug_menu_open = False
            continue


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
                        if car in mission.rival_cars:
                            continue
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

    if debug_menu_open:
        dt = 0

    # UPDATE
    day_night.update(dt)
    weather.update(dt)
    tractor_previous_center = pygame.Vector2(tractor_car.rect.center)
    for car in cars:
        car.update(cars, dt)

    tractor_motion = pygame.Vector2(tractor_car.rect.center) - tractor_previous_center
    if dt > 0 and tractor_motion.length_squared() > 0.25:
        tractor_smoke_timer += dt
        travel_direction = tractor_motion.normalize()
        exhaust_offset = pygame.Vector2(18, -90).rotate(-tractor_car.angle)
        exhaust_position = pygame.Vector2(tractor_car.rect.center) + exhaust_offset
        sideways = pygame.Vector2(-travel_direction.y, travel_direction.x)
        while tractor_smoke_timer >= 0.055:
            tractor_smoke_timer -= 0.055
            smoke_velocity = (
                -travel_direction * random.uniform(20, 38)
                + sideways * random.uniform(-10, 10)
            )
            puff = SmokeParticle(
                exhaust_position,
                smoke_velocity,
                random.uniform(0.85, 1.0),
            )
            tractor_smoke_particles.append(puff)
    else:
        tractor_smoke_timer = 0.0

    for puff in tractor_smoke_particles[:]:
        if not puff.update(dt):
            tractor_smoke_particles.remove(puff)

    player.update(cars, dt)
    mission.update(player, dt)

    # Fade birdsound out as evening falls, keep it silent overnight, and bring
    # it back gradually at dawn.
    hour = day_night.hour
    if BIRDSOUND_FADE_START_HOUR <= hour < BIRDSOUND_SILENT_HOUR:
        bird_volume = 1 - (hour - BIRDSOUND_FADE_START_HOUR) / (
            BIRDSOUND_SILENT_HOUR - BIRDSOUND_FADE_START_HOUR
        )
    elif hour >= BIRDSOUND_SILENT_HOUR or hour < BIRDSOUND_START_HOUR:
        bird_volume = 0.0
    elif BIRDSOUND_START_HOUR <= hour < BIRDSOUND_FULL_HOUR:
        bird_volume = (hour - BIRDSOUND_START_HOUR) / (
            BIRDSOUND_FULL_HOUR - BIRDSOUND_START_HOUR
        )
    else:
        bird_volume = 1.0
    bg_birdsounds.set_volume(bird_volume)

    if OWL_FADE_START_HOUR <= hour < OWL_FULL_VOLUME_HOUR:
        owl_volume = OWL_AMBIENCE_VOLUME * (
            (hour - OWL_FADE_START_HOUR) / (OWL_FULL_VOLUME_HOUR - OWL_FADE_START_HOUR)
        )
    elif hour >= OWL_FULL_VOLUME_HOUR or hour < OWL_FADE_OUT_START_HOUR:
        owl_volume = OWL_AMBIENCE_VOLUME
    elif OWL_FADE_OUT_START_HOUR <= hour < OWL_SILENT_HOUR:
        owl_volume = OWL_AMBIENCE_VOLUME * (
            1 - (hour - OWL_FADE_OUT_START_HOUR) / (OWL_SILENT_HOUR - OWL_FADE_OUT_START_HOUR)
        )
    else:
        owl_volume = 0.0

    if owl_ambience_channel:
        owl_ambience_channel.set_volume(owl_volume)


    # ENGINE SOUND
    racing_cars = mission.racing_cars()
    for car in cars:
        target_volume = 0

        if player.in_car and player.current_car is car:
            if car.active or car.reverse_active:
                target_volume = 0.25  # pedal pressed
            elif car.speed != 0:
                target_volume = 0.1  # coasting
        elif car in racing_cars and mission.race_state == "running" and car.speed != 0:
            target_volume = 0.12

        target_volume = min(1.0, target_volume * car.engine_gain)

        # smooth fade so it doesn't cut abruptly
        car.engine_volume += (target_volume - car.engine_volume) * min(1, 8 * dt)
        car.engine_sound.set_volume(car.engine_volume)

    # DRAW
    camera_group.custom_draw(camera_target)
    for puff in tractor_smoke_particles:
        puff.draw(screen, camera_group)
    world.draw_overhead_cables(screen, camera_group)
    weather.draw(screen, camera_group)
    day_night.draw(screen)  # tint the world once; keep UI clear
    world.draw_street_lamp_light(screen, camera_group, day_night.hour)

    mission.draw(screen, camera_group)
    mission.draw_ui(screen)
    minimap.draw(screen, camera_target, mission)

    if debug_menu_open:
        draw_debug_menu(screen, debug_selected_mission)

    pygame.display.update()
