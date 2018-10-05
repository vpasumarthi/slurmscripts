#!/usr/bin/env python

import numpy as np


def read_occupancy(src_path, n_traj):
    """Reads the occupancy data from traj-level directories and return a 
       dictionary of trajectory-wise occupancy data, each as a numpy array
    :param src_path:
    :param n_traj:
    :return: occupancy_data:
    """
    occupancy_file_name = 'occupancy.npy'
    occupancy_data = {}
    for traj_index in range(n_traj):
        traj_dir_path = src_path / f'traj{traj_index+1}'
        occupancy_data[traj_index+1] = np.load(traj_dir_path / occupancy_file_name)
    return occupancy_data

def get_unit_cell_indices(system_size, total_elements_per_unit_cell, n_traj,
                          occupancy_data):
    """Returns the unit cell indices of the element
    :param system_size:
    :param total_elements_per_unit_cell:
    :param system_element_index:
    :return:
    """
    unit_cell_index_data = {}
    for traj_index in range(n_traj):
        num_states = len(occupancy_data[traj_index+1])
        traj_occupancy_data = occupancy_data[traj_index+1].reshape(num_states)
        traj_unit_cell_indices = np.zeros((num_states, 3), int)
        unit_cell_element_indices = traj_occupancy_data % total_elements_per_unit_cell
        total_filled_unit_cells = ((traj_occupancy_data - unit_cell_element_indices)
                                   / total_elements_per_unit_cell)
        for index in range(3):
            traj_unit_cell_indices[:, index] = total_filled_unit_cells / system_size[index+1:].prod()
            total_filled_unit_cells -= traj_unit_cell_indices[:, index] * system_size[index+1:].prod()
        unit_cell_index_data[traj_index+1] = traj_unit_cell_indices
    return unit_cell_index_data

def compute_layer_wise_residence(src_path, system_size, total_elements_per_unit_cell,
                                 n_traj, gradient_ld, partition_length_ratio):
    """Returns the layer wise residence of charge carriers
    :param src_path:
    :param system_size:
    :param n_traj:
    :param gradient_ld:
    :param layer_length_ratio:
    :return:
    """
    occupancy_data = read_occupancy(src_path, n_traj)
    unit_cell_index_data = get_unit_cell_indices(
            system_size, total_elements_per_unit_cell, n_traj, occupancy_data)
    num_elemental_partitions = np.sum(partition_length_ratio)
    num_partitions = len(partition_length_ratio)
    bin_edges = [0]
    for partition_index in range(num_partitions):
        bin_edges.append(bin_edges[-1] + system_size[gradient_ld] // num_elemental_partitions * partition_length_ratio[partition_index])
    return None
