#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from PyCT import constants


def traj_analysis(dst_path, disp_prec):
    intra_poly_dist_list = np.array([2.8541, 2.8600, 2.9958, 3.0473])

    position_array = (np.loadtxt(dst_path.joinpath('unwrappedTraj.dat'))
                      / constants.ANG2BOHR)
    num_positions = len(position_array)
    desired_indices = [0]
    for step_index in range(1, num_positions):
        if not np.array_equal(
                        np.round(position_array[step_index, :], disp_prec),
                        np.round(position_array[step_index-1, :], disp_prec)):
            desired_indices.append(step_index)
    newposition_array = np.copy(position_array[desired_indices])

    disp_vec_array = np.diff(newposition_array, axis=0)
    disp_array = np.linalg.norm(disp_vec_array, axis=1)
    # round displacements to given precision
    disp_array_prec = np.round(disp_array, disp_prec)

    num_steps = len(disp_array)
    num_rattles = 0
    rattle_dist_list = []
    rattle_event_list = []
    mobility_dist_list = []
    for step_index in range(num_steps):
        hop_dist = disp_array_prec[step_index]
        if hop_dist in intra_poly_dist_list:
            num_rattles += 1
            if num_rattles == 2:
                hop_dist_old = disp_array_prec[step_index - 1]
                rattle_dist_list.append(hop_dist_old)
                rattle_dist_list.append(hop_dist)
            elif num_rattles > 1:
                rattle_dist_list.append(hop_dist)
        else:
            if num_rattles == 1:
                mobility_dist_list.append(disp_array_prec[step_index - 1])
            elif num_rattles > 1:
                escape_dist = hop_dist
                rattle_event_list.append([num_rattles, escape_dist])
            mobility_dist_list.append(hop_dist)
            num_rattles = 0

    rattle_event_array = np.asarray(rattle_event_list)
    rattle_dist_array = np.asarray(rattle_dist_list)
    mobility_dist_array = np.asarray(mobility_dist_list)

    # report
    report_file_name = 'traj_analysis.log'
    num_kmc_steps = disp_array.shape[0]
    total_rattle_steps = int(np.sum(rattle_event_array[:, 0]))
    [uni_escape_dist, escape_counts] = np.unique(rattle_event_array[:, 1],
                                                 return_counts=True)
    escape_dist_list = list(uni_escape_dist)
    with open(report_file_name, 'w') as report_file:
        report_file.write(f'Total number of kmc steps in simulation: '
                          f'{num_kmc_steps}\n')
        report_file.write(f'Cumulative number of kmc steps in rattling: '
                          f'{total_rattle_steps}\n')
        report_file.write(
                        f'Average number of rattles per rattle event:'
                        f'{np.mean(rattle_event_array[:, 0]):{7}.{5}}\n')
        report_file.write(
                    f'List of escape distances: '
                    f'{", ".join(str(dist) for dist in escape_dist_list)}\n')

    # analysis on choice among available processes

    # collect to bins
    [unique_hop_dist, counts_hops] = np.unique(disp_array_prec,
                                               return_counts=True)
    plt.switch_backend('Agg')
    fig = plt.figure()
    ax = fig.add_subplot(111)
    proc_indices = np.arange(len(unique_hop_dist))
    xtick_items = ['%1.4f' % item for item in unique_hop_dist]
    plt.bar(proc_indices, counts_hops, align='center', alpha=0.5,
            edgecolor='black')
    plt.xticks(proc_indices, xtick_items, rotation='vertical')

    for i, v in enumerate(counts_hops):
        ax.text(i - 0.2, v + 100, str(v), color='green', rotation='vertical',
                fontweight='bold')
    add_rectangle = 1
    if add_rectangle:
        ax.add_patch(patches.Rectangle((13.5, -10), 4, 500, fill=False,
                                       color='red'))
    ax.set_xlabel('Hopping Distance')
    ax.set_ylabel('Counts')
    ax.set_title('Histogram of processes')
    filename = 'process_histogram'
    figure_name = filename + '.png'
    figure_path = dst_path / figure_name
    plt.tight_layout()
    plt.savefig(str(figure_path))

    # analysis on escape distances
    fig = plt.figure()
    ax = fig.add_subplot(111)
    escape_dist_indices = np.arange(len(uni_escape_dist))
    xtick_items = ['%1.4f' % item for item in uni_escape_dist]
    plt.bar(escape_dist_indices, escape_counts, align='center', alpha=0.5,
            edgecolor='black')
    plt.xticks(escape_dist_indices, xtick_items, rotation='vertical')

    for i, v in enumerate(escape_counts):
        ax.text(i - 0.2, v, str(v), color='green', rotation='vertical',
                fontweight='bold')
    add_rectangle = 1
    if add_rectangle:
        ax.add_patch(patches.Rectangle((9.5, -10), 3, 60, fill=False,
                                       color='red'))
    ax.set_xlabel('Escape Distance')
    ax.set_ylabel('Counts')
    ax.set_title('Histogram of Escape Distances')
    filename = 'escape_distance_histogram'
    figure_name = filename + '.png'
    figure_path = dst_path / figure_name
    plt.tight_layout()
    plt.savefig(str(figure_path))

    # analysis on hopping distance contributing to mobility
    [unique_mobil_hop_dist, counts_mobil_hops] = np.unique(mobility_dist_array,
                                                           return_counts=True)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    mobil_dist_indices = np.arange(len(unique_mobil_hop_dist))
    xtick_items = ['%1.4f' % item for item in unique_mobil_hop_dist]
    plt.bar(mobil_dist_indices, counts_mobil_hops, align='center', alpha=0.5,
            edgecolor='black')
    plt.xticks(mobil_dist_indices, xtick_items, rotation='vertical')

    for i, v in enumerate(counts_mobil_hops):
        ax.text(i - 0.2, v, str(v), color='green', rotation='vertical',
                fontweight='bold')
    add_rectangle = 1
    if add_rectangle:
        ax.add_patch(patches.Rectangle((12.5, -10), 4, 70, fill=False,
                                       color='red'))
    ax.set_xlabel('Hop Distance')
    ax.set_ylabel('Counts')
    ax.set_title('Histogram of Hop Distances contributing to mobility')
    filename = 'mobil_hop_distance_histogram'
    figure_name = filename + '.png'
    figure_path = dst_path / figure_name
    plt.tight_layout()
    plt.savefig(str(figure_path))

    # analysis on hopping distance contributing to rattling
    [unique_rattle_hop_dist, counts_rattle_hops] = np.unique(
                                        rattle_dist_array, return_counts=True)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    rattle_dist_indices = np.arange(len(unique_rattle_hop_dist))
    xtick_items = ['%1.4f' % item for item in unique_rattle_hop_dist]
    plt.bar(rattle_dist_indices, counts_rattle_hops, align='center', alpha=0.5,
            edgecolor='black')
    plt.xticks(rattle_dist_indices, xtick_items, rotation='vertical')

    for i, v in enumerate(counts_rattle_hops):
        ax.text(i - 0.2, v, str(v), color='green', rotation='vertical',
                fontweight='bold')
    ax.set_xlabel('Hop Distance')
    ax.set_ylabel('Counts')
    ax.set_title('Histogram of Hop Distances contributing to rattling')
    filename = 'rattle_hop_distance_histogram'
    figure_name = filename + '.png'
    figure_path = dst_path / figure_name
    plt.tight_layout()
    plt.savefig(str(figure_path))
    return None