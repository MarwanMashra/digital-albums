
$(document).ready(function () {
    
    path = window.location.pathname
    if (path.split("/")[1] == "album") {
        album_id = path.split("/")[2]
        $.ajax({
            type: "POST",
            url: "/album/" + album_id,
            success: function(data) {
                if (data["status"] == "success") {
                    album = data["album"]
                    if (album_id[0] == "e") {
                        addEditSection(album, album_id)
                    }
                    displayAlbum(album, album_id)
                } else{
                    console.log(data["message"])
                }
            }
        });
    }
});

function addEditSection(album, album_id){
    $('#edit_section').replaceWith(`
            <h4> Share album :</h4>
            <input type="button" class="btn btn-secondary copy-btn copy-btn-view" id="copy-btn-view" value="copy view link"></input>  
            <input type="button" class="btn btn-secondary copy-btn copy-btn-edit" id="copy-btn-edit" value="copy edit link"></input>  
            <br><br>
            <div id="delete-section">
                <h4> Delete album :</h4>
                <button class="btn btn-danger" id="delete-album-btn">Delete</button>
            </div>
            <h4><br>Add images :</h4>
            <form method="POST" action="/upload" name="form-upload-images" id="form-upload-images" enctype="multipart/form-data">
                <div class="input-images"></div>
                <input type="hidden" name="album_id" value="${album_id}">
                <button id="upload-button" class="btn btn-primary">Upload</button>
            </form>
        `);
    $('.copy-btn').click(function () {
        current_location = window.location.href.split("/").slice(0, -1).join("/")+'/'
        if ($(this).attr("id") =="copy-btn-edit") {
            navigator.clipboard.writeText(current_location+album['edit_url'])
            $(this).removeClass('btn-secondary').addClass('btn-success').attr("value", "link copied!");
            $("#copy-btn-view").removeClass('btn-success').addClass('btn-secondary').attr("value", "copy view link");
        } else {
            navigator.clipboard.writeText(current_location+album['view_url'])
            $(this).removeClass('btn-secondary').addClass('btn-success').attr("value", "link copied!");
            $("#copy-btn-edit").removeClass('btn-success').addClass('btn-secondary').attr("value", "copy edit link");
        }
    });

    function addDeleteButtonEvent() {
        $('#delete-album-btn').click(function () {
            $("#delete-section").replaceWith(`
            <div id="delete-section-confirmation">
                <h4> Delete album :</h4>
                <input type="text" class="form-control" id="delete-album-input" placeholder="Enter album name to delete definitely">
                <button class="btn btn-danger" id="delete-album-confirm-btn">Delete definitely</button>
                <button class="btn btn-secondary" id="delete-album-cancel-btn">Cancel</button>
                </div>
            `);
            addDeleteButtonEvent();
        });

        $('#delete-album-cancel-btn').click(function () {
            $("#delete-section-confirmation").replaceWith(`
                <div id="delete-section">
                    <h4> Delete album :</h4>
                    <button class="btn btn-danger" id="delete-album-btn">Delete</button>
                </div>
            `);
            addDeleteButtonEvent();
        });

        $('#delete-album-confirm-btn').click(function () {
            album_name_input = $('#delete-album-input').val().trim()
            if (album_name_input == album['name']) {
                $("#delete-album-confirm-btn").prop('disabled', true);
                $("#delete-album-cancel-btn").prop('disabled', true);
                $.ajax({
                    type: "POST",
                    url: "/delete_album/" + album_id + "/" + album['creator'],
                    success: function (data) {
                        if (data["status"] == "success") {
                            window.location.href = "/";
                        } else {
                            console.log(data["message"])
                        }
                    }
                });
            }
            addDeleteButtonEvent();
        });

    }
    addDeleteButtonEvent();
    $('.input-images').imageUploader();
    $('#form-upload-images').submit(function (e) {
        // disable submit button
        $("#upload-button").prop('disabled', true);
        $("input[name='images[]']").attr("name", "images");
    });
}

function displayAlbum(album, album_id) {
    $('#album_name').replaceWith(`
        <h1 id="album_name">Album: ${album['name']}
        <button style="float: right;" class="btn btn-secondary" id="btn-home-page">Home Page</button>
        </h1>
    `);
    $('#btn-home-page').click(function () {
        window.location.href = "/";
    });
    html = `
        <div class="container-sm">
            <div class="row justify-content-center">
                <div class="col col-md-10">
                    <div class="gallery-container" id="animated-thumbnails-gallery">
    `
    album['images'].forEach(function(image) {
        html += `
            <a class="gallery-item" data-src="${image}">
                <img class="img-responsive" src="${image}"/>
            </a>
        `       
    });
    html += `</div></div></div></div>`

    $('#gallery').replaceWith(html);
    $("#animated-thumbnails-gallery").
        justifiedGallery({
            captions: false,
            rowHeight: 180,
            margins: 5
        }).
        on("jg.complete", function () {
            lightGallery(document.getElementById('animated-thumbnails-gallery'), {
                plugins: [lgAutoplay, lgComment, lgFullscreen, lgHash, lgPager, lgRotate, lgShare, lgVideo, lgZoom, lgThumbnail],
                thumbnail: true,
                speed: 300,
                download: false,
                cssEasing: "cubic-bezier(0.25, 0, 0.25, 1)",
                // mode: "lg-fade",
        });
    });
}
