$(document).ready(function() {
    let createModal =$('#create-modal')
    let aiChatModal =$('#ai-chat-modal')
    let individualTaskModal =$('#individual-task-modal')
    let updateModal =$('#update-modal')
    let images = ["images/15_Q0rCeTd.jpg", "images/768.png", "images/cover.jpg", "images/IMG_nMnY6QO.jpg", "images/R_1.jpg", "images/wp.jpg"]
    let centralData;
    let globalTr;
    let globalClickedTaskOptions;
    let globalName;
    let globalRowNumber;
    let secondTbody = $("#search-and-filter-tbody")
    let firstTbody = $('#first-tbody')
    let searchResultsOnly = $('.search-body-only ')
    let p = $("<p>").addClass("font-xl text-red-600 text-center mt-8").text("Nothing found")



    function createANewTableRow(item, index, element){

        function getDateOnly(date) {
            return new Date(date.getFullYear(), date.getMonth(), date.getDate());
        }

        const now = new Date();
        const dueDate = new Date(item.expires);

        // 🔑 THIS is the key change
        const today = getDateOnly(now);
        const due = getDateOnly(dueDate);

        const diffMs = due - today;
        const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));

        let dateDue = "";
        // let progress = 0;

        if (diffDays > 1) {
            dateDue = `In ${diffDays} days`;
        } else if (diffDays === 1) {
            dateDue = "In 1 day";
            // progress = 90
        } else if (diffDays === 0) {
            dateDue = "Due today";
            // progress = 100
        } else {
            dateDue = `Overdue by ${Math.abs(diffDays)} day${Math.abs(diffDays) > 1 ? "s" : ""}`;
        }


        let random = Math.floor(Math.random()* images.length)
        let random2 = Math.floor(Math.random()* images.length)

        // table row
        let tr = $('<tr>').addClass('table-rows shadow-md my-3 rounded-lg relative');
    
        // Create and append td for the first column
        let td1 = $('<td>').addClass('task-click-button px-6 py-4 whitespace-nowrap cursor-pointer');
        let div1 = $('<div>').addClass('flex items-center gap-3');
        div1.append($('<img>').attr('src', item.image_url).attr('alt', item.name).addClass('first-img fw-[20px] h-[20px] rounded-full'));
        let leftDiv = $('<div>').addClass('left');
        leftDiv.append($('<p>').addClass('table-name text-base font-bold').text(item.name));
        leftDiv.append($('<div>').addClass('date text-gray-400 text-sm').text('Oct 11, 2021'));
        div1.append(leftDiv);
        td1.append(div1);
        tr.append(td1);

        // Creating and append td for the second column
        let td2 = $('<td>').addClass('due-in pl-6 pr-4 py-4 whitespace-nowrap');
        td2.append($('<p>').addClass('text-center bg-blue-50 rounded p-2').text(dateDue)).attr('content', item.expires);
        // adding numbers for easy updating of centraldata
        let tableNumber = $('<div>').addClass('hidden');
        tableNumber.attr('data', index)
        td2.append(tableNumber)
        tr.append(td2);
        if(window.innerWidth > 768 && td2){
            td2.css('display', 'table-cell');
        }
        else{
            td2.css('display', 'none');
        }
        
       

        // Create and append td for the third column
        let td3 = $('<td>').addClass('pr-6 pl-4 py-4 whitespace-nowrap ');
        td3.append($('<p>').addClass('font-bold').text(item.tasks_number +"/"+item.total_tasks));
        td3.append($('<p>').addClass('text-sm text-gray-400').text('Tasks'));
        tr.append(td3);

        // Create and append td for the fourth column
        const itemCreated = getDateOnly(new Date(item.created));
        const itemDue = getDateOnly(new Date(item.expires));
        const itemNow = getDateOnly(new Date());

        const totalDays = (itemDue - itemCreated) / (1000 * 60 * 60 * 24);
        const elapsedDays = (itemNow - itemCreated) / (1000 * 60 * 60 * 24);

        let progress = (elapsedDays / totalDays) * 100;
        progress = Math.max(0, Math.min(100, progress));

        console.log(progress, "shuu33333333", elapsedDays, totalDays, itemCreated, itemDue); 
        let td4 = $('<td>').addClass('status px-6 whitespace-nowrap');
        td4.append($('<p>').addClass('text-blue-300').text('Progress'));
        let progressBarDiv = $('<div>').addClass('w-[80%] bg-gray-200 rounded-lg overflow-hidden');
        let progressBarDivSubDiv = $('<div>').attr('id', 'progress-bar').addClass('bg-blue-300 h-2').css("width", `${progress}%`);
        progressBarDiv.append(progressBarDivSubDiv);
        
        td4.append(progressBarDiv);
        tr.append(td4);
        if(window.innerWidth > 768 && td4){
            td4.css('display', 'table-cell');
        }
        else{
            td4.css('display', 'none');
        }

        // Create and append td for the fifth column
        let td5 = $('<td>').addClass('px-6 py-4 flex items-center whitespace-nowrap');
        let div2 = $('<div>').addClass('image-parent flex items-center');
        let strings =  item.contributors.split(",")
        div2.append($('<img>').attr('src', images[random]).attr('alt', strings[0]).addClass('first-string w-[20px] h-[20px] rounded-full'));
        div2.append($('<img>').attr('src', images[random2]).attr('alt', strings[1]).addClass('second-string w-[20px] h-[20px] rounded-full'));
        let innerDiv = $('<div>').addClass('w-[20px] h-[20px] rounded-full bg-purple-50 relative flex flex-col justify-center items-center');
        innerDiv.append($('<div>').addClass('flex absolute').append($('<p>').addClass('text-sm text-purple-300').text('+')).append($('<p>').addClass('text-sm text-purple-300').text('3')));
        div2.append(innerDiv);
        let showOptionsDiv = $('<div>').addClass('show-options').addClass('w-[120px] hidden bg-white px-4 py-3 right-[40px] rounded-lg absolute top-[40px] z-50');
        showOptionsDiv.append($('<div>').addClass('flex gap-3 cursor-pointer mb-4').append($('<p>').addClass('text-gray-500').text('Delete').addClass('delete-task')));
        showOptionsDiv.append($('<div>').addClass('show-update').addClass('flex gap-3 cursor-pointer mb-4').append($('<p>').addClass('text-gray-500').text('Update')));
        showOptionsDiv.append($('<div>').addClass('show-finish').addClass('flex gap-3 cursor-pointer').append($('<p>').addClass('text-gray-500').text('Finish')));
        // div2.append(showOptionsDiv);
        td5.append(div2);
        td5.append($('<div>').addClass('task-options').append($('<i>').addClass('fa fa-ellipsis-v ml-4 text-gray-500 text-sm cursor-pointer').attr('aria-hidden', 'true')));
        td5.append(showOptionsDiv);
        tr.append(td5);

        // Append the created row to the table body
        element.append(tr);
    }

    window.addEventListener('resize', ()=>{       
        // adjusting for DUE IN
        const show = window.innerWidth > 768;
        document.querySelectorAll('.due-in').forEach(td => {
            td.style.display = show ? 'table-cell' : 'none';
        });

        // adjusting for STATUS
        document.querySelectorAll('.status').forEach(td => {
            td.style.display = show ? 'table-cell' : 'none';
        });
    });

    // toggle history bar
    $('#expand-history').on('click', function () {
        $('#ai-history').toggle();
    });
    // show create task modal
    $('#create-task').on('click',function(){
        createModal.show()
    })
    
    // open ai chat dialogue open and close
    $('#ai-chat-support').on('click',function(){
        aiChatModal.show()
    })
    $('#ai-chat-modal-close').on('click',function(){
        aiChatModal.hide()
        $("#ai-chat-placeholder").show()
        $("#ai-chat-body").empty()
    })
    
    // open individual chat modal
    $(document).on("click", ".task-click-button", function () {
        
        individualTaskModal.show()

        const $row = $(this);
        console.log("TITLE:", $row);

        const title = $row.find(".table-name").text();
        const date = $row.find(".date").text();
        const due = $row.find(".due-in p").text();
        const imgSrc = $row.find(".first-img").attr('src');

        let container = $("<div>").addClass("w-full border-b border-b-gray-300 py-2 flex justify-space-between items-center gap-4");
        let nameHolder = $("<div>")
        let imageContainer = $("<div>")

        // image
        let img = $("<img>")
        .attr("src", imgSrc)
        .addClass("w-[30px] h-[30px] rounded-full");

        // text
        let titleP = $("<p>").addClass("font-bold").text(title);
        let dateP = $("<p>").addClass("text-sm text-gray-400").text(date);
        let dueP = $("<p>").addClass("text-sm text-blue-400").text(due);

        // append everything
        let taskProfile = $("#task-profile")
        nameHolder.append(dateP, dueP);
        imageContainer.append(img,titleP);
        container.append(imageContainer, nameHolder);
        taskProfile.empty()
        taskProfile.append(container);


    });

    $('#ai-chat-support').on('click',function(){
        
    })
    $('#individual-task-modal-close').on('click',function(){
        individualTaskModal.hide()
    })
    
   
    $('#show-filter-options').on('click',function(){
        $('#filter-options').toggle()
    })

    // hide create task modal
    $('#button-close').on('click',function(){
        createModal.hide()
    })

    $('#update-button-close').on('click',function(){
        updateModal.hide()
    })

 
    // fecthing request
    $.ajax({
        url: `${ENV.API_URL}/tasks/list/`,
        method: 'GET',
        dataType: 'json',
        success: function(response) {
            centralData = response
            // Iterate over each item in the response
            $.each(response, function(index, item) {
                createANewTableRow(item, index, firstTbody)
            
            });
            $("#loading").hide()
        },
        error: function(xhr, status, error) {
            console.error('Error fetching data:', error);
            $("#loading").hide()
        }
        
    });
    
    

    // submit form
    $('#create-submit').click(function (e) {
        $("#loadingmodal").show()
        e.preventDefault();
        let formData = new FormData();
        formData.append('name', $('#name').val());
        formData.append('contributors', $('#contributors').val());
        formData.append('expires', $('#expires').val());
        formData.append('image', $('#task_id_file')[0].files[0]);
        

        $.ajax({
            url: `${ENV.API_URL}/tasks/create/`,
            method: 'POST',
            processData: false, 
            contentType: false, 
            data: formData,
            success: function (response) {
                centralData.push(response)
                createModal.hide();
                createANewTableRow(response, index=0, firstTbody);
                Toastify({
                    text: "Task created",
                    duration: 3000,
                    newWindow: true,
                    gravity: "top", 
                    position: "right", 
                    stopOnFocus: true, 
                    style: {
                        background: "linear-gradient(to right, #00b09b, #96c93d)",
                    },
                }).showToast();
                $("#loadingmodal").hide()
            },
            error: function (xhr, status, error) {
                console.log(xhr.responseJSON); // Log the error response for debugging
    
                let errorMessages = xhr.responseJSON; // Capture error messages
    
                // Display each error message dynamically
                for (const [field, message] of Object.entries(errorMessages)) {
                    Toastify({
                        text: `${field}: ${message}`,
                        duration: 5000,
                        newWindow: true,
                        gravity: "top",
                        position: "right",
                        stopOnFocus: true,
                        style: {
                            background: "linear-gradient(to right, #ff5f6d, #ffc371)", // Red gradient for errors
                        },
                    }).showToast();
                }
    
                $("#loadingmodal").hide()
            },
        });
        
    });
    

    // to show delete and update options
    $(document).on('click', '.task-options', function() {
        let $showOptionsDiv = $(this).closest('td').find('.show-options');
        $showOptionsDiv.toggle();
    });
    

    // to delete a task
    $(document).on('click', '.delete-task', function() {
        $("#loadingmodal").show()
        let clickedTaskOptions = $(this); 
        let name = clickedTaskOptions.closest('tr').find('.table-name').text();
        let tr = clickedTaskOptions.closest('.table-rows')
        let $showOptionsDiv = $(this).closest('td').find('.show-options');

        $showOptionsDiv.hide()
        
        $.ajax({
            url: `${ENV.API_URL}/tasks/delete/${name}/`,
            method: 'DELETE',
            dataType: 'json',
            success: function(response) {
                tr.hide()
                Toastify({
                    text: "Deleted successfully",
                    duration: 3000,
                    newWindow: true,
                    gravity: "top", 
                    position: "right", 
                    stopOnFocus: true, 
                    style: {
                        background: "linear-gradient(to right, #00b09b, #96c93d)",
                    },
                    // onClick: function(){} // Callback after click
                }).showToast();
                $("#loadingmodal").hide()
                
            },
            error: function(xhr, status, error) {
                Toastify({
                    text: error,
                    duration: 3000,
                    newWindow: true,
                    gravity: "top", 
                    position: "right", 
                    stopOnFocus: true, 
                    style: {
                        background: "linear-gradient(to right, #ff5f6d, #ffc371)",
                    },
                }).showToast();
                $("#loadingmodal").hide()
            }
            });
    });

    // to show the update modal
    $(document).on('click', ".show-update", function(){
        let clickedTaskOptions = $(this);
        globalClickedTaskOptions = $(this); 
        let $showOptionsDiv = clickedTaskOptions.closest('td').find('.show-options');
        $showOptionsDiv.hide()
        let name = clickedTaskOptions.closest('tr').find('.table-name').text();
        let closestTr = $(this).closest('.table-rows');
        let associatedImage = closestTr.find('img').attr('src');
        let contentTd = closestTr.find('td[content]');     
        let contentValue = contentTd.attr('content');
        let contentNumber = contentTd.find('div[data]');
        globalRowNumber = contentNumber.attr('data')
        let firstString = clickedTaskOptions.closest('td').find('.first-string').attr('alt');
        let secondString = clickedTaskOptions.closest('td').find('.second-string').attr('alt');
        globalTr = $(this).closest('.table-rows');
        
        let form = $('#updatename')
        let contributors = $('#updatecontributors')
        let date = $('#update-expires')
        const dateValue = new Date(contentValue).toISOString().split('T')[0];
        date.val(dateValue)
        let image = $('#update-modalpreview')
        image.attr("src", associatedImage)
        globalName = name
        form.val(name)
        contributors.val(firstString+","+secondString)


        updateModal.show()
    })

    // updating tasks
    $("#update-submit").off('click').on('click', async function (e) {
        
        $("#loadingmodal").show();
        e.preventDefault();
    
        let formData = new FormData();

         // Checking if a new file is selected
        if ($('#update-task_id_file')[0].files[0]) {
            formData.append('image', $('#update-task_id_file')[0].files[0]);
        } else {
            // If no file is selected, i fetch the image from the `src` attribute
            const imageSrc = $('#update-modalpreview').attr('src');
            if (imageSrc && imageSrc !== '#') {
                const secureImageSrc = imageSrc.replace('http://', 'https://');
                try {
                    // Fetch the image and convert it to a Blob
                    const response = await fetch(secureImageSrc);


                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const blob = await response.blob();
    
                    // Create a File object from the Blob
                    const duplicatedImage = new File([blob], "duplicated_image.jpg", { type: blob.type });
    
                    // Append the duplicated image to FormData
                    formData.append('image', duplicatedImage);
                } catch (error) {
                    console.error("Failed to duplicate the image:", error);
                    Toastify({
                        text: "Error duplicating image",
                        duration: 3000,
                        gravity: "top",
                        position: "right",
                        style: {
                            background: "linear-gradient(to right, #ff5f6d, #ffc371)",
                        },
                    }).showToast();
                    $("#loadingmodal").hide();
                    return; // Stop further processing if image duplication fails
                }
            }
        }
    
        // Append fields if they are not empty
        if ($('#updatename').val() !== "") {
            formData.append('name', $('#updatename').val());
        }
        if ($('#updatecontributors').val() !== "") {
            formData.append('contributors', $('#updatecontributors').val());
        }
        if ($('#update-expires').val() !== "") {
            formData.append('expires', $('#update-expires').val());
        }
    
    
        // Perform the AJAX request
        $.ajax({
            url: `${ENV.API_URL}/tasks/update/${globalName}/`,
            method: 'PATCH',
            data: formData,
            processData: false,
            contentType: false,
            success: function (response) { 
                globalTr.find('.first-img').attr('src', response.image_url);
                let contentTd = globalTr.find('td[content]');
                contentTd.attr('content', response.expires);
                let strings = response.contributors.split(",");
                globalClickedTaskOptions.closest('tr').find('.table-name').text(response.name);
                globalClickedTaskOptions.closest('td').find('.first-string').attr('alt', strings[0]);
                globalClickedTaskOptions.closest('td').find('.second-string').attr('alt', strings[1]);
                updateModal.hide();
                Toastify({
                    text: "Update successful",
                    duration: 3000,
                    newWindow: true,
                    gravity: "top",
                    position: "right",
                    stopOnFocus: true,
                    style: {
                        background: "linear-gradient(to right, #00b09b, #96c93d)",
                    },
                }).showToast();
                $("#loadingmodal").hide();
            },
            error: function (xhr, status, error) {
                console.log(xhr.responseJSON); // Log the error response for debugging
    
                let errorMessages = xhr.responseJSON; // Capture error messages
    
                // Display each error message dynamically
                for (const [field, message] of Object.entries(errorMessages)) {
                    Toastify({
                        text: `${field}: ${message}`,
                        duration: 3000,
                        newWindow: true,
                        gravity: "top",
                        position: "right",
                        stopOnFocus: true,
                        style: {
                            background: "linear-gradient(to right, #ff5f6d, #ffc371)",
                        },
                    }).showToast();
                }
                $("#loadingmodal").hide();
            },
        });
    });
    
    // all results back
    $('#all-back').on('click', function(){
        firstTbody.show()
        searchResultsOnly.hide()
        secondTbody.hide()
        $('.all-results').hide()
    })
     // filtering by status
     $('#filter-options').on('click', 'p', function() {
        const clickedValue = $(this).text();
        firstTbody.hide()
        searchResultsOnly.hide()
        secondTbody.html("")
        $('.all-results').show()

        
        let flag = false
        for(data of centralData){
            if(data.status ===clickedValue ){
                flag = true
                createANewTableRow(data, index=0, secondTbody)
            }
        }
        if(flag === false){
            firstTbody.hide()
            secondTbody.hide()
            searchResultsOnly.empty()
            searchResultsOnly.css("display", "flex")
            searchResultsOnly.append(p)

            
        }else{
            flag && secondTbody.show()
        }
    })

    // hiding search and filter results
    $('#back').on('click',function(){
        secondTbody.hide()
        $(".results").hide()
        searchResultsOnly.hide()
        firstTbody.show()
    })


    let baseTypingTimer;
    // Function to perform the AJAX request
    function search(query) {
        const url = `${ENV.API_URL}/tasks/search/?q=` + query;

        // Clear previous timeouts
        clearTimeout(baseTypingTimer);

        // Setting a new timeout
        baseTypingTimer = setTimeout(function() {
            firstTbody.hide()
            secondTbody.hide()
            searchResultsOnly.empty()
            searchResultsOnly.css("display", "flex")
            // searchResultsOnly.show()
            $.ajax({
                url: url,
                type: 'GET',
                dataType: 'json',
                success: function(data) {
                    secondTbody.empty(); 
                    secondTbody.show();
                    if(data.length > 0){
                        $(".results").show()
                    } 
                    $('#result-number').text(data.length)
                    if (data.length >= 1) {
                        $.each(data, function(index, item) {
                           createANewTableRow(item, index, secondTbody)
                        });
                    }else{
                        searchResultsOnly.append(p)
                    }
                },
                error: function(xhr, textStatus, errorThrown) {
                    p.html(errorThrown)
                    searchResultsOnly.append(p)
                    console.error('Request failed:', textStatus, errorThrown);
                }
            });
        }, 500);
    }

    $("#input-search").on('input', function() {
        const query = $(this).val().trim(); 
        search(query); 
    });

    const taskCreateparentmodalpreview = $("#parentmodalpreview")
    const updateCreateparentmodalpreview = $("#update-parentmodalpreview")

    const updateTaskfileinputcontainer = $(".update-task-file-input-container")
    const taskfileinputcontainer= $(".task-file-input-container")

    const taskCreatemodalpreview = $("#modalpreview")
    const updatemodalpreview = $("#update-modalpreview")

    // preview buttons
    const uploadsubmitButton = $("#uploadsubmitButton")
    const uploadCancelButton = $("#uploadcancelButton")
    const generalpreview = $("#uploadPreview")
    const uploadpreviewImage = $("#uploadPreviewImage")


    const modalpreviewCancel = $("#task-preview-cancel")
    const updateModalpreviewCancel = $("#update-task-preview-cancel")
    // const taskUploadImage = $("#task_id_file")
    // const updateTaskUploadImage = $("#update-task_id_file")

    function previewFn(e, parentModal, uploadpreviewImage, modalpreviewCancel, uploadPreview, uploadCancelButton, uploadsubmitButton, modalpreview, taskfileinputcontainer, parentmodalpreview){
        const reader = new FileReader();
        let selectedFile = e.target.files[0];

        if (selectedFile) {
            reader.onload = function (e) {
                $(uploadpreviewImage).attr('src', e.target.result);
                $(uploadPreview).css('display', 'block');
                $(parentModal).css('display', 'none');
            };
            reader.readAsDataURL(selectedFile);
        }
    
        $(uploadCancelButton).click(function (e) {
            $(uploadpreviewImage).val("");
            $(uploadPreview).css('display', 'none');
            $(parentModal).css('display', 'block');

        });
    
        $(modalpreviewCancel).click(function (e) {
            alert("clicked")
            $(modalpreview).val("");
            $(parentmodalpreview).css('display', 'none');
            $(taskfileinputcontainer).css('display', 'block');
        });
    
        $(uploadsubmitButton).click(function (e) {
            $(uploadPreview).css('display', 'none');
            $(parentModal).css('display', 'block');
            $(modalpreview).css('display', 'block');
            const selectedFileUrl = URL.createObjectURL(selectedFile);
            $(taskfileinputcontainer).css({'display':'flex', "align-items":"center"});
            $(taskfileinputcontainer).css('justify-content', 'center');
            $(taskfileinputcontainer).css('gap', '1rem');
            $(parentmodalpreview).css({'display':'flex', "align-items":"center"});
            $(modalpreview).attr('src', selectedFileUrl);
        });
    }
    
    $("#task_id_file").on("change", (e)=>{
        previewFn(e, createModal, uploadpreviewImage, modalpreviewCancel, generalpreview, uploadCancelButton, uploadsubmitButton, taskCreatemodalpreview, taskfileinputcontainer, taskCreateparentmodalpreview)    
    })

    $("#update-task_id_file").on("change", (e)=>{
        previewFn(e, updateModal, uploadpreviewImage, updateModalpreviewCancel, generalpreview, uploadCancelButton, uploadsubmitButton, updatemodalpreview, updateTaskfileinputcontainer, updateCreateparentmodalpreview)    
    })


    $(document).on('click', ".show-finish", function(){
        let name = $(this).closest('tr').find('.table-name').text();
        let $showOptionsDiv = $(this).closest('td').find('.show-options');
        $showOptionsDiv.hide()
        
        $.ajax({
            url: `${ENV.API_URL}/tasks/finish-tasks/${name}/`,
            method: 'PATCH',
            dataType: 'json',
            success: function(response) {
                centralData[globalRowNumber] = response
                Toastify({
                    text: "Task marked as finished",
                    duration: 3000,
                    newWindow: true,
                    gravity: "top", 
                    position: "right", 
                    stopOnFocus: true, 
                    style: {
                        background: "linear-gradient(to right, #00b09b, #96c93d)",
                    },
                    // onClick: function(){} // Callback after click
                }).showToast();
                
            },
            error: function(xhr, status, error) {
                let errorMessage = xhr.responseJSON.error || "An error occurred.";
                Toastify({
                    text: errorMessage,
                    duration: 3000,
                    newWindow: true,
                    gravity: "top", 
                    position: "right", 
                    stopOnFocus: true, 
                    style: {
                        background: "linear-gradient(to right, #ff5f6d, #ffc371)",
                    },
                }).showToast();
            }
            });
    })

    function displayMessage(userMessage){
        $("#ai-chat-placeholder").hide()
        $("#ai-chat-body-parent").show()
        console.log("message55555555")
        // create and append the user's message to the chat body
        userResponseDiv = $("<div>").addClass("user-response-div bg-gray-200 p-3 w-fit rounded-lg h-fit self-end mt-2");
        imageAndReplyDIv = $("<div>").addClass("ai-response-div flex gap-3 mt-2 items-center self-start");
        userText = $("<p>").addClass("text-sm").text(userMessage);
        aiImage= $("<img>").attr("src", "images/gradient.jpg").addClass("rounded-full w-[35px]")
        
        userResponseDiv.append(userText);
        console.log(userMessage, "userMessage")
        $("#ai-chat-body").append(userResponseDiv);

        // add a loader to wait for a response from the server
        loader = $("<span>").addClass("loader").attr("id", "ai-chat-spinner")
        loaderAndReplyDIv = $("<div>");
        aiReply = $("<p>").addClass("text-sm hidden");
        loaderAndReplyDIv.append(loader, aiReply);
        imageAndReplyDIv.append(aiImage, loaderAndReplyDIv);
        $("#ai-chat-body").append(imageAndReplyDIv);
        // imageAndReplyDIv.append(loader);
        return {"aiReply":aiReply, "loader":loader};
        
   };

    // chat api calls
    function sendMessage(message) {
        reply = displayMessage(message);

        $.ajax({
            url: `${ENV.API_URL}/tasks/ai-chat/`,
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ message: message }),

            success: function (response) {
                // displayMessage(response.reply);
                console.log("reply", reply)
                reply.aiReply.text(response.reply);
                reply.aiReply.show();
                reply.loader.hide();
                console.log(response.reply, "response from ai chat", reply)
            },

            error: function (err) {
                console.error("Error:", err);
            }
        });
    }


    function handleSend(triggerElement) {
        const id = $(triggerElement).attr("id");
        let message;
        let input;
        console.log("Request coming from ID:", id);

       if (id === "send-icon" || id === "ai-chat") {
        input = $("#ai-chat");
        } 
        else if (id === "chat-send-icon" || id === "ai-chat-input") {
            input = $("#ai-chat-input");
        }
        message = input.val();


        console.log("omo", message, "choi", input)
        
        if (message && message.trim() !== "") {
            sendMessage(message);
            input.val("");
        }
    }

    // Icon Click Listeners
    $("#send-icon, #chat-send-icon").on("click", function() {
        handleSend(this); 
    });
    
    // Enter key listener
    $("#ai-chat, #ai-chat-input").on("keypress", function(e) {
        if (e.which === 13) {
            handleSend(this);
        }
    });


    function generateCircles() {
        const container = document.getElementById('shared-dom');
        container.innerHTML = ''; // Clear existing circles
    
        // Get the screen width
        const screenWidth = window.innerWidth;
    
        // Calculate the number of circles based on screen size
        const circleCount = Math.floor(screenWidth / 100); // Example: 1 circle per 100px of width
    
        // Create the circles dynamically
        for (let i = 0; i < circleCount; i++) {
            const circle = document.createElement('div');
            circle.classList.add('sub-rect');
            container.appendChild(circle);
        }
    }
    
    // Generate circles on page load
    generateCircles();
    
    // Regenerate circles on window resize
    window.addEventListener('resize', generateCircles);
    
  
});





