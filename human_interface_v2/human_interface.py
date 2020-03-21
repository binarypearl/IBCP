import subprocess
import time
import flask
import sys

from jinja2 import Environment
from jinja2.loaders import FileSystemLoader

try:
    from flask import Flask, render_template
except ImportError:
    sys.exit("Cannot import from flask: Do `pip3 install --user flask` to install")

app = flask.Flask(__name__)

#process = subprocess.Popen(shlex.split("/mnt/backups/anki/IBCP/applications/number_guesser/number_guesser.py -c /mnt/backups/anki/IBCP/ibcp.cfg --p1 0060100c"), stdout=subprocess.PIPE)
#stdout = process.communicate()[0]

@app.route('/')
def index():
    return render_template(
            'human_interface.html',
            header_window='/header_window.html',
            input_window='/input_window.html',
            viewer_window='/viewer_window.html'
            )

@app.route('/header_window.html')
def header_window():
    return render_template(
            'header_window.html'
            )

@app.route('/input_window.html')
def input_window():
    return render_template(
            'input_window.html'
            )

@app.route('/viewer_window.html')
def viewer_window():
    def inner():
        proc = subprocess.Popen(
            ['/usr/bin/iostat', '1', '100'],
            shell=True,
            universal_newlines=True,
            stdout=subprocess.PIPE
        )

        #sys.stdout.flush()

        for line in iter(proc.stdout.readline, ''):
            #time.sleep(1)
            yield line.rstrip() + '<br/>\n'

    env = Environment(loader=FileSystemLoader('templates'))
    tmpl = env.get_template('viewer_window.html')

    return flask.Response(tmpl.generate(result=inner()))

    #return flask.Response(inner(), mimetype='text/html')

if __name__ == "__main__":
    app.run(debug=True, port=5000, host='0.0.0.0')
