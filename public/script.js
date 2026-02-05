
// Matrix Rain Effect
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

const katakana = 'アァカサタナハマヤャラワガザダバパイィキシチニヒミリヰギジヂビピウゥクスツヌフムユュルグズブヅプエェケセテネヘメレヱゲゼデベペオォコソトノホモヨョロヲゴゾドボポヴッン';
const latin = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
const nums = '0123456789';
const alphabet = katakana + latin + nums;

const fontSize = 16;
const columns = canvas.width / fontSize;

const rainDrops = [];
for (let x = 0; x < columns; x++) {
    rainDrops[x] = 1;
}

const draw = () => {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = '#0F0';
    ctx.font = fontSize + 'px monospace';

    for (let i = 0; i < rainDrops.length; i++) {
        const text = alphabet.charAt(Math.floor(Math.random() * alphabet.length));
        ctx.fillText(text, i * fontSize, rainDrops[i] * fontSize);

        if (rainDrops[i] * fontSize > canvas.height && Math.random() > 0.975) {
            rainDrops[i] = 0;
        }
        rainDrops[i]++;
    }
};

window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
});

setInterval(draw, 30);

// Terminal Typing Effect
const termContent = [
    "> Initializing GLTCH core...",
    "> Loading personality modules...",
    "> Connecting to neural interface...",
    "> ACCESS GRANTED.",
    "> Welcome, Operator."
];

const termEl = document.getElementById('term-content');
let lineIndex = 0;
let charIndex = 0;

function typeLine() {
    if (lineIndex < termContent.length) {
        if (charIndex < termContent[lineIndex].length) {
            termEl.innerHTML += termContent[lineIndex].charAt(charIndex);
            charIndex++;
            setTimeout(typeLine, 50);
        } else {
            termEl.innerHTML += "<br>";
            lineIndex++;
            charIndex = 0;
            setTimeout(typeLine, 300);
        }
    }
}

setTimeout(typeLine, 1000);
