const { extractText } = require('./extract.js');

// parse arguments
const args = process.argv.slice(2);
const url = args[0];

// get article
extractText(url).then((article) => {
    console.log(article.title);
    console.log();
    console.log(article.content);
});
