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
from utilities.geometry import Point, Rectangle
from utilities.mouse_utils import MouseUtils
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
    mouse = MouseUtils()
    options_set: bool = False
    progress: float = 0
    status = BotStatus.STOPPED
    thread: BotThread = None

    @abstractmethod
    def __init__(self, title, description, window: Window, launchable: bool = False):
        """
        Instantiates a Bot object. This must be called by subclasses.
        Args:
            title: title of the bot to display in the UI
            description: description of the bot to display in the UI
            window: window object the bot will use to interact with the game client
            launchable: whether the game client can be launched with custom arguments from the bot's UI
        """
        self.title = title
        self.description = description
        self.options_builder = OptionsBuilder(title)
        self.win = window
        self.launchable = launchable

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
        if self.status == BotStatus.STOPPED:
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
            self.thread.stop()
            self.thread.join()
            self.set_status(BotStatus.STOPPED)
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
        self.controller.update_log(msg, overwrite)

    def clear_log(self):
        """
        Requests the controller to tell the UI to clear the log.
        """
        self.controller.clear_log()

    # --- Misc Utility Functions
    def drop_inventory(self, skip_rows: int = 0, skip_slots: list[int] = None) -> None:
        """
        Drops all items in the inventory.
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
            pag.click()
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
        pag.click()
        time.sleep(1)
        self.mouse.move_rel(0, -53, 5, 5)
        pag.click()

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
        # debug.save_image("hp_bars.png", hp_bars)
        # If there are any HP bars, return True
        return hp_bars.mean(axis=(0, 1)) != 0.0

    def get_hp(self) -> int:
        """
        Gets the HP value of the player.
        """
        res = ocr.extract_text(self.win.hp_orb_text, ocr.PLAIN_11, [clr.ORB_GREEN, clr.ORB_RED])
        return int(res[0]) if (res := re.findall(r"\d+", res)) else None

    def get_prayer(self) -> int:
        """
        Gets the Prayer points of the player.
        """
        res = ocr.extract_text(self.win.prayer_orb_text, ocr.PLAIN_11, [clr.ORB_GREEN, clr.ORB_RED])
        return int(res) if (res := re.findall(r"\d+", res)) else None

    def get_run_energy(self) -> int:
        """
        Gets the run energy of the player.
        """
        res = ocr.extract_text(self.win.run_orb_text, ocr.PLAIN_11, [clr.ORB_GREEN, clr.ORB_RED])
        return int(res) if (res := re.findall(r"\d+", res)) else None

    def get_special_energy(self) -> int:
        """
        Gets the special attack energy of the player.
        """
        res = ocr.extract_text(self.win.spec_orb_text, ocr.PLAIN_11, [clr.ORB_GREEN, clr.ORB_RED])
        return int(res) if (res := re.findall(r"\d+", res)) else None

    def get_total_xp(self) -> int:
        """
        Gets the total XP of the player using OCR.
        """
        fonts = [ocr.PLAIN_11, ocr.PLAIN_12, ocr.BOLD_12]
        for font in fonts:
            res = ocr.extract_text(self.win.total_xp, font, [clr.WHITE])
            if res := re.findall(r"\d+", res):
                return int(res[0])
        return None

    # --- OCR Functions ---
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
    # TODO: Add anti-ban functions that move camera around randomly
    def move_camera_up(self):
        """
        Moves the camera up.
        """
        # Position the mouse somewhere on the game view
        self.mouse.move_to(self.win.game_view.get_center())
        pag.keyDown("up")
        time.sleep(2)
        pag.keyUp("up")
        time.sleep(0.5)

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
        pag.rightClick()
        self.mouse.move_rel(0, rel_y, 5, 2)
        self.mouse.click()

    def set_camera_zoom(self, percentage: int) -> bool:
        """
        Sets the camera zoom level.
        Args:
            percentage: The percentage of the camera zoom level to set.
        Returns:
            True if the zoom level was set, False if an issue occured.
        """
        if percentage < 1:
            percentage = 1
        elif percentage > 100:
            percentage = 100
        self.log_msg(f"Setting camera zoom to {percentage}%...")
        if not self.__open_display_settings():
            return False
        scroll_rect = Rectangle(
            left=self.win.control_panel.left + 84,
            top=self.win.control_panel.top + 146,
            width=102,
            height=8,
        )
        x = int((percentage / 100) * (scroll_rect.left + scroll_rect.width - scroll_rect.left) + scroll_rect.left)
        p = scroll_rect.random_point()
        self.mouse.move_to((x, p.y))
        self.mouse.click()
        return True

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
        pag.click()
        time.sleep(0.5)

        if toggle_on:
            if auto_retal_btn := imsearch.search_img_in_rect(
                imsearch.BOT_IMAGES.joinpath("near_reality", "cp_combat_autoretal.png"),
                self.win.control_panel,
            ):
                self.mouse.move_to(auto_retal_btn.random_point(), mouseSpeed="medium")
                self.mouse.click()
            else:
                self.log_msg("Auto retaliate is already on.")
        elif auto_retal_btn := imsearch.search_img_in_rect(
            imsearch.BOT_IMAGES.joinpath("near_reality", "cp_combat_autoretal_on.png"),
            self.win.control_panel,
        ):
            self.mouse.move_to(auto_retal_btn.random_point(), mouseSpeed="medium")
            self.mouse.click()
        else:
            self.log_msg("Auto retaliate is already off.")

    def __open_display_settings(self) -> bool:
        """
        Opens the display settings for the game client.
        Returns:
            True if the settings were opened, False if an error occured.
        """
        control_panel = self.win.control_panel
        self.mouse.move_to(self.win.cp_tabs[11].random_point())
        self.mouse.click()
        time.sleep(0.5)
        display_tab = imsearch.search_img_in_rect(imsearch.BOT_IMAGES.joinpath("cp_settings_display_tab.png"), control_panel)
        if display_tab is None:
            self.log_msg("Could not find the display settings tab.")
            return False
        self.mouse.move_to(display_tab.random_point())
        self.mouse.click()
        time.sleep(0.5)
        return True
