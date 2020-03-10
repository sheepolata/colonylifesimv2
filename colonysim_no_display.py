import ColonyLifeSim
import parameters as p
import environment as env

import time

def main():
    simu = env.Simulation(p.parameters["GRID_W"], p.parameters["GRID_H"], nb_ent=p.initial_params["nb_ent"], nb_food=p.initial_params["nb_food"], nb_river=p.initial_params["nb_river"])

    thread_simu = ColonyLifeSim.ThreadSimulation(simu, p.sim_params["ACTION_TICK"],profiling=True,prof_steps=2000)

    print("LAUNCH COLONY LIFE SIMULATION v2.0, Welcome !")

    thread_simu.start()

if __name__ == '__main__':
    main()