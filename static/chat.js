function updateConversation(conversationHistory) {
    var promptDiv = document.getElementById("prompt");
    var responseDiv = document.getElementById("response");
    promptDiv.innerHTML = "";
    responseDiv.innerHTML = "";

    for (var i = 0; i < conversationHistory.length; i++) {
        var row = document.createElement("tr");
        var meCell = document.createElement("td");
        meCell.innerText = "Me";
        var promptCell = document.createElement("td");
        promptCell.innerText = conversationHistory[i][0];
        var botCell = document.createElement("td");
        botCell.innerText = "Bot";
        var responseCell = document.createElement("td");
        responseCell.innerText = conversationHistory[i][1];

        row.appendChild(meCell);
        row.appendChild(promptCell);
        promptDiv.appendChild(row);

        row = document.createElement("tr");
        row.appendChild(botCell);
        row.appendChild(responseCell);
        responseDiv.appendChild(row);
    }
}