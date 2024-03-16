$(document).ready(function() {
    let createModal =$('#create-modal')
    let updateModal =$('#update-modal')
    let images = ["../images/15_Q0rCeTd.jpg", "../images/768.png", "../images/cover.jpg", "../images/IMG_nMnY6QO.jpg", "../images/R_1.jpg", "../images/wp.jpg"]
    let centralData;
    let globalName;
    let secondTbody = $("#search-and-filter-tbody")
    let firstTbody = $('#first-tbody')
    let searchResultsOnly = $('.search-body-only ')
    let p = $("<p>").addClass("font-xl text-red-600 text-center mt-8").text("Nothing found")


    function createANewTableRow(item, element){
        let store = []
        const createdDate = new Date(item.created);
        const expiresDate = new Date(item.expires);

        const differenceMs = Math.abs(expiresDate - createdDate);

        let dateDue = "";
        // Convert milliseconds to days, hours, minutes, and seconds
        const days = Math.floor(differenceMs / (1000 * 60 * 60 * 24));
        const hours = Math.floor((differenceMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((differenceMs % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((differenceMs % (1000 * 60)) / 1000);


        if(days > 1){
            dateDue = `${days} days, ${minutes} mins`
        }else if(days < 1 && minutes > 1){
            dateDue = `${minutes} mins`
        }else if(days < 1 && minutes < 1 && seconds > 1){
            dateDue = `${seconds} secs`
        }


        console.log(item.expires - item.created);
        let random = Math.floor(Math.random()* images.length)
        let random2 = Math.floor(Math.random()* images.length)
        
        let tr = $('<tr>').addClass('table-rows shadow-md my-3 rounded-lg');
    
        // Create and append td for the first column
        let td1 = $('<td>').addClass('px-6 py-4 whitespace-nowrap');
        let div1 = $('<div>').addClass('flex items-center gap-3');
        div1.append($('<img>').attr('src', item.image).attr('alt', item.name).addClass('w-[20px] h-[20px] rounded-full'));
        let leftDiv = $('<div>').addClass('left');
        leftDiv.append($('<p>').addClass('table-name text-base font-bold').text(item.name));
        leftDiv.append($('<div>').addClass('date text-gray-400 text-sm').text('Oct 11, 2021'));
        div1.append(leftDiv);
        td1.append(div1);
        tr.append(td1);

        // Creating and append td for the second column
        console.log(dateDue);
        let td2 = $('<td>').addClass('w-fit px-6 py-4 whitespace-nowrap');
        td2.append($('<p>').addClass('text-center bg-blue-50 rounded p-2').text(dateDue));
        tr.append(td2);

        // Create and append td for the third column
        let td3 = $('<td>').addClass('px-6 py-4 whitespace-nowrap');
        td3.append($('<p>').addClass('font-bold').text(item.tasks_number +"/"+item.total_tasks));
        td3.append($('<p>').addClass('text-sm text-gray-400').text('Tasks'));
        tr.append(td3);

        // Create and append td for the fourth column
        let td4 = $('<td>').addClass('px-6 py-4 whitespace-nowrap w-full');
        td4.append($('<p>').addClass('text-blue-300').text('In Progress'));
        let progressBarDiv = $('<div>').addClass('w-full bg-gray-400 rounded-lg overflow-hidden');
        progressBarDiv.append($('<div>').attr('id', 'progress-bar').addClass(bg-blue-300 h-2 w-[${5}px]));
        td4.append(progressBarDiv);
        tr.append(td4);
        // Create and append td for the fifth column
        let td5 = $('<td>').addClass(' px-4 py-4 whitespace-nowrap relative');
        let div2 = $('<div>').addClass('image-parent flex items-center');
        let strings =  item.contributors.split(",")
        div2.append($('<img>').attr('src', images[random]).attr('alt', strings[0]).addClass('first-string w-[20px] h-[20px] rounded-full'));
        div2.append($('<img>').attr('src', images[random2]).attr('alt', strings[1]).addClass('second-string w-[20px] h-[20px] rounded-full'));
        let innerDiv = $('<div>').addClass('w-[20px] h-[20px] rounded-full bg-purple-50 relative flex flex-col justify-center items-center');
        innerDiv.append($('<div>').addClass('flex absolute').append($('<p>').addClass('text-sm text-purple-300').text('+')).append($('<p>').addClass('text-sm text-purple-300').text('3')));
        div2.append(innerDiv);
        div2.append($('<div>').addClass('task-options').append($('<i>').addClass('fa fa-ellipsis-v ml-4 text-gray-500 text-sm cursor-pointer').attr('aria-hidden', 'true')));
        let showOptionsDiv = $('<div>').addClass('show-options').addClass('w-[120px] hidden bg-white px-4 py-3 right-[40px] rounded-lg absolute top-0');
        showOptionsDiv.append($('<div>').addClass('flex gap-3 cursor-pointer mb-4').append($('<p>').addClass('text-gray-500').text('Delete').addClass('delete-task')));
        showOptionsDiv.append($('<div>').addClass('show-update').addClass('flex gap-3 cursor-pointer').append($('<p>').addClass('text-gray-500').attr('id', 'delete-task').text('Update')));
        div2.append(showOptionsDiv);
        td5.append(div2);
        tr.append(td5);

        // Append the created row to the table body
        console.log(element);
        element.append(tr);
    }

    $('#create-task').on('click',function(){
        createModal.show()
    })
    
   
    $('#show-filter-options').on('click',function(){
        $('#filter-options').toggle()
    })

    $('#button-close').on('click',function(){
        createModal.hide()
    })

    $('#update-button-close').on('click',function(){
        updateModal.hide()
    })

 
    // fecthing request
    $.ajax({
        url: 'http://127.0.0.1:8000/tasks/list/',
        method: 'GET',
        dataType: 'json',
        success: function(response) {
            console.log(response);
            centralData = response
            // Iterate over each item in the response
            $.each(response, function(index, item) {
                createANewTableRow(item, firstTbody)
            
            });
        },
        error: function(xhr, status, error) {
            console.error('Error fetching data:', error);
        }
    });
    
    

    // submit form
    $('#create-submit').click(function (e) {
        e.preventDefault();
        let formData = new FormData();
        formData.append('name', $('#name').val());
        formData.append('contributors', $('#contributors').val());
        formData.append('created', $('#expires').val());
        formData.append('image', $('#task_id_file')[0].files[0]);
        

        $.ajax({
            url: 'http://127.0.0.1:8000/tasks/create/',
            method: 'POST',
            processData: false, 
            contentType: false, 
            data: formData,
            success: function (response) {
                console.log(response);
                createModal.hide();
                createANewTableRow(response, firstTbody);
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

            },
            error: function (xhr, status, error) {
                console.log(error);
                Toastify({
                    text: error,
                    duration: 3000,
                    newWindow: true,
                    gravity: "top",
                    position: "right",
                    stopOnFocus: true,
                    style: {
                        background: "linear-gradient(to right, #00b09b, #96c93d)",
                    },
                }).showToast();
            }
        });
    });
    

    // to show delete and update options
    $(document).on('click', '.task-options', function() {
        let $showOptionsDiv = $(this).closest('td').find('.show-options');
        $showOptionsDiv.toggle();
    });
    

    // to delete a task
    $(document).on('click', '.delete-task', function() {
        let clickedTaskOptions = $(this); 
        let name = clickedTaskOptions.closest('tr').find('.table-name').text();
        let tr = clickedTaskOptions.closest('.table-rows')
        let $showOptionsDiv = $(this).closest('td').find('.show-options');

        $showOptionsDiv.hide()
        
        $.ajax({
            url: `http://127.0.0.1:8000/tasks/delete/${name}/`,
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
                        background: "linear-gradient(to right, #00b09b, #96c93d)",
                    },
                }).showToast();
            }
            });
    });
    

    // to show the update modal
    $(document).on('click', ".show-update", function(){
        let clickedTaskOptions = $(this); 
        let $showOptionsDiv = clickedTaskOptions.closest('td').find('.show-options');
        $showOptionsDiv.hide()
        let name = clickedTaskOptions.closest('tr').find('.table-name').text();
        let firstString = clickedTaskOptions.closest('td').find('.first-string').attr('alt');
        let secondString = clickedTaskOptions.closest('td').find('.second-string').attr('alt');
        let form = $('#updatename')
        let contributors = $('#updatecontributors')
        globalName = name
        form.val(name)
        contributors.val(firstString+","+secondString)
        updateModal.show()
    })

    // updating tasks
    $("#update-submit").on('click', function(e) {
        

        let name = $('#updatename').val()
        e.preventDefault();  
        let formData = {
        name: name,
        contributors: $('#updatecontributors').val()
        };
        $.ajax({
            url: `http://127.0.0.1:8000/tasks/update/${globalName}/`,
            method: 'PATCH',
            data:formData,
            dataType: 'json',
            success: function(response) {
                updateModal.hide()
                Toastify({
                    text: "Update successfull",
                    duration: 3000,
                    newWindow: true,
                    gravity: "top", 
                    position: "right", 
                    stopOnFocus: true, 
                    style: {
                        background: "linear-gradient(to right, #00b09b, #96c93d)",
                    },
                    }).showToast();
            },
            error: function(xhr, status, error) {
                console.log(error);
                Toastify({
                    text: error,
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
            }
            });
    });
    
     // filtering by status
     $('#filter-options').on('click', 'p', function() {
        const clickedValue = $(this).text();
        firstTbody.hide()
        searchResultsOnly.hide()
        secondTbody.html("")

        
        let flag = false
        for(data of centralData){
            console.log(centralData);
            console.log(data.status);
            console.log(clickedValue === data.status);
            if(data.status ===clickedValue ){
                flag = true
                createANewTableRow(data, secondTbody)
                console.log("ran");
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
        searchResultsOnly.hide()
        firstTbody.show()
    })


    let baseTypingTimer;
    // Function to perform the AJAX request
    function search(query) {
        // Construct the URL with the query parameter
        const url = 'http://127.0.0.1:8000/tasks/search/?q=' + query;

        // Clear previous timeouts
        clearTimeout(baseTypingTimer);

        // Set a new timeout
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
                    $('#result-number').text(data.length)
                    console.log(data);
                    if (data.length >= 1) {
                        $.each(data, function(index, item) {
                           createANewTableRow(item, secondTbody)
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
        }, 500); // Set timeout to 500 milliseconds
    }

    $("#input-search").on('input', function() {
        const query = $(this).val().trim(); 
        search(query); 
    });

    const taskCreateparentmodalpreview = $("#parentmodalpreview")
    const taskfileinputcontainer = $(".task-file-input-container")
    const taskCreatemodalpreview = $("#modalpreview")
    const uploadsubmitButton = $("#uploadsubmitButton")
    const uploadCancelButton = $("#uploadcancelButton")
    const uploadpreview = $("#uploadPreview")
    const modalpreviewCancel = $("#task-preview-cancel")
    const uploadpreviewImage = $("#uploadPreviewImage")
    const taskUploadImage = $("#task_id_file")

    function previewFn(e, uploadpreviewImage, modalpreviewCancel, uploadPreview, uploadCancelButton, uploadsubmitButton, taskCreatemodalpreview, taskfileinputcontainer, taskCreateparentmodalpreview){
        const reader = new FileReader();
        let selectedFile = e.target.files[0];
        // console.log($(this))
        // console.log($(this)[0])
        // console.log($(this).closest('body').find('#create-modal'));
        // console.log($(this).closest('#task_id_file').closest("#create-modal")[0]);
        let parent = $('#create-modal');
    
        if (selectedFile) {
            reader.onload = function (e) {
                $(uploadpreviewImage).attr('src', e.target.result);
                $(uploadPreview).css('display', 'block');
                $(parent).css('display', 'none');
            };
            reader.readAsDataURL(selectedFile);
        }
    
        $(uploadCancelButton).click(function (e) {
            $(uploadpreviewImage).val("");
            $(uploadPreview).css('display', 'none');
        });
    
        $(modalpreviewCancel).click(function (e) {
            $(modalpreview).val("");
            $(parentmodalpreview).css('display', 'none');
            $(taskfileinputcontainer).css('display', 'block');
        });
    
        $(uploadsubmitButton).click(function (e) {
            $(uploadPreview).css('display', 'none');
            $(parent).css('display', 'block');
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
        previewFn(e, uploadpreviewImage, modalpreviewCancel, uploadPreview, uploadCancelButton, uploadsubmitButton, taskCreatemodalpreview, taskfileinputcontainer, taskCreateparentmodalpreview)    
    })

});





