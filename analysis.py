import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import plotly.figure_factory as ff
import plotly.graph_objects as go
import seaborn as sns
from scipy.stats import linregress
import plotly.express as px

# List of things that YOLO can detect:
# YOLO_id = {
#     0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane', 5: 'bus', 6: 'train', 7: 'truck', 8: 'boat',
#     9: 'traffic light', 10: 'fire hydrant', 11: 'stop sign', 12: 'parking meter', 13: 'bench', 14: 'bird', 15: 'cat',
#     16: 'dog', 17: 'horse', 18: 'sheep', 19: 'cow', 20: 'elephant', 21: 'bear', 22: 'zebra', 23: 'giraffe', 24: 'backpack',
#     25: 'umbrella', 26: 'handbag', 27: 'tie', 28: 'suitcase', 29: 'frisbee', 30: 'skis', 31: 'snowboard', 32: 'sports ball',
#     33: 'kite', 34: 'baseball bat', 35: 'baseball glove', 36: 'skateboard', 37: 'surfboard', 38: 'tennis racket', 39: 'bottle',
#     40: 'wine glass', 41: 'cup', 42: 'fork', 43: 'knife', 44: 'spoon', 45: 'bowl', 46: 'banana', 47: 'apple', 48: 'sandwich',
#     49: 'orange', 50: 'broccoli', 51: 'carrot', 52: 'hot dog',53: 'pizza', 54: 'donut', 55: 'cake', 56: 'chair',57: 'couch',
#     58: 'potted plant', 59: 'bed',60: 'dining table', 61: 'toilet', 62: 'tv', 63: 'laptop', 64: 'mouse', 65: 'remote',
#     66: 'keyboard',67: 'cell phone', 68: 'microwave', 69: 'oven', 70: 'toaster', 71: 'sink', 72: 'refrigerator', 73: 'book',
#     74: 'clock',75: 'vase', 76: 'scissors', 77: 'teddy bear', 78: 'hair drier', 79: 'toothbrush'
# }


def read_csv_files(folder_path):
    dfs = {}
    for file in os.listdir(folder_path):
        if file.endswith(".csv"):
            # Read the CSV file into a DataFrame
            file_path = os.path.join(folder_path, file)
            df = pd.read_csv(file_path)
            # Store the DataFrame in the dictionary with the filename as the key
            filename = os.path.splitext(file)[0]  # Get the filename without extension
            dfs[filename] = df
    return dfs

def pedestrian_crossing(dataframe, min_x, max_x, person_id):

    crossed_ids = dataframe[(dataframe["YOLO_id"] == person_id)]
    crossed_ids_grouped = crossed_ids.groupby("Unique Id")
    filtered_crossed_ids = crossed_ids_grouped.filter(
        lambda x: (x["X-center"] <= min_x).any() and (x["X-center"] >= max_x).any()
    )
    crossed_ids = filtered_crossed_ids["Unique Id"].unique()
    return len(crossed_ids), crossed_ids

def time_to_cross(dataframe, ids):
    var = {}
    for id in ids:
        x_min = dataframe[dataframe["Unique Id"] == id]["X-center"].min()
        x_max = dataframe[dataframe["Unique Id"] == id]["X-center"].max()

        sorted_grp = dataframe[dataframe["Unique Id"] == id]

        x_min_index = sorted_grp[sorted_grp['X-center'] == x_min].index[0]
        x_max_index = sorted_grp[sorted_grp['X-center'] == x_max].index[0]

        count, flag = 0, 0
        if x_min_index < x_max_index:
            for value in sorted_grp['X-center']:
                if value == x_min:
                    flag = 1
                if flag == 1:
                    count += 1
                    if value == x_max:
                        var[id] = count/30
                        break
        
        else:
            for value in sorted_grp['X-center']:
                if value == x_max:
                    flag = 1
                if flag == 1:
                    count += 1
                    if value == x_min:
                        var[id] = count/30
                        break

    return var

def plot_displot(data):
    final_data = []

    for key, sub_dict in data.items():
        values = list(sub_dict.values())  # Simplified way to get values
        final_data.extend(values)  # Extend instead of append to avoid nested lists

    # Create a DataFrame with a column for the data and a column for the corresponding key
    df = pd.DataFrame({'Data': final_data, 'Key': [k for k in data for _ in range(len(data[k]))]})
    
    plt.figure(figsize=(10, 6))
    with sns.plotting_context(rc={"legend.fontsize": 10}):  # Adjust legend font size
        sns.displot(data=df, x='Data', hue='Key', kind='kde', multiple='stack', legend=True)
    
    plt.xlabel('Data')
    plt.ylabel('Density')
    plt.title('Distribution Plot of Final Data')
    plt.legend(title='Key')  # Provide a title for the legend
    plt.show()

