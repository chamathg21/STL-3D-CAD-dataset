import numpy as np
import trimesh
import os
import csv
import argparse
import math

def is_inside(void_shell, outer_shell):
    """Function to determine if the void shell is inside the outer shell"""
    for vertex in void_shell.vertices:
        if not outer_shell.contains(np.array([vertex])):
            return False
    return True

def distance_to_nearest_wall(vertex, external_shell):
    min_distance = float("inf")
    for triangle in external_shell.triangles:
        for v in triangle:
            distance = np.linalg.norm(vertex - v)
            if distance < min_distance:
                min_distance = distance
    return min_distance

def process_directory(directory, output_csv):
    with open(output_csv, 'w', newline='') as csvfile:
        fieldnames = ['File Name', 'Void Name', 'Risk Factor']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.endswith('.stl'):
                    filepath = os.path.join(root, filename)
                    result = process_stl(filepath, filename, args)
                    if isinstance(result, dict):
                        for void_name, risk_factor in result.items():
                            writer.writerow({'File Name': filename, 'Void Name': void_name, 'Risk Factor': risk_factor})

def distance_to_nearest_wall(vertex, external_shell):
    min_distance = float("inf")
    for triangle in external_shell.triangles:
        for v in triangle:
            distance = np.linalg.norm(vertex - v)
            if distance < min_distance:
                min_distance = distance
    return min_distance

def sigmoid(x, scale=1):
    """Sigmoid function to map values to a range of 0 to 10."""
    return 10 / (1 + math.exp(-x*scale))

def calculate_void_risk(void_shell, external_shells, proximity_scale=10):
    # Identify which outer shell the void is inside
    for outer_shell in external_shells:
        if is_inside(void_shell, outer_shell):
            containing_shell = outer_shell
            break
    else:
        return 0
    
    void_volume = void_shell.volume
    outer_volume = containing_shell.volume
    
    volume_risk = sigmoid(void_volume / outer_volume * 10)
    
    min_distance_to_wall = min(distance_to_nearest_wall(vertex, external_shells[0]) for vertex in void_shell.vertices)
    proximity_risk = 10 / (1 + math.exp(-min_distance_to_wall*proximity_scale))
    
    def calculate_thickness_risk(vertex, external_shell):
        outer_distances = [np.linalg.norm(vertex - v) for v in external_shell.vertices]
        min_outer_distance = min(outer_distances)
        
        inner_distances = [np.linalg.norm(vertex - v) for v in void_shell.vertices]
        min_inner_distance = min(inner_distances)
        
        avg_thickness = (min_outer_distance + min_inner_distance) / 2
        thickness_risk = 1 / avg_thickness
        
        return thickness_risk
    
    thickness_risks = [calculate_thickness_risk(v, containing_shell) for v in void_shell.vertices]
    avg_thickness_risk = sum(thickness_risks) / len(thickness_risks)
    
    combined_risk = (volume_risk + proximity_risk + avg_thickness_risk) / 3
    combined_risk = min(max(combined_risk, 0), 10)  # Ensure it stays within 0-10
    
    return combined_risk

def process_stl(filepath, filename, args):
    mesh = trimesh.load_mesh(filepath)
    r = mesh.split()
    num_shells = len(r)

    if num_shells == 0:
        msg = "Error: 0 shells in design. Please check or repair STL file."
        return msg

    external_shells = []
    void_shells = []

    for s in range(num_shells):
        if not r[s].is_watertight:
            msg = "Error: Shell is not watertight. Please check or repair STL file."
            return msg

        if args.directory:
            file = f'{filepath}/{filename}'
        if args.file:
            file = filename

        try:
            i_tri, i_ray, _ = r[s].ray.intersects_id(
                ray_origins=r[s].triangles_center,
                ray_directions=r[s].face_normals,
                multiple_hits=True,
                return_locations=True,
            )

            i_dict = dict()
            for i in range(len(i_ray)):
                if i_ray[i] not in i_dict:
                    i_dict[i_ray[i].item()] = []
                if i_ray[i] == i_tri[i]:
                    continue  # don't add it; self-intersection
                i_dict[i_ray[i]].append(i_tri[i].item())

            s_hidden_void = [False] * len(i_dict)
            for i in range(len(i_dict)):
                if i_dict[i]:
                    s_hidden_void[i] = True

            if all(s_hidden_void):
                # All rays have a non-self intersection, it's a void shell
                void_shells.append(r[s])
            else:
                # Some rays have a non-self intersection, it's an external shell
                external_shells.append(r[s])

        except Exception as e:
            msg = f"Error: {str(e)}"
            return msg

    if not external_shells:
        return "Error: No external shells found. Cannot calculate risk factors."

    risk_factors = {}
    void_number = 1  # Assign a unique identifier for each void shell
    for void_shell in void_shells:
        risk_factor = calculate_void_risk(void_shell, external_shells)
        risk_factors[f"Void {void_number}"] = risk_factor
        void_number += 1

    return risk_factors

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", action="store_true")
    parser.add_argument("--file", action="store_true")

    args = parser.parse_args()

    input_directory = input("Enter path to directory: ")
    output_csv = input("Enter output CSV file name: ") + ".csv"

    process_directory(input_directory, output_csv)