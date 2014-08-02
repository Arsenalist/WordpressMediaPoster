#!/bin/bash
capturejs --javascript-file ./sleep.js --uri $1 --output test.png
convert -trim test.png test2.png
./imgur test2.png