def plot_histogram(data):
    values = []
    keys = []
    for key, sub_dict in data.items():
        for val in sub_dict.values():
            values.append(val)
            keys.append(key)

    # Create histogram figure
    fig = go.Figure()

    # Add histogram traces for each key
    for key in set(keys):
        key_values = [val for val, k in zip(values, keys) if k == key]
        fig.add_trace(go.Histogram(x=key_values, name=key))

    # Update layout
    fig.update_layout(
        title="Histogram of Values from DICT",
        xaxis_title="Values",
        yaxis_title="Frequency",
        bargap=0.2,  # Gap between bars
        barmode='overlay'  # Overlay histograms
    )
    fig.show()
    
def adjust_annotation_positions(annotations):
    adjusted_annotations = []
    for i, ann in enumerate(annotations):
        adjusted_ann = ann.copy()
        # Adjust x and y coordinates to avoid overlap
        for other_ann in adjusted_annotations:
            if (abs(ann['x'] - other_ann['x']) < 2) and (abs(ann['y'] - other_ann['y']) < 1):
                adjusted_ann['y'] += 0.2
        adjusted_annotations.append(adjusted_ann)
    return adjusted_annotations

def plot_cell_phone_vs_death(df_mapping, data):
    info, death, continents, gdp = {}, [], [], []
    for key, value in data.items():
        dataframe = value
        mobile_ids = dataframe[dataframe["YOLO_id"] == 67]
        mobile_ids = mobile_ids["Unique Id"].unique()
        info[key] = len(mobile_ids)

        df = df_mapping[df_mapping['Location'] == key]
        death_value = df['death(per_100k)'].values
        death.append(death_value[0])
        continents.append(df['Continent'].values[0])
        gdp.append(df['GDP_per_capita'].values[0])

    # Filter out values where info[key] == 0
    filtered_info = {k: v for k, v in info.items() if v != 0}
    filtered_death = [d for i, d in enumerate(death) if info[list(info.keys())[i]] != 0]
    filtered_continents = [c for i, c in enumerate(continents) if info[list(info.keys())[i]] != 0]
    filtered_gdp = [c for i, c in enumerate(gdp) if info[list(info.keys())[i]] != 0] 

    fig = px.scatter(x=filtered_death, y=list(filtered_info.values()), size=filtered_gdp, color=filtered_continents)

    # Adding labels and title
    fig.update_layout(
        xaxis_title="Death per 100k",
        yaxis_title="Number of Mobile",
        title="Cell Phone Usage vs Death Rate",
        showlegend=True  # Show legend for continent colors
    )

    # Adding annotations for keys
    annotations = []
    for i, key in enumerate(filtered_info.keys()):
        annotations.append(
            dict(
                x=filtered_death[i],
                y=list(filtered_info.values())[i],
                text=key,
                showarrow=False
            )
        )

    # Adjust annotation positions to avoid overlap
    adjusted_annotations = adjust_annotation_positions(annotations)

    fig.update_layout(annotations=adjusted_annotations)

    fig.show()

def plot_hesitation():
    pass

def plot_GDP_vs_time_to_cross(mapping, data):
    gdp, mean_time = [], []
    for key, value in data.items():
        df = mapping[mapping['Location'] == key]
        gdp.append(df['GDP_per_capita'].iloc[0])
        dummy = []
        for val in value.values():
            dummy.append(val)
        mean_time.append(np.mean(dummy))

    plt.scatter(mean_time, gdp, label='Data')

    # Add annotations (keys)
    for i, txt in enumerate(data.keys()):
        plt.annotate(txt, (mean_time[i], gdp[i]), xytext=(5, 5), textcoords='offset points')

    # Fit a line using L1 (Least Absolute Deviations) regression
    # slope, intercept, _, _, _ = linregress(mean_time, gdp)
    # plt.plot(mean_time, slope * np.array(mean_time) + intercept, color='green',  label='L1 Regression')

    # Fit a line using least squares regression
    # m, b = np.polyfit(mean_time, gdp, 1)
    # plt.plot(mean_time, m * np.array(mean_time) + b, color='red',linestyle=':', label='Least Squares Regression')

    plt.xlabel('Mean Time to Cross')
    plt.ylabel('GDP per Capita')
    plt.title('GDP per Capita vs. Mean Time to Cross')
    plt.legend()
    plt.show()

