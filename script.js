function convertToFloat(time) {
    const [hours, minutes] = time.split(":").map(Number);
    return hours + minutes / 60;
}

function formatTime(date) {
    return date.toLocaleString("en-US", {
        hourCycle: "h24",
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    });
}

function calculateDropTimes(dropTime, chgSpawnTime, cycles) {
    const currentTime = new Date();
    const nextPickUpTime = new Date(
        currentTime.getTime() + chgSpawnTime * 60 * 60 * 1000
    );
    const firstDropTime = new Date(
        nextPickUpTime.getTime() + dropTime * 60 * 60 * 1000
    );

    const dropTimes = Array.from(
        { length: cycles },
        (_, i) => new Date(firstDropTime.getTime() + i * dropTime * 60 * 60 * 1000)
    );

    return {
        nextPickUpTime,
        dropTimes,
    };
}

class SpaceDrop {
    constructor({
        rarity,
        size,
        spaceId,
        cycles,
        dropTime,
        chgSpawnTime,
        identity,
        nextPickUpTime,
        dropTimes,
    }) {
        this.rarity = rarity;
        this.size = size;
        this.spaceId = spaceId;
        this.cycles = cycles;
        this.dropTime = dropTime;
        this.chgSpawnTime = chgSpawnTime;
        this.identity = identity || `${spaceId}-${Date.now()}`;
        this.nextPickUpTime = nextPickUpTime
            ? new Date(nextPickUpTime)
            : calculateDropTimes(dropTime, chgSpawnTime, cycles).nextPickUpTime;
        this.dropTimes = dropTimes
            ? dropTimes.map((time) => new Date(time))
            : calculateDropTimes(dropTime, chgSpawnTime, cycles).dropTimes;
        this.renderResultBox();
        this.startCountdown();
    }

    renderResultBox() {
        const resultDiv = document.getElementById("results");

        const resultBox = document.createElement("div");
        resultBox.classList.add("results-box");
        resultBox.dataset.identity = this.identity;

        const resultCard = document.createElement("div");
        resultCard.classList.add("result-card");
        resultCard.innerHTML = `
        <p><strong>Rarity:</strong> ${this.rarity}</p>
        <p><strong>Size:</strong> ${this.size}</p>
        <p><strong>Space ID:</strong> ${this.spaceId}</p>
        <p><strong>Cycles:</strong> ${this.cycles}</p>
        <p><strong>Spawn Interval:</strong> ${this.dropTime}</p>
        <p><strong>Next Pick-up Time:</strong> <span id="nextPickUp-${this.identity}"></span></p>
      `;
        resultCard.onclick = () => {
            const details = resultBox.querySelector(".details");
            details.style.display =
                details.style.display === "none" ? "block" : "none";
        };

        const details = document.createElement("div");
        details.classList.add("details");
        details.style.display = "none";
        details.innerHTML = this.generateResultHtml();

        resultBox.appendChild(resultCard);
        resultBox.appendChild(details);
        resultDiv.appendChild(resultBox);
    }

    generateResultHtml() {
        const dropTimesHtml = this.dropTimes
            .map(
                (time, index) =>
                    `<tr><td>Drop ${index + 1}</td><td>${formatTime(
                        time
                    )}</td></tr>`
            )
            .join("");

        return `
        <button class="delete-button" onclick="deleteResultBox('${this.identity
            }')">X</button>
        <table>
          <thead>
            <tr><th>Loops</th><th>Date & Time</th></tr>
          </thead>
          <tbody>
            <tr><td>Next Pick Up</td><td>${formatTime(
                this.nextPickUpTime
            )}</td></tr>
            ${dropTimesHtml}
          </tbody>
        </table>
      `;
    }

    saveToLocalStorage() {
        const results =
            JSON.parse(localStorage.getItem("spaceResults")) || [];
        const existingIndex = results.findIndex(
            (result) => result.identity === this.identity
        );

        const resultData = {
            rarity: this.rarity,
            size: this.size,
            spaceId: this.spaceId,
            cycles: this.cycles,
            dropTime: this.dropTime,
            chgSpawnTime: this.chgSpawnTime,
            identity: this.identity,
            nextPickUpTime: this.nextPickUpTime.toISOString(),
            dropTimes: this.dropTimes.map((time) => time.toISOString()),
        };

        if (existingIndex !== -1) {
            results[existingIndex] = resultData;
        } else {
            results.push(resultData);
        }

        localStorage.setItem("spaceResults", JSON.stringify(results));
    }

    startCountdown() {
        const countdownElement = document.getElementById(
            `nextPickUp-${this.identity}`
        );
        const updateCountdown = () => {
            const now = new Date();
            const remainingTime = this.nextPickUpTime.getTime() - now.getTime();

            if (remainingTime <= 0) {
                countdownElement.textContent = "Drop Now !!!";
                clearInterval(this.countdownInterval);
                return;
            }

            const hoursLeft = Math.floor(
                (remainingTime / (1000 * 60 * 60)) % 24
            );
            const minutesLeft = Math.floor((remainingTime / (1000 * 60)) % 60);
            const secondsLeft = Math.floor((remainingTime / 1000) % 60);

            countdownElement.textContent = `${hoursLeft
                .toString()
                .padStart(2, "0")}:${minutesLeft
                    .toString()
                    .padStart(2, "0")}:${secondsLeft.toString().padStart(2, "0")}`;
        };

        updateCountdown();
        this.countdownInterval = setInterval(updateCountdown, 1000);
    }
}

function createTimeCal() {
    const rarity = document.getElementById("rarity").value;
    const size = document.getElementById("size").value;
    const spaceId = document.getElementById("spaceId").value;
    const cycles = parseInt(document.getElementById("cycles").value);
    const dropTime = parseInt(document.getElementById("dropTime").value);
    const chgSpawnTime = convertToFloat(document.getElementById("chgSpawnTime").value);

    const spaceDrop = new SpaceDrop({
        rarity,
        size,
        spaceId,
        cycles,
        dropTime,
        chgSpawnTime,
    });
    spaceDrop.saveToLocalStorage();
}

function deleteResultBox(identity) {
    const resultBox = document.querySelector(
        `[data-identity='${identity}']`
    );
    if (resultBox) resultBox.remove();

    let results = JSON.parse(localStorage.getItem("spaceResults"));
    results = results.filter((result) => result.identity !== identity);
    localStorage.setItem("spaceResults", JSON.stringify(results));
}

function loadStoredResults() {
    const results = JSON.parse(localStorage.getItem("spaceResults")) || [];
    results.forEach((result) => new SpaceDrop(result));
}

window.onload = loadStoredResults;

