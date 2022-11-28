'''
The OSNRBot class contains properties and functions that are specific to the OSNR client. This class should
be inherited by OSNR script classes.
'''
from abc import ABCMeta
from enum import Enum
from model.runelite_bot import RuneLiteBot, RuneLiteWindow
from utilities.bot_cv import Point
import pyautogui as pag
import time
import utilities.bot_cv as bcv

class Spellbook(Enum):
    '''
    TODO: Consider moving to parent class.
    '''
    standard = 0
    ancient = 1

class OSNRWindow(RuneLiteWindow):
    def __init__(self) -> None:
        super().__init__(window_title="Near-Reality")

    # --- Spellbook ---
    def spellbook_home_tele(self, spellbook: Spellbook) -> Point:
        '''
        Returns the Point of the home teleport.
        '''
        if spellbook == Spellbook.standard:
            return self.get_relative_point(578, 258)
        elif spellbook == Spellbook.ancient:
            return self.get_relative_point(581, 251)

    def teleport_menu(self, spellbook: Spellbook):
        '''
        Returns the Point that opens the custom teleport menu.
        '''
        if spellbook == Spellbook.standard:
            return self.get_relative_point(591, 307)
        elif spellbook == Spellbook.ancient:
            return self.get_relative_point(713, 250)
    
    def teleport_menu_search(self):
        '''
        Returns the Point of the teleport menu search button.
        '''
        return self.get_relative_point(63, 49)
    
    def teleport_menu_search_result(self):
        '''
        Returns the Point of the teleport menu search result.
        '''
        return self.get_relative_point(305, 100)
    
    # --- Banking ---
    def presets_btn(self):
        '''
        Returns the Point of the presets button in the bank interface.
        '''
        return self.get_relative_point(458, 50)
    
    def presets_load_btn(self):
        '''
        Returns the Point of the load button in the presets interface.
        '''
        return self.get_relative_point(76, 315)
    
    def presets_close_btn(self):
        '''
        Returns the Point of the close button in the presets interface.
        '''
        return self.get_relative_point(490, 65)
    
    def bank_close_btn(self):
        '''
        Returns the Point of the close button in the bank interface.
        '''
        return self.get_relative_point(491, 51)