def plot_vehicles_vs_GDP(df_mapping, data, car_flag=0, motorcycle_flag=0, pedestrian_flag=0, bicycle_flag=0, bus_flag=0, truck_flag=0):
    if car_flag:
        info, gdp = {}, []
        for key, value in data.items():
            dataframe = value
            vehicle_ids = dataframe[dataframe["YOLO_id"] == 2]
            vehicle_ids = vehicle_ids["Unique Id"].unique()
            info[key] = len(vehicle_ids)

            df = df_mapping[df_mapping['Location'] == key]
            gdp.append(df['GDP_per_capita'].iloc[0])

        print("Car information : ", info)
        plt.scatter(gdp, list(info.values()))

        # Add annotations (keys)
        for i, (key, _) in enumerate(info.items()):
            plt.annotate(key, (gdp[i], list(info.values())[i]), xytext=(5, 5), textcoords='offset points')

        plt.xlabel('GDP per capita')
        plt.ylabel('Cars detected')
        plt.title('GDP per Capita vs. Cars detected')
        plt.legend()
        plt.show()




    
    if motorcycle_flag:
        info, gdp = {}, []
        for key, value in data.items():
            dataframe = value
            vehicle_ids = dataframe[(dataframe["YOLO_id"] == 3)]
            vehicle_ids = vehicle_ids["Unique Id"].unique()
            info[key] = len(vehicle_ids)
        
            df = df_mapping[df_mapping['Location'] == key]
            gdp.append(df['GDP_per_capita'].iloc[0])

        print("Motorcycle information : ", info)
        plt.scatter(gdp, list(info.values()))

        # Add annotations (keys)
        for i, (key, _) in enumerate(info.items()):
            plt.annotate(key, (gdp[i], list(info.values())[i]), xytext=(5, 5), textcoords='offset points')

        plt.xlabel('GDP per capita')
        plt.ylabel('Motorcycle detected')
        plt.title('GDP per Capita vs. Motorcycle detected')
        plt.legend()
        plt.show()



    if pedestrian_flag:
        info, gdp = {}, []
        for key, value in data.items():
            dataframe = value
            vehicle_ids = dataframe[(dataframe["YOLO_id"] == 0)]
            vehicle_ids = vehicle_ids["Unique Id"].unique()
            info[key] = len(vehicle_ids)
        
            df = df_mapping[df_mapping['Location'] == key]
            gdp.append(df['GDP_per_capita'].iloc[0])

        print("Car information : ", info)
        plt.scatter(gdp, list(info.values()))

        # Add annotations (keys)
        for i, (key, _) in enumerate(info.items()):
            plt.annotate(key, (gdp[i], list(info.values())[i]), xytext=(5, 5), textcoords='offset points')

        plt.xlabel('GDP per capita')
        plt.ylabel('Pedestrian detected')
        plt.title('GDP per Capita vs. Pedestrian detected')
        plt.legend()
        plt.show()



    if bicycle_flag:
        info, gdp = {}, []
        for key, value in data.items():
            dataframe = value
            vehicle_ids = dataframe[(dataframe["YOLO_id"] == 1)]
            vehicle_ids = vehicle_ids["Unique Id"].unique()
            info[key] = len(vehicle_ids)
        
            df = df_mapping[df_mapping['Location'] == key]
            gdp.append(df['GDP_per_capita'].iloc[0])

        print("Car information : ", info)
        plt.scatter(gdp, list(info.values()))

        # Add annotations (keys)
        for i, (key, _) in enumerate(info.items()):
            plt.annotate(key, (gdp[i], list(info.values())[i]), xytext=(5, 5), textcoords='offset points')

        plt.xlabel('GDP per capita')
        plt.ylabel('Bicycle detected')
        plt.title('GDP per Capita vs. Bicycle detected')
        plt.legend()
        plt.show()
    



    if bus_flag:
        info, gdp = {}, []
        for key, value in data.items():
            dataframe = value
            vehicle_ids = dataframe[(dataframe["YOLO_id"] == 5)]
            vehicle_ids = vehicle_ids["Unique Id"].unique()
            info[key] = len(vehicle_ids)
        
            df = df_mapping[df_mapping['Location'] == key]
            gdp.append(df['GDP_per_capita'].iloc[0])

        print("Car information : ", info)
        plt.scatter(gdp, list(info.values()))

        # Add annotations (keys)
        for i, (key, _) in enumerate(info.items()):
            plt.annotate(key, (gdp[i], list(info.values())[i]), xytext=(5, 5), textcoords='offset points')

        plt.xlabel('GDP per capita')
        plt.ylabel('Bus detected')
        plt.title('GDP per Capita vs. Bus detected')
        plt.legend()
        plt.show()



    if truck_flag:
        info, gdp = {}, []
        for key, value in data.items():
            dataframe = value
            vehicle_ids = dataframe[(dataframe["YOLO_id"] == 7)]
            vehicle_ids = vehicle_ids["Unique Id"].unique()
            info[key] = len(vehicle_ids)
        
            df = df_mapping[df_mapping['Location'] == key]
            gdp.append(df['GDP_per_capita'].iloc[0])

        print("Car information : ", info)
        plt.scatter(gdp, list(info.values()))

        # Add annotations (keys)
        for i, (key, _) in enumerate(info.items()):
            plt.annotate(key, (gdp[i], list(info.values())[i]), xytext=(5, 5), textcoords='offset points')

        plt.xlabel('GDP per capita')
        plt.ylabel('Truck detected')
        plt.title('GDP per Capita vs. Truck detected')
        plt.legend()
        plt.show()

