const DropCourses = {
    addition:[],
    removal:[],
    get_data: function() {
        return {"add_courses": this.addition, "remove_courses":this.removal}
    },
    is_empty: function() {
        return ((this.addition.length + this.removal.length) == 0);
    },
    indexAtAddlist: function(value) {
        return this.addition.findIndex(i => i == value);
    },
    indexAtRemlist: function(value) {
        return this.removal.findIndex(i => i == value);
    },
    add2addition: function(value) {
        this.addition.push(value)
    },
    add2removal: function(value) {
        this.removal.push(value);
    },
    deleteXaddition: function(value) {
        let idx = this.indexAtAddlist(value)
        this.addition.splice(idx, 1);
    },
    deleteXremoval: function(value) {
        let idx = this.indexAtRemlist(value);
        this.removal.splice(idx, 1);
    }
}


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


function showError(alertContainer, msg) {
    $(`#${alertContainer}`).removeClass("alert-success");
    $(`#${alertContainer}`).addClass("alert-danger");
    $(`#${alertContainer}`).text(msg)
    $(`#${alertContainer}`).show(200,()=>{
        setTimeout(()=>{
            $(`#${errorContainer}`).hide()
        }, 60000)
    })
}

function showInfo(alertContainer, msg) {
    $(`#${alertContainer}`).removeClass("alert-danger");
    $(`#${alertContainer}`).addClass("alert-success");
    $(`#${alertContainer}`).text(msg)
    $(`#${alertContainer}`).show(200,()=>{
        setTimeout(()=>{
            $(`#${errorContainer}`).hide()
        }, 60000)
    })
}


function hideModal(modalId) {
    $(`#${modalId}`).modal('hide'); 
}



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
    }

    return data;
}

function createCourse() {
    payload = getNewCourseData()
    if (payload) {
        $.ajax({
            type: "post",
            url: create_course_api,
            dataType: "json",
            contentType: "application/json",
            beforeSend: function(xhr){
                $("#createCourseAlert").hide()
                $("#createCourseAddBtn").attr("disabled", true)
                xhr.setRequestHeader("X-CSRFToken", csrftoken)
            },
            data: JSON.stringify(payload),
            cache: false,
            success: function(response) {
                hideModal("newSemesterEntryModal");
                showInfo("createCourseAlert", "New course created successfully! Reloading page in a moments")
                setTimeout(()=>{location.reload()}, 3000)
            },
            error: function(xhr, status, error) {
                $("#createCourseAddBtn").removeAttr("disabled");
                showError("createCourseAlert", error);
            },
        });
    }
}

function updateDropcourse() {
    if (DropCourses.is_empty()) {
        return
    }
    $.ajax({
        type: "post",
        url: drop_course_update_api,
        dataType: "json",
        contentType: "application/json",
        beforeSend: function(xhr){
            $("#dropCourseModalAlert").hide()
            $("#selectionConfirmBtn").attr("disabled", true)
            xhr.setRequestHeader("X-CSRFToken", csrftoken)
        },
        data: JSON.stringify(DropCourses.get_data()),
        cache: false,
        success: function(response) {
            // hideModal("dropCourseModal");
            console.log(response);
            // showInfo("createCourseAlert", "New course created successfully! Reloading page in a moments")
            // setTimeout(()=>{location.reload()}, 3000)
        },
        error: function(xhr, status, error) {
            $("#selectionConfirmBtn").removeAttr("disabled");
            showError("dropCourseModalAlert", error);
        },
    });
}

$(document).ready(function () {
    $("#createCourseAddBtn").on('click', createCourse)
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
    $("#selectionConfirmBtn").on('click', updateDropcourse)
    $(".btn-check").on("change", function(){
        let checked_status = $(this).prop("checked");
        let course_id = $(this).attr("id");;
        if (checked_status) {
            // todo: if a course is already present in the semester drop course, do not add to addlist
            if (DropCourses.indexAtRemlist(course_id) >= 0) {
                DropCourses.deleteXremoval(course_id);
            }
            DropCourses.add2addition(course_id)
        } else {
            if (DropCourses.indexAtAddlist(course_id) >= 0) {
                DropCourses.deleteXaddition(course_id);
            }
            // todo: if a course is already present in the semester drop course, add to removelist
            // DropCourses.remListAdd(course_id)
        }
        if (DropCourses.is_empty()) {
            $("#selectionConfirmBtn").attr('disabled', true);
        } else {
            $("#selectionConfirmBtn").removeAttr("disabled");
        }
    })
});