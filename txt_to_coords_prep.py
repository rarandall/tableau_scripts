"""
Tableau Prep Python Script for converting shape file into coordinates dataframe

Example Input txt File:

<area shape="poly" alt="" coords="82,233, 103,220, 111,232, 89,245, 82,233" href="tenant_a">
<area shape="poly" alt="" coords="104,344, 104,317, 140,308, 145,325, 145,344, 104,344" href="tenant_b">


DataFrame Output:

   shape_id    x    y path_id    tenant
0         1   82  233       1  tenant_a
1         1  103  220       2  tenant_a
2         1  111  232       3  tenant_a
3         1   89  245       4  tenant_a
4         1   82  233       5  tenant_a
5         2  104  344       1  tenant_b
6         2  104  317       2  tenant_b
7         2  140  308       3  tenant_b
8         2  145  325       4  tenant_b
9         2  145  344       5  tenant_b
10        2  104  344       6  tenant_b

"""

import re
import pandas as pd

def convert(input):
    rows = input.iloc[:,0]
    shape_id = 0
    pattern = 'coords="([\d, ]+)" href'
    tenant_pattern = 'href="(.+)"'
    df = pd.DataFrame(columns =['shape_id', 'x', 'y', 'path_id', 'tenant'])
    for row in rows:
        coords = []
        shape_id += 1
        # extract coordinates from line
        coords = re.search(pattern, row)
        # convert coords to list
        coords = coords.group(1).split(", ")
        # make each coord pair a list
        coords_l = [x.split(",") for x in coords]
        # extract tenant
        tenant = re.search(tenant_pattern, row)
        # create a temp dataframe
        df_rows = pd.DataFrame({'shape_id':shape_id,
                                'x': [x[0] for x in coords_l],
                                'y': [x[1] for x in coords_l],
                                'path_id': range(1,len(coords_l)+1),
                                'tenant': tenant.group(1)})
        # append temp dataframe to result dataframe
        df = df.append(df_rows)
    df = df.reset_index(drop=True)
    return df

def get_output_schema():
    df_output = pd.DataFrame({'shape_id': prep_int(),
                                'x': prep_string(),
                                'y': prep_string(),
                                'path_id': prep_int(),
                                'tenant': prep_string()})
    return df_output

# df_test = pd.DataFrame({'F1':['<area shape="poly" alt="" coords="82,233, 103,220, 111,232, 89,245, 82,233" href="tenant_a">','<area shape="poly" alt="" coords="104,344, 104,317, 140,308, 145,325, 145,344, 104,344" href="tenant_b">']})
# print(convert(df_test))