def plot_vehicles_vs_death(df_mapping, data, car_flag=0, motorcycle_flag=0, pedestrian_flag=0, bicycle_flag=0, bus_flag=0, truck_flag=0):
    if car_flag:
        info, death = {}, []
        for key, value in data.items():
            dataframe = value
            vehicle_ids = dataframe[dataframe["YOLO_id"] == 2]
            vehicle_ids = vehicle_ids["Unique Id"].unique()
            info[key] = len(vehicle_ids)

            df = df_mapping[df_mapping['Location'] == key]
            death.append(df['death(per_100k)'].iloc[0])

        print("Car information : ", info)
        plt.scatter(death, list(info.values()))

        # Add annotations (keys)
        for i, (key, _) in enumerate(info.items()):
            plt.annotate(key, (death[i], list(info.values())[i]), xytext=(5, 5), textcoords='offset points')

        plt.xlabel('death(per_100k) ')
        plt.ylabel('Cars detected')
        plt.title('death(per_100k) vs. Cars detected')
        plt.legend()
        plt.show()




    
    if motorcycle_flag:
        info, death = {}, []
        for key, value in data.items():
            dataframe = value
            vehicle_ids = dataframe[(dataframe["YOLO_id"] == 3)]
            vehicle_ids = vehicle_ids["Unique Id"].unique()
            info[key] = len(vehicle_ids)
        
            df = df_mapping[df_mapping['Location'] == key]
            death.append(df['death(per_100k)'].iloc[0])

        print("Motorcycle information : ", info)
        plt.scatter(death, list(info.values()))

        # Add annotations (keys)
        for i, (key, _) in enumerate(info.items()):
            plt.annotate(key, (death[i], list(info.values())[i]), xytext=(5, 5), textcoords='offset points')

        plt.xlabel('death(per_100k)')
        plt.ylabel('Motorcycle detected')
        plt.title('death(per_100k) vs. Motorcycle detected')
        plt.legend()
        plt.show()



    if pedestrian_flag:
        info, death = {}, []
        for key, value in data.items():
            dataframe = value
            vehicle_ids = dataframe[(dataframe["YOLO_id"] == 0)]
            vehicle_ids = vehicle_ids["Unique Id"].unique()
            info[key] = len(vehicle_ids)
        
            df = df_mapping[df_mapping['Location'] == key]
            death.append(df['death(per_100k)'].iloc[0])

        print("Car information : ", info)
        plt.scatter(death, list(info.values()))

        # Add annotations (keys)
        for i, (key, _) in enumerate(info.items()):
            plt.annotate(key, (death[i], list(info.values())[i]), xytext=(5, 5), textcoords='offset points')

        plt.xlabel('death(per_100k)')
        plt.ylabel('Pedestrian detected')
        plt.title('death(per_100k) vs. Pedestrian detected')
        plt.legend()
        plt.show()



    if bicycle_flag:
        info, death = {}, []
        for key, value in data.items():
            dataframe = value
            vehicle_ids = dataframe[(dataframe["YOLO_id"] == 1)]
            vehicle_ids = vehicle_ids["Unique Id"].unique()
            info[key] = len(vehicle_ids)
        
            df = df_mapping[df_mapping['Location'] == key]
            death.append(df['death(per_100k)'].iloc[0])

        print("Car information : ", info)
        plt.scatter(death, list(info.values()))

        # Add annotations (keys)
        for i, (key, _) in enumerate(info.items()):
            plt.annotate(key, (death[i], list(info.values())[i]), xytext=(5, 5), textcoords='offset points')

        plt.xlabel('death(per_100k)')
        plt.ylabel('Bicycle detected')
        plt.title('death(per_100k) vs. Bicycle detected')
        plt.legend()
        plt.show()
    



    if bus_flag:
        info, death = {}, []
        for key, value in data.items():
            dataframe = value
            vehicle_ids = dataframe[(dataframe["YOLO_id"] == 5)]
            vehicle_ids = vehicle_ids["Unique Id"].unique()
            info[key] = len(vehicle_ids)
        
            df = df_mapping[df_mapping['Location'] == key]
            death.append(df['death(per_100k)'].iloc[0])

        print("Car information : ", info)
        plt.scatter(death, list(info.values()))

        # Add annotations (keys)
        for i, (key, _) in enumerate(info.items()):
            plt.annotate(key, (death[i], list(info.values())[i]), xytext=(5, 5), textcoords='offset points')

        plt.xlabel('death(per_100k)')
        plt.ylabel('Bus detected')
        plt.title('death(per_100k) vs. Bus detected')
        plt.legend()
        plt.show()



    if truck_flag:
        info, death = {}, []
        for key, value in data.items():
            dataframe = value
            vehicle_ids = dataframe[(dataframe["YOLO_id"] == 7)]
            vehicle_ids = vehicle_ids["Unique Id"].unique()
            info[key] = len(vehicle_ids)
        
            df = df_mapping[df_mapping['Location'] == key]
            death.append(df['death(per_100k)'].iloc[0])

        print("Car information : ", info)
        plt.scatter(death, list(info.values()))

        # Add annotations (keys)
        for i, (key, _) in enumerate(info.items()):
            plt.annotate(key, (death[i], list(info.values())[i]), xytext=(5, 5), textcoords='offset points')

        plt.xlabel('death(per_100k)')
        plt.ylabel('Truck detected')
        plt.title('death(per_100k) vs. Truck detected')
        plt.legend()
        plt.show()

