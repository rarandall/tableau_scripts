"""
Tableau Prep Python Script for converting shape file into coordinates dataframe
Then, using the coordinates dataframe, compute the centroid of each shape
and append to bottom of coordinate dataframe

Example Input txt File:

<area shape="poly" alt="" coords="301,279, 301,264, 284,264, 284,237, 301,236, 299,219, 324,215, 327,233, 327,279, 301,279" href="tenant_a">
<area shape="poly" alt="" coords="145,819, 145,805, 118,805, 118,805, 104,805, 104,847, 145,838, 145,819, 145,819" href="tenant_b">
<area shape="poly" alt="" coords="345,619, 338,619, 338,611, 345,611, 345,619" href="tenant_c">

DataFrame Output:

   path_id  path_id_offset shape_id    tenant           x           y
0        1             2.0        1  tenant_a  301.000000  279.000000
1        2             3.0        1  tenant_a  301.000000  264.000000
2        3             4.0        1  tenant_a  284.000000  264.000000
3        4             5.0        1  tenant_a  284.000000  237.000000
4        5             6.0        1  tenant_a  301.000000  236.000000
5        6             7.0        1  tenant_a  299.000000  219.000000
6        7             8.0        1  tenant_a  324.000000  215.000000
7        8             9.0        1  tenant_a  327.000000  233.000000
8        9            10.0        1  tenant_a  327.000000  279.000000
9       10             1.0        1  tenant_a  301.000000  279.000000
10       1             2.0        2  tenant_b  145.000000  819.000000
11       2             3.0        2  tenant_b  145.000000  805.000000
12       3             4.0        2  tenant_b  118.000000  805.000000
13       4             5.0        2  tenant_b  118.000000  805.000000
14       5             6.0        2  tenant_b  104.000000  805.000000
15       6             7.0        2  tenant_b  104.000000  847.000000
16       7             8.0        2  tenant_b  145.000000  838.000000
17       8             9.0        2  tenant_b  145.000000  819.000000
18       9             1.0        2  tenant_b  145.000000  819.000000
19       1             2.0        3  tenant_c  345.000000  619.000000
20       2             3.0        3  tenant_c  338.000000  619.000000
21       3             4.0        3  tenant_c  338.000000  611.000000
22       4             5.0        3  tenant_c  345.000000  611.000000
23       5             1.0        3  tenant_c  345.000000  619.000000
24       0             NaN        1       NaN  309.016248  248.506656
25       0             NaN        2       NaN  123.680402  823.842679
26       0             NaN        3       NaN  341.469512  614.945094

"""

import re
import pandas as pd
from collections import defaultdict
pd.set_option("display.max_columns", 10)

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
                                'x': [float(x[0]) for x in coords_l],
                                'y': [float(x[1]) for x in coords_l],
                                'path_id': range(1,len(coords_l)+1),
                                'path_id_offset': [i if i <= len(coords_l) else 1 for i in range(2,len(coords_l)+2)],
                                'tenant': tenant.group(1)})
        # append temp dataframe to result dataframe
        df = df.append(df_rows)
    df = df.reset_index(drop=True)
    return df

## create a new dataframe, one row for each shape_id containing a point in the center of shape_id
def findCenter(df):
    # create offset column
    df['path_id_offset'] = df['path_id_offset'].astype(int)
    # keep only shape, coord, path
    cols = ['shape_id', 'x', 'y', 'path_id', 'path_id_offset']
    df = df.filter(cols)
    df_b = df
    df_merge = df.merge(df_b, how='left', left_on=['shape_id','path_id_offset'], right_on=['shape_id','path_id'])
    merge_cols = ['shape_id', 'x_x', 'y_x', 'x_y', 'y_y']
    df_merge = df_merge.filter(merge_cols)
    # rename
    df_exp = df_merge
    df_exp['x'] = [float(x) for x in df_exp['x_x']]
    df_exp['y'] = [float(x) for x in df_exp['y_x']]
    df_exp['x1'] = [float(x) for x in df_exp['x_y']]
    df_exp['y1'] = [float(x) for x in df_exp['y_y']]
    drop_cols = ['x_x', 'y_x', 'x_y', 'y_y']
    df_exp = df_exp.drop(drop_cols, axis=1)
    # loop through each shape_id, compute
    # Area of polygon : (x * y1 - x1 * y) sum for all rows / 2
    area_l = []
    for i, g in df_exp.groupby('shape_id'):
        area = 0.01
        for index, row in g.iterrows():
            xi = (row['x'] * row['y1'] - row['x1'] * row['y'])
            area += xi
        area = area / 2
        area_l.append(area)
    # X of Center: (x + x1) * (x * y1 - x1 * y) sum for all rows / (6 * Area)
    x_l = []
    for i, g in df_exp.groupby('shape_id'):
        x_sum = 0
        for index, row in g.iterrows():
            xi = (row['x'] + row['x1']) * (row['x'] * row['y1'] - row['x1'] * row['y'])
            x_sum += xi
        x_l.append(x_sum)
    # Y of Center: (y + y1) * (x * y1 - x1 * y)  sum for all rows / (6 * Area)
    y_l = []
    for i, g in df_exp.groupby('shape_id'):
        y_sum = 0
        for index, row in g.iterrows():
            yi = (row['y'] + row['y1']) * (row['x'] * row['y1'] - row['x1'] * row['y'])
            y_sum += yi
        y_l.append(y_sum)
    # apply full algorithm
    x_center = 0
    x_center_l = []
    y_center = 0
    y_center_l = []
    shape_id = 0
    shape_l = []
    for i in range(1,len(x_l)+1):
        shape_id = i
        x_center = x_l[i-1] / (6 * area_l[i-1])
        y_center = y_l[i-1] / (6 * area_l[i-1])
        x_center_l.append(float(x_center))
        y_center_l.append(float(y_center))
        shape_l.append(shape_id)
    centroid_df = pd.DataFrame()
    centroid_df['shape_id'] = shape_l
    centroid_df['x'] = x_center_l
    centroid_df['y'] = y_center_l
    centroid_df['path_id'] = 0
    return centroid_df
    #print(centroid_df)
    #print('shape: ', shape_l,'\nx_sum: ', x_l, '\ny_sum: ', y_l, '\narea: ', area_l, '\nx: ', x_center_l, '\ny: ', y_center_l)

def convert_and_centroid(input):
    shape_df = convert(input)
    shape_w_centroid = findCenter(shape_df)
    union = pd.concat([shape_df, shape_w_centroid], ignore_index=True)
    return union

def get_output_schema():
    df_output = pd.DataFrame({'shape_id': prep_int(),
                                'x': prep_decimal(),
                                'y': prep_decimal(),
                                'path_id': prep_int(),
                                'path_id_offset': prep_int(),
                                'tenant': prep_string()})
    return df_output

df_test = pd.DataFrame({'F1':['<area shape="poly" alt="" coords="301,279, 301,264, 284,264, 284,237, 301,236, 299,219, 324,215, 327,233, 327,279, 301,279" href="tenant_a">','<area shape="poly" alt="" coords="145,819, 145,805, 118,805, 118,805, 104,805, 104,847, 145,838, 145,819, 145,819" href="tenant_b">',
'<area shape="poly" alt="" coords="345,619, 338,619, 338,611, 345,611, 345,619" href="tenant_c">']})
# # # df_result = convert(df_test)
# # # print(df_result)
print(convert_and_centroid(df_test))
