import json
import arcade
from pyglet import gl
from arcade.hitbox import SimpleHitBoxAlgorithm

# ко
SURFACE_FLOOR = 0
SURFACE_RIGHT = 90
SURFACE_CEILING = 180
SURFACE_LEFT = 270
SURFACE_AIR = -1

BASE_TILE_SIZE = 64
GLOBAL_SCALE = 0.5
TILE_SIZE = BASE_TILE_SIZE * GLOBAL_SCALE


class SnailPlayer(arcade.Sprite):
    def __init__(self, textures_right, textures_left, scale):
        super().__init__(textures_right[0], scale=scale)

        self.textures_right = textures_right
        self.textures_left = textures_left

        self.current_texture_index = 0
        self.time_since_last_frame = 0
        self.animation_speed = 0.15

        self.move_speed = 4
        self.jump_force = 9
        self.gravity = 0.4

        self.surface_state = SURFACE_FLOOR
        self.vel_x = 0
        self.vel_y = 0

        self.was_in_air = False

    def update_movement(self, blocks_list, keys_pressed, particle_system):
        check_dist = 4

        on_floor = self.check_collision_offset(blocks_list, 0, -check_dist)
        on_ceiling = self.check_collision_offset(blocks_list, 0, check_dist)
        on_left_wall = self.check_collision_offset(blocks_list, -check_dist, 0)
        on_right_wall = self.check_collision_offset(blocks_list, check_dist, 0)

        if on_floor:
            self.surface_state = SURFACE_FLOOR
            self.angle = 0
        elif on_right_wall:
            self.surface_state = SURFACE_RIGHT
            self.angle = 270
        elif on_ceiling:
            self.surface_state = SURFACE_CEILING
            self.angle = 180
        elif on_left_wall:
            self.surface_state = SURFACE_LEFT
            self.angle = 90
        else:
            self.surface_state = SURFACE_AIR

        if self.surface_state != SURFACE_AIR and self.was_in_air:
            particle_system.create_dust(self.center_x, self.center_y, self.surface_state)
            self.was_in_air = False
        elif self.surface_state == SURFACE_AIR:
            self.was_in_air = True

        left_active = keys_pressed.get(arcade.key.A) or keys_pressed.get(arcade.key.LEFT)
        right_active = keys_pressed.get(arcade.key.D) or keys_pressed.get(arcade.key.RIGHT)

        is_moving = False
        active_textures = self.textures_right

        if self.surface_state == SURFACE_FLOOR:
            move_x = 0
            if left_active:
                move_x = -self.move_speed
                active_textures = self.textures_left
                is_moving = True
            if right_active:
                move_x = self.move_speed
                active_textures = self.textures_right
                is_moving = True
            self.vel_x = move_x

        elif self.surface_state == SURFACE_CEILING:
            move_x = 0
            if left_active:
                move_x = -self.move_speed
                active_textures = self.textures_right
                is_moving = True
            if right_active:
                move_x = self.move_speed
                active_textures = self.textures_left
                is_moving = True
            self.vel_x = move_x

        elif self.surface_state == SURFACE_LEFT:
            move_y = 0
            if left_active:
                move_y = self.move_speed
                active_textures = self.textures_left
                is_moving = True
            if right_active:
                move_y = -self.move_speed
                active_textures = self.textures_right
                is_moving = True
            self.vel_y = move_y

        elif self.surface_state == SURFACE_RIGHT:
            move_y = 0
            if left_active:
                move_y = -self.move_speed
                active_textures = self.textures_left
                is_moving = True
            if right_active:
                move_y = self.move_speed
                active_textures = self.textures_right
                is_moving = True
            self.vel_y = move_y

        elif self.surface_state == SURFACE_AIR:
            self.vel_y -= self.gravity
            if left_active:
                self.vel_x = -self.move_speed
                active_textures = self.textures_left
            if right_active:
                self.vel_x = self.move_speed
                active_textures = self.textures_right

        if is_moving and self.surface_state != SURFACE_AIR:
            self.time_since_last_frame += 1 / 60
            if self.time_since_last_frame >= self.animation_speed:
                self.time_since_last_frame = 0
                self.current_texture_index = (self.current_texture_index + 1) % len(active_textures)
            self.texture = active_textures[self.current_texture_index]
        else:
            self.texture = active_textures[0]

        self.center_x += self.vel_x
        hit_x = arcade.check_for_collision_with_list(self, blocks_list)
        for block in hit_x:
            if self.vel_x > 0:
                self.right = block.left
            elif self.vel_x < 0:
                self.left = block.right
            if self.surface_state == SURFACE_AIR:
                self.vel_x = 0

        self.center_y += self.vel_y
        hit_y = arcade.check_for_collision_with_list(self, blocks_list)
        for block in hit_y:
            if self.vel_y > 0:
                self.top = block.bottom
            elif self.vel_y < 0:
                self.bottom = block.top
            if self.surface_state == SURFACE_AIR:
                self.vel_y = 0

    def jump(self):
        if self.surface_state == SURFACE_FLOOR:
            self.vel_y = self.jump_force
            self.surface_state = SURFACE_AIR
        elif self.surface_state == SURFACE_CEILING:
            self.vel_y = -self.jump_force
            self.surface_state = SURFACE_AIR
        elif self.surface_state == SURFACE_LEFT:
            self.vel_x = self.jump_force
            self.vel_y = self.jump_force * 0.7
            self.surface_state = SURFACE_AIR
        elif self.surface_state == SURFACE_RIGHT:
            self.vel_x = -self.jump_force
            self.vel_y = self.jump_force * 0.7
            self.surface_state = SURFACE_AIR

    def check_collision_offset(self, blocks_list, offset_x, offset_y):
        self.center_x += offset_x
        self.center_y += offset_y
        hit = arcade.check_for_collision_with_list(self, blocks_list)
        self.center_x -= offset_x
        self.center_y -= offset_y
        return len(hit) > 0


