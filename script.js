function send(){
    let msg = document.getElementById("msg").value;

    fetch("/ai_chat", {
        method:"POST",
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({message: msg})
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("reply").innerText = data.reply;
    });
}