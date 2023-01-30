
import os, ujson
from robot_position import RobotPosition
from path_finder import PathFinder

class ManuelDirectives:
    def __init__(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__)) # Get the current directory
        self.game_info_path = f'{self.dir_path}/game_info.ujson' # Path to the game info file
        self.file_path = os.path.join(self.dir_path, "positions.ujson") # Path to the positions file
        self.game_info = {}
        self.currentcell = []
        self.robotPositionUpdate = RobotPosition()
        self.pathFinder = PathFinder() # Create a path finder object

    def goto(self, targetcell):
        try:
            self.currentcell = self.robotPositionUpdate.updateCurrentCell()
            path = self.pathFinder.findPath(self.currentcell, targetcell) # TODO: Find the path
        except:
            pass