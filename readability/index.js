const fs = require('fs');
const path = require('path');
const http = require('http');
const {Readability} = require('@mozilla/readability');
const JSDOM = require('jsdom').JSDOM;

// article getter
async function get_article(url) {
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
    const reader = new Readability(dom.window.document);
    const article = reader.parse();

    // return article
    return article;
}

// parse arguments
const args = process.argv.slice(2);
const url = args[0];

// get article
get_article(url).then((article) => {
    console.log(article.title);
    console.log(article.textContent);
});
