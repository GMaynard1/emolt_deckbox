#!/usr/bin/env python
# coding: utf-8

import numpy as np
import matplotlib.pyplot as plt
import time
import pandas as pd
from datetime import timedelta, datetime
import os
import sys
sys.path.insert(1,'/home/pi/Desktop/')
import setup_rtd


# from pandas.plotting import register_matplotlib_converters


class Plotting(object):
    def __init__(self, profile):
        self.df = profile
        self.path = '/'.join(setup_rtd.parameters['path'].split('/')[:3]) + '/'
        if len(self.df) > 0:
            if setup_rtd.parameters['tem_unit'] == 'Fahrenheit':
                self.df['TEMPERATURE'] = self.df['TEMPERATURE'] * 1.8 + 32
            if setup_rtd.parameters['depth_unit'] == 'Fathoms':
                self.df['PRESSURE'] = self.df['PRESSURE'] * 0.546807
            self.df['DATETIME'] += timedelta(hours=setup_rtd.parameters['local_time'])
            self.filename = self.df.iloc[-1]['DATETIME'].strftime('%y-%m-%d %H%M')
            try:
                self.plot_profile()
            except:
                pass
            try:
                self.plot_up_down()
            except:
                pass
            if setup_rtd.parameters['tem_unit'] == 'Fahrenheit':
                self.df['TEMPERATURE'] = (self.df['TEMPERATURE'] - 32) / 1.8
            if setup_rtd.parameters['depth_unit'] == 'Fathoms':
                self.df['PRESSURE'] = self.df['PRESSURE'] / 0.546807
            self.df['DATETIME'] -= timedelta(hours=setup_rtd.parameters['local_time'])
        # register_matplotlib_converters()

    def plot_profile(self):
        try:
            os.mkdir(self.path + 'Desktop/Profiles/' + self.filename)
        except:
            pass
        fig, ax_c = plt.subplots(figsize=(15, 9))

        lns1 = ax_c.plot(self.df['DATETIME'], self.df['PRESSURE'], '-', color='deepskyblue', label="pressure",
                         zorder=20,
                         linewidth=10)

        ax_c.set_ylabel(setup_rtd.parameters['depth_unit'], fontsize=20)
        ax_c.set_xlabel('Local time', fontsize=20)

        ax_c.set_xlim(min(self.df['DATETIME']) - timedelta(minutes=5),
                      max(self.df['DATETIME']) + timedelta(minutes=5))  # limit the plot to logged data
        ax_c.set_ylim(min(self.df['PRESSURE']) - 0.5, max(self.df['PRESSURE']) + 0.5)

        plt.tick_params(axis='both', labelsize=15)

        ax_f = ax_c.twinx()

        lns2 = ax_f.plot(self.df['DATETIME'], self.df['TEMPERATURE'], '--', color='r', label="temperature", zorder=10,
                         linewidth=10)

        ax_f.set_xlim(min(self.df['DATETIME']) - timedelta(minutes=5),
                      max(self.df['DATETIME']) + timedelta(minutes=5))  # limit the plot to logged data
        ax_f.set_ylim(min(self.df['TEMPERATURE']) - 0.5, max(self.df['TEMPERATURE']) + 0.5)

        ax_c.set_ylim(ax_c.get_ylim()[::-1])

        plt.title('{vessel} data'.format(vessel=setup_rtd.parameters['vessel_name']), fontsize=20)

        ax_f.set_ylabel(setup_rtd.parameters['tem_unit'], fontsize=20)

        fig.autofmt_xdate()

        lns = lns1 + lns2
        labs = [l.get_label() for l in lns]
        ax_c.legend(lns, labs, fontsize=15)

        plt.tick_params(axis='both', labelsize='large')

        plt.savefig(self.path + 'Desktop/Profiles/' + self.filename + '/' + self.filename + '_profile.png')

        plt.close()

    def plot_up_down(self):
        df_down = self.df[self.df['type'] == 2].reset_index(drop=True)
        df_up = self.df[self.df['type'] == 1][::-1].reset_index(drop=True)

        # plot discrepancy temperatures over time
        fig, ax = plt.subplots(figsize=(12, 12))

        mintem_row = df_down.loc[df_down['TEMPERATURE'].idxmin()]
        mintem = mintem_row['TEMPERATURE']
        dep_mintem = mintem_row['PRESSURE']

        # get the row of max value
        maxtem_row = df_down.loc[df_down['TEMPERATURE'].idxmax()]
        maxtem = maxtem_row['TEMPERATURE']
        dep_maxtem = maxtem_row['PRESSURE']

        plt.plot(df_down['TEMPERATURE'], df_down['PRESSURE'], 'green', label='down profile', alpha=0.5, linewidth=10,
                 zorder=1)

        tem = plt.scatter(self.df['TEMPERATURE'], self.df['PRESSURE'], c=self.df['TEMPERATURE'],
                          cmap='coolwarm', label='temperature', linewidth=5, zorder=3)

        # min_tem = plt.scatter(mintem, -dep_mintem, c='blue')
        plt.annotate(round(mintem, 1), (mintem, dep_mintem), fontsize=20, weight='bold')
        # max_tem = plt.scatter(maxtem, -dep_maxtem, c='green')
        plt.annotate(round(maxtem, 1), (maxtem, dep_maxtem), fontsize=20, weight='bold')

        mintem_row1 = df_up.loc[df_up['TEMPERATURE'].idxmin()]
        mintem1 = mintem_row1['TEMPERATURE']
        dep_mintem1 = mintem_row1['PRESSURE']

        # get the row of max value
        maxtem_row1 = df_up.loc[df_up['TEMPERATURE'].idxmax()]
        maxtem1 = maxtem_row1['TEMPERATURE']
        dep_maxtem1 = maxtem_row1['PRESSURE']

        plt.plot(df_up['TEMPERATURE'], df_up['PRESSURE'], 'purple', label='up profile', alpha=0.5, linewidth=10,
                 zorder=1)
        plt.annotate(round(mintem1, 1), (mintem1, dep_mintem1), fontsize=20, weight='bold')
        plt.annotate(round(maxtem1, 1), (maxtem1, dep_maxtem1), fontsize=20, weight='bold')

        ax.set_xlabel("Temperature ({tem_unit})".format(tem_unit=setup_rtd.parameters['tem_unit']), fontsize=20)
        ax.set_ylabel("Depth ({depth_unit})".format(depth_unit=setup_rtd.parameters['depth_unit']), fontsize=20)

        ax.set_ylim(ax.get_ylim()[::-1])

        plt.title("Profiles temperature vs pressure comparison on {date}".format(date=self.df['DATETIME'].iloc[-1]), fontsize=20)
        plt.legend(fontsize=15)

        cbar = plt.colorbar(tem, shrink=0.5, aspect=20)

        cbar.ax.tick_params(labelsize='large')

        plt.tick_params(axis='both', labelsize=15)

        plt.savefig(self.path + 'Desktop/Profiles/' + self.filename + '/' + self.filename + '_up_down.png')

        plt.close()



