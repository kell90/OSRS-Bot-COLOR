import math
import os
from typing import List, NamedTuple

import cv2
import mss
import numpy as np

if __name__ == "__main__":
    import sys

    sys.path[0] = os.path.dirname(sys.path[0])

import utilities.random_util as rd
import utilities.debug as debug

Point = NamedTuple("Point", x=int, y=int)

# TODO: Remove this global variable. This is a temporary fix for a bug in mss.
sct = mss.mss()


class Rectangle:

    """
    In very rare cases, we may want to exclude areas within a Rectangle (E.g., resizable game view).
    This should contain a list of dicts that represent rectangles {left, top, width, height} that
    will be subtracted from this Rectangle during screenshotting.
    """

    subtract_list: List[dict] = []
    parent_rect = None

    def __init__(self, left: int, top: int, width: int, height: int):
        """
        Defines a rectangle area on screen.
        Args:
            left: The leftmost x coordinate of the rectangle.
            top: The topmost y coordinate of the rectangle.
            width: The width of the rectangle.
            height: The height of the rectangle.
            offset: The offset to apply to the rectangle.
        Returns:
            A Rectangle object.
        """
        self.left = left
        self.top = top
        self.width = width
        self.height = height

    def scale(self, scale_width: float = 1, scale_height: float = 1, anchor_x: float = 0.5, anchor_y: float = 0.5):
        """
        Scales the rectangle by the given factors for width and height, and adjusts its position based on the anchor point.
        Args:
            scale_width: The scaling factor for the width of the rectangle (default 1).
            scale_height: The scaling factor for the height of the rectangle (default 1).
            anchor_x: The horizontal anchor point for scaling (default 0.5, which corresponds to the center).
            anchor_y: The vertical anchor point for scaling (default 0.5, which corresponds to the center).
        Returns:
            The Rectangle object, after scaling.
        Examples:
            rect = Rectangle(left=10, top=10, width=100, height=100)

            # Scale the rectangle by a factor of 2, using the center as the anchor point (default behavior).
            rect.scale(2, 2)

            # Scale the rectangle by a factor of 2, using the top-left corner as the anchor point.
            rect.scale(2, 2, anchor_x=0, anchor_y=0)

            # Scale the rectangle by a factor of 2, using the bottom-right corner as the anchor point.
            rect.scale(2, 2, anchor_x=1, anchor_y=1)

            # Scale the rectangle width by a factor of 1.5 and height by a factor of 2, using the top-right corner as the anchor point.
            rect.scale(scale_width=1.5, scale_height=2, anchor_x=1, anchor_y=0)
        """
        old_width = self.width
        old_height = self.height

        new_width = int(self.width * scale_width)
        new_height = int(self.height * scale_height)

        x_offset = int(old_width * (1 - scale_width) * anchor_x)
        y_offset = int(old_height * (1 - scale_height) * anchor_y)

        new_left = self.left + x_offset
        new_top = self.top + y_offset

        return Rectangle(new_left, new_top, new_width, new_height)

    def set_parent_rectangle(self, rect):
        """
        Sets the rectangle reference of the object.
        Args:
            rect: A reference to the the rectangle that this object belongs in
                  (E.g., Bot.win.game_view).
        """
        self.parent_rect = rect

    @classmethod
    def from_points(cls, start_point: Point, end_point: Point):
        """
        Creates a Rectangle from two points.
        Args:
            start_point: The first point.
            end_point: The second point.
            offset: The offset to apply to the rectangle.
        Returns:
            A Rectangle object.
        """
        return cls(
            start_point.x,
            start_point.y,
            end_point.x - start_point.x,
            end_point.y - start_point.y,
        )

    def screenshot(self) -> cv2.Mat:
        """
        Screenshots the Rectangle.
        Returns:
            A BGR Numpy array representing the captured image.
        """
        # with mss.mss() as sct:  # TODO: When MSS bug is fixed, reinstate this.
        global sct  # TODO: When MSS bug is fixed, remove this.
        monitor = self.to_dict()
        res = np.array(sct.grab(monitor))[:, :, :3]
        if self.subtract_list:
            for area in self.subtract_list:
                res[
                    area["top"] : area["top"] + area["height"],
                    area["left"] : area["left"] + area["width"],
                ] = 0
        return res

    def random_point(self, custom_seeds: List[List[int]] = None) -> Point:
        """
        Gets a random point within the Rectangle.
        Args:
            custom_seeds: A list of custom seeds to use for the random point. You can generate
                            a seeds list using RandomUtil's random_seeds() function with args.
                            Default: A random seed list based on current date and object position.
        Returns:
            A random Point within the Rectangle.
        """
        if custom_seeds is None:
            center = self.get_center()
            custom_seeds = rd.random_seeds(mod=(center[0] + center[1]))
        x, y = rd.random_point_in(self.left, self.top, self.width, self.height, custom_seeds)
        return Point(x, y)

    def get_center(self) -> Point:
        """
        Gets the center point of the rectangle.
        Returns:
            A Point representing the center of the rectangle.
        """
        return Point(self.left + self.width // 2, self.top + self.height // 2)

    def distance_from_point(self, reference_point: Point = None) -> float:
        """
        Gets the distance between the object and the given reference point.
        Useful for sorting lists of Rectangles.
        Args:
            reference_point: A Point representing the reference point for distance calculation.
                            Default: The center of the parent rectangle, if available.
        Returns:
            The distance from the point to the center of the object.
        Example:
            >>> # Sort based on an arbitrary point
            >>> arbitrary_point = Point(100, 200)
            >>> sorted_by_arbitrary_point = sorted(some_rectangles, key=lambda rect: rect.distance_from_point(arbitrary_point))
        """
        if reference_point is None:
            if self.parent_rect is not None:
                reference_point = self.parent_rect.get_center()
            else:
                raise ValueError("A reference point must be provided if there is no parent rectangle.")

        center: Point = self.get_center()
        return math.dist([center.x, center.y], [reference_point.x, reference_point.y])

    def get_top_left(self) -> Point:
        """
        Gets the top left point of the rectangle.
        Returns:
            A Point representing the top left of the rectangle.
        """
        return Point(self.left, self.top)

    def get_center_left(self) -> Point:
        """
        Gets the center left point of the rectangle.
        Returns:
            A Point representing the center left of the rectangle.
        """
        return Point(self.left, self.top + self.height // 2)

    def get_center_left(self) -> Point:
        """
        Gets the center left point of the rectangle.
        Returns:
            A Point representing the center left of the rectangle.
        """
        return Point(self.left, self.top + self.height // 2)

    def get_top_right(self) -> Point:
        """
        Gets the top right point of the rectangle.
        Returns:
            A Point representing the top right of the rectangle.
        """
        return Point(self.left + self.width, self.top)

    def get_bottom_left(self) -> Point:
        """
        Gets the bottom left point of the rectangle.
        Returns:
            A Point representing the bottom left of the rectangle.
        """
        return Point(self.left, self.top + self.height)

    def get_bottom_right(self) -> Point:
        """
        Gets the bottom right point of the rectangle.
        Returns:
            A Point representing the bottom right of the rectangle.
        """
        return Point(self.left + self.width, self.top + self.height)

    def to_dict(self):
        return {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
        }

    def __str__(self):
        return f"Rectangle(x={self.left}, y={self.top}, w={self.width}, h={self.height})"

    def __repr__(self):
        return self.__str__()


class RuneLiteObject:
    rect = None

    def __init__(self, x_min, x_max, y_min, y_max, width, height, center, axis):
        """
        Represents an outlined object on screen.
        Args:
            x_min, x_max: The min/max x coordinates of the object.
            y_min, y_max: The min/max y coordinates of the object.
            width: The width of the object.
            height: The height of the object.
            center: The center of the object.
            axis: A 2-column stacked array of points that exist inside the object outline.
        """
        self._x_min = x_min
        self._x_max = x_max
        self._y_min = y_min
        self._y_max = y_max
        self._width = width
        self._height = height
        self._center = center
        self._axis = axis

    def scale(self, scale_width: float = 1, scale_height: float = 1, anchor_x: float = 0.5, anchor_y: float = 0.5):
        """
        Scales the RuneLiteObject by the given factors for width and height, and adjusts its position based on the anchor point.
        Args:
            scale_width: The scaling factor for the width of the RuneLiteObject (default 1).
            scale_height: The scaling factor for the height of the RuneLiteObject (default 1).
            anchor_x: The horizontal anchor point for scaling (default 0.5, which corresponds to the center).
            anchor_y: The vertical anchor point for scaling (default 0.5, which corresponds to the center).
        Returns:
            The RuneLiteObject, after scaling.
        Examples:
            obj = RuneLiteObject(x_min=10, x_max=110, y_min=10, y_max=110, width=100, height=100, center=(60, 60), axis=None)

            # Scale the object by a factor of 2, using the center as the anchor point (default behavior).
            obj.scale(2, 2)

            # Scale the object by a factor of 2, using the top-left corner as the anchor point.
            obj.scale(2, 2, anchor_x=0, anchor_y=0)

            # Scale the object by a factor of 2, using the bottom-right corner as the anchor point.
            obj.scale(2, 2, anchor_x=1, anchor_y=1)

            # Scale the object width by a factor of 1.5 and height by a factor of 2, using the top-right corner as the anchor point.
            obj.scale(scale_width=1.5, scale_height=2, anchor_x=1, anchor_y=0)
        """
        newObject = self
        old_width = self._width
        old_height = self._height

        new_width = int(self._width * scale_width)
        new_height = int(self._height * scale_height)

        x_offset = int(old_width * (1 - scale_width) * anchor_x)
        y_offset = int(old_height * (1 - scale_height) * anchor_y)

        new_x_min = self._x_min + x_offset
        new_x_max = new_x_min + new_width
        new_y_min = self._y_min + y_offset
        new_y_max = new_y_min + new_height

        new_center = (round((new_x_min + new_x_max) / 2), round((new_y_min + new_y_max) / 2))

        # Generate all possible combinations of x and y coordinates inside the bounding box
        x_coords = np.arange(new_x_min, new_x_max + 1)
        y_coords = np.arange(new_y_min, new_y_max + 1)
        xx, yy = np.meshgrid(x_coords, y_coords)
        scaled_axis = np.column_stack((xx.ravel(), yy.ravel()))

        newObject._x_min = new_x_min
        newObject._x_max = new_x_max
        newObject._y_min = new_y_min
        newObject._y_max = new_y_max
        newObject._width = new_width
        newObject._height = new_height
        newObject._center = new_center
        newObject._axis = scaled_axis

        return newObject

    def set_parent_rectangle(self, rect: Rectangle):
        """
        Sets the parent rectangle of the object.
        Args:
            rect: A reference to the the rectangle that this object belongs in
                  (E.g., Bot.win.game_view).
        """
        self.rect = rect

    def get_center(self) -> Point:
        """
        Gets the center of the object relative to the screen.
        Returns:
            A Point.
        """
        if self.rect is None:
            raise ReferenceError("The RuneLiteObject is missing a reference to the Rectangle it's contained in and therefore the center cannot be determined.")
        return Point(self._center[0] + self.rect.left, self._center[1] + self.rect.top)

    def distance_from_point(self, point: Point) -> float:
        """
        Gets the distance between the object and the given point.
        Args:
            point: A tuple (x, y) representing the coordinates of the point.
        Returns:
            The distance from the point to the center of the object.
        Example:
            >>> reference_point = Point(300, 200)
            >>> sorted_by_distance = sorted(rl_objects, key=lambda obj: obj.distance_from_point(reference_point))
        """
        center: Point = self.get_center()
        return math.dist([center.x, center.y], [point.x, point.y])

    def distance_from_rect_center(self) -> float:
        """
        Gets the distance between the object and it's Rectangle parent center.
        Useful for sorting lists of RuneLiteObjects.
        Returns:
            The distance from the point to the center of the object.
        Note:
            Only use this if you're sorting a list of RuneLiteObjects that are contained in the same Rectangle.
        """
        center: Point = self.get_center()
        rect_center: Point = self.rect.get_center()
        return math.dist([center.x, center.y], [rect_center.x, rect_center.y])

    def distance_from_rect_left(self) -> float:
        """
        Gets the distance between the object and it's Rectangle parent left edge.
        Useful for sorting lists of RuneLiteObjects.
        Returns:
            The distance from the point to the center of the object.
        Note:
            Only use this if you're sorting a list of RuneLiteObjects that are contained in the same Rectangle.
        """
        center: Point = self.get_center()
        rect_left: Point = self.rect.get_center_left()
        return math.dist([center.x, center.y], [rect_left.x, rect_left.y])

    def distance_from_top_left(self) -> float:
        """
        Gets the distance between the object and it's Rectangle parent top left corner.
        Useful for sorting lists of RuneLiteObjects.
        Returns:
            The distance from the point to the center of the object.
        Note:
            Only use this if you're sorting a list of RuneLiteObjects that are contained in the same Rectangle.
        """
        center: Point = self.get_center()
        rect_left: Point = self.rect.get_top_left()
        return math.dist([center.x, center.y], [rect_left.x, rect_left.y])

    def distance_from_top_right(self) -> float:
        """
        Gets the distance between the object and it's Rectangle parent top right corner.
        Useful for sorting lists of RuneLiteObjects.
        Returns:
            The distance from the point to the center of the object.
        Note:
            Only use this if you're sorting a list of RuneLiteObjects that are contained in the same Rectangle.
        """
        center: Point = self.get_center()
        rect_left: Point = self.rect.get_top_right()
        return math.dist([center.x, center.y], [rect_left.x, rect_left.y])

    def random_point(self, custom_seeds: List[List[int]] = None) -> Point:
        """
        Gets a random point within the object.
        Args:
            custom_seeds: A list of custom seeds to use for the random point. You can generate
                          a seeds list using RandomUtil's random_seeds() function with args.
                          Default: A random seed list based on current date and object position.
        Returns:
            A random Point within the object.
        """
        if custom_seeds is None:
            custom_seeds = rd.random_seeds(mod=(self._center[0] + self._center[1]))
        x, y = rd.random_point_in(self._x_min, self._y_min, self._width, self._height, custom_seeds)
        return self.__relative_point([x, y]) if self.__point_exists([x, y]) else self.get_center()

    def __relative_point(self, point: List[int]) -> Point:
        """
        Gets a point relative to the object's container (and thus, the client window).
        Args:
            point: The point to get relative to the object in the format [x, y].
        Returns:
            A Point relative to the client window.
        """
        return Point(point[0] + self.rect.left, point[1] + self.rect.top)

    def __point_exists(self, p: list) -> bool:
        """
        Checks if a point exists in the object.
        Args:
            p: The point to check in the format [x, y].
        """
        return (self._axis == np.array(p)).all(axis=1).any()


if __name__ == "__main__":
    """
    Run this file directly to test this module. You must have an instance of RuneLite open for this to work.
    """
    # Get/focus the RuneLite window currently running
    win = debug.get_test_window()

    # Screenshot the chat box and display it
    img = win.chat.screenshot()
    cv2.imshow("Chat Box", img)
    cv2.waitKey(0)

    # Screenshot control panel and display it
    img = win.control_panel.screenshot()
    cv2.imshow("Control Panel", img)
    cv2.waitKey(0)

    # Screenshot game view and display it
    img = win.game_view.screenshot()
    cv2.imshow("Game View", img)
    cv2.waitKey(0)
