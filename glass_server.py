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
		"Default": [["NAV", "nav"], ["COM", "com"], ["AP", "ap"], ["Lights", "lights"], ["other", "other"]],
		"Robin DR400-160B w/ Tablet": [
			["NAV", "dr40-160b-nav"],
			["COM", "dr40-160b-com"],
			["AP", "dr40-160b-ap"],
			["lights", "dr40-160b-lights"],
			["Electrical", "dr40-160b-electrical"],
			["Fuel", "dr40-160b-fuel"],
			["other", "dr40-160b-other"]
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
			if value_to_use is None:
				EVENT_TO_TRIGGER()
			else:
				# Convert Hz BCD for NAV1_RADIO_SET, NAV2_RADIO_SET and AD_SET events
				if event_name == "NAV1_RADIO_SET" or event_name == "NAV2_RADIO_SET":
					freq_hz = float(value_to_use) * 100
					freq_hz = str(int(freq_hz))
					freq_hz_bcd = 0
					for figure, digit in enumerate(reversed(freq_hz)):
						freq_hz_bcd += int(digit) * (16 ** figure)
					EVENT_TO_TRIGGER(int(freq_hz_bcd))
				elif event_name == "ADF_COMPLETE_SET":
					freq_hz = int(value_to_use) * 10000
					freq_hz = str(int(freq_hz))
					freq_hz_bcd = 0
					for figure, digit in enumerate(reversed(freq_hz)):
						freq_hz_bcd += int(digit) * (16 ** figure)
					EVENT_TO_TRIGGER(int(freq_hz_bcd))
				elif event_name == "COM_RADIO_SET" or event_name == "COM2_RADIO_SET":
					freq_hz = float(value_to_use) * 100
					flag_3dec = int(freq_hz) != freq_hz
					freq_hz = str(int(freq_hz))
					freq_hz_bcd = 0
					for figure, digit in enumerate(reversed(freq_hz)):
						freq_hz_bcd += int(digit) * (16 ** figure)
					EVENT_TO_TRIGGER(int(freq_hz_bcd))
					# Workarouuund for 3rd decimal
					if flag_3dec is True and str(value_to_use)[-2] != "25" and str(value_to_use)[-2:] !="75":
						if event_name == "COM_RADIO_SET":
							trigger_event("COM_STBY_RADIO_SWAP")
							trigger_event("COM_RADIO_FRACT_INC")
							trigger_event("COM_STBY_RADIO_SWAP")
						else:
							trigger_event("COM2_STBY_RADIO_SWAP")
							trigger_event("COM2_RADIO_FRACT_INC")
							trigger_event("COM2_STBY_RADIO_SWAP")
				elif event_name == "XPNDR_SET":
					freq_hz = int(value_to_use) * 1
					freq_hz = str(int(freq_hz))
					fres_hz_bcd = 0
					for figure, digit in enumerate(reversed(freq_hz)):
						freq_hz_bcd += int(digit) * (16 ** figure)
					EVENT_TO_TRIGGER(int(freq_hz_bcd))
				else:
					EVENT_TO_TRIGGER(int(value_to_use))

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
		# Radios
		ui_friendly_dictionary["NAV1_STANDBY"] = round(aq.get("NAV_STANDBY_FREQUENCY:1"), 2)
		ui_friendly_dictionary["NAV1_ACTIVE"] = round(aq.get("NAV_ACTIVE_FREQUENCY:1"), 2)

		ui_friendly_dictionary["NAV2_STANDBY"] = round(aq.get("NAV_STANDBY_FREQUENCY:2"), 2)
		ui_friendly_dictionary["NAV2_ACTIVE"] = round(aq.get("NAV_ACTIVE_FREQUENCY:2"), 2)

		# ADF Active
		adf_use_bcd = int(aq.get("ADF_ACTIVE_FREQUENCY:1"))
		adf_use_digits = ""

		for i in reversed(range(4)):
			adf_use_digit = math.floor(adf_use_bcd / (65536 * (16 ** i)))
			adf_use_digits = adf_use_digits + str(adf_use_digit)
			adf_use_bcd = adf_use_bcd - (65536 * (16 ** i)) * adf_use_digit

		try:
			ui_friendly_dictionary["AFD_USE_1000"] = adf_use_digits[0]
			ui_friendly_dictionary["AFD_USE_100"] = adf_use_digits[1]
			ui_friendly_dictionary["AFD_USE_10"] = adf_use_digits[2]
			ui_friendly_dictionary["AFD_USE_1"] = adf_use_digits[3]
			ui_friendly_dictionary["ADF_USE"] = int(adf_use_digits)
		except:
			None

		# ADF Standby
		adf_stby = int(aq.get("ADF_STANDBY_FREQUENCY:1"))/1000
		try:
			if adf_stby >= 1000:
				ui_friendly_dictionary["ADF_STBY_1000"] = str(adf_stby)[0]
				ui_friendly_dictionary["ADF_STBY_100"] = str(adf_stby)[1]
				ui_friendly_dictionary["ADF_STBY_10"] = str(adf_stby)[2]
				ui_friendly_dictionary["ADF_STBY_1"] = str(adf_stby)[3]
			else:
				ui_friendly_dictionary["ADF_STBY_1000"] = 0
				ui_friendly_dictionary["ADF_STBY_100"] = str(adf_stby)[0]
				ui_friendly_dictionary["ADF_STBY_10"] = str(adf_stby)[1]
				ui_friendly_dictionary["ADF_STBY_1"] = str(adf_stby)[2]
		except:
			None

		# Comms
		ui_friendly_dictionary["COM1_STANDBY"] = round(aq.get("COM_STANDBY_FREQUENCY:1"), 3)
		ui_friendly_dictionary["COM1_ACTIVE"] = round(aq.get("COM_ACTIVE_FREQUENCY:1"), 3)
		ui_friendly_dictionary["COM1_TRANSMIT"] = aq.get("COM_TRANSMIT:1")
		ui_friendly_dictionary["COM2_STANDBY"] = round(aq.get("COM_STANDBY_FREQUENCY:2"), 3)
		ui_friendly_dictionary["COM2_ACTIVE"] = round(aq.get("COM_ACTIVE_FREQUENCY:2"), 3)
		ui_friendly_dictionary["COM2_TRANSMIT"] = aq.get("COM_TRANSMIT:2")

		# XPNDR
		xpndr_bcd = aq.get("TRANSPONDER_CODE:1")
		xpndr_digits = ""

		# XPNDR Conversion from BCD to Decimal
		try:
			for i in reversed(range(4)):
				xpndr_digit = math.floor(xpndr_bcd / (16 ** i))
				xpndr_digits = xpndr_digits + str(xpndr_digit)
				xpndr_bcd = xpndr_bcd - (16 ** i) * xpndr_digit
		except:
			None

		# Autopilot
		ui_friendly_dictionary["AUTOPILOT_MASTER"] = aq.get("AUTOPILOT_MASTER")
		ui_friendly_dictionary["AUTOPILOT_NAV1_LOCK"] = aq.get("AUTOPILOT_NAV1_LOCK")
		ui_friendly_dictionary["AUTOPILOT_HEADING_LOCK"] = aq.get("AUTOPILOT_HEADING_LOCK")
		ui_friendly_dictionary["AUTOPILOT_ALTITUDE_LOCK"] = aq.get("AUTOPILOT_ALTITUDE_LOCK")
		ui_friendly_dictionary["AUTOPILOT_GLIDESLOPE_HOLD"] = aq.get("AUTOPILOT_GLIDESLOPE_HOLD")
		ui_friendly_dictionary["AUTOPILOT_APPROACH_HOLD"] = aq.get("AUTOPILOT_APPROACH_HOLD")
		ui_friendly_dictionary["AUTOPILOT_BACKCOURSE_HOLD"] = aq.get("AUTOPILOT_BACKCOURSE_HOLD")
		ui_friendly_dictionary["AUTOPILOT_VERTICAL_HOLD"] = aq.get("AUTOPILOT_VERTICAL_HOLD")
		ui_friendly_dictionary["AUTOPILOT_FLIGHT_LEVEL_CHANGE"] = aq.get("AUTOPILOT_FLIGHT_LEVEL_CHANGE")
		ui_friendly_dictionary["AUTOPILOT_AUTOTHROTTLE"] = aq.get("AUTOPILOT_AUTOTHROTTLE")
		ui_friendly_dictionary["AUTOPILOT_YAW_DAMPER"] = aq.get("AUTOPILOT_YAW_DAMPER")
		ui_friendly_dictionary["AIRPSPEED_INDICATED"] = round(aq.get("AIRSPEED_INDICATED"))
		ui_friendly_dictionary["AUTOPILOT_AIRSPEED_HOLD"] = aq.get("AUTOPILOT_AIRSPEED_HOLD")
		ui_friendly_dictionary["AUTOPILOT_AIRSPEED_HOLD_VAR"] = aq.get("AUTOPILOT_AIRSPEED_HOLD_VAR")
		ui_friendly_dictionary["PLANE_HEADING_DEGREES"] = round(round(aq.get("PLANE_HEADING_DEGREES_MAGNETIC")) * 180/3.1416, 0)
		ui_friendly_dictionary["AUTOPILOT_FLIGHT_DIRECTOR_ACTIVE"] = aq.get("AUTOPILOT_FLIGHT_DIRECTOR_ACTIVE")
		ui_friendly_dictionary["SIMULATION_RATE"] = aq.get("SIMULATION_RATE")
		# GPS
		ui_friendly_dictionary["NEXT_WP_LAT"] = aq.get("GPS_WP_NEXT_LAT")
		ui_friendly_dictionary["NEXT_WP_LON"] = aq.get("GPS_WP_NEXT_LON")
		# Other
		ui_friendly_dictionary["GEAR_POSITION"] = aq.get("GEAR_POSITION:1")
		#ui_friendly_dictionary["FLAPS_HANDLE_PERCENT"] = round(aq.get("FLAPS_HANDLE_PERCENT") * 100)
		ui_friendly_dictionary["SPOILERS_ARMED"] = aq.get("SPOILERS_HANDLE_POSITION")

		# Current Altitude
		current_alt = aq.get("INDICATED_ALTITUDE")
		if current_alt > -300:
			ui_friendly_dictionary["INDICATED_ALTITUDE"] = round(current_alt)
			previous_alt = current_alt
		else:
			try:
				ui_friendly_dictionary["INDICATED_ALTITUDE"] = previous_alt
			except:
				pass

		# LOC and APPR Mode
		try:
			if (ui_friendly_dictionary["AUTOPILOT_APPROACH_HOLD"] == 1 and ui_friendly_dictionary["AUTOPILOT_GLIDESLOPE_HOLD"] == 1):
				ui_friendly_dictionary["AUTOPILOT_APPR_MODE"] = 1
			else:
				ui_friendly_dictionary["AUTOPILOT_APPR_MODE"] = 0
			if (ui_friendly_dictionary["AUTOPILOT_APPROACH_HOLD"] == 1 and ui_friendly_dictionary["AUTOPILOT_GLIDESLOPE_HOLD"] == 0):
				ui_friendly_dictionary["AUTOPILOT_LOC_MODE"] = 1
			else:
				ui_friendly_dictionary["AUTOPILOT_LOC_MODE"] = 0
		except:
			None

	while True:
		asyncio.run(ui_dictionnary(ui_friendly_dictionary, previous_alt))
		sleep(0.3)

# SimConnect App 2
def simconnect_thread_func2(threadname):

	global ui_friendly_dictionary

	while True:
		try:
			sm = SimConnect()
			break
		except:
			None

	ae = AircraftEvents(sm)
	aq = AircraftRequests(sm)

	def thousandify(x):
		return f"({x:,})"

	async def ui_dictionnary(ui_friendly_dictionary):
		# Additional for performance
		ui_friendly_dictionary["LATITUDE"] = round(aq.get("PLANE_LATITUDE"))
		ui_friendly_dictionary["LONGITUDE"] = round(aq.get("PLANE_LONGITUDE"))
		#ui_friendly_dictionary["AUTOPILOT_HEADING_LOCK_DIR"] = round(aq.get("AUTOPILOT_HEADING_LOCK_DIR"))
		ui_friendly_dictionary["AUTOPILOT_ALTITUDE_LOCK_VAR"] = thousandify(round(aq.get("AUTOPILOT_ALTITUDE_LOCK_VAR")))
		ui_friendly_dictionary["AUTOPILOT_VERTICAL_HOLD_VAR"] = aq.get("AUTOPILOT_VERTICAL_HOLD_VAR")
		ui_friendly_dictionary["AUTOPILOT_AIRPSPEED_HOLD_VAR"] = round(aq.get("AUTOPILOT_AIRSPEED_HOLD_VAR"))
	while True:
		asyncio.run(ui_dictionnary(ui_friendly_dictionary))

# SimConnect LVAR Reading
def simconnect_thread_func3(threadname):

	global ui_friendly_dictionary
	global selected_plane

	sm = SimConnectMobiFlight()
	vr = MobiFlightVariableRequests(sm)
	vr.clear_sim_variables()

	while True:
		#DEFAULT/GENERIC
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
	thread1 = Thread(target=simconnect_thread_func, args=('Thread-1', ))
	thread2 = Thread(target=flask_thread_func, args=('Thread-2', ))
	thread3 = Thread(target=simconnect_thread_func2, args=('Thread-3', ))
	thread4 = Thread(target=simconnect_thread_func3, args=('Thread-4', ))
	thread1.start()
	thread2.start()
	thread3.start()
	thread4.start()

	sleep(0.5)