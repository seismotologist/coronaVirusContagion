# Toy model for contagion of Corona virus, and how Social Distancing (SD)
# affects its spread, inspired by models shown in Washington Post article
# by Harry Stevens, washingtonpost.com/graphics/2020/world/corona-simulator
#
# The model can be used to show how meeting points such as super markets
# can undo the gains made from SD practices. That is, it is crucial to
# minimise the number of trips to such places, and to be extra careful on
# the trips we do have to make.
#
# by Fred Massin, v0.0, 22/03/2020
# fmassin@ethz.ch
# @f_massin
# n.ethz.ch/~fmassin
#
# Feel free to use and modify the model. Please acknowledge
# github.com/FMassin & @f_massin. Thank you (\_/)
# -------------------------------------------------------------------------

import numpy,matplotlib.pyplot

# DESCRIPTION: A fraction of people in simulation ('agents') move around,
# while others practice Social Distancing (SD) and stay home. At home,
# people do not get infected by passing people who carry the virus, but
# they can get infected at the market. Every agent has to go to the market
# at a regular time interval.

# Model parameters
nagents      = 200                # No. of agents
tstepsperday = 5                  # No. of time steps per day (affects display only)
nt           = 150                # No. of time steps of simulation
fractSD      = .75                # Fraction of people who practice social distancing
dtGoToMarket = 5*tstepsperday     # Every <dtGoToMarket> time steps, people go to the market
dtAtMarket   = 1                  # No. of time steps spent at market
dtHeal       = 10*tstepsperday    # Time after which peple recover, and become immune
rcont        = .04                # Distance below which agents pass on disease
dr           = .02                # Step length per time step
marketsize   = .1                 # Market size
xmarket      = .5                 # Market location
ymarket      = .5

# Display parameters
verbose      = False
dtpause      = .01    # simulation speed
mkSize       = 6
writeGif     = True
dtgif        = .2
gifName      = 'contagion_shopping_dtGoToMarket%d_dtHeal%d.gif'%(dtGoToMarket,dtHeal)



# Pseudo-code -----------------------------------------------------
# for it in range(nt):
#     for ia in range(nagents):
#         # 1. Movement (take step/ stay put / go to market / ... )
#         # 2. Health   (pass to others / heal)
#     # Plot
# -------------------------------------------------------------

tString = 'Time between trips to market: %d  days\n'%(dtGoToMarket/tstepsperday)
tString += 'Fraction of people who do Social Distancing: %d%s\n'%(fractSD*100,'%')
tString += 'Time sick: %.1f days'%(dtHeal/tstepsperday)

# Domain is from 0 to 1 in x and y directions; random initial positions and
# directions
x     = numpy.random.rand(nagents)
y     = numpy.random.rand(nagents)
alpha = 2*numpy.pi*numpy.random.rand(nagents)
dx    = dr*numpy.sin(alpha)
dy    = dr*numpy.cos(alpha)

# Who does Social Distancing (SD)?
doesSD = numpy.full((nagents), False)
doesSD[numpy.random.rand(nagents)>(1-fractSD)] = True

# Health status
isVulnerable  = numpy.full((nagents), True)
isSick        = numpy.full((nagents), False)
isImmune      = numpy.full((nagents), False)
tSick         = numpy.zeros((nagents))
iseed         = 0
isSick[iseed] = True
doesSD[iseed] = False

# Supermarket
tGoToMarket  = numpy.random.randint(dtGoToMarket,size=(nagents))   # time until next shopping trip
tAtMarket    = numpy.zeros((nagents))
isAtMarket   = numpy.full((nagents), False)
stayAtMarket = numpy.full((nagents), False)

# Initialise figure
hf = matplotlib.pyplot.figure()
gs = hf.add_gridspec(8,5)
s1 = hf.add_subplot(gs[1, :-1])
s1.set_xlim([0, nt/tstepsperday])
s1.set_ylim([0, nagents])
s1.set_title(tString)
s1.set_xlabel('Days')
s1.set_ylabel('No. of people')