def plot_population_vs_traffic(df_mapping, data, car_flag=0, motorcycle_flag=0, pedestrian_flag=0, bicycle_flag=0, bus_flag=0, truck_flag=0):
    if car_flag:
        info, population = {}, []
        for key, value in data.items():
            dataframe = value
            vehicle_ids = dataframe[dataframe["YOLO_id"] == 2]
            vehicle_ids = vehicle_ids["Unique Id"].unique()
            info[key] = len(vehicle_ids)

            df = df_mapping[df_mapping['Location'] == key]
            population.append(df['Population_city'].iloc[0])

        print("Car information : ", info)
        plt.scatter(population, list(info.values()))

        # Add annotations (keys)
        for i, (key, _) in enumerate(info.items()):
            plt.annotate(key, (population[i], list(info.values())[i]), xytext=(5, 5), textcoords='offset points')

        plt.xlabel('Population')
        plt.ylabel('Cars detected')
        plt.title('Population vs. Cars detected')
        plt.legend()
        plt.show()




    
    if motorcycle_flag:
        info, population = {}, []
        for key, value in data.items():
            dataframe = value
            vehicle_ids = dataframe[(dataframe["YOLO_id"] == 3)]
            vehicle_ids = vehicle_ids["Unique Id"].unique()
            info[key] = len(vehicle_ids)
        
            df = df_mapping[df_mapping['Location'] == key]
            population.append(df['Population_city'].iloc[0])

        print("Motorcycle information : ", info)
        plt.scatter(population, list(info.values()))

        # Add annotations (keys)
        for i, (key, _) in enumerate(info.items()):
            plt.annotate(key, (population[i], list(info.values())[i]), xytext=(5, 5), textcoords='offset points')

        plt.xlabel('Population')
        plt.ylabel('Motorcycle detected')
        plt.title('Population vs. Motorcycle detected')
        plt.legend()
        plt.show()



    if pedestrian_flag:
        info, population = {}, []
        for key, value in data.items():
            dataframe = value
            vehicle_ids = dataframe[(dataframe["YOLO_id"] == 0)]
            vehicle_ids = vehicle_ids["Unique Id"].unique()
            info[key] = len(vehicle_ids)
        
            df = df_mapping[df_mapping['Location'] == key]
            population.append(df['Population_city'].iloc[0])

        print("Car information : ", info)
        plt.scatter(population, list(info.values()))

        # Add annotations (keys)
        for i, (key, _) in enumerate(info.items()):
            plt.annotate(key, (population[i], list(info.values())[i]), xytext=(5, 5), textcoords='offset points')

        plt.xlabel('Population')
        plt.ylabel('Pedestrian detected')
        plt.title('Population vs. Pedestrian detected')
        plt.legend()
        plt.show()



    if bicycle_flag:
        info, population = {}, []
        for key, value in data.items():
            dataframe = value
            vehicle_ids = dataframe[(dataframe["YOLO_id"] == 1)]
            vehicle_ids = vehicle_ids["Unique Id"].unique()
            info[key] = len(vehicle_ids)
        
            df = df_mapping[df_mapping['Location'] == key]
            population.append(df['Population_city'].iloc[0])

        print("Car information : ", info)
        plt.scatter(population, list(info.values()))

        # Add annotations (keys)
        for i, (key, _) in enumerate(info.items()):
            plt.annotate(key, (population[i], list(info.values())[i]), xytext=(5, 5), textcoords='offset points')

        plt.xlabel('Population')
        plt.ylabel('Bicycle detected')
        plt.title('Population vs. Bicycle detected')
        plt.legend()
        plt.show()
    



    if bus_flag:
        info, population = {}, []
        for key, value in data.items():
            dataframe = value
            vehicle_ids = dataframe[(dataframe["YOLO_id"] == 5)]
            vehicle_ids = vehicle_ids["Unique Id"].unique()
            info[key] = len(vehicle_ids)
        
            df = df_mapping[df_mapping['Location'] == key]
            population.append(df['Population_city'].iloc[0])

        print("Car information : ", info)
        plt.scatter(population, list(info.values()))

        # Add annotations (keys)
        for i, (key, _) in enumerate(info.items()):
            plt.annotate(key, (population[i], list(info.values())[i]), xytext=(5, 5), textcoords='offset points')

        plt.xlabel('Population')
        plt.ylabel('Bus detected')
        plt.title('Population vs. Bus detected')
        plt.legend()
        plt.show()



    if truck_flag:
        info, population = {}, []
        for key, value in data.items():
            dataframe = value
            vehicle_ids = dataframe[(dataframe["YOLO_id"] == 7)]
            vehicle_ids = vehicle_ids["Unique Id"].unique()
            info[key] = len(vehicle_ids)
        
            df = df_mapping[df_mapping['Location'] == key]
            population.append(df['Population_city'].iloc[0])

        print("Car information : ", info)
        plt.scatter(population, list(info.values()))

        # Add annotations (keys)
        for i, (key, _) in enumerate(info.items()):
            plt.annotate(key, (population[i], list(info.values())[i]), xytext=(5, 5), textcoords='offset points')

        plt.xlabel('Population')
        plt.ylabel('Truck detected')
        plt.title('Population vs. Truck detected')
        plt.legend()
        plt.show()


