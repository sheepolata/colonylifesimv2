import utils
import parameters as p

#_start and _goal here are Coordinates
def heuristic_cost_estimate(_current, _goal):
    res = utils.distance2p((_current.x, _current.y), (_goal.x, _goal.y))
    # res = _goal.getCost()
    return res

def reconstructPath(came_from, current):
    total_path = [current]
    while current in came_from.keys():
        current = came_from[current]
        total_path.append(current)

    return list(reversed(total_path)) #+ [total_path[-1]]

#start and goal are tiles, heur is the heuristic method
#grid is the grid's environment
def astar(_start, _goal, grid, forbidden=[], heur=heuristic_cost_estimate, cost_dict=p.type2cost, dn=False):
    if _goal.get_type() in forbidden:
        print("Error: goal tile has a forbidden type")
        return None

    # The set of nodes already evaluated
    closedSet = []

    # The set of currently discovered nodes that are not evaluated yet.
    # Initially, only the start node is known.
    openSet = [_start]

    # For each node, which node it can most efficiently be reached from.
    # If a node can be reached from many nodes, cameFrom will eventually contain the
    # most efficient previous step.
    came_from = {}

    # For each node, the cost of getting from the start node to that node.
    g_score = {}
    for x in range(grid.width):
        for y in range(grid.height):
            g_score[grid.grid[x][y]] = float("inf")

    # The cost of going from start to start is zero.
    g_score[_start] = 0.0

    # For each node, the total cost of getting from the start node to the goal
    # by passing by that node. That value is partly known, partly heuristic.
    f_score = {}
    for x in range(grid.width):
        for y in range(grid.height):
            f_score[grid.grid[x][y]] = float("inf")
    f_score[_start] = heur(_start, _goal)


    while openSet:
        #current = Node in openSet with the lowest f_score
        mini = float("inf")
        current = None
        for elt in openSet:
            if mini >= f_score[elt]:
                mini = f_score[elt]
                current = elt

        if current == None:
            print("Error : current == None")
            return []

        if current == _goal:
            return reconstructPath(came_from, current)

        openSet.remove(current)
        closedSet.append(current)

        for _neighbour in grid.get_neighbours_of(current, diag_neigh=dn):
            if _neighbour in closedSet:
                continue

            if _neighbour not in openSet:
                openSet.append(_neighbour)

            #The distance from start to a neighbor
            #the "dist_between" function may vary as per the solution requirements.
            #May add utils.distance2p(current.getPose(), _neighbour.getPose()) to cost BUT decrease perf quite a lot
            tentative_gScore = (g_score[current] + _neighbour.get_cost(cost_dict=cost_dict))

            if tentative_gScore >= g_score[_neighbour] or _neighbour.get_type() in forbidden:
                continue

            came_from[_neighbour] = current
            g_score[_neighbour] = tentative_gScore
            f_score[_neighbour] = g_score[_neighbour] + heur(_neighbour, _goal)

    print("Error: All grid explored but no solution")
    return None

def computePathLength(path, cost_dict=p.type2cost):
    if not path:
        return -1
    if len(path) == 1:
        return 0
    res = path[0].get_cost(cost_dict=cost_dict)
    for i in range(1, len(path)):
        res = res + path[i].get_cost(cost_dict=cost_dict)
    return res

def getPathLength(tile1, tile2, grid, forbidden=[], heur=heuristic_cost_estimate, approx=False, cost_dict=p.type2cost, dn=False):
    if approx:
        res = utils.distance2p((tile1.x, tile1.y), (tile2.x, tile2.y))
    else:
        path = astar(tile1, tile2, grid, forbidden, heur, cost_dict, dn)
        res = computePathLength(path, cost_dict)
    return res