s2 = hf.add_subplot(gs[3:, :])
s2.set_xlim([0, 1])
s2.set_ylim([0, 1])
s2.set_xticks([])
s2.set_yticks([])
rectangle = matplotlib.patches.Rectangle((xmarket, ymarket), marketsize, marketsize, color=[.7, .7, .7])
s2.add_patch(rectangle)

csick       = [v/256 for v in [160,82 , 45]] # Colours
cvulnerable = [v/256 for v in [173,216,230]]
cimmune     = [v/256 for v in [221,160,221]]



# Initial positions
pa1, = s2.plot(x[isVulnerable],y[isVulnerable],'sk',markersize=mkSize,markerfacecolor=cvulnerable)
pa2, = s2.plot(x[isSick],y[isSick],'sk',markersize=mkSize,markerfacecolor=csick)
pa3, = s2.plot(x[isImmune],y[isImmune],'sk',markersize=mkSize,markerfacecolor=cimmune)

xbak = x.copy()
ybak = y.copy()

pa4 = s2.plot([x[isAtMarket],xbak[isAtMarket]], [y[isAtMarket],ybak[isAtMarket]] ,color=[.8, .8, .8])
pa5, = s2.plot(xbak[isAtMarket], ybak[isAtMarket] ,'ok')

nvulnerable = []
nsick       = []
nimmune     = []
tt          = []

pnv, = s1.plot(tt,nvulnerable,'-',lineWidth=2,color=cvulnerable,label='Healthy')
pns, = s1.plot(tt,nsick,      '-',lineWidth=2,color=csick,label='Sick')
pni, = s1.plot(tt,nimmune,    '-',lineWidth=2,color=cimmune,label='Immune')
lg = s1.legend(loc='center left', bbox_to_anchor=(1, 0.5))

matplotlib.pyplot.show(block=False)
matplotlib.pyplot.pause(dtpause)

