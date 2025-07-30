document.addEventListener('DOMContentLoaded', function() {
  const messageInput = document.getElementById('messageInput');
  const sendButton = document.getElementById('sendButton');
  const messageArea = document.getElementById('messageArea');
  const finishButton = document.getElementById('finishButton');
  const mask = document.getElementById('mask');
  const modal = document.getElementById('modal');

  // チャット相手の user_name をクエリから取得
  const params = new URLSearchParams(window.location.search);
  const toUserName = params.get('user_name'); // ★ココだけ

  let myName = "";

  // 自分の名前をAPIから取得
  fetch('/get_me')
    .then(res => res.json())
    .then(me => {
      myName = me.user_name;
      // 相手名を画面に表示
      document.getElementById('userName').textContent = toUserName || "不明なユーザー";

      // チャット履歴を取得して表示（相手名を利用）
      if (toUserName) {
        fetch('/get_chat_history?to_user=' + encodeURIComponent(toUserName))
          .then(res => res.json())
          .then(history => {
            messageArea.innerHTML = ""; // 一度クリア
            history.forEach(m => {
              if (m.from_user === myName) {
                addUserMessage(m.message);
              } else {
                addBotMessage(m.message);
              }
            });
            scrollToBottom();
          });
      }
    });

  sendButton.addEventListener('click', sendMessage);
  messageInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') sendMessage();
  });

  function sendMessage() {
    const message = messageInput.value.trim();
    if (message === '' || !toUserName) return;

    // サーバーにPOST
    fetch('/send_message', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: new URLSearchParams({
        to_user: toUserName,
        message: message
      })
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        addUserMessage(message);  // 表示
        messageInput.value = '';
        scrollToBottom();
      } else {
        alert('メッセージ送信失敗: ' + (data.error || ''));
      }
    });
  }

  function addUserMessage(text) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', 'user-message');
    messageElement.textContent = text;
    messageArea.appendChild(messageElement);
    scrollToBottom();
  }
  function addBotMessage(text) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', 'bot-message');
    messageElement.textContent = text;
    messageArea.appendChild(messageElement);
    scrollToBottom();
  }
  function scrollToBottom() {
    messageArea.scrollTop = messageArea.scrollHeight;
  }

  finishButton.addEventListener('click', () => {
    mask.classList.remove('hidden');
    modal.classList.remove('hidden');
    setTimeout(() => { window.location.href = "/search"; }, 2000);
  });

  mask.addEventListener('click', () => {
    mask.classList.add('hidden');
    modal.classList.add('hidden');
  });
});
