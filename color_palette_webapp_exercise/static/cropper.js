var cropBox = document.getElementById("cropBox"); // 获取裁剪框元素
var imagePreview = document.getElementById("imagePreview"); // 获取图片预览元素
var cropBoxCoords = document.getElementById("cropBoxCoords"); // 获取裁剪框坐标元素

function initCropBox() { // 初始化裁剪框
  cropBox.style.width = imagePreview.clientWidth + "px"; // 设置裁剪框宽度为图片预览元素的宽度
  cropBox.style.height = imagePreview.clientHeight + "px"; // 设置裁剪框高度为图片预览元素的高度
  cropBox.style.display = "block"; // 显示裁剪框
  updateCropBoxCoords(); // 更新裁剪框坐标
}

imagePreview.addEventListener("load", initCropBox); // 监听图片预览元素的加载事件，加载完成后初始化裁剪框

var dragging = false; // 是否正在拖动裁剪框
var resizing = false; // 是否正在调整裁剪框大小
var startX, startY; // 鼠标按下时的坐标
var initialWidth, initialHeight; // 裁剪框初始宽度和高度

cropBox.addEventListener("mousedown", function (e) { // 监听裁剪框的鼠标按下事件
  startX = e.clientX; // 记录鼠标按下时的横坐标
  startY = e.clientY; // 记录鼠标按下时的纵坐标
  initialWidth = parseInt(cropBox.style.width); // 记录裁剪框初始宽度
  initialHeight = parseInt(cropBox.style.height); // 记录裁剪框初始高度

  if (e.target === cropBox) { // 如果鼠标按下的是裁剪框本身
    dragging = true; // 标记正在拖动裁剪框
  } else if (e.target === resizeHandle) { // 如果鼠标按下的是裁剪框的调整大小手柄
    resizing = true; // 标记正在调整裁剪框大小
  }
});

window.addEventListener("mousemove", function (e) { // 监听窗口的鼠标移动事件
  if (dragging) { // 如果正在拖动裁剪框
    var deltaX = e.clientX - startX; // 计算鼠标横向移动距离
    var deltaY = e.clientY - startY; // 计算鼠标纵向移动距离

    cropBox.style.left = deltaX + "px"; // 设置裁剪框的左边距
    cropBox.style.top = deltaY + "px"; // 设置裁剪框的上边距
    updateCropBoxCoords(); // 更新裁剪框坐标
  } else if (resizing) { // 如果正在调整裁剪框大小
    var deltaX = e.clientX - startX; // 计算鼠标横向移动距离
    var deltaY = e.clientY - startY; // 计算鼠标纵向移动距离

    cropBox.style.width = initialWidth + deltaX + "px"; // 设置裁剪框的宽度
    cropBox.style.height = initialHeight + deltaY + "px"; // 设置裁剪框的高度
    updateCropBoxCoords(); // 更新裁剪框坐标
  }
});

window.addEventListener("mouseup", function (e) { // 监听窗口的鼠标松开事件
  dragging = false; // 标记停止拖动裁剪框
  resizing = false; // 标记停止调整裁剪框大小
});

function updateCropBoxCoords() { // 更新裁剪框坐标
  var x = parseInt(cropBox.style.left) || 0; // 获取裁剪框的左边距
  var y = parseInt(cropBox.style.top) || 0; // 获取裁剪框的上边距
  var width = parseInt(cropBox.style.width); // 获取裁剪框的宽度
  var height = parseInt(cropBox.style.height); // 获取裁剪框的高度

  cropBoxCoords.value = x + "," + y + "," + width + "," + height; // 更新裁剪框坐标元素的值
}

