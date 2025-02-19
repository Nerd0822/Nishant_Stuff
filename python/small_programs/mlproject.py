import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


arr=np.random.randint(10000,size=9999)

print(arr)

plt.hist(arr)
plt.show()