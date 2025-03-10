from flask import Flask, request, jsonify, render_template, request, abort
from werkzeug.wrappers import response
from SimConnect import *
from SimConnect.simconnect_mobiflight import SimConnectMobiFlight
from SimConnect.mobiflight_variable_requests import MobiFlightVariableRequests
from time import sleep, localtime
import random
import logging
import math
import socket
import asyncio
from threading import Thread
import datetime
import os

print(socket.gethostbyname(socket.gethostname()))

ui_friendly_dictionary = {}
event_name = None
value_to_use = None
sm = None
ae = None
selected_plane = ""

#KML Files
kml_list = []

cwd = os.path.realpath(os.path.join(
    os.getcwd(), os.path.dirname(__file__)))
files = os.listdir(cwd)
for file in files:
	if file.endswith(".kml"):
		kml_list.append(file)

# Flask WebApp
def flask_thread_func(threadname):

	global ui_friendly_dictionary
	global event_name
	global value_to_use
	global sm
	global ae

	# Define Supported Aircraft
	planes_list = [
		"Default",
		"Robin DR400-160B w/ Tablet"
	]
	planes_dict = {
		"Default": [
			["NAV", "nav"],
			["COM", "com"],
			["AP", "ap"],
			["Panel", "panel"],
			["Other", "other"]
		],
		
		"Robin DR400-160B w/ Tablet": [
			["NAV", "dr40-160b-nav"],
			["COM", "dr40-160b-com"],
			["AP", "dr40-160b-ap"],
			["Lights", "dr40-160b-lights"],
			["Electrical", "dr40-160b-electrical"],
			["Fuel", "dr40-160b-fuel"],
			["Other", "dr40-160b-other"]
		]
	}

	global selected_plane
	selected_plane = planes_list[0]
	ui_friendly_dictionary["selected_plane"] = selected_plane

	app = Flask(__name__)
	log = logging.getLogger('werkzeug')
	log.disabled = True

	@app.route('/ui')
	def output_ui_variables():
		# Intialize Dictionary
		ui_friendly_dictionary["STATUS"] = "succes"
		return jsonify(ui_friendly_dictionary)

	@app.route('/', methods=['GET', 'POST'])
	def index():
		global selected_plane
		cur_plane_select = request.form.get("plane_selected")
		if cur_plane_select != None:
			selected_plane = cur_plane_select
			ui_friendly_dictionary["selected_plane"] = selected_plane
		return render_template('glass.html', planes_list=planes_list, selected_plane=selected_plane, curr_plane=planes_dict[selected_plane])

	@app.route('/landscape', methods=['GET', 'POST'])
	def index_landscape():
		global selected_plane
		cur_plane_select = request.form.get('selected_plane')
		if cur_plane_select != None:
			selected_plane = cur_plane_select
			ui_friendly_dictionary["selected_plane"] = selected_plane
		return render_template('glass_landscape.html', planes_list=planes_list, selected_plane=selected_plane, curr_plane=planes_dict[selected_plane])

	# Returns the list of available KML files
	@app.route('/kml', methods=['GET'])
	def get_list_of_kmls():
		return jsonify(kml_list)

	# Returns the requested KML file or 404
	@app.route('/kml/<file>', methods=['GET'])
	def get_kml_file_content(file):
		try:
			return read_file(file)
		except:
			return abort(404)

	def trigger_event(event_name, value_to_use = None):
		# This function actually does the work of triggering the event

		EVENT_TO_TRIGGER = ae.find(event_name)
		if EVENT_TO_TRIGGER is not None:
			status = "success"
		else:
			status = "Error: %s is not an Event" & (event_name)

	@app.route('/event/<event_name>/trigger', methods=['POST'])
	def trigger_event_endpoint(event_name):
		# This is the http endpoint wrapper for triggering an event

		ds = request.get_json() if request.is_json else request.form
		value_to_use = ds.get('value_to_use')

		status = trigger_event(event_name, value_to_use)

		return jsonify(status)

	app.run(host='0.0.0.0', port=4000, debug=False)

