#!/usr/bin/env python

import re

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


class Occupancy(object):
    """Class definition to generate occupancy histogram files"""

    def __init__(self, site_indices_file_path, occupancy_file_path,
                 dst_path, color_list, shell_wise, site_wise):
        # Load occupancy parameters
        self.color_list = color_list
        self.num_colors = len(self.color_list)
        self.dst_path = dst_path
        self.site_indices_file_path = site_indices_file_path
        self.occupancy_file_path = occupancy_file_path
        self.shell_indices_dict = {}
        with self.site_indices_file_path.open('r') as site_indices_file:
            for line in site_indices_file:
                split_elements = re.split(',|\n', line)
                shell_index = int(split_elements[3])
                site_index = int(split_elements[0])
                if shell_index in self.shell_indices_dict:
                    self.shell_indices_dict[shell_index].append(site_index)
                else:
                    self.shell_indices_dict[shell_index] = [site_index]
                
        self.num_shells = len(self.shell_indices_dict) - 1
        self.probe_indices = []
        self.site_population_list = []
        for shell_index in range(self.num_shells+1):
            if shell_index == self.num_shells + 1:
                self.probe_indices.append(sorted(
                    [item
                     for sublist in self.shell_indices_dict[self.num_shells+1:]
                     for item in sublist]))
            else:
                self.probe_indices.append(sorted(
                    [item for item in self.shell_indices_dict[shell_index]]))
            self.site_population_list.append(
                                    [0] * len(self.probe_indices[shell_index]))

        with self.occupancy_file_path.open('r') as occupancy_file:
            for line in occupancy_file:
                site_index = int(line.split('\n')[0])
                for shell_index in range(self.num_shells+1):
                    if site_index in self.probe_indices[shell_index]:
                        list_index = self.probe_indices[shell_index].index(site_index)
                        self.site_population_list[shell_index][list_index] += 1
                        break
        if shell_wise:
            self.generate_shell_wise_occupancy()
        if site_wise:
            self.generate_site_wise_occpancy()

    def generate_site_wise_occpancy(self):
        plt.switch_backend('Agg')
        fig = plt.figure()
        plt.title('Site-wise occupancy')
        plt.axis('off')
        num_sub_plots = self.num_shells + 1
        num_cols = 2
        num_rows = num_sub_plots // num_cols + num_sub_plots % num_cols
        num_data = 0
        gs = gridspec.GridSpec(num_rows, num_cols, hspace=0.4)
        for shell_index in range(num_sub_plots):
            row_index = shell_index // num_cols
            col_index = shell_index % num_cols
            if shell_index == num_sub_plots - 1 and num_sub_plots % num_cols:
                ax = plt.subplot(gs[row_index, :])
            else:
                ax = plt.subplot(gs[row_index, col_index])
            length = len(self.probe_indices[shell_index])
            ax.bar(range(num_data, num_data+length),
                   self.site_population_list[shell_index],
                   color=self.color_list[shell_index % self.num_colors])
            ax.set_ylabel(f'{shell_index}')
            ax.set_xticks([])
            ax.set_yticks([])
            num_data += length
        figure_name = 'site-wise_occupancy.png'
        figure_path = self.dst_path / figure_name
        plt.savefig(str(figure_path))
        return None

    def generate_shell_wise_occupancy(self):
        plt.switch_backend('Agg')
        fig = plt.figure()
        plt.title('Shell-wise occupancy')
        ax = fig.add_subplot(111)
        for shell_index in range(self.num_shells+1):
            mean_value = int(np.mean(self.site_population_list[shell_index]))
            ax.bar(shell_index, mean_value,
                   color=self.color_list[shell_index % self.num_colors])
            ax.text(shell_index, 1.01 * mean_value, str(mean_value),
                    color='black', horizontalalignment='center')
        ax.set_xlabel('Shell Number')
        ax.set_ylabel('Average shell occupancy')
        xticks_list = [str(index) for index in range(self.num_shells+1)]
        plt.xticks(range(self.num_shells+1), xticks_list)
        figure_name = 'shell-wise_occupancy.png'
        figure_path = self.dst_path / figure_name
        plt.tight_layout()
        plt.savefig(str(figure_path))
        return None
