const textarea = document.querySelector('textarea');

textarea.addEventListener('input', function() {
    const newLineCount = (this.value.match(/\n/g) || []).length + 1;
    const lineHeight = parseInt(getComputedStyle(this).lineHeight);
    const maxHeight = lineHeight * 5;
    const height = Math.min(maxHeight, lineHeight * newLineCount);
    this.style.height = height + 'px';
});

textarea.addEventListener('keydown', function(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        const lineHeight = parseInt(getComputedStyle(this).lineHeight);
        const maxHeight = lineHeight * 5;
        const height = Math.min(maxHeight, lineHeight * (this.value.match(/\n/g) || []).length);
        this.style.height = height + 'px';
    }
});

textarea.addEventListener('keydown', function(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        submitPrompt();
    }
});



var model = "{{ config['OPENAI_MODEL'] }}";
console.log("Mode: " + model);
async function getResponse(prompt) {
    const response = await openai.Completion.create({
        model: model,
        prompt: prompt
    });
    const text = response.choices[0].text;
    const conversation_history = sessionStorage.getItem("conversation_history") || [];
    const new_conversation_history = [...conversation_history, {
        prompt,
        text
    }];
    sessionStorage.setItem("conversation_history", JSON.stringify(new_conversation_history));
    return text;
}

const overlay = document.querySelector('.hourglass-overlay');
const hourglass = document.querySelector('.hourglass');

async function submitPrompt() {
    // Disable the send button and enable the stop button
    document.querySelector('.send').disabled = true;
    document.querySelector('.send').style.display = 'none';
    document.querySelector('.stop').disabled = false;
    document.querySelector('.stop').style.display = 'inline-block';

    // Get the prompt text from the textarea
    const prompt = document.getElementById("prompt").value;
    console.log("prompt: " + prompt);

    // Create a new div to display the prompt with "Me:" prefix
    var promptDiv = document.createElement("div");
    promptDiv.innerHTML = "<table class='conversation-table'><tr><td class='conversation-table__column1'><b>Me:</b></td><td class='conversation-table__column2'>" + prompt.replace(/\n/g, "<br>") + "</td></tr></table>";
    // Clear the prompt textarea
    document.getElementById("prompt").value = "";
    promptDiv.classList.add("conversation-history");

    // Add the prompt to the page
    document.getElementById("conversation-history").appendChild(promptDiv);

    // Show the hourglass overlay
    overlay.style.display = 'block';
    // Show the hourglass
    hourglass.style.display = 'block';

    // Create a new AbortController instance
    const controller = new AbortController();

    // Set a timeout to automatically cancel the request after 10 seconds
    const timeoutId = setTimeout(() => {
        controller.abort();
    }, 10000);

    // Submit the prompt to the completion endpoint
    xhr = new XMLHttpRequest();
    xhr.open("POST", "/completion", true);
    xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    // Set up the onreadystatechange function to handle the response
    xhr.onreadystatechange = function() {
        // If the request is complete and successful
        if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
            // Hide the hourglass
            hourglass.style.display = 'none';
            // Hide the hourglass overlay
            overlay.style.display = 'none';

            // Enable the send button and disable the stop button
            document.querySelector('.send').disabled = false;
            document.querySelector('.send').style.display = 'inline-block';
            document.querySelector('.stop').disabled = true;
            document.querySelector('.stop').style.display = 'none';

            // Clear the timeout
            //clearTimeout(timeoutId);

            if (xhr.responseText) {
                console.log("xhr.responseText: " + xhr.responseText)
                const responseObj = JSON.parse(xhr.responseText);
                var response = responseObj.response.trim();
                console.log("response: " + response);
                // var response = JSON.parse(xhr.responseText);
                if (response.error && response.success === false) {
                    // display error message
                    alert(response.error);
                } else if (response.message && response.success === true) {
                    // display success message
                    alert(response.message);
                } else {
                    // Get the HTML string from the response
                    // console.log("xhr.responseText: " + response.message);
                    // const trimmedResponseText = response.message;
                    // const c_response = JSON.parse(trimmedResponseText);
                    // response = c_response.response.trim();                    
                    response = response.slice(3, -3);
                    console.log("response: " + response.replace(/<br>/g, '\n'));

                    // Create a new div to display the bot's response with "Bot:" prefix
                    var responseDiv = document.createElement("div");
                    responseDiv.innerHTML = "<table><tr><td class='conversation-table__column1'><b>Bot:</b></td><td>" + response.replace(/\n/g, "<br>") + "</td></tr></table>";
                    responseDiv.classList.add("conversation-history");

                    // Add the response to the page
                    document.getElementById("conversation-history").appendChild(responseDiv);
                }
            } else {
                // no response
                console.log("No response from the server");
            }
        }
    };

    // Set the signal of the request to the abort controller's signal
    // xhr.signal = controller.signal;

    xhr.send("prompt=" + encodeURIComponent(prompt));
}

// hljs.initHighlightingOnLoad();

function stopCompletion() {
    // Abort the current request
    xhr.abort();

    // Enable the send button and disable the stop button
    document.querySelector('.send').disabled = false;
    document.querySelector('.send').style.display = 'inline-block';
    document.querySelector('.stop').disabled = true;
    document.querySelector('.stop').style.display = 'none';

    // Hide the hourglass
    hourglass.style.display = 'none';
    // Hide the hourglass overlay
    overlay.style.display = 'none';
}