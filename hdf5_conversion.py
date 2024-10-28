import pandas as pd
import re

# Create a new HDF5 file
hdf = pd.HDFStore('data.h5')

# read the csv file
csv = pd.read_csv('data.csv')

# group everything together and then add to the hdf5 file with a category/name folder structure
for name, group in csv.groupby('Name'):
    category = group['Category'].iloc[0]
    part = str(group['Part ID'].iloc[0])
    category = re.sub(r'[^a-zA-Z0-9_]', '_', category)
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    part = re.sub(r'[^a-zA-Z0-9_]', '_', part)
    group.rename(columns={'Full Price': 'Full_Price', 'Discounted Price': 'Discounted_Price', 'Saved Price': 'Saved_Price'}, inplace=True)
    group['Full_Price'] = group['Full_Price'].str.replace('$', '', regex=False).str.replace(',', '', regex=False).astype('float16')
    group['Discounted_Price'] = group['Discounted_Price'].str.replace('$', '', regex=False).str.replace(',', '', regex=False).astype('float16')
    group['Saved_Price'] = group['Saved_Price'].str.replace('$', '', regex=False).str.replace(',', '', regex=False).astype('float16')
    group['Time'] = group['Time'].astype('S36')
    subgroup = group[['Time', 'Full_Price', 'Discounted_Price', 'Saved_Price']]

    subgroup.attrs.update({'category': category, 'name': name, 'part_id': part})
    
    hdf.put(f"{category}/{name}", subgroup, format='table', data_columns=True, index=False, complevel=9, complib='zlib')
    hdf.get_storer(f"{category}/{name}").attrs.part_id = part

hdf.close()

