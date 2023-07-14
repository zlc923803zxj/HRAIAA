console.log("Chat.js 已被加载！");

// 在这里添加一个全局变量来存储已经添加到页面上的聊天记录的ID
var addedMessageIds = new Set();

// 创建一个函数来处理发送消息的操作
function sendMessage() {
    var userInput = document.getElementById('userInput').value;
    var chatbox = document.getElementById('chatbox');
    var username = document.getElementById('username').innerText;  // 获取用户名

    // 如果用户没有输入任何内容，就不要发送消息
    if (userInput.trim() === '') {
        return;
    }

    // 创建一个新的消息块
    var userMessageBlock = document.createElement('div');
    userMessageBlock.className = "chat-msg user"; //添加了 user 类名

    // 创建一个新的元素来显示用户名，并将其添加到消息块中
    var userElement = document.createElement('div');
    userElement.className = "chat-msg-user";
    userElement.innerText = username;  // 使用获取的用户名

    // 创建一个新的元素来显示用户的消息文本，并将其添加到消息块中
    var userMessageElement = document.createElement('div');
    userMessageElement.className = "chat-msg-text";
    userMessageElement.innerText = userInput;

    // 创建一个新的div元素，将用户名和消息文本添加到这个div元素中
    var messageWrapper = document.createElement('div');
    messageWrapper.className = 'message-wrapper';
    messageWrapper.appendChild(userElement);
    messageWrapper.appendChild(userMessageElement);

    // 将新的div元素添加到消息块中
    userMessageBlock.appendChild(messageWrapper);

    // 将新的消息块添加到 chatbox 中
    chatbox.appendChild(userMessageBlock);

    // 将占位元素移动到聊天框的底部
    var spacer = document.getElementById('spacer');
    spacer.parentNode.removeChild(spacer);
    chatbox.appendChild(spacer);
    // 在最后滚动到占位元素的顶部
    spacer.scrollIntoView();

    var conversationHistory = Array.from(document.querySelectorAll('#chatbox .chat-msg')).map(msgBlock => {
        var role = msgBlock.querySelector('.chat-msg-user').textContent === 'You' ? 'user' : 'assistant';
        var content = msgBlock.querySelector('.chat-msg-text').textContent;
        return { role: role, content: content };
    });

    let myHeaders = new Headers({
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
    });
    // 更新助手状态为"对方正在输入…"
    document.getElementById('aiStatus').textContent = "对方正在输入…";
    // 禁用输入框和发送按钮
    document.getElementById('userInput').disabled = true;
    document.getElementById('send-btn').disabled = true;

    fetch('/chat/', {
        method: 'POST',
        headers: myHeaders,
        body: JSON.stringify({
            'message': userInput,
            'conversation_history': conversationHistory
        })
    })
    .then(response => {
    if (!response.ok && response.status !== 400) {
        throw response;
    }
    return response.json();
})
    .then(data => {
    // 检查返回的数据中是否有 'error' 属性
    if (data['error']) {
        // 如果有错误，将错误信息作为AI的消息添加到聊天界面
        // 使用当前时间戳作为消息ID
        var errorId = Date.now();
        addMessage("AI", data['error'], errorId);
    } else {
        // 如果没有错误，添加消息
        addMessage("AI", data['message'], data['message_id']);  // 使用返回的 message_id
        console.log(data);
    }
    // 在接收到回复后，更改助手状态并启用输入框
    document.getElementById('aiStatus').textContent = "人工智能家装助手";
    document.getElementById('userInput').disabled = false;
    document.getElementById('send-btn').disabled = false;
})
.catch(error => {
    // Check if the error object has a 'json' method
    if (typeof error.json === 'function') {
        error.json().then(errorData => {
            if (errorData && errorData['error']) {
                // 如果有错误，将错误信息作为AI的消息添加到聊天界面
                // 使用当前时间戳作为消息ID
                var errorId = Date.now();
                addMessage("AI", errorData['error'], errorId);
            } else {
                addMessage("AI", "An error occurred. Please try again later.");
            }
        }).catch(jsonError => {
            console.error('Error parsing JSON:', jsonError);
            addMessage("AI", "An error occurred. Please try again later.");
        });
    } else {
        // If the error object does not have a 'json' method, it is a network error
        console.error('Network error:', error);
        addMessage("AI", "A network error occurred. Please check your connection and try again.");
    }
    // 如果发生错误，也要启用输入框和发送按钮
    document.getElementById('aiStatus').textContent = "人工智能家装助手";
    document.getElementById('userInput').disabled = false;
    document.getElementById('send-btn').disabled = false;


    });

    document.getElementById('userInput').value = '';
    document.getElementById('userInput').style.height = '30px';  // 添加这行代码
}

