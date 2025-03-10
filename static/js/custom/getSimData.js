let altitude;
let fuel_percentage;
let vertical_speed;
let compass;
let airspeed;
let latitude;
latitude = 0;
let longitude;
longitude = 0;

let autopilot_master;
let autopilot_nav_selected;
let autopilot_wing_leveler;
let autopilot_heading_lock;
let autopilot_heading_lock_dir;
let autopilot_altitude_lock;
let autopilot_altitude_lock_var;
let autopilot_attitude_hold;
let autopilot_glidescope_hold;
let autopilot_approach_hold;
let autopilot_backcourse_hold;
let autopilot_vertical_hold;
let autopilot_vertical_hold_var;
let autopilot_pitch_hold;
let autopilot_pitch_hold_ref;
let autopilot_flight_director_active;
let autopilot_airspeed_hold;
let autopilot_airspeed_hold_var;

let gear_handle_position;
let elevator_trim_pct;
let elevator_trim_pct_reversed;
let rudder_trim_pct;
let flaps_handle_pct;
let flaps_handle_pct_reversed;

let cabin_seatbelts_alert_switch;
let cabin_no_smoking_alert_switch;

let light_taxi;

//Maps Size Fix Function
let map_size_fix;
let map_size_fix_mod;
map_size_fix = 0;

window.setInterval(function(){
    getSimulatorData();
    displayData()
    updateMap()
}, 2000);


function getSimulatorData() {
    $.getJSON($SCRIPT_ROOT + '/ui', {}, function(data) {

        // SIM DATA
        sim_rate = data.SIMULATION_RATE;

        // Position Data
        latitude = data.LATITUDE;
        longitude = data.LONGITUDE;

    });
    return false;
}


function displayData() {
    // SIM DATA
    $("#sim-rate").text(sim_rate);


    //Navigation
    $("#altitude").text(altitude);
    $("#compass").text(compass);
    $("#vertical-speed").text(vertical_speed);
    $("#airspeed").text(airspeed);

    //Fuel
    $("#fuel-percentage").text(fuel_percentage);
    $("#fuel-percentage-bar").css("width", fuel_percentage+"%");

    //Autopilot
    checkAndUpdateButton("#autopilot-master", autopilot_master, "Engaged", "Disengaged");
    checkAndUpdateButton("#autopilot-wing-leveler", autopilot_wing_leveler);
    checkAndUpdateButton("#autopilot-heading-lock", autopilot_heading_lock);
    checkAndUpdateButton("#autopilot-altitude-lock", autopilot_altitude_lock);
    checkAndUpdateButton("#autopilot-airspeed-hold", autopilot_airspeed_hold);
    checkAndUpdateButton("#autopilot-attitude-hold", autopilot_attitude_hold);
    checkAndUpdateButton("#autopilot-backcourse-hold", autopilot_backcourse_hold);
    checkAndUpdateButton("#autopilot-approach-hold", autopilot_approach_hold);
    checkAndUpdateButton("#autopilot-vertical-hold", autopilot_vertical_hold);
    checkAndUpdateButton("#light-taxi", light_taxi);

    $("#autopilot-heading-lock-dir").attr('placeholder', autopilot_heading_lock_dir);
    $("#autopilot-altitude-lock-var").attr('placeholder', autopilot_altitude_lock_var);
    $("#autopilot-airspeed-hold-var").attr('placeholder', autopilot_airspeed_hold_var);
    $("#autopilot-pitch-hold-ref").attr('placeholder', autopilot_pitch_hold_ref);
    $("#autopilot-vertical-hold-ref").attr('placeholder', autopilot_vertical_hold_var);

    //Control surfaces
    $("#gear-handle-position").html(gear_handle_position);
    if (gear_handle_position === "UP"){
        $("#gear-handle-position").removeClass("btn-success").addClass("btn-danger");
    } else {
        $("#gear-handle-position").removeClass("btn-danger").addClass("btn-success");
    }

    $("#flaps-handle-pct").text(flaps_handle_pct);
    $("#flaps-slider").slider({values: [flaps_handle_pct_reversed]})

    $("#elevator-trim-pct").text(elevator_trim_pct);
    $("#elevator-trim-slider").slider({values: [elevator_trim_pct_reversed]})

    //$("#rudder-trim-pct").text(rudder_trim_pct);
    //$("#rudder-trim-slider").slider({values: [rudder_trim_pct]})

    //Cabin
    if (cabin_seatbelts_alert_switch === 1){
        $("#seatbelt-sign").removeClass("btn-outline-danger").addClass("btn-danger").html("Seatbelt sign on");
    } else {
        $("#seatbelt-sign").removeClass("btn-danger").addClass("btn-outline-danger").html("Seatbelt sign off");
    }

    if (cabin_no_smoking_alert_switch === 1){
        $("#no-smoking-sign").removeClass("btn-outline-danger").addClass("btn-danger").html("No smoking sign on");
    } else {
        $("#no-smoking-sign").removeClass("btn-danger").addClass("btn-outline-danger").html("No smoking sign off");
    }}

