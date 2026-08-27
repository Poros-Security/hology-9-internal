<?php

$log = isset($_GET['log']) ? $_GET['log'] : 'logs/entry1';

?>
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TRUE LAB | LOG VIEWER</title>

    <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">

    <style>
        @font-face {
            font-family: 'Determination Sans';
            src: url('https://fonts.cdnfonts.com/s/72898/DTM-Sans.woff') format('woff');
        }

        :root {
            --ut-yellow: #ffff00;
            --ut-cyan: #66ccff;
            --ut-white: #ffffff;
            --ut-black: #000000;
            --crt-flicker: 0.06;
        }

        * {
            box-sizing: border-box;
        }

        html,
        body {
            height: 100%;
            margin: 0;
        }

        body {
            background-color: black;
            color: white;
            font-family: 'Determination Sans', 'Press Start 2P', monospace;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            position: relative;
            overflow-x: hidden;
            background-image:
                radial-gradient(circle at center, #10151a 0%, #000000 70%);
            image-rendering: pixelated;
        }

        .particles {
            position: fixed;
            inset: 0;
            pointer-events: none;
            overflow: hidden;
            z-index: 0;
        }

        .particle {
            position: absolute;
            width: 3px;
            height: 3px;
            background: var(--ut-cyan);
            box-shadow: 0 0 4px var(--ut-cyan);
            opacity: 0.5;
            animation: floatUp linear infinite;
        }

        @keyframes floatUp {
            0% {
                transform: translateY(110vh) translateX(0);
                opacity: 0;
            }

            10% {
                opacity: 0.7;
            }

            90% {
                opacity: 0.5;
            }

            100% {
                transform: translateY(-10vh) translateX(20px);
                opacity: 0;
            }
        }

        .scanlines {
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 3;
            background: repeating-linear-gradient(to bottom,
                    rgba(255, 255, 255, 0.035) 0px,
                    rgba(255, 255, 255, 0.035) 1px,
                    transparent 2px,
                    transparent 3px);
            mix-blend-mode: overlay;
        }

        .flicker-overlay {
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 4;
            background: black;
            opacity: 0;
            animation: labFlicker 6s infinite steps(1);
        }

        @keyframes labFlicker {

            0%,
            92%,
            100% {
                opacity: 0;
            }

            93% {
                opacity: var(--crt-flicker);
            }

            94% {
                opacity: 0;
            }

            95% {
                opacity: calc(var(--crt-flicker) * 2);
            }

            96% {
                opacity: 0;
            }
        }

        .sprite {
            width: 110px;
            height: 110px;
            background: repeating-linear-gradient(45deg,
                    #222,
                    #222 10px,
                    #000 10px,
                    #000 20px);
            border: 4px solid var(--ut-white);
            margin-bottom: 24px;
            image-rendering: pixelated;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            color: var(--ut-cyan);
            text-align: center;
            line-height: 1.4;
            position: relative;
            z-index: 2;
            animation: monitorGlow 3s ease-in-out infinite;
            font-family: 'Press Start 2P', monospace;
        }

        @keyframes monitorGlow {

            0%,
            100% {
                box-shadow: 0 0 6px rgba(102, 204, 255, 0.3);
            }

            50% {
                box-shadow: 0 0 18px rgba(102, 204, 255, 0.7);
            }
        }

        .dialogue-box {
            width: 80%;
            max-width: 800px;
            min-height: 200px;
            background-color: black;
            border: 6px solid white;
            border-radius: 2px;
            padding: 28px 36px;
            position: relative;
            box-shadow:
                inset 0 0 0 4px black,
                0 0 0 4px white,
                0 0 24px rgba(255, 255, 255, 0.08);
            image-rendering: pixelated;
            z-index: 2;
            animation: boxBreathe 4s ease-in-out infinite;
            display: flex;
            align-items: flex-start;
            gap: 16px;
        }

        @keyframes boxBreathe {

            0%,
            100% {
                box-shadow: inset 0 0 0 4px black, 0 0 0 4px white, 0 0 16px rgba(255, 255, 255, 0.06);
            }

            50% {
                box-shadow: inset 0 0 0 4px black, 0 0 0 4px white, 0 0 28px rgba(102, 204, 255, 0.18);
            }
        }

        .asterisk {
            font-size: 32px;
            line-height: 1.65;
            color: var(--ut-white);
            animation: asteriskBlink 1.2s steps(1) infinite;
            flex-shrink: 0;
        }

        @keyframes asteriskBlink {

            0%,
            60% {
                opacity: 1;
            }

            61%,
            100% {
                opacity: 0.2;
            }
        }

        .content {
            font-size: 26px;
            line-height: 1.65;
            letter-spacing: 0.5px;
            word-spacing: 2px;
            margin-left: 0;
            /* RESET MARGIN */
            max-width: 680px;
            white-space: pre-wrap;
            word-wrap: break-word;
            overflow-wrap: break-word;
            hyphens: auto;
            text-align: left;
            text-shadow: 2px 2px 0 #000;
            max-height: 55vh;
            overflow-y: auto;
            padding-right: 8px;
        }

        .content.typing-cursor::after {
            content: "_";
            animation: cursorBlink 0.6s steps(1) infinite;
        }

        @keyframes cursorBlink {

            0%,
            50% {
                opacity: 1;
            }

            51%,
            100% {
                opacity: 0;
            }
        }

        .content::-webkit-scrollbar {
            width: 8px;
        }

        .content::-webkit-scrollbar-track {
            background: #000;
        }

        .content::-webkit-scrollbar-thumb {
            background: var(--ut-cyan);
            border: 2px solid #000;
        }

        .title-caption {
            font-family: 'Press Start 2P', monospace;
            font-size: 12px;
            color: var(--ut-cyan);
            letter-spacing: 2px;
            margin-bottom: 18px;
            z-index: 2;
            text-shadow: 0 0 6px rgba(102, 204, 255, 0.6);
        }

        .nav {
            margin-top: 40px;
            text-align: center;
            font-size: 22px;
            display: flex;
            gap: 40px;
            justify-content: space-around;
            z-index: 2;
            position: relative;
        }

        a {
            color: var(--ut-yellow);
            text-decoration: none;
            cursor: pointer;
            padding: 6px 14px;
            border: 2px solid transparent;
            transition: color 0.15s ease, border-color 0.15s ease, transform 0.1s ease;
        }

        a::before {
            content: "· ";
            display: inline-block;
            animation: heartPulse 1.5s ease-in-out infinite;
        }

        @keyframes heartPulse {

            0%,
            100% {
                transform: scale(1);
            }

            50% {
                transform: scale(1.2);
            }
        }

        a:hover {
            color: var(--ut-white);
            border-color: var(--ut-white);
            transform: translateY(-2px);
        }

        audio {
            display: none;
        }

        @media (max-width: 600px) {
            .content {
                font-size: 19px;
                line-height: 1.55;
                margin-left: 14px;
                max-width: 100%;
                max-height: 45vh;
            }

            .dialogue-box {
                padding: 20px;
            }

            .asterisk {
                left: 18px;
                top: 18px;
                font-size: 24px;
            }
        }
    </style>
</head>

<body>
    <audio id="bgm" autoplay loop>
        <source src="assets/undertale-soundtrack.mp3" type="audio/mpeg">
    </audio>

    <div class="scanlines"></div>
    <div class="flicker-overlay"></div>
    <div class="particles" id="particles"></div>

    <div class="title-caption">♪ ONCE UPON A TIME... ♪</div>

    <div class="sprite" style="background: none; border: none; width: 320px; height: auto; animation: none;">
        <img src="https://media1.tenor.com/m/6JU0Nsz3ZTcAAAAC/dog-sleeping-napping.gif" style="width: 100%; border: 4px solid white; image-rendering: pixelated; border-radius: 4px;" alt="Annoying Dog Sleeping">
    </div>

    <div class="dialogue-box">
        <div class="asterisk">*</div>
        <div class="content" id="dialogueContent"><span id="typewriterText"><?php
                                                                            try {
                                                                                include($log . ".php");
                                                                            } catch (Exception $e) {
                                                                                echo "ENTRY CORRUPTED.";
                                                                            }
                                                                            ?></span>
        </div>
    </div>

    <div class="nav" style="width: 80%; max-width: 800px;">
        <a href="?log=logs/entry1">LOG 1</a>
        <a href="?log=logs/entry2">LOG 2</a>
    </div>

    <script>
        const bgm = document.getElementById('bgm');

        const savedTime = sessionStorage.getItem('bgmTime');

        bgm.addEventListener('loadedmetadata', function() {
            if (savedTime !== null) {
                try {
                    bgm.currentTime = parseFloat(savedTime);
                } catch (e) {}
            }
        });

        window.addEventListener('beforeunload', function() {
            sessionStorage.setItem('bgmTime', bgm.currentTime);
        });

        document.body.addEventListener('click', function() {
            bgm.play().catch(e => console.log("Audio autoplay di-block:", e));
        }, {
            once: true
        });

        (function() {
            const container = document.getElementById('particles');
            const total = 30;
            for (let i = 0; i < total; i++) {
                const p = document.createElement('div');
                p.className = 'particle';
                const left = Math.random() * 100;
                const duration = 6 + Math.random() * 10;
                const delay = Math.random() * 10;
                const size = 2 + Math.random() * 3;
                p.style.left = left + 'vw';
                p.style.width = size + 'px';
                p.style.height = size + 'px';
                p.style.animationDuration = duration + 's';
                p.style.animationDelay = delay + 's';
                container.appendChild(p);
            }
        })();

        (function() {
            const el = document.getElementById('typewriterText');
            const wrapper = document.getElementById('dialogueContent');
            const fullText = el.textContent;
            el.textContent = '';
            wrapper.classList.add('typing-cursor');

            const speed = 28;
            let i = 0;

            function typeNext() {
                if (i < fullText.length) {
                    el.textContent += fullText.charAt(i);
                    i++;
                    setTimeout(typeNext, speed);
                } else {
                    wrapper.classList.remove('typing-cursor');
                }
            }

            typeNext();
        })();
    </script>
</body>

</html>