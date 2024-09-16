"""
A Bot is a base class for bot script models. It is abstract and cannot be instantiated. Many of the methods in this base class are
pre-implemented and can be used by subclasses, or called by the controller. Code in this class should not be modified.
"""
import ctypes
import platform
import re
import threading
import time
import warnings
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Union

import customtkinter
import numpy as np
import pyautogui as pag
import pytweening
from deprecated import deprecated

import utilities.color as clr
import utilities.debug as debug
import utilities.imagesearch as imsearch
import utilities.ocr as ocr
import utilities.random_util as rd
from utilities.geometry import Point, Rectangle
from utilities.mouse import Mouse
from utilities.options_builder import OptionsBuilder
from utilities.window import Window, WindowInitializationError

warnings.filterwarnings("ignore", category=UserWarning)


class BotThread(threading.Thread):
    def __init__(self, target: callable):
        threading.Thread.__init__(self)
        self.target = target

    def run(self):
        try:
            print("Thread started.")
            self.target()
        finally:
            print("Thread stopped successfully.")

    def __get_id(self):
        """Returns id of the respective thread"""
        if hasattr(self, "_thread_id"):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def stop(self):
        """Raises SystemExit exception in the thread. This can be called from the main thread followed by join()."""
        thread_id = self.__get_id()
        if platform.system() == "Windows":
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, ctypes.py_object(SystemExit))
            if res > 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
                print("Exception raise failure")
        elif platform.system() == "Linux":
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), ctypes.py_object(SystemExit))
            if res > 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), 0)
                print("Exception raise failure")


class BotStatus(Enum):
    """
    BotStatus enum.
    """

    RUNNING = 1
    PAUSED = 2
    STOPPED = 3
    CONFIGURING = 4
    CONFIGURED = 5