# SimConnect App
def simconnect_thread_func(threadname):

	global ui_friendly_dictionary
	global event_name
	global value_to_use
	global sm
	global ae

	while True:
		try:
			sm = SimConnect()
			print("\n********** MSFS 2020 Mobile Companion 2.0 **********\n")
			print(f"Local web server initialized")
			print(
				f"Launch {socket.gethostbyname(socket.gethostname())}:4000 in your browser to access the UI\n")
			print(
				f"Make sure your mobile device is connected to the same local network as this PC.\n")
			print(
				f"Notice: If your computer has multiple network interfaces, the IP address may be different than the one shown above\n")
			print("**************************************************\n")
			break
		except:
			print("Could not find MSFS running. Please launch MSFS first and then restart the app.")
			sleep(5)

	ae = AircraftEvents(sm)
	aq = AircraftRequests(sm)

	# Initialize previous altitude for code stability
	previous_alt = -400

	async def ui_dictionnary(ui_friendly_dictionary, previous_alt):
		# SIM DATA
		ui_friendly_dictionary["SIMULATION_RATE"] = round(aq.get("SIMULATION_RATE"))

		# POSITION DATA
		ui_friendly_dictionary["LATITUDE"] = round(aq.get("PLANE_LATITUDE"), 6)
		ui_friendly_dictionary["LONGITUDE"] = round(aq.get("PLANE_LONGITUDE"), 6)

	while True:
		asyncio.run(ui_dictionnary(ui_friendly_dictionary, previous_alt))
		sleep(0.3)

# SimConnect LVAR Reading
def simconnect_thread_func2(threadname):

	global ui_friendly_dictionary
	global selected_plane

	sm = SimConnectMobiFlight()
	vr = MobiFlightVariableRequests(sm)
	vr.clear_sim_variables()

	while True:
		#Redundant code, might use it later
		ui_friendly_dictionary["LIGHT_LANDING"] = vr.get(
			"(A:LIGHT LANDING, bool)")
		ui_friendly_dictionary["LIGHT_TAXI"] = vr.get(
			"(A:LIGHT TAXI, bool)")
		ui_friendly_dictionary["LIGHT_STROBE"] = vr.get(
			"(A:LIGHT STROBE, bool)")
		ui_friendly_dictionary["LIGHT_NAV"] = vr.get(
			"(A:LIGHT NAV, bool)")
		ui_friendly_dictionary["LIGHT_BEACON"] = vr.get(
			"(A:LIGHT BEACON, bool)")
		ui_friendly_dictionary["LIGHT_CABIN"] = vr.get(
			"(A:LIGHT CABIN, bool)")
		ui_friendly_dictionary["LIGHT_LOGO"] = vr.get(
			"(A:LIGHT LOGO, bool)")
		ui_friendly_dictionary["LIGHT_PANEL"] = vr.get(	
			"(A:LIGHT PANEL, bool)")
		ui_friendly_dictionary["LIGHT_WING"] = vr.get(
			"(A:LIGHT WING, bool)")
		ui_friendly_dictionary["LIGHT_RECOGNITION"] = vr.get(
			"(A:LIGHT RECOGNITION, bool)")
		ui_friendly_dictionary["PITOT_HEAT"] = vr.get(
			"(A:PITOT HEAT, bool)")
		ui_friendly_dictionary["ENG_ANTI_ICE"] = vr.get(
			"(A:ENG ANTI ICE, bool)")
		ui_friendly_dictionary["STRUCTURAL_DEICE_SWITCH"] = vr.get(
			"(A:STRUCTURAL DEICE SWITCH, bool)")
		
		sleep (0.15)

def read_file(filename, directory=cwd):
	path = os.path.join(directory, filename)
	contents = None
	with open(path, 'rb') as file:
		contents = file.read()
		file.close()
	
	return contents

if __name__ == "__main__":
	thread1 = Thread(target=flask_thread_func, args=('Thread-1', ))
	thread2 = Thread(target=simconnect_thread_func, args=('Thread-2', ))
	thread3 = Thread(target=simconnect_thread_func2, args=('Thread-3', ))
	thread1.start()
	thread2.start()
	thread3.start()

	sleep(0.5)