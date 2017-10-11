function toggle_visibility(n) {
    var myList = document.getElementsByClassName("lesson_div");
    for (i = 0; i < myList.length; i++) {
        if (i == n) {
            myList[i].style.display = 'block';
        } else {
            myList[i].style.display = 'none';
        }
    }
}
