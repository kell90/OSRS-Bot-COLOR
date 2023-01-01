"""
API utility for MorgHTTPClient socket plugin.

Item IDs: https://www.runelocus.com/tools/osrs-item-id-list/
"""
import time
from typing import List, Tuple, Union

import animation_ids
import requests
from deprecated import deprecated
from requests.exceptions import ConnectionError


class SocketError(Exception):
    def __init__(self, error_message: str, endpoint: str):
        self.__error_message = error_message
        self.__endpoint = endpoint
        super().__init__(self.get_error())

    def get_error(self):
        return f"{self.__error_message} endpoint: '{self.__endpoint}'"


class MorgHTTPSocket:
    # TODO: ID/NPC ID/Object ID conversion function/dict to get the readable name of an object

    def __init__(self):
        self.base_endpoint = "http://localhost:8081/"

        self.inv_endpoint = "inv"
        self.stats_endpoint = "stats"
        self.equip_endpoint = "equip"
        self.events_endpoint = "events"

        self.timeout = 1

    def __do_get(self, endpoint: str) -> dict:
        """
        Args:
                endpoint: One of either "inv", "stats", "equip", "events"
        Returns:
                All JSON data from the endpoint as a dict.
        Raises:
                SocketError: If the endpoint is not valid or the server is not running.
        """
        try:
            response = requests.get(f"{self.base_endpoint}{endpoint}", timeout=self.timeout)
        except ConnectionError as e:
            raise SocketError("Unable to reach socket", endpoint) from e

        if response.status_code != 200:
            if response.status_code == 204:
                raise SocketError(
                    f"Endpoint not available, make sure you are fully logged in, status code: {response.status_code}",
                    endpoint,
                )
            else:
                raise SocketError(
                    f"Unable to reach socket, status code: {response.status_code}",
                    endpoint,
                )

        return response.json()

    def test_endpoints(self) -> bool:
        """
        Ensures all endpoints are working correctly to avoid errors happening when any method is called

        Returns:
                True if successful False otherwise
        """
        for i in list(self.__dict__.values())[1:-1]:  # Look away
            try:
                self.__do_get(endpoint=i)
            except SocketError as e:
                print(e)
                print(f"Endpoint '{i}' is not working.")
                return False
        return True

    def get_hitpoints(self) -> Union[Tuple[int, int], None]:
        """
        Fetches the current and maximum hitpoints of the player.
        Returns:
                A Tuple(current_hitpoints, maximum_hitpoints), or None if an error occurred.
        """
        try:
            data = self.__do_get(endpoint=self.events_endpoint)
        except SocketError as e:
            print(e)
            return None
        hitpoints_data = data["health"]
        cur_hp, max_hp = hitpoints_data.split("/")  # hitpoints_data example = "21/21"
        return int(cur_hp), int(max_hp)

    def get_run_energy(self) -> Union[int, None]:
        """
        Fetches the current run energy of the player.
        Returns:
                An int representing the current run energy, or None if an error occurred.
        """
        try:
            data = self.__do_get(endpoint=self.events_endpoint)
        except SocketError as e:
            print(e)
            return None
        return int(data["run energy"])

    def get_animation(self) -> Union[int, None]:
        """
        Fetches the current animation the actor is performing.
        Returns:
                An int representing the current animation, or None if an error occurred.
        """
        try:
            data = self.__do_get(endpoint=self.events_endpoint)
        except SocketError as e:
            print(e)
            return None
        return int(data["animation"])

    def get_animation_id(self) -> Union[int, None]:
        """
        Fetches the current animation frame ID the actor is using. Useful for checking if the player is doing
        a particular action.
        Returns:
                An int representing the current animation ID, or None if an error occurred.
        """
        try:
            data = self.__do_get(endpoint=self.events_endpoint)
        except SocketError as e:
            print(e)
            return None
        return int(data["animation pose"])

    def get_is_player_idle(self) -> Union[bool, None]:
        """
        Checks if the player is doing an idle animation.
        Returns:
                True if the player is idle, False otherwise, or None if an error occurred.
        """
        # run a loop for 1 second
        start_time = time.time()
        while time.time() - start_time < 1:
            try:
                data = self.__do_get(endpoint=self.events_endpoint)
            except SocketError as e:
                print(e)
                return None

            if data["animation"] != animation_ids.IDLE or data["animation pose"] not in [808, 813]:
                return False
        return True
    
    def get_is_player_woodcutting(self) -> Union[bool, None]:
        """
        Checks if the player is doing a woodcutting animation.
        Returns:
                True if the player is woodcutting, False otherwise, or None if an error occurred.
        """
        # run a loop for 1 second
        start_time = time.time()
        while time.time() - start_time < 1:
            try:
                data = self.__do_get(endpoint=self.events_endpoint)
            except SocketError as e:
                print(e)
                return None
            if data["animation"] not in animation_ids.WOODCUTTING:
                return False
        return True
    
    def get_is_player_mining(self) -> Union[bool, None]:
        """
        Checks if the player is doing a mining animation.
        Returns:
                True if the player is mining, False otherwise, or None if an error occurred.
        """
        # run a loop for 1 second
        start_time = time.time()
        while time.time() - start_time < 1:
            try:
                data = self.__do_get(endpoint=self.events_endpoint)
            except SocketError as e:
                print(e)
                return None
            if data["animation"] not in animation_ids.MINING:
                return False
        return True
    
    def get_is_player_smithing(self) -> Union[bool, None]:
        """
        Checks if the player is doing a smithing animation.
        Returns:
                True if the player is smithing, False otherwise, or None if an error occurred.
        """
        # run a loop for 1 second
        start_time = time.time()
        while time.time() - start_time < 1:
            try:
                data = self.__do_get(endpoint=self.events_endpoint)
            except SocketError as e:
                print(e)
                return None
            if data["animation"] not in animation_ids.SMITHING:
                return False
        return True
    
    def get_is_player_fishing(self) -> Union[bool, None]:
        """
        Checks if the player is doing a fishing animation.
        Returns:
                True if the player is fishing, False otherwise, or None if an error occurred.
        """
        # run a loop for 1 second
        start_time = time.time()
        while time.time() - start_time < 1:
            try:
                data = self.__do_get(endpoint=self.events_endpoint)
            except SocketError as e:
                print(e)
                return None
            if data["animation"] not in animation_ids.FISHING:
                return False
        return True
    
    def get_is_player_fletching(self) -> Union[bool, None]:
        """
        Checks if the player is doing a fletching animation.
        Returns:
                True if the player is fletching, False otherwise, or None if an error occurred.
        """
        # run a loop for 1 second
        start_time = time.time()
        while time.time() - start_time < 1:
            try:
                data = self.__do_get(endpoint=self.events_endpoint)
            except SocketError as e:
                print(e)
                return None
            if data["animation"] not in animation_ids.FLETCHING:
                return False
        return True
    
    def get_is_player_cooking(self) -> Union[bool, None]:
        """
        Checks if the player is doing a cooking animation.
        Returns:
                True if the player is cooking, False otherwise, or None if an error occurred.
        """
        # run a loop for 1 second
        start_time = time.time()
        while time.time() - start_time < 1:
            try:
                data = self.__do_get(endpoint=self.events_endpoint)
            except SocketError as e:
                print(e)
                return None
            if data["animation"] not in animation_ids.COOKING:
                return False
        return True
    
    def get_is_player_casting_magic(self) -> Union[bool, None]:
        """
        Checks if the player is doing a casting magic animation.
        Returns:
                True if the player is casting magic, False otherwise, or None if an error occurred.
        """
        # run a loop for 1 second
        start_time = time.time()
        while time.time() - start_time < 1:
            try:
                data = self.__do_get(endpoint=self.events_endpoint)
            except SocketError as e:
                print(e)
                return None
            if data["animation"] not in animation_ids.MAGIC:
                return False
        return True
    
    def get_is_player_hunting(self) -> Union[bool, None]:
        """
        Checks if the player is doing a hunter animation.
        Returns:
                True if the player is hunter, False otherwise, or None if an error occurred.
        """
        # run a loop for 1 second
        start_time = time.time()
        while time.time() - start_time < 1:
            try:
                data = self.__do_get(endpoint=self.events_endpoint)
            except SocketError as e:
                print(e)
                return None
            if data["animation"] not in animation_ids.HUNTER:
                return False
        return True
    
    def get_is_player_doing_herblore(self) -> Union[bool, None]:
        """
        Checks if the player is doing a herblore animation.
        Returns:
                True if the player is herblore, False otherwise, or None if an error occurred.
        """
        # run a loop for 1 second
        start_time = time.time()
        while time.time() - start_time < 1:
            try:
                data = self.__do_get(endpoint=self.events_endpoint)
            except SocketError as e:
                print(e)
                return None
            if data["animation"] not in animation_ids.HERBLORE:
                return False
        return True
    
    def get_is_player_gem_cutting(self) -> Union[bool, None]:
        """
        Checks if the player is doing a gem cutting animation.
        Returns:
                True if the player is gem cutting, False otherwise, or None if an error occurred.
        """
        # run a loop for 1 second
        start_time = time.time()
        while time.time() - start_time < 1:
            try:
                data = self.__do_get(endpoint=self.events_endpoint)
            except SocketError as e:
                print(e)
                return None
            if data["animation"] not in animation_ids.GEM_CUTTING:
                return False
        return True
    
    def get_is_player_farming(self) -> Union[bool, None]:
        """
        Checks if the player is doing a farming animation.
        Returns:
                True if the player is farming, False otherwise, or None if an error occurred.
        """
        # run a loop for 1 second
        start_time = time.time()
        while time.time() - start_time < 1:
            try:
                data = self.__do_get(endpoint=self.events_endpoint)
            except SocketError as e:
                print(e)
                return None
            if data["animation"] not in animation_ids.FARMING:
                return False
        return True
    
    def get_is_player_crafting(self) -> Union[bool, None]:
        """
        Checks if the player is doing a crafting animation.
        Returns:
                True if the player is crafting, False otherwise, or None if an error occurred.
        """
        # run a loop for 1 second
        start_time = time.time()
        while time.time() - start_time < 1:
            try:
                data = self.__do_get(endpoint=self.events_endpoint)
            except SocketError as e:
                print(e)
                return None
            if data["animation"] not in animation_ids.CRAFTING:
                return False
        return True

    def get_skill_level(self, skill: str) -> Union[int, None]:
        """
        Gets level of inputted skill.
        Args:
                skill: the name of the skill (not case sensitive)
        Returns:
                The level of the skill as an int, or None if an error occurred.
        """
        # TODO: Make class for stat_names to make invalid names impossible
        skill = skill.lower().capitalize()
        try:
            data = self.__do_get(endpoint=self.stats_endpoint)
        except SocketError as e:
            print(e)
            return None

        try:
            level = next(int(i["level"]) for i in data[1:] if i["stat"] == skill)
        except StopIteration:
            print(f"Invalid stat name: {skill}")
            return None

        return level

    def get_skill_xp(self, skill: str) -> Union[int, None]:
        """
        Gets the total xp of a skill.
        Args:
                skill: the name of the skill (not case sensitive)
        Returns:
                The total xp of the skill as an int, or None if an error occurred.
        """
        skill = skill.lower().capitalize()
        try:
            data = self.__do_get(endpoint=self.stats_endpoint)
        except SocketError as e:
            print(e)
            return None

        try:
            total_xp = next(int(i["xp"]) for i in data[1:] if i["stat"] == skill)
        except StopIteration:
            print(f"Invalid stat name: {skill}")
            return None

        return total_xp

    def get_skill_xp_gained(self, skill: str) -> Union[int, None]:
        """
        Gets the xp gained of a skill. The tracker begins at 0 on client startup.
        Args:
                skill: the name of the skill (not case sensitive)
        Returns:
                The xp gained of the skill as an int, or None if an error occurred.
        """
        skill = skill.lower().capitalize()  # Ensures str is formatted correctly for socket json key
        try:
            data = self.__do_get(endpoint=self.stats_endpoint)
        except SocketError as e:
            print(e)
            return None

        try:
            xp_gained = next(int(i["xp gained"]) for i in data[1:] if i["stat"] == skill)
        except StopIteration:
            print(f"Invalid skill name: {skill}")
            return None

        return xp_gained

    def wait_til_gained_xp(self, skill: str, timeout: int = 10) -> Union[int, None]:
        """
        Waits until the player has gained xp in the inputted skill.
        Args:
                skill: the name of the skill (not case sensitive).
                timeout: the maximum amount of time to wait for xp gain (seconds).
        Returns:
                The xp gained of the skill as an int, or None if an error occurred.
        """
        skill = skill.lower().capitalize()  # Ensures str is formatted correctly for socket json key

        starting_xp = self.get_skill_xp(skill)
        if starting_xp is None:
            print("Failed to get starting xp.")
            return None

        stop_time = time.time() + timeout
        while time.time() < stop_time:
            try:
                data = self.__do_get(endpoint=self.stats_endpoint)
            except SocketError as e:
                print(e)
                return None

            final_xp = next(int(i["xp"]) for i in data[1:] if i["stat"] == skill)
            if final_xp > starting_xp:
                return final_xp

            time.sleep(0.2)

        return None

    def get_game_tick(self) -> Union[int, None]:
        """
        Fetches game tick number.
        Returns:
                An int representing the current game tick, or None if an error occurred.
        """
        try:
            data = self.__do_get(endpoint=self.events_endpoint)
        except SocketError as e:
            print(e)
            return None

        return int(data["game tick"])

    def get_player_position(self) -> Union[SocketError, Tuple[int, int, int]]:
        """
        Fetches the world point of a player.
        Returns:
                A tuple of ints representing the player's world point (x, y, z),
                or None if an error occurred.
        """
        try:
            data = self.__do_get(endpoint=self.events_endpoint)
        except SocketError as e:
            print(e)
            return None

        return (
            int(data["worldPoint"]["x"]),
            int(data["worldPoint"]["y"]),
            int(data["worldPoint"]["plane"]),
        )

    def get_player_region_data(self) -> Union[Tuple[int, int, int], None]:
        """
        Fetches region data of a player's position.
        Returns:
                A tuple of ints representing the player's region data (region_x, region_y, region_ID),
                or None if an error occurred.
        """
        try:
            data = self.__do_get(endpoint=self.events_endpoint)
        except SocketError as e:
            print(e)
            return None

        return (
            int(data["worldPoint"]["regionX"]),
            int(data["worldPoint"]["regionY"]),
            int(data["worldPoint"]["regionID"]),
        )

    def get_camera_position(self) -> Union[dict, None]:
        """
        Fetches the position of a player's camera.
        Returns:
                A dict containing the player's camera position {yaw, pitch, x, y, z, x2, y2, z2},
        """
        try:
            data = self.__do_get(endpoint=self.events_endpoint)
        except SocketError as e:
            print(e)
            return None

        return data["camera"]

    def get_mouse_position(self) -> Union[Tuple[int, int], None]:
        """
        Fetches the position of a player's mouse.
        Returns:
                A tuple of ints representing the player's mouse position (x, y),
                or None if an error occurred.
        """
        try:
            data = self.__do_get(endpoint=self.events_endpoint)
        except SocketError as e:
            print(e)
            return None

        return int(data["mouse"]["x"]), int(data["mouse"]["y"])

    def get_interaction_code(self) -> Union[str, None]:
        """
        Fetches the interacting code of the current interaction. (Use case unknown)
        """
        try:
            data = self.__do_get(endpoint=self.events_endpoint)
        except SocketError as e:
            print(e)
            return None

        return data["interacting code"]

    def get_is_in_combat(self) -> Union[bool, None]:
        """
        Determines if the player is in combat.
        Returns:
                True if the player is in combat, False if not, or None if an error occurred.
        """
        try:
            data = self.__do_get(endpoint=self.events_endpoint)
        except SocketError as e:
            print(e)
            return None

        res = data["npc name"]
        return res != "null"

    @deprecated(reason="This method seems to return unreliable values for the NPC's HP.")
    def get_npc_hitpoints(self) -> Union[int, None]:
        """
        Fetches the HP of the NPC currently targetted.
        TODO: Result seems to be multiplied by 6...?
        Returns:
                An int representing the NPC's HP, or None if an error occurred.
                If no NPC is in combat, returns 0.
        """
        try:
            data = self.__do_get(endpoint=self.events_endpoint)
        except SocketError as e:
            print(e)
            return None

        return int(data["npc health "])

    def get_if_item_in_inv(self, item_id: int) -> Union[bool, None]:
        """
        Checks if an item is in the inventory or not
        Args:
                item_id: the id of the item to check for
        Returns:
                True if the item is in the inventory, False if not, or None if an error occurred.
        """
        try:
            data = self.__do_get(endpoint=self.inv_endpoint)
        except SocketError as e:
            print(e)
            return None

        return any(inventory_slot["id"] == item_id for inventory_slot in data)

    def get_inv_item_indices(self, id: Union[List[int], int]) -> list:
        """
        For the given item ID(s), returns a list of inventory slot indexes that the item exists in.
        Useful for locating items you do not want to drop.
        Args:
                id: The item ID to search for (an single ID, or list of IDs).
        Returns:
                A list of inventory slot indexes that the item(s) exists in.
        """
        try:
            data = self.__do_get(endpoint=self.inv_endpoint)
        except SocketError as e:
            print(e)
            return None

        if isinstance(id, int):
            return [i for i, inventory_slot in enumerate(data) if inventory_slot["id"] == id]
        elif isinstance(id, list):
            return [i for i, inventory_slot in enumerate(data) if inventory_slot["id"] in id]

    @deprecated(reason="This function needs to be rewritten, as one item can't be stacked in multiple slots. Consider get_inv_item_indices instead.")
    def find_item_in_inv(self, item_id: int) -> Union[List[Tuple[int, int]], None]:
        """
        Finds an item in the inventory and returns a list of tuples containing the slot and quantity.
        Args:
                item_id: the id of the item to check for
        Returns:
                A list of tuples containing the slot and quantity of the item [(index, quantity), ...],
                or None if an error occurred.
        """
        try:
            data = self.__do_get(endpoint=self.inv_endpoint)
        except SocketError as e:
            print(e)
            return None

        return [(index, inventory_slot["quantity"]) for index, inventory_slot in enumerate(data) if inventory_slot["id"] == item_id]

    def get_player_equipment(self) -> Union[List[int], None]:
        """
        Currently just gets the ID of the equipment until there is an easier way to convert ID to readable name
        -1 = nothing
        Returns: [helmet, cape, neck, weapon, chest, shield, legs, gloves, boots, ring, arrow]

        NOTE: Socket may be bugged with -1's in the middle of the data even all equipment slots are filled
        """
        try:
            data = self.__do_get(endpoint=self.equip_endpoint)
        except SocketError as e:
            print(e)
            return None

        return [equipment_id["id"] for equipment_id in data]

    def convert_player_position_to_pixels(self):
        """
        Convert a world point into coordinate where to click with the mouse to make it possible to move via the socket.
        TODO: Implement.
        """
        pass


