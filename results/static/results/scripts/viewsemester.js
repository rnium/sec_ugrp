function showNotification(msg) {
    const elem = document.getElementById('notificationModal')
    const toastBody = document.getElementById('modal-body');
    toastBody.innerText = msg;
    const mBootstrap = new bootstrap.Modal(elem);
    mBootstrap.show()
}

const saveBtn = document.getElementById("save-btn")
saveBtn.addEventListener('click', ()=>{
    // do some saving stuff
    showNotification("Saved Successfully!")
})


function showDevModal(id) {
    const elem = document.getElementById(id)
    const mBootstrap = new bootstrap.Modal(elem);
    mBootstrap.show()
}

showDevModal("newEntryModal")

const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))


function getNewCourseData() {
    let courseCodeIn = $("#courseCodeInput").val().trim();
    let courseTitleIn = $("#courseTitleInput").val().trim();
    let totalMarksIn = parseInt($("#totalMarksInput").val().trim());
    let creditsIn = parseInt($("#courseCreditsInput").val().trim());
    let partAMarksIn = parseInt($("#partAmarksInput").val().trim());
    let partBMarksIn = parseInt($("#partBmarksInput").val().trim());
    let incourseMarksIn = parseInt($("#inCourseMarksInput").val().trim());
    
    let courseCodeArray = courseCodeIn.split(" ")
    let courseCodeNumber = parseInt(courseCodeArray[1])
    
    if (isNaN(totalMarksIn) | isNaN(creditsIn) | isNaN(partAMarksIn) | isNaN(partBMarksIn) | isNaN(incourseMarksIn)) {
        $("#createCourseAlert").text("Invalid Input(s), please fill correctly");
        $("#createCourseAlert").show()
        return false;
    }

    if (courseCodeIn.length == 0 | courseTitleIn.length == 0) {
        $("#createCourseAlert").text("Please fill all the fields");
        $("#createCourseAlert").show()
        return false;
    }
    if (courseCodeArray.length != 2 | isNaN(courseCodeNumber)) {
        $("#createCourseAlert").text("Invalid Course code! Please enter correctly.");
        $("#createCourseAlert").show()
        return false;
    }
    let semesterCodeOfCC = parseInt(courseCodeNumber.toString()[0])
    if (semesterNthNumber != semesterCodeOfCC) {
        $("#createCourseAlert").text("Invalid Course code for this semester!");
        $("#createCourseAlert").show()
        return false;
    }
    if ((partAMarksIn+partBMarksIn+incourseMarksIn) > totalMarksIn) {
        $("#createCourseAlert").text("Invalid Marks Distribution!");
        $("#createCourseAlert").show()
        return false;
    }
    else {
        $("#createCourseAlert").hide()
    }
    
    data = {
        "semester": semesterId,
        "code": courseCodeIn,
        "title": courseTitleIn,
        "course_credit": creditsIn,
        "total_marks": totalMarksIn,
        "part_A_marks": partAMarksIn,
        "part_B_marks": partBMarksIn,
        "incourse_marks": incourseMarksIn,
        "added_by": userId,
    }

    return data;
}

$(document).ready(function () {
    $("#createCourseAddBtn").on('click', ()=>{
        console.log(getNewCourseData());
    })
    $(".marksinput").on('keyup', function(){
        let totalMarksIn = parseInt($("#totalMarksInput").val().trim());
        let partAMarksIn = parseInt($("#partAmarksInput").val().trim());
        let partBMarksIn = parseInt($("#partBmarksInput").val().trim());
        let incourseMarksIn = parseInt($("#inCourseMarksInput").val().trim());
        if (isNaN(totalMarksIn) | isNaN(partAMarksIn) | isNaN(partBMarksIn) | isNaN(incourseMarksIn)) {
            $("#incourseInfoAlert").hide()
        }
        else {
            let marksDiff = totalMarksIn - (partAMarksIn+partBMarksIn);
            if (marksDiff != incourseMarksIn) {
                $("#incourseInfoAlert .from").text(incourseMarksIn)
                $("#incourseInfoAlert .to").text(marksDiff)
                $("#incourseInfoAlert").show()
            }
            else {
                $("#incourseInfoAlert").hide()
            }
        }
    })
});