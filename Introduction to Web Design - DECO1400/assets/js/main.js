function toggle_background_video_sound() {
    let soundButton = document.getElementById("soundtrack_toggle_button");
    let vid = document.getElementById("home_background_video");

    if (vid.muted) {
        soundButton.innerHTML = "&#Xf028;";
        vid.muted = false;
    }
    else {
        soundButton.innerHTML = "&#Xf026;";
        vid.muted = true;
    }

}


function toggle_soundtrack_sound() {
    // debugger;
    let soundButton = document.getElementById("soundtrack_toggle_button");
    let sound = document.getElementById("story_soundtrack");

    if (sound.muted) {
        soundButton.innerHTML = "&#Xf028;";
        sound.muted = false;
    }
    else {
        soundButton.innerHTML = "&#Xf026;";
        sound.muted = true;
    }

}

toggle_background_video_sound();
toggle_soundtrack_sound();
