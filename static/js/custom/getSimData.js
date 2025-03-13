// SIM DATA
let sim_rate;
sim_rate = 0;

// POSITION DATA
let compass;
let latitude;
latitude = 0;
let longitude;
longitude = 0;

//Maps Size Fix Function
let map_size_fix;
let map_size_fix_mod;
map_size_fix = 0;

window.setInterval(function(){
    getSimulatorData();
    displayData()
    updateMap()
}, 500);


function getSimulatorData() {
    $.getJSON($SCRIPT_ROOT + '/ui', {}, function(data) {

        // SIM DATA
        sim_rate = data.SIMULATION_RATE;

        // POSITION DATA
        latitude = data.LATITUDE;
        longitude = data.LONGITUDE;
        compass = data.COMPASS_MAG;

    });
    return false;
}

function displayData() {}

function checkAndUpdateButton(buttonName, variableToCheck, onText="On", offText="Off") {
    if (variableToCheck === 1) {
        $(buttonName).removeClass("btn-danger").addClass("btn-success").html(onText);
    } else {
        $(buttonName).removeClass("btn-success").addClass("btn-danger").html(offText);
    }
}

function toggleFollowPlane() {
    followPlane = followPlane + 1;
	if (followPlane === 4) {
		followPlane = 1
	}
    if (followPlane === 1) {
        $("#followMode").text("Unfollow Plane")
        $("#followModeButton").removeClass("btn-info btn-sm").addClass("btn-primary btn-sm")
		marker.addTo(map);
    }
    if (followPlane === 2) {
        $("#followMode").text("Hide Plane")
        $("#followModeButton").removeClass("btn-primary btn-sm").addClass("btn-info btn-sm")
    }
	if (followPlane === 3) {
        $("#followMode").text("Show Plane")
		$("followModeButton").removeClass("btn-primary btn-sm").addClass("btn-success btn-sm")
		marker.remove();
    }
}

function toggleGPStrack() {
    trackGPS = !trackGPS;
    if (trackGPS === true) {
        $("#GPStrackButton").removeClass("btn-danger btn-sm").addClass("btn-primary btn-sm");
        trackline.setStyle({opacity: 1.0});
    }
    if (trackGPS === false) {
        $("#GPStrackButton").removeClass("btn-primary btn-sm").addClass("btn-danger btn-sm")
        trackline.setStyle({opacity: 0});
    }
}

function updateMap() {
    var pos = L.latLng(latitude, longitude);

    marker.setLatLng(pos, {
        duration: 200,
    });
    marker.setRotationAngle(compass);

    if (followPlane === 1) {
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