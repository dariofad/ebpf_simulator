import matplotlib.pyplot as plt
import matplotlib.patches as patches
import csv

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
ZSET_KEY = 'simulation:0'

signals = {
    "TIME": 0,
    "PANGLE": 1,
    "AF": 2,
    "CMODE": 3,
}

plt.rcParams.update({'font.size': 16})

CASES = ["1.csv", "2.csv"]
TITLES = ["Normal execution", "Runtime enforcement"]
fig, axs = plt.subplots(1, 2, figsize=(20, 4))
handles, labels = [], []
times = []
pangle = []
af = []
cmode = []
for c, case in enumerate(CASES):
    times.append([])
    pangle.append([])
    af.append([])
    cmode.append([])    
    with open(case, mode='r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)
        for line in csv_reader:
            times[c].append(int(line[0]))
            pangle[c].append(float(line[1]))
            af[c].append(float(line[2]))
            cmode[c].append(float(line[3]))            

    axs[c].plot(times[c], pangle[c], label="Pedal angle", linestyle='--', linewidth=3, color='green')
    axs[c].set_ylim(0, 65)
    axs[c].set_ylabel("Angle [°]")
    # perturbation
    if c == 1:
        pert = [0.0 for _ in range(1001)]
        for j in range(450):
            pert[50+j] = float(j)/30
        axs[c].plot(times[c], pert, label="Pedal angle injection", linestyle=':', linewidth=3, color='red')            
    twin_g = axs[c].twinx()
    twin_g.plot(times[c], af[c], color='blue', linewidth=3, label="Air-to-fuel ratio")
    twin_g.set_ylim(10, 20)
    axs[c].autoscale(axis='x', tight=True)
    axs[c].set_title(TITLES[c])
    if c == 1:
         h, l = axs[1].get_legend_handles_labels()
         handles.extend(h)
         labels.extend(l)
         hh, ll = twin_g.get_legend_handles_labels()
         handles.extend(hh)
         labels.extend(ll)         
    if c == 0:
        axs[c].text(135, 55, 'response lag', ha='center', va='center', fontsize=16, color='black')                
        axs[0].annotate(text='', xy=(0, 50), xytext=(270,50),
                        arrowprops=dict(arrowstyle='<->', color='black'))
        axs[0].annotate(text='', xy=(265, 30), xytext=(265,50),
                        arrowprops=dict(arrowstyle='-', color='black', linestyle=':'))        
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, -0.17), ncol=3)
fig.savefig('af-exp-lag.png', bbox_inches='tight')
