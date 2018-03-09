import pyfoil2
from os import path

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

scraper = pyfoil2.foilscrape(path.dirname(path.realpath(__file__)))
'''e387 = pyfoil2.foilmath(scraper, 'ah79100b', 6.5, 1)


fig, ax = plt.subplots()

ax.plot([g[0] for g in e387.top], [g[1] for g in e387.top], 'r')
ax.plot([g[0] for g in e387.bottom], [g[1] for g in e387.bottom], 'g')
ax.set_title('enis')
ax.axis([0,1,-0.5,0.5])
plt.grid(True)
plt.axis('scaled')
#plt.gca().set_aspect('equal', adjustable='box')
plt.show()'''

def frange(start, stop, step):
    i = start
    while i < stop:
        yield i
        i += step

for x in frange(0, 90, 0.5):
    for f in scraper.good_foil_list:
        print(f)
        foil = pyfoil2.foilmath(scraper, f, x, 0)
        le = foil.calc_leading_edge()
        te = foil.calc_trailing_edge()
        #leg1, leg2 = foil.calc_le_gradient()
        #teg1, teg2 = foil.calc_te_gradient()
        thick = foil.calc_max_thickness()
        camber = foil.calc_max_camber()

        with open('allfoils.csv', 'a') as csv:
            csv.write(','.join(str([f, le, te, thick, camber, '\n'])))
