import yaml
import io
import requests
import base64
from urllib.parse import urlencode
from datetime import datetime
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import plotly.graph_objects as go
from utils import build_url, convert_to_unix


class reports_class:

    def __init__(self, form):
        self.form = form
        self.config = {}
        self.data_aquired = False
        with open("static/config.yaml", 'r') as stream:
            try:
                self.config = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
        self.make_api_request()

    def make_api_request(self):
        base_url = self.config['reports']['base_url']
        paths = [self.form[k] for k in self.config['reports']['paths']]
        params = {k: self.form[k] for k in self.config['reports']['params']
                  if k in self.form and self.form[k] and self.form[k]}
        if 'start' in params:
            params['start'] = convert_to_unix(params['start'])
        if 'end' in params:
            params['end'] = convert_to_unix(params['end'])
        params['api_key'] = self.config['credentials']['api_key']
        api_request = build_url(base_url, paths, params)
        self.reports = requests.get(url=api_request, verify=True).json()
        self.check_request()

        if self.data_aquired:
            zone = int(self.form['zone'])
            self.reports = [
                report for report in self.reports if report['zone'] == zone or zone == 0]
            for report in self.reports:
                report['start'] = datetime.utcfromtimestamp(
                    report['start']/1000).strftime('%Y-%m-%d')

    def check_request(self):
        if "error" not in self.reports:
            self.data_aquired = True


class logs_class(reports_class):

    def make_api_request(self):

        base_url = self.config['logs']['base_url']
        params = {k: self.form[k] for k in self.config['logs']['params']
                  if k in self.form and self.form[k]}
        params['api_key'] = self.config['credentials']['api_key']
        params['end'] = '20000000'
        paths = [self.form[k]
                 for k in self.config['logs']['paths'] if k != 'code' and k in self.form]
        codes = self.form.getlist('code')

        api_requests = [build_url(base_url, paths + [code], params)
                        for code in codes]
        print(api_requests)

        self.logs = [requests.get(url=request, verify=True).json()
                     for request in api_requests]

    def crunch_data(self):

        data_dict = {}
        colors = []
        for log in self.logs:
            total = sum(item['total'] for item in log['entries'])
            for entry in log['entries']:
                if entry['type'] not in self.form['sourceclasses']:
                    continue
                if entry['name'] not in data_dict:
                    data_dict[entry['name']] = [entry['total']/total * 100]
                    colors.append(
                        self.config['class_colors'][entry['type']]['color'])
                else:
                    data_dict[entry['name']].append(entry['total']/total * 100)

        for player in data_dict:
            data_dict[player] = [np.mean(data_dict[player]), np.std(
                data_dict[player]), len(data_dict[player])]

        colors = [x for _, x in sorted(
            zip([v[0] for v in data_dict.values()], colors))]

        data_dict = {k: v for k, v in sorted(
            data_dict.items(), key=lambda item: item[1])}

        self.graph = self.mage_graph(data_dict, colors)

    def mage_graph(self, data, colors):
        avgs = [v[0] for v in data.values()]
        names = ['[' + str(v[2]) + ']' + ' ' + k for k, v in data.items()]
        stds = [v[1] for v in data.values()]

        log_type = 'damage' if self.form['log_type'] == 'damage-done' else 'healing'

        fig = Figure(figsize=(16, 8))
        ax = fig.add_subplot(1, 1, 1)
        ax.bar(np.arange(len(names)), avgs, yerr=stds,
               align='center', alpha=0.5, ecolor='black', capsize=10, color=colors)
        ax.set_ylabel(log_type.capitalize() + r' $\%$', fontsize=20)
        ax.set_xticks(np.arange(len(names)))
        ax.tick_params(axis='both', which='major', labelsize=25)
        ax.set_xticklabels(names, rotation=60, fontsize=12, ha='right')
        ax.yaxis.grid(True)
        ax.set_facecolor('xkcd:gray')
        fig.tight_layout()

        pngImage = io.BytesIO()
        FigureCanvas(fig).print_png(pngImage)

        pngImageB64String = "data:image/png;base64,"
        pngImageB64String += base64.b64encode(
            pngImage.getvalue()).decode('utf8')

        return pngImageB64String
