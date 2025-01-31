const fs = require('fs');
const {Readability} = require('@mozilla/readability');
const JSDOM = require('jsdom').JSDOM;

// serializer
function getClass(elem) {
    return elem.constructor.name;
}

function getTextInner(elem) {
    if (elem.children?.length > 0) {
        return [...elem.children].map(getTextInner).join('\n\n');
    } else if (elem.childNodes?.length > 0) {
        return [...elem.childNodes].map(getTextInner).join('\n\n');
    }
    return elem.textContent;
}

function compressNewlines(text) {
    text = text.replace(/\n\s*\n/g, '\n\n');
    text = text.replace(/\n\n\s+/g, '\n\n');
    text = text.replace(/\s+\n\n/g, '\n\n');
    return text.trim();
}

function getText(elem) {
    return compressNewlines(getTextInner(elem));
}

// article getter
async function extractText(url, serializer) {
    serializer = serializer ?? (elem => elem.innerHTML);

    // get html local/url
    let html;
    if (fs.existsSync(url)) {
        html = fs.readFileSync(url, 'utf8');
    } else {
        const response = await fetch(url);
        html = await response.text();
    }

    // get article text
    const dom = new JSDOM(html);
    const reader = new Readability(dom.window.document, { serializer: getText });
    const article = reader.parse();

    // return article
    return article;
}

module.exports = { extractText };
