
import os, ujson

# info PathFinder Class to find the path
# info This class is used to find the path from the robot to the target cell
# info The path is found using the A* algorithm
# info Every cell has 4 neighbors
# IMPORTANT IT CAN BE IMPROVED, NOT DONE...

class PathFinder:
    def __init__(self, gridSize, colors): # points ex.: {"B":1, "G":3, "Y":4}
        self.gridSize = gridSize
        self.colors = colors
        self.paths = []
        self.previousStep = None

    def findNeighbors(self, cell):
        try:
            neighbors = []
            if cell[0]+1 <= self.gridSize[0]-1 and self.colors[cell[0] + 1][cell[1]] in ['W','G','Y','B']:
                neighbors.append([cell[0] + 1, cell[1]])
            if cell[0]-1 >= 0 and self.colors[cell[0] - 1][cell[1]] in ['W', 'G', 'Y', 'B']:
                neighbors.append([cell[0] - 1, cell[1]])
            if cell[1]+1 <= self.gridSize[1]-1 and self.colors[cell[0]][cell[1] + 1] in ['W','G','Y','B']:
                neighbors.append([cell[0], cell[1] + 1])
            if cell[1]-1 >= 0 and self.colors[cell[0]][cell[1] - 1] in ['W', 'G', 'Y', 'B']:
                neighbors.append([cell[0], cell[1] - 1])
            return neighbors
        except:
            return []

    def findPathRecursive(self, startcell, targetcell, path=[]):
        neighbors = self.findNeighbors(startcell)
        if self.previousStep in neighbors:
            neighbors.remove(self.previousStep) # Prevents going back and forth

        if targetcell in neighbors:
            foundPath = path + [startcell] + [targetcell]
            self.paths.append(foundPath)

        else:    
            path.append(startcell)
            self.previousStep = startcell

        for neighbor in neighbors:
            if neighbor in path:
                neighbors.remove(neighbor)
        if len(neighbors) == 0:
            dangerZone = path[-1]
            path.pop()
            if len(path) > 0:
                self.previousStep = path[-1]
                neighbors = self.findNeighbors(path[-1])
                if dangerZone in neighbors:
                    neighbors.remove(dangerZone)
                if self.previousStep in neighbors:
                    neighbors.remove(self.previousStep) # Prevents going back and forth
                for neighbor in neighbors:
                    if neighbor in path:
                        neighbors.remove(neighbor)
        else:
            for neighbor in neighbors:
                if neighbor not in path and targetcell not in neighbors:
                    self.findPathRecursive(neighbor, targetcell, path=path)

    def findPath(self, startcell, targetcell):
        self.paths = []
        self.findPathRecursive(startcell, targetcell)
        return self.paths