# sourcery skip: remove-redundant-if
if __name__ == "__main__":
    api = MorgHTTPSocket()

    id_logs = 1511
    id_bones = 526

    # Note: Making API calls in succession too quickly can result in issues
    while True:
        # Player Data
        if False:
            # Example of safely getting player data
            if hp := api.get_hitpoints():
                print(f"Current HP: {hp[0]}")
                print(f"Max HP: {hp[1]}")

            print(f"Run Energy: {api.get_run_energy()}")
            print(f"get_animation(): {api.get_animation()}")
            print(f"get_animation_id(): {api.get_animation_id()}")
            print(f"Is player idle: {api.get_is_player_idle()}")

        # World Data
        if False:
            print(f"Game tick: {api.get_game_tick()}")
            print(f"Player position: {api.get_player_position()}")
            print(f"Player region data: {api.get_player_region_data()}")
            print(f"Mouse position: {api.get_mouse_position()}")
            # print(f"get_interaction_code(): {api.get_interaction_code()}")
            print(f"Is in combat?: {api.get_is_in_combat()}")
            print(f"get_npc_health(): {api.get_npc_hitpoints()}")

        # Inventory Data
        if True:
            print(f"Are logs in inventory?: {api.get_if_item_in_inv(item_id=1511)}")
            print(f"Find logs in inv: {api.find_item_in_inv(item_id=1511)}")
            print(f"Get position of all bones in inv: {api.get_inv_item_indices(id=[526])}")

        # Wait for XP to change
        if False:
            print(f"WC Level: {api.get_skill_level('woodcutting')}")
            print(f"WC XP: {api.get_skill_xp('woodcutting')}")
            print(f"WC XP Gained: {api.get_skill_xp_gained('woodcutting')}")
            print("---waiting for wc xp to be gained---")
            if api.wait_til_gained_xp(skill="woodcutting", timeout=10):
                print("Gained xp!")
            else:
                print("No xp gained.")

        time.sleep(2)

        print("\n--------------------------\n")