class ParticleSystem:
    def __init__(self):
        self.particles = arcade.SpriteList()

    def create_dust(self, x, y, surface_state):
        for _ in range(5):
            particle = arcade.SpriteCircle(radius=3, color=arcade.color.LIGHT_GRAY)
            particle.center_x = x
            particle.center_y = y

            import random
            if surface_state == SURFACE_FLOOR:
                particle.change_x = random.uniform(-2, 2)
                particle.change_y = random.uniform(0.5, 2)
            elif surface_state == SURFACE_CEILING:
                particle.change_x = random.uniform(-2, 2)
                particle.change_y = random.uniform(-2, -0.5)
            elif surface_state == SURFACE_LEFT:
                particle.change_x = random.uniform(0.5, 2)
                particle.change_y = random.uniform(-2, 2)
            elif surface_state == SURFACE_RIGHT:
                particle.change_x = random.uniform(-2, -0.5)
                particle.change_y = random.uniform(-2, 2)

            particle.alpha = 255
            self.particles.append(particle)

    def update(self):
        for p in self.particles:
            p.center_x += p.change_x
            p.center_y += p.change_y
            p.alpha -= 8
            if p.alpha <= 0:
                p.remove_from_sprite_lists()

    def draw(self):
        self.particles.draw()


class GameLevel(arcade.View):
    def __init__(self, level_id, game_progress, return_to_menu_callback):
        super().__init__()
        self.level_id = level_id
        self.game_progress = game_progress
        self.return_to_menu_callback = return_to_menu_callback
        self.level_data = game_progress[level_id]

        self.scene = None
        self.player_sprite = None
        self.keys_pressed = {}

        self.has_key = False
        self.level_complete_timer = -1.0

        self.camera = arcade.camera.Camera2D(arcade.LBWH(0, 0, self.window.width, self.window.height))
        self.gui_camera = arcade.camera.Camera2D(arcade.LBWH(0, 0, self.window.width, self.window.height))
        self.particle_system = ParticleSystem()

        self.sound_banana = arcade.load_sound("assets/sounds/banana.mp3")
        self.sound_key = arcade.load_sound("assets/sounds/key.mp3")
        self.sound_door_open = arcade.load_sound("assets/sounds/door_open.mp3")
        self.sound_locked = arcade.load_sound("assets/sounds/locked.mp3")

        self.level_title_text = arcade.Text(
            text=f"{self.level_data['name'].upper()}",
            x=20,
            y=560,
            color=arcade.color.WHITE,
            font_size=18,
            bold=True
        )

    def on_show_view(self):
        arcade.set_background_color(arcade.color.CORNFLOWER_BLUE)

        hb_algorithm = SimpleHitBoxAlgorithm()

        crate_texture = arcade.load_texture("assets/images/box.png", hit_box_algorithm=hb_algorithm)
        crate_texture.image.texture_filter = gl.GL_NEAREST

        gem_texture = arcade.load_texture("assets/images/banana.png", hit_box_algorithm=hb_algorithm)
        gem_texture.image.texture_filter = gl.GL_NEAREST

        key_texture = arcade.load_texture("assets/images/key.png", hit_box_algorithm=hb_algorithm)
        key_texture.image.texture_filter = gl.GL_NEAREST

        door_texture = arcade.load_texture("assets/images/door.png", hit_box_algorithm=hb_algorithm)
        door_texture.image.texture_filter = gl.GL_NEAREST

        self.door_open_texture = arcade.load_texture("assets/images/door_open.png", hit_box_algorithm=hb_algorithm)
        self.door_open_texture.image.texture_filter = gl.GL_NEAREST

        block_scale = TILE_SIZE / crate_texture.width
        banana_scale = TILE_SIZE / gem_texture.width
        key_scale = TILE_SIZE / key_texture.width
        door_scale = TILE_SIZE / door_texture.width

        self.scene = arcade.Scene()
        blocks_list = arcade.SpriteList(use_spatial_hash=True)
        objects_list = arcade.SpriteList()

        banana_index = 0

        map_path = f"levels/{self.level_id}.json"
        with open(map_path, "r", encoding="utf-8") as f:
            map_data = json.load(f)

        map_width = map_data["width"]
        map_height = map_data["height"]

        snail_r1 = arcade.load_texture("assets/images/snail.png")
        snail_r2 = arcade.load_texture("assets/images/snail2.png")

        snail_l1 = arcade.load_texture("assets/images/snail_left.png")
        snail_l2 = arcade.load_texture("assets/images/snail2_left.png")

        snail_r1.image.texture_filter = gl.GL_NEAREST
        snail_r2.image.texture_filter = gl.GL_NEAREST
        snail_l1.image.texture_filter = gl.GL_NEAREST
        snail_l2.image.texture_filter = gl.GL_NEAREST

        textures_right = [snail_r1, snail_r2]
        textures_left = [snail_l1, snail_l2]

        for layer in map_data["layers"]:
            if layer["name"] == "blocks" and layer["type"] == "tilelayer":
                data = layer["data"]
                for index, tile_id in enumerate(data):
                    if tile_id == 1:
                        grid_x = index % map_width
                        grid_y = index // map_width

                        pos_x = (grid_x * TILE_SIZE) + (TILE_SIZE / 2)
                        pos_y = ((map_height - 1 - grid_y) * TILE_SIZE) + (TILE_SIZE / 2)

                        block_sprite = arcade.Sprite(crate_texture, scale=block_scale)
                        block_sprite.center_x = pos_x
                        block_sprite.center_y = pos_y
                        blocks_list.append(block_sprite)

            elif layer["name"] == "objects" and layer["type"] == "objectgroup":
                for obj in layer["objects"]:
                    obj_type = ""
                    if "properties" in obj:
                        for prop in obj["properties"]:
                            if prop["name"] == "type":
                                obj_type = prop["value"]

                    obj_x = obj["x"] * TILE_SIZE
                    obj_y = (map_height - obj["y"] - 1) * TILE_SIZE

                    center_x = obj_x + (TILE_SIZE / 2)
                    center_y = obj_y + (TILE_SIZE / 2)

                    if obj_type == "player":
                        self.player_sprite = SnailPlayer(textures_right, textures_left,
                                                         scale=TILE_SIZE / snail_r1.width)
                        self.player_sprite.center_x = center_x
                        self.player_sprite.center_y = center_y

                    elif obj_type == "banana":
                        banana_sprite = arcade.Sprite(gem_texture, scale=banana_scale)
                        banana_sprite.center_x = center_x
                        banana_sprite.center_y = center_y
                        banana_sprite.properties["is_banana"] = True
                        banana_sprite.properties["index"] = banana_index
                        banana_index += 1
                        objects_list.append(banana_sprite)

                    elif obj_type == "key":
                        key_sprite = arcade.Sprite(key_texture, scale=key_scale)
                        key_sprite.center_x = center_x
                        key_sprite.center_y = center_y
                        key_sprite.properties["is_key"] = True
                        objects_list.append(key_sprite)

                    elif obj_type == "door":
                        door_sprite = arcade.Sprite(door_texture, scale=door_scale)
                        door_sprite.center_x = center_x
                        door_sprite.center_y = center_y
                        door_sprite.properties["is_door"] = True
                        objects_list.append(door_sprite)

        self.scene.add_sprite_list("blocks", sprite_list=blocks_list)
        self.scene.add_sprite_list("objects", sprite_list=objects_list)

        if self.player_sprite is None:
            self.player_sprite = SnailPlayer(textures_right, textures_left, scale=TILE_SIZE / snail_r1.width)
            self.player_sprite.center_x = TILE_SIZE * 1.5
            self.player_sprite.center_y = TILE_SIZE * 1.5

        self.scene.add_sprite("player", self.player_sprite)
        self.level_title_text.y = self.window.height - 40

    def scroll_to_player(self):
        if not self.player_sprite:
            return

        target_x = self.player_sprite.center_x
        target_y = self.player_sprite.center_y

        camera_position = (target_x, target_y)
        self.camera.position = camera_position

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.return_to_menu_callback()

        if self.level_complete_timer > 0:
            return

        self.keys_pressed[key] = True

        if key == arcade.key.SPACE and self.player_sprite:
            self.player_sprite.jump()

    def on_key_release(self, key, modifiers):
        self.keys_pressed[key] = False

    def on_update(self, delta_time):
        if self.level_complete_timer > 0:
            self.level_complete_timer -= delta_time
            if self.level_complete_timer <= 0:
                self.return_to_menu_callback()
            return

        if self.player_sprite and self.scene:
            try:
                blocks = self.scene.get_sprite_list("blocks")
                self.player_sprite.update_movement(blocks, self.keys_pressed, self.particle_system)
            except KeyError:
                pass

        self.particle_system.update()
        self.scroll_to_player()

        if self.scene and self.player_sprite:
            try:
                objects = self.scene.get_sprite_list("objects")
                if objects:
                    hit_list = arcade.check_for_collision_with_list(self.player_sprite, objects)
                    for item in hit_list:
                        if item.properties.get("is_banana"):
                            banana_index = item.properties.get('index')
                            self.level_data["collected"] = (self.level_data["collected"][:banana_index] + '1'
                                                            + self.level_data["collected"][banana_index + 1:])
                            item.remove_from_sprite_lists()
                            arcade.play_sound(self.sound_banana)

                        elif item.properties.get("is_key"):
                            item.remove_from_sprite_lists()
                            self.has_key = True
                            arcade.play_sound(self.sound_key)

                        elif item.properties.get("is_door"):
                            if self.has_key:
                                item.texture = self.door_open_texture
                                self.player_sprite.visible = False
                                self.level_data["passed"] = True
                                arcade.play_sound(self.sound_door_open)
                                self.level_complete_timer = 1.0
            except KeyError:
                pass

    def on_draw(self):
        self.clear()

        self.camera.use()
        if self.scene:
            self.scene.draw()
        self.particle_system.draw()

        self.gui_camera.use()
        self.level_title_text.draw()