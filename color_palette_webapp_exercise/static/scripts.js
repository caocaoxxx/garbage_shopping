// 添加上elem可以实现特效显示在不同的色块上，否则会永远显示在第一个色块上
function startAnimation(elem) {
  const lines = elem.querySelector('.lines');
  lines.classList.add('start');
  setTimeout(() => {
    lines.classList.remove('start');
  }, 600);
}

function createColorBlock(color) {
    // 创建一个包含颜色值的 div
    var colorDiv = $("<div>").addClass("color-block").css({
        "background-color": color,
        "width": "100px",
        "height": "100px",
        "display": "flex",
        "align-items": "center",
        "justify-content": "center",
        "position": "relative",
    });

    // 创建一个包含颜色值的文本
    var colorText = $("<p>").text(color).css({
        "position": "absolute",
        "top": "50%",
        "left": "50%",
        "transform": "translate(-50%, -50%)",
        "color": "#ffffff", // 修改文字颜色为白色
    });

    var copyMessage = $("<p>").text("已拷贝").css({
        "position": "absolute",
        "top": "50%",
        "left": "50%",
        "transform": "translate(-50%, -50%)",
        "color": "#ffffff", // 修改文字颜色为白色
        "display": "none"
    });


    // 添加 lines 的子 div 实现鼠标 hover时的动画效果的div
    var lines = $('<div>').addClass("lines").html('<div><svg><rect x="0" y="0" width="100%" height="100%" rx="0" ry="0" pathLength="10"></rect></svg></div>');
    colorDiv.append(lines);

    // 将颜色值文本和“copy”消息 div 添加到颜色块中
    colorDiv.append(colorText);
    colorDiv.append(copyMessage);


    // 为 colorDiv 添加点击事件处理程序
    colorDiv.click(function() {
        // 复制颜色值到剪贴板
        var tempInput = $("<input>").val(color).appendTo("body").select();
        document.execCommand("copy");
        tempInput.remove();

        // 在颜色块上显示“copy”字样
        colorText.css("display", "none");
        copyMessage.css("display", "block");
    });

    // 当鼠标离开颜色块时，恢复显示颜色的16进制数字
    colorDiv.mouseleave(function() {
        colorText.css("display", "block");
        copyMessage.css("display", "none");
    });

    // 添加函数，使得鼠标放上去时可以显示色块边界动画
    colorDiv.mouseenter(function() {
        startAnimation(this);
    });

    return colorDiv;
}

$("#generateButton").click(function() {
    $.post("/random_palette", function(data) {
        var paletteDisplay = $("#paletteDisplay");
        paletteDisplay.empty();

        for (var i = 0; i < data.length; i++) {
            var colorDiv = createColorBlock(data[i]);
            paletteDisplay.append(colorDiv);
        }
    });
});


$("#imageFile").change(function() {
    if (this.files && this.files[0]) {
        cropBox.style.left = "0px";
        cropBox.style.top = "0px";
        var reader = new FileReader();

        reader.onload = function(e) {
            $("#imagePreview").attr("src", e.target.result);

            $("#imagePreview").show();
        };

        reader.readAsDataURL(this.files[0]);
    }
});

$("#uploadButton").click(function() {
    var originalImageSize = getOriginalImageSize($("#imagePreview")[0]);
    var scaleX = originalImageSize.width / $("#imagePreview").width();
    var scaleY = originalImageSize.height / $("#imagePreview").height();

    updateCropBoxCoords(scaleX, scaleY);

    var file_data = $("#imageFile").prop("files")[0];

    var form_data = new FormData();

    form_data.append("file", file_data);

    form_data.append("cropBoxCoords", $("#cropBoxCoords").val());

    var xhr = new XMLHttpRequest();

    xhr.open("POST", "/upload_image");

    xhr.onload = function() {
        if (xhr.status === 200) {
            var data = JSON.parse(xhr.responseText);
            var imagePaletteDisplay = $("#imagePaletteDisplay");
            imagePaletteDisplay.empty();

            for (var i = 0; i < data.length; i++) {
                var colorDiv = createColorBlock(data[i]);
                imagePaletteDisplay.append(colorDiv);
            }
        } else {
            alert("Error uploading image");
        }
        $("#imagePaletteDisplay .loader").remove();
    };

    var loader = $('<div class="loader"></div>');
    $("#imagePaletteDisplay").append(loader);
    xhr.send(form_data);
});


function getOriginalImageSize(img) {
    var tempImage = new Image();
    tempImage.src = img.src;
    return {
        width: tempImage.width,
        height: tempImage.height,
    };
}

var cropBox = document.getElementById("cropBox");
var imagePreview = document.getElementById("imagePreview");
var cropBoxCoords = document.getElementById("cropBoxCoords");

function initCropBox() {
    cropBox.style.width = imagePreview.clientWidth + "px";
    cropBox.style.height = imagePreview.clientHeight + "px";
    cropBox.style.display = "block";
    updateCropBoxCoords();
}

imagePreview.addEventListener("load", initCropBox);

var dragging = false;
var resizing = false;
var startX, startY;
var initialWidth, initialHeight;

cropBox.addEventListener("mousedown", function(e) {
    startX = e.clientX;
    startY = e.clientY;
    initialWidth = parseInt(cropBox.style.width);
    initialHeight = parseInt(cropBox.style.height);

    if (e.target === cropBox) {
        dragging = true;
    } else if (e.target === resizeHandle) {
        resizing = true;
    }
});

window.addEventListener("mousemove", function(e) {
    if (dragging) {
        var deltaX = e.clientX - startX;
        var deltaY = e.clientY - startY;

        var newX = Math.max(0, Math.min(imagePreview.clientWidth - cropBox.clientWidth, deltaX));
        var newY = Math.max(0, Math.min(imagePreview.clientHeight - cropBox.clientHeight, deltaY));

        cropBox.style.left = newX + "px";
        cropBox.style.top = newY + "px";
        updateCropBoxCoords();
    } else if (resizing) {
        var deltaX = e.clientX - startX;
        var deltaY = e.clientY - startY;

        var newWidth = Math.max(0, Math.min(imagePreview.clientWidth - parseInt(cropBox.style.left), initialWidth + deltaX));
        var newHeight = Math.max(0, Math.min(imagePreview.clientHeight - parseInt(cropBox.style.top), initialHeight + deltaY));

        cropBox.style.width = newWidth + "px";
        cropBox.style.height = newHeight + "px";
        updateCropBoxCoords();
    }
});

window.addEventListener("mouseup", function(e) {
    dragging = false;
    resizing = false;
});

function updateCropBoxCoords(scaleX = 1, scaleY = 1) {
    var x = parseInt(cropBox.style.left) || 0;
    var y = parseInt(cropBox.style.top) || 0;
    var width = parseInt(cropBox.style.width);
    var height = parseInt(cropBox.style.height);

    cropBoxCoords.value =
        Math.round(x * scaleX) +
        "," +
        Math.round(y * scaleY) +
        "," +
        Math.round(width * scaleX) +
        "," +
        Math.round(height * scaleY);
}
