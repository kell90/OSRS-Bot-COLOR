"""
This class contains functions for interacting with the game client window. All Bot classes have a
Window object as a property. This class allows you to locate important points/areas on screen no
matter where the game client is positioned. This class can be extended to add more functionality
(See RuneLiteWindow within runelite_bot.py for an example).

At the moment, it only works for 2007-style interfaces. In the future, to accomodate other interface
styles, this class should be abstracted, then extended for each interface style.
"""
import time
from typing import List

import pywinctl
from deprecated import deprecated

import utilities.debug as debug
import utilities.imagesearch as imsearch
from utilities.geometry import Point, Rectangle


class WindowInitializationError(Exception):
    """
    Exception raised for errors in the Window class.
    """

    def __init__(self, message=None):
        if message is None:
            message = (
                "Failed to initialize window. Make sure the client is NOT in 'Resizable-Modern' "
                "mode. Make sure you're using the default client configuration (E.g., Opaque UI, status orbs ON)."
            )
        super().__init__(message)


class Window:
    client_fixed: bool = None

    # CP Area
    control_panel: Rectangle = None  # https://i.imgur.com/BeMFCIe.png
    cp_tabs: List[Rectangle] = []  # https://i.imgur.com/huwNOWa.png
    inventory_slots: List[Rectangle] = []  # https://i.imgur.com/gBwhAwE.png
    spellbook_normal: List[Rectangle] = []  # https://i.imgur.com/vkKAfV5.png
    prayers: List[Rectangle] = []  # https://i.imgur.com/KRmC3YB.png
    skill_boxes: List[Rectangle] = [] # https://i.imgur.com/Ipm0BWr.png

    # Chat Area
    chat: Rectangle = None  # https://i.imgur.com/u544ouI.png
    chat_tabs: List[Rectangle] = []  # https://i.imgur.com/2DH2SiL.png

    # Minimap Area
    compass_orb: Rectangle = None
    hp_orb_text: Rectangle = None
    minimap_area: Rectangle = None  # https://i.imgur.com/idfcIPU.png OR https://i.imgur.com/xQ9xg1Z.png
    minimap: Rectangle = None
    prayer_orb_text: Rectangle = None
    prayer_orb: Rectangle = None
    run_orb_text: Rectangle = None
    run_orb: Rectangle = None
    spec_orb_text: Rectangle = None
    spec_orb: Rectangle = None

    # Game View Area
    game_view: Rectangle = None
    mouseover: Rectangle = None
    total_xp: Rectangle = None

    def __init__(self, window_title: str, padding_top: int, padding_left: int) -> None:
        """
        Creates a Window object with various methods for interacting with the client window.
        Args:
            window_title: The title of the client window.
            padding_top: The height of the client window's header.
            padding_left: The width of the client window's left border.
        """
        self.window_title = window_title
        self.padding_top = padding_top
        self.padding_left = padding_left

    def _get_window(self):
        self._client = pywinctl.getWindowsWithTitle(self.window_title)
        if self._client:
            return self._client[0]
        else:
            raise WindowInitializationError("No client window found.")

    window = property(
        fget=_get_window,
        doc="A Win32Window reference to the game client and its properties.",
    )

    def focus(self) -> None:  # sourcery skip: raise-from-previous-error
        """
        Focuses the client window.
        """
        if client := self.window:
            try:
                client.activate()
            except Exception:
                raise WindowInitializationError("Failed to focus client window. Try bringing it to the foreground.")

    def position(self) -> Point:
        """
        Returns the origin of the client window as a Point.
        """
        if client := self.window:
            return Point(client.left, client.top)

    def rectangle(self) -> Rectangle:
        """
        Returns a Rectangle outlining the entire client window.
        """
        if client := self.window:
            return Rectangle(client.left, client.top, client.width, client.height)

    def resize(self, width: int, height: int) -> None:
        """
        Resizes the client window..
        Args:
            width: The width to resize the window to.
            height: The height to resize the window to.
        """
        if client := self.window:
            client.size = (width, height)

    def initialize(self):
        """
        Initializes the client window by locating critical UI regions.
        This function should be called when the bot is started or resumed (done by default).
        Returns:
            True if successful, False otherwise along with an error message.
        """
        start_time = time.time()
        client_rect = self.rectangle()
        a = self.__locate_minimap(client_rect)
        b = self.__locate_chat(client_rect)
        c = self.__locate_control_panel(client_rect)
        d = self.__locate_game_view(client_rect)
        if all([a, b, c, d]):  # if all templates found
            print(f"Window.initialize() took {time.time() - start_time} seconds.")
            return True
        raise WindowInitializationError()

    def __locate_chat(self, client_rect: Rectangle) -> bool:
        """
        Locates the chat area on the client.
        Args:
            client_rect: The client area to search in.
        Returns:
            True if successful, False otherwise.
        """
        if chat := imsearch.search_img_in_rect(imsearch.BOT_IMAGES.joinpath("ui_templates", "chat.png"), client_rect):
            # Locate chat tabs
            self.chat_tabs = []
            x, y = 5, 143
            for _ in range(7):
                self.chat_tabs.append(Rectangle(left=x + chat.left, top=y + chat.top, width=52, height=19))
                x += 62  # btn width is 52px, gap between each is 10px
            self.chat = chat
            return True
        print("Window.__locate_chat(): Failed to find chatbox.")
        return False

    def __locate_control_panel(self, client_rect: Rectangle) -> bool:
        """
        Locates the control panel area on the client.
        Args:
            client_rect: The client area to search in.
        Returns:
            True if successful, False otherwise.
        """
        if cp := imsearch.search_img_in_rect(imsearch.BOT_IMAGES.joinpath("ui_templates", "inv.png"), client_rect):
            self.__locate_cp_tabs(cp)
            self.__locate_inv_slots(cp)
            self.__locate_prayers(cp)
            self.__locate_spells(cp)
            self.__locate_skill_boxes(cp)
            self.control_panel = cp
            return True
        print("Window.__locate_control_panel(): Failed to find control panel.")
        return False

    def __locate_cp_tabs(self, cp: Rectangle) -> None:
        """
        Creates Rectangles for each interface tab (inventory, prayer, etc.) relative to the control panel, storing it in the class property.
        """
        self.cp_tabs = []
        slot_w, slot_h = 29, 26  # top row tab dimensions
        gap = 4  # 4px gap between tabs
        y = 4  # 4px from top for first row
        for _ in range(2):
            x = 8 + cp.left
            for _ in range(7):
                self.cp_tabs.append(Rectangle(left=x, top=y + cp.top, width=slot_w, height=slot_h))
                x += slot_w + gap
            y = 303  # 303px from top for second row
            slot_h = 28  # slightly taller tab Rectangles for second row

    def __locate_skill_boxes(self, cp: Rectangle) -> None:
        """
        Creates Rectangles for each skill box relative to the control panel, storing it in the class property.
        """
        self.skill_boxes = []
        slot_w, slot_h = 59, 29 # dimensions of a skill box
        gap_x, gap_y = 2, 3 # pixel gap between skills
        y = 38 + cp.top 
        for _ in range(8): 
            x = 27 + cp.left 
            for _ in range(3):
                self.skill_boxes.append(Rectangle(left=x, top=y, width=slot_w, height=slot_h))
                x += slot_w + gap_x
            y += slot_h + gap_y

    def __locate_inv_slots(self, cp: Rectangle) -> None:
        """
        Creates Rectangles for each inventory slot relative to the control panel, storing it in the class property.
        """
        self.inventory_slots = []
        slot_w, slot_h = 36, 32  # dimensions of a slot
        gap_x, gap_y = 6, 4  # pixel gap between slots
        y = 44 + cp.top  # start y relative to cp template
        for _ in range(7):
            x = 40 + cp.left  # start x relative to cp template
            for _ in range(4):
                self.inventory_slots.append(Rectangle(left=x, top=y, width=slot_w, height=slot_h))
                x += slot_w + gap_x
            y += slot_h + gap_y

    def __locate_prayers(self, cp: Rectangle) -> None:
        """
        Creates Rectangles for each prayer in the prayer book menu relative to the control panel, storing it in the class property.
        """
        self.prayers = []
        slot_w, slot_h = 34, 34  # dimensions of the prayers
        gap_x, gap_y = 3, 3  # pixel gap between prayers
        y = 46 + cp.top  # start y relative to cp template
        for _ in range(6):
            x = 30 + cp.left  # start x relative to cp template
            for _ in range(5):
                self.prayers.append(Rectangle(left=x, top=y, width=slot_w, height=slot_h))
                x += slot_w + gap_x
            y += slot_h + gap_y
        del self.prayers[29]  # remove the last prayer (unused)

    def __locate_spells(self, cp: Rectangle) -> None:
        """
        Creates Rectangles for each magic spell relative to the control panel, storing it in the class property.
        Currently only populates the normal spellbook spells.
        """
        self.spellbook_normal = []
        slot_w, slot_h = 22, 22  # dimensions of a spell
        gap_x, gap_y = 4, 2  # pixel gap between spells
        y = 37 + cp.top  # start y relative to cp template
        for _ in range(10):
            x = 30 + cp.left  # start x relative to cp template
            for _ in range(7):
                self.spellbook_normal.append(Rectangle(left=x, top=y, width=slot_w, height=slot_h))
                x += slot_w + gap_x
            y += slot_h + gap_y

    def __locate_game_view(self, client_rect: Rectangle) -> bool:
        """
        Locates the game view while considering the client mode (Fixed/Resizable). https://i.imgur.com/uuCQbxp.png
        Args:
            client_rect: The client area to search in.
        Returns:
            True if successful, False otherwise.
        """
        if self.minimap_area is None or self.chat is None or self.control_panel is None:
            print("Window.__locate_game_view(): Failed to locate game view. Missing minimap, chat, or control panel.")
            return False
        if self.client_fixed:
            # Uses the chatbox and known fixed size of game_view to locate it in fixed mode
            self.game_view = Rectangle(left=self.chat.left, top=self.chat.top - 337, width=517, height=337)
        else:
            # Uses control panel to find right-side bounds of game view in resizable mode
            self.game_view = Rectangle.from_points(
                Point(
                    client_rect.left + self.padding_left,
                    client_rect.top + self.padding_top,
                ),
                self.control_panel.get_bottom_right(),
            )
            # Locate the positions of the UI elements to be subtracted from the game_view, relative to the game_view
            minimap = self.minimap_area.to_dict()
            minimap["left"] -= self.game_view.left
            minimap["top"] -= self.game_view.top

            chat = self.chat.to_dict()
            chat["left"] -= self.game_view.left
            chat["top"] -= self.game_view.top

            control_panel = self.control_panel.to_dict()
            control_panel["left"] -= self.game_view.left
            control_panel["top"] -= self.game_view.top

            self.game_view.subtract_list = [minimap, chat, control_panel]
        self.mouseover = Rectangle(left=self.game_view.left, top=self.game_view.top, width=407, height=26)
        return True

    def __locate_minimap(self, client_rect: Rectangle) -> bool:
        """
        Locates the minimap area on the clent window and all of its internal positions.
        Args:
            client_rect: The client area to search in.
        Returns:
            True if successful, False otherwise.
        """
        # 'm' refers to minimap area
        if m := imsearch.search_img_in_rect(imsearch.BOT_IMAGES.joinpath("ui_templates", "minimap.png"), client_rect):
            self.client_fixed = False
            self.compass_orb = Rectangle(left=40 + m.left, top=7 + m.top, width=24, height=26)
            self.hp_orb_text = Rectangle(left=4 + m.left, top=60 + m.top, width=20, height=13)
            self.minimap = Rectangle(left=52 + m.left, top=5 + m.top, width=154, height=155)
            self.prayer_orb = Rectangle(left=30 + m.left, top=86 + m.top, width=20, height=20)
            self.prayer_orb_text = Rectangle(left=4 + m.left, top=94 + m.top, width=20, height=13)
            self.run_orb = Rectangle(left=39 + m.left, top=118 + m.top, width=20, height=20)
            self.run_orb_text = Rectangle(left=14 + m.left, top=126 + m.top, width=20, height=13)
            self.spec_orb = Rectangle(left=62 + m.left, top=144 + m.top, width=18, height=20)
            self.spec_orb_text = Rectangle(left=36 + m.left, top=151 + m.top, width=20, height=13)
            self.total_xp = Rectangle(left=m.left - 147, top=m.top + 4, width=104, height=21)
        elif m := imsearch.search_img_in_rect(imsearch.BOT_IMAGES.joinpath("ui_templates", "minimap_fixed.png"), client_rect):
            self.client_fixed = True
            self.compass_orb = Rectangle(left=31 + m.left, top=7 + m.top, width=24, height=25)
            self.hp_orb_text = Rectangle(left=4 + m.left, top=55 + m.top, width=20, height=13)
            self.minimap = Rectangle(left=52 + m.left, top=4 + m.top, width=147, height=160)
            self.prayer_orb = Rectangle(left=30 + m.left, top=80 + m.top, width=19, height=20)
            self.prayer_orb_text = Rectangle(left=4 + m.left, top=89 + m.top, width=20, height=13)
            self.run_orb = Rectangle(left=40 + m.left, top=112 + m.top, width=19, height=20)
            self.run_orb_text = Rectangle(left=14 + m.left, top=121 + m.top, width=20, height=13)
            self.spec_orb = Rectangle(left=62 + m.left, top=137 + m.top, width=19, height=20)
            self.spec_orb_text = Rectangle(left=36 + m.left, top=146 + m.top, width=20, height=13)
            self.total_xp = Rectangle(left=m.left - 104, top=m.top + 6, width=104, height=21)
        if m:
            # Take a bite out of the bottom-left corner of the minimap to exclude orb's green numbers
            self.minimap.subtract_list = [{"left": 0, "top": self.minimap.height - 20, "width": 20, "height": 20}]
            self.minimap_area = m
            return True
        print("Window.__locate_minimap(): Failed to find minimap.")
        return False


class MockWindow(Window):
    def __init__(self):
        super().__init__(window_title="None", padding_left=0, padding_top=0)

    def _get_window(self):
        print("MockWindow._get_window() called.")

    window = property(
        fget=_get_window,
        doc="A Win32Window reference to the game client and its properties.",
    )

    def initialize(self) -> None:
        print("MockWindow.initialize() called.")

    def focus(self) -> None:
        print("MockWindow.focus() called.")

    def position(self) -> Point:
        print("MockWindow.position() called.")
