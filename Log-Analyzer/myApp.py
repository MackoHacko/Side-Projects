import yaml
import os
import requests
from flask import Flask, render_template, request, jsonify
from flask_wtf import FlaskForm
from wtforms import SelectField
from log_classes import reports_class, logs_class
from utils import convert_to_unix

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'


class Form(FlaskForm):
    with open(r'static/config.yaml') as file:
        sc = yaml.load(file, Loader=yaml.FullLoader)['sourceclasses']

    zone = SelectField('zone', choices=[(0, 'All'),
                                        (1000, 'MC'), (1001, 'Onyxia'), (1002, 'BWL'), (1003, 'ZG')])
    encounter = SelectField('encounter', choices=[("", 'Encounters + Trash')])

    log_type = SelectField('log_type', choices=[(
        'damage-done', 'Damage'), ('healing', 'Healing')])

    sourceclasses = SelectField('sourceclasses', choices=[
                                (v, k) for k, v in sc.items()])


@app.route("/", methods=['GET', 'POST'])
def analyzer():
    return render_template("analyzer.html", form=Form())


@app.route('/encounters/<zone>')
def encounters(zone):
    with open(r'static/config.yaml') as file:
        zones = yaml.load(file, Loader=yaml.FullLoader)['zones']
    encounters = zones[int(zone)]
    encounterArray = [{'id': encounter['id'], 'name': encounter['name']}
                      for encounter in encounters]
    return jsonify({'encounters': encounterArray})


@app.route("/about")
def about():
    return render_template("about.html")


@app.route('/reports', methods=['POST'])
def reports():

    reports = reports_class(request.form)
    if not reports.data_aquired:
        return render_template("error.html")
    if len(reports.reports) == 0:
        return render_template("empty.html")

    params = {'log_type': request.form['log_type'],
              'sourceclasses': request.form['sourceclasses'], 'zone': int(request.form['zone']), 'encounter': request.form['encounter']}
    return render_template("reports.html", reports=reports.reports, params=params)


@app.route("/result", methods=["POST"])
def result():

    logs = logs_class(request.form)
    logs.crunch_data()
    return render_template("result.html", graph=logs.graph, form=request.form)


if __name__ == "__main__":
    app.run(debug=True)