class OSNRBot(RuneLiteBot, metaclass=ABCMeta):
    
    win: OSNRWindow = None

    def __init__(self, title, description) -> None:
        super().__init__(title, description, OSNRWindow())

    def __disable_private_chat(self):
        '''
        Disables private chat in game.
        '''
        self.log_msg("Disabling private chat...")
        private_btn = self.win.get_relative_point(218, 517)  # TODO: Make chat buttons accessible in RuneLiteWindow
        self.mouse.move_to(private_btn)
        pag.rightClick()
        time.sleep(0.05)
        self.mouse.move_rel(0, -28)
        pag.click()
    
    # -- Banking --
    def close_bank(self):
        '''
        Closes the bank interface.
        '''
        self.log_msg("Closing bank...")
        self.mouse.move_to(self.win.bank_close_btn())
        pag.click()
        time.sleep(1)

    def deposit_inventory(self) -> bool:
        '''
        From within the banking interface, clicks the "deposit all" button.
        '''
        empty = bcv.search_img_in_rect(f"{bcv.BOT_IMAGES}/bank_deposit_all.png", self.win.rect_game_view())
        if empty is None:
            self.log_msg("Cannot find deposit button.")
            return False
        self.mouse.move_to(empty.random_point())
        pag.click()
        time.sleep(1)
        return True
    
    def load_preset(self):
        '''
        Loads the default preset from the bank interface.
        '''
        self.log_msg("Loading preset...")
        self.mouse.move_to(self.win.presets_btn())
        pag.click()
        time.sleep(1)
        self.mouse.move_to(self.win.presets_load_btn())
        pag.click()
        time.sleep(1)
        self.mouse.move_to(self.win.presets_close_btn())
        pag.click()
        time.sleep(1)

    def teleport_and_bank(self, spellbook: Spellbook) -> bool:
        '''
        Teleports to a predefined location and enters the bank interface.
        Args:
            spellbook: The spellbook to use.
        Returns:
            True if successful, False otherwise.
        '''
        if not self.teleport_to(spellbook, "Castle Wars"):
            return False

        if not self.status_check_passed():
            return

        time.sleep(4)

        if not self.status_check_passed():
            return

        bank_icon = bcv.search_img_in_rect(f"{bcv.BOT_IMAGES}/minimap_bank_icon.png",
                                           self.win.rect_minimap(),
                                           confidence=0.8)
        if bank_icon is None:
            self.log_msg("Bank icon not found.")
            return False
        self.mouse.move_to(bank_icon.random_point())
        pag.click()

        if not self.status_check_passed():
            return

        time.sleep(4)

        if not self.status_check_passed():
            return

        banks = self.get_all_tagged_in_rect(self.win.rect_game_view(), self.PINK)
        if len(banks) == 0:
            self.log_msg("No banks found.")
            return False
        self.mouse.move_to(banks[0])
        pag.click()
        return True

    # Teleporting
    def teleport_home(self, spellbook: Spellbook):
        '''
        Teleports to the home location.
        '''
        self.log_msg("Teleporting to home...")
        self.mouse.move_to(self.win.cp_tab(7))
        pag.click()
        time.sleep(0.5)
        self.mouse.move_to(self.win.spellbook_home_tele(spellbook), mouseSpeed='medium')
        pag.click()

    def teleport_to(self, spellbook: Spellbook, location: str) -> bool:
        '''
        Teleports player to a location from the teleport menu interface.
        Args:
            spellbook: The player's current spellbook.
            location: The location name to lookup in the teleport interface.
        Returns:
            True if successful, False otherwise.
        '''
        self.log_msg(f"Teleporting to {location}...")
        self.mouse.move_to(self.win.cp_tab(7), mouseSpeed='medium')
        pag.click()
        time.sleep(0.5)

        if not self.status_check_passed():
            return

        self.mouse.move_to(self.win.teleport_menu(spellbook), mouseSpeed='medium')
        pag.click()
        time.sleep(1.5)

        if not self.status_check_passed():
            return

        self.mouse.move_to(self.win.teleport_menu_search(), mouseSpeed='medium')
        pag.click()
        time.sleep(1)
        result = self.win.teleport_menu_search_result()
        no_result_rgb = pag.pixel(result.x, result.y)
        pag.typewrite(location, interval=0.05)

        if not self.status_check_passed():
            return

        time.sleep(1.5)
        new_result = self.win.teleport_menu_search_result()
        if no_result_rgb == pag.pixel(new_result.x, new_result.y):
            self.log_msg(f"No results found for {location}.")
            return False
        self.mouse.move_to(new_result, mouseSpeed='medium')
        pag.click()
        self.log_msg("Teleport successful.")
        return True

    # Client Settings Config
    def set_compass_north(self):
        self.log_msg("Setting compass North...")
        self.mouse.move_to(self.win.orb_compass())
        self.mouse.click()

    def set_compass_west(self):
        self.__compass_right_click("Setting compass West...", 72)

    def set_compass_east(self):
        self.__compass_right_click("Setting compass East...", 43)

    def set_compass_south(self):
        self.__compass_right_click("Setting compass South...", 57)

    def __compass_right_click(self, msg, rel_y):
        self.log_msg(msg)
        self.mouse.move_to(self.win.orb_compass())
        pag.rightClick()
        self.mouse.move_rel(0, rel_y)
        self.mouse.click()

    def toggle_auto_retaliate(self, toggle_on: bool):
        '''
        Toggles auto retaliate. Assumes client window is configured.
        Args:
            toggle_on: Whether to turn on or off.
        '''
        state = "on" if toggle_on else "off"
        self.log_msg(f"Toggling auto retaliate {state}...")
        # click the combat tab
        self.mouse.move_to(self.win.cp_tab(1))
        pag.click()
        time.sleep(0.5)

        if toggle_on:
            if auto_retal_btn := bcv.search_img_in_rect(f"{bcv.BOT_IMAGES}/near_reality/cp_combat_autoretal.png", self.win.rect_inventory()):
                self.mouse.move_to(auto_retal_btn.random_point(), mouseSpeed="medium")
                self.mouse.click()
            else:
                self.log_msg("Auto retaliate is already on.")
        elif auto_retal_btn := bcv.search_img_in_rect(f"{bcv.BOT_IMAGES}/near_reality/cp_combat_autoretal_on.png", self.win.rect_inventory()):
            self.mouse.move_to(auto_retal_btn.random_point(), mouseSpeed="medium")
            self.mouse.click()
        else:
            self.log_msg("Auto retaliate is already off.")

    def setup_osnr(self, set_layout_fixed=True, logout_runelite=False, zoom_percentage=25):
        '''
        Sets up the OSNR client.
        '''
        self.setup_client(set_layout_fixed=set_layout_fixed,
                          logout_runelite=logout_runelite)
        if not self.status_check_passed():
            return
        self.set_camera_zoom(zoom_percentage)
        self.log_msg("Selecting inventory...")
        self.mouse.move_to(self.win.cp_tab(4))
        self.mouse.click()
        time.sleep(0.5)
        self.__disable_private_chat()
        time.sleep(0.5)
