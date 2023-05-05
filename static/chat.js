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

let chat_session_id = null; // Change this line to declare a variable instead of a constant

// Fetch a new session ID from the server
async function fetchNewSession() {
    try {
        const response = await fetch('/new_session', { credentials: 'same-origin' });
        const data = await response.json();
        // Store the session ID in the browser's session storage
        sessionStorage.setItem('session_id', data.session_id);
        // Update the chat_session_id variable
        chat_session_id = data.session_id;
        // console.log("Session ID0:", chat_session_id);
    } catch (error) {
        console.error("Failed to fetch new session ID:", error);
    }
}


// Initialize the chat session
async function initChatSession() {
    // Get the chat session ID from the server
    const response = await fetch('/chat_session');
    const data = await response.json();
    chat_session_id = data.session_id; // Assign the session ID to the variable instead of a constant
    // console.log("Session ID1:", chat_session_id);
}

// Call initChatSession to initialize the chat session
initChatSession();

async function getResponse(prompt) {
    const response = await openai.ChatCompletion.create({
        model: model,
        prompt: prompt
    });
    const text = response['choices'][0]['message']['content'].strip()
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
    // console.log("prompt: " + prompt);

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

    // console.log("Session ID2:", chat_session_id);

    // Submit the prompt to the completion endpoint
    xhr = new XMLHttpRequest();
    // console.log(xhr);
    xhr.open("POST", "/completion", true);
    xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    const temperature = 0.7;
    const max_tokens = 50;

    xhr.send("prompt=" + encodeURIComponent(prompt) + "&session_id=" + encodeURIComponent(chat_session_id) + "&temperature=" + temperature + "&max_tokens=" + max_tokens);
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
            // console.log("responseText: " + xhr.responseText);
            if (xhr.responseText) {
                const responseObj = JSON.parse(xhr.responseText);

                if (responseObj.error && responseObj.success === false) {
                    // display error message
                    alert(responseObj.error);
                } else if (responseObj.message && responseObj.success === true) {
                    // display success message
                    alert(responseObj.message);
                } else {
                    var response = responseObj.message;
                    if (response) {
                        response = response.trim();
                    }
                    // console.log("response: " + response);
                    if (responseObj.error && responseObj.success === false) {
                        // display error message
                        alert(responseObj.error);
                    } else if (responseObj.message && responseObj.success === true) {
                        // display success message
                        alert(responseObj.message);
                    } else {
                        // Get the HTML string from the response
                        // console.log("xhr.responseText: " + response);
                        if (response) {
                            response = response.slice(3, -3);
                        }
                        // console.log("response: " + response.replace(/<br>/g, '\n'));

                        // Create a new div to display the bot's response with "Bot:" prefix
                        var responseDiv = document.createElement("div");
                        responseDiv.innerHTML = "<table><tr><td class='conversation-table__column1'><b>Bot:</b></td><td>" + response.replace(/\n/g, "<br>") + "</td></tr></table>";
                        responseDiv.classList.add("conversation-history");

                        // Add the response to the page
                        document.getElementById("conversation-history").appendChild(responseDiv);
                    }
                }
            } else {
                // no response
                console.log("No response from the server");
            }
        }
    };

    // Set the signal of the request to the abort controller's signal
    // xhr.signal = controller.signal;

}

// hljs.initHighlightingOnLoad();

function stopCompletion() {
    // Abort the current request
    if (xhr.readyState === XMLHttpRequest.OPENED) {
        xhr.abort();
    }

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