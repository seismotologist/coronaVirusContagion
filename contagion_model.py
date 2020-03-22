import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches


class ContagionSimulator:

    def __init__(self):
        pass

    def set_params(self, params):
        """
        Set model parameters from dictionary
        """
        self.__dict__.update(params)
        pass

    def initialise(self):
        """
        Initialise buffers for simulation
        """

        nagents = self.nagents

        """
        Initialise agents
        """
        # Position
        self.x = np.random.rand(nagents)
        self.y = np.random.rand(nagents)
        # Cache initial positions
        self.xbak = self.x.copy()
        self.ybak = self.y.copy()
        # Direction
        alpha = 2 * np.pi * np.random.rand(nagents)
        self.dx = self.dr * np.sin(alpha)
        self.dy = self.dr * np.cos(alpha)

        # Agent status
        self.doesSD = np.floor(np.random.rand(nagents) + self.fractSD).astype(bool)
        self.isVulnerable = np.ones(nagents, dtype=bool)
        self.isSick = np.zeros(nagents, dtype=bool)
        self.isImmune = np.zeros(nagents, dtype=bool)
        self.agentStatus = np.zeros(nagents, dtype=int)
        self.tSick = np.zeros(nagents)

        # Patient zero (literally, because Python starts counting at 0 and not 1 like in MATLAB)
        iseed = 0
        self.isSick[iseed] = True
        self.doesSD[iseed] = False
        self.agentStatus[iseed] = 1

        """
        Initialise events and times
        """
        self.tGoToMarket = np.random.randint(low=1, high=self.dtGoToMarket, size=nagents)
        self.tAtMarket = np.zeros(nagents)
        self.isAtMarket = np.zeros(nagents, dtype=bool)
        self.stayAtMarket = np.zeros(nagents, dtype=bool)

        """
        Initialise health status counts
        """
        nt = self.nt
        self.nvulnerable = np.zeros(nt) * np.nan
        self.nsick = np.zeros(nt) * np.nan
        self.nimmune = np.zeros(nt) * np.nan
        self.tt = np.arange(nt) / self.tstepsperday
        pass

    def run_simulation(self, fig, save_file="contagion.mp4"):
        # Initialise buffers
        self.initialise()

        # Create animation from simulation
        self.fig = fig
        self.ani = animation.FuncAnimation(
            self.fig, self.update_plot, interval=100, init_func=self.init_plot,
            blit=True, frames=self.nt, repeat=False
        )
        self.ani.save(save_file)
        plt.show()
        pass

    def go_to_market(self, ia):
        """
        Position an agent at a random location inside the market
        """
        self.x[ia] = self.xmarket + np.random.rand() * self.marketsize
        self.y[ia] = self.ymarket + np.random.rand() * self.marketsize
        self.tGoToMarket[ia] = -1
        self.isAtMarket[ia] = True
        pass

    def return_from_market(self, ia):
        """
        Place an agent back from the market to its original position
        """
        self.x[ia] = self.xbak[ia]
        self.y[ia] = self.ybak[ia]
        self.tGoToMarket[ia] = self.dtGoToMarket
        self.tAtMarket[ia] = 0
        self.isAtMarket[ia] = False
        pass

    def take_step(self, ia):
        """
        Let the agent move around one step
        """
        xnew = self.x[ia] + self.dx[ia]
        ynew = self.y[ia] + self.dy[ia]

        # Check for domain boundaries
        hitWall = (xnew > 1) | (xnew < 0) | (ynew > 1) | (ynew < 0)
        ntries = 0
        stillTrying = True
        # If the agent is moving outside of the domain
        while hitWall and stillTrying:
            # New random direction vector
            alpha = 2 * np.pi * np.random.rand()
            self.dx[ia] = self.dr * np.sin(alpha)
            self.dy[ia] = self.dr * np.cos(alpha)
            # New location
            xnew = self.x[ia] + self.dx[ia]
            ynew = self.y[ia] + self.dy[ia]
            # If new location is still outside domain: try again
            hitWall = (xnew > 1) | (xnew < 0) | (ynew > 1) | (ynew < 0)
            ntries += 1
            if ntries > 100:
                stillTrying = False

        # Update position
        self.x[ia] = xnew
        self.y[ia] = ynew
        pass

    def stay_put(self, ia):
        """
        Do nothing
        """
        pass

    def check_health(self, ia):
        """
        Check the health status of the agent
        """
        if self.isSick[ia]:
            # Increment sick timer
            self.tSick[ia] += 1
            # If sick timer exceeds time to get better
            if self.tSick[ia] > self.dtHeal:
                # Agent is no longer sick
                self.isSick[ia] = False
                # AGent is immune
                self.isImmune[ia] = True
                self.agentStatus[ia] = 2

    def check_contagion(self, ia):
        """
        Let the agent contaminate others
        """
        if self.isSick[ia]:
            # Compute the distance between the agent and others
            xdist = self.x[ia] - self.x
            ydist = self.y[ia] - self.y
            r = np.sqrt(xdist**2 + ydist**2)
            # All agents within contagion distance
            meetAgents = (r <= self.rcont)
            # Who is at home?
            isHome = (self.x == self.xbak) & (self.y == self.ybak)
            # Infect those within contagion distance,
            # who are not immune, and who are not at home
            inds = (meetAgents & ~self.isImmune & ~isHome)
            self.isSick[inds] = True
            self.agentStatus[inds] = 1

    def count_cases(self, it):
        """
        Count the number of sick/immune agents
        """
        self.isVulnerable = (~self.isSick & ~self.isImmune)
        self.nvulnerable[it] = self.isVulnerable.sum()
        self.nsick[it] = self.isSick.sum()
        self.nimmune[it] = self.isImmune.sum()
        nall = self.nvulnerable[it] + self.nsick[it] + self.nimmune[it]
        if nall != self.nagents:
            print("Counts don't add up")
            self.break_simulation = True
        pass

    def simulation_step(self, it):
        """
        Perform one simulation step
        """

        tGoToMarket = self.tGoToMarket
        isAtMarket = self.isAtMarket
        tAtMarket = self.tAtMarket
        stayAtMarket = self.stayAtMarket
        dtAtMarket = self.dtAtMarket
        xbak = self.xbak
        ybak = self.ybak
        x = self.x
        y = self.y
        doesSD = self.doesSD

        # Loop over all agents
        for ia in range(self.nagents):
            # Decrement time to go to the market
            tGoToMarket[ia] -= 1
            # If agent is at the market
            if isAtMarket[ia]:
                # Increment time at the market
                tAtMarket[ia] += 1
                # Check if agent will stay at the market
                stayAtMarket[ia] = (tAtMarket[ia] < dtAtMarket)
            else:
                xbak[ia] = x[ia]
                ybak[ia] = y[ia]

            # Reset nextMove
            nextMove = None

            # If agent doesn't need to go to the market
            if tGoToMarket[ia] > 0:
                # If agent doesn't practise social distancing
                if not doesSD[ia]:
                    # Walk around
                    nextMove = "take_step"
                # If agent practises social distancing
                else:
                    # Stay put
                    nextMove = "stay_put"

            # If agent is at the market
            if isAtMarket[ia]:
                # If agent still needs toilet paper
                if tAtMarket[ia] < dtAtMarket:
                    nextMove = "stay_put"
                # Else go home
                elif tAtMarket[ia] == dtAtMarket:
                    nextMove = "return_from_market"

            # If agent needs toilet paper
            if tGoToMarket[ia] == 0:
                nextMove = "go_to_market"

            # print(f"Next action of agent {ia} at ({x[ia]}, {y[ia]}): {nextMove}")

            # If the nextMove is not defined (should never happen
            if nextMove is None:
                print(it, ia, tGoToMarket[ia], isAtMarket[ia])
                exit()

            # Call the method corresponding to nextMove
            move = getattr(self, nextMove)
            move(ia)

            # Check health status
            self.check_health(ia)

            # Contaminate others
            self.check_contagion(ia)

        # Count cases
        self.count_cases(it)
        pass

    def init_plot(self):
        """
        Initialise the animation window
        """
        # Initialise buffers
        self.initialise()

        # Location of the market
        ms = self.marketsize
        xm = self.xmarket
        ym = self.ymarket
        rect = patches.Rectangle((xm, ym), ms, ms, linewidth=2, edgecolor="k", facecolor="none")

        # Health status colours
        self.colours = ["C0", "r", "C2"]
        cm = LinearSegmentedColormap.from_list("agent_colours", self.colours, N=3)

        # Plotting panels
        gs = gridspec.GridSpec(ncols=1, nrows=3, figure=self.fig)

        # Panel 1: time series of health status
        self.ax_plt = self.fig.add_subplot(gs[0])
        # Number of sick agents
        self.nsick_plt, = self.ax_plt.plot(self.tt[0], self.nsick[0], "-", c="r", label="Sick")
        # Number of immune agents
        self.nimmune_plt, = self.ax_plt.plot(self.tt[0], self.nimmune[0], "-", c="C2", label="Immune")
        # Format axes
        self.ax_plt.set_xlim((0, self.nt / self.tstepsperday))
        self.ax_plt.set_ylim((-1, 1.1*self.nagents))
        self.ax_plt.legend(ncol=1, loc="upper left")
        self.ax_plt.set_ylabel("Count")
        self.ax_plt.set_xlabel("Time [days]")

        # Panel 2: scatter plot of agents
        self.ax_sct = self.fig.add_subplot(gs[1:])
        # Add supermarket
        self.ax_sct.add_patch(rect)
        # Plot agents
        self.sct = self.ax_sct.scatter(self.x, self.y, c=self.agentStatus, cmap=cm, vmin=0, vmax=2)
        # Format axes
        self.ax_sct.set_xlim((0, 1))
        self.ax_sct.set_ylim((0, 1))
        self.ax_sct.set_xticks([])
        self.ax_sct.set_yticks([])

        self.fig.tight_layout()
        self.fig.subplots_adjust(top=0.95, bottom=0.05, left=0.1, right=0.95)

        return self.nsick_plt, self.nimmune_plt, self.sct,

    def update_plot(self, it):
        # Do one simulation step
        self.simulation_step(it)
        # Agent coordinates
        pos = np.c_[self.x, self.y]
        # Update agent positions
        self.sct.set_offsets(pos)
        # Update agent colours
        self.sct.set_array(self.agentStatus)
        # Update time series
        self.nsick_plt.set_data(self.tt[:it], self.nsick[:it])
        self.nimmune_plt.set_data(self.tt[:it], self.nimmune[:it])

        return self.nsick_plt, self.nimmune_plt, self.sct,


if __name__ == "__main__":

    params = {
        # Model parameters
        "nagents": 200,         # No. of agents
        "tstepsperday": 5,      # No. of time steps per day (affects display only)
        "nt": 150,              # No. of time steps of simulation
        "fractSD": .75,         # Fraction of people who practice social distancing
        "dtGoToMarket": 25,     # Every <dtGoToMarket> time steps, people go to the market
        "dtAtMarket": 1,        # No. of time steps spent at market
        "dtHeal": 50,           # Time after which peple recover, and become immune
        "rcont": .04,           # Distance below which agents pass on disease
        "dr": .02,              # Step length per time step
        "marketsize": .1,       # Market size
        "xmarket": .5,          # Market location
        "ymarket": .5,
    }

    simulator = ContagionSimulator()
    simulator.set_params(params)
    simulator.run_simulation(plt.figure())

