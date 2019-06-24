import json
from random import randint
import os
os.environ["CUDA_VISIBLE_DEVICES"]="-1"
import flask
import numpy as np
import plotly
import plotly.graph_objs as go
import tensorflow as tf
from flask import Flask, render_template, request
from plot import plot_single_prediction


app = Flask(__name__)

def load_model():
    global model  # bc YOLO
    model_dir = "saved_model/"
    model = tf.keras.experimental.load_from_saved_model(model_dir)


def make_prediction(cycle_data, response):
    cycles = { 'Qdlin': np.array(json.loads(cycle_data['Qdlin'])),
                'Tdlin': np.array(json.loads(cycle_data['Tdlin'])),
                'IR': np.array(json.loads(cycle_data['IR'])),
                'Discharge_time': np.array(json.loads(cycle_data['Discharge_time'])),
                'QD': np.array(json.loads(cycle_data['QD']))
            }

    predictions = model.predict(cycles)

    print("Returning predictions:")
    print(type(predictions))
    print(predictions)

    response['predictions'] = json.dumps(predictions.tolist())
    response['success'] = True
    
    return flask.jsonify(response)


def make_plot(predictions):
    predictions = np.array(predictions)
    first_pred = predictions[0]
    window_size = model.input_shape[0][1]
    scaling_factors_dict = {"Remaining_cycles": 2159.0}
    mean_cycle_life = 674
    figure = plot_single_prediction(first_pred,
                                  window_size,
                                  scaling_factors_dict,
                                  mean_cycle_life)
    gaphJSON = json.dumps(figure, cls=plotly.utils.PlotlyJSONEncoder)
    return gaphJSON


@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html", title="Home")


@app.route('/predict', methods=['POST'])
def predict():
    res = { 'success': False }

    if flask.request.method == 'POST':
        # read payload json
        if len(request.files) > 0:
            print("Upload via form")
            parsed_data = request.files["jsonInput"].read().decode('utf8')
            json_data = json.loads(parsed_data)
            predictions_response = make_prediction(json_data, res)
            predictions = json.loads(predictions_response.json["predictions"])
            plot = make_plot(predictions)
            return render_template("results.html", title="Results", plot=plot)
        else:
            print("Upload via curl")
            json_data = request.get_json()
            return make_prediction(json_data, res)


@app.route('/example')
def example():
    if request.args:
        rand = randint(1,5)
        filename = "sample_input_{}.json".format(rand)
        with open("static/samples/{}".format(filename), "r") as json_file:
            json_data = json.load(json_file)
    else:
        filename = ""
        json_data = None
    return render_template("example.html", title="Samples", filename=filename, data=json_data)

    
if __name__ == "__main__":
    print('--> Loading Keras Model and starting server')
    model = None
    load_model()        
    app.run(host="0.0.0.0")
