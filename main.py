import json
import os
import arcade
import arcade.gui
from game import GameLevel

# константы настройки экрана
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Banana Snail"

# стандартный прогресс на случай, если файл сохранения не найден
DEFAULT_PROGRESS = {
    "level_1": {"name": "Уровень 1", "collected": "000", "passed": False},
    "level_2": {"name": "Уровень 2", "collected": "000", "passed": False},
    "level_3": {"name": "Уровень 3", "collected": "000", "passed": False},
}


# загрузка прогресса
def load_progress():
    if os.path.exists("save.json"):
        try:
            with open("save.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_PROGRESS
    return DEFAULT_PROGRESS


# сохранение прогресса
def save_progress(progress):
    with open("save.json", "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=4)


GAME_PROGRESS = load_progress()


# класс кнопки меню
class MultilineButton(arcade.gui.UIFlatButton):
    def __init__(self, **kwargs):
        display_text = kwargs.pop("text", "")

        super().__init__(text="", **kwargs)

        self.label_element = arcade.gui.UILabel(
            text=display_text,
            font_name=kwargs.get("style", {}).get("font_name", "Arial"),
            font_size=kwargs.get("style", {}).get("font_size", 14),
            text_color=arcade.color.WHITE,
            multiline=True,
            align="center",
            width=kwargs.get("width", 160) - 20
        )

        layout = arcade.gui.UIAnchorLayout(width=kwargs.get("width", 160), height=kwargs.get("height", 160))
        layout.add(child=self.label_element, anchor_x="center_x", anchor_y="center_y")
        self.add(layout)


# класс игрового меню
class MainMenu(arcade.View):
    def __init__(self):
        super().__init__()

        self.manager = arcade.gui.UIManager()
        self.v_box = arcade.gui.UIBoxLayout(space_between=30)

        title_label = arcade.gui.UILabel(
            text="BANANA SNAIL",
            font_size=36,
            font_name="Arial",
            bold=True,
            text_color=arcade.color.WHITE
        )
        self.v_box.add(title_label)

        # если игрок собрал награды на всех уровнях, то показываем текст поздравления
        all_collected = all(lvl["collected"] == "111" and lvl["passed"] for lvl in GAME_PROGRESS.values())
        if all_collected:
            trophy_label = arcade.gui.UILabel(
                text="ВСЕ БАНАНЫ СОБРАНЫ!",
                font_size=16,
                font_name="Arial",
                bold=True,
                text_color=arcade.color.GOLD
            )
            self.v_box.add(trophy_label)

        self.h_box = arcade.gui.UIBoxLayout(vertical=False, space_between=20)

        button_style = {
            "normal": {"font_name": "Arial", "font_size": 14},
            "hover": {"font_name": "Arial", "font_size": 14},
            "press": {"font_name": "Arial", "font_size": 14}
        }

        # инициализация кнопок меню
        for lvl_id, data in GAME_PROGRESS.items():
            complete_text = "" if not data.get("passed") else "".join(
                ['🍌' if b == '1' else '--' for b in data['collected']])
            status_text = f"{data['name']}\n\nИГРАТЬ\n\n{complete_text}"

            level_button = MultilineButton(
                text=status_text,
                width=160,
                height=160,
                style=button_style
            )

            level_button.on_click = self.make_click_handler(lvl_id)
            self.h_box.add(level_button)

        self.v_box.add(self.h_box)

        anchor_layout = arcade.gui.UIAnchorLayout()
        anchor_layout.add(
            child=self.v_box,
            anchor_x="center_x",
            anchor_y="center_y"
        )
        self.manager.add(anchor_layout)

    def make_click_handler(self, level_id):
        def on_click(_):
            game_view = GameLevel(level_id, GAME_PROGRESS, self.return_to_menu)
            self.window.show_view(game_view)

        return on_click

    def return_to_menu(self):
        menu_view = MainMenu()
        self.window.show_view(menu_view)

    def on_show_view(self):
        self.manager.enable()

    def on_hide_view(self):
        self.manager.disable()

    # прорисовка меню
    def on_draw(self):
        self.background_color = arcade.color.DARK_SLATE_GRAY
        self.clear()
        self.manager.draw()


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

    # метод для сохранения при закрытии программы
    def close_and_save():
        save_progress(GAME_PROGRESS)
        arcade.Window.on_close(window)

    window.on_close = close_and_save

    menu_view = MainMenu()
    window.show_view(menu_view)
    arcade.run()


if __name__ == "__main__":
    main()