data_folder = "data"
dfs = read_csv_files(data_folder)
# print(len(dfs))
pedestrian_crossing_count, data = {}, {}

for key, value in dfs.items():
    count, ids = pedestrian_crossing(dfs[key], 0.45, 0.55, 0)
    pedestrian_crossing_count[key] = {"count": count, "ids": ids}
    data[key] = time_to_cross(dfs[key], pedestrian_crossing_count[key]["ids"])

# plot_displot(data)
# plot_histogram(data)

df_mapping = pd.read_csv("mapping.csv")
plot_GDP_vs_time_to_cross(df_mapping,data)

# plot_vehicles_vs_GDP(df_mapping, dfs, car_flag = 1, motorcycle_flag = 1, pedestrian_flag = 1, bicycle_flag = 1, bus_flag = 1, truck_flag= 1)
# plot_vehicles_vs_death(df_mapping, dfs, car_flag=1, motorcycle_flag = 1, pedestrian_flag = 1, bicycle_flag = 1, bus_flag = 1, truck_flag = 1)
# plot_population_vs_traffic(df_mapping, dfs, car_flag=1, motorcycle_flag = 1, pedestrian_flag = 1, bicycle_flag = 1, bus_flag = 1, truck_flag = 1)
# plot_cell_phone_vs_GDP(df_mapping, dfs)

plot_cell_phone_vs_death(df_mapping, dfs)