function checkAndUpdateButton(buttonName, variableToCheck, onText="On", offText="Off") {
    if (variableToCheck === 1) {
        $(buttonName).removeClass("btn-danger").addClass("btn-success").html(onText);
    } else {
        $(buttonName).removeClass("btn-success").addClass("btn-danger").html(offText);
    }
}


function toggleFollowPlane() {
    followPlane = !followPlane;
    if (followPlane === true) {
        $("#followMode").text("Moving map enabled")
        $("#followModeButton").removeClass("btn-danger").addClass("btn-primary")
    }
    if (followPlane === false) {
        $("#followMode").text("Moving map disabled")
        $("#followModeButton").removeClass("btn-primary").addClass("btn-danger")
    }
}

function toggleGPStrack() {
    trackGPS = !trackGPS;
    if (trackGPS === true) {
        $("#GPStrackButton").removeClass("btn-danger").addClass("btn-primary");
        trackline.setStyle({opacity: 1.0});
    }
    if (trackGPS === false) {
        $("#GPStrackButton").removeClass("btn-primary").addClass("btn-danger")
        trackline.setStyle({opacity: 0});
    }
}

function updateMap() {
    var pos = L.latLng(latitude, longitude);

    marker.setLatLng(pos, {
        duration: 1500,
    });
    marker.setRotationAngle(compass);

    if (followPlane === true) {
        map.panTo(pos);
    }
}

function mapRefreshFix() {
	map_size_fix = map_size_fix + 1;
	map_size_fix_mod = map_size_fix % 2;
	
	if (map_size_fix_mod = 0) {
		$('#map_row').height('+=1');
	} else {
		$('#map_row').height('-=1');
	};
	
	map_size_fix = map_size_fix * 1;
}

function refreshMapSize() {
	setInterval(function () {
	map.invalidateSize();
	}, 1000);
}

function setSimDatapoint(datapointToSet, valueToUse) {
    url_to_call = "/datapoint/"+datapointToSet+"/set";
    $.post( url_to_call, { value_to_use: valueToUse } );
}

function triggerSimEvent(eventToTrigger, valueToUse, hideAlert = false){
    url_to_call = "/event/"+eventToTrigger+"/trigger";
    $.post( url_to_call, { value_to_use: valueToUse } );

    if (!hideAlert) {
        temporaryAlert('', "Sending instruction", "success")
    }
}

function triggerSimEventFromField(eventToTrigger, fieldToUse, messageToDisplay = null){
    // Get the field and the value in there
    fieldToUse = "#" + fieldToUse
    valueToUse = $(fieldToUse).val();

    // Pass it to the API
    url_to_call = "/event/"+eventToTrigger+"/trigger";
    $.post( url_to_call, { value_to_use: valueToUse } );

    // Clear the field so it can be repopulated with the placeholder
    $(fieldToUse).val("")

    if (messageToDisplay) {
        temporaryAlert('', messageToDisplay + " to " + valueToUse, "success")
    }

}

function triggerCustomEmergency(emergency_type) {
    url_to_call = "/custom_emergency/" + emergency_type
    $.post (url_to_call)

    if (emergency_type === "random_engine_fire") {
        temporaryAlert("Fire!", "Random engine fire trigger sent", "error")
    }
}


function temporaryAlert(title, message, icon) {
    let timerInterval

    Swal.fire({
        title: title,
        html: message,
        icon: icon,
        timer: 2000,
        timerProgressBar: true,
        onBeforeOpen: () => {
            Swal.showLoading()
            timerInterval = setInterval(() => {
                const content = Swal.getContent()
                if (content) {
                    const b = content.querySelector('b')
                    if (b) {
                        b.textContent = Swal.getTimerLeft()
                    }
                }
            }, 100)
        },
        onClose: () => {
            clearInterval(timerInterval)
        }
    }).then((result) => {
        /* Read more about handling dismissals below */
        if (result.dismiss === Swal.DismissReason.timer) {
            console.log('I was closed by the timer')
        }
    })
}