import json
from collections import deque
import threading
import time
import paho.mqtt.client as mqtt
import dash
from dash import dcc, html
import plotly.graph_objs as go

# MQTT Configuration
broker = "broker.hivemq.com"
topic = "iot/fake/sensors"

# Data buffers
max_length = 50
temperatures = deque(maxlen=max_length)
humidities = deque(maxlen=max_length)
timestamps = deque(maxlen=max_length)

# MQTT callback
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print("Received:", payload)
        temperatures.append(payload["temperature"])
        humidities.append(payload["humidity"])
        timestamps.append(time.strftime("%H:%M:%S"))
        
    except Exception as e:
        print("Error:", e)

# Start MQTT in a thread
def start_mqtt():
    client = mqtt.Client(protocol=mqtt.MQTTv311)
    client.on_message = on_message
    client.connect(broker, 1883, 60)
    client.subscribe(topic)
    client.loop_forever()

mqtt_thread = threading.Thread(target=start_mqtt)
mqtt_thread.daemon = True
mqtt_thread.start()

# Dash App
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("ESP8266 Sensor Data (Live)"),
    dcc.Graph(id='live-temp-graph'),
    dcc.Graph(id='live-hum-graph'),
    dcc.Interval(id='interval-component', interval=2000, n_intervals=0)
])

@app.callback(
    dash.dependencies.Output('live-temp-graph', 'figure'),
    dash.dependencies.Input('interval-component', 'n_intervals')
)
def update_temp_graph(n):
    return {
        'data': [go.Scatter(x=list(timestamps), y=list(temperatures), mode='lines+markers', name='Temp (°C)')],
        'layout': go.Layout(title='Temperature over Time', xaxis=dict(title='Time'), yaxis=dict(title='°C'))
    }

@app.callback(
    dash.dependencies.Output('live-hum-graph', 'figure'),
    dash.dependencies.Input('interval-component', 'n_intervals')
)
def update_hum_graph(n):
    return {
        'data': [go.Scatter(x=list(timestamps), y=list(humidities), mode='lines+markers', name='Humidity (%)')],
        'layout': go.Layout(title='Humidity over Time', xaxis=dict(title='Time'), yaxis=dict(title='%'))
    }

if __name__ == '__main__':
    app.run(debug=True)