class Bot(ABC):
    mouse = Mouse()
    options_set: bool = False
    progress: float = 0
    status = BotStatus.STOPPED
    thread: BotThread = None

    @abstractmethod
    def __init__(self, game_title, bot_title, description, window: Window):
        """
        Instantiates a Bot object. This must be called by subclasses.
        Args:
            game_title: title of the game the bot will interact with
            bot_title: title of the bot to display in the UI
            description: description of the bot to display in the UI
            window: window object the bot will use to interact with the game client
            launchable: whether the game client can be launched with custom arguments from the bot's UI
        """
        self.game_title = game_title
        self.bot_title = bot_title
        self.description = description
        self.options_builder = OptionsBuilder(bot_title)
        self.win = window

    @abstractmethod
    def main_loop(self):
        """
        Main logic of the bot. This function is called in a separate thread.
        """
        pass

    @abstractmethod
    def create_options(self):
        """
        Defines the options for the bot using the OptionsBuilder.
        """
        pass

    @abstractmethod
    def save_options(self, options: dict):
        """
        Saves a dictionary of options as properties of the bot.
        Args:
            options: dict - dictionary of options to save
        """
        pass

    def get_options_view(self, parent) -> customtkinter.CTkFrame:
        """
        Builds the options view for the bot based on the options defined in the OptionsBuilder.
        """
        self.clear_log()
        self.log_msg("Options panel opened.")
        self.create_options()
        view = self.options_builder.build_ui(parent, self.controller)
        self.options_builder.options = {}
        return view

    def play(self):
        """
        Fired when the user starts the bot manually. This function performs necessary set up on the UI
        and locates/initializes the game client window. Then, it launches the bot's main loop in a separate thread.
        """
        if self.status in [BotStatus.STOPPED, BotStatus.CONFIGURED]:
            self.clear_log()
            self.log_msg("Starting bot...")
            if not self.options_set:
                self.log_msg("Options not set. Please set options before starting.")
                return
            try:
                self.__initialize_window()
            except WindowInitializationError as e:
                self.log_msg(str(e))
                return
            self.reset_progress()
            self.set_status(BotStatus.RUNNING)
            self.thread = BotThread(target=self.main_loop)
            self.thread.setDaemon(True)
            self.thread.start()
        elif self.status == BotStatus.RUNNING:
            self.log_msg("Bot is already running.")
        elif self.status == BotStatus.CONFIGURING:
            self.log_msg("Please finish configuring the bot before starting.")

    def __initialize_window(self):
        """
        Attempts to focus and initialize the game window by identifying core UI elements.
        """
        self.win.focus()
        time.sleep(0.5)
        self.win.initialize()

    def stop(self):
        """
        Fired when the user stops the bot manually.
        """
        self.log_msg("Stopping script.")
        if self.status != BotStatus.STOPPED:
            self.set_status(BotStatus.STOPPED)
            self.thread.stop()
            self.thread.join()
        else:
            self.log_msg("Bot is already stopped.")

    # ---- Controller Setter ----
    def set_controller(self, controller):
        self.controller = controller

    # ---- Functions that notify the controller of changes ----
    def reset_progress(self):
        """
        Resets the current progress property to 0 and notifies the controller to update UI.
        """
        self.progress = 0
        self.controller.update_progress()

    def update_progress(self, progress: float):
        """
        Updates the progress property and notifies the controller to update UI.
        Args:
            progress: float - number between 0 and 1 indicating percentage of progress.
        """
        if progress < 0:
            progress = 0
        elif progress > 1:
            progress = 1
        self.progress = progress
        self.controller.update_progress()

    def set_status(self, status: BotStatus):
        """
        Sets the status property of the bot and notifies the controller to update UI accordingly.
        Args:
            status: BotStatus - status to set the bot to
        """
        self.status = status
        self.controller.update_status()

    def log_msg(self, msg: str, overwrite=False):
        """
        Sends a message to the controller to be displayed in the log for the user.
        Args:
            msg: str - message to log
            overwrite: bool - if True, overwrites the current log message. If False, appends to the log.
        """
        msg = f"{debug.current_time()}: {msg}"
        self.controller.update_log(msg, overwrite)

    def clear_log(self):
        """
        Requests the controller to tell the UI to clear the log.
        """
        self.controller.clear_log()

    # --- Misc Utility Functions
    def drop_all(self, skip_rows: int = 0, skip_slots: List[int] = None) -> None:
        """
        Shift-clicks all items in the inventory to drop them.
        Args:
            skip_rows: The number of rows to skip before dropping.
            skip_slots: The indices of slots to avoid dropping.
        """
        self.log_msg("Dropping inventory...")
        # Determine slots to skip
        if skip_slots is None:
            skip_slots = []
        if skip_rows > 0:
            row_skip = list(range(skip_rows * 4))
            skip_slots = np.unique(row_skip + skip_slots)
        # Start dropping
        pag.keyDown("shift")
        for i, slot in enumerate(self.win.inventory_slots):
            if i in skip_slots:
                continue
            p = slot.random_point()
            self.mouse.move_to(
                (p[0], p[1]),
                mouseSpeed="fastest",
                knotsCount=1,
                offsetBoundaryY=40,
                offsetBoundaryX=40,
                tween=pytweening.easeInOutQuad,
            )
            self.mouse.click()
        pag.keyUp("shift")

    def drop(self, slots: List[int]) -> None:
        """
        Shift-clicks inventory slots to drop items.
        Args:
            slots: The indices of slots to drop.
        """
        self.log_msg("Dropping items...")
        pag.keyDown("shift")
        for i, slot in enumerate(self.win.inventory_slots):
            if i not in slots:
                continue
            p = slot.random_point()
            self.mouse.move_to(
                (p[0], p[1]),
                mouseSpeed="fastest",
                knotsCount=1,
                offsetBoundaryY=40,
                offsetBoundaryX=40,
                tween=pytweening.easeInOutQuad,
            )
            self.mouse.click()
        pag.keyUp("shift")

    def friends_nearby(self) -> bool:
        """
        Checks the minimap for green dots to indicate friends nearby.
        Returns:
            True if friends are nearby, False otherwise.
        """
        minimap = self.win.minimap.screenshot()
        # debug.save_image("minimap.png", minimap)
        only_friends = clr.isolate_colors(minimap, [clr.GREEN])
        # debug.save_image("minimap_friends.png", only_friends)
        mean = only_friends.mean(axis=(0, 1))
        return mean != 0.0

    def logout(self):  # sourcery skip: class-extract-method
        """
        Logs player out.
        """
        self.log_msg("Logging out...")
        self.mouse.move_to(self.win.cp_tabs[10].random_point())
        self.mouse.click()
        time.sleep(1)
        self.mouse.move_rel(0, -53, 5, 5)
        self.mouse.click()

    def take_break(self, min_seconds: int = 1, max_seconds: int = 30, fancy: bool = False):
        """
        Takes a break for a random amount of time.
        Args:
            min_seconds: minimum amount of time the bot could rest
            max_seconds: maximum amount of time the bot could rest
            fancy: if True, the randomly generated value will be from a truncated normal distribution
                   with randomly selected means. This may produce more human results.
        """
        self.log_msg("Taking a break...")
        if fancy:
            length = rd.fancy_normal_sample(min_seconds, max_seconds)
        else:
            length = rd.truncated_normal_sample(min_seconds, max_seconds)
        length = round(length)
        for i in range(length):
            self.log_msg(f"Taking a break... {int(length) - i} seconds left.", overwrite=True)
            time.sleep(1)
        self.log_msg(f"Done taking {length} second break.", overwrite=True)

    # --- Player Status Functions ---
    def has_hp_bar(self) -> bool:
        """
        Returns whether the player has an HP bar above their head. Useful alternative to using OCR to check if the
        player is in combat. This function only works when the game camera is all the way up.
        """
        # Position of character relative to the screen
        char_pos = self.win.game_view.get_center()

        # Make a rectangle around the character
        offset = 30
        char_rect = Rectangle.from_points(
            Point(char_pos.x - offset, char_pos.y - offset),
            Point(char_pos.x + offset, char_pos.y + offset),
        )
        # Take a screenshot of rect
        char_screenshot = char_rect.screenshot()
        # Isolate HP bars in that rectangle
        hp_bars = clr.isolate_colors(char_screenshot, [clr.RED, clr.GREEN])
        # If there are any HP bars, return True
        return hp_bars.mean(axis=(0, 1)) != 0.0

    def get_hp(self) -> int:
        """
        Gets the HP value of the player. Returns -1 if the value couldn't be read.
        """
        if res := ocr.extract_text(self.win.hp_orb_text, ocr.PLAIN_11, [clr.ORB_GREEN, clr.ORB_RED]):
            return int("".join(re.findall(r"\d", res)))
        return -1

    def get_prayer(self) -> int:
        """
        Gets the Prayer points of the player. Returns -1 if the value couldn't be read.
        """
        if res := ocr.extract_text(self.win.prayer_orb_text, ocr.PLAIN_11, [clr.ORB_GREEN, clr.ORB_RED]):
            return int("".join(re.findall(r"\d", res)))
        return -1

    def get_run_energy(self) -> int:
        """
        Gets the run energy of the player. Returns -1 if the value couldn't be read.
        """
        if res := ocr.extract_text(self.win.run_orb_text, ocr.PLAIN_11, [clr.ORB_GREEN, clr.ORB_RED]):
            return int("".join(re.findall(r"\d", res)))
        return -1

    def get_special_energy(self) -> int:
        """
        Gets the special attack energy of the player. Returns -1 if the value couldn't be read.
        """
        if res := ocr.extract_text(self.win.spec_orb_text, ocr.PLAIN_11, [clr.ORB_GREEN, clr.ORB_RED]):
            return int("".join(re.findall(r"\d", res)))
        return -1

    def get_total_xp(self) -> int:
        """
        Gets the total XP of the player using OCR. Returns -1 if the value couldn't be read.
        """
        fonts = [ocr.PLAIN_11, ocr.PLAIN_12, ocr.BOLD_12]
        for font in fonts:
            if res := ocr.extract_text(self.win.total_xp, font, [clr.WHITE]):
                return int("".join(re.findall(r"\d", res)))
        return -1

    def mouseover_text(
        self,
        contains: Union[str, List[str]] = None,
        color: Union[clr.Color, List[clr.Color]] = None,
    ) -> Union[bool, str]:
        """
        Examines the mouseover text area.
        Args:
            contains: The text to search for (single word, phrase, or list of words). Case sensitive. If left blank,
                      returns all text in the mouseover area.
            color: The color(s) to isolate. If left blank, isolates all expected colors. Consider using
                   clr.OFF_* colors for best results.
        Returns:
            True if exact string is found, False otherwise.
            If args are left blank, returns the text in the mouseover area.
        """
        if color is None:
            color = [
                clr.OFF_CYAN,
                clr.OFF_GREEN,
                clr.OFF_ORANGE,
                clr.OFF_WHITE,
                clr.OFF_YELLOW,
            ]
        if contains is None:
            return ocr.extract_text(self.win.mouseover, ocr.BOLD_12, color)
        return bool(ocr.find_text(contains, self.win.mouseover, ocr.BOLD_12, color))

    def chatbox_text(self, contains: str = None) -> Union[bool, str]:
        """
        Examines the chatbox for text. Currently only captures player chat text.
        Args:
            contains: The text to search for (single word or phrase). Case sensitive. If left blank,
                      returns all text in the chatbox.
        Returns:
            True if exact string is found, False otherwise.
            If args are left blank, returns the text in the chatbox.
        """
        if contains is None:
            return ocr.extract_text(self.win.chat, ocr.PLAIN_12, clr.BLUE)
        if ocr.find_text(contains, self.win.chat, ocr.PLAIN_12, clr.BLUE):
            return True

    # --- Client Settings ---
    def set_compass_north(self):
        self.log_msg("Setting compass North...")
        self.mouse.move_to(self.win.compass_orb.random_point())
        self.mouse.click()

    def set_compass_west(self):
        self.__compass_right_click("Setting compass West...", 72)

    def set_compass_east(self):
        self.__compass_right_click("Setting compass East...", 43)

    def set_compass_south(self):
        self.__compass_right_click("Setting compass South...", 57)

    def __compass_right_click(self, msg, rel_y):
        self.log_msg(msg)
        self.mouse.move_to(self.win.compass_orb.random_point())
        self.mouse.right_click()
        self.mouse.move_rel(0, rel_y, 5, 2)
        self.mouse.click()

    def move_camera(self, horizontal: int = 0, vertical: int = 0):
        """
        Rotates the camera by specified degrees in any direction.
        Agrs:
            horizontal: The degree to rotate the camera (-360 to 360).
            vertical: The degree to rotate the camera up (-90 to 90).
        Note:
            A negative degree will rotate the camera left or down.
        """
        if horizontal == 0 and vertical == 0:
            raise ValueError("Must specify at least one argument.")
        if horizontal < -360 or horizontal > 360:
            raise ValueError("Horizontal degree must be between -360 and 360.")
        if vertical < -90 or vertical > 90:
            raise ValueError("Vertical degree must be between -90 and 90.")

        rotation_time_h = 3.549  # seconds to do a full 360 degree rotation horizontally
        rotation_time_v = 1.75  # seconds to do a full 90 degree rotation vertically
        sleep_h = rotation_time_h / 360 * abs(horizontal)  # time to hold arrow key
        sleep_v = rotation_time_v / 90 * abs(vertical)  # time to hold arrow key

        direction_h = "right" if horizontal < 0 else "left"
        direction_v = "down" if vertical < 0 else "up"

        def keypress(direction, duration):
            pag.keyDown(direction)
            time.sleep(duration)
            pag.keyUp(direction)

        # if a single direction is 0 avoid pressing that key for any length of time so we don't nudge the camera over
        if vertical == 0:
            keypress(direction_h, sleep_h)
            return
        elif horizontal == 0:
            keypress(direction_v, sleep_v)
            return
            
        thread_h = threading.Thread(target=keypress, args=(direction_h, sleep_h), daemon=True)
        thread_v = threading.Thread(target=keypress, args=(direction_v, sleep_v), daemon=True)
        delay = rd.fancy_normal_sample(0, max(sleep_h, sleep_v))
        if sleep_h > sleep_v:
            thread_h.start()
            time.sleep(delay)
            thread_v.start()
        else:
            thread_v.start()
            time.sleep(delay)
            thread_h.start()
        thread_h.join()
        thread_v.join()

    def toggle_auto_retaliate(self, toggle_on: bool):
        """
        Toggles auto retaliate. Assumes client window is configured.
        Args:
            toggle_on: Whether to turn on or off.
        """
        state = "on" if toggle_on else "off"
        self.log_msg(f"Toggling auto retaliate {state}...")
        # click the combat tab
        self.mouse.move_to(self.win.cp_tabs[0].random_point())
        self.mouse.click()
        time.sleep(0.5)

        if toggle_on:
            if auto_retal_btn := imsearch.search_img_in_rect(
                imsearch.BOT_IMAGES.joinpath("combat", "autoretal_off.png"),
                self.win.control_panel,
            ):
                self.mouse.move_to(auto_retal_btn.random_point(), mouseSpeed="medium")
                self.mouse.click()
            else:
                self.log_msg("Auto retaliate is already on.")
        elif auto_retal_btn := imsearch.search_img_in_rect(
            imsearch.BOT_IMAGES.joinpath("combat", "autoretal_on.png"),
            self.win.control_panel,
        ):
            self.mouse.move_to(auto_retal_btn.random_point(), mouseSpeed="medium")
            self.mouse.click()
        else:
            self.log_msg("Auto retaliate is already off.")

    def select_combat_style(self, combat_style: str):
        """
        Selects a combat style from the combat tab.
        Args:
            combat_style: the attack type ("accurate", "aggressive", "defensive", "controlled", "rapid", "longrange").
        """
        # Ensuring that args are valid
        if combat_style not in ["accurate", "aggressive", "defensive", "controlled", "rapid", "longrange"]:
            raise ValueError(f"Invalid combat style: {combat_style}. See function docstring for valid options.")

        # Click the combat tab
        self.mouse.move_to(self.win.cp_tabs[0].random_point(), mouseSpeed="fastest")
        self.mouse.click()

        # It is important to keep ambiguous words at the end of the list so that they are matched as a last resort
        styles = {
            "accurate": ["Accurate", "Short fuse", "Punch", "Chop", "Jab", "Stab", "Spike", "Reap", "Bash", "Flick", "Pound", "Pummel"],
            "aggressive": ["Kick", "Smash", "Hack", "Swipe", "Slash", "Impale", "Lunge", "Pummel", "Chop", "Pound"],
            "defensive": ["Block", "Fend", "Focus", "Deflect"],
            "controlled": ["Spike", "Lash", "Lunge", "Jab"],
            "rapid": [
                "Rapid",
                "Medium fuse",
            ],
            "longrange": [
                "Longrange",
                "Long fuse",
            ],
        }

        for style in styles[combat_style]:
            # Try and find the center of the word with OCR
            if result := ocr.find_text(style, self.win.control_panel, ocr.PLAIN_11, clr.OFF_ORANGE):
                # If the word is found, draw a rectangle around it and click a random point in that rectangle
                center = result[0].get_center()
                rect = Rectangle.from_points(Point(center[0] - 32, center[1] - 34), Point(center[0] + 32, center[1] + 10))
                self.mouse.move_to(rect.random_point(), mouseSpeed="fastest")
                self.mouse.click()
                self.log_msg(f"Combat style {combat_style} selected.")
                return
        self.log_msg(f"{combat_style.capitalize()} style not found.")

    def toggle_run(self, toggle_on: bool):
        """
        Toggles run. Assumes client window is configured. Images not included.
        Args:
            toggle_on: True to turn on, False to turn off.
        """
        state = "on" if toggle_on else "off"
        self.log_msg(f"Toggling run {state}...")

        if toggle_on:
            if run_status := imsearch.search_img_in_rect(imsearch.BOT_IMAGES.joinpath("run_off.png"), self.win.run_orb, 0.323):
                self.mouse.move_to(run_status.random_point())
                self.mouse.click()
            else:
                self.log_msg("Run is already on.")
        elif run_status := imsearch.search_img_in_rect(imsearch.BOT_IMAGES.joinpath("run_on.png"), self.win.run_orb, 0.323):
            self.mouse.move_to(run_status.random_point())
            self.mouse.click()
        else:
            self.log_msg("Run is already off.")
