const fs = require('fs');
const fabric = require('fabric').fabric;

const sleep = (delay) => new Promise((resolve) => setTimeout(resolve, delay));

// Read element properties from JSON file
const jsonstr = fs.readFileSync(__dirname + '/gpt4_response.json', 'utf-8');
const jsonData = JSON.parse(jsonstr);

const canvas = new fabric.Canvas('canvas', {
    width: 1024,
    height: 1024
});


// Function to create canvas and render elements
async function createCanvas() {
    // Read all URLs from the text file
    const urls = fs.readFileSync(__dirname + '/mid_journey_images.txt', 'utf-8').split('\n');

    for (let i = 0; i < 4; i++) {
        const url = urls[i];
        console.log(`Processing image ${i+1}: ${url}`);

        await new Promise((resolve, reject) => {
            // load image
            fabric.Image.fromURL(url, function (img) {
                img.scaleToWidth(1024)
                img.scaleToHeight(1024)

                // Create text elements dynamically
                const textElements = jsonData.Text_component_details_LIST.map(detail => {
                    const component = Object.keys(detail)[0];
                    const prop = detail[component];
                    return createDynamicText(prop.text, 512, parseInt(prop['location at y-axis']), 500, 50, prop.font_name, prop.font_weight, prop.font_colour, parseInt(prop.font_size), prop.font_style);
                });
                
                // Add image and text elements to a group
                const group = new fabric.Group([img, ...textElements], {});
                canvas.add(group);
                
                canvas.renderAll();

                // Save JSON
                const json = JSON.stringify(canvas);
                // console.log(json);

                // Save PNG
                const out = fs.createWriteStream(__dirname + `/output${i+1}.png`);
                const stream = canvas.createPNGStream();
                stream.pipe(out);
                out.on('finish', () =>  {
                    console.log(`PNG saved successfully as output${i+1}.png.`);
                    resolve();
                });
            }, function (err) {
                console.log('Error loading image.');
                console.log(err);
                reject(err);
            });

            // Set the size of the canvas
            canvas.setDimensions({ width: 1024, height: 1024 });
        });
    }
};

// Function to create text with dynamic font size and centered horizontally
function createDynamicText(text, left, top, width, height, fontFamily, fontWeight, fill, fontSize, fontStyle = 'normal') {
    // TODO: 
    // Textbox or Text or IText

    // console.log("INSIDE CREATE DYNAMIC TEXT")
    const textbox = new fabric.Text(text, {
        left: left,
        top: top,
        // width: width,
        // height: height,
        fontSize: fontSize,
        fontFamily: fontFamily,
        fontWeight: fontWeight,
        fill: fill,
        fontStyle: fontStyle,
        textAlign: 'center',
    });

    // Calculate the actual width of the text
    const textWidth = getTextWidth(text, fontFamily, fontWeight, fontSize);

    // Adjust the left position to center the text horizontally
    textbox.set({
        // fontSize: fontSize,
        left: left - (textWidth / 2)
    });

    return textbox;
}

function getTextWidth(text, fontFamily, fontWeight, fontSize) {
    // const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    ctx.font = fontWeight + " " + fontSize + "px " + fontFamily;
    const width = ctx.measureText(text).width;
    return width;
}

function getTextHeight(text, fontFamily, fontWeight, fontSize) {
    // const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    ctx.font = fontWeight + " " + fontSize + "px " + fontFamily;
    // Returns the total line height
    return ctx.measureText('M').actualBoundingBoxAscent + ctx.measureText('M').actualBoundingBoxDescent;
}

function findFontSize(text, fontFamily, fontWeight, width, height) {
    const minSize = 1;
    const maxSize = 100;
    const fontSize = 50; // Default font size
    while (maxSize - minSize > 1) {
        fontSize = (minSize + maxSize) / 2; // Calculate the middle font size
        if (getTextWidth(text, fontFamily, fontWeight, fontSize) > width || getTextHeight(text, fontFamily, fontWeight, fontSize) > height) {
            maxSize = fontSize; // Adjust the max size
        } else {
            minSize = fontSize; // Adjust the min size
        }
    }
    return minSize; // Return the final font size
}




createCanvas();