# Loop over all time steps
for it in range(nt):

    # Loop over all agents
    for ia in range(nagents):


        # Movement
        # ========
        # Check next action of agent

        tGoToMarket[ia] = tGoToMarket[ia]-1                               # Update time to market

        if isAtMarket[ia]:
            tAtMarket[ia] = tAtMarket[ia]+1                               # Update time at market
            stayAtMarket[ia] = tAtMarket[ia]<dtAtMarket
        else:
            xbak[ia] = x[ia]                                              # Backup position
            ybak[ia] = y[ia]

        nextMove = 'None'                                      # ACTIONs
        if tGoToMarket[ia] >0 and  not doesSD[ia] :
            nextMove = 'takeStep'                              # Keep walking
        elif tGoToMarket[ia] >0 and  doesSD[ia]:
            nextMove = 'stayPut'                               # Stay at home
        elif isAtMarket[ia]     and  tAtMarket[ia]<dtAtMarket:
            nextMove = 'stayPut'                               # Stay at market
        elif isAtMarket[ia]     and  tAtMarket[ia]>=dtAtMarket :
            nextMove = 'returnFromMarket'                      # Go back to where you were before shopping
        elif tGoToMarket[ia]<=0 :
            nextMove = 'goToMarket'                            # Go to market
        
        if nextMove =='None' :
            print('nextMove', 'tGoToMarket[ia]', 'doesSD[ia]', 'isAtMarket[ia]' , 'tAtMarket[ia]' ,'dtAtMarket' )
            print(nextMove, tGoToMarket[ia], doesSD[ia], isAtMarket[ia] , tAtMarket[ia] ,dtAtMarket )
        if verbose :
            print('Next action of agent %d at (%3.1f/%3.1f): %s'%(ia,x[ia],y[ia],nextMove))

        if nextMove == 'goToMarket':

            # Jump to market and stay for <ntGoShopping> time steps
            x[ia]           = xmarket+numpy.random.rand(1)*marketsize
            y[ia]           = ymarket+numpy.random.rand(1)*marketsize
            tGoToMarket[ia] = -1
            isAtMarket[ia]  = True

        elif nextMove == 'returnFromMarket':

            # Return to position from before market, and re-set shopping clocks
            x[ia]           = xbak[ia]
            y[ia]           = ybak[ia]
            tGoToMarket[ia] = dtGoToMarket
            tAtMarket[ia]   = 0
            isAtMarket[ia]  = False

        elif nextMove =='stayPut':

            # Do nothing
            numpy.pi-3.141592653589793 # This is inherited from Men-Aldrin Meier (I guess a swiss joke)

        elif nextMove == 'takeStep':

            # Try new position
            xnew = x[ia] + dx[ia]
            ynew = y[ia] + dy[ia]

            # If you hit a wall, try a random new direction, until you no
            # longer hit a wall
            hitWall = xnew>1 or xnew<0 or ynew>1 or ynew<0
            ntries  = 0
            stillTrying = True
            while hitWall and stillTrying:

                # Choose random new direction & update position
                alpha[ia] = 2*numpy.pi*numpy.random.rand(1,1)
                dx[ia]    = dr*numpy.sin(alpha[ia])
                dy[ia]    = dr*numpy.cos(alpha[ia])
                xnew      = x[ia] + dx[ia]
                ynew      = y[ia] + dy[ia]
                hitWall = (xnew>=1) or (xnew<=0) or (ynew>=1) or (ynew<=0)

                ntries = ntries+1;
                stillTrying = False if ntries>100 else True
            
            x[ia] = xnew
            y[ia] = ynew



        # Health status
        # =============
        # Check if agent heals and becomes immune
        if isSick[ia]:
            tSick[ia] = tSick[ia]+1
            if tSick[ia]>dtHeal:
                isSick[ia]   = False
                isImmune[ia] = True


        # Contagion
        if isSick[ia]:

            # Pass on disease to all within <rcont> that are not immune
            xdist      = x[ia] - x
            ydist      = y[ia] - y
            r          = numpy.sqrt(xdist**2+ydist**2)   # Distance to other agent
            meetAgents = r<=rcont
            isHome     = (x==xbak) * (y==ybak)           # People at home don't get infected
            isSick[meetAgents * (1-isImmune) *  (1-isHome)] = True
            #print(sum(meetAgents),'close enough')
            #print(sum(meetAgents * (1-isImmune)),'close enough & not immune')
            #print(sum(meetAgents * (1-isImmune) *  (1-isHome)),'close enough & not immune & not at home')
            #print(isSick[meetAgents * (1-isImmune) *  (1-isHome)])
            
    # Count cases
    isVulnerable = (1-isSick) * (1-isImmune)
    nvulnerable  += [sum(isVulnerable)]
    nsick        += [sum(isSick)]
    nimmune      += [sum(isImmune)]
    tt           += [it/tstepsperday]
    nall         = nvulnerable[-1] + nsick[-1] + nimmune[-1]
    
    if nall != nagents :
        print(nall, nvulnerable[-1] , nsick[-1] , nimmune[-1])
        print('Counts dont add up.')
        
    # Update figure
    [o.remove() for o in pa4]
    pa4 = s2.plot([x[isAtMarket],xbak[isAtMarket]], [y[isAtMarket],ybak[isAtMarket]] ,color=[.8, .8, .8])
    pa5.set_data(xbak[isAtMarket], ybak[isAtMarket])
    
    #pa1.remove()
    #pa1, = s2.plot(x[isVulnerable],y[isVulnerable],'sk',markersize=mkSize,markerfacecolor=cvulnerable)
    pa1.set_data(x[isVulnerable],y[isVulnerable])
    pa2.set_data(x[isSick],y[isSick])
    pa3.set_data(x[isImmune],y[isImmune])

    
    s2.set_title('t = %3.1f days'%(it/tstepsperday))

    pnv.set_data(tt,nvulnerable)
    pns.set_data(tt,nsick)
    pni.set_data(tt,nimmune)
    
    matplotlib.pyplot.draw()
    matplotlib.pyplot.pause(dtpause)

    if writeGif:
        pass
        # Capture the plot as an image & write to gif
        #drawnow
        #frame      = getframe(hf);
        #im         = frame2im(frame);
        #[imind,cm] = rgb2ind(im,256);
        #if it==1; imwrite(imind,cm,gifName,'gif','DelayTime',dtgif, 'Loopcount',inf);
        #else      imwrite(imind,cm,gifName,'gif','DelayTime',dtgif,'WriteMode','append');
matplotlib.pyplot.show()