// 检查一个字符串是否包含代码
function containsCode(str) {
    // 这是一个简单的检查，你可以根据需要添加更多的关键词
    const codeKeywords = ['function', 'var', 'let', 'if', 'for', 'while', 'do', 'switch', 'case', 'python', 'javascript', 'html'];
    for (let keyword of codeKeywords) {
        if (str.includes(keyword)) {
            return true;
        }
    }
    return false;
}

function addMessage(sender, message,id) {
    console.log("Adding message: ", sender, message)
    // 检查这个消息是否已经被添加过了
    if (addedMessageIds.has(id)) {
        return;
    }
    // 如果没有被添加过，将它的ID添加到全局变量中
    addedMessageIds.add(id);

    var chatbox = document.getElementById('chatbox');

    // 创建一个新的消息块
    var messageBlock = document.createElement('div');
    messageBlock.className = "chat-msg " + (sender === 'You' ? 'user' : 'ai');
    console.log("messageBlock: ", messageBlock);  // 打印 messageBlock 的值



    // 创建一个新的元素来显示用户名，并将其添加到消息块中
    var userElement = document.createElement('div');
    userElement.className = "chat-msg-user";

    message = message.replace(/</g, '&lt;').replace(/>/g, '&gt;');

    // 检查AI的消息中是否有被三个反引号包围的部分，如果有，使用 <pre> 标签
    if (sender === 'AI') {
        let regex = /```([^`]+)```/g;  // 正则表达式，匹配 ``` 之间的部分
        message = message.replace(regex, function(match, p1) {
            return '<pre>' + p1 + '</pre>';
        });
    }

    // 如果发送者是AI，我们将其名字设置为一个图片，否则为用户名
    if (sender === 'AI') {
        var imgElement = document.createElement('img');
        imgElement.src = '/static/images/AI.png';  // 换成你的图片路径
        imgElement.alt = 'AI';
        imgElement.className = 'ai-img';
        userElement.appendChild(imgElement);
    } else {
        userElement.innerText = sender;
    }
    // 检查消息中是否有链接
    var urlPattern = /(https?:\/\/[^\s]+)/g;
    message = message.replace(urlPattern, '<a href="$1" target="_blank">$1</a>');


    // 创建一个新的元素来显示用户的消息文本，并将其添加到消息块中
    var userMessageElement = document.createElement('div');
    userMessageElement.className = "chat-msg-text";
    userMessageElement.innerHTML = message;


    // 创建一个新的div元素，将用户名和消息文本添加到这个div元素中
    var messageWrapper = document.createElement('div');
    messageWrapper.className = 'message-wrapper';
    messageWrapper.appendChild(userElement);
    messageWrapper.appendChild(userMessageElement);

    // 将新的div元素添加到消息块中
    messageBlock.appendChild(messageWrapper);

    // 将新的消息块添加到 chatbox 中
    chatbox.appendChild(messageBlock);
    // 将占位元素移动到聊天框的底部
    var spacer = document.getElementById('spacer');
    spacer.parentNode.removeChild(spacer);
    chatbox.appendChild(spacer);
    // 在最后滚动到占位元素的顶部
    spacer.scrollIntoView();
    console.log("chatbox.innerHTML: ", chatbox.innerHTML);  // 打印 chatbox.innerHTML 的值
// 滚动到 chatbox 的最底部
    chatbox.scrollTop = chatbox.scrollHeight;

}

// 添加输入框键盘按下事件监听器
document.getElementById('userInput').addEventListener('keydown', function(event) {
    if (event.keyCode === 13 && !event.shiftKey) { // 如果是按下的 Enter 键（keyCode 为 13），且没有按下 Shift 键
        event.preventDefault();
        sendMessage(); // 在按下 Enter 键时调用 sendMessage 函数
    }
});

// 添加 Send 按钮点击事件监听器
document.getElementById('send-btn').addEventListener('click', function(event) {
    event.preventDefault();
    sendMessage(); // 在点击 Send 按钮时调用 sendMessage 函数
});

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 当 DOM 完全加载后执行
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('userInput').addEventListener('input', function() {
        var maxHeight = parseInt(window.getComputedStyle(this).getPropertyValue('max-height'));

        this.style.height = '0px';

        if (this.scrollHeight > maxHeight) {
            this.style.overflowY = 'auto';
            this.style.height = maxHeight + 'px';
        } else {
            this.style.height = Math.max(this.scrollHeight, this.clientHeight) + 'px';
            this.style.overflowY = 'hidden';
        }
    });

    // 页面加载完成后，发送一个 GET 请求获取聊天记录
    fetch('/chat/history/', {  // 将这里的 URL 改为 '/chat/history/'
        method: 'GET',
    })
    .then(response => response.json())
    .then(data => {
        var username = document.getElementById('username').innerText;  // 获取用户名
        data.chat_history.forEach((msg, index) => {
            // 使用返回的 message_id
            addMessage(msg.role === 'user' ? username : 'AI', msg.content, msg.message_id);  // 使用获取的用户名
        });
    });
});
