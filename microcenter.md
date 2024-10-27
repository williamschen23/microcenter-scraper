This is a little guide of how to view the hdf5 file for microcenter. Since there is only one file, you would open up the view on it
```python
import pandas as pd
hdf = pd.HDFStore('microcenter_data.h5')
```

To view an item, select the category and then item name like so:

```python
data = hdf['Graphics_Cards/AMD_Radeon_RX_7600_Dual_Fan_8GB_GDDR6_PCIe_4_0_Graphics_Card']
```
Perform whatever operation that you would want to do on this data frame.